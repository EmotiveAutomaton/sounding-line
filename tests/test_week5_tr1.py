from pathlib import Path
import json
import numpy as np
import pytest
from runners.drive.cards import week5_tr1 as study
from runners.drive.cards import week5_tr1_math as math
from runners.drive.cards import week5_tr1_fixture as fixture


def test_recent_luck_matches_scalar_and_first_rating_is_pretrial(tmp_path):
    task = fixture.constructed_task(tmp_path / 'task.npz')
    with np.load(task) as data:
        plays = data['plays']
    x, y, total = math.recent_luck(plays)
    for i, play in enumerate(plays):
        state = 0.; expected = []; cumulative = 0.
        for trial in range(30):
            luck = (play[trial, 7] - (play[trial, 3] + play[trial, 4]) / 2) if play[trial, 6] else 0.
            if trial == 0:
                expected.append(0.)
            state = .65 * state + luck; cumulative += luck
            if trial > 0 and np.isfinite(play[trial, 9]):
                expected.append(state)
        assert np.allclose(x[i], expected, atol=1e-12)
        assert total[i] == cumulative
    assert y.shape[1] == 12


def test_coefficients_and_ar1_covariance_match_dense_reference():
    rng = np.random.default_rng(2); x = rng.normal(size=(20, 12)); y = 7 + .4*x + rng.normal(size=x.shape)
    fitted = math.play_table(x, y, .3)
    correlation = .3 ** np.abs(np.arange(12)[:, None] - np.arange(12)[None, :])
    for i in range(len(x)):
        design = np.column_stack((np.ones(12), x[i])); inverse = np.linalg.inv(design.T @ design)
        expected = np.linalg.lstsq(design, y[i], rcond=None)[0]
        a = inverse @ design.T; residual = y[i] - design @ expected
        sigma2 = residual @ residual / np.trace((np.eye(12) - design @ a) @ correlation)
        covariance = sigma2 * a @ correlation @ a.T
        assert np.allclose(fitted['coefficient'][i], expected, atol=1e-11)
        assert np.allclose(fitted['sampling_variance'][i], np.diag(covariance), atol=1e-11)


def test_unclipped_ratio_and_negative_true_variance_retained():
    values = np.arange(30.)
    coefficients = np.column_stack((values, values))
    table = {'coefficient': coefficients, 'sampling_variance': np.full((30, 2), 10.),
             'half': np.stack((coefficients, coefficients), axis=1), 'rating_sd': np.ones(30)}
    result = math.stability(table, np.arange(30), np.arange(30), np.ones(30), 'sampling')
    assert result['stability'] > 1
    table['sampling_variance'][:] = 1000
    result = math.stability(table, np.arange(30), np.arange(30), np.ones(30), 'sampling')
    assert result['minimum_true_variance'] < 0
    assert result['status'] == 'nonpositive_reliability' and result['stability'] is None


def test_calibration_selection_and_all_world_failure_are_reachable():
    cases = {str(target): {'sampling': {'status': 'ok', 'stability': target + .02},
                           'split_half': {'status': 'ok', 'stability': target + .03}} for target in (0., .5, 1.)}
    assert math.choose_calibration(cases)['selected_method'] == 'sampling'
    cases['1.0']['sampling']['stability'] = .4
    assert math.choose_calibration(cases)['selected_method'] == 'split_half'
    cases['0.0']['split_half']['stability'] = .2
    assert math.choose_calibration(cases)['qualified'] is False
    with pytest.raises(ValueError):
        math.choose_calibration({'0.0': cases['0.0']})


def test_case_gate_precedes_stability_and_no_failed_draw_is_deleted():
    ok = {'status': 'ok', 'interval': [.6, .9]}
    assert math.decision({'status': 'ok', 'interval': [-.1, .4]}, ok, True).startswith('no between-person')
    assert math.decision({'status': 'ok', 'interval': [.1, .4]}, ok, True) == 'supports a stable sensitivity'
    rows = [{'stability': .7}] * 2000; rows[41] = {'stability': None}
    result = math.uncertainty(.7, rows, 'stability', .5)
    assert result['status'] == 'invalid_uncertainty' and result['failed_draws'] == [41]


def test_whole_person_pairs_and_ambiguity_preserved():
    data = {'person': np.array([0, 0, 0, 1, 1, 2]), 'counter': np.array([1, 2, 4, 1, 2, 1]),
            'repeat_eligible': np.array([1, 1, 1, 0, 0, 1], bool)}
    selected, people, audit = study.roster(data)
    assert selected.tolist() == [0, 1, 2] and people.tolist() == [0, 0, 0]
    assert audit['ambiguous_people_excluded'] == 1 and audit['one_play_people_excluded'] == 1
    left, right = math.consecutive(people, data['counter'][selected])
    assert left.tolist() == [0, 1] and right.tolist() == [1, 2]


def test_carryover_matches_dense_person_fixed_effects():
    person = np.repeat(np.arange(6), 4); counter = np.tile(np.arange(4), 6)
    left, right = math.consecutive(person, counter)
    rng = np.random.default_rng(8); total = rng.normal(size=24); first = rng.normal(size=24)
    first[right] += .7 * total[left]
    dummy = np.eye(6)[person[right]]
    design = np.column_stack((dummy, total[left]))
    expected = np.linalg.lstsq(design, first[right], rcond=None)[0][-1]
    result = math.carryover(total, first, person, left, right, np.ones(6))
    assert abs(result['slope'] - expected) < 1e-10


def test_complete_2000_draw_chain_and_independent_replay(tmp_path):
    task = fixture.constructed_task(tmp_path / 'task.npz')
    result, proof, terminals = fixture.complete_chain(tmp_path / 'run', task)
    assert proof['verified'] is True and terminals.count('yielded') >= 4
    assert result.get('complete_computation') is True, result
    draws = json.loads((tmp_path / 'run/BOOTSTRAP.json').read_text())['draws']
    assert len(draws) == 2000
    cases = json.loads((tmp_path / 'run/CALIBRATION.json').read_text())['cases']
    assert all(case['synthetic_people'] == 2000 for case in cases.values())


def test_resume_refuses_changed_source_and_false_verification(tmp_path):
    task = fixture.constructed_task(tmp_path / 'task.npz'); output = tmp_path / 'run'
    config = {'phase': 'TR1', 'draws': 2000, 'max_new_draws': 1, 'max_wall_seconds': 100}
    with fixture.source_boundary(task):
        first = study.execute(output, {}, config)
        assert first['status'] == 'yielded' and first['verified'] is False
        path = output / 'PROJECTION.json'; value = json.loads(path.read_text()); value['completed'] = 100
        path.write_text(json.dumps(value))
        with pytest.raises(ValueError, match='checkpoint changed'):
            study.execute(output, {}, config)


def test_no_source_or_semantic_waiver(tmp_path):
    with pytest.raises(ValueError):
        study.authenticate({})
    with pytest.raises(ValueError):
        study.run(tmp_path, {}, {'phase': 'TR1', 'draws': 12})


def test_real_handler_stops_on_unqualified_estimators(tmp_path, monkeypatch):
    task = fixture.constructed_task(tmp_path / 'task.npz')
    failed = {method: {'status': 'unsupported'} for method in math.METHODS}
    monkeypatch.setattr(study, 'planted_world', lambda data, noise, target: failed)
    result, proof, _ = fixture.complete_chain(tmp_path / 'run', task)
    assert proof['verified'] is True and result['human_inference'] is False
    assert result['status'] == 'estimator unqualified'
    assert not (tmp_path / 'run/BOOTSTRAP.json').exists()


def test_changed_constructed_source_cannot_resume(tmp_path):
    task = fixture.constructed_task(tmp_path / 'task.npz'); output = tmp_path / 'run'
    config = {'phase': 'TR1', 'draws': 2000, 'max_new_draws': 1, 'max_wall_seconds': 100}
    with fixture.source_boundary(task):
        assert study.execute(output, {}, config)['status'] == 'yielded'
        with task.open('ab') as stream:
            stream.write(b'changed source capsule')
        with pytest.raises(ValueError, match='source/semantic binding'):
            study.execute(output, {}, config)
