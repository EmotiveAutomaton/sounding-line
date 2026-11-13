import ast
import inspect
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import numpy as np
import pytest
from scipy.optimize import minimize
from scipy.special import expit
from runners.drive.cards import week5_in9_v1 as old
from runners.drive.cards import week5_in9_v2 as study
from runners.drive.cards import week5_in9_convergence_fixture_v2 as fixture


def test_handler_exact_scientific_body_and_reference_tail_unchanged():
    before = Path(old.__file__).read_text('utf8')
    expected = before.replace('"""IN9 items-first table card, isolated two-day packet implementation.',
        '"""IN9 items-first reference-convergence successor; original scientific contract.').replace(
        'from . import week5_in9_reference_v1 as reference',
        'from . import week5_in9_reference_v2 as reference')
    assert Path(study.__file__).read_text('utf8') == expected
    assert study.math is old.math
    for name in ['interval_and_se']:
        first = ast.parse(inspect.getsource(getattr(old.reference, name))).body[0]
        second = ast.parse(inspect.getsource(getattr(study.reference, name))).body[0]
        first.body = first.body[1:]; second.body = second.body[1:]
        assert ast.dump(first) == ast.dump(second)
    assert (study.reference.GTOL, study.reference.CERTIFICATE,
            study.reference.MAXITER, study.reference.MAX_RECENTERS) == (1e-8, 1e-6, 100, 2)


def test_relative_objective_hand_value_and_complete_difference():
    design = np.array([[1., -2.], [1., 1.], [1., 3.]])
    y = np.array([0., 1., 1.]); w = np.array([2., 5., 3.]); penalty = np.diag([0., 1.])
    anchor = np.array([.2, -.3])
    def objective(b):
        z = design@b
        return np.sum(w*(np.logaddexp(0., z)-y*z))+.5*b@penalty@b
    for displacement in [np.array([.04, -.02]), np.array([3., -2.]), np.array([-5., 3.])]:
        actual = study.reference.relative_loss(design, y, w, penalty, anchor, displacement)
        assert abs(actual-(objective(anchor+displacement)-objective(anchor))) < 2e-13
    assert study.reference.relative_loss(design, y, w, penalty, anchor, np.zeros(2)) == 0.
    # Balanced intercept-only sample, three positive and three negative units:
    # L(d)-L(0)=6*log(cosh(d/2)), including a sub-ulp full-loss decrement.
    x = np.ones((2, 1)); labels = np.array([0., 1.]); weights = np.array([3., 3.])
    displacement = np.array([1e-7])
    actual = study.reference.relative_loss(x, labels, weights, np.zeros((1, 1)),
                                          np.zeros(1), displacement)
    assert abs(actual-.75e-14) < 1e-21


def test_real_optimizer_limit_reproduces_on_frozen_weighted_ill_conditioned_cases(tmp_path):
    records = []; rescued = 0; failures = []
    for seed in (17, 29, 43):
        for multiplier in (1., 10.):
            design, target, weight = fixture.weighted_case(seed, multiplier)
            diagnostics = []
            record = {'seed': seed, 'weight_multiplier': multiplier,
                'design_condition': float(np.linalg.cond(design)), 'attempts': diagnostics}
            try:
                beta = study.reference.fit_weighted(design, target, weight, diagnostics)
                penalty = np.r_[0., beta[1:]]
                gradient = design.T@(weight*(expit(design@beta)-target))+penalty
                record['separate_gradient_inf'] = float(np.max(np.abs(gradient)))
                if record['separate_gradient_inf'] > 1e-6 or not diagnostics[-1]['certified']:
                    failures.append([seed, multiplier])
                rescued += int(not diagnostics[0]['certified'])
            except (ValueError, np.linalg.LinAlgError) as error:
                record['failure'] = str(error); failures.append([seed, multiplier])
            records.append(record)
    (tmp_path/'CONVERGENCE_CONTROL.json').write_text(json.dumps(records, indent=2)+'\n')
    assert not failures, 'Preserved constructed cases still fail the unchanged certificate'
    assert rescued >= 1, 'Frozen constructed cases did not reproduce old optimizer limit; do not claim qualification'


def test_original_certified_solution_is_returned_without_recenter():
    x = np.array([[1., -1.], [1., -1.], [1., 1.], [1., 1.]])
    diagnostics = []
    beta = study.reference.fit_weighted(x, np.array([0., 1., 0., 1.]), np.ones(4), diagnostics)
    assert np.array_equal(beta, np.zeros(2)) and len(diagnostics) == 1
    assert diagnostics[0]['certified']


def test_recenter_budget_cannot_return_uncertified_candidate(monkeypatch):
    calls = []
    def failed(fun, x0, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(x=np.asarray(x0), status=2, nit=0)
    monkeypatch.setattr(study.reference, 'minimize', failed)
    with pytest.raises(ValueError, match='independent ridge gradient certificate not met'):
        study.reference.fit_weighted(np.array([[1., -1.], [1., 1.]]),
                                     np.array([0., 1.]), np.ones(2))
    assert len(calls) == 3
    assert all(c['method'] == 'trust-exact' and c['options'] == {'gtol': 1e-8, 'maxiter': 100} for c in calls)


def test_weighted_fold_auc_and_item_equivalence_without_production_solver_in_reference(monkeypatch):
    frame = fixture.original_fixture.world(3, 400)
    x = frame[list(study.ITEMS)].to_numpy(float); y = frame.emotion.eq('shame').to_numpy(int)
    folds, codes, _ = study.math.fold_codes(frame.prolific_id.to_numpy(str))
    w = study.math.draw_weights(codes, 19); indices = [0, 3, 7]
    expected = study.math.evaluate(x, y, folds, w, indices)
    monkeypatch.setattr(study.math, 'ridge_fit', lambda *a: pytest.fail('reference used production optimizer'))
    actual = study.reference.evaluate(x, y, folds, w, indices)
    assert np.allclose(actual, expected, atol=2e-6, rtol=0)
    with pytest.raises(ValueError, match='fewer than two weighted labels'):
        study.reference.evaluate(x, y, folds, w*(y == 1), indices)


def test_source_and_old_checkpoint_bindings_refuse_reentry(tmp_path):
    frame = fixture.original_fixture.world(0, 200)
    config = {'phase': 'IN9-items', 'draws': 2000, 'max_new_draws': 1}
    with fixture.original_fixture.constructed_source(frame):
        assert old.execute(tmp_path/'old', {}, config)['status'] == 'yielded'
    with fixture.constructed_source(frame), pytest.raises(ValueError, match='binding changed'):
        study.execute(tmp_path/'old', {}, config)
    with fixture.constructed_source(frame):
        assert study.execute(tmp_path/'new', {}, config)['status'] == 'yielded'
    frame.loc[0, 'intensity'] += .1
    with fixture.constructed_source(frame), pytest.raises(ValueError, match='binding changed'):
        study.execute(tmp_path/'new', {}, config)


def test_complete_2000_draw_execute_and_fresh_process_verifier(tmp_path):
    root = tmp_path/'chain'
    for operation, maximum in [('execute', 1), ('execute', 2000), ('verify', 1), ('verify', 2000)]:
        completed = subprocess.run([sys.executable, '-X', 'utf8', '-B', '-m',
            'runners.drive.cards.week5_in9_convergence_fixture_v2', operation, str(root), str(maximum)],
            capture_output=True, text=True, timeout=120)
        assert completed.returncode == 0, completed.stderr
    result = json.loads((root/'RESULT.json').read_text())
    assert result['primary']['estimate'] == .5 and result['primary']['interval'] == [.5, .5]
    assert json.loads((root/'verify-1-CONTROL.json').read_text())['verified'] is False
    assert json.loads((root/'verify-2000-CONTROL.json').read_text())['verified'] is True
    for name in ('DRAWS.json', 'independent-replay/DRAWS.json'):
        bank = json.loads((root/name).read_text())
        assert len(bank['draws']) == 2000 and not bank['point'].get('failure')
        assert all(row.get('value', [None])[0] == .5 for row in bank['draws'])


def test_failure_is_retained_and_no_interval_released():
    value = {'value': [.7]+[0.]*6}
    rows = [value.copy() for _ in range(2000)]
    rows[4] = {'failure': 'independent ridge gradient certificate not met'}
    result = study.summaries(value, rows, {'guilt': 200, 'shame': 200}, 200)
    assert result['failed_draws'] == [4] and result['status'] == 'invalid uncertainty'
    assert 'primary' not in result
