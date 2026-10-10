"""Fixed reporting markers only; never dispatch science or extend authority.

DESIGN CHECK: LESSONS 5. NULL: future markers do not emit; changed bindings,
duplicate owners and invalid calendars refuse. ALTERNATIVE: due markers emit
once, reentry preserves their bytes, and the actual watcher carries delivery.
"""
import argparse
import time
from datetime import datetime, timezone
from pathlib import Path

from .common import atomic, filehash, freeze, limits, now, read, check_pins
from runners.stage9.process_identity import native_identity
from tools.codex_common import singleton


def run(root, interval=30):
    root=Path(root); proc=limits(); started=proc.cpu_times()
    contract=read(root/'CONTRACT.json'); pin=filehash(root/'CONTRACT.json')
    names=('reporting','final_review','deadline')
    if set(contract['schedule'])!=set(names): raise ValueError('invalid checkpoint names')
    schedule={k:contract['schedule'][k] for k in names}; times=[datetime.fromisoformat(x) for x in schedule.values()]
    if any(x.tzinfo is None for x in times) or times!=sorted(times):
        raise ValueError('invalid ordered checkpoint schedule')
    check_pins(contract['source_pins'])
    with singleton(root/'checkpoints.lock'):
        atomic(root/'OWNER.json',dict(native=native_identity(),at=now(),contract_sha256=pin))
        try:
            while True:
                if filehash(root/'CONTRACT.json')!=pin: raise ValueError('checkpoint contract changed')
                check_pins(contract['source_pins'])
                if (root/'CANCEL.json').exists(): reason='explicit cancellation'; break
                pending={}
                for name,due in schedule.items():
                    if (root/f'{name}.json').exists():
                        saved=read(root/f'{name}.json')
                        if saved['contract_sha256']!=pin or saved['scheduled_at']!=due: raise ValueError('checkpoint binding changed')
                    elif datetime.now(timezone.utc)>=datetime.fromisoformat(due):
                        freeze(root/f'{name}.json',dict(status='complete',at=now(),scheduled_at=due,contract_sha256=pin,scientific_verdict=False,
                            action='Inspect completed evidence, preserve unfinished cells and assemble the Friday packet. No new authority.'))
                    else: pending[name]=due
                atomic(root/'HEARTBEAT.json',dict(at=now(),pending=pending,scientific_verdict=False))
                if not pending: reason='fixed final checkpoint emitted'; break
                time.sleep(interval)
            if not (root/'EXIT.json').exists():
                freeze(root/'EXIT.json',dict(status='complete',at=now(),reason=reason,contract_sha256=pin,scientific_verdict=False))
        except BaseException as exc:
            atomic(root/'FAILED.json',dict(status='failed',at=now(),error=repr(exc),contract_sha256=pin,scientific_verdict=False))
            raise
        finally:
            ended=proc.cpu_times()
            atomic(root/'COST.json',dict(cpu_seconds=ended.user+ended.system-started.user-started.system,gpu_seconds=0,at=now()))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);run(p.parse_args().root)
