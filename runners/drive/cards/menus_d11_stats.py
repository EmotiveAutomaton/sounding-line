"""Certified convex partial-pooling logistic fits, including bootstrap copies.

DESIGN CHECK: LESSONS 3-5 read October18. Independent labels yield zero-centered
population slopes; planted positive/reversed slopes retain their sign. Identical
copies of a resampled writer receive identical conditional modes, so weighting
both their likelihood AND their random-effect penalty is exactly the cloned
problem. Uncertified numerical modes never enter a primary interval.
"""
from collections import Counter
import numpy as np
from scipy.special import expit


def observation_weights(rows):
    sessions=Counter((r['writer'],r['session']) for r in rows);writers=Counter(w for w,_ in sessions)
    return np.asarray([len(rows)/len(writers)/writers[r['writer']]/sessions[r['writer'],r['session']] for r in rows])


def fit(x,y,group,own,weights,config,multiplicity=None,start=None):
    x=np.asarray(x,float);y=np.asarray(y,float);group=np.asarray(group,int);own=np.asarray(own,float)
    n,q=x.shape;writers=int(group.max())+1
    if y.shape!=(n,) or not np.isfinite(x).all() or not np.isin(y,[0,1]).all():raise ValueError('invalid logistic design')
    copies=np.ones(writers) if multiplicity is None else np.asarray(multiplicity,float)
    if copies.shape!=(writers,) or np.any(copies<0) or not np.any(copies>0):raise ValueError('invalid writer copies')
    active=np.flatnonzero(copies>0);lookup=np.full(writers,-1,int);lookup[active]=np.arange(len(active));mask=copies[group]>0
    original_group=group[mask];group=lookup[original_group];x=x[mask];y=y[mask];own=own[mask]
    weights=np.asarray(weights)[mask]*copies[original_group];z=np.column_stack([np.ones(len(y)),own]);k=len(active)
    beta=np.zeros(q) if start is None else np.asarray(start['beta']).copy()
    random=np.zeros((k,2)) if start is None else np.asarray(start['random'])[active].copy()
    fixed_penalty=np.full(q,config['fixed_ridge']);fixed_penalty[0]=0
    random_penalty=copies[active,None]*np.asarray([config['intercept_ridge'],config['slope_ridge']])[None,:]

    def objective(beta,random):
        logits=x@beta+np.sum(z*random[group],axis=1)
        return float(np.sum(weights*(np.logaddexp(0,logits)-y*logits))+.5*np.sum(fixed_penalty*beta*beta)+.5*np.sum(random_penalty*random*random))

    for iteration in range(config['max_iterations']):
        p=expit(x@beta+np.sum(z*random[group],axis=1));residual=weights*(p-y);curvature=weights*p*(1-p)
        gb=x.T@residual+fixed_penalty*beta;gr=random_penalty*random
        np.add.at(gr,group,residual[:,None]*z)
        gap=max(float(np.max(np.abs(gb))),float(np.max(np.abs(gr))))
        if gap<=config['gradient_tolerance']:break
        bb=x.T@(curvature[:,None]*x)+np.diag(fixed_penalty)
        rr=np.zeros((k,2,2));br=np.zeros((k,q,2))
        for j in range(k):
            subset=group==j;weighted_z=curvature[subset,None]*z[subset]
            rr[j]=z[subset].T@weighted_z+np.diag(random_penalty[j]);br[j]=x[subset].T@weighted_z
        ri=np.linalg.inv(rr);profile=bb-np.einsum('wqi,wij,wrj->qr',br,ri,br,optimize=True)
        rhs=gb-np.einsum('wqi,wij,wj->q',br,ri,gr,optimize=True)
        try:db=np.linalg.solve(profile,rhs)
        except np.linalg.LinAlgError as exc:raise ValueError('singular logistic profile') from exc
        dr=np.einsum('wij,wj->wi',ri,gr-np.einsum('wqi,q->wi',br,db))
        current=objective(beta,random);step=1.
        for _ in range(35):
            nb=beta-step*db;nr=random-step*dr
            if objective(nb,nr)<=current-1e-4*step*(gb@db+np.sum(gr*dr)):
                beta,random=nb,nr;break
            step*=.5
        else:raise ValueError('logistic line search uncertified')
    else:raise ValueError('logistic iteration cap')
    full=np.zeros((writers,2));full[active]=random
    return dict(beta=beta.tolist(),random=full.tolist(),gradient_gap=gap,iterations=iteration,
                objective=objective(beta,random),active_writers=active.tolist())
