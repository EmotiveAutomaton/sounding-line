from datetime import datetime, timezone, timedelta
from pathlib import Path
import json
import pytest
from runners.drive.cards import midrun_policy as p


@pytest.mark.parametrize('projection,forecast,waiting,expected', [
    (1300,600,True,False), (7199,300,True,False),
    (7200,300,False,False), (7200,300,True,True),
    (8000,4000,True,False), (8001,4000,True,True)])
def test_forecast_boundary(projection, forecast, waiting, expected):
    assert p.forecast_yield(projection, forecast, waiting) is expected


def test_waiter_needs_fresh_real_plan(tmp_path):
    plan = tmp_path/'PLAN.json'; plan.write_text('{}')
    receipt = tmp_path/'waiting.json'
    now = datetime.now(timezone.utc)
    def put(expiry):
        receipt.write_text(json.dumps(dict(expires_at=expiry.isoformat(), reviewed=True,
            runnable=True, waiting_for_slot=True, plan_path=str(plan), plan_sha256=p.filehash(plan))))
    assert not p.reviewed_waiter(receipt, now)
    put(now+timedelta(seconds=30)); assert p.reviewed_waiter(receipt, now)
    put(now); assert not p.reviewed_waiter(receipt, now)
    put(now+timedelta(seconds=30)); plan.write_text('{"changed":true}')
    assert not p.reviewed_waiter(receipt, now)


def test_environment_does_not_excuse_invalid_science():
    assert p.environmental_evidence('os_refusal', dict(winerror=5,traceback_sha256='a'*64))
    assert p.environmental_evidence('memory_guard', dict(sample=dict(free_MiB=912)))
    for kind in ['invalid_data','code_bug','non_convergence','known_answer_failure']:
        assert not p.environmental_evidence(kind, dict(sample=dict(free_MiB=912)))
    assert not p.environmental_evidence('memory_guard', {})


def test_safety_yield_has_priority(tmp_path):
    assert p.yield_reason(tmp_path, {}, dict(ram_available_GiB=3,commit_headroom_GiB=40,disk_free_GiB=100)) == 'resource_floor_yield'


# Native subprocess fixture: no scientific outputs or mocked subprocesses.
def execute(output, inputs, config):
    import time
    from runners.stage14.common import freeze
    freeze(output/'FIRST_TENTH.json', dict(projected_seconds=3600))
    time.sleep(4)
    if (output/'YIELD_REQUEST.json').exists():
        raise ValueError('Sub-two-hour card incorrectly yielded')
    freeze(output/'ANSWER.json', dict(value=6*7))
    return dict(status='complete', value=42)


def verify(output, inputs, config):
    assert p.read(output/'ANSWER.json') == dict(value=42)
    return dict(verified=True)


def test_native_supervisor_does_not_yield_short_card(tmp_path):
    import os, subprocess, time
    if os.name != 'nt':
        pytest.skip('Native Windows supervision fixture')
    from runners.drive.cards.batch_runtime import PYTHON, REPO, atomic, native_identity
    root=tmp_path/'native'; root.mkdir()
    atomic(root/'PLAN.json',dict(card='policy-native-fixture',module=__name__,inputs={},config={},
        forecast_cpu_seconds=1,max_wall_seconds=60,max_output_bytes=1048576,
        pins={str(Path(__file__).resolve()):p.filehash(__file__)}))
    worker=subprocess.Popen([str(PYTHON),'-X','utf8','-B','-m',
        'runners.drive.cards.batch_runtime_v3','run',str(root)],cwd=REPO,
        stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,creationflags=0x08000000)
    owner=None
    try:
        until=time.monotonic()+20
        while not (root/'OWNER.json').exists():
            if worker.poll() is not None or time.monotonic()>until:
                raise AssertionError('No native owner handshake')
            time.sleep(.1)
        owner=p.read(root/'OWNER.json')
        assert native_identity(owner['native']['pid'])==owner['native']
        import psutil
        assert worker.pid in [ancestor.pid for ancestor in psutil.Process(owner['native']['pid']).parents()]
        atomic(root/'MONITOR_READY.json',dict(owner_sha256=p.filehash(root/'OWNER.json')))
        _,err=worker.communicate(timeout=45)
        assert worker.returncode==0,err.decode()
        assert p.read(root/'COMPLETE.json')['fresh_process_verified']
        assert not (root/'PAUSED.json').exists()
    finally:
        if owner and native_identity(owner['native']['pid'])==owner['native']:
            import psutil
            controller=psutil.Process(owner['native']['pid'])
            for child in controller.children(recursive=True): child.terminate()
            controller.terminate()
        if worker.poll() is None:
            worker.terminate();worker.wait(timeout=10)
