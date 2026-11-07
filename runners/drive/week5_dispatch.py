"""Dispatch only explicitly prepared and owner-reviewed immutable Week 5 plans.

DESIGN CHECK: LESSONS 3–5. This does not translate TODO, design experiments,
interpret results, publish, retry failures or create follow-ups. Changed plans
and sources refuse; completed/attempted identities never restart. Runtime
admission rechecks clocks, native leases, resource peaks and measured budgets.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,time
from runners.stage14.common import REPO,read,atomic,freeze,filehash,now
from runners.stage9.process_identity import native_identity
from runners.drive import week5_launch_v2 as launcher
from runners.drive.cards import week5_policy as policy

def candidates(registry,base=policy.ROOT):
    entries=registry['entries'];seen=set();pending=[]
    for entry in entries:
        root=Path(entry['root']).resolve();root.relative_to(base.resolve())
        if root in seen:raise ValueError('Duplicate queue identity')
        seen.add(root)
        if (root/'ATTEMPT.claim').exists():continue
        if any((root/(n+'.json')).exists() for n in ('COMPLETE','FAILED','PAUSED','MONITOR_FAILED')):continue
        if filehash(root/'PLAN.json')!=entry['plan_sha256']:raise ValueError('Queue plan bytes changed')
        pending.append(entry)
    return sorted(pending,key=lambda x:(x['priority'],x['root']))

def dispatch_once(registry):
    started=[];waiting=[]
    for entry in candidates(registry):
        root=Path(entry['root']);plan=read(root/'PLAN.json')
        try:
            launcher.review(plan)
            policy.admission(plan)
        except Exception as exc:
            waiting.append(dict(card=plan['card'],reason=str(exc)));continue
        try:
            started.append(launcher.launch(root))
        except Exception as exc:
            # A handshake failure never triggers a second process launch here.
            waiting.append(dict(card=plan['card'],reason=str(exc),attempted=(root/'ATTEMPT.claim').exists()))
    return dict(started=started,waiting=waiting)

def run(root):
    root=Path(root).resolve();plan=read(root/'PLAN.json')
    with (root/'ATTEMPT.claim').open('x',encoding='utf8') as f:f.write(now())
    freeze(root/'OWNER.json',dict(at=now(),native=native_identity(),plan_sha256=filehash(root/'PLAN.json')))
    try:
        until=time.monotonic()+90
        while not (root/'MONITOR_READY.json').exists():
            if time.monotonic()>until:raise TimeoutError('Dispatcher monitor handshake')
            time.sleep(.2)
        if read(root/'MONITOR_READY.json')['owner_sha256']!=filehash(root/'OWNER.json'):raise ValueError('Monitor identity mismatch')
        for p,h in plan['pins'].items():
            if filehash(p)!=h:raise ValueError('Dispatcher source changed')
        while datetime.now(timezone.utc)<policy.DRAIN:
            if datetime.now(timezone.utc)<policy.FREEZE:
                registry=read(plan['registry']);state=dispatch_once(registry)
            else:state=dict(started=[],waiting=[],start_freeze=True)
            atomic(root/'HEARTBEAT.json',dict(at=now(),**state))
            if state['started']:
                with (root/'DISPATCH.jsonl').open('a',encoding='utf8',newline='\n') as f:
                    import json
                    for row in state['started']:f.write(json.dumps(dict(at=now(),**row))+'\n')
            time.sleep(30)
        freeze(root/'COMPLETE.json',dict(at=now(),status='COMPLETE',dispatch_only=True))
    except Exception as exc:
        freeze(root/'FAILED.json',dict(at=now(),status='FAILED',error=repr(exc),dispatch_only=True));raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);run(p.parse_args().root)
