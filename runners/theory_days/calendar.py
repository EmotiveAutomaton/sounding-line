"""Finite theory-days freeze/drain markers, without scientific or paid dispatch.

DESIGN CHECK: LESSONS 3-5. UTC deadlines apply identically to every outcome.
Late recovery cannot reopen starts. Markers require owner landing, not verdicts.
"""
from datetime import datetime,timezone
from pathlib import Path
import argparse,time
from runners.stage14.common import REPO,read,freeze,atomic,filehash,now
from runners.stage9.process_identity import native_identity
from .policy import FREEZE,DRAIN

MILESTONES=(('FINAL_DIGEST_AND_START_FREEZE',FREEZE),('FINAL_DRAIN_RECONCILIATION',DRAIN))


def tick(root,config_path,at):
    if at.tzinfo is None:raise ValueError('Explicit timezone required')
    root=Path(root)
    due=[name for name,deadline in MILESTONES if at>=deadline and not (root/(name+'.json')).exists()]
    if at>=DRAIN:
        config=read(config_path)
        if config.get('transition_only') is not True:
            config['transition_only']=True;atomic(config_path,config)
    for name in due:
        freeze(root/(name+'.json'),dict(at=at.isoformat(),scheduled_at=dict(MILESTONES)[name].isoformat(),
            event=name,owner_action_required=True,scientific_verdict=False,publication_performed=False,
            authority='Stage 15 theory-days packet section 0',digest='results/phase_2_4_stage_15/THEORY_DAYS/DIGEST.md'))
    return due


def run(root):
    root=Path(root).resolve();plan=read(root/'PLAN.json')
    with (root/'ATTEMPT.claim').open('x') as f:f.write(now())
    freeze(root/'OWNER.json',dict(at=now(),native=native_identity(),plan_sha256=filehash(root/'PLAN.json')))
    try:
        end=time.monotonic()+90
        while not (root/'MONITOR_READY.json').exists():
            if time.monotonic()>end:raise TimeoutError('Calendar monitoring absent')
            time.sleep(.25)
        assert read(root/'MONITOR_READY.json')['owner_sha256']==filehash(root/'OWNER.json')
        for path,h in plan['pins'].items():
            if filehash(path)!=h:raise ValueError('Calendar source changed')
        while True:
            tick(root,REPO/'.agent-state/watch.json',datetime.now(timezone.utc))
            pending=[name for name,_ in MILESTONES if not (root/(name+'.json')).exists()]
            atomic(root/'HEARTBEAT.json',dict(at=now(),next_milestones=pending))
            if not pending:
                freeze(root/'COMPLETE.json',dict(at=now(),status='COMPLETE',calendar_only=True));return
            time.sleep(30)
    except Exception as exc:
        freeze(root/'FAILED.json',dict(at=now(),status='FAILED',calendar_only=True,error=repr(exc)));raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('root',type=Path);run(parser.parse_args().root)
