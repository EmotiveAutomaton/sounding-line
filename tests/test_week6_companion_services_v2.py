"""Constructed companion ownership, refusal and slot-race qualification.

DESIGN CHECK: immutable evidence and infrastructure lessons. Valid counted
readers pass under either scientific direction; changed or absent proof refuses.
Capacity overflow releases only our new lease. No human records are used.
"""
from contextlib import nullcontext
from datetime import datetime, timezone
from pathlib import Path
import copy
import json
import time
import pytest
from runners.drive.cards import week6_companion_proof_v1 as proof
from runners.drive.cards import week6_policy_services_v2 as policy
from runners.drive.cards import week6_runtime_services_v2 as runtime


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding='utf8')


@pytest.fixture
def example(tmp_path, monkeypatch):
    root=tmp_path/'companion';output=root/'.local/trigger/cell';slot=tmp_path/'slots/slot-0.json'
    launcher=root/'scripts/engine-readers-job.py';helper=root/'scripts/engine-two-day-job.py'
    venv=root/'venv/python.exe';base=root/'base/python.exe';snapshot=output/'code/a.py'
    for p in (launcher,helper,venv,base,snapshot):
        p.parent.mkdir(parents=True,exist_ok=True);p.write_text('fixture',encoding='utf8')
    born=time.time()+1;ticks=int((born+11644473600)*10000000)
    native=dict(pid=9001,created_ticks=ticks,executable=str(base))
    parent_native=dict(pid=9000,created_ticks=ticks-10000,executable=str(venv))
    command=[str(venv),'scripts/engine-readers-job.py','--seed','71','--fold','3','--output',str(output)]
    worker=dict(native=native,cwd=str(root),command=command,parent_pid=9000)
    parent=dict(native=parent_native,cwd=str(root),command=list(command),parent_pid=8999)
    observed={9001:worker,9000:parent}
    env={k:'2' for k in proof.THREADS};env['CUDA_VISIBLE_DEVICES']='-1'
    monkeypatch.setattr(proof.service,'observe',lambda pid:copy.deepcopy(observed.get(pid)))
    monkeypatch.setattr(proof,'environment',lambda pid:dict(env))
    stamp=lambda s:datetime.fromtimestamp(s,timezone.utc).isoformat()
    lease=dict(native=copy.deepcopy(native),card=proof.CARD,at=stamp(born+1),projected_peak_ram_GiB=6,output=str(output))
    manifest={'a.py':proof.filehash(snapshot)}
    plan=dict(card='TP23',threads=2,hours=1,deadlineAt=stamp(born+3601),launcherSha256=proof.filehash(launcher),snapshotFiles=manifest)
    source_pins={str(p):proof.filehash(p) for p in (launcher,helper,proof.REPO/'runners/drive/cards/week5_policy_v2.py')}
    record=dict(kind=proof.KIND,owner_reviewed=True,root=str(root),venv=str(venv),base=str(base),source_pins=source_pins,
                image_pins={str(p):proof.filehash(p) for p in (venv,base)},snapshot_files=copy.deepcopy(manifest),
                command_template=[str(venv),'scripts/engine-readers-job.py','--seed','{seed}','--fold','{fold}','--output','{output}'])
    owner=output/'owner.json';lock=root/'.local/bench/two-day-scoring.lock'
    write(slot,lease);write(owner,dict(lease,lease=str(slot)));write(lock,lease);write(output/'plan.json',plan)
    return dict(root=root,output=output,slot=slot,lease=lease,record=record,plan=plan,owner=owner,lock=lock,
                worker=worker,parent=parent,observed=observed,env=env,launcher=launcher,base=base,snapshot=snapshot,
                at=datetime.fromtimestamp(born+2,timezone.utc))


@pytest.mark.parametrize('threads',['1','2'])
def test_valid_counted_reader_within_ceiling(example,threads):
    x=example;x['env'].update({k:threads for k in proof.THREADS})
    assert proof.prove_lease(x['slot'],x['lease'],x['record'],at=x['at'])==[x['worker']['native'],x['parent']['native']]


@pytest.mark.parametrize('fault',[
    'stale_pid','parent_image','parent_command','parent_cwd','parent_birth','worker_cwd','seed','fold',
    'owner','exclusive_lock','source','image','snapshot','extra_snapshot','escaped_snapshot','expired',
    'duplicate_key','threads','gpu','missing_source','unreviewed','role','memory','missing_parent'])
def test_changed_or_incomplete_proof_refuses(example,fault):
    x=example
    if fault=='stale_pid':x['worker']['native']['created_ticks']+=1
    elif fault=='parent_image':x['parent']['native']['executable']='elsewhere'
    elif fault=='parent_command':x['parent']['command'].append('extra')
    elif fault=='parent_cwd':x['parent']['cwd']='elsewhere'
    elif fault=='parent_birth':x['parent']['native']['created_ticks']-=100000000
    elif fault=='worker_cwd':x['worker']['cwd']='elsewhere'
    elif fault=='seed':x['worker']['command'][3]='99'
    elif fault=='fold':x['worker']['command'][5]='5'
    elif fault=='owner':write(x['owner'],{})
    elif fault=='exclusive_lock':write(x['lock'],{})
    elif fault=='source':x['launcher'].write_text('changed')
    elif fault=='image':x['base'].write_text('changed')
    elif fault=='snapshot':x['snapshot'].write_text('changed')
    elif fault=='extra_snapshot':x['snapshot'].with_name('extra.py').write_text('extra')
    elif fault=='escaped_snapshot':
        x['plan']['snapshotFiles']={'../a.py':'0'*64};x['record']['snapshot_files']=x['plan']['snapshotFiles'];write(x['output']/'plan.json',x['plan'])
    elif fault=='expired':x['plan']['deadlineAt']='2000-01-01T00:00:00+00:00';write(x['output']/'plan.json',x['plan'])
    elif fault=='duplicate_key':x['owner'].write_text('{"x":1,"x":2}')
    elif fault=='threads':x['env']['OMP_NUM_THREADS']='3'
    elif fault=='gpu':x['env']['CUDA_VISIBLE_DEVICES']='0'
    elif fault=='missing_source':x['record']['source_pins'].pop(str(x['launcher']))
    elif fault=='unreviewed':x['record']['owner_reviewed']=False
    elif fault=='role':x['lease']['card']='other'
    elif fault=='memory':x['lease']['projected_peak_ram_GiB']=5
    elif fault=='missing_parent':x['observed'].pop(9000)
    with pytest.raises((ValueError,FileNotFoundError,KeyError)):
        proof.prove_lease(x['slot'],x['lease'],x['record'],at=x['at'])


def test_missing_lease_confers_no_exemption(example,monkeypatch):
    x=example;monkeypatch.setattr(proof,'SLOTS',(x['slot'].parent,));x['slot'].unlink()
    assert proof.reader_compatibility(x['record'])==[]


def test_duplicate_companion_leases_refuse(example,monkeypatch):
    x=example;monkeypatch.setattr(proof,'SLOTS',(x['slot'].parent,));write(x['slot'].with_name('slot-1.json'),x['lease'])
    with pytest.raises(ValueError,match='Multiple companion'):proof.reader_compatibility(x['record'])


@pytest.mark.parametrize('occupied,active,passes',[(8,False,True),(9,False,False),(8,True,False),(7,True,True)])
def test_post_claim_capacity(occupied,active,passes,monkeypatch):
    monkeypatch.setattr(policy,'lease_paths',lambda:list(range(occupied)))
    monkeypatch.setattr(policy,'shared_reservation',lambda:dict(active=active))
    monkeypatch.setattr(policy,'memory_reserve',lambda paths:2*len(paths))
    monkeypatch.setattr(policy,'resource_snapshot',lambda:dict(ram_available_GiB=64,commit_headroom_GiB=64,disk_free_GiB=100))
    if passes:assert policy.post_claim()['disk_free_GiB']==100
    else:
        with pytest.raises(RuntimeError,match='capacity'):policy.post_claim()


@pytest.mark.parametrize('field',['ram_available_GiB','commit_headroom_GiB','disk_free_GiB'])
def test_post_claim_resource_refusal(field,monkeypatch):
    values=dict(ram_available_GiB=64,commit_headroom_GiB=64,disk_free_GiB=100);values[field]=10
    monkeypatch.setattr(policy,'lease_paths',lambda:[]);monkeypatch.setattr(policy,'shared_reservation',lambda:dict(active=False))
    monkeypatch.setattr(policy,'memory_reserve',lambda paths:0);monkeypatch.setattr(policy,'resource_snapshot',lambda:values)
    with pytest.raises(RuntimeError):policy.post_claim()


def test_failed_post_claim_releases_only_own_lease(tmp_path,monkeypatch):
    old=tmp_path/'old';new=tmp_path/'new';old.mkdir();new.mkdir()
    foreign=old/'slot-0.json';write(foreign,dict(owner='foreign'));before=foreign.read_bytes()
    monkeypatch.setattr(policy,'OLD_SLOTS',old);monkeypatch.setattr(policy,'NEW_SLOTS',new)
    monkeypatch.setattr(runtime.kernel,'admission_lock',lambda path:nullcontext())
    monkeypatch.setattr(policy,'admission',lambda plan:{})
    monkeypatch.setattr(runtime,'native_identity',lambda:dict(pid=1,created_ticks=2,executable='fixture'))
    def reject():raise RuntimeError('Post-claim counted capacity exceeded')
    monkeypatch.setattr(policy,'post_claim',reject)
    with pytest.raises(RuntimeError,match='capacity'):
        runtime.claim(tmp_path/'attempt',dict(card='fixture',family='ES',projected_peak_ram_GiB=2))
    assert foreign.read_bytes()==before and not list(new.glob('slot-*.json'))


def test_unknown_unleased_workspace_process_still_refuses():
    from runners.drive.cards.week6_transition_services_v2 import classify_process
    assert classify_process(['python','unknown.py'],str(proof.REPO))=='unknown_workspace'


def test_original_execution_and_accounting_bodies_preserved():
    from runners.drive.cards import week6_runtime_services_v1 as old
    import inspect
    assert inspect.getsource(runtime.run)==inspect.getsource(old.run)
    assert inspect.getsource(runtime.failure_charge)==inspect.getsource(old.failure_charge)
