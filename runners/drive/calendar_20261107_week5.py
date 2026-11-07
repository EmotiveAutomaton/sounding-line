"""Week 5 calendar and build-wake maintenance, independent of older clocks.

DESIGN CHECK: LESSONS 3-5. No scientific interpretation or publication. Every
tick rereads watcher configuration, so older campaigns cannot park an open
Week 5. Drained and closed are distinct. Existing unacknowledged wakes persist.
"""
from datetime import datetime, timezone, timedelta
from pathlib import Path
import argparse,sys,time
from runners.stage14.common import REPO,read,freeze,atomic,filehash,now
from runners.stage9.process_identity import native_identity
from runners.drive.cards.week5_policy import OPEN,FREEZE,DRAIN,ADDENDUM

MILESTONES=tuple((f'DIGEST_202611{d:02d}',datetime(2026,11,d+1,4,tzinfo=timezone.utc)) for d in range(7,15))+(
    ('FINAL_DIGEST_AND_START_FREEZE',FREEZE),('FINAL_DRAIN_RECONCILIATION',DRAIN),('DRAIN_ADDENDUM_DUE',ADDENDUM))

def tick(root,config_path,at):
    if at.tzinfo is None: raise ValueError('Explicit timezone required')
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    config=read(config_path)
    desired=not (OPEN<=at<DRAIN)
    if config.get('transition_only')!=desired:
        config['transition_only']=desired;atomic(config_path,config)
        log=root/'OPS_LOG.jsonl'
        with log.open('a',encoding='utf-8',newline='\n') as f:
            import json
            f.write(json.dumps(dict(at=at.isoformat(),action='watch_mode_reset',transition_only=desired))+'\n')
    due=[]
    for name,deadline in MILESTONES:
        if at>=deadline and not (root/(name+'.json')).exists():
            freeze(root/(name+'.json'),dict(at=at.isoformat(),scheduled_at=deadline.isoformat(),event=name,
                owner_action_required=True,scientific_verdict=False,publication_performed=False,campaign='S15-WEEK5'))
            due.append(name)
    return due

def ensure_build_wake(at):
    sys.path.insert(0,str(REPO/'tools'))
    from codex_common import database,get
    from codex_watch import schedule
    with database() as db:
        current=get(db,'wake_plan')
        pending=False
        if current and current.get('event_id'):
            row=db.execute('SELECT acknowledged FROM events WHERE id=?',(current['event_id'],)).fetchone()
            pending=bool(row and row['acknowledged'] is None)
    if pending:return 'pending_owner_inspection'
    if current and at.timestamp() < current['due'] <= at.timestamp()+3600:return 'scheduled'
    if current and not current.get('event_id') and current['due']<=at.timestamp():return 'due_for_delivery'
    schedule(3300,'Week 5 commissioned build, dispatch and full landing check; amendments I–K.',now=at.timestamp())
    return 'scheduled'

def run(root):
    root=Path(root).resolve();plan=read(root/'PLAN.json')
    with (root/'ATTEMPT.claim').open('x') as f:f.write(now())
    freeze(root/'OWNER.json',dict(at=now(),native=native_identity(),plan_sha256=filehash(root/'PLAN.json')))
    try:
        end=time.monotonic()+90
        while not (root/'MONITOR_READY.json').exists():
            if time.monotonic()>end:raise TimeoutError('Calendar monitoring absent')
            time.sleep(.25)
        if read(root/'MONITOR_READY.json')['owner_sha256']!=filehash(root/'OWNER.json'):raise ValueError('Monitor identity differs')
        for p,h in plan['pins'].items():
            if filehash(p)!=h:raise ValueError('Calendar source changed')
        while True:
            at=datetime.now(timezone.utc);tick(root,REPO/'.agent-state/watch.json',at)
            wake=ensure_build_wake(at) if OPEN<=at<DRAIN else 'closed'
            pending=[n for n,_ in MILESTONES if not (root/(n+'.json')).exists()]
            atomic(root/'HEARTBEAT.json',dict(at=now(),next_milestones=pending,build_wake=wake))
            if not pending:
                freeze(root/'COMPLETE.json',dict(at=now(),status='COMPLETE',calendar_only=True));return
            time.sleep(30)
    except Exception as exc:
        freeze(root/'FAILED.json',dict(at=now(),status='FAILED',calendar_only=True,error=repr(exc)));raise

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('root',type=Path);run(parser.parse_args().root)
