"""Constructed checks for reviewed local admission; no participant sources.

DESIGN CHECK: LESSONS 3-5. Reviewed exact bytes pass under either scientific
outcome; missing/altered/failed evidence and scope changes refuse. Native scratch
runs exercise execution, replay, output limits and source checks without Git.
"""
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import threading
import time
import pytest
import numpy  # expose actual numerical pools to the independent witness
from runners.drive.cards import week6_local_review_v1 as local
from runners.drive.cards import week6_launch_services_v5 as launch
from runners.drive.cards import week6_policy_services_v5 as policy
from runners.drive.cards import week6_runtime_services_v5 as runtime
from runners.drive.cards.batch_runtime import filehash, read, freeze


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding='utf8')
    return path


def seal(p, m, path):
    p.pop('reviewed_local_manifest', None)
    p['pins'].pop(str(path), None)
    m['plan_sha256'] = local.contract_digest(p)
    put(path, m)
    p['reviewed_local_manifest'] = dict(path=str(path), sha256=filehash(path))
    p['pins'][str(path)] = filehash(path)


def candidate(tmp_path, monkeypatch):
    monkeypatch.setattr(local, 'require_exited', lambda native: None)
    design=tmp_path/'DESIGN.md';design.write_text('constructed-only design',encoding='utf8')
    source=tmp_path/'fixture-source.py';source.write_text('# constructed',encoding='utf8')
    qp=put(tmp_path/'fixture/PLAN.json',dict(owner={'constructed':True}))
    child=put(qp.parent/'CHILD.json',dict(native={'constructed':True}))
    q=put(qp.parent/'COMPLETE.json',dict(status='COMPLETE',error=None,constructed_only=True,
        lease_released=True,cases=1,source_pins={str(source):filehash(source)},
        outputs={str(x):filehash(x) for x in (qp,child)}))
    p=dict(owner_reviewed=True,fixture_passed=True,review_owner='constructed-owner',
        design=str(design),reviewed_design_commit=None,validation_receipts=[str(q)],
        accounting_runtime='week6-extension-v2',module='runners.drive.cards.week6_runtime_fixture_v1',
        card='constructed-local-review',family='CH',budget_key='CH14',campaign='S15-WEEK6',
        operating_gear=2,paid=False,gpu=False,ollama=False,numerical_threads=2,
        max_cpu_seconds=60,max_wall_seconds=60,projected_peak_ram_GiB=1,
        inputs={'literal':[2,3,5]},config={'scenario':'normal'},
        pins={str(x):filehash(x) for x in (design,source,q,local.AUTHORITY)})
    for src in launch.closure([p['module'],*launch.MODULES]):p['pins'][str(src)]=filehash(src)
    m=dict(schema='WEEK6_LOCAL_REVIEW_V1',owner_reviewed=True,owner=p['review_owner'],
        at=datetime.now(timezone.utc).isoformat(),authority=dict(path=str(local.AUTHORITY),sha256=filehash(local.AUTHORITY)),
        fixtures=[dict(path=str(q),sha256=filehash(q),cases=1)])
    path=tmp_path/'LOCAL_REVIEW.json';seal(p,m,path)
    return p,m,path,q,source


def test_exact_local_review_without_any_git_call(tmp_path,monkeypatch):
    p,*_=candidate(tmp_path,monkeypatch)
    monkeypatch.setattr(local.subprocess,'run',lambda *a,**k:pytest.fail('Git called for local review'))
    assert local.review_design(p)=='local-reviewed'
    launch.review(p)


@pytest.mark.parametrize('key,value', [('card','other'),('family','LA'),('budget_key','LA6'),
    ('inputs',{'literal':[9]}),('config',{'scenario':'other'}),('max_cpu_seconds',80001),
    ('max_wall_seconds',999999),('operating_gear',3),('paid',True),('gpu',True),
    ('numerical_threads',3),('review_owner','other')])
def test_changed_reviewed_plan_refuses(tmp_path,monkeypatch,key,value):
    p,*_=candidate(tmp_path,monkeypatch);p[key]=value
    with pytest.raises(ValueError):launch.review(p)


@pytest.mark.parametrize('target',['design','source','manifest','receipt','output'])
def test_changed_evidence_refuses(tmp_path,monkeypatch,target):
    p,m,path,q,source=candidate(tmp_path,monkeypatch)
    item={'design':Path(p['design']),'source':source,'manifest':path,'receipt':q,'output':q.parent/'CHILD.json'}[target]
    item.write_text('changed',encoding='utf8')
    with pytest.raises((ValueError,RuntimeError)):launch.review(p)


@pytest.mark.parametrize('field,value',[('status','FAILED'),('error','failed'),('constructed_only',False),('lease_released',False),('cases',0)])
def test_resealed_failed_fixture_is_still_refused(tmp_path,monkeypatch,field,value):
    p,m,path,q,_=candidate(tmp_path,monkeypatch);v=read(q);v[field]=value;put(q,v)
    p['pins'][str(q)]=filehash(q);m['fixtures'][0]['sha256']=filehash(q);seal(p,m,path)
    with pytest.raises(ValueError):launch.review(p)


@pytest.mark.parametrize('condition',['absent','wrong_owner','future','missing_fixture','fake_commit'])
def test_review_contract_refusals(tmp_path,monkeypatch,condition):
    p,m,path,q,_=candidate(tmp_path,monkeypatch)
    if condition=='absent':p.pop('reviewed_local_manifest')
    elif condition=='fake_commit':p['reviewed_design_commit']='local';seal(p,m,path)
    else:
        if condition=='wrong_owner':m['owner']='other'
        elif condition=='future':m['at']='2999-01-01T00:00:00+00:00'
        else:m['fixtures']=[]
        seal(p,m,path)
    with pytest.raises(ValueError):launch.review(p)


def test_native_identity_failure_is_not_ignored(tmp_path,monkeypatch):
    p,*_=candidate(tmp_path,monkeypatch)
    def refusal(native):raise RuntimeError('native identity unknown')
    monkeypatch.setattr(local,'require_exited',refusal)
    with pytest.raises(RuntimeError,match='unknown'):launch.review(p)


def test_real_commit_route_still_compares_exact_bytes(tmp_path,monkeypatch):
    p,*_=candidate(tmp_path,monkeypatch);p.pop('reviewed_local_manifest');p['reviewed_design_commit']='actual-commit'
    class Response:stdout=Path(p['design']).read_bytes()
    calls=[]
    def run(argv,**kwargs):calls.append(argv);return Response()
    monkeypatch.setattr(local.subprocess,'run',run)
    assert local.review_design(p)=='committed'
    assert calls[0][:2]==['git','show']
    Response.stdout=b'changed'
    with pytest.raises(ValueError):local.review_design(p)


def test_policy_and_runtime_retain_predecessor_guards():
    root=local.REPO/'runners/drive/cards'
    old=(root/'week6_policy_services_v4.py').read_text('utf8')
    new=(root/'week6_policy_services_v5.py').read_text('utf8')
    replacement="    if not plan.get('fixture_passed') or not plan.get('reviewed_design_commit'):\n        raise ValueError('Reviewed committed design and passed native fixture required')"
    assert new.replace('    from .week6_local_review_v1 import review_design\n    review_design(plan)',replacement)==old
    old=(root/'week6_runtime_services_v4.py').read_text('utf8')
    new=(root/'week6_runtime_services_v5.py').read_text('utf8')
    assert new.replace('week6_policy_services_v5','week6_policy_services_v4').replace('    from .week6_launch_services_v5 import review\n    review(plan)\n','')==old


@pytest.mark.parametrize('scenario,terminal',[('normal','COMPLETE'),('execute_yield','PAUSED'),('verify_overcap','FAILED')])
def test_native_scratch_execution_and_fresh_replay(tmp_path,monkeypatch,scenario,terminal):
    p,m,path,q,_=candidate(tmp_path,monkeypatch)
    root=tmp_path/'attempt';root.mkdir();p['attempt_root']=str(root);p['config']['scenario']=scenario
    p['max_output_bytes']=1024 if scenario=='verify_overcap' else 1048576
    seal(p,m,path);freeze(root/'PLAN.json',p)
    slots=tmp_path/'slots';slots.mkdir()
    monkeypatch.setattr(policy,'OLD_SLOTS',slots);monkeypatch.setattr(policy,'NEW_SLOTS',slots)
    # Only the external campaign/resources are replaced in this constructed
    # scratch. Actual review, lease, native child, replay and byte guards run.
    def admit(plan):
        local.review_design(plan)
        return dict(remaining_cpu_seconds=60,constructed_resource_provider=True)
    monkeypatch.setattr(policy,'admission',admit)
    monkeypatch.setattr(policy,'post_claim',lambda:{'constructed':True})
    monkeypatch.setattr(policy,'available',lambda *a,**k:1000)
    monkeypatch.setattr(policy,'yield_reason',lambda *a,**k:None)
    def monitor():
        deadline=time.monotonic()+20
        while not (root/'OWNER.json').exists():
            assert time.monotonic()<deadline;time.sleep(.05)
        freeze(root/'MONITOR_READY.json',dict(owner_sha256=filehash(root/'OWNER.json')))
    t=threading.Thread(target=monitor);t.start()
    try:
        if terminal=='FAILED':
            with pytest.raises(RuntimeError,match='byte cap'):runtime.run(root)
        else:runtime.run(root)
    finally:t.join(timeout=20)
    result=read(root/(terminal+'.json'));assert result['status']==terminal
    assert result['cpu_seconds']>0 and not list(slots.glob('slot-*.json'))
    assert (root/'EXECUTE_JOB_USAGE.json').exists()
    if terminal=='COMPLETE':assert read(root/'VERIFIED.json')['verified'] is True
    with pytest.raises(FileExistsError):runtime.run(root)

