"""Week 7 closing obligations. Emit an owner event for each due boundary, once."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import time
from runners.stage14.common import REPO, atomic, filehash, freeze, now, read
from runners.stage9.process_identity import native_identity

FREEZE = datetime(2026,11,27,4,tzinfo=timezone.utc)
MILESTONES = (('FINAL_START_FREEZE',FREEZE),
              ('FINAL_DRAIN_RECONCILIATION_DUE',FREEZE+timedelta(hours=2)),
              ('FINAL_ADDENDUM_DUE',FREEZE+timedelta(hours=3)))

def tick(root,at):
    if at.tzinfo is None:
        raise ValueError('An explicit UTC offset is required')
    for name,due in MILESTONES:
        path=root/(name+'.json')
        if at>=due and not path.exists():
            freeze(path,dict(at=at.isoformat(),due=due.isoformat(),campaign='S15-WEEK7',
                  event=name,owner_action_required=True,scientific_verdict=False))
    return [name for name,_ in MILESTONES if not (root/(name+'.json')).exists()]

def run(root):
    with (root/'ATTEMPT.claim').open('x') as claim:claim.write(now())
    freeze(root/'OWNER.json',dict(at=now(),native=native_identity(),plan_sha256=filehash(root/'PLAN.json')))
    try:
        deadline=time.monotonic()+90
        while not (root/'MONITOR_READY.json').exists():
            if time.monotonic()>=deadline:raise TimeoutError('Missing monitor handshake')
            time.sleep(.25)
        if read(root/'MONITOR_READY.json')['owner_sha256']!=filehash(root/'OWNER.json'):
            raise ValueError('Monitor owner mismatch')
        plan=read(root/'PLAN.json')
        if plan['milestones']!={n:d.isoformat() for n,d in MILESTONES}:raise ValueError('Calendar dates changed')
        for path,digest in plan['pins'].items():
            if filehash(path)!=digest:raise ValueError('Calendar pins changed')
        while True:
            cfg=read(REPO/'.agent-state/watch.json')
            if not cfg.get('single_pending_wake') or cfg.get('owner_idle_seconds')!=21600:
                raise RuntimeError('Unexpected wake configuration')
            pending=tick(root,datetime.now(timezone.utc))
            atomic(root/'HEARTBEAT.json',dict(at=now(),next_milestones=pending,research_dispatch=False))
            if not pending:break
            time.sleep(30)
        freeze(root/'COMPLETE.json',dict(at=now(),calendar_only=True))
    except Exception as exc:
        freeze(root/'FAILED.json',dict(at=now(),reason=str(exc),calendar_only=True))
        raise

if __name__=='__main__':
    run(Path(sys.argv[1]).resolve())
