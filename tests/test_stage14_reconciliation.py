"""Ended-attempt evidence, PID reuse and actual successor dispatch on scratch roots."""
from types import SimpleNamespace
from pathlib import Path
import pytest
from runners.stage14 import dispatcher_v3 as queue, terminal_reconciliation as rec, worker
from runners.stage14.common import read, freeze, atomic, filehash


def fixture(raw, monkeypatch):
    monkeypatch.setattr(rec, 'REPO', raw)
    native = dict(pid=123, created_ticks=100, executable='fixture/python.exe')
    card = dict(id='old', resource='cpu', wall_seconds=600, source_pins={}, input_pins={}, produces=['VALUE.json'])
    cp = raw/'cards/old.json'; freeze(cp, card)
    out = raw/'jobs/old'
    freeze(out/'DISPATCH.json', dict(at='2026-10-01T00:00:00+00:00', native=native, card_sha256=filehash(cp)))
    freeze(out/'FAILED.json', dict(at='2026-10-01T00:01:00+00:00', status='failed', card_sha256=filehash(cp)))
    proof = dict(inspected_at='2026-10-02T00:00:00+00:00', method='Win32_Process exact PID query',
                 query_succeeded=True, pid=123, observed=dict(pid=123, created_ticks=200, executable='fixture/browser.exe'))
    atomic(raw/'proof.json', proof)
    receipt = dict(schema='stage14-failed-exit-v1', attempts={'old':dict(binding=rec.failed_binding(out, cp),
        observation_path='proof.json', observation_sha256=filehash(raw/'proof.json'))})
    atomic(raw/'retired.json', receipt)
    plan = dict(id='fixture', cards=['old'], card_pins={'old':filehash(cp)}, reporting='2099-01-01T00:00:00+00:00',
                failed_attempt_reconciliation=dict(path='retired.json', sha256=filehash(raw/'retired.json')))
    return plan, proof, receipt


@pytest.mark.parametrize('observed', [None, dict(pid=123, created_ticks=200, executable='fixture/browser.exe')])
def test_absent_or_reused_pid_validates(tmp_path, monkeypatch, observed):
    plan, proof, receipt = fixture(tmp_path, monkeypatch)
    proof['observed'] = observed
    repin(tmp_path, plan, proof, receipt)
    assert set(rec.load_reconciled(plan, tmp_path)) == {'old'}


def repin(raw, plan, proof, receipt):
    atomic(raw/'proof.json', proof)
    receipt['attempts']['old']['observation_sha256'] = filehash(raw/'proof.json')
    atomic(raw/'retired.json', receipt)
    plan['failed_attempt_reconciliation']['sha256'] = filehash(raw/'retired.json')


@pytest.mark.parametrize('change', ['unknown', 'same_native', 'wrong_pid', 'partial', 'earlier', 'missing', 'unknown_method'])
def test_unproven_exit_refuses(tmp_path, monkeypatch, change):
    plan, proof, receipt = fixture(tmp_path, monkeypatch)
    if change == 'unknown': proof['query_succeeded'] = False
    elif change == 'same_native': proof['observed']['created_ticks'] = 100
    elif change == 'wrong_pid': proof['observed']['pid'] = 124
    elif change == 'partial': del proof['observed']['executable']
    elif change == 'earlier': proof['inspected_at'] = '2026-09-01T00:00:00+00:00'
    elif change == 'missing': del proof['observed']
    else: proof['method'] = 'access denied means dead'
    repin(tmp_path, plan, proof, receipt)
    with pytest.raises(ValueError): rec.load_reconciled(plan, tmp_path)


@pytest.mark.parametrize('path', ['proof.json', 'retired.json', 'jobs/old/FAILED.json', 'jobs/old/DISPATCH.json', 'cards/old.json'])
def test_changed_evidence_refuses(tmp_path, monkeypatch, path):
    plan, _, _ = fixture(tmp_path, monkeypatch)
    p=tmp_path/path; data=read(p); data['altered']=True; atomic(p, data)
    with pytest.raises(ValueError): rec.load_reconciled(plan, tmp_path)


def isolated_kernel(monkeypatch):
    kernel=SimpleNamespace(CreateMutexW=lambda *a:1, ReleaseMutex=lambda *a:1, CloseHandle=lambda *a:1)
    monkeypatch.setattr(queue.ctypes, 'WinDLL', lambda *a, **k:kernel)
    monkeypatch.setattr(queue.ctypes, 'get_last_error', lambda:0)
    monkeypatch.setattr(queue, 'limits', lambda:None)
    monkeypatch.setattr(queue, 'native_identity', lambda *a:dict(pid=999, created_ticks=1000, executable='fixture'))


def test_actual_loop_retains_failure_blocks_child_and_runs_independent_job(tmp_path, monkeypatch):
    plan, _, _ = fixture(tmp_path, monkeypatch); isolated_kernel(monkeypatch)
    counter=[]
    def fake_run(card, out, raw, tick):
        counter.append(card['id']); freeze(out/'VALUE.json', dict(value=1))
    monkeypatch.setattr(worker.importlib, 'import_module', lambda n:SimpleNamespace(run=fake_run))
    monkeypatch.setattr(worker, 'native_identity', queue.native_identity)
    for job, deps in [('dependent',['old']), ('independent',[])]:
        cp=tmp_path/'cards'/f'{job}.json'
        freeze(cp, dict(id=job, requires=deps, gates=[], handler='fake', resource='cpu', wall_seconds=60,
                        source_pins={}, input_pins={}, produces=['VALUE.json']))
        plan['cards'].append(job); plan['card_pins'][job]=filehash(cp)
    class Child:
        pid=999
        def __init__(self,args,**kwargs): worker.run(Path(args[-1]),tmp_path)
        def poll(self): return 0
    monkeypatch.setattr(queue.subprocess, 'Popen', Child)
    monkeypatch.setattr(queue, 'readiness', lambda c:(True,'fixture'))
    monkeypatch.setattr(queue.time, 'sleep', lambda t:None)
    def no_old_query(n): raise AssertionError('retired PID must not be queried')
    monkeypatch.setattr(queue, 'is_same_live_process', no_old_query)
    freeze(tmp_path/'plan.json', plan); queue.run(tmp_path/'plan.json', tmp_path)
    assert read(tmp_path/'queue/fixture/STATUS.json')['states']==dict(old='failed', dependent='blocked', independent='complete')
    assert counter==['independent']
    assert (tmp_path/'queue/fixture/EXIT.json').exists()


@pytest.mark.parametrize('live', [True, 'unknown'])
def test_actual_loop_current_worker_is_adopted_or_unknown_refuses(tmp_path, monkeypatch, live):
    plan, _, _ = fixture(tmp_path, monkeypatch); isolated_kernel(monkeypatch)
    del plan['failed_attempt_reconciliation']
    # A FAILED receipt alone does not certify exit; this exercises the unreconciled path.
    def identity(n):
        if live=='unknown': raise OSError('identity unavailable')
        return True
    monkeypatch.setattr(queue, 'is_same_live_process', identity)
    monkeypatch.setattr(queue, 'stop_owned', lambda *a:pytest.fail('fixture worker must stay within its original wall budget'))
    p=tmp_path/'jobs/old/DISPATCH.json'; data=read(p); data['at']=queue.now(); atomic(p, data)
    monkeypatch.setattr(queue.time, 'sleep', lambda t:(_ for _ in ()).throw(InterruptedError('end bounded fixture')))
    freeze(tmp_path/'plan.json', plan)
    with pytest.raises((OSError, InterruptedError)): queue.run(tmp_path/'plan.json', tmp_path)
    failure=read(tmp_path/'queue/fixture/FAILED.json')
    if live is True: assert failure['states']['old']=='running'
    else: assert 'identity unavailable' in failure['error'] and not (tmp_path/'queue/fixture/STATUS.json').exists()
