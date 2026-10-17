import math
from runners.drive.cards.states_v2 import contrast_state


def test_percentile_interval_can_exclude_observed_point():
    assert contrast_state(.999353, .997594, .999017) == 'positive'
    assert contrast_state(-.999353, -.999017, -.997594) == 'negative'
    assert contrast_state(-.999353, -.999017, -.997594, -1) == 'positive'
    assert contrast_state(.8, -.1, .5) == 'marginal'
    assert contrast_state(-.8, -.5, .1) == 'null'


def test_invalid_and_exhaustive_zero_boundaries():
    for value in [(1, 3, 2), (math.nan, 0, 1), (1, -math.inf, 2), (1, 0, math.inf)]:
        assert contrast_state(*value) == 'invalid'
    assert contrast_state(1, 0, 2) == 'marginal'
    assert contrast_state(-1, -2, 0) == 'null'
    assert contrast_state(0, 0, 0) == 'null'
    assert contrast_state(1, .1, 2, valid=False) == 'invalid'
