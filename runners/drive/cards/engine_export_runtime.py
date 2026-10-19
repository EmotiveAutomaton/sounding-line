"""Counted week runtime with contained native workers and two-phase monitoring.

DESIGN CHECK (2026-10-18)
Lessons read: LESSONS sections 3-5. Under null and alternative, changed pins,
resource/cost overruns or failed fresh verification prevent completion. Failure
direction: fail closed, retaining partial outputs. Operational bands exhaustive:
COMPLETE or FAILED; no automatic retry, spend, selection or scientific verdict.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from pathlib import Path
import time

from runners.drive.native_job import ContainedProcess
from .batch_runtime import (PYTHON,REPO,atomic,freeze,read,filehash,now,native_identity,
    check_files,claim_slot,release_slot,child,resource_snapshot)
from .week_policy import admission,instant


def run(root):
    plan=read(root/'PLAN.json')
    with (root/'ATTEMPT.claim').open('x') as stream:stream.write(now())
    freeze(root/'OWNER.json',dict(at=now(),native=native_identity(),plan_sha256=filehash(root/'PLAN.json')))
    lease=None
    try:
        deadline=time.monotonic()+90
        while not (root/'MONITOR_READY.json').exists():
            if time.monotonic()>deadline:raise TimeoutError('Monitor handshake absent')
            time.sleep(.25)
        if read(root/'MONITOR_READY.json')['owner_sha256']!=filehash(root/'OWNER.json'):
            raise ValueError('Monitor owner binding mismatch')
        check_files(plan['pins']);resources=admission(plan)
        lease=claim_slot(REPO/'results/.cpu-slots-20261017',native_identity(),plan['card'],slots=resources['slots'])
        freeze(root/'ADMISSION.json',dict(at=now(),**resources,lease=str(lease[0]),threads=1))
        deadline=time.monotonic()+min(plan['max_wall_seconds'],(instant(resources['drain_utc'])-datetime.now(timezone.utc)).total_seconds())
        for operation in ('execute','verify'):
            atomic(root/'PROGRESS.json',dict(at=now(),phase=operation))
            with ContainedProcess([PYTHON,'-X','utf8','-B','-m','runners.drive.cards.engine_export_runtime','_'+operation,root],
                REPO,root/f'{operation}.stdout.log',root/f'{operation}.stderr.log') as worker:
                freeze(root/f'{operation.upper()}_CHILD.json',dict(at=now(),native=native_identity(worker.pid),contained=True))
                next_check=0
                while worker.poll() is None:
                    if time.monotonic()>deadline:raise TimeoutError('Combined execution/replay bound exceeded')
                    if time.monotonic()>=next_check:
                        snapshot=resource_snapshot();next_check=time.monotonic()+2
                        size=sum(p.stat().st_size for p in (root/'output').rglob('*') if p.is_file())
                        if (snapshot['ram_available_GiB']<8 or snapshot['commit_headroom_GiB']<8
                                or snapshot['disk_free_GiB']<20 or size>plan['max_output_bytes']):
                            raise RuntimeError('Exporter resource or output floor reached')
                        atomic(root/'RESOURCES.json',dict(at=now(),phase=operation,**snapshot,output_bytes=size))
                    time.sleep(.2)
                if worker.poll()!=0:raise RuntimeError(f'{operation} child failed; retained stderr')
        check_files(plan['pins'])
        outputs={p.relative_to(root).as_posix():filehash(p) for p in root.rglob('*') if p.is_file()
            and p.suffix in {'.json','.jsonl','.gz'} and p.name not in {'PROGRESS.json','MONITOR_READY.json','RESOURCES.json'}}
        freeze(root/'COMPLETE.json',dict(at=now(),status='COMPLETE',card=plan['card'],outputs=outputs,
            fresh_process_verified=True,scientific_admission=False,write_through_required=True))
    except Exception as exc:
        freeze(root/'FAILED.json',dict(at=now(),status='FAILED',card=plan['card'],error=repr(exc),scientific_admission=False))
        raise
    finally:
        if lease:release_slot(*lease)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('operation',choices=['run','_execute','_verify'])
    parser.add_argument('root',type=Path);args=parser.parse_args()
    if args.operation=='run':run(args.root.resolve())
    else:child(args.root.resolve(),args.operation[1:])


if __name__=='__main__':main()
