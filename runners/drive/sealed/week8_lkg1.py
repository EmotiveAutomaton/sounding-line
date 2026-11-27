"""Survey-only liking comparisons. All dyad links and memberships stay in the sealed job."""
from collections import Counter
from datetime import date, datetime
import re
from pathlib import Path
import numpy as np
import pandas as pd
from independent_release import Entry, decide
from runners.drive.cards.week6_sealed_support_v1 import SealedFailure, write_tables
from runners.drive.sealed.week6_sc1_counts_v1 import source_layout, Unavailable

IDS=['conversation_id','user_id','partner_id']
RATINGS=['i_like_you','you_like_me']
# Historical output memberships only. These fields never enter a new fit.
HISTORY=['technical_quality','laughter','affect','pre_affect','arousal','how_enjoyable','you_are_funny','i_think_your_status']
COLS=IDS+['date']+RATINGS+HISTORY
FIELDS={'i_like_you':7,'you_like_me':7,'laughter':9,'affect':9,'pre_affect':9,
        'how_enjoyable':9,'arousal':9}


def read_frame(root, pin):
    import pyarrow.parquet as pq
    try:
        base=source_layout(root,{'survey':pin})
    except Unavailable as err:
        raise SealedFailure(err.args[0],'Source binding failed') from None
    path=base/pin[0]
    if not path.is_file():
        raise SealedFailure(21,'Survey missing')
    with pq.ParquetFile(path) as src:
        if any(src.schema_arrow.names.count(k)!=1 for k in COLS):
            raise SealedFailure(22,'Column binding failed')
        tab=src.read(columns=COLS,use_threads=False)
    df=tab.to_pandas()
    for k,high in FIELDS.items():
        clean=[]
        for v in tab[k].to_pylist():
            if v is None:
                clean.append(np.nan)
                continue
            if isinstance(v,str) and re.fullmatch(r'[0-9]+(?:\.0+)?',v):
                v=float(v)
            if type(v) not in (int,float) or v not in range(1,high+1):
                raise SealedFailure(24,'Response domain failed')
            clean.append(float(v))
        df[k]=clean
    return df


def project(df,previous):
    if df[['conversation_id','user_id']].isna().any().any() or df.duplicated(['conversation_id','user_id']).any():
        raise SealedFailure(22,'Ambiguous roster')
    universe=frozenset(df.user_id)
    known=[]
    for k,n in previous['survey'].items():
        ids=frozenset(df.loc[df[k].notna(),'user_id'])
        if len(ids)!=n:
            raise SealedFailure(14,'Survey census mismatch')
        known.append(ids)
    # A matching upper bound identifies an earlier roster only when membership
    # in the original fit logically required every survey condition used here.
    valid=df.groupby('conversation_id').user_id.transform('nunique').eq(2)
    pair=df.loc[valid].merge(df.loc[valid],left_on=['conversation_id','partner_id'],
                             right_on=['conversation_id','user_id'],suffixes=('','_other'),validate='many_to_one')
    pair=pair.loc[pair.user_id.eq(pair.partner_id_other)&pair.user_id.ne(pair.partner_id)]
    both=lambda fields:pair[fields+[k+'_other' for k in fields]].notna().all(axis=1)
    for fields,observed in [(['laughter','pre_affect','affect'],previous['lgh2']),
                             (['you_are_funny','i_like_you','i_think_your_status'],previous['sc2'])]:
        upper=frozenset(pair.loc[both(fields),'user_id'])
        if len(upper)==observed:
            known.append(upper)
    primary=pair.dropna(subset=['how_enjoyable','pre_affect','arousal'])
    counts=primary.groupby('user_id').conversation_id.nunique()
    upper_all=frozenset(counts.index)
    upper_repeat=frozenset(counts.index[counts>=2])
    nr,ns=previous['cad1']
    if len(upper_repeat)==nr:
        known.append(upper_repeat)
        if len(upper_all)==nr+ns:
            known.append(upper_all-upper_repeat)
    panel=pair[['conversation_id','user_id','date','i_like_you','you_like_me','i_like_you_other']].copy()
    panel.columns=['conversation','person','date','L','M','R']
    panel['G']=panel.M-panel.R
    return panel,universe,known


def weights(n,draws,seed):
    rng=np.random.default_rng(seed)
    yield np.ones((1,n))
    for offset in range(0,draws,64):
        size=min(64,draws-offset)
        yield np.vstack([np.bincount(rng.integers(n,size=n),minlength=n) for _ in range(size)])


def icc(w,n,s,ss):
    total=w@n
    people=w.sum(axis=1)
    summed=(w*s).sum(axis=1)
    between=(w*s**2/n).sum(axis=1)
    msb=(between-summed**2/total)/(people-1)
    msw=((w*ss).sum(axis=1)-between)/(total-people)
    typical=(total-w@(n*n)/total)/(people-1)
    return (msb-msw)/(msb+(typical-1)*msw)


def wcov(w,x,y):
    return (w@(x*y))/w.sum(axis=1)-(w@x)*(w@y)/w.sum(axis=1)**2


def ordered_pair(df):
    def parse(v):
        if isinstance(v,(datetime,date,pd.Timestamp)):
            return pd.to_datetime(v,utc=True,errors='coerce')
        if isinstance(v,str) and re.fullmatch(r'\d{4}-\d\d-\d\d(?:[ T].*)?',v):
            return pd.to_datetime(v,utc=True,errors='coerce')
        return pd.NaT
    d=df.copy()
    d['time']=d.date.map(parse)
    d=d.sort_values(['person','time'])
    grp=d.groupby('person',sort=False)
    take=(grp.time.transform('count')==grp.time.transform('size')) & (grp.cumcount()<2)
    duplicated=d.duplicated(['person','time'],keep=False)
    bad=set(d.loc[take & duplicated,'person'])
    kept=d.loc[take & ~d.person.isin(bad)]
    return kept


def analyze(df,previous,draws=2000):
    panel,universe,known=project(df,previous)
    estimates=[]
    supports=[]
    def emit(code,arr,people):
        arr=np.asarray(arr)
        if len(people)<11 or arr.shape!=(draws+1,) or not np.isfinite(arr).all():return
        lo,hi=np.quantile(arr[1:],[.025,.975])
        estimates.append(Entry(dict(measure=code,estimate=arr[0],lower=lo,upper=hi,n=len(people)),people))
    complete=panel.dropna(subset=['G'])
    if not complete.empty:
        ids,idx=np.unique(complete.person,return_inverse=True)
        n=np.bincount(idx)
        sums=np.bincount(idx,weights=complete.G)
        vals=np.concatenate([(w@sums)/(w@n) for w in weights(len(ids),draws,2026112701)])
        emit(1,vals,frozenset(ids))
    allthree=panel.dropna(subset=['M','L','R'])
    multi=allthree.loc[allthree.groupby('person').conversation.transform('size')>=2]
    people=frozenset(multi.person)
    if len(people)>=11:
        supports.append(Entry(dict(measure=2,n=len(people)),people))
    if len(people)>=20:
        _,pid=np.unique(multi.person,return_inverse=True)
        n=np.bincount(pid)
        L,M,R=[multi[k].to_numpy(float) for k in ['L','M','R']]
        G=M-R
        totals=lambda v: np.bincount(pid,weights=v)
        gs,gss,ls,lss,cross,ds,dss=[totals(v) for v in (G,G**2,L,L**2,G*L,M-L,(M-L)**2)]
        bank=[[],[],[]]
        with np.errstate(invalid='ignore',divide='ignore'):
            for w in weights(len(n),draws,2026112702):
                obs=w@n
                a=(w@cross-(w@gs)*(w@ls)/obs)/(w@lss-(w@ls)**2/obs)
                bank[0].extend(icc(w,n,gs,gss))
                bank[1].extend(icc(w,n,gs-a[:,None]*ls,gss-2*a[:,None]*cross+a[:,None]**2*lss))
                bank[2].extend(icc(w,n,ds,dss))
        for code,arr in enumerate(bank,2):
            emit(code,arr,people)
        pair=ordered_pair(multi)
        actors=frozenset(pair.person)
        if len(actors)>=20:
            L,M,R,G=[pair[k].to_numpy(float).reshape(-1,2).T for k in ('L','M','R','G')]
            bank=[[] for _ in range(5)]
            with np.errstate(invalid='ignore',divide='ignore'):
                for w in weights(len(actors),draws,2026112705):
                    cgg=wcov(w,*G)
                    crr=wcov(w,*R)
                    cmr=(wcov(w,M[0],R[1])+wcov(w,M[1],R[0]))/2
                    cll=wcov(w,*L)
                    cml=(wcov(w,M[0],L[1])+wcov(w,M[1],L[0]))/2
                    bank[0].extend(cgg/np.sqrt(wcov(w,G[0],G[0])*wcov(w,G[1],G[1])))
                    bank[1].extend(crr)
                    for j,c in enumerate((.25,.5,.75),2):
                        bank[j].extend(cgg-cll+(1+c)*(cll-cml)-(cmr-crr)**2/crr)
            emit(5,bank[0],actors)
            emit(6,bank[1],actors)
            if np.isfinite(bank[1]).all() and np.quantile(bank[1][1:],.025)>0:
                for j in range(2,5):emit(j+5,bank[j],actors)
    result,_=decide([(1,'liking',estimates),(2,'support',supports)],universe,tuple(known))
    if not result:raise SealedFailure(12,'No disclosable eligible comparison')
    return result


def run(root,out,config):
    result=analyze(read_frame(root,config['pin']),config['previous'],config['draws'])
    if result!=analyze(read_frame(root,config['pin']),config['previous'],config['draws']):
        raise SealedFailure(14,'Independent replay differed')
    write_tables(out,result)
