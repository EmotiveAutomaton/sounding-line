"""Dispatch only reviewed immutable Week 5 plans through runtime v4.

DESIGN CHECK: LESSONS 3-5. No TODO translation, scientific decisions, new
plans, retries or publication. An ambiguous launch permanently holds that
attempt for owner inspection; capacity refusals before launch remain waiting.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,time,json
from runners.stage14.common import REPO,atomic,freeze,filehash,now
from runners.stage9.process_identity import native_identity
from runners.drive import week5_launch_v4 as launcher
from runners.drive.cards import week5_policy_v2 as policy
read=policy.read


def candidates(registry,base=policy.ROOT):
    seen=set();pending=[]
    for entry in registry['entries']:
        root=Path(entry['root']).resolve();root.relative_to(base.resolve())
        if root in seen:raise ValueError('Duplicate queue identity')
        seen.add(root)
        if any(policy.present(root/name) for name in ('ATTEMPT.claim','DISPATCH_ATTEMPT.json','COMPLETE.json','FAILED.json','PAUSED.json','MONITOR_FAILED.json')):continue
        if filehash(root/'PLAN.json')!=entry['plan_sha256']:raise ValueError('Queue plan bytes changed')
        pending.append(entry)
    return sorted(pending,key=lambda x:(x['priority'],x['root']))


def dispatch_once(registry,base=policy.ROOT):
    started=[];waiting=[]
    for entry in candidates(registry,base):
        root=Path(entry['root']);plan=read(root/'PLAN.json')
        try:
            launcher.review(plan);policy.admission(plan)
        except Exception as exc:
            waiting.append(dict(card=plan['card'],reason=str(exc)));continue
        # Saved before the launcher: a failed handshake can leave a process
        # running before ATTEMPT.claim appears. Never retry it on a later scan.
        freeze(root/'DISPATCH_ATTEMPT.json',dict(at=now(),plan_sha256=entry['plan_sha256'],dispatcher=native_identity()))
        try:started.append(launcher.launch(root))
        except Exception as exc:
            refusal=dict(at=now(),card=plan['card'],reason=str(exc),owner_inspection_required=True)
            freeze(root/'DISPATCH_REVIEW_REQUIRED.json',refusal);waiting.append(refusal)
    return dict(started=started,waiting=waiting)


def run(root):
    root=Path(root).resolve();plan=read(root/'PLAN.json')
    with (root/'ATTEMPT.claim').open('x',encoding='utf8') as f:f.write(now())
    freeze(root/'OWNER.json',dict(at=now(),native=native_identity(),plan_sha256=filehash(root/'PLAN.json')))
    try:
        until=time.monotonic()+90
        while not policy.present(root/'MONITOR_READY.json'):
            if time.monotonic()>until:raise TimeoutError('Dispatcher monitor handshake')
            time.sleep(.2)
        if read(root/'MONITOR_READY.json')['owner_sha256']!=filehash(root/'OWNER.json'):raise ValueError('Monitor identity mismatch')
        for p,h in plan['pins'].items():
            if filehash(p)!=h:raise ValueError('Dispatcher source changed')
        while datetime.now(timezone.utc)<policy.DRAIN:
            if policy.present(root/'STOP_REQUEST.json'):break
            state=dispatch_once(read(plan['registry'])) if datetime.now(timezone.utc)<policy.FREEZE else dict(started=[],waiting=[],start_freeze=True)
            atomic(root/'HEARTBEAT.json',dict(at=now(),**state))
            if state['started']:
                with (root/'DISPATCH.jsonl').open('a',encoding='utf8',newline='\n') as f:
                    for row in state['started']:f.write(json.dumps(dict(at=now(),**row))+'\n')
            time.sleep(30)
        freeze(root/'COMPLETE.json',dict(at=now(),status='COMPLETE',dispatch_only=True))
    except Exception as exc:
        freeze(root/'FAILED.json',dict(at=now(),status='FAILED',error=repr(exc),dispatch_only=True));raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);run(p.parse_args().root)
