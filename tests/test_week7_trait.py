import sys
from pathlib import Path
from types import ModuleType
from hashlib import sha256
from zipfile import ZipFile
import numpy as np
import pandas as pd
import pytest
from runners.drive.cards import week7_trait_v1 as study


@pytest.mark.parametrize('world',['Q0','Q0F','Q1','Q1F','QN','QC'])
def test_packet_trait_operator(monkeypatch,world):
    archive=Path('.agent-state/drive-20261115/lattice-20261120/intake/received-at-root/PREFLIGHT_2026-11-22.zip')
    assert sha256(archive.read_bytes()).hexdigest()=='87bdb419bf581e68ca29045e217a57450e4e323df32874f11126dfde22115e1d'
    with ZipFile(archive) as z:
        for name in ('pf_slopes','pf_trait'):
            entry,=[p for p in z.namelist() if p.endswith('/'+name+'.py')]
            mod=ModuleType(name)
            mod.__file__=entry
            monkeypatch.setitem(sys.modules,name,mod)
            exec(compile(z.read(entry),entry,'exec'),mod.__dict__)
    mod.NBOOT=20
    expected=mod.one_rep(np.random.default_rng(41),80,30,.28,world,2)['ADJ']
    tr,x,y=mod.generate(np.random.default_rng(41),80,30,.28,world)
    halves=[mod.half_stats(x[:,t],y[:,t]) for t in (slice(None,30),slice(30,None))]
    for half in halves:
        half['b']=np.where((half['n1']>=2)&(half['n0']>=2),half['b'],np.nan)
    w=np.ones((1,len(tr)))
    assert study.effect(tr,halves,w)[0]==pytest.approx(expected,abs=1e-11)
    assert np.isnan(study.effect(np.ones_like(tr),halves,w)[0])


def test_period_cut_support_and_replay():
    f=pd.DataFrame({'id':np.repeat(['a','b','c','d'],16),'day':np.tile(np.repeat([1,2],8),4),
        'study_period':0,'pleasantness':np.tile([-3,-3,0,1,1,1,2,3],8)})
    for k in study.FEELINGS[:-1]:f[k]=1+(np.arange(len(f))%6)
    # Move one person's first-half observations out of the baseline;
    # a different participant lacks the trait.
    f.loc[:7,'study_period']=1
    f.loc[16,'day']=np.nan
    traits=pd.DataFrame({'id':['a','b','c','d'],'neuroticism':[3,4,np.nan,5]})
    s,halves,report=study.parts(f,traits)
    rs,again,replay=study.parts(f,traits,True)
    assert report==replay and report['cutoff']==0 and report['undated_prompts']==1
    assert report['missing_trait_people']==1 and report['feelings']['sad']['supported_people']==2
    for side,other in zip(halves['sad'],again['sad']):
        for field in side:np.testing.assert_allclose(side[field],other[field],equal_nan=True)
    with pytest.raises(ValueError,match='one trait record'):
        study.parts(f,pd.concat([traits,traits.iloc[:1]]))
