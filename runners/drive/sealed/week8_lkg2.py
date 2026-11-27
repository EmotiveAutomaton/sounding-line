"""Reciprocal conversation trait and standing comparisons on fixed survey fields."""
import numpy as np
import pandas as pd
from independent_release import Entry,decide
from runners.drive.cards.week6_sealed_support_v1 import SealedFailure,write_tables
from runners.drive.sealed import week8_lkg1 as liking
from runners.drive.sealed.week6_sc1_counts_v1 import source_layout

TRAITS=('extraversion','agreeable','conscientious','neurotic','open')
STATUS=('you_think_my_status','i_think_your_status')
RATINGS=[prefix+t for prefix in ('my_','your_') for t in TRAITS]
EXTRA=[*RATINGS,*STATUS]


def fields(root,config):
    import pyarrow.parquet as pq
    df=liking.read_frame(root,config['pin'])
    layout=source_layout(root,{'survey':config['pin']})
    with pq.ParquetFile(layout/config['pin'][0]) as survey:
        present=[k for k in EXTRA if survey.schema_arrow.names.count(k)==1]
        extra=survey.read(columns=liking.IDS+present,use_threads=False).to_pandas()
    keys=liking.IDS
    if not df[keys].equals(extra[keys]):
        raise SealedFailure(22,'Extra and original keys differ')
    counts=config['trait_counts']
    earlier=[]
    for k in EXTRA:
        if k not in present:
            df[k]=np.nan
            continue
        group=frozenset(extra.loc[extra[k].notna(),'user_id'])
        if k in counts:
            if len(group)!=counts[k]:
                raise SealedFailure(14,'Survey field support differs')
            earlier.append(group)
        v=pd.to_numeric(extra[k],errors='coerce')
        clean=(v.isna() & extra[k].isna()) | v.between(1,10 if k in STATUS else 5)
        if k in STATUS:
            clean &= v.isna() | v.mod(1).eq(0)
        df[k]=v if clean.all() else np.nan
    return df,earlier


def analyze(df,known,extra_known,draws):
    panel,universe,previous=liking.project(df,known)
    own=df[['conversation_id','user_id','partner_id','you_think_my_status',*['my_'+t for t in TRAITS]]]
    other=df[['conversation_id','user_id','partner_id','i_think_your_status',*['your_'+t for t in TRAITS]]]
    traits=own.merge(other,left_on=['conversation_id','user_id','partner_id'],right_on=['conversation_id','partner_id','user_id'],
                     suffixes=('_self','_partner'),validate='one_to_one')
    traits=traits.rename(columns={'conversation_id':'conversation','user_id_self':'person'})
    rows=panel[['conversation','person','G']].merge(traits,on=['conversation','person'],validate='one_to_one')
    rows['standing']=rows['you_think_my_status']-rows['i_think_your_status']
    for prefix in ('my_','your_'):
        rows[prefix+'neurotic']=6-rows[prefix+'neurotic']
    means=rows.groupby('person',sort=True)[['G','standing',*RATINGS]].mean()
    tables=[]
    def emit(code,values,ids):
        v=np.concatenate(values)
        if len(ids)<11 or len(v)!=draws+1 or not np.isfinite(v).all():
            return
        lo,hi=np.quantile(v[1:],[.025,.975])
        tables.append(Entry(dict(measure=code,estimate=float(v[0]),lower=float(lo),upper=float(hi),n=len(ids)),frozenset(ids)))
    def correlation(code,field):
        pairs=means[['G',field]].dropna()
        if len(pairs)<11:return
        x,y=pairs.to_numpy().T
        values=[]
        with np.errstate(divide='ignore',invalid='ignore'):
            for w in liking.weights(len(x),draws,2026112712+code):
                values.append(liking.wcov(w,x,y)/np.sqrt(liking.wcov(w,x,x)*liking.wcov(w,y,y)))
        emit(code,values,pairs.index)
    for code,field in enumerate(RATINGS,1):
        correlation(code,field)
    single=rows.dropna(subset=['standing']).groupby('person').standing.agg(['count','sum',lambda x:x@x])
    if len(single)>=11:
        n,s,_=single.to_numpy().T
        emit(11,[(w@s)/(w@n) for w in liking.weights(len(n),draws,2026112724)],single.index)
    repeats=single.loc[single['count']>=2]
    if len(repeats)>=20:
        n,s,ss=repeats.to_numpy().T
        with np.errstate(divide='ignore',invalid='ignore'):
            vals=[liking.icc(w,n,s,ss) for w in liking.weights(len(n),draws,2026112725)]
        emit(12,vals,repeats.index)
    correlation(13,'standing')
    result,_=decide([(1,'comparisons',tables)],universe,[*previous,*extra_known])
    if not result:raise SealedFailure(12,'No eligible releasable comparison')
    return result


def run(root,out,config):
    def read_once():
        df,prior=fields(root,config)
        return analyze(df,config['previous'],prior,config['draws'])
    first=read_once()
    if first!=read_once():raise SealedFailure(14,'Independent source replay differs')
    write_tables(out,first)
