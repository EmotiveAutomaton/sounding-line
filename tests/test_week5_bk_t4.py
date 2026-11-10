import copy
import numpy as np
import pytest
from runners.drive.cards import week5_bk_t4 as t4
from runners.drive.cards.week5_bk_t4_fixture import fixture_bundle, checks


def test_resampling_and_choice_blind_calibration():
    assert all(checks().values())


def test_padding_and_test_values_do_not_set_training_scale():
    p=fixture_bundle()['packed']
    for half in ('train','test'):
        p[half]=copy.deepcopy(p[half]);p[half]['mask']=(np.arange(5)[None,:]<np.full((36,1),2)).tolist();p[half]['y']=[0]*36
        p[half]['x']=np.zeros((36,5,5)).tolist()
    p['test']['x']=np.where(np.asarray(p['test']['mask'])[:,:,None],1e6,0)*np.ones((36,5,5))
    a=t4.resample(p,[0,1,2])
    assert np.all(a['train']['x']==0)
    assert np.all(a['test']['x'][~a['test']['mask']]==0)


def test_complete_reduction_refuses_missing_uncertainty():
    with pytest.raises(ValueError,match='Missing uncertainty'):
        t4.reduce_values({},[dict(binding='a',kind='bootstrap',records=[])],2000)


def test_reference_never_selects_padding():
    p=fixture_bundle()['packed']
    p['train']=copy.deepcopy(p['train']);p['test']=copy.deepcopy(p['test'])
    for h in ('train','test'):
        p[h]['mask']=(np.arange(5)[None,:] < np.tile([1,2,3],12)[:,None]).tolist()
        p[h]['y']=np.tile([0,1,5],12).tolist()
    b=fixture_bundle();b['packed']=p
    result=t4.draw(b,'reference',0)
    assert np.isfinite(result['gain'])
