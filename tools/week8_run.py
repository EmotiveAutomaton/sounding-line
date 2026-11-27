"""Run a reviewed local Week 8 unit and its replay in measured Windows jobs.

DESIGN CHECK (LESSONS §§3–5). A changed input or an unqualified fixture refuses
before outcomes. Budget, resource and drain stops retain the last checkpoint.
"""
import argparse
from datetime import datetime, timezone
import importlib
import os
from pathlib import Path
import sys
import time

for variable in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[variable] = '2'
os.environ['CUDA_VISIBLE_DEVICES'] = ''
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from runners.drive.cards import week8_gear as gear
from runners.drive.cards.batch_runtime_v8 import measured_child, job_cpu
from runners.stage14.common import read, freeze, atomic, filehash, now
from runners.stage9.process_identity import native_identity

STATE = ROOT/'.agent-state/drive-20261127/week8'
SPEC = ROOT/'docs/design/stage-15/week8'
MODULES = {name:'week8_'+name.lower() for name in gear.CARDS}


def study(name):
    return importlib.import_module('runners.drive.cards.'+MODULES[name])


def capacity(cap, peak):
    mem = gear.resource_snapshot()
    return (mem['disk_free_GiB'] >= 20 and mem['ram_available_GiB'] >= 6
            and mem['commit_headroom_GiB'] >= 8 and peak + 8 <= min(mem['ram_available_GiB'],mem['commit_headroom_GiB']))


def qualify(card, unit):
    mod = study(card)
    info = mod.design(unit)
    pins = {str(p):filehash(p) for p in [*info['inputs'], Path(mod.__file__), Path(__file__).resolve(),
            Path(gear.__file__), gear.AUTHORITY]}
    for path, expected in info.get('expected',{}).items():
        if pins.get(str(path)) != expected:
            raise ValueError('Existing reviewed input changed: '+str(path))
    proof = mod.fixture()
    review = dict(card=card,unit=unit,source=info['source'],peak=info['peak'],cap=info['cap'],
                  operations=info['operations'],pins=pins,fixture=proof)
    path = STATE/'reviews'/(unit+'.json')
    path.parent.mkdir(exist_ok=True,parents=True)
    freeze(path,review)
    print(card,unit,'qualified',filehash(path))


def dispatch(card, unit, attempt):
    review_path = STATE/'reviews'/(unit+'.json')
    review = read(review_path)
    if review['card']!=card or review['unit']!=unit:
        raise ValueError('Wrong study review')
    pins = {**review['pins'],str(review_path):filehash(review_path)}
    d = gear.ROOT/attempt
    cap = review['cap']
    with gear.admit(d,card=card,source=review['source'],requested=cap,peak=review['peak'],sealed=False,pins=pins):
        used = 0.
        try:
            freeze(d/'LOCAL_REVIEW.json', review)
            for mode in review['operations']:
                args=[sys.executable,'-B',str(Path(__file__).resolve()),card,unit,mode,'--attempt',attempt]
                with measured_child(d,mode,args) as worker:
                    freeze(d/(mode+'_CHILD.json'),dict(native=native_identity(worker.pid),at=now()))
                    while worker.poll() is None:
                        current=job_cpu(worker)
                        if used+current+12>=cap or datetime.now(timezone.utc)>=gear.DRAIN:
                            raise TimeoutError('Row allowance or campaign drain')
                        resources=gear.resource_snapshot()
                        if resources['ram_available_GiB']<4 or resources['commit_headroom_GiB']<6 or resources['disk_free_GiB']<20:
                            raise RuntimeError('Shared resource floor')
                        atomic(d/'PROGRESS.json',dict(at=now(),operation=mode,charged_cpu_seconds=used+current))
                        time.sleep(2)
                    if worker.poll()!=0:
                        raise RuntimeError(mode+' exit '+str(worker.poll()))
                used+=read(d/(mode.upper()+'_JOB_USAGE.json'))['cpu_seconds']
            if used>cap:
                raise RuntimeError('Final metered use exceeded cap')
            mod=study(card)
            files=mod.check(unit,d)
            gear.settle(d,used,'Measured Windows jobs including all descendants and replay')
            freeze(d/'COMPLETE.json',dict(at=now(),card=card,unit=unit,verified=True,results=files,review_sha256=filehash(review_path)))
        except BaseException as exc:
            if not (d/'COST.json').exists():
                measured=sum(read(p)['cpu_seconds'] for p in d.glob('*_JOB_USAGE.json'))
                if measured<=cap:
                    gear.settle(d,measured,'Measured jobs through failure')
            freeze(d/'FAILED.json',dict(at=now(),card=card,unit=unit,reason=str(exc)))
            raise


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('card',choices=MODULES)
    parser.add_argument('unit')
    parser.add_argument('mode',choices=['qualify','dispatch','execute','verify'])
    parser.add_argument('--attempt')
    args=parser.parse_args()
    for name in [args.unit,args.attempt or args.unit]:
        if not name or not all(c.isascii() and (c.isalnum() or c in '-_') for c in name):
            raise ValueError('Invalid unit or attempt')
    attempt=args.attempt or args.unit
    if args.mode=='qualify':
        qualify(args.card,args.unit)
    elif args.mode=='dispatch':
        dispatch(args.card,args.unit,attempt)
    else:
        d=gear.ROOT/attempt
        local=read(d/'LOCAL_REVIEW.json')
        if local['card']!=args.card or local['unit']!=args.unit or args.mode not in local['operations']:
            raise ValueError('Unreviewed child operation')
        study(args.card).run(args.unit,d,args.mode)

if __name__=='__main__':
    main()
