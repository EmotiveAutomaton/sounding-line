"""Stage-scoped declarations for the existing native queue; no scheduler rewrite.

DESIGN CHECK: LESSONS 3-5. NULL: one failed card does not block independent
families; produced cards skip on reentry. ALTERNATIVE: unavailable prerequisites
remain deferred. A kernel owner prevents overlapping queues, including after
an inaccessible identity. Each worker has no detached children, checks its own
clock/cost boundaries and is bounded by the native engine's outer timeout.
"""
from __future__ import annotations
import argparse
import sys
import sysconfig
import uuid
from pathlib import Path
from .common import RAW, REPO, SOURCE, read, freeze, atomic, check_pins, filehash, now, limit_process
from tools.codex_common import singleton
from runners.stage9.process_identity import native_identity

def run(plan_path,raw=RAW):
    from runners import run_queue as engine
    raw=Path(raw);plan_path=Path(plan_path);plan=read(plan_path)
    if filehash(raw/'CONTRACT.json')!=plan['contract_sha256']:raise ValueError('original week contract changed')
    queue_root=raw/plan.get('queue_directory','queue')
    if not queue_root.resolve().is_relative_to(raw.resolve()):raise ValueError('queue output outside stage')
    limit_process();check_pins(plan['source_pins'])
    with singleton(raw/'locks/queue-kernel.lock'):
        native=native_identity()
        exit_path=queue_root/('EXIT-'+uuid.uuid4().hex+'.json')
        atomic(queue_root/'OWNER.json',dict(native=native,at=now(),plan_sha256=filehash(plan_path),
                                        exit_path=str(exit_path.relative_to(REPO))))
        stages=[]
        for item in plan['cards']:
            cp=raw/'manifests'/(item+'.json');card=read(cp)
            if filehash(cp)!=plan['manifest_hashes'][item]:raise ValueError('queue card changed')
            entry=("import sys,runpy;sys.path.insert(0,"+repr(sysconfig.get_paths()['purelib'])+");sys.path.insert(0,"+repr(str(SOURCE))+");import runners;"
                   "runners.__path__.append("+repr(str(REPO/'runners'))+");runpy.run_module('runners.stage12.worker',run_name='__main__')")
            # Invoke the actual interpreter directly. The Windows venv launcher
            # creates a child; killing that launcher alone can orphan its worker.
            stages.append(dict(name='S12-'+item,cmd=[native['executable'],'-B','-c',entry,
                '--card',str(cp),'--raw',str(raw)],
                produces=str((raw/'jobs'/item/'COMPLETE.json').relative_to(REPO)),
                needs=card.get('needs',[]),resource=card['resource'],gpu=card['resource']=='gpu',
                est=max(5,card['wall_seconds']/360),why=card['question']))
        # A private stage namespace and serial shard reuse the existing queue's
        # failure-continuation, produces inspection and timeout machinery.
        engine.REPO=REPO;engine.STAGES=stages;engine.STATUS=queue_root/'STATUS.json';engine.LOCK=raw/'locks/queue-native.lock'
        original_owner=engine._owner_state
        def verified_owner(record):
            try:
                if native_identity(record['pid']) is None:return 'exited'
            except (OSError,KeyError,ValueError):return 'unknown'
            return original_owner(record)
        engine._owner_state=verified_owner
        old=sys.argv;sys.argv=['stage12-native-queue']
        try:engine.main()
        finally:
            engine._release_lock();sys.argv=old
        state=read(engine.STATUS)
        # A drained pass may contain waiting or failed scientific cards. It is
        # never called campaign COMPLETE and does not close the week.
        atomic(queue_root/'AWAITING_SELECTION.json',dict(status='waiting',at=now(),native=native,
            plan_sha256=filehash(plan_path),stages=state['stages'],
            action='Land completed cards; inspect named missing inputs and eligible successors within the original week'))
        freeze(exit_path,dict(status='complete',at=now(),native=native,
            scientific_verdict=False,kind='native queue pass exit',plan_sha256=filehash(plan_path),
            waiting_or_failed_cards_retained=True))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--plan',required=True,type=Path);p.add_argument('--raw',type=Path,default=RAW)
    a=p.parse_args();run(a.plan,a.raw)
