"""TWO3. Describe lagged feelings between two partners on the same diary occasion.

DESIGN CHECK (2026-11-27). Lessons read: LESSONS §§2–5. Gates,
null/alternative/direction: under the null of identical four partner slopes
the same-minus-other contrast is zero. Under the alternative a planted own
and same-partner contribution is recovered with both directions kept in the
same resampling cluster. The failure direction is a false lag from a missing
occasion, an ambiguous partner or a duplicated report.
Verdict bands per arm, exhaustive: estimable differences are descriptive,
non-identifiable contrasts are void and under 20 couples are below floor.
"""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from runners.stage14.common import filehash, freeze, read
from . import week8_cluster_ols as model

ROOT=Path(__file__).resolve().parents[3]
PREVIOUS=ROOT/'.agent-state/drive-20261115/week7-phase1'
NATIVE=PREVIOUS.parent/'lattice-20261119/fixture-reader-native'
sys.path.append(str(NATIVE))
import pyreadstat

UNIT='TWO3-original-paired-occasions'
FEELINGS=('angr','down','disa','nerv')
KEYS=['couple','id','trial']
NAME='ESM data_disclosing daily hassles.sav'

def source():
    root=Path(read(ROOT/'.agent-state/data_collection_root.json')['root'])/'open/couples-daily-hassles'
    note=PREVIOUS/'ADM_couples-daily-hassles_METADATA.json'
    record=read(note)
    item=record['files'][NAME]
    for k in [*KEYS,*FEELINGS]:
        if not item['fields'].get(k):
            raise ValueError('Couple, occasion or feeling missing in dictionary')
    return root/'raw'/NAME,note,{root/'SOURCE.json':record['manifest'],root/'SCHEMA.json':record['schema'],root/'raw'/NAME:item['sha256']}

def design(unit):
    if unit!=UNIT:
        raise ValueError('Unrecognized couples unit')
    _,note,pins=source()
    return dict(inputs=[note,*pins,Path(model.__file__),Path(pyreadstat.__file__),ROOT/'docs/design/stage-15/week8/TWO3.md'],
                expected={str(k):v for k,v in pins.items()},peak=.55,cap=20000,operations=['execute','verify'],
                source='Disclosing Daily Hassles original couples experience-sampling survey')

def align(frame):
    f=frame.copy()
    for key in KEYS:
        v=pd.to_numeric(f[key],errors='coerce')
        f[key]=v.where(np.isfinite(v)&(v==np.floor(v)))
    missing=f[KEYS].isna().any(axis=1)
    f=f.loc[~missing].copy()
    memberships=f[['couple','id']].drop_duplicates()
    valid=memberships.groupby('couple').id.size().eq(2)
    # A participant identifier must resolve to only one dyad.
    repeated=memberships.id.duplicated(keep=False)
    valid.loc[memberships.loc[repeated,'couple'].unique()]=False
    f=f.loc[f.couple.isin(valid[valid].index)].copy()
    dup=f.duplicated(KEYS,keep=False)
    duplicate_rows=int(dup.sum())
    f=f.loc[~dup].copy()
    for k in FEELINGS:
        f[k]=pd.to_numeric(f[k],errors='coerce').where(lambda v:v.isin(range(7)))
    memo=memberships.loc[memberships.couple.isin(valid[valid].index)].sort_values(['couple','id']).copy()
    memo['partner']=memo.groupby('couple').id.transform(lambda a:a.iloc[::-1].to_numpy())
    current=f.merge(memo,on=['couple','id'],validate='many_to_one')
    prior=f.rename(columns={k:'own_'+k for k in FEELINGS}).copy()
    prior['trial']+=1
    match=current.merge(prior,on=KEYS,validate='one_to_one')
    other=prior.rename(columns={'id':'partner',**{'own_'+k:'partner_'+k for k in FEELINGS}})
    match=match.merge(other,on=['couple','partner','trial'],validate='one_to_one').sort_values(KEYS)
    return match,dict(original_reports=len(frame),missing_keys=int(missing.sum()),couples_with_ambiguous_roster=int((~valid).sum()),
                      removed_duplicate_rows=duplicate_rows,eligible_couples=int(valid.sum()),linked_directions=len(match))

def analyze(frame,seed=2026112738,boot=2000):
    joined,structure=align(frame)
    roster=sorted(joined.couple.unique())
    results={}
    if not roster:
        return dict(status='No aligned occasions',structure=structure,comparisons=results)
    weights=model.draws(len(roster),seed,boot)
    for i,k in enumerate(FEELINGS):
        fields=['own_'+k,*['partner_'+j for j in FEELINGS]]
        same=np.eye(5)[i+1]
        cross=(np.array([0.,1.,1.,1.,1.])-same)/3.
        contrasts=[same,cross,same-cross,*np.eye(5)]
        estimates,n=model.fit(joined[fields],joined[k],joined.id,joined.couple,roster,weights,contrasts)
        labels=['partner_same','partner_other_mean','same_minus_other',*fields]
        results[k]=dict(support=n,scope='below floor descriptive' if n['clusters_with_variation']<20 else 'descriptive',
                        comparisons={label:model.summary(estimates[:,j]) for j,label in enumerate(labels)})
    return dict(structure=structure,draws=boot,comparisons=results)

def fixture():
    rng=np.random.default_rng(1938);records=[]
    for couple in range(32):
        last=rng.integers(0,7,(2,4))
        for t in range(1,12):
            next_values=last[::-1] if t%2==0 else rng.integers(0,7,(2,4))
            for i in range(2):
                records.append([couple,2*couple+i,t,*next_values[i]])
            last=next_values
    f=pd.DataFrame(records,columns=[*KEYS,*FEELINGS])
    test=analyze(f,boot=80)
    assert all(r['comparisons']['same_minus_other']['interval'][0]>.25 for r in test['comparisons'].values())
    tiny=f[f.couple==0].copy()
    tiny=tiny[~((tiny.id==1)&(tiny.trial==4))]
    joined,_=align(pd.concat([tiny,tiny[(tiny.id==0)&(tiny.trial==7)]]))
    assert not joined.trial.isin([5,8]).any() and not ((joined.id==0)&(joined.trial==7)).any()
    no_pair,_=align(tiny[tiny.id==0])
    assert no_pair.empty
    v=np.arange(12.)
    beta,_=model.fit(np.column_stack((v,v)),v,np.zeros(12),np.zeros(12),[0],np.ones((2,1)),[[1,-1],[1,1]])
    np.testing.assert_allclose(beta[:,1],1)
    assert np.isnan(beta[:,0]).all()
    return dict(planted_same_above_other=True,missing_and_duplicate_never_bridged=True,partner_unique=True,
                both_directions_one_cluster=True,unidentified_contrast_withheld=True)

def run(unit,d,mode):
    path,_,_=source()
    frame,_=pyreadstat.read_sav(str(path),usecols=[*KEYS,*FEELINGS],user_missing=False)
    freeze(d/(mode+'_COUPLES.json'),analyze(frame))

def check(unit,d):
    outputs=[d/(mode+'_COUPLES.json') for mode in ('execute','verify')]
    if read(outputs[0])!=read(outputs[1]):
        raise ValueError('Independent original-file couples replay differs')
    return {p.name:filehash(p) for p in outputs}
