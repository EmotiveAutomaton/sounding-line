"""Selective recovery preserves old chains, original roster and charged failures."""
import json
import subprocess
import sys

import pytest

from runners.stage11_1 import branch_runtime as run, preflight as prep
from runners.stage11_1 import transport_recovery as recovery
from runners.stage11_1.common import contract, allocation, freeze, read
from runners.stage11_1.construct import twins
from runners.stage11_1.cheap import fit


def setup(root):
    contract(root)
    allocation(root)
    freeze(root / 'ACCOUNT_PILOT_PASSED-v3.json',
           dict(status='COMPLETE', fake=True, sources=run.base.source_pin()))
    rows = twins()[:4]
    freeze(root / 'CHEAP_FIT.json', fit(rows))
    plan = prep.plan('original', 'S3', [prep.forecast(r, 'breadth', 'account') for r in rows],
                     'recover recorded events', 'constructed fixture', 'complete full roster')
    path = root / 'branch_plans/original.json'
    freeze(path, plan)
    return path


def interrupted(root, monkeypatch):
    path = setup(root)
    raw = run.fake_raw
    calls = 0

    def fail_fifth(*args):
        nonlocal calls
        calls += 1
        if calls == 5:
            raise TimeoutError('injected missing first response')
        return raw(*args)

    with monkeypatch.context() as local:
        local.setattr(run, 'fake_raw', fail_fifth)
        with pytest.raises(RuntimeError, match='uncertain transport'):
            run.execute(root, path, True)
    recipe, supplement = recovery.prepare(root, path, 'supplement', True)
    return path, recipe, supplement


def test_whole_roster_cli_replay_and_all_attempt_charges(tmp_path, monkeypatch):
    path, recipe, supplement = interrupted(tmp_path, monkeypatch)
    assert len(read(supplement)['tasks']) == 2
    old_budget = run.base.budget(tmp_path)
    assert old_budget['attempts'] == 5 and old_budget['charged_seconds'] >= 630
    with pytest.raises(FileNotFoundError):
        recovery.analyze(tmp_path, recipe)
    assert run.base.budget(tmp_path) == old_budget
    run.execute(tmp_path, supplement, True)
    before = run.base.budget(tmp_path)
    monkeypatch.setattr(run, 'api', lambda *a, **k: pytest.fail('offline replay dispatched'))
    result = recovery.analyze(tmp_path, recipe)
    assert result['tasks'] == 4 and result['retained_calls'] == 8
    assert result['attempted_calls_including_failure'] == 9
    assert result['charged_seconds_including_failure'] == before['charged_seconds']
    assert not (tmp_path / 'branch_jobs/original/COMPLETE.json').exists()
    assert recovery.analyze(tmp_path, recipe) == result and run.base.budget(tmp_path) == before
    cli = subprocess.run([sys.executable, '-B', '-m', 'runners.stage11_1.transport_recovery',
                          str(recipe), '--root', str(tmp_path)], capture_output=True, text=True, timeout=30)
    assert cli.returncode == 0, cli.stderr
    assert run.base.budget(tmp_path) == before
    # Same fixed parser/scorer on an independently complete fake cell, including
    # the fake account's ambiguous/invalid forecast, must give identical cells.
    control = tmp_path / 'control'
    control_path = setup(control)
    run.execute(control, control_path, True)
    assert result['cells'] == run.analyze(control, control_path)['cells']


@pytest.mark.parametrize('mutation', ['raw', 'plan', 'source', 'missing_response', 'roster'])
def test_changed_or_missing_evidence_refuses(tmp_path, monkeypatch, mutation):
    path, recipe, supplement = interrupted(tmp_path, monkeypatch)
    run.execute(tmp_path, supplement, True)
    before = run.base.budget(tmp_path)
    if mutation == 'raw':
        next((tmp_path / 'calls/original').rglob('RAW.json')).write_text('{}')
    elif mutation == 'plan':
        value = read(path)
        value['tasks'][0]['evaluator']['target']['handling'] = 'different'
        path.write_text(json.dumps(value))
    elif mutation == 'source':
        monkeypatch.setattr(recovery, 'pin', lambda: {})
    elif mutation == 'missing_response':
        next((tmp_path / 'calls/supplement').rglob('RAW.json')).unlink()
    else:
        value = read(recipe)
        value['task_origins'].pop()
        recipe.write_text(json.dumps(value))
    monkeypatch.setattr(run, 'api', lambda *a, **k: pytest.fail('refusal dispatched'))
    with pytest.raises((ValueError, FileNotFoundError)):
        recovery.analyze(tmp_path, recipe)
    assert run.base.budget(tmp_path) == before
    assert not (recipe.parent / 'COMPLETE.json').exists()


def test_old_partial_refuses_and_recovery_preserves_request(tmp_path, monkeypatch):
    path, recipe, supplement = interrupted(tmp_path, monkeypatch)
    before = run.base.budget(tmp_path)
    with pytest.raises(ValueError, match='partial block'):
        run.execute(tmp_path, path, True)
    assert run.base.budget(tmp_path) == before
    original = read(path)
    assert read(supplement)['tasks'] == original['tasks'][2:]
    task = original['tasks'][2]
    old = read(tmp_path / 'calls/original' / task['id'] / '0/REQUEST.json')['request']
    run.execute(tmp_path, supplement, True)
    new = read(tmp_path / 'calls/supplement' / task['id'] / '0/REQUEST.json')['request']
    assert old == new
    payload = json.loads(new['messages'][-1]['content'])
    assert set(payload) == {'evidence', 'response_schema', 'confidence_probability', 'slot_order', 'slot_questions'}
    assert payload['evidence'] == task['public']
    poisoned = dict(task['public'], evaluator=task['evaluator'])
    with pytest.raises(ValueError):
        run.model.request_for(poisoned, 'account', None, 4)


def test_recovery_does_not_accept_dependent_tasks_or_unbound_target(tmp_path):
    path = setup(tmp_path)
    value = read(path)
    value['tasks'][0]['history_ref'] = 'unavailable'
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match='independent forecasts'):
        recovery.prepare(tmp_path, path, 'new', True)
