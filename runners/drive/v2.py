"""Whole saved-forecast decomposition; no model calls or refitting.

DESIGN CHECK: LESSONS 3-5. NULL: constant forecasts have zero resolution;
invalid replies retain loss one and cannot be normalized into successes.
ALTERNATIVE: known perfect forecasts have zero loss; exact raw decomposition
closes including covariance. Every arm retained, no selected winner or promotion.
"""
import os
for _n in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[_n]='1'
import argparse,threading,time,traceback
import numpy as np
from runners.stage14.common import REPO,read,freeze,atomic,pins,check_pins,filehash,now,limits
from runners.stage9.process_identity import native_identity
from runners.next_round.queue import resource_snapshot,require_resources
from runners.stage14_midweek.data import ACTIONS
from .statistics import half_brier,decomposition,cluster_interval

ROOT=REPO/'results/phase_2_4_stage_15/raw/drive-v2-v1'
PHASE=REPO/'results/phase_2_4_stage_15/raw/phase0-v1/T0c'
CAL=REPO/'results/phase_2_4_stage_15/raw/t0b-convergence-v2'
BASE=REPO/'results/gear3/G3-S14-MAKER-1/raw'

def source_files():
    out=[]
    for folder in [PHASE,CAL,BASE/'modal-analysis-v2']:
        terminal=read(folder/'COMPLETE.json');out.append(folder/'COMPLETE.json')
        for name,sha in terminal['outputs'].items():
            p=folder/name
            if filehash(p)!=sha:raise ValueError('saved output changed: '+name)
            out.append(p)
    return out+[BASE/'data-v2/EVALUATOR.json']

def analyze(p,y,groups,base,valid=None):
    p=np.asarray(p,float);y=np.asarray(y,int);valid=np.ones(len(y),bool) if valid is None else np.asarray(valid,bool)
    if len(valid)!=len(y):raise ValueError('validity denominator mismatch')
    losses=np.ones(len(y));result=dict(rows=len(y),invalid=int((~valid).sum()))
    if valid.any():
        losses[valid]=half_brier(p[valid],y[valid]);result['merged_deciles']=decomposition(p[valid],y[valid]);result['exact_vectors']=decomposition(p[valid],y[valid],True)
    else:result.update(merged_deciles=None,exact_vectors=None)
    result['system_half_brier']=float(losses.mean());result['gain_over_reference']=cluster_interval(half_brier(base,y)-losses,groups)
    return result

def prepare():
    if (ROOT/'PLAN.json').exists():raise ValueError('existing V2 attempt')
    paths=[REPO/p for p in ['runners/drive/v2.py','runners/drive/statistics.py','runners/stage14/common.py',
        'runners/stage14_midweek/data.py','runners/stage9/process_identity.py','runners/next_round/queue.py',
        'tests/test_drive_v2.py','docs/design/stage-15/drive/V2.md']]+source_files()
    freeze(ROOT/'PLAN.json',dict(at=now(),pins=pins(paths),max_wall_seconds=3600,max_resource_wait_seconds=21600,
        provider_calls=0,model_calls=0,scientific_admission=False))

def compute(guard):
    results={};rows=read(PHASE/'PREDICTIONS.json');y=[ACTIONS.index(r['truth']) for r in rows];groups=[r['writer'] for r in rows]
    pop=[r['probabilities']['B-pop'] for r in rows]
    for arm in ('B-pop','B-writer','B-mixlogit'):
        guard('phase0',arm);results['phase0/'+arm]=analyze([r['probabilities'][arm] for r in rows],y,groups,pop)
    source=read(BASE/'modal-analysis-v2/PREDICTIONS.json');rows=sorted([r for r in read(BASE/'data-v2/EVALUATOR.json') if not r['pilot']],key=lambda r:r['key'])
    keys=[r['key'] for r in rows]
    if set(keys)!=set(source) or len(set(keys))!=len(keys):raise ValueError('aligned reader cohort changed')
    y=[ACTIONS.index(r['handling']) for r in rows];groups=[r['writer'] for r in rows];base=[source[k]['B-mixlogit']['probabilities'] for k in keys]
    for arm in ('B-pop','B-writer','B-mixlogit','R27.H0','R27.H1','R27.H2','R27.H3'):
        guard('raw_reader',arm);p=[source[k][arm]['probabilities'] if source[k][arm]['valid'] else [.25]*4 for k in keys]
        results['reader/'+arm]=analyze(p,y,groups,base,[source[k][arm]['valid'] for k in keys])
    for arm,rr in read(CAL/'PREDICTIONS.json').items():
        lookup={r['key']:r for r in rr}
        if len(lookup)!=len(rr) or set(lookup)!=set(keys):raise ValueError('calibration cohort differs')
        for mode in ('corrected','stacked'):
            guard('calibrated_reader',arm+'.'+mode)
            results['reader/'+arm+'.'+mode]=analyze([lookup[k][mode] for k in keys],y,groups,base,
                [lookup[k]['raw_valid'] for k in keys] if mode=='corrected' else None)
    freeze(ROOT/'SUMMARY.json',dict(curve=results,primary='decomposition of every frozen forecast; no selected arm',
        corrections_iid_only=True,descriptive=True,scientific_admission=False))

def run():
    limits();plan=read(ROOT/'PLAN.json');check_pins(plan['pins']);require_resources(resource_snapshot())
    with (ROOT/'ATTEMPT.claim').open('x',encoding='utf8') as f:f.write(now()+'\n')
    freeze(ROOT/'OWNER.json',dict(at=now(),native=native_identity(),plan_sha256=filehash(ROOT/'PLAN.json')))
    start=time.time();stop=threading.Event();lease=REPO/'results/.cpu.lock';token=f'{os.getpid()} drive-v2-v1'.encode();owned=False
    def hard():
        if stop.wait(plan['max_wall_seconds']+plan['max_resource_wait_seconds']+90):return
        atomic(ROOT/'FAILED.json',dict(status='FAILED',at=now(),reason='hard finite ceiling'));os._exit(124)
    threading.Thread(target=hard,daemon=True).start()
    try:
        while not (ROOT/'MONITOR_READY.json').exists():
            if time.time()-start>90:raise TimeoutError('monitor handshake')
            time.sleep(.25)
        if read(ROOT/'MONITOR_READY.json')['owner_sha256']!=filehash(ROOT/'OWNER.json'):raise ValueError('monitor binding')
        while True:
            require_resources(resource_snapshot())
            try:
                fd=os.open(lease,os.O_WRONLY|os.O_CREAT|os.O_EXCL);os.write(fd,token);os.close(fd);owned=True;break
            except FileExistsError:
                atomic(ROOT/'PROGRESS.json',dict(at=now(),task='WAITING_CPU_LEASE'))
                if time.time()-start>plan['max_resource_wait_seconds']:raise TimeoutError('CPU resource wait')
                time.sleep(60)
        began=time.time();check_pins(plan['pins'])
        def guard(task,detail):
            require_resources(resource_snapshot())
            if time.time()-began>plan['max_wall_seconds']:raise TimeoutError('V2 compute ceiling')
            atomic(ROOT/'PROGRESS.json',dict(at=now(),task=task,detail=detail))
        compute(guard);check_pins(plan['pins'])
        freeze(ROOT/'COMPLETE.json',dict(status='COMPLETE',at=now(),outputs={p.name:filehash(p) for p in ROOT.glob('*.json') if p.name not in ('PROGRESS.json','MONITOR_READY.json')},write_through_required=True,scientific_admission=False))
    except BaseException as exc:
        freeze(ROOT/'FAILED.json',dict(status='FAILED',at=now(),reason=str(exc),traceback=traceback.format_exc()));raise
    finally:
        stop.set()
        if owned and lease.exists() and lease.read_bytes()==token:lease.unlink()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);a=p.parse_args();prepare() if a.action=='prepare' else run()
