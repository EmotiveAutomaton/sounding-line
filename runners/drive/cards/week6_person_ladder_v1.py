"""Prospective person-slope sources and whole-person resampling for Round 34.
Only aggregate quantities leave the worker. The diary and every source input
are bound to the curator-approved temporary root before outcome processing.
"""
from pathlib import Path
import os
import time
import numpy as np
import pandas as pd
from . import week6_person_slopes_v1 as op
from .week6_person_small_v1 import MANIFEST, ROOT_NAME
from .batch_runtime import filehash, read, freeze, atomic, now

STUDENT=('sad','worries','depressed','relaxed','enthusiastic','tense','energetic','guilty',
         'attentive','angry','content','happy','afraid','proud','excited','curious','rarely_anxious','rarely_excited')
STATUS=tuple('int_'+x for x in ('proud','success','superior','angry','excluded','envious','resentful',
                               'ashamed','insecure','enthusiastic','relaxed','anxious','sad','lonely'))
CONFIG={
    '0060':(STUDENT,('intellect','argument_family','argument_friend')),
    '0057':(STATUS,('interaction','status_criticised')),
}
DRAWS=2000


def source(member,root):
    levels,events=CONFIG[member]
    path=Path(root)
    if not path.is_absolute() or path.drive.casefold()!=os.environ['SystemDrive'].casefold() or path.name!=ROOT_NAME:
        raise ValueError('Require local temporary root')
    mf=path/'DRT1_MANIFEST.json'
    if filehash(mf)!=MANIFEST: raise ValueError('Changed copy manifest')
    pins={r['path']:r for r in read(mf)['files']}
    prefix='open/openesm-'+member+'/'
    def checked(rel):
        pin=pins[prefix+rel];p=path/pin['path']
        if p.stat().st_size!=pin['bytes'] or filehash(p)!=pin['sha256']: raise ValueError('Changed local original')
        return p
    record=read(checked('SOURCE.json')); checked('LICENCE_RECORD.json')
    if record['slug']!='openesm-'+member or record['class'] not in ('open-clean','open-tests-only'):
        raise ValueError('Unreviewed source')
    meta=read(checked('DOCUMENTED_METADATA.json'))
    variables=set(('id','day',*levels,*events))
    if float(meta['n_days'])<7 or not variables<={x['name'] for x in meta['features']}:
        raise ValueError('Source codebook binding failed')
    table,=[x for x in read(checked('SCHEMA.json'))['files'] if x['file'].endswith('_ts.tsv')]
    if table['malformed_row_count'] or not variables<={x['name'] for x in table['columns']}: raise ValueError('Source layout differs')
    p=checked('raw/'+table['file'])
    if filehash(p)!=table['sha256']: raise ValueError('Layout digest differs')
    return p,sorted(variables)


def scale(y,ids):
    series=pd.Series(y,dtype=float)
    grouped=series.groupby(ids)
    residual=series-grouped.transform('mean')
    dof=int(series.count()-grouped.count().gt(0).sum())
    sd=np.sqrt(residual.pow(2).sum()/dof) if dof>0 else np.nan
    return series.to_numpy()/sd if sd>0 else np.full(len(y),np.nan)


def project(frame,member):
    feelings,events=CONFIG[member]
    raw_count=len(frame)
    f=frame.loc[~frame.id.isin(['','NA'])].copy()
    roster,ids=np.unique(f.pop('id').astype(str),return_inverse=True)
    for col in f:
        v=pd.to_numeric(f[col].replace({'':np.nan,'NA':np.nan}),errors='raise')
        if col=='day':
            if ((v%1!=0)&v.notna()).any():raise ValueError('Fractional study day')
        else:
            lo=0 if col in ('argument_family','argument_friend') else 1
            hi=(1 if lo==0 else 3 if col=='intellect' else 2 if col=='interaction' else 5 if member=='0060' else 6)
            if ((v<lo)|(v>hi)|((v%1!=0)&v.notna())).any():raise ValueError('Item coding differs: '+col)
        f[col]=v
    mask=f.day.notna().to_numpy()
    if member=='0057':mask = mask & (f.interaction==1).to_numpy()
    ids=ids[mask]; f=f.loc[mask].reset_index(drop=True)
    y={k:scale(f[k],ids) for k in feelings}
    if member=='0060':
        arg=f[['argument_family','argument_friend']].max(axis=1,skipna=False).to_numpy()
        intellect=f.intellect.to_numpy()
        intellectual=np.where(np.isfinite(intellect),intellect>1,np.nan)
        slopes={'curiosity':(intellectual,y['curious']),'argument_anger':(arg,y['angry']),
                'argument_fear':(arg,y['afraid']),'argument_anger_minus_fear':(arg,y['angry']-y['afraid'])}
        unpleasant=('argument_anger','argument_fear')
    else:
        ev=f.status_criticised.to_numpy()
        criticism=np.where(np.isfinite(ev),ev>1,np.nan)
        slopes={'criticism_anger':(criticism,(y['int_angry']+y['int_resentful'])/2),
                'criticism_shame':(criticism,y['int_ashamed'])}
        unpleasant=tuple(slopes)
    day=f.day.to_numpy()
    dates=f.day.groupby(ids)
    halfway=(dates.transform('min')+dates.transform('max'))/2
    splits={'time':(day>halfway.to_numpy()).astype(int),'odd_even':(day%2==0).astype(int)}
    return dict(ids=ids,n=len(roster),feelings=y,slopes=slopes,splits=splits,unpleasant=unpleasant,
                counts=dict(source_reports=raw_count,dated_context_reports=len(day),source_people=len(roster)))


def summaries(ids,values,mask,n,verify=False):
    keep=mask&np.isfinite(values);v=values[keep];i=ids[keep]
    cnt=np.bincount(i,minlength=n)
    if verify:
        stats=pd.Series(v).groupby(i).agg(['mean','std']).reindex(range(n))
        return cnt,stats['mean'].to_numpy(),stats['std'].to_numpy()
    avg=np.divide(np.bincount(i,weights=v,minlength=n),cnt,out=np.full(n,np.nan),where=cnt>0)
    ss=np.bincount(i,weights=(v-avg[i])**2,minlength=n)
    sd=np.sqrt(np.divide(ss,cnt-1,out=np.full(n,np.nan),where=cnt>1))
    return cnt,avg,sd


def half_panel(data,half,verify):
    ids,n=data['ids'],data['n']
    values={};features=[]
    for side in (0,1):
        keep=half==side; means=[];spreads=[]
        for y in data['feelings'].values():
            _,level,spread=summaries(ids,y,keep,n,verify)
            means.append(level);spreads.append(spread)
        features.append([np.column_stack(means),np.column_stack(spreads)])
        for name,(ev,y) in data['slopes'].items():
            n0,lev,spread=summaries(ids,y,keep&(ev==0),n,verify)
            n1,other,_=summaries(ids,y,keep&(ev==1),n,verify)
            slope=np.where((n0>=2)&(n1>=2),other-lev,np.nan)
            values.setdefault(name,[]).append(dict(n1=n1,n0=n0,b=slope,L=lev,S=spread))
    return values,features


def quant(v):
    a=np.asarray(v,float)
    valid=a[np.isfinite(a)]
    return (np.quantile(valid,[.025,.975]).tolist() if len(valid)>=2 else None),len(valid)


def stat(point,draws):
    ci,n=quant(draws)
    return dict(estimate=float(point) if np.isfinite(point) else None,interval=ci,valid_draws=n,
                bootstrap_sd=float(np.nanstd(draws,ddof=1)) if n>=2 else None)


def supported(parts,keep):
    return [{key:v[keep] for key,v in side.items()} for side in parts]


def slope_support(groups):
    counts={}
    for key,parts in groups.items():
        keep=np.logical_and.reduce([np.isfinite(s['b']) for s in parts])
        first,second=supported(parts,keep)
        counts[key]=dict(people=int(keep.sum()),excluded_people=int(len(keep)-keep.sum()),
                         events=[int(first['n1'].sum()),int(second['n1'].sum())],
                         others=[int(first['n0'].sum()),int(second['n0'].sum())])
    return counts


def variance_reading(interval,share):
    if interval and interval[0]>0:return 'stable beyond level and spread'
    if interval and interval[0]<=0<=interval[1] and share and share['upper']<.5:return 'flat within bound'
    return 'could not say'


def factor_reading(pair):
    if pair['status']!='estimable pair':return dict(qualifying_pairs=0,reading='no verdict')
    corr=pair['adjusted_correlation']
    point,interval=corr['estimate'],corr['interval']
    if point is None or interval is None:return dict(qualifying_pairs=0,reading='no verdict')
    reading='undecided'
    if point>=.5 and interval[0]>.30:reading='one'
    if point<.3 and interval[1]<.50:reading='several'
    return dict(qualifying_pairs=1,pooled=point,interval=interval,cochran_q=0.,q_df=0,reading=reading)


def analyze_split(data,half,seed,verify,guard):
    groups,features=half_panel(data,half,verify)
    singles={};pairs={}
    support=slope_support(groups)
    for j,(key,parts) in enumerate(groups.items()):
        keep=np.logical_and.reduce([np.isfinite(s['b']) for s in parts])
        a,b=supported(parts,keep);w=np.minimum(a['n1'],b['n1'])
        if len(w)<2: singles[key]=dict(status='insufficient support');continue
        use=bool(np.isfinite(a['S']).all() and op.wpearson(w,a['S'],b['S'])>=.30)
        covariates=[(a['L'],b['L'])]+([(a['S'],b['S'])] if use else [])
        weights=w[None,:]
        rng=np.random.default_rng([seed,1,j]); block=[]
        for start in range(0,DRAWS+1,50):
            guard()
            weights=(np.vstack([w,op.boot_counts(rng,len(w),49)*w]) if start==0 else
                     op.boot_counts(rng,len(w),min(50,DRAWS+1-start))*w)
            raw,adjusted,_=op.adjust(weights,(a['b'],b['b']),covariates)
            mean=op.wmean(weights,(a['b']+b['b'])/2)
            block.extend(np.column_stack([mean,raw,adjusted]))
        mean,raw,adj=np.asarray(block).T
        m=stat(mean[0],mean[1:]);ad=stat(adj[0],adj[1:])
        share=None
        if m['interval'] and ad['interval'] and m['interval'][0]*m['interval'][1]>0:
            share=dict(estimate=float(np.sqrt(max(adj[0],0))/abs(mean[0])),
                       upper=float(np.sqrt(max(ad['interval'][1],0))/abs(mean[0])))
        singles[key]=dict(mean=m,raw_variance=stat(raw[0],raw[1:]),adjusted_variance=ad,share=share,spread_selected=use,reading=variance_reading(ad["interval"],share))
    # Both requested first-source pairs have one common event. Use the smaller
    # event count from all four halves when an incomplete outcome changes support.
    left,right=data['unpleasant']
    keep=np.logical_and.reduce([np.isfinite(s['b']) for k in (left,right) for s in groups[k]])
    aa,bb=supported(groups[left],keep),supported(groups[right],keep)
    w=np.minimum.reduce([s['n1'] for s in (*aa,*bb)])
    pair=dict(people=len(w),status='no supported pair')
    if len(w)>=2:
        rng=np.random.default_rng([seed,2])
        sides=[dict(A=aa[k],B=bb[k]) for k in (0,1)]
        use={k:bool(op.wpearson(w,sides[0][k]['S'],sides[1][k]['S'])>=.30) for k in ('A','B')}
        rows=[]
        for start in range(0,DRAWS+1,50):
            guard()
            wt=(np.vstack([w,op.boot_counts(rng,len(w),49)*w]) if start==0 else op.boot_counts(rng,len(w),min(50,DRAWS+1-start))*w)
            _,_,va,vb,rho=op.slope_block(wt,*sides,use)
            # The adjusted covariance is defined even when the true-correlation
            # denominator is unidentified. Compute it explicitly in that case.
            xa=[(aa[0]['L'],aa[1]['L'])]+([(aa[0]['S'],aa[1]['S'])] if use['A'] else [])
            xb=[(bb[0]['L'],bb[1]['L'])]+([(bb[0]['S'],bb[1]['S'])] if use['B'] else [])
            ba=(aa[0]['b'],aa[1]['b']); bc=(bb[0]['b'],bb[1]['b'])
            beta_a=op.adjust(wt,ba,xa)[2];beta_b=op.adjust(wt,bc,xb)[2]
            cov=op.cc(wt,ba,bc)
            for u,x in enumerate(xa):cov-=beta_a[:,u]*op.cc(wt,x,bc)
            for v,y in enumerate(xb):cov-=beta_b[:,v]*op.cc(wt,y,ba)
            for u,x in enumerate(xa):
                for v,y in enumerate(xb):cov+=beta_a[:,u]*beta_b[:,v]*op.cc(wt,x,y)
            rows.extend(np.column_stack([va,vb,cov,rho]))
        va,vb,cov,rho=np.asarray(rows).T
        valid=all(x in singles and singles[x].get('adjusted_variance',{}).get('interval',[0])[0]>0 for x in (left,right))
        valid=valid and quant(va[1:])[0][0]>0 and quant(vb[1:])[0][0]>0
        pair.update(adjusted_covariance=stat(cov[0],cov[1:]),adjusted_correlation=stat(rho[0],rho[1:]),
                    first_factor_share=float((1+abs(rho[0]))/2) if valid and abs(rho[0])<=1 else None,
                    status='estimable pair' if valid else 'no supported pair')
    pairs[left+' / '+right]=pair
    pooled=factor_reading(pair)
    # No linkage outside this source. Ranking uses the corpus of people with
    # observable level and spread in both halves; missing slopes get the mean.
    keep=np.logical_and.reduce([np.isfinite(v).all(axis=1) for blocks in features for v in blocks])
    n=int(keep.sum());ranking=dict(people=n,excluded=int(len(keep)-n),status='insufficient ranking support')
    if n>=22:
        columns=[]
        for k in (0,1):
            vectors=[]
            for name in groups:
                x=groups[name][k]['b'][keep]
                if np.isfinite(x).any(): x=np.where(np.isfinite(x),x,np.nanmean(x))
                else:x=np.zeros(n)
                vectors.append(x)
            columns.append(op.zs(np.column_stack([features[k][0][keep],features[k][1][keep],*vectors])))
        f=features[0][0].shape[1]
        hits,chance=op.fold_hits(np.random.default_rng([seed,3]),*columns,
                                {'mean':slice(0,f),'spread':slice(0,2*f),'slopes':slice(None)})
        rng=np.random.default_rng([seed,4]);hit=np.column_stack([*hits.values(),hits['slopes']-hits['spread']])
        draws=[]
        for _ in range(DRAWS//50):
            guard();draws.extend(op.boot_counts(rng,n,50)@hit/n)
        table={k:stat(v,np.asarray(draws)[:,i]) for i,(k,v) in enumerate(zip((*hits,'added_slopes'),hit.mean(axis=0)))}
        diff=table['added_slopes']
        ranking.update(reading='adds to level and spread' if diff['estimate']>=.02 and diff['interval'][0]>0 else 'uninformative about slope variance',status='complete',chance=float(chance),fold_sizes=[n//2,n-n//2],arms=table)
    return dict(support=support,PST1=singles,PST2=ranking,PST3=pairs,PST3_pool=pooled)


def run(output,inputs,config,verify):
    member=config['member'];root=Path(inputs['data_root'])
    p,cols=source(member,root)
    if filehash(p)!=inputs['source_sha256'] or inputs['manifest_sha256']!=MANIFEST:raise ValueError('Unpinned source')
    output=Path(output);phase='verify' if verify else 'execute'
    directory=output/phase;directory.mkdir(exist_ok=True,parents=True)
    data=project(pd.read_csv(p,sep='\t',usecols=cols,dtype=str,keep_default_na=False),member)
    def guard():
        if (output/'STOP_REQUEST.json').exists() or (output/'YIELD_REQUEST.json').exists():raise InterruptedError('Bounded source yield')
    support={k:slope_support(half_panel(data,v,verify)[0]) for k,v in data['splits'].items()}
    support_record=dict(member=member,temporary_root=ROOT_NAME,manifest_sha256=MANIFEST,support=support)
    dest=directory/'SUPPORT.json'
    if dest.exists():
        if read(dest)!=support_record:raise ValueError('Changed support on restart')
    else:freeze(dest,support_record)
    panel={}
    try:
        for i,(name,index) in enumerate(data['splits'].items()):
            guard()
            panel[name]=analyze_split(data,index,202611210000+int(member)*10+i,verify,guard)
            atomic(directory/'PROGRESS.json',dict(at=now(),phase=phase,completed_split=name,temporary_root=ROOT_NAME,manifest_sha256=MANIFEST))
    except InterruptedError:
        return dict(status='yielded',verified=False,operation=phase,scientific_result_complete=False)
    result=dict(member=member,counts=data['counts'],temporary_root=ROOT_NAME,manifest_sha256=MANIFEST,draws=DRAWS,splits=panel)
    if verify:
        from .week5_rr3_v1 import compare_record
        compare_record(read(output/'execute/ENGINE_RESULT.json'),result)
    path=directory/'ENGINE_RESULT.json'
    if path.exists():
        if read(path)!=result:raise ValueError("Changed completed result")
    else:freeze(path,result)
    return dict(status='verified' if verify else 'computed',verified=verify,requires_fresh_replay=not verify,
                scientific_result_complete=verify,engine_sha256=filehash(path),draw_count=DRAWS)


def execute(output,inputs,config):return run(output,inputs,config,False)


def verify(output,inputs,config):return run(output,inputs,config,True)

