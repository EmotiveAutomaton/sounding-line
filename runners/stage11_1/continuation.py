"""Reviewed finite queue; no generated research, silent retry or stale lock reclaim.

DESIGN CHECK: LESSONS 3-5. NULL: changed plans, incomplete attempts, reused PID,
missing produce or failed admission cannot advance a dependent method. ALTERNATIVE:
the existing owner finishes before the queue takes its producer lock; complete
tasks replay, independent methods proceed, and resource/selection stops notify.
The whole scheduler is exercised on a scratch root before real launch.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime,timezone
import hashlib
import os
from pathlib import Path
import time
import traceback
from .common import PRIVATE,read,freeze,digest,canonical
from . import run_v3b as legacy
from . import branch_runtime as branch
from . import report_v3b as report
from runners.stage9.process_identity import native_identity
from tools.codex_common import atomic_json


@contextmanager
def producer_lock(root):
    import msvcrt
    with (root/'producer.lock').open('a+b') as lock:
        lock.seek(0);lock.write(b'1');lock.flush();lock.seek(0)
        msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        try: yield
        finally: lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)


def checked_plan(root,item):
    path=root/item['path'];plan=read(path)
    if digest(plan)!=item['digest']:raise ValueError('frozen queue plan changed')
    return path,plan


def admitted(root,gate,fake):
    if not (root/gate).exists(): return False
    receipt=read(root/gate)
    if receipt['status'] not in ('PASS','COMPLETE') or receipt.get('fake',False)!=fake:return False
    if gate.startswith('DIRECT_'):
        carried=read(root/'GATES-v3b.json').get('pilot_carryforward',{}) if not fake else {}
        if carried and digest(receipt)!=carried['digest']:raise ValueError('direct pilot carryforward changed')
    elif 'v3' in gate:
        if receipt['sources']!=legacy.source_pin():raise ValueError('legacy pilot source identity changed')
    elif receipt['sources']!=branch.sources():raise ValueError('branch pilot source identity changed')
    return True


def forecast_seconds(root,calls):
    costs=[]
    for path in (root/'calls').rglob('ATTEMPT.json'):
        costs.append(read(path)['cost']['wall_seconds'])
    upper=max(costs,default=27.737965)*1.25+5
    return calls*upper


def validate_manifest(manifest):
    ids=[i['id'] for i in manifest['items']]
    if len(ids)!=len(set(ids)):raise ValueError('duplicate queue produce identity')
    for item in manifest['items']:
        if item['runner'] not in ('legacy','branch'):raise ValueError('unreviewed queue runner')
        if Path(item['path']).is_absolute() or '..' in Path(item['path']).parts:raise ValueError('plan outside private root')


def run(root,manifest_path,fake=False):
    manifest=read(manifest_path);validate_manifest(manifest);pin=branch.sources()
    directory=root/'continuation'/manifest.get('id','setup-v1');directory.mkdir(parents=True,exist_ok=True)
    freeze(directory/'QUEUE-BINDING.json',dict(manifest_digest=digest(manifest),sources=pin,fake=fake))
    wait=manifest.get('wait_for')
    if wait and not fake:
        while True:
            if (root/'STOP').exists() or (root/'PAUSE').exists() or (directory/'CANCEL').exists():
                freeze(directory/'STOPPED.json',dict(status='STOPPED',reason='owner interruption before takeover'));return
            current=native_identity(wait['native']['pid'])
            if current is None:break
            if current!=wait['native']:raise ValueError('original PID reused before takeover')
            atomic_json(directory/'STATUS.json',dict(status='WAITING_FOR_NATIVE_OWNER',native=current,at=datetime.now(timezone.utc).isoformat()))
            time.sleep(10)  # Non-LLM waiting; cancellation checked before any action.
        done=read(root/wait['produce'])
        if done['status']!='COMPLETE':raise ValueError('original owner did not complete normally')
        if done['sources']!=legacy.source_pin():raise ValueError('original producer source differs')
    with producer_lock(root):
        owner_path=directory/f'OWNER-{os.getpid()}.json'
        owner=dict(native=native_identity(),manifest_digest=digest(manifest))
        freeze(owner_path,owner)
        for item in manifest['items']:
            if branch.sources()!=pin:raise ValueError('loaded continuation sources changed')
            path,plan=checked_plan(root,item)
            disposition=directory/'dispositions'/f"{item['id']}.json"
            if disposition.exists():
                prior=read(disposition)
                if prior['status'] in ('BLOCKED_METHOD','DEFERRED_RESERVE'):continue
                if prior['status']!='COMPLETE' and prior['status']!='INSTRUMENT_FAILED':raise ValueError('prior resource/failure stop needs explicit continuation')
                if prior['status']=='INSTRUMENT_FAILED':continue
                # Complete results are replayed below; no file-only skip.
            if any(not admitted(root,g,fake) for g in item.get('requires',[])):
                freeze(disposition,dict(status='BLOCKED_METHOD',item=item['id'],reason='required literal method gate failed or absent',next_action='Continue independent admitted methods'))
                continue
            if not disposition.exists() and item.get('reserve_seconds'):
                estimate=forecast_seconds(root,item['calls']);remaining=read(root/'CONTRACT.json')['maximum_gpu_seconds']-legacy.budget(root)['charged_seconds']
                if remaining-estimate<item['reserve_seconds']:
                    freeze(disposition,dict(status='DEFERRED_RESERVE',item=item['id'],remaining_seconds=remaining,estimated_seconds=estimate,reserve_seconds=item['reserve_seconds'],next_action='Preserve later-branch comparisons; operator reallocates after complete cells'))
                    continue
            if (directory/'CANCEL').exists():
                freeze(directory/'STOPPED.json',dict(status='STOPPED',reason='owner cancelled finite queue'));return
            atomic_json(directory/'STATUS.json',dict(status='RUNNING',item=item['id'],at=datetime.now(timezone.utc).isoformat(),gear=2))
            if item['runner']=='legacy':
                try: result=legacy.execute(root,path,fake)
                except ValueError as exc:
                    # Only a completely retained literal pilot can retire its own
                    # method. Transport, partial blocks and integrity faults stop.
                    job=plan['jobs'][0];terminal=root/'jobs'/job['id']/'COMPLETE.json'
                    if str(exc)!='literal pilot grammar failure retained' or len(plan['jobs'])!=1 or not job.get('pilot') or not terminal.exists():raise
                    result=read(terminal)
                    if result['status']!='COMPLETE' or result['calls']!=item['calls'] or not result['invalid']:raise
                    result=dict(result,status='INSTRUMENT_FAILED')
                if result['status']=='COMPLETE' and not any(j.get('pilot') for j in plan['jobs']):
                    for job in plan['jobs']:report.analyze(job['id'],root)
            else:
                result,_=branch.execute(root,path,fake)
                if result['status']=='COMPLETE' and not plan.get('pilot'):branch.analyze(root,path)
            freeze(disposition,dict(status=result['status'],item=item['id'],result_digest=digest(result),next_action=item['next_action']))
            if result['status'] not in ('COMPLETE','INSTRUMENT_FAILED'):
                freeze(directory/'STOPPED.json',dict(status=result['status'],item=item['id'],next_action='Reconcile resource/owner stop; no automatic retry'));return
        freeze(directory/'AWAITING_SELECTION.json',dict(status='AWAITING_SELECTION',
            reason='Prepared S2 and leading S3 contrasts require full completed S1 comparison and explicit operator selection',
            next_action='Land finished blocks, choose viable leading methods, activate frozen S2/S3 plans and account-use diagnostic; retain original clocks',
            budget=legacy.budget(root),fake=fake))


def main():
    p=argparse.ArgumentParser();p.add_argument('manifest',type=Path);p.add_argument('--root',type=Path,default=PRIVATE);p.add_argument('--fake',action='store_true')
    args=p.parse_args();args.root.mkdir(parents=True,exist_ok=True)
    # The coordinator also has a singleton while waiting for the current owner.
    import msvcrt
    with (args.root/'continuation.lock').open('a+b') as lock:
        lock.write(b'1');lock.flush();lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        freeze(args.root/'continuation'/f'COORDINATOR-{os.getpid()}.json',dict(native=native_identity(),manifest=str(args.manifest),fake=args.fake))
        try:run(args.root,args.manifest,args.fake)
        except BaseException:
            freeze(args.root/'continuation'/f'FAILED-{os.getpid()}.json',dict(status='FAILED',at=datetime.now(timezone.utc).isoformat(),error=traceback.format_exc()))
            raise
        else:
            freeze(args.root/'continuation'/f'EXIT-{os.getpid()}.json',dict(status='COMPLETE',
                kind='operational coordinator exit',scientific_verdict=False,
                next_action='Inspect the queue selection/resource disposition; this is not campaign closure'))


if __name__=='__main__':main()
