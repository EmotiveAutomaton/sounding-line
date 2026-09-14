"""Finite Modal campaign adapter. Paid dispatch is exposed only by gear3.py.

DESIGN CHECK: LESSONS3-5 and Round 1 cost contract. Reserve before any cloud
object, retain unknown charges and original expiry, cancel even during startup.
No ordinary retries, concurrent container, evaluator upload or budget reset.
The provider backstop is required separately from this estimated-cost ledger.
"""
from contextlib import contextmanager
import hashlib
import json
import math
from pathlib import Path
import threading
import time
from .gear3_campaign import CampaignLedger,authoritative_ledger,atomic_json
from .stage10.gear3_io import verify_archive
from .stage10.contracts import digest

IMAGE='ollama/ollama@sha256:9d30908e41144b1f1da89b9d8e33c07e4aeb43ff41a8660241b1686e2cc330ad'
AUTHORITY='2026-09-13 curator commission: set up and run prescribed Gear 3 Round 1 carefully under its supplied $50 specification; provenance G3R1.5'


def account_backstop(path,*,now=None):
    value=json.loads(path.read_text(encoding='utf8'));now=time.time() if now is None else now
    required={'workspace','observed_at','source','usage_limit_cents','metered_at_check_cents',
              'net_spend_limit_cents','remaining_credits_cents','other_workloads','status','cycle_start_at','cycle_end_at','payment_method_present','storage_allowance_cents','environment'}
    if not required <= set(value) <= required | {'attribution'} or value['status']!='VERIFIED' or value['source'] not in {'owner-billing-page','provider-api'}:
        raise ValueError('verified workspace billing backstop required before paid dispatch')
    if not isinstance(value['workspace'],str) or not value['workspace'].strip() or not 0<=now-value['observed_at']<=86400:
        raise ValueError('workspace budget evidence is absent or stale')
    if not value['cycle_start_at'] <= value['observed_at'] <= now < value['cycle_end_at']:
        raise ValueError('billing evidence must belong to the current unexpired cycle')
    fields=required & {'usage_limit_cents','metered_at_check_cents','net_spend_limit_cents','remaining_credits_cents'}
    if any(type(value[k])is not int or value[k]<0 for k in fields):raise ValueError('billing values must be nonnegative integer cents')
    if not 0<value['usage_limit_cents']-value['metered_at_check_cents']<=5000 or value['net_spend_limit_cents']>5000:
        raise ValueError('provider usage/net-spend backstop exceeds this campaign ceiling')
    if value['payment_method_present'] is not True or not isinstance(value['environment'],str) or not value['environment'].strip():
        raise ValueError('payment method and explicit environment required')
    if value['other_workloads'] not in {'none','retained-storage-only'}:
        raise ValueError('shared-workspace budget interactions require a resolved allocation')
    allowance=value['storage_allowance_cents']
    if type(allowance) is not int or allowance<0 or (value['other_workloads']=='retained-storage-only' and allowance<100):
        raise ValueError('retained storage requires an explicit conservative allowance')
    if account_campaign_cap(value)<=1000:raise ValueError('insufficient headroom with repair reserve retained')
    return value


def account_campaign_cap(account):
    return min(5000,account['usage_limit_cents']-account['metered_at_check_cents']-account['storage_allowance_cents'])

def account_reservation_guard(account, data, node, cost):
    from .gear3_campaign import CAMPAIGN
    totals=CampaignLedger.totals(data); cap=account_campaign_cap(account)
    overlap=0
    attribution=account.get('attribution')
    if attribution is not None:
        required={'baseline_sha256','snapshot_sha256','cycle_start_at','cycle_end_at','settlements'}
        snapshot=digest({k:v for k,v in account.items() if k!='attribution'})
        if (set(attribution)!=required or attribution['snapshot_sha256']!=snapshot
                or any(attribution[k]!=account[k] for k in ('cycle_start_at','cycle_end_at'))
                or len(attribution['baseline_sha256'])!=64):
            raise ValueError('billing attribution snapshot/cycle differs')
        indexed={r['invocation_id']:r for r in data['runs'] if r.get('campaign_id')==CAMPAIGN}
        for invocation,sha in attribution['settlements'].items():
            row=indexed.get(invocation,{})
            settlements=row.get('settlements',[])
            if len(settlements)!=1 or digest(settlements[0])!=sha:
                raise ValueError('billing overlap lacks original provider settlement')
            receipt=settlements[0]
            if (receipt['baseline_sha256']!=attribution['baseline_sha256']
                    or receipt['cycle_start_at']!=account['cycle_start_at']
                    or receipt['cycle_end_at']!=account['cycle_end_at']
                    or receipt['observed_at']>account['observed_at']):
                raise ValueError('billing attribution crosses evidence/cycle')
            overlap+=row['provider_charge_cents']
        if overlap>account['metered_at_check_cents']:
            raise ValueError('billing attribution exceeds provider meter')
    # Campaign totals still count every settled expense and unresolved reservation.
    # Only provider-attributed charges already in THIS workspace snapshot overlap.
    additional=sum(totals.values())-overlap+cost
    if additional>cap:
        raise ValueError('workspace allocation exceeded before reservation')
    if node!='Reserve' and additional+max(0,1000-totals['Reserve'])>cap:
        raise ValueError('workspace allocation must retain the repair reserve')


def verify_completed_blocks(job, bundle, restored, ghost_root):
    if job['mode']!='science': return
    import zipfile
    from unittest.mock import patch
    from .stage10 import gear3_batch, ollama
    def forbidden(*a,**k): raise ValueError('returned evidence requires an absent model call')
    with zipfile.ZipFile(bundle) as archive, patch.object(ollama,'api',forbidden):
        for name in job['blocks']:
            block=json.loads(archive.read(name)); folder=restored/'blocks'/block['block_id']
            if not (folder/'COMPLETE.json').is_file(): raise ValueError('completed block missing from returned archive')
            gear3_batch.run_block(block,folder,ghost_root=ghost_root)


def workspace_info(client):
    """Read token workspace metadata without exposing token/user credentials."""
    from modal._utils.async_utils import synchronizer
    from modal_proto import api_pb2
    @synchronizer.create_blocking
    async def inspect(bound_client):
        info = await bound_client.stub.TokenInfoGet(api_pb2.TokenInfoGetRequest(), timeout=15, retry=None)
        return {'workspace': info.workspace_name, 'workspace_id': info.workspace_id}
    return inspect(client)


def provider_client(account):
    import modal
    client = modal.Client.from_env()
    actual = workspace_info(client)
    if actual.get('workspace') != account['workspace'] or not actual.get('workspace_id'):
        raise ValueError('authenticated workspace differs from the inspected billing backstop')
    return client, actual


def stop_app_rpc(client, app_id):
    from modal._utils.async_utils import synchronizer
    from modal_proto import api_pb2
    @synchronizer.create_blocking
    async def stop(bound_client):
        await bound_client.stub.AppStop(api_pb2.AppStopRequest(app_id=app_id, source=api_pb2.APP_STOP_SOURCE_CLI), timeout=15, retry=None)
    stop(client)
    return {'app_id': app_id, 'status': 'stop requested; final ownership still requires verification'}


def request_stop(cancel_call, stop_app, *, timeout_seconds=16):
    """Bound both independent requests; neither is proof of owner termination.

    AppStop starts first. A stuck SDK cancellation cannot postpone it, and a
    stuck AppStop cannot prevent the separate call cancellation attempt.
    Daemon threads may finish late; they never dispatch work or release money.
    """
    evidence = {}
    def bounded(action):
        finished = threading.Event(); outcome = {}
        def run():
            try: outcome['value'] = action()
            except Exception as exc: outcome['error'] = repr(exc)
            finally: finished.set()
        threading.Thread(target=run, daemon=True).start()
        if not finished.wait(timeout_seconds): return {'error': 'request deadline exceeded'}
        return dict(outcome)
    app = bounded(stop_app)
    evidence['app_error' if 'error' in app else 'app_stop'] = app.get('error', app.get('value'))
    if cancel_call is not None:
        call = bounded(cancel_call)
        evidence['call_error' if 'error' in call else 'call_cancel_requested'] = call.get('error', True)
    if 'app_error' in evidence:
        raise RuntimeError('provider termination unresolved: '+json.dumps(evidence))
    return evidence


@contextmanager
def deadline_guard(expires,cancel,record):
    """Native timing only; no model/agent wake is scheduled by this controller."""
    done=threading.Event()
    def monitor():
        if not done.wait(max(0,expires-time.time())):
            try:record({'status':'DEADLINE_STOP_REQUESTED','at':time.time(),'evidence':cancel()})
            except Exception as exc:record({'status':'DEADLINE_CANCEL_UNKNOWN','at':time.time(),'error':repr(exc)})
    worker=threading.Thread(target=monitor,daemon=True);worker.start()
    try:yield
    finally:done.set();worker.join(timeout=20)


def dispatch(repo,args):
    account=account_backstop(args.account)
    from .gear3_runtime import validate_runtime
    runtime = validate_runtime()  # no cloud objects, before any reservation
    client, authenticated = provider_client(account)
    import modal  # import and local API inspection incur no cloud allocation
    from .stage10.gear3_bundle import validate_input
    main=authoritative_ledger(repo).parents[1]
    bundle=args.bundle.resolve();job,checked=validate_input(bundle,repo,main/'results/phase_2_4_stage_10/raw/interface-v3/ghost-public')
    supplement = None
    if getattr(args, 'context_supplement', False):
        from .gear3_supplement import verify_payload
        supplement = verify_payload(repo, bundle, job)
    import zipfile
    if job['mode'] not in {'cache','science'}:raise ValueError('unknown campaign job')
    if args.seconds is None or args.startup_seconds is None or not 1<=args.startup_seconds<=args.seconds:
        raise ValueError('explicit startup and total bounds required')
    if time.time()+args.seconds+60 >= account['cycle_end_at']:
        raise ValueError('job would cross the verified billing-cycle backstop')
    if job['mode']=='science' and args.node!='Reserve':
        with zipfile.ZipFile(bundle) as z:
            if any(json.loads(z.read(name))['node']!=args.node for name in job['blocks']):raise ValueError('branch differs from reserved job')
    if args.node!='P' and args.node!='Reserve':
        # Scientific sizing and literal admission are a single recorded checkpoint.
        if not args.pilot or not args.plan:raise ValueError('science needs passed literal pilot and frozen affordable PLAN')
        from .gear3_plan import validate_plan
        plan=json.loads(args.plan.read_text())
        book=CampaignLedger(authoritative_ledger(repo))
        with book.transaction() as data:
            validate_plan(repo,plan,account,data,main/'results/phase_2_4_stage_10/raw/interface-v3/ghost-public')
        match=[j for j in plan['jobs'] if j['invocation']==args.invocation]
        if len(match)!=1:raise ValueError('invocation absent from approved PLAN')
        planned=match[0]
        if (planned['bundle_sha256']!=checked['archive_sha256'] or planned['node']!=args.node
                or any(planned[k]!=getattr(args,k) for k in ('seconds','startup_seconds','overhead_cents'))):
            raise ValueError('dispatch differs from whole affordable PLAN')
    ledger=CampaignLedger(authoritative_ledger(repo))
    local=repo/'private/gear3/G3-S10-READER-1/invocations'/args.invocation
    if local.exists():raise ValueError('existing invocation requires inspection, not a second dispatch')
    from .gear3_campaign import capped_cost_cents
    existing=json.loads(ledger.path.read_text()) if ledger.path.exists() else {'runs':[]}
    account_reservation_guard(account,existing,args.node,capped_cost_cents(args.seconds,args.overhead_cents,cache=job['mode']=='cache'))
    ledger.enroll(AUTHORITY,repo/'docs/archive/study-specs/GEAR_3_ROUND_1_2026-09-13.md')
    reservation=ledger.reserve(args.invocation,args.node,['runners/gear3.py','round1',checked['archive_sha256']],
        {'job_sha256':digest(job),'image':IMAGE,'account_evidence_sha256':digest(account),'authenticated_workspace_sha256':digest(authenticated),'startup_seconds':args.startup_seconds},
        args.seconds,args.overhead_cents,approval=args.approval,recovery_of=args.recovery_of,cache=job['mode']=='cache',
        reservation_guard=lambda data,node,cost: account_reservation_guard(account,data,node,cost),
        supplement_authorization=supplement)
    if reservation.get('existing_reservation'):raise ValueError('existing invocation is inspection-only; never resubmit it')
    app=None;call=None;app_id=None;ledger_terminal=False
    def cancel():
        def stop_app():
            identity=(app.app_id if app is not None else None) or app_id
            if not identity:
                raise RuntimeError('provider app identity unresolved; reservation retained')
            return stop_app_rpc(client, identity)
        return request_stop((lambda: call.cancel(terminate_containers=True)) if call is not None else None, stop_app)
    terminal=None
    try:
        local.mkdir(parents=True,exist_ok=False);atomic_json(local/'RESERVATION.json',reservation)
        atomic_json(local/'AUTHENTICATED_WORKSPACE.json',authenticated)
        atomic_json(local/'CONTROLLER_RUNTIME.json',runtime)
        app=modal.App('sounding-line-g3-round1')
        with deadline_guard(reservation['expires_at'],cancel,lambda r:atomic_json(local/'DEADLINE.json',r)):
            volume=modal.Volume.from_name('sounding-line-g3-round1',create_if_missing=True,client=client,environment_name=account['environment'])
            image=(modal.Image.from_registry(IMAGE,add_python='3.13').entrypoint([])
                   .pip_install('numpy==2.4.6'))
            resources=reservation['resources']
            def remote(reservation,bundle_path,mode):
                # Bootstrap uses only stdlib; validate all members before importing
                # the explicitly bundled, hash-pinned execution sources.
                import hashlib,json,os,sys,zipfile
                from pathlib import Path,PurePosixPath
                volume.reload();archive=Path('/campaign')/bundle_path
                if hashlib.sha256(archive.read_bytes()).hexdigest()!=reservation['command'][-1]:raise ValueError('input archive changed')
                with zipfile.ZipFile(archive) as z:
                    manifest=json.loads(z.read('__gear3_archive_manifest__.json'))['files']
                    if set(z.namelist())!=set(manifest)|{'__gear3_archive_manifest__.json'}:raise ValueError('input member inventory differs')
                    for name,entry in manifest.items():
                        parts=PurePosixPath(name)
                        if parts.is_absolute() or '..' in parts.parts or '\\' in name or ':' in name:raise ValueError('unsafe input member')
                        raw=z.read(name)
                        if len(raw)!=entry['bytes'] or hashlib.sha256(raw).hexdigest()!=entry['sha256']:raise ValueError('input member changed')
                        p=Path('/repo')/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
                os.chdir('/repo');sys.path.insert(0,'/repo')
                from runners.stage10.gear3_worker import run
                return run(volume,reservation,bundle_path,mode)
            function=app.function(image=image,gpu=resources['gpu'],cpu=(2,2),
                memory=(resources['memory_request_mib'],resources['memory_limit_mib']),
                max_containers=1,min_containers=0,buffer_containers=0,scaledown_window=2,
                retries=0,timeout=args.seconds,startup_timeout=args.startup_seconds,
                volumes={'/campaign':volume},serialized=True,include_source=False)(modal.concurrent(max_inputs=1)(remote))
            with app.run(detach=False,client=client,environment_name=account['environment']):
                app_id=app.app_id
                atomic_json(local/'APP.json',{'app_id':app.app_id,'expires_at':reservation['expires_at']})
                if time.time()>=reservation['expires_at']-30:raise TimeoutError('reservation exhausted during app setup')
                remote_path='inputs/'+args.invocation+'.zip'
                with volume.batch_upload() as upload:upload.put_file(bundle,'/'+remote_path)
                if time.time()>=reservation['expires_at']-30:raise TimeoutError('reservation exhausted during upload')
                call=function.spawn(reservation,remote_path,job['mode'])
                ledger.transition(args.invocation,'SUBMITTED',call_id=call.object_id)
                atomic_json(local/'CALL.json',{'app_id':app.app_id,'call_id':call.object_id,'expires_at':reservation['expires_at']})
                terminal=call.get(timeout=max(1,reservation['expires_at']-time.time()))
                atomic_json(local/'REMOTE_TERMINAL.json',terminal)
                if (terminal['reservation_sha256']!=digest(reservation) or terminal.get('source_archive_sha256')!=checked['archive_sha256']
                        or terminal.get('owner_ended') is not True or terminal.get('mode')!=job['mode']
                        or terminal.get('status') not in {'COMPLETE','FAILED'}):
                    raise ValueError('remote reservation/input/owner binding differs')
                archive=local/'OUTPUT.zip'
                with archive.open('xb') as stream:
                    for chunk in volume.read_file(terminal['archive_path']):stream.write(chunk)
                receipt=verify_archive(archive,local/'restored')
                if json.loads((local/'restored/TERMINAL.json').read_text())!=terminal:raise ValueError('returned terminal differs from full archive')
                if terminal['status']=='COMPLETE':
                    verify_completed_blocks(job,bundle,local/'restored',main/'results/phase_2_4_stage_10/raw/interface-v3/ghost-public')
                atomic_json(local/'RETRIEVAL.json',receipt)
            ledger.transition(args.invocation,terminal['status'],owner_ended=True,
                evidence={'app_id':app_id,'call_id':call.object_id,'full_archive_sha256':receipt['archive_sha256']})
            ledger_terminal=True
            atomic_json(local/('COMPLETE.json' if terminal['status']=='COMPLETE' else 'FAILED.json'),{'status':terminal['status'],'retrieval':receipt,'accounting':'complete reservation retained pending provider charge reconciliation'})
            return terminal
    except Exception as exc:
        if ledger_terminal:
            # The remote owner and full archive are already verified. A local
            # receipt write failure cannot erase that evidence or rerun the job.
            atomic_json(local/'LANDING_FAILED.json',{'status':'LOCAL_RECEIPT_FAILED',
                'remote_status':terminal['status'],'error':repr(exc),'ledger_terminal_preserved':True})
            raise
        cancellation=None
        try:cancellation=cancel()
        except Exception as cancel_error:cancellation={'unknown':repr(cancel_error)}
        ledger.transition(args.invocation,'UNKNOWN',evidence={'error':repr(exc),'cancellation':cancellation})
        atomic_json(local/'FAILED.json',{'status':'UNKNOWN','error':repr(exc),'cancellation':cancellation,'charges':'entire reservation retained; no automatic retry'})
        raise
