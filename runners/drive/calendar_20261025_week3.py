"""Finite Week 3 operational markers; no study selection or publication.

DESIGN CHECK: LESSONS 3-5. Null/alternative studies share these deadlines.
DST uses UTC instants. Late recovery cannot reopen an ended window. Every
marker requests inspection; none asserts scientific completion.
"""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import time
from runners.stage14.common import REPO, atomic, freeze, read, filehash, now
from runners.stage9.process_identity import native_identity

MILESTONES = (
    ('DIGEST_20261025', '2026-10-26T03:00:00+00:00'),
    ('READER_IDENTITY_DUE', '2026-10-27T03:00:00+00:00'),
    ('DIGEST_20261026', '2026-10-27T03:00:00+00:00'),
    ('DIGEST_20261027', '2026-10-28T03:00:00+00:00'),
    ('WB1_RETURN_DUE', '2026-10-28T19:00:00+00:00'),
    ('DIGEST_20261028', '2026-10-29T03:00:00+00:00'),
    ('DIGEST_20261029', '2026-10-30T03:00:00+00:00'),
    ('PAID_CUTOFF', '2026-10-31T00:00:00+00:00'),
    ('DIGEST_20261030', '2026-10-31T03:00:00+00:00'),
    ('DIGEST_20261031', '2026-11-01T03:00:00+00:00'),
    ('FINAL_DIGEST_AND_START_FREEZE', '2026-11-02T04:00:00+00:00'),
    ('FINAL_DRAIN_RECONCILIATION', '2026-11-02T06:00:00+00:00'),
    ('DRAIN_ADDENDUM_DUE', '2026-11-02T07:00:00+00:00'),
)


def due_names(at, existing):
    if at.tzinfo is None:
        raise ValueError('Explicit timezone required')
    return [name for name, due in MILESTONES if name not in existing and at >= datetime.fromisoformat(due)]


def tick(root, config_path, at):
    root = Path(root)
    due = due_names(at, {name for name, _ in MILESTONES if (root/(name+'.json')).exists()})
    if 'FINAL_DRAIN_RECONCILIATION' in due:
        config = read(config_path)
        config['transition_only'] = True
        atomic(config_path, config)
    for name in due:
        freeze(root/(name+'.json'), dict(at=at.isoformat(), event=name,
            scheduled_at=dict(MILESTONES)[name], owner_action_required=True,
            scientific_verdict=False, publication_performed=False,
            authority='SOUNDING_LINE_STAGE15_WEEK3_PACKET_2026-10-25'))
    return due


def run(root):
    root = Path(root).resolve()
    plan = read(root/'PLAN.json')
    with (root/'ATTEMPT.claim').open('x') as stream:
        stream.write(now())
    freeze(root/'OWNER.json', dict(at=now(), native=native_identity(), plan_sha256=filehash(root/'PLAN.json')))
    try:
        deadline = time.monotonic() + 90
        while not (root/'MONITOR_READY.json').exists():
            if time.monotonic() > deadline:
                raise TimeoutError('Calendar monitoring absent')
            time.sleep(.25)
        if read(root/'MONITOR_READY.json')['owner_sha256'] != filehash(root/'OWNER.json'):
            raise ValueError('Owner binding differs')
        for path, digest in plan['pins'].items():
            if filehash(path) != digest:
                raise ValueError('Calendar source changed')
        while True:
            tick(root, REPO/'.agent-state/watch.json', datetime.now(timezone.utc))
            pending = [n for n, _ in MILESTONES if not (root/(n+'.json')).exists()]
            atomic(root/'HEARTBEAT.json', dict(at=now(), next_milestones=pending))
            if not pending:
                freeze(root/'COMPLETE.json', dict(at=now(), status='COMPLETE', calendar_only=True))
                return
            time.sleep(30)
    except Exception as exc:
        freeze(root/'FAILED.json', dict(at=now(), status='FAILED', error=repr(exc), calendar_only=True))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    run(parser.parse_args().root)
