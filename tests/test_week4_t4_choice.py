import numpy as np
import pytest
from runners.drive.cards import week4_t4_choice as c

def test_probability_gradient_and_dismissal_invariance():
    assert all(c.known_answers().values())

def test_bad_choices_refuse():
    data=dict(x=np.zeros((4,3,5)),z=np.zeros((4,2)),w=np.arange(4),y=np.full(4,4))
    with pytest.raises(ValueError,match='choice'):c.checked(data)

def test_projected_gradient_sign_and_native_replay(tmp_path):
    assert c.projected_gradient(np.array([-3.,3.]),np.array([1.,-1.]),[(-3.,3.)]*2)==0
    assert c.projected_gradient(np.array([-3.,3.]),np.array([-1.,1.]),[(-3.,3.)]*2)==1
    cfg=c.configuration('constructed');c.execute(tmp_path,{},cfg);assert c.verify(tmp_path,{},cfg)['complete_fitted_replay']
    (tmp_path/'SUMMARY.json').write_text('{}')
    with pytest.raises(ValueError,match='replay'):c.verify(tmp_path,{},cfg)
