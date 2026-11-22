"""Paired purpose-in-life trajectory for a reviewed three-wave projection."""
from pathlib import Path
import numpy as np
import pandas as pd

from runners.drive.cards.week6_sealed_support_v1 import SealedFailure, write_tables


def projected(waves, items):
    if len(waves)!=3 or len(set(items))!=len(items) or not items:
        raise ValueError('three editions and common scored items required')
    scores=[]
    for i, frame in enumerate(waves):
        if frame.person.isna().any() or frame.person.duplicated().any():
            raise ValueError('ambiguous cross-wave key')
        frame=frame.set_index('person')
        if not set(items)<=set(frame):
            raise ValueError('common purpose item missing')
        values=frame[list(items)].apply(pd.to_numeric,errors='raise')
        if np.isinf(values.to_numpy(float)).any():
            raise ValueError('invalid purpose value')
        scores.append(values.mean(axis=1,skipna=False).rename('wave'+str(i+1)))
    follow=waves[1].set_index('person')
    if not follow.role_loss.dropna().isin([0,1]).all():
        raise ValueError('invalid role-loss flag')
    cohort=pd.concat([*scores,follow.role_loss,follow.family],axis=1,join='inner')
    return cohort.loc[cohort.role_loss.eq(1)].dropna(subset=['wave1','wave2','wave3'])


def trajectory(waves, items, draws=2000):
    cohort=projected(waves,items)
    n=len(cohort)
    if n<11 or cohort.family.isna().any():
        raise SealedFailure(12,'insufficient linked family roster')
    values=cohort[['wave1','wave2','wave3']].to_numpy(float)
    _,family=np.unique(cohort.family.to_numpy(),return_inverse=True)
    groups=int(max(family))+1
    rng=np.random.default_rng(2026112202)
    def stats(w):
        count=w.sum()
        means=np.average(values,weights=w,axis=0)
        sd=np.sqrt(np.sum(w*(values[:,0]-means[0])**2)/(count-1)) if count>1 else np.nan
        return [*means,(means[2]-means[0])/sd if sd>0 else np.nan]
    point=stats(np.ones(n))
    bank=np.array([stats(np.bincount(rng.integers(groups,size=groups),minlength=groups)[family])
                   for _ in range(draws)])
    rows=[]
    for i,estimate in enumerate(point):
        if np.isfinite(estimate) and np.isfinite(bank[:,i]).all():
            lower,upper=np.quantile(bank[:,i],[.025,.975])
            rows.append(dict(measure=i+1,estimate=estimate,lower=lower,upper=upper,n=n))
    return rows


def rehearse(root, out, items, draws=2000):
    """Local projection fixture only. No original mount is bound to these columns."""
    waves=[pd.read_csv(Path(root)/f'made_wave_{i}.csv') for i in (1,2,3)]
    return write_tables(out,{'purpose':trajectory(waves,items,draws)})
