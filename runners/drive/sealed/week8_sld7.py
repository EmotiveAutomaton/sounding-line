"""Purpose changes after becoming married. Family and age weights stay in the seal."""
import numpy as np
from independent_release import Entry,decide
from runners.drive.cards.week6_sealed_support_v1 import SealedFailure,write_tables
from runners.drive.sealed import week8_sld5 as loss
from runners.drive.sealed.r48_forms import choose


def one(frames,config):
    obs,old,comp,later=loss.membership(frames,config['known'])
    previous=list(old.values())
    lost={1:old[1,1],2:old[2,1],3:old[3,1],4:later}
    for label,n in config['loss_counts'].items():
        group=lost[int(label)]
        if len(group)!=n:raise SealedFailure(14,'Previously released loss membership differs')
        bands=set(obs.loc[list(group),'age']//10)
        subset=frozenset(p for p in comp if obs.at[p,'age']//10 in bands)
        previous.extend([group,comp,subset])
    clock=loss.old.month_index
    dates=[clock(frame[p+'YR'],frame[p+'MO']).reindex(obs.index) for p,frame in zip(('A1PI_','B1PIDATE_','C1PIDATE_'),frames)]
    valid=dates[0].lt(dates[1]) & dates[1].lt(dates[2]) & obs[['p0','p1','p2','family','age']].notna().all(axis=1)
    valid &= obs[['s0','s1','s2']].isin(range(1,6)).all(axis=1)
    married=obs[['s0','s1','s2']].eq(1)
    gains=frozenset(obs.index[valid & ~married.s0 & married.s1 & married.s2])
    if len(gains)<11:raise SealedFailure(12,'Gain unavailable')
    age=obs.loc[list(gains),'age']
    control=frozenset(obs.index[valid & ~married.any(axis=1) & obs.age.between(age.min(),age.max())])
    bands=set(age//10)
    positive=frozenset(p for p in control if obs.at[p,'age']//10 in bands)
    defined,_=decide([(1,'purpose',[Entry(dict(n=len(gains)),gains,(control,positive))])],frozenset(frames[0].index),previous)
    if not defined:raise SealedFailure(12,'New rosters withheld')
    result=loss.estimates(obs,gains,control,loss.PAIRS,config['draws'])
    if not result:raise SealedFailure(12,'No defined comparison')
    entries=[Entry(r,gains,(control,positive)) for r in result]
    primary=[e for e in entries if e.fields['form']==1]
    pooled=[e for e in primary if e.fields['transition']==2]
    return choose({'fine':[(1,'purpose',entries)],
                   'coarse':[(1,'purpose',primary)],
                   'summary':[(1,'purpose',pooled)] if pooled else []},
                  frozenset(frames[0].index),previous)


def run(root,out,config):
    data=one(loss.load(root,config['files']),config)
    if data!=one(loss.load(root,config['files']),config):
        raise SealedFailure(14,'Independent source replay differs')
    write_tables(out,data)
