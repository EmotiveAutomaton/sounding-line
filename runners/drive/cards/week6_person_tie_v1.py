"""Whole-person analysis with the original single-slope and matching equations."""
import numpy as np
import pandas as pd
from pathlib import Path
from . import week6_person_slopes_v1 as op
from .week6_person_ladder_v1 import (DRAWS,MANIFEST,ROOT_NAME,half_panel,slope_support,supported,stat,variance_reading)
from .week6_person_more_sources_v1 import source,project
from .week6_person_more_pairs_v1 import summarize
from .batch_runtime import now,atomic,freeze,read,filehash

def ranking_feature(values):
    return np.round(values, decimals=12)


def verify_metric_tree(left,right,key='result'):
    from .week5_rr3_v1 import compare_record
    if isinstance(left,dict) and isinstance(right,dict) and left.keys()==right.keys():
        for field in left:verify_metric_tree(left[field],right[field],key+'.'+field)
    else:
        try:compare_record(left,right)
        except ValueError as error:raise ValueError('Independent aggregate differs at '+key) from error


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
    pairs,pooled=summarize(groups,data['n'],data['unpleasant'],singles,seed,guard)
    # No linkage outside this source. Ranking uses the corpus of people with
    # observable level and spread in both halves; missing slopes get the mean.
    keep=np.logical_and.reduce([np.isfinite(v).all(axis=1) for blocks in features for v in blocks])
    n=int(keep.sum());ranking=dict(people=n,excluded=int(len(keep)-n),status='insufficient ranking support')
    if n>=22:
        columns=[]
        for k in (0,1):
            vectors=[]
            for name in groups:
                x=ranking_feature(groups[name][k]['b'][keep])
                if np.isfinite(x).any(): x=np.where(np.isfinite(x),x,np.nanmean(x))
                else:x=np.zeros(n)
                vectors.append(x)
            columns.append(op.zs(np.column_stack([ranking_feature(features[k][0][keep]),ranking_feature(features[k][1][keep]),*vectors])))
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
        freeze(directory/'REPLAY_AGGREGATES.json',result)
        verify_metric_tree(read(output/'execute/ENGINE_RESULT.json'),result)
    path=directory/'ENGINE_RESULT.json'
    if path.exists():
        if read(path)!=result:raise ValueError("Changed completed result")
    else:freeze(path,result)
    return dict(status='verified' if verify else 'computed',verified=verify,requires_fresh_replay=not verify,
                scientific_result_complete=verify,engine_sha256=filehash(path),draw_count=DRAWS)


def execute(output,inputs,config):return run(output,inputs,config,False)


def verify(output,inputs,config):return run(output,inputs,config,True)

