import json
import numpy as np
import pytest
from runners.drive.cards import week5_rr3_v1 as study
from runners.drive.cards import week5_rr3_fixture_v1 as fixture


def test_recent_has_hand_answers_and_never_looks_at_current_or_future_outcomes():
    play = fixture.hand_play()
    value = study.math.recent(play)
    assert np.isnan(value[0, 0])
    assert np.allclose(value[0, 1:5], [4., 2., 0., -4/3])
    assert np.allclose(value, study.math.reference_recent(play), equal_nan=True)
    changed = play.copy(); changed[0, 5:, 7] += 100
    assert np.array_equal(value[:, :6], study.math.recent(changed)[:, :6], equal_nan=True)


def test_recent_resets_at_each_play_and_uses_chosen_option_expected_value():
    play = fixture.hand_play(); pair = np.concatenate([play, play])
    pair[0, -1, 7] = 1000
    assert np.array_equal(study.math.recent(pair)[1], study.math.recent(play)[0], equal_nan=True)
    play[0, 0, 6] = 0; play[0, 0, 2] = 1
    assert study.math.recent(play)[0, 1] == 5


def test_source_preparation_independent_formula_and_all_first_trial_exclusions():
    data = fixture.source_shaped(); selected, census = study.previous.roster(data)
    standing = study.features.dynamic_features(data['first'], .65)[:, :, 3:5].sum(axis=2).std(ddof=1)
    left = study.prepare(data, selected, census, standing)
    right = study.prepare(data, selected, census, standing, True)
    assert np.allclose(left['x'], right['x'], atol=1e-12, rtol=0)
    assert left['census']['first_trials_excluded_no_history'] == 72
    assert left['x'].shape == (72*29, 9)
    assert np.array_equal(left['attempt'], np.repeat(data['counter'][selected], 29))
    assert left['scales'][3] == left['scales'][4] == standing


def test_absolute_coefficient_contrast_hand_answers():
    beta = np.zeros(9); beta[[8, 3, 4]] = [-.3, .1, -.2]
    assert np.allclose(study.math.contrast(beta), [-.3, .1, -.2, .1])
    assert study.math.contrast(beta) == study.math.reference_contrast(beta)


def test_two_signed_plants_full_2000_person_banks(tmp_path):
    results = fixture.signed_proofs(tmp_path/'signed')
    assert set(results) == {'recent', 'distance'}


def test_full_null_production_state_machine_and_independent_2000_draw_reentry(tmp_path):
    assert fixture.null_chain(tmp_path/'null')['passed'] is True


def test_failed_draws_remain_indexed_and_prevent_interval():
    point = {'value': [.3, 0., 0., .3], 'informative_participants': 20}
    draws = [point.copy() for _ in range(2000)]; draws[17] = {'failure': 'rank_deficient'}
    result = study.summary(point, draws, 20)
    assert result['status'] == 'invalid_uncertainty' and result['failed_draws'] == [17]
    assert 'primary' not in result
    with pytest.raises(ValueError, match='Unfinished'):
        study.summary(point, draws[:100], 20)


def test_below_twenty_people_remains_descriptive():
    point = {'value': [.3, 0., 0., .3], 'informative_participants': 19}
    result = study.summary(point, [point]*2000, 19)
    assert result['primary']['outcome'] == 'below floor, descriptive'


def test_operational_bounds_cannot_change_semantics_or_resume_source(tmp_path):
    with pytest.raises(ValueError):
        study.settings({'phase': 'RR3', 'draws': 1999})
    with pytest.raises(ValueError):
        study.settings({'phase': 'RR3', 'max_wall_seconds': float('inf')})
    with pytest.raises(ValueError):
        study.load({})
    table = fixture.paired_null(); config = {'phase': 'RR3', 'max_new_draws': 1}
    with fixture.prepared_boundary(table):
        assert study.execute(tmp_path, {}, config)['status'] == 'yielded'
    table['x'][0, 0] += .1
    with fixture.prepared_boundary(table), pytest.raises(ValueError, match='binding changed'):
        study.execute(tmp_path, {}, config)


def test_independent_interval_correlation_and_full_record_refusal():
    left = study.math.interval_and_se([0., 1., 2., 3.]); right = study.math.interval_and_se([0., 1., 2., 3.], True)
    assert np.allclose(left[0], [.075, 2.925]) and np.allclose(left[0], right[0])
    assert abs(left[1]-right[1]) < 1e-15
    assert study.math.correlation([1, 2, 3], [6, 4, 2], True) == -1
    with pytest.raises(ValueError):
        study.compare_record({'activation': [], 'count': 2}, {'activation': [], 'count': 3})
