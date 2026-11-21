"""PST6. Joint whole-person draws for elementary held slopes.

DESIGN CHECK (2026-11-21). Lessons read: LESSONS 3-5. Under the null,
stable individual responses to one event need not correlate with responses
to a different event. Under the alternative a common response can produce
positive correlations in both strata. Excluding algebraic differences guards
against shared terms. Failure direction: including a difference can inflate the correlation.
Verdict bands are exhaustive: one at 0.5 with lower bound above 0.3, several
below 0.3 with upper bound below 0.5, otherwise undecided. Missing positive
variance or incomplete correlation draws leaves the applicable pool undecided.
"""
from itertools import combinations
from pathlib import Path
import numpy as np
import pandas as pd
from . import week6_br_v1 as br
from . import week6_person_slopes_v1 as op
from .batch_runtime import read, filehash, freeze

MANIFEST,ROOT_NAME,source=br.MANIFEST,br.ROOT_NAME,br.source


def pool(rows):
    if not rows:
        return dict(reading='no verdict',pairs=0)
    mat=np.array(rows)
    if not np.isfinite(mat).all():
        return dict(reading='undecided',pairs=len(mat),reason='Incomplete correlation draws')
    variance=mat[:,1:].var(axis=1,ddof=1)
    if min(variance)<=0:
        return dict(reading='undecided',pairs=len(mat),reason='Zero bootstrap variance')
    weights=1/variance
    rho=np.average(mat,axis=0,weights=weights)
    v=br.base.stat(rho[0],rho[1:])
    lo,hi=v['interval']
    reading='one' if rho[0]>=.5 and lo>.3 else 'several' if rho[0]<.3 and hi<.5 else 'undecided'
    return dict(reading=reading,pairs=len(mat),correlation=v,draws=rho.tolist())


def estimate_pair(parts,n,seed,guard):
    valid=np.logical_and.reduce([np.isfinite(s['b']) for sides in parts for s in sides])
    size=int(valid.sum())
    if size<2:return dict(people=size,reading='unsupported'),None
    a,b=[br.base.supported(p,valid) for p in parts]
    w=np.minimum.reduce([s['sxx'] for s in (*a,*b)])
    halves=[dict(A=a[i],B=b[i]) for i in range(2)]
    use={key:op.wpearson(w,sides[0]['S'],sides[1]['S'])>=.3 for key,sides in [('A',a),('B',b)]}
    rng=np.random.default_rng(seed)
    runs=[]
    for i in range(0,2001,50):
        guard()
        num=min(50,2001-i)
        weights=op.boot_counts(rng,n,num-(i==0))[:,valid]*w
        if i==0:weights=np.vstack([w,weights])
        _,_,va,vb,rho=op.slope_block(weights,*halves,use)
        # Residualize each side with its cross-half adjustment. This also
        # yields the covariance on draws where the correlation is undefined.
        residuals=[]
        for batch,key in ((a,'A'),(b,'B')):
            slopes=(batch[0]['b'],batch[1]['b'])
            covars=[(batch[0]['L'],batch[1]['L'])]
            if use[key]:covars.append((batch[0]['S'],batch[1]['S']))
            beta=op.adjust(weights,slopes,covars)[2]
            residuals.append([slopes[t]-sum(beta[:,j,None]*cov[t] for j,cov in enumerate(covars)) for t in (0,1)])
        cross=op.cc(weights,*residuals)
        runs.extend(np.column_stack([va,vb,rho,cross]))
    va,vb,rho,cross=np.array(runs).T
    v=[br.base.stat(x[0],x[1:]) for x in (va,vb,rho)]
    eligible=all(k['interval'] and k['interval'][0]>0 for k in v[:2]) and np.isfinite(rho[0])
    share=float((1+abs(rho[0]))/2) if eligible and abs(rho[0])<=1 else None
    return dict(people=size,variances=v[:2],correlation=v[2],covariance=br.base.stat(cross[0],cross[1:]),
                two_slope_first_factor_share=share,reading='estimable' if eligible else 'no verdict'),rho if eligible else None


def operate(output,inputs,config,replay):
    member=config['member']
    src,cols=source(member,inputs['data_root'])
    assert filehash(src)==inputs['source_sha256'] and inputs['manifest_sha256']==MANIFEST
    p=inputs['forms']
    if filehash(p['path'])!=p['sha256']:raise ValueError('Changed admission results')
    prior=read(p['path'])
    frame=pd.read_csv(src,sep='\t',dtype=str,usecols=cols,keep_default_na=False)
    def guard():
        if any((Path(output)/name).exists() for name in ('STOP_REQUEST.json','YIELD_REQUEST.json')):
            raise InterruptedError('Requested yield')
    result={}
    for label,rows in prior.items():
        first=label=='first'
        data=(br.base if first else br.sources).project(frame,member)
        f=br.retained(frame,member,first)
        held={}
        for name,row in rows.items():
            if not row['held'] or '_minus_' in name:continue
            ev,y=data['slopes'][name]
            grade=np.where(np.isfinite(ev),f[br.grade_column(member,name)]-1,np.nan)
            held[name]=br.graded_halves(data,grade,y,data['splits']['time'],replay)
        pairs={}
        groups={'same':[],'different':[]}
        for a,b in combinations(sorted(held),2):
            key='same' if rows[a]['event']==rows[b]['event'] else 'different'
            entry,rho=estimate_pair((held[a],held[b]),data['n'],[34,int(member),6],guard)
            pairs[a+' / '+b]=dict(event_group=key,**entry)
            if rho is not None:groups[key].append(rho)
        result[label]=dict(held_plain=sorted(held),pairs=pairs,groups={k:pool(v) for k,v in groups.items()})
    output=Path(output)
    dest=output/('verify' if replay else 'execute')
    dest.mkdir(parents=True,exist_ok=True)
    if replay:br.verify_metric_tree(read(output/'execute/ENGINE_RESULT.json'),result)
    freeze(dest/'ENGINE_RESULT.json',result)
    return dict(status='verified' if replay else 'computed',verified=replay,requires_fresh_replay=not replay,
                scientific_result_complete=replay,engine_sha256=filehash(dest/'ENGINE_RESULT.json'),draw_count=2000)


def execute(output,inputs,config):
    return operate(output,inputs,config,False)


def verify(output,inputs,config):
    return operate(output,inputs,config,True)

