import numpy as np
import pytest
from runners.drive.cards import week4_wd1_calibration_h3 as m
from tests.test_week4_wd1_calibration_h2 import near


def test_zero_columns_have_exact_zero_optimum_and_full_certificate():
    rng=np.random.default_rng(38);a=np.c_[np.ones(500),rng.normal(size=(500,5))]
    x=np.c_[a,np.zeros((500,70))];y=(rng.random(500)<m.original.expit(a[:,1]-.2)).astype(float)
    before=m.original.logistic_fit(x,y);after=m.logistic_fit(x,y)
    np.testing.assert_allclose(after,before,atol=1e-11,rtol=1e-11)
    np.testing.assert_array_equal(after[6:],0.)
    assert np.max(np.abs(m.original.logistic_objective(x,y,after)[1]))<=.001


def test_tiny_nonzero_columns_are_kept_and_intercept_unpenalized():
    rng=np.random.default_rng(13);x=np.c_[np.ones(600),rng.normal(size=600),rng.normal(size=600)*1e-12,np.zeros(600)]
    y=(rng.random(600)<.7).astype(float)
    np.testing.assert_allclose(m.logistic_fit(x,y),m.original.logistic_fit(x,y),atol=1e-11,rtol=1e-11)
    x=np.c_[np.ones(1000),np.zeros((1000,8))];y=np.r_[np.ones(700),np.zeros(300)]
    assert m.logistic_fit(x,y)[0]==pytest.approx(np.log(7/3),abs=1e-8)


def test_complete_population_and_profiles_match_all_constructed_families():
    for family in m.base.FAMILIES:
        sessions,rows,scalar,embedding,_=m.base.world(family,20261104,6,16)
        for assignment in ({},m.original.permute_sessions(sessions,20261105)):
            a=m.original.evaluate(sessions,rows,scalar,embedding,assignment,dict(seed=20261104,pca_dimensions=16))
            b=m.evaluate(sessions,rows,scalar,embedding,assignment,dict(seed=20261104,pca_dimensions=16))
            # Floating reduction ordering can move last bits but never the
            # original gradient tolerance; comparisons are much tighter.
            def compare(x,y):
                if isinstance(x,float):assert x==pytest.approx(y,abs=1e-9,rel=1e-9)
                elif isinstance(x,dict):
                    assert set(x)==set(y)
                    for k in x:compare(x[k],y[k])
                elif isinstance(x,list):
                    assert len(x)==len(y)
                    for u,v in zip(x,y):compare(u,v)
                else:assert x==y
            compare(a,b)


def test_native_full_prefix_and_fresh_replay(tmp_path):
    cfg=m.configuration('constructed');r=m.execute(tmp_path,{},cfg)
    assert r['worlds']==4 and not r['calibration']['complete']
    assert m.verify(tmp_path,{},cfg)['full_fresh_calibration_refit']
    assert r['source_sha256']==m.base.filehash(m.__file__)


def test_invalid_design_and_certificate_still_refused():
    with pytest.raises(ValueError):m.logistic_fit(np.ones((12,2)),np.ones(12))
    with pytest.raises(ValueError):m.logistic_fit(np.full((12,2),np.nan),np.arange(12)%2)
