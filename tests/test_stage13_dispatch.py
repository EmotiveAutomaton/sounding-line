from pathlib import Path
import sys
import json
import pytest
from runners.stage13 import dispatch
from runners.stage13.common import atomic, filehash


def fixture(tmp_path, names):
    cards=[]
    for name, deps in names:
        c=dict(id=name,requires=deps,gates=[],resource='cpu',wall_seconds=30,
               source_pins={},input_pins={})
        atomic(tmp_path/'manifests'/f'{name}.json',c);cards.append(c)
    return cards


def done(raw,c):
    atomic(raw/'jobs'/c['id']/'COMPLETE.json',dict(status='complete',outputs={},
        card_sha256=filehash(raw/'manifests'/f"{c['id']}.json")))


def test_late_parent_gates_and_unknown(tmp_path):
    cards=fixture(tmp_path,[('child',['parent']),('parent',[])])
    states=dispatch.inventory(tmp_path,cards,{})
    assert not dispatch.eligible(cards[0],states,tmp_path)
    done(tmp_path,cards[1]);states=dispatch.inventory(tmp_path,cards,{})
    assert dispatch.eligible(cards[0],states,tmp_path)
    cards[0]['gates']=['parent'];atomic(tmp_path/'jobs/parent/ADMISSION.json',dict(admitted=False))
    assert dispatch.inventory(tmp_path,cards,{})['child']=='BLOCKED'
    atomic(tmp_path/'jobs/child/DISPATCH.json',{})
    with pytest.raises(RuntimeError,match='unknown attempt'):dispatch.inventory(tmp_path,cards,{})


def test_actual_dispatch_completion_failure_and_reentry(tmp_path,monkeypatch):
    cards=fixture(tmp_path,[('consumer',['producer']),('failure',[]),('producer',[]),('blocked',['failure'])])
    atomic(tmp_path/'CONTRACT.json',dict(reporting='2030-01-01T00:00:00+00:00'))
    atomic(tmp_path/'ALLOCATION.json',dict(gear=2))
    plan=dict(id='fixture',cpu_workers=2,cards=[c['id'] for c in cards],
        source_pins={},contract_sha256=filehash(tmp_path/'CONTRACT.json'),
        dispatcher_sha256=filehash(Path(dispatch.__file__)),
        manifest_hashes={c['id']:filehash(tmp_path/'manifests'/f"{c['id']}.json") for c in cards})
    pp=tmp_path/'plan.json';atomic(pp,plan)
    monkeypatch.setattr(dispatch,'REPO',tmp_path)
    commands=[]
    def command(c,p,raw):
        commands.append(c['id']);out=raw/'jobs'/c['id']
        record=(dict(status='failed',error='known failure') if c['id']=='failure' else
            dict(status='complete',outputs={},card_sha256=filehash(raw/'manifests'/f"{c['id']}.json")))
        terminal='FAILED.json' if c['id']=='failure' else 'COMPLETE.json'
        script='from pathlib import Path;import json,time;time.sleep(.05);p=Path('+repr(str(out/terminal))+');p.parent.mkdir(parents=True,exist_ok=True);p.write_text('+repr(json.dumps(record))+')'
        return [sys.executable,'-B','-c',script]
    monkeypatch.setattr(dispatch,'worker_command',command)
    monkeypatch.setattr(dispatch.subprocess,'run',lambda *a,**k:None)
    original_sleep=dispatch.time.sleep
    monkeypatch.setattr(dispatch.time,'sleep',lambda n:original_sleep(min(n,.05)))
    dispatch.run(pp,tmp_path)
    s=json.loads((tmp_path/'queue/fixture/STATUS.json').read_text())
    assert s['states']==dict(consumer='DONE',failure='FAILED',producer='DONE',blocked='BLOCKED')
    assert commands.index('producer')<commands.index('consumer')
    assert commands.count('producer')==1 and 'blocked' not in commands
    assert dispatch.inventory(tmp_path,cards,{})==s['states']


def test_live_prior_coordinator_refuses_before_owner_write(tmp_path):
    from runners.stage9.process_identity import native_identity
    atomic(tmp_path/'CONTRACT.json',dict(reporting='2030-01-01T00:00:00+00:00'))
    p=dict(id='refuse',cards=[],cpu_workers=1,source_pins={},manifest_hashes={},
        contract_sha256=filehash(tmp_path/'CONTRACT.json'),dispatcher_sha256=filehash(Path(dispatch.__file__)),
        prior_owners=[native_identity()])
    pp=tmp_path/'plan.json';atomic(pp,p)
    with pytest.raises(RuntimeError,match='prior coordinator'):dispatch.run(pp,tmp_path)
    assert not (tmp_path/'queue/refuse/OWNER.json').exists()


def test_adopted_native_worker_finishes_without_redispatch(tmp_path,monkeypatch):
    import subprocess
    from runners.stage9.process_identity import native_identity
    cards=fixture(tmp_path,[('existing',[])])
    atomic(tmp_path/'CONTRACT.json',dict(reporting='2030-01-01T00:00:00+00:00'))
    atomic(tmp_path/'ALLOCATION.json',dict(gear=2))
    out=tmp_path/'jobs/existing'
    result=dict(status='complete',outputs={},card_sha256=filehash(tmp_path/'manifests/existing.json'))
    script='from pathlib import Path;import time;time.sleep(.8);p=Path('+repr(str(out/'COMPLETE.json'))+');p.write_text('+repr(json.dumps(result))+')'
    proc=subprocess.Popen([sys.executable,'-B','-c',script])
    try:
        native=native_identity(proc.pid)
        atomic(out/'DISPATCH.json',dict(at=dispatch.now(),native=native))
        plan=dict(id='adopt',cpu_workers=2,cards=['existing'],source_pins={},
            contract_sha256=filehash(tmp_path/'CONTRACT.json'),
            dispatcher_sha256=filehash(Path(dispatch.__file__)),
            manifest_hashes={'existing':filehash(tmp_path/'manifests/existing.json')},adopt={'existing':native})
        pp=tmp_path/'plan.json';atomic(pp,plan)
        monkeypatch.setattr(dispatch,'worker_command',lambda *a:pytest.fail('adopted worker redispatched'))
        # Isolate adoption; environment construction has its own native regression.
        original_command=dispatch.worker_command
        monkeypatch.setattr(dispatch,'worker_command',lambda *a:[sys.executable,'-B','-c','pass'])
        monkeypatch.setattr(dispatch.subprocess,'run',lambda *a,**k:None)
        monkeypatch.setattr(dispatch.subprocess,'Popen',lambda *a,**k:pytest.fail('adopted worker redispatched'))
        original_sleep=dispatch.time.sleep
        monkeypatch.setattr(dispatch.time,'sleep',lambda n:original_sleep(min(n,.05)))
        dispatch.run(pp,tmp_path)
        assert json.loads((tmp_path/'queue/adopt/STATUS.json').read_text())['states']=={'existing':'DONE'}
        assert proc.wait(timeout=3)==0
    finally:
        if proc.poll() is None:proc.terminate();proc.wait(timeout=3)


def test_worker_environment_survives_native_coordinator_sysconfig(tmp_path):
    import subprocess,sysconfig
    plan=dict(source_capsule='capsule',python_site_packages=sysconfig.get_paths()['purelib'])
    command=dispatch.worker_command(dict(id='fixture'),plan,tmp_path)[:4]
    command[3]=command[3].split(';runpy.run_module(')[0]+";import psutil,torch,numpy,scipy,transformers;print('environment-ok')"
    result=subprocess.run(command,cwd=dispatch.REPO,capture_output=True,text=True,timeout=60)
    assert result.returncode==0,result.stderr
    assert 'environment-ok' in result.stdout
