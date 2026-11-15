"""Independent constructed rulers and time-alignment guards for DC1."""
import itertools
import numpy as np
import pytest
from runners.drive.cards import week6_dc1_v1 as dc


def test_preflight_continuous_reference_is_preserved_separately():
    value = dc.preflight_reference()
    assert round(value['sum'], 3) == .406
    assert not value['production_binary_validation']


def binary_world(null=False):
    patterns = np.asarray(list(itertools.product((-1., 1.), repeat=9)))
    x = np.tile(np.repeat(patterns, 20, axis=0), (3, 1))
    person = np.repeat(np.arange(3), len(patterns) * 20)
    replicate = np.tile(np.arange(20), len(patterns) * 3)
    a, b = (.2, .2) if null else (.3, .1)
    rating = a * x[:, dc.RECENT] + b * x[:, dc.LEVEL] + np.where(replicate < 10, 1., -1.) * np.sqrt(1 - a * a - b * b)
    probability = .5 + (a / 2) * x[:, dc.LEVEL] + (b / 2) * x[:, dc.RECENT]
    choice = (replicate < np.rint(probability * 20)).astype(int)
    return x, rating, choice, person


def test_binary_standardized_primary_recovers_both_parts_and_exact_null():
    arrays = binary_world()
    value = dc.primary(*arrays)
    expected = .2 * np.sqrt((len(arrays[0]) - 1) / len(arrays[0]))
    assert value['parts'] == pytest.approx([expected, expected], abs=1e-12)
    assert dc.primary(*binary_world(True))['parts'] == pytest.approx([0, 0], abs=1e-12)
    with pytest.raises(ValueError, match='binary choices'):
        dc.primary(arrays[0], arrays[1], arrays[1], arrays[3])


def test_exact_sufficient_statistics_match_rowwise_and_whole_person_resampling():
    arrays = binary_world()
    stats = dc.sufficient_statistics(*arrays)
    weights = np.array([2, 0, 1])
    expected = dc.primary(*arrays, weights=weights)
    value = dc.from_statistics(stats, weights)
    for key in expected:
        assert value[key] == pytest.approx(expected[key], abs=1e-11)
    assert dc.bootstrap_draw(stats, 2) == dc.bootstrap_draw(stats, 2)


def test_within_person_estimator_against_dense_fixed_effect_oracle():
    rng = np.random.default_rng(52)
    people = np.repeat(np.arange(4), 20)
    x = rng.normal(size=(80, 3)); y = x @ [.2, -.1, .3] + people * 5 + rng.normal(size=80)
    dense = np.column_stack((x, *[(people == p).astype(float) for p in range(4)]))
    expected = np.linalg.lstsq(dense, (y - y.mean()) / y.std(ddof=1), rcond=None)[0][:3]
    assert dc.fixed_effect(x, y, people)['beta'] == pytest.approx(expected, abs=1e-12)


def plays():
    p = np.zeros((2, 30, 15))
    p[:, :, 2] = 1; p[:, :, 3] = 4; p[:, :, 4] = -2
    p[:, :, 6] = np.arange(30) % 2; p[:, :, 7] = np.arange(30)
    p[:, :, 9] = np.nan
    p[:, [0, 2, 5, 7, 10, 12, 15, 17, 20, 22, 25, 29], 9] = 2
    return p


def test_posttrial_rating_pairs_next_choice_without_future_outcome_leak():
    p = plays(); scales = np.ones(9)
    rows, audit = dc.timing_table(p, [1, 2], [1, 1], [1, 2], [1, 2], scales)
    first = rows[0]
    assert first['stored_rating_trial'] == 2 and first['next_choice_trial'] == 3
    assert first['history_last_trial'] == 2
    assert first['x'][dc.RECENT] == pytest.approx(0.)  # errors through trials 0..2: -1,0,1
    assert len(rows) == 20 and len(audit['dispositions']) == 24
    assert not audit['production_admitted']
    changed = p.copy(); changed[:, 3:, 7] += 1000
    later, _ = dc.timing_table(changed, [1, 2], [1, 1], [1, 2], [1, 2], scales)
    assert later[0]['x'] == first['x']
    assert {d['reason'] for d in audit['dispositions']} == {
        'initial_rating_before_first_trial_no_recent_history', 'final_rating_has_no_next_choice',
        'paired_pending_control_timing_review'}


def test_common_roster_coverage_and_first_play_fail_closed():
    common, audit = dc.common_roster([1, 2], [2, 3], [1, 2, 3, 4])
    assert common == [2] and audit['TR1_only'] == audit['RR3_only'] == 1
    with pytest.raises(ValueError, match='absent'):
        dc.common_roster([1], [3], [1, 2])
    with pytest.raises(ValueError, match='actual first play'):
        dc.timing_table(plays(), [1, 2], [2, 1], [1, 2], [1, 2], np.ones(9))


def test_two_part_gate_never_substitutes_positive_sum():
    rng = np.random.default_rng(6)
    point = {'parts': [.3, -.1]}
    draws = [{'parts': (np.asarray(point['parts']) + rng.normal(0, .005, 2)).tolist()} for _ in range(2000)]
    result = dc.summarize(point, draws, 40)
    assert result['parts'][0]['outcome'] == 'supports'
    assert not result['both_supported']
    draws[3] = None
    assert dc.summarize(point, draws, 40)['status'] == 'invalid_uncertainty'


def test_stability_correction_never_clips_or_invents_choice_reliability():
    result = dc.corrected_person_correlation([0, 1, 2], [0, 1, 2], .25)
    assert result['corrected'] == pytest.approx(2.)
    assert result['choice_reliability_unmeasured'] and result['correction_above_one_retained']
    assert dc.corrected_person_correlation([0, 1, 2], [0, 1, 2], 0)['status'] == 'unsupported'
