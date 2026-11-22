"""Reconcile stored aggregates with each bootstrap fit's own covariances."""
import numpy as np
from . import week6_person_slopes_v1 as bn
from . import week6_person_ladder_v1 as ladder


def adjustment(W, halves, spread):
    a,b=halves
    pair=lambda key:(a[key],b[key])
    X=[pair('L')]+([pair('S')] if spread else [])
    raw, adjusted, beta=bn.adjust(W,pair('b'),X)
    ll=bn.cc(W,pair('L'),pair('L'))
    full=np.zeros(len(W),bool)
    if spread:
        ls=bn.cc(W,pair('L'),pair('S'))
        ss=bn.cc(W,pair('S'),pair('S'))
        mat=np.stack([ll,ls,ls,ss],-1).reshape(-1,2,2)
        full=np.linalg.eigvalsh(mat)[:,0]>bn.EPS
    bare=(~full)&(ll<=bn.EPS)
    assert np.all(beta[bare]==0) and np.allclose(raw[bare],adjusted[bare])
    if spread:assert np.all(beta[~full,1]==0)
    np.testing.assert_allclose(ll, np.sum(W*(a['L']-bn.wmean(W,a['L'])[:,None])*(b['L']-bn.wmean(W,b['L'])[:,None]),axis=1)/W.sum(1),rtol=1e-12,atol=1e-12)
    return raw,adjusted,ll,~full,bare


def reconcile(parts,seed):
    valid=np.isfinite(parts[0]['b'])&np.isfinite(parts[1]['b'])
    a,b=ladder.supported(parts,valid)
    w=np.minimum(a['n1'],b['n1'])
    spread=bn.wpearson(w,a['S'],b['S'])>=.30
    rng=np.random.default_rng(seed)
    chunks=[]
    for start in range(0,2001,50):
        count=min(50,2001-start)
        W=bn.boot_counts(rng,len(w),count-(start==0))*w
        if start==0:W=np.vstack([w,W])
        chunks.append(np.column_stack(adjustment(W,(a,b),spread)))
    raw,adjusted,ll,dropped,bare=np.concatenate(chunks).T
    return dict(people=len(w),raw=ladder.stat(raw[0],raw[1:]),adjusted=ladder.stat(adjusted[0],adjusted[1:]),
                level_covariance=ladder.stat(ll[0],ll[1:]),spread_dropped=float(dropped[1:].mean()),unadjusted=float(bare[1:].mean()))
