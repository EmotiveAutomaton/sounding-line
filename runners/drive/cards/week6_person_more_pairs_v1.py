"""Pair-specific measurement and inverse-variance pooling with shared person draws."""
from itertools import combinations
import numpy as np
from . import week6_person_ladder_v1 as base
from . import week6_person_slopes_v1 as op

def positive(row):
    interval=row.get('interval')
    return bool(interval and interval[0]>0)

def summarize(groups,n,unpleasant,singles,seed,guard):
    from .week6_person_ladder_v1 import DRAWS
    pairs={}; qualified={};indices={}
    for left,right in combinations(unpleasant,2):
        guard()
        label=left+' / '+right
        valid=np.logical_and.reduce([np.isfinite(s['b']) for name in (left,right) for s in groups[name]])
        a,b=[base.supported(groups[k],valid) for k in (left,right)]
        weights=np.minimum.reduce([v['n1'] for v in (*a,*b)])
        entry=pairs[label]=dict(people=int(valid.sum()),status='no supported pair')
        if len(weights)<2:continue
        sides=[dict(A=a[i],B=b[i]) for i in (0,1)]
        covariates={}
        use={}
        for k,v in [('A',a),('B',b)]:
            use[k]=bool(op.wpearson(weights,v[0]['S'],v[1]['S'])>=.30)
            covariates[k]=[(v[0]['L'],v[1]['L'])]+([(v[0]['S'],v[1]['S'])] if use[k] else [])
        # A common source draw supplies aligned weights even for overlapping pairs.
        rng=np.random.default_rng([seed,2,47]);rows=[]
        for start in range(0,DRAWS+1,50):
            guard()
            count=min(50,DRAWS+1-start)
            if start==0:
                w=np.vstack([weights,op.boot_counts(rng,n,count-1)[:,valid]*weights])
            else:w=op.boot_counts(rng,n,count)[:,valid]*weights
            _,_,va,vb,rho=op.slope_block(w,*sides,use)
            xa,xb=covariates['A'],covariates['B']
            sa=a[0]['b'],a[1]['b'];sb=b[0]['b'],b[1]['b']
            ba=op.adjust(w,sa,xa)[2];bb=op.adjust(w,sb,xb)[2]
            cov=op.cc(w,sa,sb)
            for i,x in enumerate(xa):cov-=ba[:,i]*op.cc(w,x,sb)
            for j,y in enumerate(xb):cov-=bb[:,j]*op.cc(w,y,sa)
            for i,x in enumerate(xa):
                for j,y in enumerate(xb):cov+=ba[:,i]*bb[:,j]*op.cc(w,x,y)
            rows.extend(np.column_stack([cov,rho,va,vb]))
        cov,rho,va,vb=np.asarray(rows).T
        entry.update(adjusted_covariance=base.stat(cov[0],cov[1:]),adjusted_correlation=base.stat(rho[0],rho[1:]))
        if (all(positive(singles[k].get('adjusted_variance',{})) for k in (left,right)) and
            all(positive(base.stat(v[0],v[1:])) for v in (va,vb)) and np.isfinite(rho[0])):
            entry['status']='estimable pair'
            qualified[label]=rho;indices[label]=(left,right)
    pool=dict(qualifying_pairs=len(qualified),reading='no verdict',first_factor_share=None)
    if not qualified:return pairs,pool
    matrix=np.stack(list(qualified.values()))
    if not np.isfinite(matrix).all():
        pool['reason']='At least one qualifying pair lacks an indexed correlation draw.'
        return pairs,pool
    if len(matrix)==1:weights=np.ones(1)
    else:
        variances=matrix[:,1:].var(axis=1,ddof=1)
        if min(variances)<=0:
            pool['reason']='Inverse variance unavailable for a constant pair.'
            return pairs,pool
        weights=1/variances
    pooled=np.average(matrix,axis=0,weights=weights)
    stat=base.stat(pooled[0],pooled[1:])
    pool.update(pooled=stat['estimate'],interval=stat['interval'],reading='undecided',cochran_q=float(np.sum(weights*(matrix[:,0]-pooled[0])**2)),q_df=len(matrix)-1)
    lo,hi=pool['interval'];p=pool['pooled']
    if p>=.5 and lo>.3:pool['reading']='one'
    if p<.3 and hi<.5:pool['reading']='several'
    names=sorted({k for v in indices.values() for k in v})
    if len(indices)==len(names)*(len(names)-1)//2:
        corr=np.eye(len(names))
        for label,(a,b) in indices.items():
            i,j=names.index(a),names.index(b);corr[i,j]=corr[j,i]=qualified[label][0]
        eig=np.linalg.eigvalsh(corr)
        if eig[0]>=-1e-10:pool['first_factor_share']=float(eig[-1]/len(names))
    return pairs,pool

