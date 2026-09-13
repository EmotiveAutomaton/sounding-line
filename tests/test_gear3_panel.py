"""Analyst V1-V10 fault fixtures. No provider or model access."""
from copy import deepcopy
from dataclasses import replace
import hashlib,json,threading,time
from pathlib import Path
import pytest
from runners import gear3_round1 as controller,gear3_campaign as cost,gear3_runtime
from runners.stage10 import gear3_batch as batch,gear3_io,gear3_inputs,gear3_comparison
from runners.stage10 import human_memory,human_memory_routes
from runners.stage10.contracts import digest
from tests.test_gear3_round1 import manifest,transport,profile
from tests.test_gear3_controller import account
from tests.test_gear3_comparison import make_cell
from runners.stage10 import human_memory_checks as fixtures


def test_stuck_cancellation_cannot_delay_app_stop():
    finish=threading.Event();events=[]
    try:
        result=controller.request_stop(lambda:finish.wait(10),lambda:events.append('app') or {},timeout_seconds=.01)
        assert events==['app'] and 'deadline' in result['call_error']
        assert 'owner_ended' not in result
    finally:finish.set()


def test_stuck_app_stop_still_attempts_cancellation():
    finish=threading.Event();events=[]
    try:
        with pytest.raises(RuntimeError,match='unresolved'):
            controller.request_stop(lambda:events.append('call'),lambda:finish.wait(10),timeout_seconds=.01)
        assert events==['call']
    finally:finish.set()


def test_installed_adapter_contract_and_wrong_version(monkeypatch):
    assert gear3_runtime.validate_runtime()['modal']=='1.5.4'
    monkeypatch.setattr(gear3_runtime.importlib.metadata,'version',lambda _: 'unsupported')
    with pytest.raises(ValueError,match='runtime'):gear3_runtime.validate_runtime()


def rehash(folder):
    for path in sorted(folder.rglob('COMPLETE.json'),key=lambda p:len(p.parts),reverse=True):
        obj=json.loads(path.read_text())
        obj['files']={p.relative_to(path.parent).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in path.parent.rglob('*') if p.is_file() and p!=path}
        path.write_text(json.dumps(obj))


@pytest.mark.parametrize('mutation',['forecast','missing-cost','execution','feedback'])
@pytest.mark.parametrize('complete',[False,True])
def test_rehashed_semantic_forgery_refused_before_new_call(tmp_path,monkeypatch,mutation,complete):
    requests=transport(monkeypatch);m=manifest();out=tmp_path/'block'
    if complete:batch.run_block(m,out)
    else:
        # R0,R2,R3 of first model retained, other model not attempted.
        with pytest.raises(InterruptedError):batch.run_block(m,out,stop_after=3)
    units=list((out/'units').glob('*/UNIT.json'))
    target=next(p for p in units if json.loads(p.read_text())['unit']['arm']==('R0' if mutation in {'forecast','missing-cost'} else 'R3'))
    saved=json.loads(target.read_text());route=target.parent/'route'
    if mutation in {'forecast','missing-cost'}:
        path=route/'ATTEMPT.json';v=json.loads(path.read_text())
        if mutation=='forecast':v['forecast']['explanation']='forged parse'
        else:v['cost'].pop('eval_count')
        path.write_text(json.dumps(v));saved['result']=deepcopy(v)
    elif mutation=='execution':
        path=route/'round-1/EXECUTION.json';v=json.loads(path.read_text());v['probabilities']={k:.25 for k in v['probabilities']};path.write_text(json.dumps(v))
    else:
        path=route/'round-2/proposal/REQUEST.json';v=json.loads(path.read_text());body=json.loads(v['request']['messages'][1]['content'])
        body['execution_of_own_previous_rules']['probabilities']={k:.25 for k in body['execution_of_own_previous_rules']['probabilities']}
        v['request']['messages'][1]['content']=json.dumps(body);path.write_text(json.dumps(v))
    rehash(route);saved['files']=gear3_io.inventory(route);target.write_text(json.dumps(saved))
    if complete:
        path=out/'COMPLETE.json';v=json.loads(path.read_text());v['files']=gear3_io.inventory(out);v['files'].pop('COMPLETE.json');path.write_text(json.dumps(v))
    count=len(requests);before=gear3_io.inventory(out)
    with pytest.raises(ValueError):batch.run_block(m,out)
    assert len(requests)==count and gear3_io.inventory(out)==before


def test_recovery_root_is_single_and_payload_bound(tmp_path):
    book=cost.CampaignLedger(tmp_path/'ledger.json');book.enroll(controller.AUTHORITY,Path('docs/archive/study-specs/GEAR_3_ROUND_1_2026-09-13.md'))
    book.reserve('root','P',['original'],{'job_sha256':'one'},1000,0,approval='fixture',now=100)
    book.transition('root','SUBMITTED',call_id='original');book.transition('root','FAILED',owner_ended=True,evidence={ 'app_id':'ap-root'})
    with pytest.raises(ValueError,match='payload'):book.reserve('changed','Reserve',['other'],{'job_sha256':'one'},100,0,approval='fixture',now=200,recovery_of='root')
    r=book.reserve('repair','Reserve',['original'],{'job_sha256':'one'},100,0,approval='fixture',now=200,recovery_of='root')
    assert r['expires_at']<=1100
    book.transition('repair','SUBMITTED',call_id='repair');book.transition('repair','FAILED',owner_ended=True,evidence='fixture')
    with pytest.raises(ValueError,match='recovery of a recovery'):book.reserve('chain','Reserve',['original'],{'job_sha256':'one'},50,0,approval='fixture',now=250,recovery_of='repair')
    with pytest.raises(ValueError,match='only one'):book.reserve('sibling','Reserve',['original'],{'job_sha256':'one'},50,0,approval='fixture',now=250,recovery_of='root')


def test_settlement_meter_overlap_and_unrelated_use(tmp_path):
    acc=account(tmp_path/'account.json');start=acc['cycle_start_at'];now=time.time()
    book=cost.CampaignLedger(tmp_path/'ledger.json');book.enroll(controller.AUTHORITY,Path('docs/archive/study-specs/GEAR_3_ROUND_1_2026-09-13.md'))
    book.reserve('root','P',['cache'],{'authenticated_workspace_sha256':'a'*64},600,25,approval='fixture',cache=True)
    book.transition('root','SUBMITTED',call_id='call');book.transition('root','COMPLETE',owner_ended=True,evidence={'app_id':'app'})
    receipt={'provider_record_sha256':'b'*64,'baseline_sha256':digest(acc),'workspace_sha256':'a'*64,
             'cycle_start_at':start,'cycle_end_at':acc['cycle_end_at'],'observed_at':time.time(),
             'charge_cents':10,'app_id':'app','call_id':'call','status':'PROVIDER_CONFIRMED_FINAL','coverage':'entire-app-lifecycle'}
    settled=book.settle('root',receipt);assert settled['reserved_cents']==28 and settled['booked_cents']==10
    data=json.loads(book.path.read_text());controller.account_reservation_guard(acc,data,'A',3990)
    updated={**acc,'observed_at':time.time(),'metered_at_check_cents':10}
    updated['attribution']={'baseline_sha256':digest(acc),'snapshot_sha256':digest(updated),
                           'cycle_start_at':start,'cycle_end_at':acc['cycle_end_at'],'settlements':{'root':digest(receipt)}}
    controller.account_reservation_guard(updated,data,'A',3990)
    with pytest.raises(ValueError):book.settle('root',{**receipt,'charge_cents':0})
    updated['metered_at_check_cents']=11;updated['attribution']['snapshot_sha256']=digest({k:v for k,v in updated.items() if k!='attribution'})
    with pytest.raises(ValueError,match='repair reserve'):controller.account_reservation_guard(updated,data,'A',3990)
    # Without attribution even a refreshed meter must retain unknown overlap.
    updated.pop('attribution')
    with pytest.raises(ValueError):controller.account_reservation_guard(updated,data,'A',3990)


def test_capped_writer_and_case_breadth():
    rows=[{'writer':g,'i':i} for i in range(20) for g in range(5)]
    for cap in (2,8):
        kept=gear3_inputs.capped(rows,lambda r:r['writer'],cap,64)
        assert len(kept)==cap*5
    ghost=[{'group':g,'record':{'task_id':g+str(i)}} for g in ('one','two','three') for i in range(4)]
    order=gear3_inputs.case_first(ghost)
    assert len({r['group'] for r in order[:3]})==3
    assert gear3_inputs.case_first(list(reversed(ghost)))==order


def test_human_names_preserve_support_and_whole_examples():
    public,answers=fixtures.rows('signal');learned=human_memory.induce(public,answers);t=fixtures.task(100,2)
    opaque,_=human_memory_routes.representation_for(t,public,answers,learned,'R4-opaque',profile=profile())
    grounded,_=human_memory_routes.representation_for(t,public,answers,learned,'R4-grounded',profile=profile())
    stripped=deepcopy(grounded)
    for p in stripped['procedures']:p.pop('description')
    assert opaque==stripped
    assert opaque['procedures'] and all('training_uses' in p for p in opaque['procedures'])
