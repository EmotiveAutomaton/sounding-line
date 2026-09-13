"""Simulated provider lifecycle plus real allowlisted source-bundle checks."""
from contextlib import contextmanager
from dataclasses import asdict
import io,json,os,sys,time
from pathlib import Path
from types import SimpleNamespace
import pytest
from runners import gear3_round1 as controller,gear3_campaign as cost
from runners.stage10 import gear3_bundle as bundles,gear3_io as storage,gear3_inputs as inputs,gear3_batch as batch,ollama
from runners.stage10.contracts import digest


def account(path):
    value={'workspace':'fixture-only','environment':'main','payment_method_present':True,'storage_allowance_cents':0,'observed_at':time.time(),'source':'owner-billing-page','usage_limit_cents':5000,
        'metered_at_check_cents':0,'net_spend_limit_cents':5000,'remaining_credits_cents':0,'other_workloads':'none','status':'VERIFIED','cycle_start_at':time.time()-3600,'cycle_end_at':time.time()+86400}
    path.write_text(json.dumps(value));return value


def test_account_backstop_and_early_deadline(tmp_path):
    p=tmp_path/'billing.json';value=account(p);assert controller.account_backstop(p)==value
    for key,changed in [('usage_limit_cents',5001),('status','UNVERIFIED'),('other_workloads','unknown'),('observed_at',0)]:
        altered={**value,key:changed};p.write_text(json.dumps(altered))
        with pytest.raises(ValueError):controller.account_backstop(p)
    records=[];cancelled=[]
    with controller.deadline_guard(time.time()+.03,lambda:cancelled.append('startup') or 'stopped',records.append):
        time.sleep(.08)
    assert cancelled==['startup'] and records[0]['status']=='DEADLINE_STOP_REQUESTED'
    records.clear()
    with controller.deadline_guard(time.time()+60,lambda:pytest.fail('early cancellation'),records.append):pass
    assert not records


def test_cpu_cache_price_and_expired_recovery(tmp_path):
    l=cost.CampaignLedger(tmp_path/'ledger.json');l.enroll(controller.AUTHORITY,Path('docs/archive/study-specs/GEAR_3_ROUND_1_2026-09-13.md'))
    r=l.reserve('cache','P',['cache'],{},600,25,approval='fixture',cache=True,now=100)
    assert r['resources']['gpu'] is None and r['reserved_cents']==28
    l.transition('cache','SUBMITTED',call_id='fixture');l.transition('cache','FAILED',owner_ended=True,evidence='fixture')
    with pytest.raises(ValueError,match='expired'):l.reserve('retry','Reserve',['cache'],{},60,0,approval='fixture',recovery_of='cache',now=701)


def test_allowlisted_real_bundle_and_source_census(tmp_path):
    if not os.environ.get('G3_GHOST_ROOT'):pytest.skip('requires reviewed local source bank before cloud admission')
    root=Path.cwd();main=Path(os.environ['G3_GHOST_ROOT']).parents[4]
    # Explicit source bank; no hidden evaluator values enter returned metadata.
    c=inputs.census(main,tmp_path/'census');assert c['counts']['human_opportunities']==96
    r=inputs.roster(c);assert len(r['A'])==76 and len(r['B'])==48
    source=bundles.source_closure(root)
    profiles={k:asdict(ollama.ReaderProfile('qwen3.5:'+k,batch.PINS[k],'0.32.14')) for k in batch.PINS}
    m=inputs.make_block('A',1,r['A'][:2],{},profiles,source)
    dest=tmp_path/'bundle';ghost_root=Path(os.environ['G3_GHOST_ROOT'])
    bundles.build(root,[m],ghost_root,dest,mode='science',profiles=profiles,server_version='0.32.14')
    job,receipt=bundles.validate_input(dest/'INPUT.zip',root,ghost_root)
    assert len(job['blocks'])==1 and not any('evaluator' in k or 'CENSUS' in k for k in receipt['files'])
    # A well-checksummed extra file is still an illegal cloud payload.
    (dest/'contents'/'unrelated-secret.txt').write_text('constructed poison')
    storage.make_archive(dest/'contents',tmp_path/'poison.zip')
    with pytest.raises(ValueError,match='extra'):bundles.validate_input(tmp_path/'poison.zip',root,ghost_root)


def test_complete_prepared_pilot_offline(monkeypatch,tmp_path):
    if not os.environ.get('G3_GHOST_ROOT'):pytest.skip('requires reviewed source bank before pilot')
    from runners.stage10.gear3_prepare import prepare
    from tests.test_gear3_round1 import transport
    native=Path(os.environ['G3_GHOST_ROOT']);main=native.parents[4]
    prepared=tmp_path/'prepared';receipt=prepare(main,prepared)
    assert receipt['pilot_units']==44
    blocks=prepared/'pilot/contents';job=json.loads((blocks/'JOB.json').read_text())
    requests=transport(monkeypatch);results=[]
    reservation={'invocation_id':'whole-pilot-fixture','reserved_cents':200,'expires_at':time.time()+600}
    out=tmp_path/'raw'
    with storage.durable_attempts(out,reservation,lambda:None):
        for name in job['blocks']:
            m=json.loads((blocks/name).read_text());results.append((m,batch.run_block(m,out/m['block_id'],ghost_root=native)))
    assert len(requests)==72
    archive=tmp_path/'full.zip';storage.make_archive(out,archive);restored=tmp_path/'restored';storage.verify_archive(archive,restored)
    def forbidden(*a,**k):raise AssertionError('completed pilot repeated inference')
    monkeypatch.setattr(ollama.urllib.request,'urlopen',forbidden)
    for m,expected in results:assert batch.run_block(m,restored/m['block_id'],ghost_root=native)==expected
    controls=json.loads((prepared/'CHEAP_CONTROLS.json').read_text())
    original=json.loads((main/'results/phase_2_4_stage_10/raw/human-baselines-v1/RESULT.json').read_text())
    assert controls['fitted']['models']==original['fitted']['models']


@pytest.mark.parametrize('failure',[False,True,'receipt'])
def test_controller_reserves_then_preserves_complete_or_unknown(tmp_path,monkeypatch,failure):
    from runners.stage10 import gear3_bundle
    # Source/bundle boundaries have a separate real integration check above.
    checked={'archive_sha256':'a'*64,'files':{}}
    job={'mode':'cache','profiles':{},'server_version':'0.32.14','blocks':[]}
    monkeypatch.setattr(gear3_bundle,'validate_input',lambda *a:(job,checked))
    repo=tmp_path/'repo';spec=repo/'docs/archive/study-specs/GEAR_3_ROUND_1_2026-09-13.md';spec.parent.mkdir(parents=True)
    spec.write_bytes(Path('docs/archive/study-specs/GEAR_3_ROUND_1_2026-09-13.md').read_bytes())
    ledger=repo/'results/gear3_ledger.json';monkeypatch.setattr(controller,'authoritative_ledger',lambda _:ledger)
    args=SimpleNamespace(account=tmp_path/'account.json',bundle=tmp_path/'INPUT.zip',seconds=60,startup_seconds=30,
        invocation='fixture',node='P',overhead_cents=5,approval='constructed',recovery_of=None,pilot=None,plan=None)
    account(args.account);args.bundle.write_bytes(b'fixture')
    if failure=='receipt':
        original_write=controller.atomic_json
        def faulty_write(path,value):
            if path.name=='COMPLETE.json':raise OSError('constructed local receipt failure')
            return original_write(path,value)
        monkeypatch.setattr(controller,'atomic_json',faulty_write)
    events=[];saved={};volume=SimpleNamespace();bound_client=object()
    monkeypatch.setattr(controller,'provider_client',lambda account:(bound_client,{'workspace':'fixture-only','workspace_id':'wk-fixture'}))
    monkeypatch.setattr(controller,'stop_app_rpc',lambda client,app_id:events.append('cancel-app') or {'app_id':app_id})
    @contextmanager
    def upload():yield SimpleNamespace(put_file=lambda *a:events.append('upload'))
    volume.batch_upload=upload
    volume.read_file=lambda p:iter([saved['archive']])
    class Image:
        def entrypoint(self,*a):return self
        def pip_install(self,*a):return self
    class App:
        app_id='ap-fixture'
        def __init__(self,*a):
            assert json.loads(ledger.read_text())['runs'][-1]['status']=='RESERVED';events.append('app')
        def function(self,**options):
            assert options['gpu'] is None and options['cpu']==(2,2) and options['retries']==0 and options['max_containers']==1
            assert options['startup_timeout']==30 and options['timeout']==60 and options['include_source'] is False
            return lambda f:SimpleNamespace(spawn=spawn)
        @contextmanager
        def run(self,**kwargs):assert kwargs['detach'] is False and kwargs['client'] is bound_client;yield self
    class Call:
        object_id='fc-fixture'
        def get(self,timeout):
            assert json.loads(ledger.read_text())['runs'][-1]['status']=='SUBMITTED'
            if failure is True:raise TimeoutError('constructed provider disappearance')
            return saved['terminal']
        def cancel(self,**kwargs):events.append('cancel-call')
    def spawn(reservation,path,mode):
        events.append('spawn');terminal={'status':'COMPLETE','reservation_sha256':digest(reservation),'mode':'cache','archive_path':'exports/fixture.zip','owner_ended':True,'source_archive_sha256':checked['archive_sha256']}
        folder=tmp_path/'remote';folder.mkdir();(folder/'TERMINAL.json').write_text(json.dumps(terminal))
        storage.make_archive(folder,tmp_path/'output.zip');saved.update(terminal=terminal,archive=(tmp_path/'output.zip').read_bytes())
        return Call()
    fake=SimpleNamespace(App=App,Volume=SimpleNamespace(from_name=lambda *a,**k:volume),
        Image=SimpleNamespace(from_registry=lambda *a,**k:Image()),concurrent=lambda **k:lambda f:f)
    monkeypatch.setitem(sys.modules,'modal',fake)
    class Client:
        @staticmethod
        async def from_env():
            async def stop(*a,**k):events.append('cancel-app')
            return SimpleNamespace(stub=SimpleNamespace(AppStop=stop))
    monkeypatch.setitem(sys.modules,'modal.client',SimpleNamespace(_Client=Client))
    if failure=='receipt':
        with pytest.raises(OSError,match='local receipt'):controller.dispatch(repo,args)
        assert json.loads((repo/'private/gear3/G3-S10-READER-1/invocations/fixture/LANDING_FAILED.json').read_text())['ledger_terminal_preserved']
    elif failure:
        with pytest.raises(TimeoutError):controller.dispatch(repo,args)
    else:assert controller.dispatch(repo,args)['status']=='COMPLETE'
    row=json.loads(ledger.read_text())['runs'][0]
    assert 'wk-fixture' not in ledger.read_text() and 'fixture-only' not in ledger.read_text()
    assert row['profile']['authenticated_workspace_sha256']==digest({'workspace':'fixture-only','workspace_id':'wk-fixture'})
    assert row['status']==('UNKNOWN' if failure is True else 'COMPLETE')
    assert row['booked_cents']==row['reserved_cents'] and row['provider_charge_cents'] is None
    assert events[:3]==['app','upload','spawn']
    if failure is True:assert 'cancel-call' in events and 'cancel-app' in events
    with pytest.raises(ValueError):controller.dispatch(repo,args)
    assert len(json.loads(ledger.read_text())['runs'])==1
