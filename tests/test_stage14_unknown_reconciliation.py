"""Interrupted worker reentry, immutable evidence, and fail-closed supervision."""
from types import SimpleNamespace
import pytest
from runners.stage14 import dispatcher_v4 as queue, unknown_reconciliation as rec
from runners.stage14.common import freeze, atomic, read, filehash


def setup(raw, monkeypatch):
    monkeypatch.setattr(rec, 'REPO', raw)
    card = raw / 'cards/old.json'; out = raw / 'jobs/old'
    freeze(card, dict(id='old', resource='cpu', wall_seconds=600, source_pins={}))
    native = dict(pid=123, created_ticks=100, executable='fixture/python.exe')
    freeze(out / 'DISPATCH.json', dict(at='2026-10-01T00:00:00+00:00', native=native, card_sha256=filehash(card)))
    binding = rec.record_unknown(out, card)
    proof = dict(method='native_identity', query_succeeded=True, pid=123, observed=None, inspected_at='2098-01-01T00:00:00+00:00')
    receipt = dict(schema='stage14-unknown-exit-v1', attempts={'old': dict(binding=binding, observation_path='proof.json')})
    plan = dict(id='fixture', cards=['old'], card_pins={'old':filehash(card)}, reporting='2099-01-01T00:00:00+00:00')
    repin(raw, plan, proof, receipt)
    return plan, proof, receipt


def repin(raw, plan, proof, receipt):
    atomic(raw / 'proof.json', proof)
    receipt['attempts']['old']['observation_sha256'] = filehash(raw / 'proof.json')
    atomic(raw / 'reconciled.json', receipt)
    plan['unknown_attempt_reconciliation'] = dict(path='reconciled.json', sha256=filehash(raw / 'reconciled.json'))


def test_record_is_idempotent(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch)
    out = tmp_path / 'jobs/old'; card = tmp_path / 'cards/old.json'
    before = (out / 'UNKNOWN.json').read_bytes()
    rec.record_unknown(out, card); rec.record_unknown(out, card)
    assert before == (out / 'UNKNOWN.json').read_bytes()


@pytest.mark.parametrize('change', ['unknown', 'same_native', 'earlier', 'missing', 'wrong_pid', 'partial', 'wrong_method'])
def test_unproved_exit_refuses(tmp_path, monkeypatch, change):
    plan, proof, receipt = setup(tmp_path, monkeypatch)
    if change == 'unknown': proof['query_succeeded'] = False
    elif change == 'same_native': proof['observed'] = receipt['attempts']['old']['binding']['native']
    elif change == 'earlier': proof['inspected_at'] = '2000-01-01T00:00:00+00:00'
    elif change == 'missing': del proof['observed']
    elif change == 'wrong_pid': proof['pid'] = 124
    elif change == 'partial': proof['observed'] = dict(pid=123)
    else: proof['method'] = 'age-based assumption'
    repin(tmp_path, plan, proof, receipt)
    with pytest.raises(ValueError): rec.load_unknown(plan, tmp_path)


@pytest.mark.parametrize('name', ['cards/old.json', 'jobs/old/DISPATCH.json', 'jobs/old/UNKNOWN.json', 'proof.json', 'reconciled.json'])
def test_changed_evidence_refuses(tmp_path, monkeypatch, name):
    plan, _, _ = setup(tmp_path, monkeypatch)
    p = tmp_path / name; value = read(p); value['changed'] = True; atomic(p, value)
    with pytest.raises(ValueError): rec.load_unknown(plan, tmp_path)


@pytest.mark.parametrize('terminal', ['COMPLETE.json', 'FAILED.json', 'TIMEOUT.json'])
def test_conflicting_terminal_refuses(tmp_path, monkeypatch, terminal):
    plan, _, _ = setup(tmp_path, monkeypatch)
    freeze(tmp_path / 'jobs/old' / terminal, dict(status='complete'))
    with pytest.raises(ValueError): rec.load_unknown(plan, tmp_path)


@pytest.mark.parametrize('reconciled', [True, False])
def test_actual_loop_repeats_unknown_blocks_child_and_holds_independent(tmp_path, monkeypatch, reconciled):
    plan, _, _ = setup(tmp_path, monkeypatch)
    if not reconciled: del plan['unknown_attempt_reconciliation']
    original = (tmp_path / 'jobs/old/UNKNOWN.json').read_bytes()
    for job, deps in [('child', ['old']), ('independent', [])]:
        card = tmp_path / 'cards' / (job + '.json')
        freeze(card, dict(id=job, resource='cpu', requires=deps, source_pins={}, wall_seconds=60))
        plan['cards'].append(job); plan['card_pins'][job] = filehash(card)
    kernel = SimpleNamespace(CreateMutexW=lambda *a:1, ReleaseMutex=lambda *a:1, CloseHandle=lambda *a:1)
    monkeypatch.setattr(queue.ctypes, 'WinDLL', lambda *a, **kw:kernel)
    monkeypatch.setattr(queue.ctypes, 'get_last_error', lambda:0)
    monkeypatch.setattr(queue, 'limits', lambda:None)
    monkeypatch.setattr(queue, 'native_identity', lambda:dict(pid=999, created_ticks=200, executable='fixture'))
    monkeypatch.setattr(queue, 'is_same_live_process', lambda n:False)
    monkeypatch.setattr(queue, 'readiness', lambda c:(False, 'fixture resource hold'))
    monkeypatch.setattr(queue.subprocess, 'Popen', lambda *a, **kw:pytest.fail('no job may dispatch'))
    ticks = iter(range(0, 1000, 11)); monkeypatch.setattr(queue.time, 'monotonic', lambda:next(ticks))
    scans = []
    def stop_after_scans(t):
        scans.append(read(tmp_path / 'queue/fixture/STATUS.json'))
        if len(scans) == 4: raise InterruptedError('bounded fixture ends')
    monkeypatch.setattr(queue.time, 'sleep', stop_after_scans)
    freeze(tmp_path / 'plan.json', plan)
    with pytest.raises(InterruptedError): queue.run(tmp_path / 'plan.json', tmp_path)
    assert all(s['states'] == dict(old='unknown', child='blocked', independent='resource-held') for s in scans)
    assert (tmp_path / 'jobs/old/UNKNOWN.json').read_bytes() == original
    assert not (tmp_path / 'jobs/child/DISPATCH.json').exists()


@pytest.mark.parametrize('live', [True, 'unknown'])
def test_current_identity_handling_unchanged(tmp_path, monkeypatch, live):
    from tests import test_stage14_reconciliation as existing
    monkeypatch.setattr(existing, 'queue', queue)
    existing.test_actual_loop_current_worker_is_adopted_or_unknown_refuses(tmp_path, monkeypatch, live)


def test_successor_actual_independent_dispatch(tmp_path, monkeypatch):
    from tests import test_stage14_reconciliation as existing
    monkeypatch.setattr(existing, 'queue', queue)
    existing.test_actual_loop_retains_failure_blocks_child_and_runs_independent_job(tmp_path, monkeypatch)
