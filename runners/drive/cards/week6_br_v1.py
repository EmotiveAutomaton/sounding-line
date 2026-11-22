"""BR severity, temporal separation and fallback diagnostics, on authenticated diaries.

DESIGN CHECK (2026-11-21). Lessons read: LESSONS 3-5, inherited diary operator.
Gates, null/alternative/direction: the morning operator's measurement, null and
replication checks carry over. In the synthetic severity-only and episode-only
worlds, the respective control should reduce the false positive frequency.
Under the alternative, true slope variation can survive either form with adequate repeated prompts.
The two supplied count tables bound discrepancies at 0.10. A graded slope
requires distinct above-floor ratings. Unsupported comparisons have no estimate.
Verdict bands per arm, exhaustive: an interval strictly above zero meets the bar; all other intervals miss it.
A held slope meets all three bars. A floor, poor severity proxy or a short
diary can prevent separation. Independent replay checks the grouped fits.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from . import week6_br_forms_v1 as forms
from . import week6_person_ladder_v1 as base
from . import week6_person_more_sources_v1 as sources
from . import week6_person_slopes_v1 as op
from .week6_person_tie_v1 import verify_metric_tree
from .batch_runtime import read, filehash, freeze, atomic, now

MANIFEST, ROOT_NAME = base.MANIFEST, base.ROOT_NAME
source = sources.source


def grade_column(member, name):
    if member == '0072' or name.startswith('argument_'):
        return None
    if member == '0060':
        return 'intellect'
    if member == '0076':
        return 'stressed'
    if name.startswith('intellectual_'):
        return 'intellectual'
    event = name.split('_')[0]
    return 'status_' + ('criticised' if event == 'criticism' else event)


def retained(frame, member, first):
    f = frame.loc[~frame.id.isin(['','NA'])].copy()
    for k in f.columns.drop('id'):
        f[k] = pd.to_numeric(f[k].replace({'':np.nan,'NA':np.nan}), errors='raise')
    f = f.loc[f.day.notna()]
    if member == '0056' or (member == '0057' and first):
        f = f.loc[f.interaction.eq(1)]
    elif member == '0057':
        f = f.loc[f.interaction.isin([1,2])]
    elif member == '0076':
        f = f.dropna(subset=['interaction_playful','interaction_pleasant','stressed'])
    elif member == '0072':
        f = f.loc[~f.duplicated(['id','day'],keep=False)]
    return f


def graded_halves(data, grade, feeling, half, replay):
    people = data['ids']
    parts = []
    for side in (0,1):
        use=(half==side)&np.isfinite(grade)&np.isfinite(feeling)
        ids=people[use]
        counts=np.bincount(ids,minlength=data['n'])
        width=max(1,int(counts.max()))
        ix=pd.Series(ids).groupby(ids).cumcount().to_numpy(dtype=int)
        r=np.full((len(counts),width),np.nan)
        y=np.full_like(r,np.nan)
        r[ids,ix]=grade[use]
        y[ids,ix]=feeling[use]
        side_stats=forms.graded_stats(r,y)
        if replay:
            for person in np.flatnonzero(np.isfinite(side_stats['b'])):
                valid=np.isfinite(r[person])
                rv=r[person,valid];yv=y[person,valid]
                slope,intercept=np.linalg.lstsq(np.column_stack([rv,np.ones(len(rv))]),yv,rcond=None)[0]
                if not np.isclose(side_stats['b'][person],slope,rtol=1e-9,atol=1e-10):
                    raise ValueError('Independent graded fit differs')
                side_stats['b'][person]=slope
        parts.append(side_stats)
    return parts


def estimate(parts, seed, weight, guard):
    valid=np.isfinite(parts[0]['b']) & np.isfinite(parts[1]['b'])
    a,b=base.supported(parts,valid)
    n=int(valid.sum())
    if n<2:
        return dict(people=n,reading='insufficient support')
    w=np.minimum(a[weight],b[weight])
    def pair(k): return a[k],b[k]
    corr=op.wpearson(w,*pair('L'))
    spread=op.wpearson(w,*pair('S'))>=.3
    cov=[pair('L')]+([pair('S')] if spread else [])
    rng=np.random.default_rng(seed)
    results=[]
    for start in range(0,2001,50):
        guard()
        count=min(50,2001-start)
        W=op.boot_counts(rng,n,count-(start==0))*w
        if start==0: W=np.vstack([w,W])
        raw,adj,_=op.adjust(W,pair('b'),cov)
        ll=op.cc(W,pair('L'),pair('L'))
        if spread:
            ls=op.cc(W,pair('L'),pair('S'))
            ss=op.cc(W,pair('S'),pair('S'))
            mat=np.stack([ll,ls,ls,ss],-1).reshape(-1,2,2)
            use_spread=np.linalg.eigvalsh(mat)[:,0]>op.EPS
        else:
            use_spread=np.zeros(len(W),dtype=bool)
        results.extend(np.column_stack([raw,adj,~use_spread,(~use_spread)&(ll<=op.EPS)]))
    raw,adj,drop,bare=np.array(results).T
    var=base.stat(adj[0],adj[1:])
    return dict(people=n,median_event_prompts_per_half=[float(np.median(t['n1'])) for t in (a,b)],
                level_correlation=float(corr) if np.isfinite(corr) else None,
                spread_dropped=float(drop[1:].mean()),unadjusted=float(bare[1:].mean()),
                raw_variance=base.stat(raw[0],raw[1:]),adjusted_variance=var,
                reading='stable' if var['interval'][0]>0 else 'could not say')


def operate(output,inputs,config,replay):
    output=Path(output)
    phase='verify' if replay else 'execute'
    dest=output/phase
    dest.mkdir(exist_ok=True)
    member=config['member']
    src,cols=source(member,inputs['data_root'])
    if filehash(src)!=inputs['source_sha256'] or inputs['manifest_sha256']!=MANIFEST:
        raise ValueError('Changed diary pin')
    frame=pd.read_csv(src,sep='\t',dtype=str,usecols=cols,keep_default_na=False)
    metadata=read(src.parent.parent/'DOCUMENTED_METADATA.json')
    features={x['name']:x for x in metadata['features']}
    def guard():
        if any((output/f).exists() for f in ('STOP_REQUEST.json','YIELD_REQUEST.json')):
            raise InterruptedError('Requested yield')
    result={}
    for label,pin in inputs['morning'].items():
        path=Path(pin['path'])
        if filehash(path)!=pin['sha256']:raise ValueError('Changed morning result')
        original=read(path)['result']['splits']['time']['PST1']
        first=label=='first'
        data=(base if first else sources).project(frame,member)
        if set(data['slopes'])!=set(original):raise ValueError('Morning coverage mismatch')
        f=retained(frame,member,first)
        roster=np.unique(frame.loc[~frame.id.isin(['','NA']),'id'].astype(str))
        if not np.array_equal(roster[data['ids']],f.id.astype(str)):raise ValueError('Person alignment')
        days=f.day.groupby(f.id)
        early,late=forms.gap_masks(f.day,days.transform('min'),days.transform('max'))
        groups=base.half_panel(data,data['splits']['time'],replay)[0]
        gap=base.half_panel(data,np.where(early,0,np.where(late,1,-1)),replay)[0]
        rows={}
        for j,(name,(event,y)) in enumerate(data['slopes'].items()):
            pre=original[name]
            row=rows[name]=dict(morning=pre.get('reading',pre.get('status')),morning_variance=pre.get('adjusted_variance'))
            if row['morning']=='could not say':
                diag=estimate(groups[name],[202611210000+int(member)*10,1,j],'n1',guard)
                if not np.allclose(diag['raw_variance']['interval'],pre['raw_variance']['interval'],rtol=1e-7,atol=1e-8):
                    raise ValueError('Morning raw interval mismatch '+name)
                row['PST7']=diag
        for j,(name,(event,y)) in enumerate(data['slopes'].items()):
            row=rows[name]
            col=grade_column(member,name)
            row['event']=col or ('child_distress' if name.startswith('child_') else name.split('_')[0])
            if col is None:
                row['PST4']=dict(reading='void',reason='Parent diary void under BR' if member=='0072' else 'Binary argument event')
            else:
                if int(features[col]['answer_categories'])<3:raise ValueError('Graded binding failed '+col)
                grade=np.where(np.isfinite(event),f[col].to_numpy()-1,np.nan)
                if not np.array_equal(np.where(np.isfinite(grade),grade>0,np.nan),event,equal_nan=True):
                    raise ValueError('Event floor mismatch '+name)
                parts=graded_halves(data,grade,y,data['splits']['time'],replay)
                row['PST4']=estimate(parts,[34,int(member),4,j],'sxx',guard)
            row['PST5']=estimate(gap[name],[34,int(member),5,j],'n1',guard)
            row['held']=bool((row['morning_variance'] or {}).get('interval') and row['morning_variance']['interval'][0]>0 and
                             all(row[k]['reading']=='stable' for k in ('PST4','PST5')))
        result[label]=rows
        atomic(dest/'PROGRESS.json',dict(at=now(),completed=label))
    if replay:
        verify_metric_tree(read(output/'execute/ENGINE_RESULT.json'),result)
    freeze(dest/'ENGINE_RESULT.json',result)
    return dict(status='verified' if replay else 'computed',verified=replay,requires_fresh_replay=not replay,
                scientific_result_complete=replay,engine_sha256=filehash(dest/'ENGINE_RESULT.json'),draw_count=2000)


def execute(output,inputs,config):
    return operate(output,inputs,config,False)


def verify(output,inputs,config):
    return operate(output,inputs,config,True)

