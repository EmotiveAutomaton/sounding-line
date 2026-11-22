"""Phase 0 constructed qualification for four CL operators.

DESIGN CHECK (LESSONS 3–5). These functions consume numeric arrays. Known
answers and direct comparisons to the supplied scripts exercise both
directions, unidentified designs, skewed item responses and weak separation.
"""
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit, logit, ndtr
from scipy.sparse.csgraph import connected_components
from scipy.stats import rankdata, norm


def rebound(person, current, previous, play, weights=None):
    """Person-centred play on current stress and the two directions of change."""
    p,s,prev,y=map(np.asarray,(person,current,previous,play))
    ok=np.isfinite(s)&np.isfinite(prev)&np.isfinite(y)
    p,s,prev,y=p[ok],s[ok],prev[ok],y[ok]
    d=prev-s
    X=np.column_stack((s,np.maximum(d,0),np.maximum(-d,0)))
    z=np.column_stack((X,y)).astype(float)
    for k in np.unique(p):
        idx=p==k
        z[idx]-=z[idx].mean(axis=0)
    w=np.ones(len(p)) if weights is None else np.asarray(weights)[p]
    X=z[:,:3]*np.sqrt(w)[:,None]
    if not len(X) or np.linalg.matrix_rank(X)<3:return None
    return np.linalg.lstsq(X,z[:,3]*np.sqrt(w),rcond=None)[0]


def refusal(counts,cuts=None):
    """Observed refusal, excess and top-bin dip for one item's ordered log-price bins."""
    counts=np.asarray(counts,float)
    if counts.ndim!=1 or len(counts)<4 or not np.isfinite(counts).all() or min(counts)<0:
        raise ValueError('Expected finite nonnegative bin counts followed by refusals')
    if counts.sum()==0:return None
    price=counts[:-1]
    if np.count_nonzero(price)<2:return None
    cuts=np.arange(len(price))+.5 if cuts is None else np.asarray(cuts,float)
    if len(cuts)!=len(price) or not np.isfinite(cuts).all() or np.any(np.diff(cuts)<=0):
        raise ValueError('Bind the ordered log-price upper edges, including the censoring cut')
    shares=counts/counts.sum()
    def nll(theta):
        F=ndtr((cuts-theta[0])/np.exp(theta[1]))
        conditional=np.diff(np.r_[0.,F])/max(F[-1],1e-300)
        return -float(price@np.log(np.maximum(conditional,1e-300)))/price.sum()
    mids=cuts-.5*np.median(np.diff(cuts))
    mean=np.average(mids,weights=price)
    sd=max(np.sqrt(np.average((mids-mean)**2,weights=price)),.1)
    fit=minimize(nll,[mean,np.log(sd)],method='Nelder-Mead',
                 options={'maxiter':900,'xatol':1e-8,'fatol':1e-11})
    if not fit.success:return None
    below=ndtr((cuts[-1]-fit.x[0])/np.exp(fit.x[1]))
    if below<=0:return None
    excess=shares[-1]-(1-shares[-1])*(1-below)/below
    return shares[-1],float(excess),float(shares[-2]-min(shares[-1],shares[-3]))


def choice_product(rater,yes,reason,gate,weights=None,rank_normal=False):
    """Return the logistic product coefficient with both squared ratings held."""
    ids,y,r,g=map(np.asarray,(rater,yes,reason,gate))
    _,ids=np.unique(ids,return_inverse=True)
    if not len(y) or not np.isin(y,(0,1)).all() or not np.isfinite([r,g]).all():
        raise ValueError('Expected matched finite choice ratings')
    def center(values):
        v=np.asarray(values,float).copy()
        for k in np.unique(ids):
            mask=ids==k
            if rank_normal:v[mask]=norm.ppf((rankdata(v[mask])-.5)/mask.sum())
            v[mask]-=v[mask].mean()
        return v
    R,G=center(r),center(g)
    n=np.bincount(ids)[ids]
    yes_rate=(np.bincount(ids,weights=y)[ids]-y+.5)/n
    X=np.column_stack((np.ones(len(y)),R,G,R*G,logit(yes_rate),R**2,G**2))
    w=np.ones(len(y)) if weights is None else np.asarray(weights)[ids]
    if np.linalg.matrix_rank(X[w>0])!=X.shape[1]:return None
    beta=np.zeros(X.shape[1])
    for _ in range(60):
        p=expit(X@beta)
        info=X.T@((w*p*(1-p))[:,None]*X)
        if np.linalg.matrix_rank(info)!=len(beta):return None
        step=np.linalg.solve(info,X.T@(w*(y-p)))
        beta+=np.clip(step,-2.,2.)
        if np.max(abs(step))<1e-7:return float(beta[3])
    return None


def merge_components(mixture):
    """Join modes connected by midpoint densities at or above the 0.8 bar."""
    centers=mixture.means_
    peaks=mixture.score_samples(centers)
    graph=np.eye(len(centers),dtype=bool)
    for i,center in enumerate(centers):
        if i+1>=len(centers):break
        mid=mixture.score_samples((centers[i+1:]+center)/2)
        joined=mid-np.minimum(peaks[i],peaks[i+1:])>=np.log(.8)
        graph[i,i+1:]=joined
        graph[i+1:,i]=joined
    count,labels=connected_components(graph,directed=False)
    return labels,int(count)
