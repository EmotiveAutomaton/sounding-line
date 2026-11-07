import copy
import itertools
import numpy as np
import pytest
from runners.theory_days import moral_components as m

def test_every_binary_pattern_and_paired_algebra():
    a=np.array(list(itertools.product([0,1],repeat=4)))
    _,v=m.vectors(a)
    for row,pair in zip(a,v):
        baseline=(row[2]+row[3])/2
        assert tuple(pair)==(row[0]-baseline,row[1]-baseline)
        assert pair.mean()==(row[0]+row[1]-row[2]-row[3])/2

def test_signed_null_and_opposing_components():
    r=m.fixtures()
    assert r['opposing']['original_subset_difference']==0
    assert r['opposing']['components']['Species']['verdict']=='supports'
    assert r['opposing']['components']['Intervention']['verdict']=='against'
    ci=r['zero']['components']['Species']['interval']
    expected=2*np.sqrt(np.log(80)/(2*1200))
    assert ci==pytest.approx([-expected,expected])

def test_joint_bootstrap_tails_against_direct_binary_counts():
    # One independent binary group indicator: literal Binomial bootstrap is exact.
    a=np.r_[np.tile([0,1,0,0],(400,1)),np.tile([1,0,0,0],(800,1))]
    r=m.summarize(a,2000);rng=np.random.default_rng(20261106)
    weights=rng.multinomial(1200,[1/3,2/3],size=2000)
    for name,col in [('Species',1),('Intervention',0)]:
        ci=np.quantile(weights[:,col]/1200,[.0125,.9875])
        assert r['components'][name]['interval']==pytest.approx(ci)
    assert r['compression_classes']==2

def test_parent_and_invalid_support_refusal():
    a=np.tile([1,0,1,0],(1200,1));r=m.summarize(a,64)
    p=dict(common_fingerprints=1200,equal_exposure_rates=r['original_subset_rates'],primary=dict(difference=0))
    m.check_parent(r,p)
    bad=copy.deepcopy(p);bad['equal_exposure_rates']['Species']=0
    with pytest.raises(AssertionError):m.check_parent(r,bad)
    with pytest.raises(ValueError):m.summarize(np.tile([.5,0,0,0],(1200,1)))
    assert m.summarize(a[:999])['status']=='design cannot test'

def test_actual_handler_replay_and_immutable_reentry(tmp_path):
    m.execute(tmp_path,{},dict(constructed=True))
    assert m.verify(tmp_path,{},dict(constructed=True))['complete_recalculation']
    before=(tmp_path/'SCIENCE.json').read_bytes()
    m.execute(tmp_path,{},dict(constructed=True))
    assert (tmp_path/'SCIENCE.json').read_bytes()==before
