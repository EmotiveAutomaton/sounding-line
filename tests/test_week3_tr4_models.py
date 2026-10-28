import copy
import math

import numpy as np
import pytest
from runners.drive.cards import week3_tr4_models as m


def test_smoothed_shares_and_observation_are_analytic():
    value=[1,2,3,4];p=m.shares(value)
    assert np.allclose(p,np.array([1.5,2.5,3.5,4.5])/12)
    z,R=m.observation(value)
    assert np.allclose(z,np.log(np.array([2.5,3.5,4.5])/1.5))
    assert np.allclose(R,np.diag(1/np.array([2.5,3.5,4.5]))+np.ones((3,3))/1.5)
    assert np.linalg.eigvalsh(R).min()>0


@pytest.mark.parametrize('value',[[1,2,3],[-1,2,3,4],[1.,2.,3.,4.],[True,False,True,False],[1,2,3,math.inf]])
def test_invalid_counts_refuse(value):
    with pytest.raises(ValueError):m.counts(value)


def test_all_six_exact_uniform_null():
    result=m.forecast([[20,20,20,20]]*24)
    for row in result:
        for p in row['probabilities'].values():assert np.allclose(p,[.25]*4,rtol=0,atol=1e-14)
        assert row['q']==0 and row['trend_q']==0
    gains=[m.log_loss([20]*4,r['probabilities']['whole'])-m.log_loss([20]*4,r['probabilities']['kalman']) for r in result]
    assert gains==[0.]*24


def test_current_and_future_outcomes_cannot_change_a_forecast():
    sequence=[[2+i,8,3,1] for i in range(15)];changed=copy.deepcopy(sequence)
    changed[9:]=[[1,1,1,200]]*6
    a=m.forecast(sequence);b=m.forecast(changed)
    assert a[:10]==b[:10]
    assert a[10]!=b[10]


def test_last_whole_and_exponential_have_exact_known_updates():
    a=[10,1,2,3];b=[1,10,2,3];model=m.SixForecasts(.25,.05)
    model.update(a);model.update(b);pred,meta=model.predict()
    assert np.allclose(pred['whole'],(m.shares(a)+m.shares(b))/2)
    assert np.array_equal(pred['last'],m.shares(b))
    assert np.allclose(pred['exponential'],.75*m.shares(a)+.25*m.shares(b))
    assert meta['observed_sessions']==2


def test_gaussian_first_update_matches_direct_linear_algebra():
    value=[20,6,4,2];bank=m.GaussianBank(grid=(0.,.1));z,R=m.observation(value)
    prior=np.eye(3)*10;K=prior@np.linalg.inv(prior+R)
    expected_mean=K@z;expected_cov=(np.eye(3)-K)@prior
    bank.update(value)
    assert np.allclose(bank.mean,np.tile(expected_mean,(2,1)))
    assert np.allclose(bank.cov,np.tile(expected_cov,(2,1,1)))
    assert bank.likelihood[0]==bank.likelihood[1]
    _,q=bank.predict();assert q==0


def test_retained_grid_matches_separate_single_grid_filters():
    data=[[20,4,1,2],[2,20,1,4],[3,12,2,1],[6,1,2,15]]
    for trend in (False,True):
        bank=m.GaussianBank(trend);singles=[m.GaussianBank(trend,grid=(q,)) for q in m.Q_GRID]
        for value in data:
            bank.update(value)
            for one in singles:one.update(value)
            for i,one in enumerate(singles):
                assert np.allclose(bank.mean[i],one.mean[0])
                assert np.allclose(bank.cov[i],one.cov[0])
                assert np.isclose(bank.likelihood[i],one.likelihood[0])
            assert bank.predict()[1]==m.Q_GRID[int(np.argmax([s.likelihood[0] for s in singles]))]


def test_changepoint_zero_hazard_is_exact_pooled_dirichlet():
    model=m.ChangePoint(0);total=np.zeros(4)
    for value in [[3,4,1,8],[9,1,3,2],[1,5,7,3]]:
        assert np.allclose(model.predict(),(total+.5)/(total.sum()+2))
        model.update(value);total+=value
    assert len(model.log_weights)==4
    assert np.allclose(model.predict(),(total+.5)/(total.sum()+2))


def test_changepoint_certain_reset_is_prior_and_one_step_mixture_exact():
    value=[10,2,1,3]
    always=m.ChangePoint(1);always.update(value);assert np.array_equal(always.predict(),[.25]*4)
    model=m.ChangePoint(.2);model.update(value)
    assert np.allclose(model.predict(),.2*np.array([.25]*4)+.8*m.shares(value))


def test_missing_observation_is_not_an_invented_choice():
    model=m.SixForecasts(.1,.05);model.update([20,1,2,3])
    before,meta=model.predict();n=model.changepoint.alpha.copy()
    model.update([0,0,0,0]);after,later=model.predict()
    for key in ('whole','last','exponential','changepoint'):assert np.array_equal(before[key],after[key])
    assert later['observed_sessions']==meta['observed_sessions']==1
    assert np.array_equal(n,model.changepoint.alpha)
    assert model.kalman.steps==2
    assert m.log_loss([0]*4,[.25]*4) is None


def test_known_persistent_change_favors_adaptation_and_covariances_remain_valid():
    sequence=[[250,250,250,250]]*12+[[850,50,50,50]]*12
    result=m.forecast(sequence)
    gain=np.mean([m.log_loss(x,r['probabilities']['whole'])-m.log_loss(x,r['probabilities']['kalman']) for x,r in zip(sequence[16:],result[16:])])
    assert gain>0.05
    for trend in (False,True):
        bank=m.GaussianBank(trend)
        for value in sequence:
            bank.update(value)
            assert np.linalg.eigvalsh(bank.cov).min()>0


@pytest.mark.parametrize('p',[[0,.3,.3,.4],[.1,.2,.3,.3],[.25,.25,.25,float('nan')]])
def test_invalid_forecast_refuses(p):
    with pytest.raises(ValueError):m.log_loss([1]*4,p)


def test_log_loss_uses_raw_counts_not_smoothed_targets():
    assert m.log_loss([1,0,0,0],[.5,.25,.125,.125])==math.log(2)
