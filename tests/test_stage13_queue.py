from datetime import datetime,timezone
from pathlib import Path
import json
import sys
import pytest
from runners.stage13.common import atomic,freeze,bound,filehash
from runners.stage13.queue import topological
from runners.stage13 import worker
from runners.stage13.scoring import interval


def test_topological_late_parent_and_cycles():
    cards=[dict(id='consumer',requires=['producer']),dict(id='independent'),dict(id='producer',requires=['admission']),dict(id='admission')]
    names=[c['id'] for c in topological(cards)]
    assert names.index('admission')<names.index('producer')<names.index('consumer')
    with pytest.raises(ValueError):topological([dict(id='a',requires=['b']),dict(id='b',requires=['a'])])
    with pytest.raises(ValueError):topological([dict(id='a'),dict(id='a')])


def test_bounds_and_single_component_interval(tmp_path):
    atomic(tmp_path/'CONTRACT.json',dict(reporting='2030-01-02T00:00:00+00:00'))
    atomic(tmp_path/'ALLOCATION.json',dict(gear=1))
    at=datetime(2030,1,1,tzinfo=timezone.utc)
    assert bound(tmp_path,dict(resource='cpu',wall_seconds=100),at)
    with pytest.raises(RuntimeError):bound(tmp_path,dict(resource='gpu',wall_seconds=100),at)
    with pytest.raises(RuntimeError):bound(tmp_path,dict(resource='cpu',wall_seconds=86400),at)
    atomic(tmp_path/'PAUSE.json',{})
    with pytest.raises(RuntimeError):bound(tmp_path,dict(resource='cpu',wall_seconds=100),at)
    assert interval([0,1],['only','only'])['low'] is None


def test_worker_reentry_and_unknown_are_not_new_attempts(tmp_path,monkeypatch):
    atomic(tmp_path/'CONTRACT.json',dict(reporting='2030-01-02T00:00:00+00:00'))
    atomic(tmp_path/'ALLOCATION.json',dict(gear=1))
    card=dict(id='fixture',source_pins={},input_pins={},resource='cpu',wall_seconds=600,kind='infrastructure')
    cp=tmp_path/'card.json';atomic(cp,card);calls=[]
    def fake(c,out,raw,tick):
        calls.append(1);freeze(out/'OUTPUT.json',dict(known=42));tick()
    monkeypatch.setattr(worker,'handle',fake)
    first=worker.run(cp,tmp_path);second=worker.run(cp,tmp_path)
    assert first==second and calls==[1]
    atomic(tmp_path/'jobs/fixture/OUTPUT.json',dict(known=43))
    with pytest.raises(ValueError):worker.run(cp,tmp_path)
    card['id']='unknown';atomic(cp,card);atomic(tmp_path/'jobs/unknown/DISPATCH.json',dict(status='started'))
    with pytest.raises(RuntimeError):worker.run(cp,tmp_path)
    assert calls==[1]


def test_failed_gate_is_not_an_admission(tmp_path,monkeypatch):
    atomic(tmp_path/'CONTRACT.json',dict(reporting='2030-01-02T00:00:00+00:00'))
    atomic(tmp_path/'ALLOCATION.json',dict(gear=1));atomic(tmp_path/'jobs/gate/ADMISSION.json',dict(admitted=False))
    card=dict(id='blocked',source_pins={},resource='cpu',wall_seconds=100,kind='producer',gates=['gate'])
    cp=tmp_path/'card.json';atomic(cp,card)
    with pytest.raises(RuntimeError):worker.run(cp,tmp_path)
    assert not (tmp_path/'jobs/blocked/DISPATCH.json').exists()


def test_kernel_singleton_refuses_concurrent_owner(tmp_path):
    from tools.codex_common import singleton
    with singleton(tmp_path/'owner.lock'):
        with pytest.raises(OSError):
            with singleton(tmp_path/'owner.lock'):pass
    with singleton(tmp_path/'owner.lock'):pass


def test_native_queue_continues_independent_failure(tmp_path,monkeypatch):
    from runners import run_queue as engine
    monkeypatch.setattr(engine,'REPO',tmp_path);monkeypatch.setattr(engine,'STATUS',tmp_path/'results/status.json')
    monkeypatch.setattr(engine,'LOCK',tmp_path/'results/test.lock');monkeypatch.setattr(engine,'_LOCK_TOKEN',None)
    monkeypatch.setattr(sys,'argv',['fixture-native-queue'])
    # Known fixtures only, no model, network, corpus or study source.
    stages=[dict(name='expected_failure',cmd=[sys.executable,'-c','raise SystemExit(7)'],produces='results/bad.json',needs=[],resource='cpu',est=5,why='known failure'),
            dict(name='independent',cmd=[sys.executable,'-c',"from pathlib import Path;Path('results/good.json').write_text('{\"status\":\"complete\",\"fixture\":true}')"],produces='results/good.json',needs=[],resource='cpu',est=5,why='known independent success')]
    monkeypatch.setattr(engine,'STAGES',stages)
    try:engine.main()
    finally:engine._release_lock()
    state=json.loads((tmp_path/'results/status.json').read_text())
    assert state['stages'][0]['status'].startswith('FAILED')
    assert state['stages'][1]['status']=='DONE'
