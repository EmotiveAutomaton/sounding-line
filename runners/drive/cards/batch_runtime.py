"""Owner-dispatched, bounded CPU cards for the October 17 campaign.

DESIGN CHECK: 2026-10-17; LESSONS 3-5 read. Null/alternative scientific
states belong to states.py and the card. Infrastructure failure direction is
fail-closed: changed pins, occupied slots, missing monitoring or failed fresh
verification cannot produce COMPLETE. Operational bands are exhaustive.
No automatic research selection, retries, paid calls or publication.
"""
from __future__ import annotations
import argparse
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

for _name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[_name] = '2'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
from runners.stage14.common import REPO, atomic, freeze, read, filehash, now
from runners.stage9.process_identity import native_identity
from runners.next_round.queue import resource_snapshot

PYTHON = REPO / '.venv/Scripts/python.exe'
FREEZE_UTC = '2026-10-21T13:00:00+00:00'


def slot_count(logical=None):
    logical = os.cpu_count() if logical is None else logical
    return 4 if logical >= 12 else 3 if logical >= 8 else 2


def check_files(bindings):
    for name, expected in bindings.items():
        if filehash(Path(name)) != expected:
            raise ValueError(f'Frozen source/input changed: {name}')


def claim_slot(directory, identity, card, slots=None):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    value = dict(native=identity, card=card, at=now())
    for i in range(slot_count() if slots is None else slots):
        path = directory / f'slot-{i}.json'
        try:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                json.dump(value, stream)
            return path, value
        except FileExistsError:
            continue
    raise RuntimeError('All counted CPU slots occupied; no stale ownership is reclaimed automatically')


def release_slot(path, expected):
    if read(path) != expected:
        raise RuntimeError('CPU lease ownership changed')
    path.unlink()


def check_start(plan):
    from datetime import datetime
    if datetime.now().astimezone() >= datetime.fromisoformat(FREEZE_UTC):
        raise RuntimeError('Campaign no-new-start freeze reached')
    if plan['forecast_cpu_seconds'] >= 7200 and not plan.get('pilot_verified'):
        raise RuntimeError('Separate pilot required for this forecast')
    snapshot = resource_snapshot()
    if snapshot['ram_available_GiB'] < 6 or snapshot['commit_headroom_GiB'] < 8 or snapshot['disk_free_GiB'] < 20:
        raise RuntimeError('New CPU start below RAM/commit/disk floor')
    return snapshot


def child(root, operation):
    plan = read(root / 'PLAN.json')
    check_files(plan['pins'])
    module = importlib.import_module(plan['module'])
    if os.name == 'nt':
        import psutil
        process = psutil.Process()
        process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
        if process.nice() != psutil.BELOW_NORMAL_PRIORITY_CLASS:
            raise OSError('Cannot set below-normal priority')
    if operation == 'execute':
        result = module.execute(root / 'output', plan['inputs'], plan['config'])
        freeze(root / 'RESULT.json', result)
    else:
        result = module.verify(root / 'output', plan['inputs'], plan['config'])
        if not result.get('verified'):
            raise ValueError('Fresh-process verification did not pass')
        freeze(root / 'VERIFIED.json', result)
    check_files(plan['pins'])


def run(root):
    plan = read(root / 'PLAN.json')
    with (root / 'ATTEMPT.claim').open('x') as claim:
        claim.write(now())
    freeze(root / 'OWNER.json', dict(at=now(), native=native_identity(), plan_sha256=filehash(root/'PLAN.json')))
    lease = None
    worker = None
    try:
        deadline = time.monotonic() + 90
        while not (root / 'MONITOR_READY.json').exists():
            if time.monotonic() > deadline:
                raise TimeoutError('Monitor handshake absent')
            time.sleep(.25)
        if read(root/'MONITOR_READY.json')['owner_sha256'] != filehash(root/'OWNER.json'):
            raise ValueError('Monitor owner binding mismatch')
        check_files(plan['pins'])
        resources = check_start(plan)
        lease = claim_slot(REPO/'results/.cpu-slots-20261017', native_identity(), plan['card'])
        freeze(root/'ADMISSION.json', dict(at=now(), resources=resources, lease=str(lease[0]), threads=2))
        for operation in ('execute', 'verify'):
            atomic(root/'PROGRESS.json', dict(at=now(), phase=operation))
            with (root/f'{operation}.stdout.log').open('wb') as out, (root/f'{operation}.stderr.log').open('wb') as err:
                worker = subprocess.Popen([str(PYTHON),'-X','utf8','-B','-m','runners.drive.cards.batch_runtime', '_'+operation,str(root)],
                    cwd=REPO, stdout=out, stderr=err, creationflags=0x08000000 | 0x4000)
                freeze(root/f'{operation.upper()}_CHILD.json', dict(at=now(), native=native_identity(worker.pid)))
                try:
                    code = worker.wait(timeout=plan['max_wall_seconds'])
                except subprocess.TimeoutExpired:
                    worker.terminate()
                    worker.wait(timeout=30)
                    raise TimeoutError(f'{operation} exceeded frozen wall bound')
                if code:
                    raise RuntimeError(f'{operation} child exited {code}; retained stderr')
        check_files(plan['pins'])
        outputs = {p.relative_to(root).as_posix(): filehash(p) for p in root.rglob('*')
                   if p.is_file() and p.suffix in {'.json','.npz','.npy','.gz'}
                   and p.name not in {'PROGRESS.json','MONITOR_READY.json'}}
        freeze(root/'COMPLETE.json', dict(at=now(), status='COMPLETE', card=plan['card'], outputs=outputs,
            descriptive=True, scientific_admission=False, fresh_process_verified=True, write_through_required=True))
    except Exception as exc:
        freeze(root/'FAILED.json',dict(at=now(),status='FAILED',card=plan['card'],error=repr(exc),
            engineering_retry_available=True, scientific_admission=False))
        raise
    finally:
        if lease:
            release_slot(*lease)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['run','_execute','_verify'])
    parser.add_argument('root',type=Path)
    args=parser.parse_args()
    if args.operation == 'run':
        run(args.root.resolve())
    else:
        child(args.root.resolve(),args.operation[1:])


if __name__ == '__main__':
    main()
