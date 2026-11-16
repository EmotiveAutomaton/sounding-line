"""Literal constructed identity controls; no claim of real service qualification."""
from pathlib import Path
from types import SimpleNamespace
import copy
import json
import os
import pytest
from runners.drive.cards import week6_process_services_v1 as m
from runners.drive.cards import week6_transition_services_v1 as transition


@pytest.fixture
def world(tmp_path,monkeypatch):
    repo=tmp_path/'repo';repo.mkdir()
    watcher=repo/'tools/codex_watch.py';venv=repo/'.venv/Scripts/python.exe'
    base=tmp_path/'python.exe';windowless=tmp_path/'pythonw.exe'
    files=[watcher,repo/'tools/codex_common.py',repo/'tools/codex_queue_api.py',
           repo/'runners/stage9/process_identity.py',venv,base,windowless]
    for i,path in enumerate(files):
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(('literal-'+str(i)).encode())
        os.utime(path,(100,100))
    code={str(p):m.filehash(p) for p in files[:4]};images={str(p):m.filehash(p) for p in files[4:]}
    for name,value in dict(REPO=repo,WATCHER=watcher,VENV=venv,BASE=base,WINDOWLESS=windowless,
                           CODE_PINS=code,IMAGE_PINS=images).items():monkeypatch.setattr(m,name,value)
    native=dict(pid=101,created_ticks=int((11644473600+1000)*10_000_000),executable=str(windowless))
    command=[str(windowless),'-B',str(watcher),'run']
    boot=dict(pid=101,started=1001.,source_sha256=code[str(watcher)],
              common_sha256=code[str(repo/'tools/codex_common.py')],
              queue_api_sha256=code[str(repo/'tools/codex_queue_api.py')])
    record=dict(kind='sounding-line-durable-watcher',owner_reviewed=True,native=native,
                command=command,cwd=str(repo),startup=boot,source_pins=code,
                image_pins={str(windowless):images[str(windowless)]})
    current=dict(native=native,command=command,cwd=str(repo),parent_pid=999)
    monkeypatch.setattr(m,'watcher_boot',lambda:copy.deepcopy(boot))
    monkeypatch.setattr(m,'observe',lambda pid:copy.deepcopy(current))
    return SimpleNamespace(repo=repo,record=record,boot=boot,current=current,files=files,images=images)


def test_exact_watcher_is_compatible(world):
    assert m.watcher_compatibility(world.record)==world.record['native']


@pytest.mark.parametrize('field,value',[
    ('kind','arbitrary-service'),('owner_reviewed',False),('source_pins',{}),('image_pins',{}),
    ('command',['python','tools/codex_watch.py','register-queue']),('cwd','wrong-workspace')])
def test_unreviewed_or_changed_service_contract(world,field,value):
    record=copy.deepcopy(world.record);record[field]=value
    with pytest.raises(ValueError):m.watcher_compatibility(record)


@pytest.mark.parametrize('index',[0,1,2,3,6])
def test_changed_source_or_image(world,index):
    world.files[index].write_bytes(b'changed implementation')
    with pytest.raises(ValueError):m.watcher_compatibility(world.record)


def test_changed_loaded_startup_pin(world,monkeypatch):
    boot=dict(world.boot,source_sha256='0'*64);monkeypatch.setattr(m,'watcher_boot',lambda:boot)
    with pytest.raises(ValueError):m.watcher_compatibility(world.record)


def test_same_code_rewritten_after_birth_refuses(world):
    os.utime(world.files[3],(1002,1002))
    with pytest.raises(ValueError,match='since process creation'):m.watcher_compatibility(world.record)


def test_pid_reuse_does_not_inherit_service_exemption(world,monkeypatch):
    row=copy.deepcopy(world.current);row['native']['created_ticks']+=1
    monkeypatch.setattr(m,'observe',lambda pid:row)
    with pytest.raises(ValueError,match='PID identity'):m.watcher_compatibility(world.record)


def test_exited_service_adds_no_identity(world,monkeypatch):
    monkeypatch.setattr(m,'observe',lambda pid:None)
    assert m.watcher_compatibility(world.record) is None


def test_unknown_service_identity_refuses(world,monkeypatch):
    def unknown(pid):raise PermissionError('constructed inaccessible identity')
    monkeypatch.setattr(m,'observe',unknown)
    with pytest.raises(PermissionError):m.watcher_compatibility(world.record)


@pytest.mark.parametrize('field,value',[('command',['python','-c','anything']),('cwd','elsewhere')])
def test_live_command_or_cwd_change(world,monkeypatch,field,value):
    row=copy.deepcopy(world.current);row[field]=value;monkeypatch.setattr(m,'observe',lambda pid:row)
    with pytest.raises(ValueError):m.watcher_compatibility(world.record)


def pair(world):
    command=[str(m.VENV),'-X','utf8','-B','-m','literal.reviewed.module','literal-root']
    parent=dict(native=dict(pid=201,created_ticks=100,executable=str(m.VENV)),command=command,
                cwd=str(world.repo),parent_pid=999)
    child=dict(native=dict(pid=202,created_ticks=200,executable=str(m.BASE)),command=command,
               cwd=str(world.repo),parent_pid=201)
    return parent,child


def test_exact_native_venv_pair(world):
    assert m.forwarder_pair(*pair(world))


@pytest.mark.parametrize('change',['parent','executable','command','cwd','old','after'])
def test_no_forwarder_basename_exemption(world,change):
    parent,child=copy.deepcopy(pair(world))
    if change=='parent':child['parent_pid']=301
    elif change=='executable':parent['native']['executable']=str(world.repo/'unreviewed/python.exe')
    elif change=='command':parent['command']=['python','-c','other code']
    elif change=='cwd':parent['cwd']='somewhere else'
    elif change=='old':child['native']['created_ticks']=60_000_101
    else:parent['native']['created_ticks']=201
    assert not m.forwarder_pair(parent,child)


def census(world,monkeypatch,rows,compatible=()):
    parent,caller=pair(world);caller['native']['pid']=os.getpid()
    allrows={parent['native']['pid']:parent,os.getpid():caller,**{r['native']['pid']:r for r in rows}}
    monkeypatch.setattr(m,'observe',lambda pid:copy.deepcopy(allrows.get(pid)))
    monkeypatch.setattr(m.psutil,'process_iter',lambda _: [SimpleNamespace(pid=pid,info={'name':'python.exe'}) for pid in allrows])
    def classify(command,cwd):
        return 'outside_workspace' if command==['outside'] else 'unknown_workspace'
    return m.check_census(compatible,classify,world.images)


def test_current_caller_native_forwarder_allowed(world,monkeypatch):
    assert census(world,monkeypatch,[])['python_processes']==2


def test_calendar_exact_owner_and_forwarder_allowed(world,monkeypatch):
    parent,child=pair(world);parent['native']['pid']=301;child['native']['pid']=302;child['parent_pid']=301
    assert census(world,monkeypatch,[parent,child],[child['native']])['python_processes']==4


@pytest.mark.parametrize('command',[
    ['python','-c','unknown budget read'],
    ['python','-m','runners.drive.cards.week6_runtime_extension_v2','frozen-root'],
    ['python','-m','runners.drive.cards.week6_runtime_services_v1','frozen-root'],
    ['python','-m','runners.drive.cards.week6_carried_runtime_v1','frozen-root'],
    ['python','tools/codex_hooks.py'],
])
def test_unknown_and_pre_owner_readers_refuse(world,monkeypatch,command):
    row=dict(native=dict(pid=303,created_ticks=300,executable=str(m.BASE)),command=command,
             cwd=str(world.repo),parent_pid=999)
    with pytest.raises(RuntimeError):census(world,monkeypatch,[row])


def test_reused_owned_pid_does_not_inherit_allowance(world,monkeypatch):
    row=copy.deepcopy(world.current);row['native']['created_ticks']+=1
    with pytest.raises(RuntimeError):census(world,monkeypatch,[row],[world.record['native']])


def test_unrelated_workspace_process_not_reclassified(world,monkeypatch):
    row=copy.deepcopy(world.current);row['command']=['outside'];row['cwd']='other project'
    assert census(world,monkeypatch,[row])['python_processes']==3


def test_unknown_census_identity_propagates(world,monkeypatch):
    monkeypatch.setattr(m,'observe',lambda pid:(_ for _ in ()).throw(PermissionError('literal unknown')))
    with pytest.raises(PermissionError):m.check_census([],lambda c,d:'outside_workspace',world.images)


def test_changed_forwarder_image_refuses(world,monkeypatch):
    m.VENV.write_bytes(b'changed forwarding binary')
    with pytest.raises(ValueError):census(world,monkeypatch,[])


def test_native_observation_rechecks_identity(world,monkeypatch):
    observations=iter([world.record['native'],dict(world.record['native'],created_ticks=1)])
    monkeypatch.setattr(m,'native_identity',lambda pid:next(observations))
    process=SimpleNamespace(cmdline=lambda:world.record['command'],cwd=lambda:str(world.repo),ppid=lambda:999)
    monkeypatch.setattr(m.psutil,'Process',lambda pid:process)
    # world replaced observe for service controls; use its preserved real body.
    with pytest.raises(ValueError,match='changed during observation'):_REAL_OBSERVE(101)


_REAL_OBSERVE=m.observe


@pytest.mark.parametrize('owner',['missing','changed','exact'])
def test_extension_native_requires_exact_owner_binding(world,monkeypatch,owner):
    campaign=world.repo/'campaign';attempt=campaign/'attempt';attempt.mkdir(parents=True)
    plan=attempt/'PLAN.json';plan.write_text(json.dumps(dict(campaign='S15-WEEK6',accounting_runtime=transition.EPOCH)))
    (attempt/'EXECUTE_NATIVE.json').write_text(json.dumps(world.record['native']))
    if owner!='missing':
        (attempt/'OWNER.json').write_text(json.dumps(dict(native=world.record['native'],
            plan_sha256=m.filehash(plan) if owner=='exact' else '0'*64)))
    seen=[];monkeypatch.setattr(m,'check_census',lambda allowed,*args:seen.extend(allowed))
    if owner=='exact':
        transition.check_process_census([],campaign,services=[],images=world.images)
        assert world.record['native'] in seen
    else:
        with pytest.raises(ValueError):transition.check_process_census([],campaign,services=[],images=world.images)
        assert not seen


def test_service_code_is_rechecked_after_census(world,monkeypatch):
    campaign=world.repo/'campaign';campaign.mkdir()
    monkeypatch.setattr(m,'check_census',lambda *args:world.files[0].write_bytes(b'changed during census'))
    with pytest.raises(ValueError,match='bytes changed'):
        transition.check_process_census([],campaign,services=[world.record],images=world.images)
