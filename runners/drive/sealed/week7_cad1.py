"""CAD1. Registered enjoyment and pace controls across a speaker's conversations."""
from collections import defaultdict
from pathlib import Path
import re

import numpy as np
import pandas as pd
from runners.drive.cards.week6_sealed_support_v1 import SealedFailure, write_tables
from runners.drive.sealed.week6_sc1_counts_v1 import source_layout, Unavailable
from runners.drive.sealed.week6_sc2_source_v1 import PINS, finite, key, seconds_union


ENJOY='how_enjoyable'
MAIN=(ENJOY,'arousal','pre_affect','partner_rate')
EXPANDED=(*MAIN,'overall_affect','i_like_you','my_partner_paid_attention_to_me')
SURVEY=('conversation_id','user_id','partner_id',*(k for k in EXPANDED if k!='partner_rate'))
COLUMNS={'survey':SURVEY,'clock':('conversation_id','ceil_recording_end_second'),
         'speech':('conversation_id','turn_id','speaker','start','stop','utterance')}
WORDS=re.compile(r"[^\W_]+(?:['’][^\W_]+)*",re.UNICODE)


def rates(turns, people, duration):
    if len(turns)<3 or turns.turn_id.isna().any() or turns.turn_id.duplicated().any():
        return {}
    turns=turns.sort_values('turn_id').iloc[1:-1]
    spans=defaultdict(list)
    counts=defaultdict(int)
    for row in turns.itertuples():
        if (row.speaker not in people or not finite(row.start) or not finite(row.stop)
                or not 0<=row.start<row.stop<=duration or not isinstance(row.utterance,str)):
            return {}
        spans[row.speaker].append((row.start,row.stop))
        counts[row.speaker]+=len(WORDS.findall(re.sub(r'\[[^\]]*\]',' ',row.utterance)))
    return {p:counts[p]/seconds_union(v) for p,v in spans.items() if seconds_union(v)>0}


def project(survey,clock,speech):
    by_turn=speech.groupby('conversation_id',sort=False)
    by_clock=clock.groupby('conversation_id',sort=False)
    records=[]
    for conversation,dyad in survey.groupby('conversation_id',sort=False):
        if not key(conversation) or len(dyad)!=2 or conversation not in by_clock.groups or conversation not in by_turn.groups:
            continue
        a,b=dyad.itertuples(index=False)
        if (not key(a.user_id) or not key(b.user_id) or a.user_id==b.user_id
                or a.partner_id!=b.user_id or b.partner_id!=a.user_id):
            continue
        duration=by_clock.get_group(conversation).ceil_recording_end_second
        if len(duration)!=1 or not finite(duration.iloc[0]) or duration.iloc[0]<=0:
            continue
        pace=rates(by_turn.get_group(conversation),{a.user_id,b.user_id},duration.iloc[0])
        if len(pace)!=2:
            continue
        for response in (a,b):
            record={k:getattr(response,k) for k in SURVEY if k!='partner_id'}
            record.update(own_rate=pace[response.user_id],partner_rate=pace[response.partner_id])
            records.append(record)
    return pd.DataFrame.from_records(records,columns=['conversation_id','user_id','own_rate',*EXPANDED])


def within(panel, weights):
    person,conversation,values=panel
    w=weights[conversation]
    totals=np.bincount(person,weights=w,minlength=person.max()+1)
    counts=np.bincount(person,weights=(w>0),minlength=len(totals))
    valid=(w>0)&(counts[person]>=2)
    if not valid.any():
        return np.nan
    means=np.column_stack([np.bincount(person,weights=w*col,minlength=len(totals))
                           /np.maximum(1,totals) for col in values.T])
    centered=(values[valid]-means[person[valid]])*np.sqrt(w[valid,None])
    X=centered[:,1:]
    beta,_,rank,_=np.linalg.lstsq(X,centered[:,0],rcond=1e-9)
    return float(beta[0]) if rank==X.shape[1] else np.nan


def score(frame, draws=2000):
    if frame.duplicated(['user_id','conversation_id']).any():
        raise ValueError('repeated speaker conversation')
    all_people=set(frame.user_id)
    if len(all_people)<11:
        raise SealedFailure(12,'insufficient speakers')
    roster=sorted(set(frame.conversation_id))
    panels=[]
    groups=[]
    for reading,cols in enumerate((MAIN,EXPANDED),1):
        complete=frame.dropna(subset=['own_rate',*cols])
        n_conv=complete.groupby('user_id').conversation_id.nunique()
        single=set(n_conv.index[n_conv.eq(1)])
        use=complete[complete.user_id.isin(n_conv.index[n_conv.ge(2)])]
        people=set(use.user_id)
        groups.append((people,single))
        vals=use[['own_rate',*cols]].to_numpy(float)
        if not np.isfinite(vals).all():
            raise ValueError('invalid numeric response')
        panels.append((pd.Categorical(use.user_id).codes.astype(int),
                       pd.Categorical(use.conversation_id,categories=roster).codes,vals))
    # Counts and estimates from both models can be combined externally. Only
    # disclose a new membership when all intersections and complements are safe.
    protected=[]
    def may_disclose(group):
        if len(group)<11:return False
        memberships=[*protected,group]
        counts=defaultdict(int)
        for p in all_people:counts[tuple(p in g for g in memberships)]+=1
        if min(counts.values())<11:return False
        protected.append(group)
        return True
    estimates=[];support=[]
    accepted=[may_disclose(group) for group,_ in groups]
    for reading,((people,single),allowed) in enumerate(zip(groups,accepted),1):
        if allowed:support.append(dict(reading=reading,kind=1,n=len(people)))
        if may_disclose(single):support.append(dict(reading=reading,kind=2,n=len(single)))
    rng=np.random.default_rng(2026112201)
    bank=[[],[]]
    for j in range(draws+1):
        weights=np.ones(len(roster),int) if j==0 else np.bincount(rng.integers(len(roster),size=len(roster)),minlength=len(roster))
        for i,(panel,allow) in enumerate(zip(panels,accepted)):
            if allow:bank[i].append(within(panel,weights))
    for i,values in enumerate(bank):
        if values and np.isfinite(values).all():
            lo,hi=np.quantile(values[1:],[.025,.975])
            estimates.append(dict(reading=i+1,estimate=values[0],lower=lo,upper=hi,n=len(groups[i][0])))
    return {'pace':estimates,'support':support}


def run(root,out,pins=PINS,draws=2000):
    import pyarrow.parquet as pq
    base=source_layout(Path(root),pins)
    tables={}
    for name,cols in COLUMNS.items():
        path=base/pins[name][0]
        with pq.ParquetFile(path) as file:
            available=file.schema_arrow.names
            required=set(cols)
            if name=='survey':
                required-=set(EXPANDED[len(MAIN):])
            if any(available.count(k)!=1 for k in required):
                raise Unavailable(22)
            selected=[k for k in cols if k in available]
            if any(available.count(k)!=1 for k in selected):raise Unavailable(22)
            frame=file.read(columns=selected,use_threads=False).to_pandas()
            tables[name]=frame.reindex(columns=cols)
    return write_tables(out,score(project(**tables),draws))
