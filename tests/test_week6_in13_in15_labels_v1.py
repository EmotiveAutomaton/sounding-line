"""Label-only boundary checks: no source reads, fits or bootstrap recomputation."""
import numpy as np
import pytest
from runners.drive.cards import week6_in13_in15_common_v1 as common
from runners.drive.cards import week6_in13_v1 as in13

# Matches the independently reviewed IN14/IN16 boundary interpretation.
CASES = [
    ((-.2,-.2),'against'),((-.2,-.1),'against'),((-.2,0.),'inconclusive'),
    ((-.2,.1),'inconclusive'),((-.2,.2),'inconclusive'),
    ((-.1,-.1),'against'),((-.1,0.),'against'),((-.1,.1),'against'),((-.1,.2),'inconclusive'),
    ((0.,0.),'against'),((0.,.1),'against'),((0.,.2),'inconclusive'),
    ((.1,.1),'against'),((.1,.2),'inconclusive'),((.2,.2),'supports'),
    ((-.2,-1e-12),'against'),((-.2,1e-12),'inconclusive'),
    ((.1+1e-12,.2),'supports'),((.1-1e-12,.2),'inconclusive'),
    ((-.1-1e-12,.1),'inconclusive'),((-.1+1e-12,.1),'against'),
    ((-.1,.1+1e-12),'inconclusive'),((-.1,.1-1e-12),'against'),
]

@pytest.mark.parametrize('interval,expected', CASES)
@pytest.mark.parametrize('direction', [1, -1])
def test_three_way_signed_boundaries(interval, expected, direction):
    signed = interval if direction == 1 else (-interval[1], -interval[0])
    assert common.classify(signed, .1, direction) == expected

def test_invalid_inputs_and_summary_scope():
    for interval, bar, direction in [((1.,0.),.1,1),((0.,np.nan),.1,1),((0.,np.inf),.1,1),
            ((0.,1.),0.,1),((0.,1.),-.1,1),((0.,1.),np.inf,1),((0.,1.),.1,0),((0.,),.1,1)]:
        with pytest.raises(ValueError): common.classify(interval, bar, direction)
    for point, expected in [(0., 'against'), (-.05, 'against'), (-.2, 'against'), (.2, 'supports')]:
        result = common.summary(point, [point]*2000, 30, .1)
        assert result['estimate'] == point and result['interval'] == [point, point]
        assert result['outcome'] == expected
    assert 'outcome' not in common.summary(.2, [.2]*2000, 19, .1)
    assert 'outcome' not in common.summary(.2, [.2]*1999+[None], 30, .1)

def test_profile_uses_three_way_simultaneous_interval_without_scalar():
    prepared = {'keys': list(range(20)), 'split_counts': {},
        'panels': [{'supported': True, 'direction': 1}, {'supported': True, 'direction': 0}]}
    result = in13.profile_result(prepared, {'point': [-.05, 0.], 'draws': [[-.05, 0.]]*2000})
    assert result['table'][0]['outcome'] == 'against'
    assert result['table'][0]['simultaneous_interval'][1] < 0
    assert 'outcome' not in result['table'][1]
    assert result['primary_scalar'] is None
