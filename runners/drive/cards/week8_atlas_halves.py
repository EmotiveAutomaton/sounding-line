"""Whole-person half splits and grouped Form O fits for the frozen diary atlas."""
import hashlib

import numpy as np
from numba import njit
from scipy.sparse import coo_matrix


def seed(*parts):
    return int.from_bytes(hashlib.sha256('|'.join(map(str,('ATL2',*parts))).encode()).digest()[:8],'big')


def split_people(people, member, split):
    people=np.asarray(sorted(set(people)))
    order=np.random.default_rng(seed(member,split)).permutation(len(people))
    return [np.sort(x) for x in np.array_split(people[order],2)]


@njit
def grouped_fit(matrix, totals, successes):
    """Same three columns, Newton step, singularity cutoff and line search as ATL."""
    n=totals.sum()
    yes=successes.sum()
    if matrix.shape[0]<3 or yes==0 or n==yes or n==0:
        return np.nan
    b=np.zeros(3)
    for _ in range(60):
        hessian=np.zeros((3,3))
        grad=np.zeros(3)
        objective=0.
        for i in range(len(totals)):
            if totals[i]==0:
                continue
            z=b[0]+b[1]*matrix[i,1]+b[2]*matrix[i,2]
            t=np.exp(-abs(z))
            prob=1/(1+t) if z>=0 else t/(1+t)
            delta=totals[i]*prob-successes[i]
            scale=totals[i]*prob*(1-prob)
            objective+=totals[i]*(max(0.,z)+np.log1p(t))-successes[i]*z
            for j in range(3):
                grad[j]+=matrix[i,j]*delta
                for k in range(j+1):
                    hessian[j,k]+=matrix[i,j]*matrix[i,k]*scale
        for j in range(3):
            for k in range(j):
                hessian[k,j]=hessian[j,k]
        if np.linalg.cond(hessian)>1e12:
            return np.nan
        step=np.linalg.solve(hessian,grad)
        if np.max(np.abs(step))<1e-8:
            return b[1]*np.sqrt(np.dot(totals,matrix[:,1]**2)/n)
        for j in range(32):
            cand=b-step/(2**j)
            new_value=0.
            for i in range(len(totals)):
                if totals[i]>0:
                    z=cand[0]+cand[1]*matrix[i,1]+cand[2]*matrix[i,2]
                    new_value+=totals[i]*(max(0.,z)+np.log1p(np.exp(-abs(z))))-successes[i]*z
            if new_value<=objective+1e-10:
                b=cand
                break
        else:
            return np.nan
    return np.nan


@njit
def fit_batch(matrix, totals, successes):
    values=np.empty(len(totals))
    for draw in range(len(totals)):
        values[draw]=grouped_fit(matrix,totals[draw],successes[draw])
    return values


def fit_half(person,x,y,owners,draw_seed,draws=2000,batch=16):
    """Keep the same people weights across all item readings in a diary half."""
    valid=np.isfinite(x)&np.isfinite(y)&np.isin(person,owners)
    group=np.searchsorted(owners,person[valid])
    amount=np.bincount(group,minlength=len(owners))
    if np.count_nonzero(amount)<20:
        return None
    x=x[valid]
    y=y[valid]
    person_mean=np.divide(np.bincount(group,weights=x,minlength=len(owners)),amount,
                          out=np.zeros(len(owners)),where=amount>0)
    centered=x-person_mean[group]
    if len(np.unique(group[centered!=0]))<20:
        return None
    pairs,bin_index=np.unique(np.column_stack((centered,person_mean[group])),axis=0,return_inverse=True)
    X=np.column_stack((np.ones(len(pairs)),pairs))
    shape=(len(pairs),len(owners))
    counts=coo_matrix((np.ones(len(y)),(bin_index,group)),shape=shape).tocsr()
    success=coo_matrix((y,(bin_index,group)),shape=shape).tocsr()
    common=np.ones(len(owners))
    point=grouped_fit(X,counts@common,success@common)
    if not np.isfinite(point):
        return None
    weights=np.ones(len(owners))/len(owners)
    rng=np.random.default_rng(draw_seed)
    estimates=np.empty(draws+1)
    estimates[0]=point
    for start in range(0,draws,batch):
        size=min(batch,draws-start)
        w=rng.multinomial(len(owners),weights,size=size).T
        n=np.ascontiguousarray((counts@w).T)
        s=np.ascontiguousarray((success@w).T)
        estimates[start+1:start+1+size]=fit_batch(X,n,s)
    return estimates


def pooled(items):
    """Median of items within each diary, followed by the median across diaries."""
    diaries=[]
    for vectors in items:
        if vectors:
            diaries.append(np.median(np.stack(vectors),axis=0))
    if not diaries:
        return None
    distribution=np.median(np.stack(diaries),axis=0)
    if not np.isfinite(distribution).all():
        return None
    lower,upper=np.quantile(distribution[1:],[.025,.975])
    return float(distribution[0]),float(lower),float(upper)


def direction(estimate):
    if estimate is None:
        return 0
    return int(estimate[1]>0)-int(estimate[2]<0)
