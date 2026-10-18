"""Trial-level crossed response-scale random effects for D15/V3.

DESIGN CHECK: LESSONS 3-5 read 2026-10-18. Centered quadratic moments have
expectation linear in the variance components, including at zero. Independent
trial noise must recover zero-centered unconstrained writer variance; planted
writer offsets must recover their variance. Nonnegative moment fitting permits
an exact zero boundary. Constant and aliased components are diagnosed from the
design before outcomes; unresolved aliasing invalidates separation, not science.
These Gaussian second-moment models of one-hot responses are not multinomial
likelihoods, latent-logit ICCs, or calibrated probability forecasts.
"""
from __future__ import annotations
import numpy as np
from scipy.optimize import nnls
from scipy import sparse
from scipy.sparse.linalg import spsolve


def encode(labels):
    names=sorted(set(labels));lookup={v:i for i,v in enumerate(names)}
    return np.asarray([lookup[v] for v in labels],int),names


def components(groups):
    """tr(P K_j P K_k), using contingency counts rather than N-square matrices."""
    groups=[np.asarray(g,int) for g in groups];n=len(groups[0]);counts=[]
    if n<3 or any(len(g)!=n or g.min()<0 for g in groups):raise ValueError('unsupported crossed design')
    for g in groups:counts.append(np.bincount(g))
    a=np.zeros((len(groups)+1,len(groups)+1))
    for j,g in enumerate(groups):
        cj=counts[j];nj=float(cj@cj)
        a[j,-1]=a[-1,j]=n-nj/n
        for k,h in enumerate(groups[:j+1]):
            ck=counts[k];nk=float(ck@ck)
            pair,c=np.unique(g*len(ck)+h,return_counts=True);c=c.astype(float)
            value=c@c-2*np.sum(c*cj[pair//len(ck)]*ck[pair%len(ck)])/n+nj*nk/n**2
            a[j,k]=a[k,j]=value
    a[-1,-1]=n-1
    return a,counts


def fit(y,groups,names):
    y=np.asarray(y,float)
    if y.ndim==1:y=y[:,None]
    if not np.isfinite(y).all() or len(groups)!=len(names):raise ValueError('invalid crossed observations')
    a,counts=components(groups);active=[i for i in range(len(groups)) if a[i,i]>1e-9]
    dropped=[names[i] for i in range(len(groups)) if i not in active]
    keep=active+[len(groups)];matrix=a[np.ix_(keep,keep)]
    norm=np.sqrt(np.diag(matrix));scaled=matrix/norm[:,None]/norm[None,:]
    condition=float(np.linalg.cond(scaled))
    if not np.isfinite(condition) or condition>1e10:raise ValueError('aliased crossed variance components')
    centered=y-y.mean(axis=0);quadratic=[]
    for i in active:
        sums=np.zeros((len(counts[i]),y.shape[1]));np.add.at(sums,groups[i],centered)
        quadratic.append(np.sum(sums*sums,axis=0))
    quadratic=np.vstack(quadratic+[np.sum(centered*centered,axis=0)])
    unconstrained=np.linalg.solve(matrix,quadratic)
    constrained=np.column_stack([nnls(matrix/norm[:,None],q/norm)[0] for q in quadratic.T])
    variances=np.zeros((len(groups)+1,y.shape[1]));raw=variances.copy()
    variances[keep]=constrained;raw[keep]=unconstrained
    return dict(variance=variances,unconstrained=raw,means=y.mean(axis=0),condition=condition,
                structural_constants=dropped,moment_matrix=a,quadratic=quadratic,active=active)


def blup(y,groups,result):
    """Best linear unbiased predictions conditional on the fitted components."""
    y=np.asarray(y,float)
    if y.ndim==1:y=y[:,None]
    n=len(y);sizes=[int(np.max(g))+1 for g in groups]
    z=sparse.hstack([sparse.csr_matrix((np.ones(n),(np.arange(n),g)),shape=(n,size))
                     for g,size in zip(groups,sizes)],format='csr')
    design=sparse.hstack((np.ones((n,1)),z),format='csc');cross=(design.T@design).tocsc()
    estimates=[];intercepts=[]
    for column in range(y.shape[1]):
        variance=result['variance'][:,column];residual=variance[-1]
        if not np.any(y[:,column]!=y[0,column]):
            intercepts.append(float(y[0,column]));estimates.append(np.zeros(sum(sizes)));continue
        if residual<=1e-12*max(1.,float(variance.sum())):raise ValueError('degenerate zero residual variance')
        repeated=np.repeat(variance[:-1],sizes);active=np.r_[True,repeated>1e-12]
        penalty=np.r_[0.,residual/repeated[repeated>1e-12]]
        system=cross[active][:,active]+sparse.diags(penalty)
        rhs=np.asarray(design[:,active].T@y[:,column]).ravel()
        answer=spsolve(system,rhs);gap=float(np.max(np.abs(system@answer-rhs)))
        if not np.isfinite(answer).all() or gap>1e-7*max(1.,float(np.max(np.abs(rhs)))):
            raise ValueError('uncertified crossed BLUP solve')
        full=np.zeros(1+sum(sizes));full[active]=answer
        intercepts.append(float(full[0]));estimates.append(full[1:])
    matrix=np.column_stack(estimates);cuts=np.cumsum([0]+sizes)
    return dict(intercepts=intercepts,effects=[matrix[cuts[i]:cuts[i+1]] for i in range(len(sizes))])


def icc(result):
    # Conditional on the observed prompts: prompt main effects are held fixed.
    # Writer-by-prompt variation remains within-person variation across prompts.
    values=result['variance'];numerator=values[0]
    denominator=values.sum(axis=0)-values[1]
    per_feature=np.divide(numerator,denominator,out=np.full_like(numerator,np.nan),where=denominator>0)
    trace=float(numerator.sum()/denominator.sum()) if denominator.sum()>0 else None
    return trace,per_feature


def decisions_for_reliability(value):
    if value is None or not np.isfinite(value) or value<0 or value>1: return None
    return None if value==0 else float(4*(1-value)/value)
