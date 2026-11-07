"""Week 5 counted leases on the retained Windows-contained execution kernel.

DESIGN CHECK: LESSONS 3-5. Both scientific directions share identical admission.
Eight leases across two namespaces, immutable plans, descendant CPU accounting,
fresh replay and native identity preserve operational evidence. No outcome gates
are relaxed. No stale lease is reclaimed automatically.
"""
import argparse
from pathlib import Path
import os
from . import batch_runtime_v8 as kernel
from . import week5_policy as policy
from .batch_runtime import REPO, atomic, freeze, read, native_identity, now


def claim(root,plan):
    # The original admission mutex serializes both generations' slot claims.
    with kernel.admission_lock(policy.OLD_SLOTS):
        resources=policy.admission(dict(plan,attempt_root=str(root)))
        policy.NEW_SLOTS.mkdir(parents=True,exist_ok=True)
        value=dict(native=native_identity(),card=plan['card'],family=plan['family'],at=now(),
                   runtime='week5',attempt_root=str(root),projected_peak_ram_GiB=plan['projected_peak_ram_GiB'])
        # Prefer the new bank. Original four are borrowed only when idle.
        # No slot numbered 4+ is ever written into the legacy bank.
        for index in (4,5,6,7,0,1,2,3):
            path=(policy.NEW_SLOTS if index>=4 else policy.OLD_SLOTS)/f'slot-{index}.json'
            try:
                with path.open('x',encoding='utf-8',newline='\n') as f:
                    import json
                    json.dump(value,f)
                return (path,value),resources
            except FileExistsError: continue
        raise RuntimeError('No free counted slot')


from datetime import datetime, timezone
import time
from .batch_runtime import PYTHON, filehash, check_files, release_slot, resource_snapshot
from .batch_runtime_v8 import measured_child, job_cpu, output_bytes

def run(root):
    root=Path(root).resolve()
    plan = read(root/'PLAN.json')
    os.environ['CUDA_VISIBLE_DEVICES']=''
    for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        os.environ[key]='2'
    with (root/'ATTEMPT.claim').open('x') as stream:
        stream.write(now())
    freeze(root/'OWNER.json', dict(at=now(), native=native_identity(), plan_sha256=filehash(root/'PLAN.json')))
    lease = worker = None
    charged = 0.0
    started = time.monotonic()
    failure_class = 'engineering'
    try:
        handshake_deadline = time.monotonic()+90
        while not (root/'MONITOR_READY.json').exists():
            if time.monotonic() > handshake_deadline:
                raise TimeoutError('Monitor handshake absent')
            time.sleep(.25)
        if read(root/'MONITOR_READY.json')['owner_sha256'] != filehash(root/'OWNER.json'):
            raise ValueError('Monitor owner binding mismatch')
        check_files(plan['pins'])
        lease, resources = claim(root, plan)
        cap=min(plan['max_cpu_seconds'],resources['remaining_cpu_seconds'])
        atomic(root/'BUDGET_PROGRESS.json',dict(at=now(),cpu_seconds=0.0))
        freeze(root/'ADMISSION.json', dict(**resources, lease=str(lease[0]), threads=2))
        deadline = min(time.monotonic()+plan['max_wall_seconds'],
                       time.monotonic()+(policy.DRAIN-datetime.now(timezone.utc)).total_seconds())
        for operation in ('execute', 'verify'):
            atomic(root/'PROGRESS.json', dict(at=now(), phase=operation, cpu_seconds=charged))
            with measured_child(root, operation, [str(PYTHON), '-X', 'utf8', '-B', '-m',
                    'runners.drive.cards.week5_child', operation, str(root)]) as worker:
                freeze(root/f'{operation.upper()}_CHILD.json', dict(at=now(), native=native_identity(worker.pid)))
                next_check = 0
                sampled_cpu = 0.0
                while worker.poll() is None:
                    sampled_cpu = job_cpu(worker)
                    atomic(root/'BUDGET_PROGRESS.json',dict(at=now(),cpu_seconds=charged+sampled_cpu))
                    room=policy.remaining(plan['family'],exclude=root)
                    if charged+sampled_cpu+30 >= room:
                        failure_class='cost'
                        raise TimeoutError('Combined family or campaign CPU ceiling')
                    if charged+sampled_cpu > cap:
                        failure_class = 'cost'
                        charged += sampled_cpu
                        raise TimeoutError('Combined execution/replay CPU ceiling')
                    if time.monotonic() > deadline:
                        failure_class = 'cost' if datetime.now(timezone.utc) < policy.DRAIN else 'environment'
                        charged += sampled_cpu
                        raise TimeoutError('Combined execution/replay safety wall or drain ceiling')
                    if time.monotonic() >= next_check:
                        snapshot = resource_snapshot()
                        next_check = time.monotonic()+30
                        atomic(root/'PROGRESS.json', dict(at=now(), phase=operation, cpu_seconds=charged+sampled_cpu, resources=snapshot))
                        if output_bytes(root/'output') > plan.get('max_output_bytes', 32*1024**3):
                            failure_class = 'environment'
                            raise RuntimeError('Frozen output byte cap')
                        reason = policy.yield_reason(root, plan, snapshot)
                        if reason:
                            atomic(root/'output/YIELD_REQUEST.json', dict(at=now(), reason=reason))
                    time.sleep(2)
                measured = job_cpu(worker)
                charged += measured
                if worker.poll():
                    raise RuntimeError(f'{operation} child exited {worker.poll()}; retained stderr')
            worker = None
            if operation == 'execute' and read(root/'RESULT.json').get('status') == 'yielded':
                freeze(root/'PAUSED.json', dict(at=now(), status='PAUSED', card=plan['card'],
                    reason=read(root/'output/YIELD_REQUEST.json'), cpu_seconds=charged,
                    scientific_admission=False, checkpoint_validation_required=True))
                return
        check_files(plan['pins'])
        if charged > cap or charged+30 >= policy.remaining(plan['family'],exclude=root):
            failure_class = 'cost'
            raise TimeoutError('Final measured CPU usage exceeded combined allowance')
        outputs = {p.relative_to(root).as_posix(): filehash(p) for p in root.rglob('*')
                   if p.is_file() and p.suffix in {'.json','.jsonl','.npz','.npy','.gz','.joblib'}
                   and p.name not in {'PROGRESS.json','MONITOR_READY.json'}}
        freeze(root/'COMPLETE.json', dict(at=now(), status='COMPLETE', card=plan['card'],
            outputs=outputs, cpu_seconds=charged, wall_seconds=time.monotonic()-started,
            descriptive=True, scientific_admission=False, fresh_process_verified=True,
            write_through_required=True))
    except Exception as exc:
        # The context manager closes the kernel job before this handler, so
        # the venv launcher and every Python descendant have already stopped.
        charged = sum(read(p)['cpu_seconds'] for p in root.glob('*_JOB_USAGE.json'))
        freeze(root/'FAILED.json', dict(at=now(), status='FAILED', card=plan['card'],
            error=repr(exc), failure_class=failure_class, cpu_seconds=charged,
            wall_seconds=time.monotonic()-started, scientific_admission=False))
        raise
    finally:
        if lease:
            release_slot(*lease)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('root',type=Path)
    run(parser.parse_args().root)
