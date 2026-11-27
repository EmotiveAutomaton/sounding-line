"""DRV1. Acceleration in falling standing and current anxiety versus sadness.

DESIGN CHECK (2026-11-27). Lessons read: LESSONS §§2–5 and the original
answered-prompt clock contract. Gates, null/alternative/direction: under
the null the paired difference of equal feelings is exactly zero. Under the
alternative a planted acceleration effect on anxiety alone is positive.
The failure direction is a spurious triple across days or missing scales.
Verdict bands per arm, exhaustive: both intervals positive supports the
registered direction; both negative are against. Insufficient support,
a missing binding or disagreement in sign or clarity cannot support a verdict.
"""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from runners.stage14.common import filehash,freeze,read
from . import week8_cluster_ols as model
from . import week7_answered_v1 as clock
from . import es_clock_v1

ROOT=Path(__file__).resolve().parents[3]
PREVIOUS=ROOT/'.agent-state/drive-20261115/week7-phase0/TRX1_KEY_EVIDENCE.json'
UNIT='DRV1-two-status-diaries'
MEMBERS=('0056','0057')
FEELINGS=('superior','anxious','sad')
ITEMS=['interaction',*[context+'_'+k for context in ('int','occup') for k in FEELINGS]]

def sources():
    root=Path(read(ROOT/'.agent-state/data_collection_root.json')['root'])
    evidence=read(PREVIOUS)['members']
    for m in MEMBERS:
        base=root/'open'/('openesm-'+m)
        filename=m+'_ryvkina_ts.tsv'
        yield m,base/'raw'/filename,evidence[m]['sources'][filename],base/'DOCUMENTED_METADATA.json'

def design(unit):
    if unit!=UNIT:
        raise ValueError('Unknown status-diary study')
    pins={}
    inputs=[PREVIOUS,ROOT/'docs/design/stage-15/week8/DRV1.md',ROOT/'docs/design/stage-15/week7/ANSWERED_PROMPTS.md',
            Path(clock.__file__),Path(es_clock_v1.__file__),Path(model.__file__)]
    for _,path,digest,meta in sources():
        inputs.extend([path,meta])
        pins[str(path)]=digest
    return dict(inputs=inputs,expected=pins,peak=.65,cap=20000,operations=['execute','verify'],source='Original Ryvkina status diaries 0056 and 0057')

def upper(values,q):
    ok=values.dropna()
    if not len(ok):
        return pd.Series(np.nan,index=values.index),None,None
    cut=float(np.quantile(ok,q,method='inverted_cdf'))
    code=(values>=cut).astype(float).where(values.notna())
    return code,cut,float(code.mean())

def construct(frame,timing,cap):
    f=frame.loc[timing.index].copy()
    context=pd.to_numeric(f.interaction,errors='coerce')
    for k in FEELINGS:
        yes=pd.to_numeric(f['int_'+k],errors='coerce')
        no=pd.to_numeric(f['occup_'+k],errors='coerce')
        values=yes.where(context.eq(1),no.where(context.eq(2)))
        f[k]=values.where(values.isin(range(1,7)))
    f['anxiety_high'],cut_a,share_a=upper(f.anxious,.7)
    f['sadness_high'],cut_s,share_s=upper(f.sad,.75)
    s=f.superior
    fall=s.shift()-s
    previous=s.shift(2)-s.shift()
    gap=timing.gap
    linked=gap.gt(0)&gap.shift().gt(0)
    eligible=linked&fall.gt(0)&previous.notna()
    f['acceleration']=(fall>previous).astype(float)
    f['level']=s
    f['fall']=fall
    f['short']=(gap.le(cap)&gap.shift().le(cap)) if cap is not None else False
    return f.loc[eligible],dict(valid_anxiety=int(f.anxious.count()),valid_sadness=int(f.sad.count()),
            anxiety_cut=cut_a,sadness_cut=cut_s,anxiety_share=share_a,sadness_share=share_s,
            consecutive_triples=int(linked.sum()),falling_triples=int(eligible.sum()))

def evaluate(frame,summary,roster,seed,boot=2000):
    if not len(roster):
        return dict(status='void',reason='No eligible people',support=summary)
    w=model.draws(len(roster),seed,boot)
    result={}
    for label,t in [('all',frame),('short',frame[frame.short])]:
        t=t.dropna(subset=['anxiety_high','sadness_high'])
        x=t[['acceleration','level','fall']]
        diff=t.anxiety_high-t.sadness_high
        slopes,support=model.fit(x,diff,t.id,t.id,roster,w,[[1,0,0]])
        component={}
        for col in ('anxiety_high','sadness_high'):
            z,_=model.fit(x,t[col],t.id,t.id,roster,w,[[1,0,0]])
            component[col]=model.summary(z[:,0])
        result[label]=dict(primary=model.summary(slopes[:,0]),components=component,support=support)
    primary=result['all']['primary']
    match=clock.reading(primary,result['short']['primary'])
    status='undecided'
    if min(r['support']['clusters_with_variation'] for r in result.values())<20:
        status='below floor descriptive'
    elif match=='consistent' and primary['interval'] is not None:
        if primary['interval'][0]>0:status='predicted direction'
        if primary['interval'][1]<0:status='against'
    return dict(status=status,agreement=match,readings=result,thresholds=summary,draws=boot)

def fixture():
    rng=np.random.default_rng(310)
    parts=[]
    for i in range(32):
        n=48
        s=rng.integers(1,7,n)
        fall=np.r_[np.nan,s[:-1]-s[1:]]
        accel=fall>np.roll(fall,1)
        t=pd.DataFrame(dict(id=i,interaction=1,int_superior=s,int_anxious=np.where(accel,6,1),
            int_sad=rng.integers(1,7,n),occup_superior=np.nan,occup_anxious=np.nan,occup_sad=np.nan))
        parts.append(t)
    f=pd.concat(parts,ignore_index=True)
    timing=pd.DataFrame({'gap':np.where(np.arange(len(f))%48==0,np.nan,60.)},index=f.index)
    a,defs=construct(f,timing,120.)
    r=evaluate(a,defs,sorted(f.id.unique()),193,boot=80)
    assert r['readings']['all']['primary']['interval'][0]>.5 and r['status']=='predicted direction'
    a['sadness_high']=a['anxiety_high']
    zero=evaluate(a,defs,sorted(f.id.unique()),193,boot=30)
    assert zero['readings']['all']['primary']['interval']==[0.,0.]
    # Break standing at the middle occasion. Removing its value never shifts neighbors together.
    t=f.iloc[:8].copy()
    t['int_superior']=[5,4,np.nan,3,2,5,3,2]
    g=timing.iloc[:8].copy()
    g['gap']=[np.nan,20,20,20,20,np.nan,170,20]
    valid,_=construct(t,g,75)
    assert set(valid.index)=={7} and not valid.short.any()
    return dict(identical_feelings_exact_zero=True,planted_acceleration=True,missing_no_bridge=True,
                day_boundary=True,both_gaps_capped=True,ties_preserved=True)

def run(unit,d,mode):
    results={}
    for i,(member,path,_,meta) in enumerate(sources()):
        dictionary={r['name']:r for r in read(meta)['features']}
        if any(k not in dictionary for k in ITEMS) or any(str(dictionary[k].get('answer_categories'))!='6' for k in ITEMS[1:]):
            results[member]=dict(status='void',reason='Registered context or six-point item did not bind')
            continue
        timing,support=clock.chronology(pd.read_csv(path,sep='\t',usecols=clock.CLOCKS,dtype={'id':str},low_memory=False))
        frame=pd.read_csv(path,sep='\t',usecols=['id',*ITEMS],dtype={'id':str},low_memory=False)
        rows,defs=construct(frame,timing,support['cap_minutes'])
        value=evaluate(rows,defs,sorted(timing.id.unique()),2026112748+i)
        results[member]=dict(clock=support,**value)
    freeze(d/(mode+'_STATUS_DIARIES.json'),results)

def check(unit,d):
    paths=[d/(mode+'_STATUS_DIARIES.json') for mode in ('execute','verify')]
    if read(paths[0])!=read(paths[1]):
        raise ValueError('Independent diary replay differs')
    return {p.name:filehash(p) for p in paths}
