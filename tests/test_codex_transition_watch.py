"""Transition-only monitoring never wakes an agent for healthy elapsed time."""
import json
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import codex_watch as watch
from codex_common import database, put


@pytest.fixture
def context(tmp_path):
    repo = tmp_path; state = repo/'.agent-state'
    native = {'pid': 123, 'created_ticks': 456, 'executable': 'python.exe'}
    cfg = {'transition_only': True, 'fallback_seconds': 1, 'paths': ['job/COMPLETE.json', 'job/FAILED.json'],
           'process_watches': [{'native': native, 'terminal_paths': ['job/COMPLETE.json', 'job/FAILED.json'],
                               'failure_output': '.agent-state/job-disappeared/FAILED.json'}]}
    with database(state) as db:
        put(db, 'owner', 'owner'); put(db, 'owner_phase', 'idle'); put(db, 'last_fallback', 0)
        put(db, 'wake_plan', {'owner': 'owner', 'id': 'obsolete', 'due': 1})
    return repo, state, cfg, native


def test_healthy_process_never_wakes_despite_deadlines(context, monkeypatch):
    repo, state, cfg, native = context
    monkeypatch.setattr(watch, 'native_identity', lambda pid: native)
    for now in (10, 10000, 10000000):
        assert watch.scan(cfg, repo=repo, state=state, now=now) == []
    with database(state) as db:
        put(db, 'wake_plan', None)
    assert watch.scan(cfg, repo=repo, state=state, now=20000000) == []


@pytest.mark.parametrize('actual', [None, {'pid': 123, 'created_ticks': 999, 'executable': 'python.exe'}])
def test_disappearance_or_reuse_creates_one_fault(context, monkeypatch, actual):
    repo, state, cfg, native = context
    monkeypatch.setattr(watch, 'native_identity', lambda pid: actual)
    assert len(watch.scan(cfg, repo=repo, state=state, now=10)) == 1
    assert watch.scan(cfg, repo=repo, state=state, now=1000) == []
    assert (repo/cfg['process_watches'][0]['failure_output']).is_file()


def test_unknown_identity_is_monitor_failure_not_claim_of_death(context, monkeypatch):
    repo, state, cfg, native = context
    def denied(pid):
        raise OSError('denied')
    monkeypatch.setattr(watch, 'native_identity', denied)
    assert len(watch.scan(cfg, repo=repo, state=state, now=10)) == 1
    record = json.loads((repo/cfg['process_watches'][0]['failure_output']).read_text())
    assert 'unavailable' in record['reason'] and not record['scientific_verdict']


@pytest.mark.parametrize('name,record', [
    ('COMPLETE.json', {'status': status})
    for status in ('COMPLETE', 'complete', 'Complete', 'PASS', 'pass', 'FITTED', 'fitted')
] + [('FAILED.json', {'status': 'failed'}), ('FAILED.json', {'error': 'failure'})])
def test_terminal_output_owns_notification(context, monkeypatch, name, record):
    repo, state, cfg, native = context
    (repo/'job').mkdir(); (repo/'job'/name).write_text(json.dumps(record))
    monkeypatch.setattr(watch, 'native_identity', lambda pid: None)
    assert len(watch.scan(cfg, repo=repo, state=state, now=10)) == 1
    assert not (repo/cfg['process_watches'][0]['failure_output']).exists()
    assert watch.urgent({'path': 'job/'+name}, cfg)


@pytest.mark.parametrize('record', [{}, {'status': 'running'}, {'status': 'incomplete'},
                                  {'status': None}, {'status': []}, [], True])
def test_invalid_terminal_does_not_hide_disappearance(context, monkeypatch, record):
    repo, state, cfg, native = context
    (repo/'job').mkdir(); (repo/'job/COMPLETE.json').write_text(json.dumps(record))
    monkeypatch.setattr(watch, 'native_identity', lambda pid: None)
    watch.scan(cfg, repo=repo, state=state, now=10)
    assert (repo/cfg['process_watches'][0]['failure_output']).exists()


@pytest.mark.parametrize('name,changes,expected', [
    ('FAILED-123.json', {}, True),
    ('FAILED-worker.json', {}, False),
    ('FAILED-0.json', {}, False),
    ('FAILED-123.json.tmp', {}, False),
    ('FAILED-123.json', {'error': None}, False),
    ('FAILED-123.json', {'error': ''}, False),
    ('FAILED-123.json', {'traceback': []}, False),
    ('FAILED-123.json', {'at': None}, False),
    ('FAILED-123.json', {'status': 'running'}, False),
    ('FAILED-123.json', {'status': 'incomplete'}, False),
])
def test_pid_failure_receipt_owns_only_its_terminal_notification(context, monkeypatch, name, changes, expected):
    """The coordinator's real statusless failure shape must not become a missing-output alarm."""
    repo, state, cfg, native = context
    record = {'at': '2026-09-20T14:09:46.291625+00:00',
              'error': 'TimeoutExpired(worker, 21600)',
              'traceback': 'Traceback: child.wait(timeout=21600) raised TimeoutExpired',
              'dispositions': []}
    record.update(changes)
    (repo/'job').mkdir()
    terminal = 'job/'+name
    (repo/terminal).write_text(json.dumps(record))
    cfg['paths'] = [terminal]
    cfg['process_watches'][0]['terminal_paths'] = [terminal]
    monkeypatch.setattr(watch, 'native_identity', lambda pid: None)
    events = watch.scan(cfg, repo=repo, state=state, now=10)
    fault = repo/cfg['process_watches'][0]['failure_output']
    assert fault.exists() is not expected
    assert len(events) == (1 if expected else 2)
    assert watch.urgent({'path': terminal}, cfg)
