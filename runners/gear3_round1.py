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
              'net_spend_limit_cents','remaining_credits_cents','other_workloads','status'}
    if set(value)!=required or value['status']!='VERIFIED' or value['source'] not in {'owner-billing-page','provider-api'}:
        raise ValueError('verified workspace billing backstop required before paid dispatch')
    if not value['workspace'] or not 0<=now-value['observed_at']<=86400:
        raise ValueError('workspace budget evidence is absent or stale')
    fields=required & {'usage_limit_cents','metered_at_check_cents','net_spend_limit_cents','remaining_credits_cents'}
    if any(type(value[k])is not int or value[k]<0 for k in fields):raise ValueError('billing values must be nonnegative integer cents')
    if not 0<value['usage_limit_cents']-value['metered_at_check_cents']<=5000 or value['net_spend_limit_cents']>5000:
        raise ValueError('provider usage/net-spend backstop exceeds this campaign ceiling')
    if value['other_workloads']!='none':raise ValueError('shared-workspace budget interactions require a resolved allocation')
    return value


@contextmanager
def deadline_guard(expires,cancel,record):
    """Native timing only; no model/agent wake is scheduled by this controller."""
    done=threading.Event()
    def monitor():
        if not done.wait(max(0,expires-time.time())):
            try:record({'status':'DEADLINE_CANCELLED','at':time.time(),'evidence':cancel()})
            except Exception as exc:record({'status':'DEADLINE_CANCEL_UNKNOWN','at':time.time(),'error':repr(exc)})
    worker=threading.Thread(target=monitor,daemon=True);worker.start()
    try:yield
    finally:done.set();worker.join(timeout=20)


def dispatch(repo,args):
    account=account_backstop(args.account)
    import modal  # import and local API inspection incur no cloud allocation
    from .stage10.gear3_bundle import validate_input
    main=authoritative_ledger(repo).parents[1]
    bundle=args.bundle.resolve();job,checked=validate_input(bundle,repo,main/'results/phase_2_4_stage_10/raw/interface-v3/ghost-public')
    import zipfile
    if job['mode'] not in {'cache','science'}:raise ValueError('unknown campaign job')
    if args.seconds is None or args.startup_seconds is None or not 1<=args.startup_seconds<=args.seconds:
        raise ValueError('explicit startup and total bounds required')
    if job['mode']=='science' and args.node!='Reserve':
        with zipfile.ZipFile(bundle) as z:
            if any(json.loads(z.read(name))['node']!=args.node for name in job['blocks']):raise ValueError('branch differs from reserved job')
    if args.node!='P' and args.node!='Reserve':
        # Scientific sizing and literal admission are a single recorded checkpoint.
        if not args.pilot or not args.plan:raise ValueError('science needs passed literal pilot and frozen affordable PLAN')
        pilot=json.loads(args.pilot.read_text());plan=json.loads(args.plan.read_text())
        if pilot.get('status')!='PASS' or plan.get('pilot_sha256')!=digest(pilot):raise ValueError('pilot or PLAN admission differs')
        if checked['archive_sha256'] not in plan['allowed_bundle_sha256']:raise ValueError('bundle was not frozen before science')
    ledger=CampaignLedger(authoritative_ledger(repo))
    local=repo/'private/gear3/G3-S10-READER-1/invocations'/args.invocation
    if local.exists():raise ValueError('existing invocation requires inspection, not a second dispatch')
    ledger.enroll(AUTHORITY,repo/'docs/archive/study-specs/GEAR_3_ROUND_1_2026-09-13.md')
    reservation=ledger.reserve(args.invocation,args.node,['runners/gear3.py','round1',checked['archive_sha256']],
        {'job_sha256':digest(job),'image':IMAGE,'account_evidence_sha256':digest(account),'startup_seconds':args.startup_seconds},
        args.seconds,args.overhead_cents,approval=args.approval,recovery_of=args.recovery_of,cache=job['mode']=='cache')
    if reservation.get('existing_reservation'):raise ValueError('existing invocation is inspection-only; never resubmit it')
    app=None;call=None;app_id=None;ledger_terminal=False
    def cancel():
        # App ID is set before image construction in the installed SDK. A
        # function call is cancellable while queued/starting as well as running.
        if call is not None:call.cancel(terminate_containers=True)
        identity=(app.app_id if app is not None else None) or app_id
        if identity:
            import asyncio
            from modal.client import _Client
            from modal_proto import api_pb2
            async def stop_app():
                client=await _Client.from_env()
                await client.stub.AppStop(api_pb2.AppStopRequest(app_id=identity,source=api_pb2.APP_STOP_SOURCE_CLI),timeout=15)
            asyncio.run(stop_app())
            return {'app_id':identity,'call_id':call.object_id if call else None}
        raise RuntimeError('provider app identity unresolved; reservation retained')
    terminal=None
    try:
        local.mkdir(parents=True,exist_ok=False);atomic_json(local/'RESERVATION.json',reservation)
        app=modal.App('sounding-line-g3-round1')
        with deadline_guard(reservation['expires_at'],cancel,lambda r:atomic_json(local/'DEADLINE.json',r)):
            volume=modal.Volume.from_name('sounding-line-g3-round1',create_if_missing=True)
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
            with app.run(detach=False):
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
                if terminal['reservation_sha256']!=digest(reservation):raise ValueError('remote reservation binding differs')
                archive=local/'OUTPUT.zip'
                with archive.open('xb') as stream:
                    for chunk in volume.read_file(terminal['archive_path']):stream.write(chunk)
                receipt=verify_archive(archive,local/'restored')
                if json.loads((local/'restored/TERMINAL.json').read_text())!=terminal:raise ValueError('returned terminal differs from full archive')
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
