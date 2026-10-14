"""Runtime-drift refusal and independent dispatch through the actual successor."""
from types import SimpleNamespace
import pytest
from runners.stage14 import dispatcher_v5 as queue, local
from tests import test_stage14_unknown_reconciliation as unknown
from tests import test_stage14_reconciliation as failed


@pytest.fixture
def resources(tmp_path, monkeypatch):
    monkeypatch.setattr(queue, 'REPO', tmp_path)
    monkeypatch.setattr(queue.psutil, 'virtual_memory', lambda:SimpleNamespace(available=16*1024**3))
    monkeypatch.setattr(queue.psutil, 'disk_usage', lambda p:SimpleNamespace(free=30*1024**3))
    return tmp_path


@pytest.mark.parametrize('version', ['0.40.3', None, 351, ''])
def test_changed_or_missing_runtime_cannot_reach_reader_admission(resources, monkeypatch, version):
    monkeypatch.setattr(local, 'api', lambda path:{'version':version})
    monkeypatch.setattr(local, 'ready', lambda *a:pytest.fail('reader must not be admitted'))
    assert queue.readiness(dict(resource='gpu',model_digest='fixed'))[0] is False


@pytest.mark.parametrize('admitted',[True,False])
def test_prior_runtime_still_obeys_existing_resource_gate(resources, monkeypatch, admitted):
    monkeypatch.setattr(local, 'api', lambda path:{'version':'0.35.1'})
    calls=[]
    def ready(*args):
        calls.append(args);return dict(ready=admitted,reason='existing gate')
    monkeypatch.setattr(local, 'ready', ready)
    assert queue.readiness(dict(resource='gpu',model='fixed',model_digest='digest',memory_MiB=7000))==(admitted,'existing gate')
    assert calls==[('fixed','digest',7000)]


def test_changed_service_does_not_block_empty_service_torch_or_cpu(resources, monkeypatch):
    monkeypatch.setattr(local, 'api', lambda path:{'models':[]} if path=='/api/ps' else pytest.fail('torch does not use the reader runtime'))
    from runners.stage12 import local_api
    monkeypatch.setattr(local_api, 'snapshot', lambda:dict(free_MiB=8000,temperature_C=50))
    assert queue.readiness(dict(resource='gpu',memory_MiB=5500))[0]
    assert queue.readiness(dict(resource='cpu'))[0]


def test_actual_successor_preserves_unknown_and_independent_dispatch(tmp_path,monkeypatch):
    monkeypatch.setattr(failed,'queue',queue)
    failed.test_actual_loop_retains_failure_blocks_child_and_runs_independent_job(tmp_path,monkeypatch)


@pytest.mark.parametrize('reconciled',[True,False])
def test_actual_successor_repeats_unknown(tmp_path,monkeypatch,reconciled):
    monkeypatch.setattr(unknown,'queue',queue)
    unknown.test_actual_loop_repeats_unknown_blocks_child_and_holds_independent(tmp_path,monkeypatch,reconciled)


def test_actual_loop_holds_changed_reader_and_dispatches_independent_cpu(resources,monkeypatch):
    from pathlib import Path
    from runners.stage14 import worker
    from runners.stage14.common import freeze,read,filehash
    monkeypatch.setattr(failed,'queue',queue)
    failed.isolated_kernel(monkeypatch)
    calls=[]
    def fake_run(card,out,raw,tick):
        calls.append(card['id']);freeze(out/'VALUE.json',dict(value=1))
    monkeypatch.setattr(worker.importlib,'import_module',lambda name:SimpleNamespace(run=fake_run))
    monkeypatch.setattr(worker,'native_identity',queue.native_identity)
    monkeypatch.setattr(local,'api',lambda path:{'version':'0.40.3'})
    monkeypatch.setattr(local,'ready',lambda *args:pytest.fail('changed reader reached admission'))
    plan=dict(id='fixture',cards=['reader','cpu'],card_pins={},reporting='2099-01-01T00:00:00+00:00')
    for job in plan['cards']:
        card=dict(id=job,requires=[],gates=[],handler='fake',resource='cpu',wall_seconds=60,source_pins={},produces=['VALUE.json'])
        if job=='reader':card.update(resource='gpu',model_digest='fixed')
        path=resources/'cards'/f'{job}.json';freeze(path,card);plan['card_pins'][job]=filehash(path)
    class Child:
        pid=999
        def __init__(self,args,**kwargs):worker.run(Path(args[-1]),resources)
        def poll(self):return 0
    monkeypatch.setattr(queue.subprocess,'Popen',Child)
    scans=[]
    def stop(t):
        scans.append(read(resources/'queue/fixture/STATUS.json'))
        if len(scans)==2:raise InterruptedError('bounded fixture ends')
    monkeypatch.setattr(queue.time,'sleep',stop)
    freeze(resources/'plan.json',plan)
    with pytest.raises(InterruptedError):queue.run(resources/'plan.json',resources)
    assert scans[-1]['states']==dict(reader='resource-held',cpu='complete')
    assert calls==['cpu'] and not (resources/'jobs/reader/DISPATCH.json').exists()
