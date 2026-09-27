"""Cheap fixed-calendar checkpoints; the existing watcher owns agent delivery.

DESIGN CHECK: LESSONS 5. NULL: setup/restart cannot move the deadline; duplicate
helpers refuse. ALTERNATIVE: reporting/final-review markers are emitted once.
This helper runs no experiment, never changes gear and never starts an agent.
"""
import time
from datetime import datetime,timezone
from .common import RAW,now,atomic,freeze,limit_process
from .report import write_checkpoint
from tools.codex_common import singleton
from runners.stage9.process_identity import native_identity

CHECKPOINTS={'reporting-start':'2026-10-02T04:00:00+00:00','final-review':'2026-10-02T10:00:00+00:00','deadline':'2026-10-02T12:00:00+00:00'}


def run(raw=RAW):
    limit_process()
    with singleton(raw/'locks/checkpoints.lock'):
        freeze(raw/'checkpoints/OWNER.json',dict(native=native_identity(),at=now(),schedule=CHECKPOINTS))
        try:
            while True:
                current=datetime.now(timezone.utc);pending=[]
                for name,at in CHECKPOINTS.items():
                    if (raw/'checkpoints'/f'{name}.json').exists():continue
                    if current>=datetime.fromisoformat(at):write_checkpoint(name,raw)
                    else:pending.append(at)
                atomic(raw/'checkpoints/HEARTBEAT.json',dict(at=now(),pending=pending))
                if not pending:break
                time.sleep(min(60,max(.1,(min(datetime.fromisoformat(a) for a in pending)-datetime.now(timezone.utc)).total_seconds())))
            freeze(raw/'checkpoints/EXIT.json',dict(status='complete',at=now(),scientific_verdict=False))
        except BaseException as exc:
            freeze(raw/'checkpoints/FAILED.json',dict(status='failed',at=now(),error=type(exc).__name__+': '+str(exc)));raise

if __name__=='__main__':run()
