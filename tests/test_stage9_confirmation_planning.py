import copy
import math

import pytest

from runners.stage9.confirmation_planning import allocate, unit_estimates, SCIENTIFIC_SEEDS
from runners.stage9.scoring import confirmation_size


def grid():
    # Unit b contains more targets; it must still have the same weight as unit a.
    return [{'unit': unit, 'target': str(target), 'seed': seed, 'difference': base + shift}
            for unit, base, count in [('a', -1., 1), ('b', 1., 3), ('c', 0., 2)]
            for seed, shift in zip(SCIENTIFIC_SEEDS, (-.3, 0., .3))
            for target in range(count)]


def test_seed_and_target_count_do_not_become_independent_units():
    result = unit_estimates(grid(), SCIENTIFIC_SEEDS)
    assert result['n_units'] == 3 and result['n_observations'] == 18
    assert result['values'] == pytest.approx([-1., 1., 0.])
    assert result['standard_deviation'] == pytest.approx(1.)
    assert list(result['seed_means'].values()) == pytest.approx([-.3, 0., .3])
    assert unit_estimates(list(reversed(grid())), SCIENTIFIC_SEEDS) == result


@pytest.mark.parametrize('fault', ['missing_seed', 'partial_target', 'duplicate', 'nonfinite', 'boolean', 'extra_field'])
def test_incomplete_or_invalid_seed_grid_cannot_supply_variance(fault):
    rows = copy.deepcopy(grid())
    if fault == 'missing_seed':
        rows = [r for r in rows if r['seed'] != 9003]
    elif fault == 'partial_target':
        rows = rows[:-1]
    elif fault == 'duplicate':
        rows.append(copy.deepcopy(rows[0]))
    elif fault == 'nonfinite':
        rows[0]['difference'] = math.inf
    elif fault == 'boolean':
        rows[0]['difference'] = True
    else:
        rows[0]['score'] = 1.
    with pytest.raises(ValueError):
        unit_estimates(rows, SCIENTIFIC_SEEDS)


def test_positive_and_negative_use_same_variance_and_frozen_effect():
    args = dict(seeds=SCIENTIFIC_SEEDS, threshold=.05, available_units=10000)
    positive = allocate(grid(), kind='positive', **args)
    negative = allocate(grid(), kind='negative', **args)
    assert positive['required_units'] == negative['required_units'] == confirmation_size(1.)['n']
    assert positive['planning_assumed_true_difference'] == .05
    assert negative['planning_assumed_true_difference'] == -.05
    shifted = [r | {'difference': r['difference'] + 10.} for r in grid()]
    assert allocate(shifted, kind='positive', **args)['required_units'] == positive['required_units']
    assert positive['normal_approximation_power_at_planned_units'] >= .90
    assert positive['scientific_confirmation'] is False


def test_equivalence_uses_its_own_centered_power_calculation():
    result = allocate(grid(), seeds=SCIENTIFIC_SEEDS, threshold=.05,
                      available_units=10000, kind='equivalence')
    directional = confirmation_size(1.)['n']
    assert result['required_units'] != directional
    assert result['planning_assumed_true_difference'] == 0.
    assert .90 <= result['normal_approximation_power_at_planned_units'] < .901
    assert result['detectable_effect_or_centered_equivalence_margin'] <= .05


def test_short_reserve_stays_exploratory_without_retargeting_effect():
    result = allocate(grid(), seeds=SCIENTIFIC_SEEDS, threshold=.05,
                      available_units=20, kind='negative')
    assert result['planned_units'] == result['available_units'] == 20
    assert not result['power_adequate'] and not result['scientific_confirmation']
    assert result['practical_threshold'] == .05
    assert result['detectable_effect_or_centered_equivalence_margin'] > .05
    assert result['normal_approximation_power_at_planned_units'] < .90


def test_no_unvalidated_crossed_or_zero_variance_plan():
    args = dict(seeds=SCIENTIFIC_SEEDS, threshold=.05, available_units=200, kind='positive')
    with pytest.raises(ValueError, match='crossed'):
        allocate(grid(), design='person_and_script', **args)
    with pytest.raises(ValueError, match='zero discovery variance'):
        allocate([r | {'difference': 0.} for r in grid()], **args)
    for invalid in (dict(available_units=True), dict(threshold=True), dict(seeds=[9001])):
        with pytest.raises(ValueError):
            allocate(grid(), **(args | invalid))


def test_untrained_arm_uses_independent_units_without_invented_seeds():
    rows = [{'unit': 'u'+str(i), 'target': 't', 'seed': None, 'difference': value}
            for i, value in enumerate([-1., 0., 1.])]
    result = allocate(rows, seeds=[None], threshold=.05, available_units=10000, kind='positive')
    assert result['discovery']['n_units'] == result['discovery']['n_observations'] == 3
    assert result['discovery']['seeds'] == [None]
