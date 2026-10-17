"""Finite target-matched outcome plasmodes through the unchanged Phase 0 fit.

DESIGN CHECK: LESSONS 3-5. NULL: zero injection exactly preserves generating
probabilities, future labels cannot enter lags, natural labels cannot alter
simulated worlds. ALTERNATIVE: assigned positive logit offsets increase accept
probability. Complete fixed grid, original fit, no scientific engine admission.
"""
import os
for _n in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[_n]='1'
import argparse,copy,heapq,re,threading,time,traceback,sys,importlib.metadata
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.special import softmax
from runners.stage14.common import REPO,read,freeze,atomic,pins,check_pins,filehash,now,limits
from runners.stage9.process_identity import native_identity
from runners.next_round.queue import resource_snapshot,require_resources
from runners.next_round.phase0 import prequential_session
from runners.stage14_midweek.baselines import matrix
from runners.stage14_midweek.data import ACTIONS
from .statistics import half_brier,cluster_interval

ROOT=REPO/'results/phase_2_4_stage_15/raw/drive-v1-phase0-v1'
PHASE=REPO/'results/phase_2_4_stage_15/raw/phase0-v1'
PRIORITY=REPO/'results/phase_2_4_stage_15/raw/drive-v2-v1'
GRID=[dict(effect=e,delta=d,replicate=r,seed=161016+i*1000+j*10+r) for i,e in enumerate(('offset','content','habit')) for j,d in enumerate((0.,.1,.2,.4,.8)) for r in range(10)]

def runtime():return dict(python=sys.version,packages={p:importlib.metadata.version(p) for p in ('numpy','scipy','scikit-learn')})

def wilson(k,n):
    if n<1 or not 0<=k<=n:raise ValueError('invalid recovery denominator')
    z=1.959963984540054;p=k/n;center=(p+z*z/(2*n))/(1+z*z/n)
    radius=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
    return [float(center-radius),float(center+radius)]

def content_covariates(sessions):
    words=lambda text:set(re.findall(r'\w+',text.lower()))
    tokens={s['session']:words(max(s['rows'],key=lambda r:(r['open_at'],r['key']))['document']) for s in sessions if s['rows']}
    result={};writers=defaultdict(list)
    for s in sessions:
        history=set()
        for p in sessions:
            if p['writer']==s['writer'] and p['prompt']!=s['prompt'] and p['end_at']<s['timestamp']:
                history.update(tokens.get(p['session'],set()))
        for row in s['rows']:
            scores=[]
            for text in row['menu']:
                w=words(text);scores.append(len(w&history)/max(1,len(w|history)))
            result[row['key']]=max(scores,default=0.);writers[s['writer']].append(row['key'])
    for keys in writers.values():
        x=np.array([result[k] for k in keys]);sd=x.std()
        for k,v in zip(keys,x):result[k]=float((v-x.mean())/sd) if sd>0 else 0.
    return result

def construct(sessions,base,content,effect,delta,seed):
    if effect not in ('offset','content','habit') or delta<0:raise ValueError('undeclared construction')
    ss=copy.deepcopy(sessions);rows=sorted([r for s in ss for r in s['rows']],key=lambda r:(r['open_at'],r['key']))
    if len({r['key'] for r in rows})!=len(rows) or set(base)!={r['key'] for r in rows}:raise ValueError('base support mismatch')
    rng=np.random.default_rng(seed);writers=sorted({r['writer'] for r in rows});active=set(rng.choice(writers,len(writers)//2,replace=False).tolist())
    signs={w:int(rng.choice([-1,1])) for w in writers};history=defaultdict(list);pending=[];generating={};trace=[]
    for row in rows:
        if row['resolved_at']<row['open_at']:raise ValueError('negative source duration')
        while pending and pending[0][0]<=row['open_at']:
            resolved,key,w,label=heapq.heappop(pending);history[w].append((resolved,key,label))
        past=history[row['writer']];row['previous_handling']=past[-1][2] if past else None
        factor=1. if effect=='offset' else content[row['key']]*signs[row['writer']] if effect=='content' else (np.mean([v[2]=='accept' for v in past[-3:]])-.5 if past else 0.)
        p=np.asarray(base[row['key']],float)
        if len(p)!=4 or not np.isfinite(p).all() or (p<=0).any() or not np.isclose(p.sum(),1,atol=1e-12,rtol=0):raise ValueError('invalid generating base')
        shift=delta*factor if row['writer'] in active else 0.
        q=p.copy() if shift==0 else softmax(np.log(p)+np.array([shift,0,0,0]))
        row['handling']=ACTIONS[int(rng.choice(4,p=q))];generating[row['key']]=q.tolist()
        heapq.heappush(pending,(row['resolved_at'],row['key'],row['writer'],row['handling']))
        trace.append(dict(key=row['key'],previous_handling=row['previous_handling'],truth=row['handling'],generating=q.tolist(),shift=float(shift)))
    return ss,generating,trace

def fit_world(sessions,guard):
    rows=sorted([r for s in sessions for r in s['rows']],key=lambda r:(r['open_at'],r['key']));index={r['key']:i for i,r in enumerate(rows)}
    x=matrix(rows,False);predictions=[];fits=[]
    for i,s in enumerate(sorted(sessions,key=lambda s:(s['timestamp'],s['session']))):
        guard(i,len(sessions))
        if s['rows']:
            p,f=prequential_session(sessions,s,x,index);predictions.extend(p);fits.append(f)
    if len(predictions)!=len(rows):raise ValueError('fitted support mismatch')
    return predictions,fits

def score_world(predictions,truth,base):
    rows=sorted(predictions,key=lambda r:r['key']);keys=[r['key'] for r in rows];y=[ACTIONS.index(r['truth']) for r in rows]
    p=np.array([r['probabilities']['B-pop'] for r in rows]);q=np.array([r['probabilities']['B-mixlogit'] for r in rows]);g=np.array([truth[k] for k in keys]);b=np.array([base[k] for k in keys])
    observed=half_brier(p,y)-half_brier(q,y);ci=cluster_interval(observed,[r['writer'] for r in rows])
    expected=float(np.mean(.5*np.sum((p-g)**2-(q-g)**2,axis=1)))
    return dict(rows=len(rows),gain=ci,recovered=bool(ci['interval95'][0]>0),oracle_injected_gain=float(.5*np.mean(np.sum((g-b)**2,axis=1))),
        fitted_conditional_expected_gain=expected,interval_covers_conditional_target=bool(ci['interval95'][0]<=expected<=ci['interval95'][1]),observed_minus_expected=ci['estimate']-expected)

def prepare():
    if (ROOT/'PLAN.json').exists():raise ValueError('existing V1 attempt')
    source=read(PHASE/'T0c/COMPLETE.json')
    for name in ('PREDICTIONS.json','FITS.json'):
        if filehash(PHASE/'T0c'/name)!=source['outputs'][name]:raise ValueError('changed Phase 0 source')
    old=read(PHASE/'PLAN.json');src=PHASE/'prepared/SESSIONS.json'
    if old['pins'][src.relative_to(REPO).as_posix()]!=filehash(src):raise ValueError('changed source sessions')
    paths=[REPO/p for p in ('runners/drive/v1_phase0.py','runners/drive/statistics.py','runners/next_round/phase0.py','runners/next_round/statistics.py',
        'runners/next_round/queue.py','runners/stage14_midweek/baselines.py','runners/stage14_midweek/data.py','runners/stage14_midweek/analyze_modal.py',
        'runners/stage14/common.py','runners/stage9/process_identity.py','tests/test_drive_v1.py','docs/design/stage-15/drive/V1_PHASE0.md')]+[src,PHASE/'T0c/COMPLETE.json',PHASE/'T0c/PREDICTIONS.json']
    freeze(ROOT/'PLAN.json',dict(at=now(),pins=pins(paths),grid=GRID,max_wall_seconds=20*3600,max_resource_wait_seconds=12*3600,max_output_bytes=10*1024**3,
        runtime=runtime(),provider_calls=0,model_calls=0,scientific_admission=False,whole_grid_required=True))

def compute(plan,guard):
    sessions=read(PHASE/'prepared/SESSIONS.json');base={r['key']:r['probabilities']['B-pop'] for r in read(PHASE/'T0c/PREDICTIONS.json')};covariates=content_covariates(sessions)
    freeze(ROOT/'COVARIATES.json',covariates);results=[]
    for i,cell in enumerate(plan['grid']):
        guard(dict(world=i,worlds=len(plan['grid']),phase='construct'))
        generated,g,trace=construct(sessions,base,covariates,**cell_without_replicate(cell));folder=ROOT/'worlds'/f'{i:03d}';freeze(folder/'CONSTRUCTION.json',dict(cell=cell,rows=trace))
        predictions,fits=fit_world(generated,lambda n,total:guard(dict(world=i,worlds=len(plan['grid']),sessions=n,total_sessions=total)))
        freeze(folder/'PREDICTIONS.json',predictions);freeze(folder/'FITS.json',fits)
        result=dict(cell=cell,**score_world(predictions,g,base));freeze(folder/'RESULT.json',result);results.append(result)
    recovery=[]
    for effect in sorted({r['cell']['effect'] for r in results}):
        for delta in sorted({r['cell']['delta'] for r in results if r['cell']['effect']==effect}):
            rr=[r for r in results if r['cell']['effect']==effect and r['cell']['delta']==delta];k=sum(r['recovered'] for r in rr)
            recovery.append(dict(effect=effect,delta=delta,recovered=k,worlds=len(rr),rate=k/len(rr),wilson95=wilson(k,len(rr)),
                conditional_interval_coverage=sum(r['interval_covers_conditional_target'] for r in rr)/len(rr),
                observed_minus_expected_quantiles=np.quantile([r['observed_minus_expected'] for r in rr],[.025,.5,.975]).tolist()))
    freeze(ROOT/'SUMMARY.json',dict(curve=results,recovery=recovery,all_worlds_complete=True,other_V1_arms_run=False,scientific_admission=False))

def cell_without_replicate(cell):return {k:v for k,v in cell.items() if k!='replicate'}

def run():
    limits();plan=read(ROOT/'PLAN.json');check_pins(plan['pins']);require_resources(resource_snapshot())
    if runtime()!=plan['runtime']:raise ValueError('runtime identity changed')
    with (ROOT/'ATTEMPT.claim').open('x',encoding='utf8') as f:f.write(now()+'\n')
    freeze(ROOT/'OWNER.json',dict(at=now(),native=native_identity(),plan_sha256=filehash(ROOT/'PLAN.json')))
    start=time.time();stop=threading.Event();lease=REPO/'results/.cpu.lock';token=f'{os.getpid()} drive-v1-phase0-v1'.encode();owned=False
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
            prior_finished=any((PRIORITY/n).is_file() for n in ('COMPLETE.json','FAILED.json','MONITOR_FAILED.json'))
            if prior_finished:
                try:
                    fd=os.open(lease,os.O_WRONLY|os.O_CREAT|os.O_EXCL);os.write(fd,token);os.close(fd);owned=True;break
                except FileExistsError:pass
            atomic(ROOT/'PROGRESS.json',dict(at=now(),task='WAITING_CPU_ORDER',prior_finished=prior_finished))
            if time.time()-start>plan['max_resource_wait_seconds']:raise TimeoutError('CPU resource wait')
            time.sleep(60)
        began=time.time();check_pins(plan['pins']);last_size=began
        def guard(progress):
            nonlocal last_size
            require_resources(resource_snapshot())
            if time.time()-began>plan['max_wall_seconds']:raise TimeoutError('finite V1 computation ceiling')
            if time.time()-last_size>60:
                if sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())>plan['max_output_bytes']:raise RuntimeError('output byte ceiling')
                last_size=time.time()
            atomic(ROOT/'PROGRESS.json',dict(at=now(),task='plasmode',progress=progress))
        compute(plan,guard);check_pins(plan['pins'])
        freeze(ROOT/'COMPLETE.json',dict(status='COMPLETE',at=now(),outputs={p.relative_to(ROOT).as_posix():filehash(p) for p in ROOT.rglob('*.json') if p.name not in ('PROGRESS.json','MONITOR_READY.json')},write_through_required=True,scientific_admission=False))
    except BaseException as exc:
        freeze(ROOT/'FAILED.json',dict(status='FAILED',at=now(),reason=str(exc),traceback=traceback.format_exc()));raise
    finally:
        stop.set()
        if owned and lease.exists() and lease.read_bytes()==token:lease.unlink()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);a=p.parse_args();prepare() if a.action=='prepare' else run()
