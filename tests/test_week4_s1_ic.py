import numpy as np
import pytest
from runners.drive.cards import week4_s1_ic as m

def test_exact_planted_histories_and_complete_gate():
    assert all(m.checks().values())

def test_coupled_worlds_preserve_source_and_equal_lengths():
    a,proof=m.world(20261102,0.);b,other=m.world(20261102,.2)
    assert proof==other
    assert all(x['nuisance']==y['nuisance'] and x['label']==y['label'] for x,y in zip(a,b))
    assert all(y['outcome']>=x['outcome'] for x,y in zip(a,b))
    assert all(x['outcome']==y['outcome'] for x,y in zip(a,b) if x['label']==0)

def test_count_uncertainty_does_not_collapse_at_boundaries():
    assert m.wilson(0,20)[1]>0 and m.wilson(20,20)[0]<1
    with pytest.raises(ValueError):m.wilson(0,0)

def test_actual_native_interface_and_tamper_refusal(tmp_path):
    c=m.configuration('constructed');m.execute(tmp_path,{},c)
    assert m.verify(tmp_path,{},c)['complete_statistical_replay']
    (tmp_path/'SUMMARY.json').write_text('{}')
    with pytest.raises(ValueError,match='replay'):m.verify(tmp_path,{},c)
