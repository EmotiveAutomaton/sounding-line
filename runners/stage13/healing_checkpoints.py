"""Revised calendar markers, not experiment launch or scientific verdict.

DESIGN CHECK: LESSONS 5. NULL: missing/changed contract and duplicate native owner
refuse; cancellation preserves its receipt. ALTERNATIVE: each fixed marker emits
once and the sole durable watcher delivers it. Marker is not a final packet.
"""
import argparse
import time
from pathlib import Path
from datetime import datetime,timezone
from .common import read,freeze,atomic,now,filehash,limit_process
from tools.codex_common import singleton
from runners.stage9.process_identity import native_identity


def run(raw):
    limit_process();contract=read(raw/'CONTRACT.json');pin=filehash(raw/'CONTRACT.json')
    schedule={k:contract[k] for k in ('reporting','final_review','deadline')}
    folder=raw/'checkpoints'
    with singleton(raw/'locks/checkpoints.lock'):
        freeze(folder/'OWNER.json',dict(native=native_identity(),at=now(),schedule=schedule,contract_sha256=pin))
        try:
            while True:
                if filehash(raw/'CONTRACT.json')!=pin:raise ValueError('checkpoint contract changed')
                if (folder/'CANCEL.json').exists():
                    freeze(folder/'EXIT.json',dict(status='complete',at=now(),reason='explicit cancellation',scientific_verdict=False));return
                pending={}
                for name,at in schedule.items():
                    if (folder/f'{name}.json').exists():continue
                    if datetime.now(timezone.utc)>=datetime.fromisoformat(at):
                        freeze(folder/f'{name}.json',dict(status='complete',at=now(),scheduled_at=at,scientific_verdict=False,
                            action='Inspect complete cells, reconcile deficits and assemble final packet under Thursday deadline'))
                    else:pending[name]=at
                atomic(folder/'HEARTBEAT.json',dict(at=now(),pending=pending))
                if not pending:break
                time.sleep(30)
            freeze(folder/'EXIT.json',dict(status='complete',at=now(),scientific_verdict=False))
        except BaseException as exc:
            freeze(folder/'FAILED.json',dict(status='failed',at=now(),error=type(exc).__name__+': '+str(exc)));raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);run(p.parse_args().raw)
