import numpy as np
import pytest
from runners.drive.cards import week4_t4_variable as v
from runners.drive.cards import week4_t4_choice as b

def test_compact_mask_gradient_and_invariance():
    assert all(v.known_answers().values())

def test_no_mask_fit_matches_original():
    rng=np.random.default_rng(7);data=dict(x=rng.normal(size=(60,3,5)),z=rng.normal(size=(60,2)),w=np.arange(60)%3,y=np.arange(60)%4)
    for individual in (False,True):
        assert v.fit(data,individual)==b.fit(data,individual)

def test_invalid_mask_and_changed_output_refuse(tmp_path):
    data=dict(x=np.zeros((4,3,5)),z=np.zeros((4,2)),w=np.arange(4),y=np.zeros(4,dtype=int),mask=np.zeros((4,3),bool))
    with pytest.raises(ValueError,match='mask'):v.checked(data)
    c=v.configuration('constructed');v.execute(tmp_path,{},c);assert v.verify(tmp_path,{},c)['complete_fitted_replay']
    (tmp_path/'SUMMARY.json').write_text('{}')
    with pytest.raises(ValueError,match='replay'):v.verify(tmp_path,{},c)
