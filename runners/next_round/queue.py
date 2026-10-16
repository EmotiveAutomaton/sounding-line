"""Finite, serial, local Phase 0 worker. A launch is not a scientific verdict.

DESIGN CHECK: LESSONS 3-5 read 2026-10-14. NULL: changed pins, duplicate
attempt, missing resources or past deadline refuses; no retry hides failure.
ALTERNATIVE: admitted CPU work writes durable checkpoints and verified terminal
hashes. Monitor only this native identity; never touch another project's work.
"""
import os
for _name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[_name]='1'
import argparse, ctypes, sys, threading, time, traceback
from datetime import datetime, timezone
from pathlib import Path
import psutil
from runners.stage14.common import REPO, read, freeze, atomic, pins, check_pins, filehash, limits, now
from runners.stage9.process_identity import native_identity

ROOT=REPO/'results/phase_2_4_stage_15/raw/phase0-v1'
DEADLINE=datetime.fromisoformat('2026-10-16T17:00:00+00:00').timestamp()


def resource_snapshot():
    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(n,ctypes.c_ulonglong) for n in
            ('total_phys','avail_phys','total_page','avail_page','total_virtual','avail_virtual','avail_extended')]
    m=MEMORYSTATUSEX(); m.length=ctypes.sizeof(m)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
        raise OSError('host commit inspection unavailable')
    return dict(ram_available_GiB=m.avail_phys/1024**3,commit_headroom_GiB=m.avail_page/1024**3,
                disk_free_GiB=psutil.disk_usage(str(REPO)).free/1024**3)


def require_resources(snapshot):
    if snapshot['ram_available_GiB']<8 or snapshot['commit_headroom_GiB']<8 or snapshot['disk_free_GiB']<20:
        raise RuntimeError('resource floor refused')


def prepare():
    limits(); require_resources(resource_snapshot())
    if (ROOT/'PLAN.json').exists(): raise ValueError('already prepared; inspect, do not replace')
    ROOT.mkdir(parents=True,exist_ok=True)
    from runners.stage14_midweek.data import load_source
    from .phase0 import BASE,verify_manifest
    verify_manifest(BASE/'modal-analysis-v2'); verify_manifest(BASE/'baselines-v1')
    sessions, source_pins, exclusions=load_source()
    clean=[]
    for s in sessions:
        if not s['rows']: continue
        clean.append({k:s[k] for k in ('session','writer','prompt','timestamp','end_at','rows')})
    del sessions
    prepared=ROOT/'prepared'
    freeze(prepared/'SESSIONS.json',clean); freeze(prepared/'EXCLUSIONS.json',exclusions)
    freeze(prepared/'SOURCE_PINS.json',source_pins)
    freeze(prepared/'CENSUS.json',dict(sessions=len(clean),writers=len({s['writer'] for s in clean}),
        decisions=sum(len(s['rows']) for s in clean),chronology_exclusions=len(exclusions),historically_exposed=True))
    paths=list((REPO/'runners/next_round').glob('*.py'))+list((REPO/'runners/stage14_midweek').glob('*.py'))
    paths += [REPO/p for p in ('runners/stage14/common.py','runners/stage9/process_identity.py',
        'runners/stage9/coauthor.py','runners/stage9/common.py','tests/test_next_round.py',
        'docs/design/stage-15/PHASE0_PROTOCOL.md','docs/design/stage-15/IMPLEMENTATION_REVIEW.md',
        'docs/design/stage-15/SOUNDING_LINE_NEXT_ROUND_SPEC_2026-10-14.md')]
    paths+=list(prepared.glob('*.json'))+list((BASE/'modal-analysis-v2').glob('*.json'))
    paths+=list((BASE/'baselines-v1').glob('*.json'))+list((BASE/'data-v2').glob('*.json'))
    # Progress files are mutable and are not scientific inputs.
    paths=[p for p in paths if p.name!='PROGRESS.json']
    bindings=pins(paths); bindings.update(source_pins)
    freeze(ROOT/'PLAN.json',dict(schema=1,at=now(),tasks=['T0c','T0b','T0a'],pins=bindings,
        deadline_epoch=DEADLINE,max_wall_seconds=18*3600,gear=2,network_calls=0,provider_spend_cents=0,
        source_order_reason='Long prequential replay first, then saved-reader calibration and variance decomposition.',
        engine_admission=False))
    print('Phase 0 plan frozen with complete input/source bindings; no scientific cell executed.')


def run():
    limits(); plan=read(ROOT/'PLAN.json'); check_pins(plan['pins'])
    if time.time()>=plan['deadline_epoch']: raise ValueError('reporting reserve already started')
    require_resources(resource_snapshot())
    # Atomic exclusive claim: durable after crashes, no stale-lock reclamation.
    with (ROOT/'ATTEMPT.claim').open('x',encoding='utf8') as f: f.write(now()+'\n')
    started=time.time(); current={'task':'initializing'}
    freeze(ROOT/'OWNER.json',dict(at=now(),native=native_identity(),argv=sys.argv,plan_sha256=filehash(ROOT/'PLAN.json')))
    def guard(task, progress):
        current['task']=task
        snap=resource_snapshot(); require_resources(snap)
        if time.time()>=min(plan['deadline_epoch'],started+plan['max_wall_seconds']):
            raise TimeoutError('finite CPU allowance exhausted')
        atomic(ROOT/'PROGRESS.json',dict(at=now(),task=task,progress=progress,resources=snap))
    def deadline_guard():
        delay=max(0,min(plan['deadline_epoch'],started+plan['max_wall_seconds'])-time.time())
        # Cheap worker timer, not an agent polling loop or scheduled publication.
        if stop.wait(delay): return
        atomic(ROOT/'FAILED.json',dict(status='FAILED',at=now(),task=current['task'],reason='hard finite deadline'))
        os._exit(124)
    stop=threading.Event(); threading.Thread(target=deadline_guard,daemon=True).start()
    try:
        from .phase0 import TASKS
        for task in plan['tasks']:
            guard(task,dict(phase='starting')); folder=ROOT/task; folder.mkdir(exist_ok=False)
            check_pins(plan['pins'])
            kwargs={'prepared':ROOT/'prepared'} if task=='T0c' else {}
            TASKS[task](folder,guard,**kwargs)
            check_pins(plan['pins'])
            outputs={p.relative_to(folder).as_posix():filehash(p) for p in folder.rglob('*.json')}
            freeze(folder/'COMPLETE.json',dict(status='COMPLETE',at=now(),outputs=outputs,
                plan_sha256=filehash(ROOT/'PLAN.json'),scientific_admission=False))
        freeze(ROOT/'COMPLETE.json',dict(status='COMPLETE',at=now(),wall_seconds=time.time()-started,
            outputs={f'{t}/COMPLETE.json':filehash(ROOT/t/'COMPLETE.json') for t in plan['tasks']},
            plan_sha256=filehash(ROOT/'PLAN.json'),inference_calls=0,provider_spend_cents=0,
            write_through_required=True,engine_admission=False))
    except BaseException as exc:
        freeze(ROOT/'FAILED.json',dict(status='FAILED',at=now(),task=current['task'],type=type(exc).__name__,
            error=str(exc),traceback=traceback.format_exc(),plan_sha256=filehash(ROOT/'PLAN.json')))
        raise
    finally: stop.set()


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('action',choices=['prepare','run'])
    args=parser.parse_args()
    prepare() if args.action=='prepare' else run()
