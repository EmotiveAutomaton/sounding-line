"""Full WD1.h2 calibration of conditional reference and original contrast.

DESIGN CHECK: LESSONS3-5, CONTROLS1-7 read2026-11-04.
NULL/no recurring slope and criterion-only worlds must not become positive;
stable slopes must recover positive recurrence, reversed halves negative.
Support failures are retained, not converted to nulls. Complete30 worlds,
1000conditional references,2000paired writer draws, fresh full refits required.
"""
from pathlib import Path
from collections import Counter
import time
import numpy as np
from scipy.special import ndtr
from runners.stage14.common import read,filehash,digest,atomic
from .timing_p6 import write_equal
from . import week3_sdt_newton as old
from . import week4_wd1_conditioned_support as support

FAMILIES=('null','criterion','stable','reversed')


def correlations(values):
    a=np.asarray(values,float);center=a-a.mean(axis=1,keepdims=True)
    den=np.sqrt(np.sum(center[:,:,0]**2,axis=1)*np.sum(center[:,:,1]**2,axis=1))
    if np.any(den<1e-14):return None
    return np.sum(center[:,:,0]*center[:,:,1],axis=1)/den


def summarize(real,controls,draws,seed):
    # Same original arithmetic and RNG; vectorize independent reference rows.
    writers=sorted(real['profiles'])
    if len(writers)<4:return dict(state='unsupported',reason='fewer than four supported writers',writers=len(writers))
    if any(sorted(c['profiles'])!=writers for c in controls):
        return dict(state='invalid',reason='permutation changed supported writer population',writers=len(writers))
    def matrix(record,field):return np.array([[part[field] for part in record['profiles'][w]['halves']] for w in writers])
    values=matrix(real,'sensitivity');fake=np.array([matrix(c,'sensitivity') for c in controls])
    actual=old.correlation(values);null=correlations(fake)
    if actual is None or null is None:
        return dict(state='invalid',reason='constant sensitivity makes reliability undefined',writers=len(writers))
    rng=np.random.default_rng(seed+101);deltas=[]
    for _ in range(draws):
        ix=rng.integers(0,len(writers),len(writers));r=old.correlation(values[ix]);refs=correlations(fake[:,ix,:])
        if r is None or refs is None:return dict(state='invalid',reason='undefined paired bootstrap draw',writers=len(writers))
        deltas.append(r-float(np.mean(refs)))
    estimate=actual-float(null.mean());low,high=map(float,np.quantile(deltas,[.025,.975]))
    p=float((1+np.sum(null>=actual-1e-14))/(len(null)+1))
    state='positive' if low>0 and p<.05 else 'negative' if high<0 else 'marginal' if estimate>0 else 'null'
    if low>0 and p>=.05:state='unresolved'
    changes={}
    for field in ('criterion','sensitivity'):
        ds=[v['thirds'][1][field]-v['thirds'][0][field] for v in real['profiles'].values() if 'thirds' in v]
        changes[field]=dict(writers=len(ds),mean_last_minus_first=float(np.mean(ds)) if ds else None)
    return dict(state=state,writers=len(writers),sensitivity_reliability=actual,permutation_mean=float(null.mean()),
        permutation_95_interval=np.quantile(null,[.025,.975]).tolist(),permutation_p_one_sided=p,
        real_minus_permutation_mean=estimate,paired_writer_95_interval=[low,high],bootstrap_draws=draws,
        permutation_draws=len(null),criterion_reliability_secondary=old.correlation(matrix(real,'criterion')),
        session_thirds_secondary=changes,null_wording='not detected; sensitivity untested' if state=='null' else None)


def world(family,seed,writers=12,decisions=32):
    if family not in FAMILIES:raise ValueError('Unknown family')
    rng=np.random.default_rng(seed);sessions=[];records=[];vectors=[];truth=[]
    for w in range(writers):
        intercept=-1.2+2.4*w/(writers-1) if family=='criterion' else -.2
        slope=.35+1.3*w/(writers-1) if family in ('stable','reversed') else 1.
        for si in range(8):
            prompt=si%2;sid=f'w{w}:s{si}';start=si*10000+w;rows=[]
            current=2.-slope if family=='reversed' and prompt else slope
            for di in range(decisions if si<6 else 0):
                q=-2.5+5*di/(decisions-1)+rng.normal(0,.02);key=f'{sid}:{di}'
                probability=float(ndtr(intercept+current*q));accepted=rng.random()<probability
                rows.append(dict(key=key,writer=str(w),session=sid,prompt=str(prompt),session_time=start,
                    open_at=start+di*10+1,resolved_at=start+di*10+5,handling='accept' if accepted else 'dismiss',
                    document='fixed context',menu=['alpha','beta'],decision_index=di))
                offset=len(vectors);vectors.extend([[q,np.sin(q),1.],[q,.1,0.],[q,.2,1.]])
                records.append(dict(key=key,writer=str(w),session=sid,context=offset,options=[offset+1,offset+2],
                    cosine=[.2,.3],scalars=[[q,0,1,1],[q,1,0,1]]))
                truth.append(dict(key=key,slope=current,intercept=intercept,probability=probability))
            sessions.append(dict(writer=str(w),session=sid,prompt=str(prompt),timestamp=start,end_at=start+1000,rows=rows))
    return (*old.population_features(sessions,records,np.asarray(vectors)),truth)


def configuration(mode):
    if mode not in ('constructed','timing','full'):raise ValueError('Unknown mode')
    return dict(card='WD1.h2-calibration',mode=mode,seed=20261104,
        writers=6 if mode=='constructed' else 12,decisions=16 if mode=='constructed' else 32,
        permutation_draws=4 if mode=='constructed' else 10 if mode=='timing' else 1000,
        bootstrap_draws=20 if mode=='constructed' else 100 if mode=='timing' else 2000,
        pca_dimensions=16,maximum_proposals=2000)


def evaluate_world(output,family,seed,config,saving,progress):
    start=time.process_time();sessions,rows,scalar,embedding,truth=world(family,seed,config['writers'],config['decisions'])
    b=support.bank(sessions,config['permutation_draws'],config['maximum_proposals'],seed)
    setup=time.process_time()-start
    if not b['complete']:raise ValueError('Conditional calibration bank unavailable')
    write_equal(output/'BANK.json',b) if saving else _equal(output/'BANK.json',b)
    proof=dict(truth_sha256=digest(truth),metadata_sha256=b['metadata_sha256'],rows=len(rows),sessions=len(sessions))
    write_equal(output/'WORLD.json',proof) if saving else _equal(output/'WORLD.json',proof)
    records=[];timings=[]
    for number,assignment in enumerate([{}]+[a['assignment'] for a in b['accepted']]):
        path=output/'fits'/f'{number:04}.json';tick=time.process_time()
        if saving and path.exists():record=read(path)
        else:
            record=old.evaluate(sessions,rows,scalar,embedding,assignment,dict(seed=seed,pca_dimensions=config['pca_dimensions']))
            write_equal(path,record) if saving else _equal(path,record)
        timings.append(time.process_time()-tick);records.append(record);progress(number+1,len(b['accepted'])+1)
    tick=time.process_time();summary=summarize(records[0],records[1:],config['bootstrap_draws'],seed)
    elapsed=time.process_time()-tick
    result=dict(family=family,seed=seed,primary=summary,bank_sha256=digest(b),truth_sha256=digest(truth),
        fit_digests=[digest(r) for r in records],proposals=len(b['proposals']))
    write_equal(output/'RESULT.json',result) if saving else _equal(output/'RESULT.json',result)
    return result,dict(setup_cpu_seconds=setup,fit_cpu_seconds=timings,summary_cpu_seconds=elapsed)


def _equal(path,value):
    if digest(read(path))!=digest(value):raise ValueError('Complete calibration replay differs: '+str(path))


def gate(results):
    counts={f:dict(worlds=0,positive=0,negative=0,invalid=0) for f in FAMILIES}
    for r in results:
        c=counts[r['family']];c['worlds']+=1;state=r['primary']['state']
        c['positive']+=state=='positive';c['negative']+=state=='negative';c['invalid']+=state in ('invalid','unsupported')
    complete=[counts[f]['worlds'] for f in FAMILIES]==[10,10,5,5]
    passed=complete and not any(c['invalid'] for c in counts.values()) and all(counts[f]['positive']<=1 for f in ('null','criterion')) and counts['stable']['positive']>=4 and counts['reversed']['negative']>=4
    return dict(complete=complete,passes=passed,counts=counts)


def calculate(output,inputs,config,saving):
    if inputs or config!=configuration(config.get('mode')):raise ValueError('Frozen constructed contract required')
    output=Path(output);results=[];timings=[]
    for index,family in enumerate(FAMILIES):
        n=(10 if index<2 else 5) if config['mode']=='full' else 1
        for ordinal in range(n):
            seed=config['seed']+index*1000+ordinal;root=output/'worlds'/f'{family}-{seed}'
            def progress(done,total):
                if (output.parent/'STOP').exists() or (output/'YIELD_REQUEST.json').exists():raise InterruptedError('Calibration fit boundary yield')
                atomic(output/'PROGRESS.json',dict(phase=('execute-' if saving else 'verify-')+family,
                    worlds_completed=len(results),arms_done=done,arms_total=total))
            r,t=evaluate_world(root,family,seed,config,saving,progress);results.append(r);timings.append(t)
    report=dict(card=config['card'],mode=config['mode'],worlds=len(results),calibration=gate(results),
        results=results,scientific_admission=False,source_sha256=filehash(__file__))
    write_equal(output/'SUMMARY.json',report) if saving else _equal(output/'SUMMARY.json',report)
    return report,timings


def execute(output,inputs,config):
    Path(output).mkdir(parents=True,exist_ok=True);r,t=calculate(output,inputs,config,True)
    write_equal(Path(output)/'TIMING.json',t);return r


def verify(output,inputs,config):
    r,t=calculate(output,inputs,config,False);out=dict(verified=True,full_fresh_calibration_refit=True,verification_timing=t)
    if config['mode']=='timing':
        timings=read(Path(output)/'TIMING.json')+t
        setup=max(v['setup_cpu_seconds'] for v in timings)*200
        fit=max(max(v['fit_cpu_seconds']) for v in timings)*1001
        summary=max(v['summary_cpu_seconds'] for v in timings)*2000/config['bootstrap_draws']*1000/config['permutation_draws']
        forecast=dict(full_cpu_seconds=3*2*30*(setup+fit+summary),safety_factor=3,
            world_setup=setup,world_fits=fit,world_summary=summary,full_worlds=30,
            basis='Worst complete setup, fit and summary from both passes; both full phases, all banks and factor3')
        write_equal(Path(output)/'FORECAST.json',forecast);out['forecast']=forecast
    return out
