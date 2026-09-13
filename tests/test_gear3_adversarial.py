"""Additional fault-injection checks before any paid Round 1 execution."""
from copy import deepcopy
import json
from types import SimpleNamespace
import pytest
from runners import gear3_round1 as controller
from runners.stage10 import gear3_batch as batch
from tests.test_gear3_round1 import manifest, transport

@pytest.mark.parametrize('field', ['result', 'profile', 'unit'])
def test_partial_resume_revalidates_entire_saved_unit_before_new_calls(tmp_path, monkeypatch, field):
    requests = transport(monkeypatch); m = manifest(); out = tmp_path/'partial'
    with pytest.raises(InterruptedError):
        batch.run_block(m, out, stop_after=1)
    p = next(out.rglob('UNIT.json')); saved = json.loads(p.read_text())
    if field == 'result':
        saved['result']['forecast']['explanation'] = 'forged retained answer'
    elif field == 'profile':
        saved['profile']['model_digest'] = 'a'*64
    else:
        saved['unit']['arm'] = 'R3'
    p.write_text(json.dumps(saved))
    count = len(requests)
    with pytest.raises(ValueError):
        batch.run_block(m, out)
    assert len(requests) == count

def test_cancellation_attempts_app_stop_even_if_call_cancel_raises():
    events = []
    def bad_call():
        events.append('call'); raise OSError('call cancellation unavailable')
    def stop_app():
        events.append('app'); return {'app_id': 'ap-fixture'}
    result = controller.request_stop(bad_call, stop_app)
    assert events == ['call', 'app'] and result['app_stop']['app_id'] == 'ap-fixture'
    assert 'call cancellation unavailable' in result['call_error']

def test_cancel_reports_both_failed_paths():
    events = []
    def fail(name):
        def run():
            events.append(name); raise OSError(name+' failed')
        return run
    with pytest.raises(RuntimeError, match='app failed'):
        controller.request_stop(fail('call'), fail('app'))
    assert events == ['call', 'app']

@pytest.mark.parametrize('actual', [{'workspace': 'wrong', 'workspace_id': 'wk-other'}, {'workspace': 'inspected', 'workspace_id': ''}, {'workspace': 'inspected', 'workspace_id': 'wk-correct'}])
def test_actual_authenticated_workspace_must_match_billing(monkeypatch, actual):
    import sys
    client = object()
    monkeypatch.setitem(sys.modules, 'modal', SimpleNamespace(Client=SimpleNamespace(from_env=lambda: client)))
    monkeypatch.setattr(controller, 'workspace_info', lambda c: actual if c is client else pytest.fail('client changed'))
    if actual['workspace'] != 'inspected' or not actual['workspace_id']:
        with pytest.raises(ValueError, match='authenticated workspace'):
            controller.provider_client({'workspace': 'inspected'})
    else:
        assert controller.provider_client({'workspace': 'inspected'}) == (client, actual)

@pytest.mark.parametrize('node', ['A', 'C'])
def test_scientific_target_writer_cannot_overlap_training(node):
    m = manifest(node)
    m['tasks'][0]['group'] = m['training']['coauthor-handling']['answers'][0]['writer_component']
    with pytest.raises(ValueError, match='training source group'):
        batch.validate(m)


def test_timeout_rpc_contract_uses_no_retry(monkeypatch):
    import asyncio
    from modal._utils.async_utils import synchronizer
    observed=[]
    monkeypatch.setattr(synchronizer,'create_blocking',lambda f: lambda *a,**k: asyncio.run(f(*a,**k)))
    async def info(request,**kwargs):
        assert kwargs=={'timeout':15,'retry':None}; observed.append('info')
        return SimpleNamespace(workspace_name='fixture',workspace_id='wk-fixture')
    async def stop(request,**kwargs):
        assert request.app_id=='ap-fixture' and kwargs=={'timeout':15,'retry':None}; observed.append('stop')
    client=SimpleNamespace(stub=SimpleNamespace(TokenInfoGet=info,AppStop=stop))
    assert controller.workspace_info(client)['workspace']=='fixture'
    assert controller.stop_app_rpc(client,'ap-fixture')['app_id']=='ap-fixture'
    assert observed==['info','stop']


def test_smaller_workspace_keeps_storage_and_repair_reserve(tmp_path):
    from tests.test_gear3_controller import account
    from runners import gear3_campaign as cost
    from pathlib import Path
    p=tmp_path/'account.json'; v=account(p)
    v.update(usage_limit_cents=4250,metered_at_check_cents=1,net_spend_limit_cents=1250,remaining_credits_cents=3000,other_workloads='retained-storage-only',storage_allowance_cents=100)
    p.write_text(json.dumps(v)); assert controller.account_backstop(p)==v
    assert controller.account_campaign_cap(v)==4149
    controller.account_reservation_guard(v,{'runs':[]},'A',3149)
    with pytest.raises(ValueError,match='repair reserve'):controller.account_reservation_guard(v,{'runs':[]},'A',3150)
    for key,value in [('payment_method_present',False),('storage_allowance_cents',0),('cycle_end_at',v['observed_at']-1)]:
        p.write_text(json.dumps({**v,key:value}))
        with pytest.raises(ValueError):controller.account_backstop(p)
    book=cost.CampaignLedger(tmp_path/'ledger.json')
    book.enroll(controller.AUTHORITY,Path('docs/archive/study-specs/GEAR_3_ROUND_1_2026-09-13.md'))
    with pytest.raises(ValueError,match='repair reserve'):
        book.reserve('over-allocation','A',['fixture'],{},1800,0,approval='fixture',workspace_cap_cents=1100)
    assert json.loads(book.path.read_text())['runs']==[]


def test_billing_boundary_refuses_before_reservation_or_cloud(tmp_path,monkeypatch):
    import time,sys
    from tests.test_gear3_controller import account
    from runners.stage10 import gear3_bundle
    p=tmp_path/'account.json';v=account(p);v['cycle_end_at']=time.time()+80;p.write_text(json.dumps(v))
    monkeypatch.setattr(controller,'provider_client',lambda account:(object(),{'workspace':'fixture-only','workspace_id':'wk-fixture'}))
    monkeypatch.setitem(sys.modules,'modal',SimpleNamespace())
    monkeypatch.setattr(controller,'authoritative_ledger',lambda _:tmp_path/'results/ledger.json')
    monkeypatch.setattr(gear3_bundle,'validate_input',lambda *a:({'mode':'cache'},{'archive_sha256':'a'*64}))
    args=SimpleNamespace(account=p,bundle=tmp_path/'input.zip',seconds=60,startup_seconds=30)
    with pytest.raises(ValueError,match='billing-cycle'):controller.dispatch(tmp_path,args)
    assert not (tmp_path/'results/ledger.json').exists()


def test_terminal_export_recovery_preserves_raw_without_inference(tmp_path,monkeypatch):
    from runners.stage10 import gear3_worker as worker, gear3_io as storage
    root=tmp_path;out=root/'attempts/fixture';out.mkdir(parents=True)
    terminal={'status':'COMPLETE','archive_path':'exports/fixture.zip'}
    (out/'TERMINAL.json').write_text(json.dumps(terminal));(out/'RAW.json').write_text('{"retained":"original"}')
    commits=[];volume=SimpleNamespace(commit=lambda:commits.append(1))
    monkeypatch.setattr(worker.ollama,'api',lambda *a,**k:pytest.fail('export invoked inference'))
    assert worker.finish_export(volume,root,out,terminal)==terminal
    blob=(root/terminal['archive_path']).read_bytes()
    assert worker.finish_export(volume,root,out,terminal)==terminal
    assert (root/terminal['archive_path']).read_bytes()==blob and len(commits)==2
    (out/'RAW.json').write_text('changed')
    with pytest.raises(ValueError,match='differs'):worker.finish_export(volume,root,out,terminal)


def test_controller_replays_complete_return_before_acceptance(tmp_path,monkeypatch):
    import zipfile
    from runners.stage10 import gear3_io as storage
    m=manifest();transport(monkeypatch);out=tmp_path/'restored/blocks'/m['block_id']
    batch.run_block(m,out)
    archive=tmp_path/'input.zip'
    with zipfile.ZipFile(archive,'w') as z:z.writestr('blocks/one.json',json.dumps(m))
    job={'mode':'science','blocks':['blocks/one.json']}
    controller.verify_completed_blocks(job,archive,tmp_path/'restored',None)
    p=next(out.rglob('UNIT.json')); original=p.read_bytes();p.write_text('{}')
    with pytest.raises(ValueError):controller.verify_completed_blocks(job,archive,tmp_path/'restored',None)
    assert p.read_text()=='{}'
