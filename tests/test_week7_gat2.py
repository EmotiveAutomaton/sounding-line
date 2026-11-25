import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit

from runners.drive.cards.week7_gat2 import cohort, designs, disposition, fit, slope


def example():
    return pd.DataFrame(dict(iid=[1]*4, wave=[1]*4, order=[1,2,3,4], dec=[0,1,0,1],
        intel=[7,3,7,3], amb=[3,7,7,3], intel3_1=[5]*4, amb3_1=[5]*4))


def test_order_and_square():
    frame, counts = cohort(example())
    _, _, (main, intelligence, ambition) = designs(frame)
    np.testing.assert_allclose(main[:, 3], [-.25,-.25,.75,-.25])
    np.testing.assert_allclose(main[:, 2], main[:, 1]**2)
    np.testing.assert_allclose(intelligence[:, 3], [.5,-.5,.5,-.5])
    np.testing.assert_allclose(ambition[:, 3], [-.5,.5,.5,-.5])
    scaled = frame.copy()
    scaled[["intel", "intel3_1"]] = scaled[["intel", "intel3_1"]] / 2 + 1
    np.testing.assert_allclose(designs(scaled)[2][0], main)


def test_exclusions():
    f = example()
    frames = [f, f.assign(iid=2, amb=5), f.iloc[:1].assign(iid=3),
              f.assign(iid=4, intel3_1=[4,5,5,5]), f.assign(iid=5, dec=np.nan)]
    _, c = cohort(pd.concat(frames, ignore_index=True))
    assert c["analysed_raters"] == c["zero_spread_raters"] == c["insufficient_repeat_raters"] == c["inconsistent_self_raters"] == c["raters_without_complete_rows"] == 1


import pytest


@pytest.mark.parametrize("common_threshold", [True, False])
def test_reference_and_whole_raters(common_threshold):
    rng = np.random.default_rng(241125)
    n = 60
    ids = np.repeat(np.arange(n), 18)
    ratings = rng.integers(1, 11, size=(len(ids), 2))
    own = np.repeat(2 + np.arange(n) % 7, 18)
    if common_threshold:
        own = np.full(len(ids), 5)
    adv = np.maximum(ratings.mean(axis=1) - own, 0)
    y = (rng.random(len(ids)) < expit(-1.3 + .8*adv if common_threshold else -2.0 + 1.6*adv + .35*(own-5))).astype(float)
    frame = pd.DataFrame(dict(iid=ids,wave=1,order=np.tile(np.arange(18),n),dec=y,
        intel=ratings[:,0],amb=ratings[:,1],intel3_1=own,amb3_1=own))
    ids, y, (x, _, _) = designs(frame)
    w = rng.multinomial(n, np.ones(n)/n)
    weights = w[ids]
    ref = minimize(lambda b: np.sum(weights*(np.logaddexp(0, x@b)-y*(x@b))),
                   np.zeros(x.shape[1]), jac=lambda b: x.T@(weights*(expit(x@b)-y)), method="BFGS")
    assert np.isclose(ref.x[3], slope(x,y,weights), atol=1e-5)
    if not common_threshold:
        assert slope(x,y,weights)>0
    assert np.isclose(slope(np.repeat(x,weights,axis=0),np.repeat(y,weights),np.ones(int(weights.sum()))),ref.x[3],atol=1e-5)
    assert slope(x*0,y,weights) is None
    assert fit(frame,lambda _:None,draws=12)==fit(frame,lambda _:None,draws=12)


def test_discordance():
    assert disposition([[1,2],[1,2],[-3,-1]]).startswith("undecided")
    assert disposition([[1,2],[-3,-1],[1,2]]).startswith("undecided")
    assert disposition([[1,2],[-1,1],[1,2]])=="registered bar met"
    assert disposition([[-1,2],[-1,1],[1,2]])=="registered bar not met"
    assert disposition([None,[1,2],[1,3]])=="undecided"



