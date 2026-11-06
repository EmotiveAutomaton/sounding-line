"""Finite retrieval-only monitor for an explicitly submitted Week 4 batch.

DESIGN CHECK: LESSONS 5. No submission or retry method is called. Missing,
unknown or changed identities stop with retained evidence. Completion requests
owner write-through and does not itself license scientific interpretation.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,time
from runners.stage14.common import freeze,atomic,read,filehash,now
from runners.stage9.process_identity import native_identity
from runners.drive import week4_proc_prompt_h1

def run(phase):
    folder=week4_proc_prompt_h1.ROOT/phase
    plan=read(folder/'MONITOR_PLAN.json')
    for name,sha in plan['pins'].items():
        if filehash(name)!=sha:raise ValueError('Monitor source or admission binding changed')
    freeze(folder/'MONITOR_OWNER.json',dict(native=native_identity(),at=now()))
    try:
        deadline=time.monotonic()+300
        while not (folder/'SUBMITTED.json').exists():
            if (folder/'UNKNOWN.json').exists():raise RuntimeError('Unknown submission; reservation retained, no retry')
            if time.monotonic()>deadline:raise TimeoutError('Submission not observed; no submission performed by monitor')
            time.sleep(2)
        binding=filehash(folder/'SUBMITTED.json')
        while True:
            if filehash(folder/'SUBMITTED.json')!=binding:raise ValueError('Submission identity changed')
            result=week4_proc_prompt_h1.retrieve(phase)
            atomic(folder/'MONITOR_HEARTBEAT.json',dict(at=now(),status=result.get('status')))
            if result.get('status')=='COMPLETE':return
            if datetime.now(timezone.utc)>=datetime.fromisoformat('2026-11-09T07:00:00+00:00'):
                raise TimeoutError('Finite retrieval window ended; retrieve only')
            time.sleep(60)
    except BaseException as exc:
        freeze(folder/'MONITOR_FAILED.json',dict(at=now(),error_type=type(exc).__name__,error=str(exc),submission_retry_authorized=False))
        raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['calibration','main']);run(p.parse_args().phase)
