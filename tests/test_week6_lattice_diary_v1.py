import numpy as np
import pytest
from scipy.optimize import minimize
from scipy.special import expit
from runners.drive.cards import week6_lattice_diary_v1 as m


def fixture():
    rng = np.random.default_rng(739)
    x = np.column_stack([np.ones(1000), rng.normal(size=(1000, 2))])
    y = rng.binomial(1, expit(x @ np.array([-.4, .7, -.25])))
    return x, y


def test_unpenalized_logit_matches_independent_optimizer():
    x,y=fixture()
    b=m.logit_fit(x,y)
    f=lambda z: np.sum(np.logaddexp(0,x@z)-y*(x@z))
    g=lambda z: x.T@(expit(x@z)-y)
    other=minimize(f, np.zeros(3), jac=g, method='BFGS', options={'gtol':1e-7})
    assert np.max(np.abs(g(other.x))) < 1e-5
    assert np.allclose(b,other.x,atol=1e-7,rtol=0)


def test_weighted_fit_equals_literal_whole_person_replication():
    x,y=fixture(); people=np.repeat(np.arange(100),10)
    w=m.person_draw(people,source_seed=20261119,draw=8)
    repeated=np.repeat(np.arange(len(x)),w)
    assert np.allclose(m.logit_fit(x,y,w),m.logit_fit(x[repeated],y[repeated]),atol=1e-9,rtol=0)


@pytest.mark.parametrize('case', ['separated','one_class','rank','nonfinite','nonconverged'])
def test_invalid_fit_is_not_a_null(case):
    x,y=fixture()
    opts={}
    if case=='separated': y=(x[:,1]>0).astype(int)
    if case=='one_class': y=np.zeros(len(x))
    if case=='rank': x=np.column_stack([x,x[:,1]])
    if case=='nonfinite': x[0,1]=np.nan
    if case=='nonconverged': opts['max_iter']=1
    with pytest.raises(m.InvalidFit): m.logit_fit(x,y,**opts)


def test_within_scale_and_draw_are_order_invariant():
    ids=np.repeat(np.arange(20),4)
    v=np.random.default_rng(3).normal(size=(80,2))+ids[:,None]
    a,means,scales=m.within(v,ids)
    assert np.allclose(a.reshape(20,4,2).mean(axis=1),0,atol=1e-14)
    assert np.allclose(np.mean(a*a,axis=0),1)
    w=m.person_draw(ids,source_seed=2,draw=9)
    order=np.random.default_rng(7).permutation(80)
    assert np.array_equal(w[order],m.person_draw(ids[order],source_seed=2,draw=9))
    with pytest.raises(m.InvalidFit): m.within(v,ids,np.arange(80)+1)


def test_linear_weighted_known_answer():
    x,_=fixture(); truth=np.array([.2,.4,-.3]); y=x@truth
    assert np.allclose(m.linear_fit(x,y),truth,atol=1e-12,rtol=0)
