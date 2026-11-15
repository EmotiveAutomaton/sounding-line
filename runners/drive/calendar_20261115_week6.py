"""Week 6 milestones only; the durable watcher owns event/idle delivery.

DESIGN CHECK: LESSONS 3-5, 2026-11-15. A start-time notification is never actual
predecessor drain or research admission. All milestones emit once and preserve
their first bytes; no hourly wake, research dispatch or publication occurs.
"""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import time
from runners.stage14.common import REPO, read, freeze, atomic, filehash, now
from runners.stage9.process_identity import native_identity
from runners.drive.cards.week6_policy_v1 import OPEN, FREEZE, DRAIN, ADDENDUM

MILESTONES = (('START_GATE_REVIEW_DUE', OPEN),) + tuple(
    (f'DIGEST_202611{day:02d}', datetime(2026, 11, day+1, 4, tzinfo=timezone.utc))
    for day in range(16, 22)
) + (('FINAL_DIGEST_AND_START_FREEZE', FREEZE),
     ('FINAL_DRAIN_RECONCILIATION', DRAIN), ('DRAIN_ADDENDUM_DUE', ADDENDUM))


def tick(root, config_path, at):
    if at.tzinfo is None:
        raise ValueError('Explicit timezone required')
    config = read(config_path)
    if config.get('wake_mode') != 'events_and_idle' or config.get('fallback_seconds') != 14400 or not config.get('single_pending_wake'):
        raise ValueError('Preserved event/four-hour/single-pending configuration required')
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    due = []
    for name, deadline in MILESTONES:
        if at >= deadline and not (root/(name+'.json')).exists():
            freeze(root/(name+'.json'), dict(at=at.isoformat(), scheduled_at=deadline.isoformat(),
                event=name, owner_action_required=True, scientific_verdict=False,
                research_admitted=False, publication_performed=False, campaign='S15-WEEK6'))
            due.append(name)
    return due


def run(root):
    root = Path(root).resolve()
    plan = read(root/'PLAN.json')
    with (root/'ATTEMPT.claim').open('x') as stream:
        stream.write(now())
    freeze(root/'OWNER.json', dict(at=now(), native=native_identity(), plan_sha256=filehash(root/'PLAN.json')))
    try:
        deadline = time.monotonic()+90
        while not (root/'MONITOR_READY.json').exists():
            if time.monotonic() > deadline:
                raise TimeoutError('Calendar monitor handshake absent')
            time.sleep(.25)
        if read(root/'MONITOR_READY.json')['owner_sha256'] != filehash(root/'OWNER.json'):
            raise ValueError('Calendar owner binding differs')
        for path, digest in plan['pins'].items():
            if filehash(path) != digest:
                raise ValueError('Calendar source changed')
        while True:
            at = datetime.now(timezone.utc)
            tick(root, REPO/'.agent-state/watch.json', at)
            pending = [name for name, _ in MILESTONES if not (root/(name+'.json')).exists()]
            atomic(root/'HEARTBEAT.json', dict(at=now(), next_milestones=pending,
                wake_policy='events_and_four_hour_idle_single_pending', research_dispatch=False))
            if not pending:
                freeze(root/'COMPLETE.json', dict(at=now(), status='COMPLETE', calendar_only=True))
                return
            time.sleep(30)
    except Exception as exc:
        freeze(root/'FAILED.json', dict(at=now(), status='FAILED', calendar_only=True, error=repr(exc)))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    run(parser.parse_args().root)
