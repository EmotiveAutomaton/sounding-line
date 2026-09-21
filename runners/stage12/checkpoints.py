"""Predeclared week checkpoints for the durable watcher, no research dispatch.

DESIGN CHECK: LESSONS 5. NULL: no due checkpoint causes no wake artifact.
ALTERNATIVE: each original due time emits once; restart cannot move the clock.
Cancellation emits a genuine helper exit. This cannot restart work or authorize
spend, gear, delegation or a new scientific conclusion.
"""
import argparse
from datetime import datetime,timezone
from pathlib import Path
import time
import uuid
from .common import REPO,RAW,read,freeze,atomic,filehash,now,own_cpu,limit_process
from runners.stage9.process_identity import native_identity
from tools.codex_common import singleton


def due(contract,at):
    return [(name,contract[field]) for name,field in [('interim-96h','interim'),('reporting-start','reporting'),('final-checkpoint','deadline')]
            if at>=datetime.fromisoformat(contract[field])]


def run(raw=RAW,interval=60):
    raw=Path(raw);root=raw/'checkpoints';limit_process();start_cpu=own_cpu()
    with singleton(raw/'locks/checkpoints-kernel.lock'):
        charge_path=raw/'charges/ops-checkpoints.json'
        old=read(charge_path) if charge_path.exists() else {}
        prior_cpu=old.get('cpu_seconds',0)+(60 if old.get('state')=='running' else 0)
        contract=read(raw/'CONTRACT.json');binding=filehash(raw/'CONTRACT.json')
        exit_path=root/('EXIT-'+uuid.uuid4().hex+'.json');native=native_identity()
        atomic(root/'OWNER.json',dict(native=native,at=now(),contract_sha256=binding,exit_path=str(exit_path.relative_to(REPO))))
        try:
            while True:
                if filehash(raw/'CONTRACT.json')!=binding:raise ValueError('original week clock changed')
                if (raw/'CANCEL.json').exists():reason='explicit cancellation';break
                for name,timestamp in due(contract,datetime.now(timezone.utc)):
                    path=root/(name+'.json')
                    if not path.exists():freeze(path,dict(status='complete',kind='predeclared operational checkpoint',at=now(),
                        due=timestamp,contract_sha256=binding,scientific_verdict=False,
                        action='Inspect actual completed evidence and missing work; full internal write-through; report the due stage packet. No new authority.'))
                atomic(charge_path,dict(cpu_seconds=prior_cpu+own_cpu()-start_cpu,gpu_seconds=0,
                    diagnostic_gpu_seconds=0,host_cpu_seconds=0,state='running',at=now()))
                if (root/'final-checkpoint.json').exists():reason='original final deadline reached';break
                atomic(root/'STATUS.json',dict(status='running',at=now(),native=native,contract_sha256=binding))
                time.sleep(interval)
        except BaseException as exc:
            freeze(exit_path,dict(status='failed',at=now(),native=native,error=repr(exc),scientific_verdict=False));raise
        else:
            freeze(exit_path,dict(status='complete',at=now(),native=native,reason=reason,scientific_verdict=False))
        finally:
            atomic(charge_path,dict(cpu_seconds=prior_cpu+own_cpu()-start_cpu,gpu_seconds=0,
                diagnostic_gpu_seconds=0,host_cpu_seconds=0,state='exited',at=now()))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,default=RAW)
    run(p.parse_args().raw)
