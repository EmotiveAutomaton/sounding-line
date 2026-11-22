"""Mood before and after a conversation, with conversation-level resampling."""
import numpy as np
import pandas as pd

from runners.drive.cards.week6_sealed_support_v1 import SealedFailure, write_tables


def projection(frame, marked, reward_kind=False):
    needed=['conversation','speaker','pre_affect','affect']
    if marked:
        needed+=['minutes','reward_count' if reward_kind else 'laugh_count']
    else:
        # A separate codebook-verified projection must orient the comparative
        # survey response toward the respondent. It is never divided by time.
        needed+=['reported_own_relative_laughter']
    data=frame[needed].copy()
    if data[['conversation','speaker']].isna().any().any() or data.duplicated(['conversation','speaker']).any():
        raise ValueError('ambiguous conversation roster')
    if not data.groupby('conversation').speaker.nunique().eq(2).all():
        raise ValueError('incomplete dyad')
    if marked:
        counts=data[needed[-1]]
        if (counts.dropna()<0).any() or (counts.dropna()%1!=0).any():
            raise ValueError('invalid marked count')
        if (data.minutes.dropna()<=0).any():raise ValueError('invalid exposure')
        data['measure']=counts/data.minutes
    else:data['measure']=data.reported_own_relative_laughter
    numeric=['pre_affect','affect','measure']
    if np.isinf(data[numeric].to_numpy(float)).any():raise ValueError('invalid response')
    complete=data[numeric].notna().all(axis=1)
    use=complete.groupby(data.conversation).transform('all')
    return data.loc[use,['conversation','speaker',*numeric]]


def coefficients(rows,weights):
    z=np.sqrt(weights)
    incoming=rows.pre_affect.to_numpy()
    laughter=rows.measure.to_numpy()
    out=[]
    # The reviewed projection orients both mood ratings toward pleasantness.
    # The first registered coefficient is per unit of incoming unpleasantness.
    for predictors,y in (([-incoming],laughter),([laughter,incoming],rows.affect.to_numpy())):
        x=np.column_stack((np.ones(len(rows)),*predictors))*z[:,None]
        b,_,rank,_=np.linalg.lstsq(x,y*z,rcond=1e-9)
        out.append(b[1] if rank==x.shape[1] else np.nan)
    return out


def run(frame,out,*,marked,reward_kind=False,draws=2000):
    rows=projection(frame,marked,reward_kind)
    n=rows.speaker.nunique()
    if n<11:raise SealedFailure(12,'insufficient matched people')
    rng=np.random.default_rng(2026112204)
    conv,inverse=np.unique(rows.conversation,return_inverse=True)
    point=coefficients(rows,np.ones(len(rows)))
    bank=np.array([coefficients(rows,np.bincount(rng.integers(len(conv),size=len(conv)),
                  minlength=len(conv))[inverse]) for _ in range(draws)])
    result=[]
    for i,v in enumerate(point):
        if np.isfinite(v) and np.isfinite(bank[:,i]).all():
            lo,hi=np.quantile(bank[:,i],[.025,.975])
            result.append(dict(comparison=i+1,source=2 if marked and reward_kind else int(marked),
                               estimate=v,lower=lo,upper=hi,n=n))
    return write_tables(out,{'mood':result,'support':[dict(conversations=len(conv),n=n)]})
