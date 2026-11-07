import numpy as np
import pytest
from runners.theory_days.word_followups import deletion_curve,axes_diagnostic,fixtures,execute,verify

def test_signed_literal_cases():
    r=fixtures()
    assert r['increasing']['against_fraction']==0
    assert r['reversed']['against_fraction']==1
    assert r['same']['arousal_minus_joy_order_rho']==0
    assert r['opposite']['arousal_minus_joy_order_rho']==-2

def test_deletion_new_adjacency_and_floor():
    x=[0,3,2,1,4];r=deletion_curve(x,np.arange(5),np.arange(5))
    assert r['baseline']['inversions']==2
    assert [v['inversions'] for v in r['variants']]==[2,1,1,1,2]
    assert all(v['covered']==4 for v in r['variants'])
    with pytest.raises(ValueError):deletion_curve([0]*4,[0]*4,[0]*4)

def test_ties_constants_and_missing():
    r=axes_diagnostic([0,1,2,3],[0,0,1,1],[1,1,1,1])
    assert r['pairs']['joy__arousal']['tied']==2
    assert r['pairs']['joy__arousal']['concordant']==4
    assert r['pairs']['joy__dominance']['rho'] is None
    assert r['pairs']['joy__dominance']['tied']==6
    assert axes_diagnostic([0,1,2,3],[0,1,2,np.nan],[0,1,2,3])['status']=='design cannot test'
    z=deletion_curve([1]*5,[1]*5,[1]*5)
    assert z['counts']['design cannot test']==5

def test_handler_reentry(tmp_path):
    config=dict(constructed=True)
    execute(tmp_path,{},config);before=(tmp_path/'DIAGNOSTIC.json').read_bytes()
    execute(tmp_path,{},config);assert verify(tmp_path,{},config)['complete_recalculation']
    assert (tmp_path/'DIAGNOSTIC.json').read_bytes()==before
