"""Checkpoint-aware CPU dispatch; original runtime remains immutable.

DESIGN CHECK: LESSONS 3-5 read for this design, 2026-10-17.
NULL/ALTERNATIVE: scientific outcomes cannot alter dispatch or verification.
Infrastructure gates fail closed on changed pins, missing ownership, resource
limits or failed replay. A forecast overshoot yields at a saved boundary; it
never becomes a scientific null. PAUSED, FAILED and COMPLETE are distinct.
"""
from __future__ import annotations

from pathlib import Path
import argparse
import subprocess
import time

from runners.drive.cards.batch_runtime import (
    PYTHON, REPO, atomic, freeze, read, filehash, now, native_identity,
    check_files, check_start, claim_slot, release_slot, child, resource_snapshot,
)


def yield_reason(root, plan, resources=None):
    marker = root / 'output/FIRST_TENTH.json'
    if marker.exists() and not (root / 'FORECAST_YIELD_SATISFIED.json').exists():
        value = read(marker)
        projection = value.get('projected_cpu_seconds', value.get('projected_seconds'))
        if projection is None:
            raise ValueError('First-tenth projection missing')
        if projection > 2 * plan['forecast_cpu_seconds']:
            return 'first_tenth_projection_exceeds_twice_forecast'
    if resources is not None:
        if resources['ram_available_GiB'] < 4 or resources['commit_headroom_GiB'] < 6 or resources['disk_free_GiB'] < 20:
            return 'resource_floor_yield'
    return None


def run(root):
    plan = read(root / 'PLAN.json')
    with (root / 'ATTEMPT.claim').open('x') as stream:
        stream.write(now())
    freeze(root / 'OWNER.json', dict(at=now(), native=native_identity(), plan_sha256=filehash(root/'PLAN.json')))
    lease = worker = None
    try:
        deadline = time.monotonic() + 90
        while not (root/'MONITOR_READY.json').exists():
            if time.monotonic() > deadline:
                raise TimeoutError('Monitor handshake absent')
            time.sleep(.25)
        if read(root/'MONITOR_READY.json')['owner_sha256'] != filehash(root/'OWNER.json'):
            raise ValueError('Monitor owner binding mismatch')
        check_files(plan['pins'])
        resources = check_start(plan)
        lease = claim_slot(REPO/'results/.cpu-slots-20261017', native_identity(), plan['card'])
        freeze(root/'ADMISSION.json', dict(at=now(), resources=resources, lease=str(lease[0]), threads=2))
        deadline = time.monotonic() + plan['max_wall_seconds']
        for operation in ('execute', 'verify'):
            atomic(root/'PROGRESS.json', dict(at=now(), phase=operation))
            with (root/f'{operation}.stdout.log').open('wb') as out, (root/f'{operation}.stderr.log').open('wb') as err:
                worker = subprocess.Popen([str(PYTHON), '-X', 'utf8', '-B', '-m',
                    'runners.drive.cards.batch_runtime_v2', '_'+operation, str(root)],
                    cwd=REPO, stdout=out, stderr=err, creationflags=0x08000000 | 0x4000)
                freeze(root/f'{operation.upper()}_CHILD.json', dict(at=now(), native=native_identity(worker.pid)))
                next_resource = 0
                while worker.poll() is None:
                    if time.monotonic() > deadline:
                        raise TimeoutError('Combined execution/replay exceeded frozen wall bound')
                    if operation == 'execute':
                        snapshot = None
                        if time.monotonic() >= next_resource:
                            snapshot = resource_snapshot()
                            next_resource = time.monotonic() + 30
                            size = sum(p.stat().st_size for p in (root/'output').rglob('*') if p.is_file())
                            if size > plan.get('max_output_bytes', 32*1024**3):
                                raise RuntimeError('Frozen output byte cap exceeded')
                        reason = yield_reason(root, plan, snapshot)
                        if reason:
                            atomic(root/'output/YIELD_REQUEST.json', dict(at=now(), reason=reason))
                    time.sleep(2)
                if worker.returncode:
                    raise RuntimeError(f'{operation} child exited {worker.returncode}; retained stderr')
            if operation == 'execute' and read(root/'RESULT.json').get('status') == 'yielded':
                freeze(root/'PAUSED.json', dict(at=now(), status='PAUSED', card=plan['card'],
                    reason=read(root/'output/YIELD_REQUEST.json'), saved_result_sha256=filehash(root/'RESULT.json'),
                    resume='Owner must dispatch the next two ranked eligible cards before forecast-yield resume; same scientific plan and saved checkpoints.',
                    scientific_admission=False))
                return
        check_files(plan['pins'])
        outputs = {p.relative_to(root).as_posix(): filehash(p) for p in root.rglob('*')
                   if p.is_file() and p.suffix in {'.json','.jsonl','.npz','.npy','.gz','.joblib'}
                   and p.name not in {'PROGRESS.json','MONITOR_READY.json'}}
        freeze(root/'COMPLETE.json', dict(at=now(), status='COMPLETE', card=plan['card'], outputs=outputs,
            descriptive=True, scientific_admission=False, fresh_process_verified=True, write_through_required=True))
    except Exception as exc:
        if worker is not None and worker.poll() is None:
            worker.terminate()
            worker.wait(timeout=30)
        freeze(root/'FAILED.json', dict(at=now(), status='FAILED', card=plan['card'], error=repr(exc),
            engineering_retry_available=True, scientific_admission=False))
        raise
    finally:
        if lease:
            release_slot(*lease)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['run','_execute','_verify'])
    parser.add_argument('root', type=Path)
    args = parser.parse_args()
    if args.operation == 'run':
        run(args.root.resolve())
    else:
        child(args.root.resolve(), args.operation[1:])


if __name__ == '__main__':
    main()
