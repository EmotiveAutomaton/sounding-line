import numpy as np
import pytest
from scipy.special import ndtr

from runners.drive.cards.week7_grouped_price import CUTS
from runners.drive.cards.week7_price_tail_recovery import fit_tail


@pytest.mark.parametrize('drop_zero', [True, False])
def test_interior_and_boundary_have_different_dispositions(drop_zero):
    for location, spread in ((3.1, 2.2), (8., 4.)):
        cumulative = ndtr((CUTS - location) / spread)
        counts = np.diff(cumulative, prepend=0.)
        expected = (1 - cumulative[-1]) / (cumulative[-1] - (cumulative[0] if drop_zero else 0.))
        estimate = fit_tail(counts[None, :], drop_zero, force_check=True)[0]
        assert estimate == pytest.approx(expected, rel=.001)
    rate = .6
    boundary = np.r_[np.exp(-6 * rate), np.exp(rate * np.arange(-5, 1)) * -np.expm1(-rate)]
    assert np.isnan(fit_tail(boundary[None, :], drop_zero, force_check=True)[0])
