"""Finite campaign calendar: due markers and the ratified watcher restoration.

No study dispatch, scoring, model requests or publication. The durable watcher
delivers these markers to the existing owner, who performs each required digest.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from pathlib import Path
import time
from runners.stage14.common import REPO, atomic, freeze, read, filehash, now
from runners.stage9.process_identity import native_identity

MILESTONES = (
    ('DIGEST_20261017', '2026-10-18T03:00:00+00:00'),
    ('DIGEST_20261018', '2026-10-19T03:00:00+00:00'),
    ('PAID_CUTOFF', '2026-10-20T00:00:00+00:00'),
    ('DIGEST_20261019', '2026-10-20T03:00:00+00:00'),
    ('TALK_PAGE_DUE', '2026-10-21T01:00:00+00:00'),
    ('DIGEST_20261020', '2026-10-21T03:00:00+00:00'),
    ('FREEZE', '2026-10-21T13:00:00+00:00'),
    ('DRAIN_REVIEW', '2026-10-21T19:00:00+00:00'),
)


def due_names(instant, existing):
    if instant.tzinfo is None:
        raise ValueError('Calendar time requires timezone')
    return [name for name, due in MILESTONES
            if name not in existing and instant >= datetime.fromisoformat(due)]


def tick(root, config_path, instant):
    root = Path(root)
    existing = {name for name, _ in MILESTONES if (root / (name + '.json')).exists()}
    emitted = []
    for name in due_names(instant, existing):
        extra = {}
        if name == 'FREEZE':
            config = read(config_path)
            before = filehash(config_path)
            config['transition_only'] = True
            atomic(config_path, config)
            extra = dict(watcher_transition_only=True, previous_config_sha256=before,
                         restored_config_sha256=filehash(config_path))
        freeze(root / (name + '.json'), dict(at=instant.isoformat(), event=name,
            scheduled_at=dict(MILESTONES)[name], owner_action_required=True,
            scientific_verdict=False, publication_performed=False, **extra))
        emitted.append(name)
    return emitted


def run(root):
    root = root.resolve()
    plan = read(root / 'PLAN.json')
    with (root / 'ATTEMPT.claim').open('x') as stream:
        stream.write(now())
    freeze(root / 'OWNER.json', dict(at=now(), native=native_identity(), plan_sha256=filehash(root / 'PLAN.json')))
    try:
        deadline = time.monotonic() + 90
        while not (root / 'MONITOR_READY.json').exists():
            if time.monotonic() >= deadline:
                raise TimeoutError('Calendar monitoring handshake absent')
            time.sleep(.25)
        if read(root / 'MONITOR_READY.json')['owner_sha256'] != filehash(root / 'OWNER.json'):
            raise ValueError('Calendar owner binding differs')
        for path, expected in plan['pins'].items():
            if filehash(Path(path)) != expected:
                raise ValueError('Calendar pinned source differs')
        while True:
            tick(root, REPO / '.agent-state/watch.json', datetime.now(timezone.utc))
            atomic(root / 'HEARTBEAT.json', dict(at=now(), next_milestones=[name for name, _ in MILESTONES if not (root / (name + '.json')).exists()]))
            if (root / 'DRAIN_REVIEW.json').exists():
                freeze(root / 'COMPLETE.json', dict(at=now(), status='COMPLETE', calendar_only=True))
                return
            time.sleep(30)
    except Exception as exc:
        freeze(root / 'FAILED.json', dict(at=now(), status='FAILED', error=repr(exc), calendar_only=True))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    run(parser.parse_args().root)
