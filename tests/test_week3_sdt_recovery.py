"""Unchanged ridge objective, original certificate, and fresh whole-card replay."""
import json
from pathlib import Path
import numpy as np
import pytest
from scipy.special import expit
from runners.drive.cards import week3_sdt as original
from runners.drive.cards import week3_sdt_newton as card
from tests.test_week3_sdt import fixture


def test_derivatives_and_hessian_have_independent_finite_difference_answers():
    rng=np.random.default_rng(31); x=np.c_[np.ones(100),rng.normal(size=(100,4))]
    y=rng.integers(0,2,100); beta=rng.normal(size=5); eps=1e-5
    value,g,h=card.logistic_objective(x,y,beta)
    numerical_g=[]; numerical_h=[]
    for j in range(5):
        shift=np.eye(5)[j]*eps
        plus=card.logistic_objective(x,y,beta+shift); minus=card.logistic_objective(x,y,beta-shift)
        numerical_g.append((plus[0]-minus[0])/(2*eps))
        numerical_h.append((plus[1]-minus[1])/(2*eps))
    np.testing.assert_allclose(g,numerical_g,atol=1e-7)
    np.testing.assert_allclose(h,np.array(numerical_h).T,atol=1e-7)
    assert np.linalg.eigvalsh(h).min()>0


def test_known_constant_probability_and_zero_slopes():
    x=np.c_[np.ones(1000),np.zeros((1000,3))]; y=np.r_[np.ones(700),np.zeros(300)]
    beta,certificate=card.logistic_fit_with_certificate(x,y)
    assert beta[0]==pytest.approx(np.log(7/3),abs=1e-8)
    np.testing.assert_array_equal(beta[1:],0.)
    assert certificate['final_absolute_gradient_max']<=.001


def test_large_collinear_design_retains_original_gradient_limit():
    rng=np.random.default_rng(13); z=rng.normal(size=(8000,5))
    x=np.c_[np.ones(len(z)),z,np.repeat(z[:,:1],30,axis=1)]
    y=(rng.random(len(z))<expit(.2+.7*z[:,0]-.4*z[:,1])).astype(float)
    beta,c=card.logistic_fit_with_certificate(x,y)
    assert c['same_objective_and_penalty'] and c['certificate_limit']==.001
    assert np.max(np.abs(card.logistic_objective(x,y,beta)[1]))<=.001
    assert abs(beta[0]-.2)<.1
    assert abs(beta[1]+beta[6:].sum()-.7)<.1


def test_original_and_recovery_agree_on_supported_reference(tmp_path):
    inputs=fixture(tmp_path); raw=json.loads(Path(inputs['sessions']).read_text())
    sessions,rows,scalar,embedding=card.population_features(raw,json.loads(Path(inputs['records']).read_text()),np.load(inputs['vectors']))
    a,truth,_=original.reference_scores(sessions,rows,scalar,embedding,{},dimensions=2)
    b,other,_=card.reference_scores(sessions,rows,scalar,embedding,{},dimensions=2)
    np.testing.assert_allclose(a,b,atol=2e-5)
    np.testing.assert_array_equal(truth,other)


def test_recovery_actual_handler_fresh_replay_and_source_binding(tmp_path):
    inputs=fixture(tmp_path/'input'); output=tmp_path/'output'
    config=dict(mode='fixture',permutation_draws=2,bootstrap_draws=4,pca_dimensions=2)
    report=card.execute(output,inputs,config)
    assert report['future_own_history_used'] is False
    assert 'original gradient certificate' in report['engineering_recovery']
    assert card.verify(output,inputs,config)['verified']
    assert card.execute(output,inputs,config)==report
    binding=json.loads((output/'BINDINGS.json').read_text())
    assert binding['original_source_sha256'] != binding['source_sha256']


def test_failed_certificate_and_degenerate_reference_are_not_accepted():
    with pytest.raises(ValueError,match='mixed binary'):
        card.logistic_fit(np.ones((12,2)),np.ones(12))
    with pytest.raises(ValueError,match='invalid reference'):
        card.logistic_fit(np.full((12,2),np.nan),np.arange(12)%2)
