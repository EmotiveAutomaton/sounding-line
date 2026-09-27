"""Dependency-ordered Stage 13 declarations for the existing native queue engine.

DESIGN CHECK: LESSONS 3-5. NULL: cycles, duplicate IDs/owners or corrupt completed
outputs refuse. ALTERNATIVE: an input listed after its consumer is sorted before
it, and independent work continues after failures. Gear 1 excludes GPU cards.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
import sysconfig
import uuid
from .common import RAW,REPO,read,freeze,atomic,filehash,check_pins,now,limit_process
from .worker import verify
from tools.codex_common import singleton
from runners.stage9.process_identity import native_identity


def topological(cards):
    by={c['id']:c for c in cards}
    if len(by)!=len(cards):raise ValueError('duplicate job ID')
    waiting=list(cards);done=set();result=[]
    while waiting:
        eligible=[c for c in waiting if not (set(c.get('requires',[]))&set(by)-done)]
        if not eligible:raise ValueError('dependency cycle')
        c=eligible[0];result.append(c);done.add(c['id']);waiting.remove(c)
    return result


def run(plan_path,raw=RAW):
    from runners import run_queue as engine
    limit_process();plan_path=Path(plan_path);plan=read(plan_path)
    if filehash(raw/'CONTRACT.json')!=plan['contract_sha256']:raise ValueError('campaign contract changed')
    if plan.get('conditional'):
        from datetime import datetime,timezone,timedelta
        end=datetime.fromisoformat(read(raw/'CONTRACT.json')['reporting'])
        if datetime.now(timezone.utc)+timedelta(seconds=plan['minimum_whole_family_seconds'])>=end:raise RuntimeError('conditional whole family does not fit fixed reserve')
    check_pins(plan['source_pins']);cards=[]
    for name in plan['cards']:
        p=raw/'manifests'/f'{name}.json'
        if filehash(p)!=plan['manifest_hashes'][name]:raise ValueError('card changed')
        card=read(p)
        if (raw/'jobs'/name/'COMPLETE.json').exists():
            record=verify(raw/'jobs'/name)
            if record['card_sha256']!=filehash(p):raise ValueError('completed job changed card')
        cards.append(card)
    cards=topological(cards);queue_root=raw/'queue'/plan['id']
    with singleton(raw/'locks/queue-kernel.lock'):
        native=native_identity();exit_path=queue_root/('EXIT-'+uuid.uuid4().hex+'.json')
        atomic(queue_root/'OWNER.json',dict(at=now(),native=native,plan_sha256=filehash(plan_path),exit_path=str(exit_path.relative_to(REPO))))
        stages=[]
        for c in cards:
            entry=("import os,sys,runpy;os.environ['SL_STAGE13_REPO']="+repr(str(REPO))+";sys.path.insert(0,"+repr(sysconfig.get_paths()['purelib'])+");sys.path.insert(0,"+repr(str(raw/plan['source_capsule']))+");import runners;runners.__path__.append("+repr(str(REPO/'runners'))+");runpy.run_module('runners.stage13.worker',run_name='__main__')")
            stages.append(dict(name='S13-'+c['id'],cmd=[native['executable'],'-B','-c',entry,'--card',str(raw/'manifests'/f"{c['id']}.json"),'--raw',str(raw)],
                produces=str((raw/'jobs'/c['id']/'COMPLETE.json').relative_to(REPO)),needs=[str((raw/'jobs'/n/'COMPLETE.json').relative_to(REPO)) for n in c.get('requires',[])],
                resource=c['resource'],gpu=c['resource']=='gpu',est=max(5,c['wall_seconds']/360),why=c['question']))
        engine.REPO=REPO;engine.STAGES=stages;engine.STATUS=queue_root/'STATUS.json';engine.LOCK=raw/'locks/queue-native.lock'
        original=engine._owner_state
        def verified(record):
            try:
                if native_identity(record['pid']) is None:return 'exited'
            except (OSError,KeyError,ValueError):return 'unknown'
            return original(record)
        engine._owner_state=verified;old=sys.argv
        sys.argv=['stage13-native-queue']+(['--no-gpu'] if read(raw/'ALLOCATION.json')['gear']==1 else [])
        try:engine.main()
        finally:engine._release_lock();engine._owner_state=original;sys.argv=old
        state=read(engine.STATUS)
        atomic(queue_root/'AWAITING_SELECTION.json',dict(status='waiting',at=now(),plan_sha256=filehash(plan_path),stages=state['stages'],held_for_gear2=state.get('held_for_gear2',[]),
            action='Land whole outputs and inspect eligible successors under unchanged absolute deadline; a queue pass is not campaign completion'))
        freeze(exit_path,dict(status='complete',at=now(),native=native,kind='native queue pass exit',scientific_verdict=False,plan_sha256=filehash(plan_path)))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--plan',type=Path,required=True);p.add_argument('--raw',type=Path,default=RAW);a=p.parse_args()
    try:run(a.plan,a.raw)
    except BaseException as exc:
        freeze(a.raw/'queue'/read(a.plan)['id']/'FAILED.json',dict(status='failed',at=now(),error=type(exc).__name__+': '+str(exc)))
        raise
