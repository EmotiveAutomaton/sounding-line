"""Finite additional week deadlines; no study dispatch or publication."""
from datetime import datetime,timezone
from pathlib import Path
import argparse
import time
from runners.stage14.common import REPO,atomic,freeze,read,filehash,now
from runners.stage9.process_identity import native_identity

MILESTONES=(
    ('ENGINE_EXPORT_DUE','2026-10-19T19:00:00+00:00'),
    ('ENGINE_WRAPPER_FALLBACK','2026-10-19T21:00:00+00:00'),
    ('DIGEST_20261021','2026-10-22T03:00:00+00:00'),
    ('POST_TALK_OPEN','2026-10-22T14:00:00+00:00'),
    ('DIGEST_20261022','2026-10-23T03:00:00+00:00'),
    ('DIGEST_20261023','2026-10-24T03:00:00+00:00'),
    ('DIGEST_20261024','2026-10-25T03:00:00+00:00'),
    ('FINAL_DIGEST_AND_START_FREEZE','2026-10-26T03:00:00+00:00'),
    ('FINAL_DRAIN_RECONCILIATION','2026-10-26T05:00:00+00:00'))


def due_names(at,existing):
    if at.tzinfo is None:raise ValueError('Explicit timezone required')
    return [name for name,due in MILESTONES if name not in existing and at>=datetime.fromisoformat(due)]


def tick(root,config_path,at):
    root=Path(root)
    due=due_names(at,{name for name,_ in MILESTONES if (root/(name+'.json')).exists()})
    if 'POST_TALK_OPEN' in due or 'FINAL_DRAIN_RECONCILIATION' in due:
        # Late recovery must not temporarily reopen an already-ended window.
        final=at>=datetime.fromisoformat(dict(MILESTONES)['FINAL_DRAIN_RECONCILIATION'])
        config=read(config_path);config['transition_only']=final;atomic(config_path,config)
    for name in due:
        freeze(root/(name+'.json'),dict(at=at.isoformat(),event=name,scheduled_at=dict(MILESTONES)[name],
            owner_action_required=True,scientific_verdict=False,publication_performed=False,
            authority='WEEK_PACKET_20261018; review dependencies and execute only an already authorized/admitted plan'))
    return due


def run(root):
    root=Path(root).resolve();plan=read(root/'PLAN.json')
    with (root/'ATTEMPT.claim').open('x') as f:f.write(now())
    freeze(root/'OWNER.json',dict(at=now(),native=native_identity(),plan_sha256=filehash(root/'PLAN.json')))
    try:
        deadline=time.monotonic()+90
        while not (root/'MONITOR_READY.json').exists():
            if time.monotonic()>deadline:raise TimeoutError('Calendar monitoring absent')
            time.sleep(.25)
        if read(root/'MONITOR_READY.json')['owner_sha256']!=filehash(root/'OWNER.json'):raise ValueError('Owner binding differs')
        for p,h in plan['pins'].items():
            if filehash(p)!=h:raise ValueError('Calendar source changed')
        while True:
            tick(root,REPO/'.agent-state/watch.json',datetime.now(timezone.utc))
            pending=[n for n,_ in MILESTONES if not (root/(n+'.json')).exists()]
            atomic(root/'HEARTBEAT.json',dict(at=now(),next_milestones=pending))
            if not pending:
                freeze(root/'COMPLETE.json',dict(at=now(),status='COMPLETE',calendar_only=True));return
            time.sleep(30)
    except Exception as exc:
        freeze(root/'FAILED.json',dict(at=now(),status='FAILED',error=repr(exc),calendar_only=True));raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('root',type=Path);run(parser.parse_args().root)
