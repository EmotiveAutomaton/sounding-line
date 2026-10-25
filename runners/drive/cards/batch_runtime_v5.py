"""Week 3 native CPU execution with one combined execution/replay allowance.

DESIGN CHECK: LESSONS 3-5. Null and alternative outcomes share admission and
cost limits. Ownership, pins, replay and containment fail closed. Environmental
or cost stops retain outputs; neither can be relabelled as a scientific null.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import argparse
import os
import subprocess
import time
import psutil
import ctypes
from ctypes import wintypes as W
from runners.drive.native_job import ContainedProcess
from .batch_runtime import (PYTHON, REPO, atomic, freeze, read, filehash, now,
    native_identity, check_files, release_slot, child, resource_snapshot, slot_count)
from .week3_policy import admission, yield_reason, DRAIN


@contextmanager
def admission_lock(directory):
    directory.mkdir(parents=True, exist_ok=True)
    with (directory/'.week3-admission.lock').open('a+b') as stream:
        stream.seek(0)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(stream.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(stream, fcntl.LOCK_EX)
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == 'nt':
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


def claim(root, plan):
    directory = REPO/'results/.cpu-slots-20261017'
    with admission_lock(directory):
        resources = admission(plan)
        # Count every occupied slot, including the top slot when a reservation
        # appears during a full queue. Never reclaim an unverified stale lease.
        occupied = list(directory.glob('slot-*.json'))
        if len(occupied) >= resources['slots']:
            raise RuntimeError('Counted slots occupied or reserved for ToMpathy')
        value = dict(native=native_identity(), card=plan['card'], at=now(), runtime='v5')
        for index in range(slot_count()):
            path = directory/f'slot-{index}.json'
            try:
                with path.open('x', encoding='utf8', newline='\n') as stream:
                    import json
                    json.dump(value, stream)
                return (path, value), resources
            except FileExistsError:
                continue
        raise RuntimeError('No free counted slot')


def child_with_usage(root, operation):
    started = time.monotonic()
    freeze(root/f'{operation.upper()}_NATIVE.json', dict(at=now(), native=native_identity()))
    try:
        child(root, operation)
    finally:
        times = psutil.Process().cpu_times()
        freeze(root/f'{operation.upper()}_USAGE.json', dict(at=now(),
            cpu_seconds=times.user+times.system, wall_seconds=time.monotonic()-started,
            peak_rss_bytes=psutil.Process().memory_info().peak_wset if os.name == 'nt' else psutil.Process().memory_info().rss))


class JobAccounting(ctypes.Structure):
    _fields_ = [('user', ctypes.c_int64), ('kernel', ctypes.c_int64),
                ('period_user', ctypes.c_int64), ('period_kernel', ctypes.c_int64),
                ('faults', W.DWORD), ('total', W.DWORD),
                ('active', W.DWORD), ('terminated', W.DWORD)]


def job_cpu(worker):
    info = JobAccounting()
    query = worker.kernel.QueryInformationJobObject
    query.argtypes = [W.HANDLE, ctypes.c_int, W.LPVOID, W.DWORD, W.LPVOID]
    query.restype = W.BOOL
    if not query(worker.job, 1, ctypes.byref(info), ctypes.sizeof(info), None):
        raise ctypes.WinError(ctypes.get_last_error())
    return (info.user+info.kernel)/10_000_000


@contextmanager
def measured_child(root, operation, command):
    with ContainedProcess(command, REPO, root/f'{operation}.stdout.log', root/f'{operation}.stderr.log') as worker:
        try:
            yield worker
        finally:
            # Retain job accounting even on an exception. On forced termination
            # reserve two additional CPU seconds for the interval before close.
            code = worker.poll()
            measured = job_cpu(worker)
            freeze(root/f'{operation.upper()}_JOB_USAGE.json', dict(at=now(),
                cpu_seconds=measured+(2.0 if code is None else 0.0),
                measured_cpu_seconds=measured, termination_margin_cpu_seconds=2.0 if code is None else 0.0,
                includes_all_descendants_and_exited_processes=True, exit_code=code))


def run(root):
    plan = read(root/'PLAN.json')
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
        freeze(root/'ADMISSION.json', dict(**resources, lease=str(lease[0]), threads=2))
        deadline = min(time.monotonic()+plan['max_wall_seconds'],
                       time.monotonic()+(DRAIN-datetime.now(timezone.utc)).total_seconds())
        for operation in ('execute', 'verify'):
            atomic(root/'PROGRESS.json', dict(at=now(), phase=operation, cpu_seconds=charged))
            with measured_child(root, operation, [str(PYTHON), '-X', 'utf8', '-B', '-m',
                    'runners.drive.cards.batch_runtime_v5', '_'+operation, str(root)]) as worker:
                freeze(root/f'{operation.upper()}_CHILD.json', dict(at=now(), native=native_identity(worker.pid)))
                next_check = 0
                sampled_cpu = 0.0
                while worker.poll() is None:
                    sampled_cpu = job_cpu(worker)
                    if charged+sampled_cpu > plan['max_cpu_seconds']:
                        failure_class = 'cost'
                        charged += sampled_cpu
                        raise TimeoutError('Combined execution/replay CPU ceiling')
                    if time.monotonic() > deadline:
                        failure_class = 'cost' if datetime.now(timezone.utc) < DRAIN else 'environment'
                        charged += sampled_cpu
                        raise TimeoutError('Combined execution/replay safety wall or drain ceiling')
                    if time.monotonic() >= next_check:
                        snapshot = resource_snapshot()
                        next_check = time.monotonic()+30
                        atomic(root/'PROGRESS.json', dict(at=now(), phase=operation, cpu_seconds=charged+sampled_cpu, resources=snapshot))
                        if sum(p.stat().st_size for p in (root/'output').rglob('*') if p.is_file()) > plan.get('max_output_bytes', 32*1024**3):
                            failure_class = 'environment'
                            raise RuntimeError('Frozen output byte cap')
                        reason = yield_reason(root, plan, snapshot)
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
        if charged > plan['max_cpu_seconds']:
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['run','_execute','_verify'])
    parser.add_argument('root', type=Path)
    args = parser.parse_args()
    if args.operation == 'run':
        run(args.root.resolve())
    else:
        child_with_usage(args.root.resolve(), args.operation[1:])
