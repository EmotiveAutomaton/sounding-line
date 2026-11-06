"""Registered D7.s fixed-penalty duration curve.

DESIGN CHECK: LESSONS3-5/CONTROLS1-7 reread 2026-11-04. Constant NULL
must be exact zero; signed novelty predicts with either sign. Every penalty
passes complete null/nuisance/signed calibration before human admission.
Support changes, incomplete banks and altered dependencies refuse, never null.
"""
from pathlib import Path
from types import FunctionType
import time
import numpy as np
from threadpoolctl import threadpool_limits
from runners.stage14.common import read, filehash, digest, atomic
from . import week3_d7_models as m
from . import week4_d7_calibration as c
from . import week4_d7_human_h1 as h
from .timing_p6 import write_equal

PENALTIES=(.001,.01,.1)
KEYS=tuple(format(x,'.3g') for x in PENALTIES)


def checked(path,value,verifying=False):
    if verifying:
        if read(path)!=value:raise ValueError('Fresh record replay differs')
    else:write_equal(path,value)


def configuration(mode):
    if mode not in ('constructed','calibration-cost','calibration-full','human-cost','human-full'):
        raise ValueError('Unknown mode')
    return dict(card='D7.s',mode=mode,seed=20261026,penalties=list(PENALTIES),
                references=200 if mode.endswith('full') else 2,
                bootstrap_draws=20 if mode=='constructed' else 2000,
                calibration_seeds=10 if mode=='calibration-full' else 1,
                primary='duration/elapsed',no_descendants=True)


def compare(rows,labels=None):
    groups,reason=m.partition(rows)
    if reason:raise ValueError('Unsupported writer: '+reason)
    labels=m.label_array(rows) if labels is None else np.asarray(labels,float)
    if labels.shape!=(len(rows),2) or not np.isfinite(labels).all() or np.any(labels[:,0]<0) or not np.isin(labels[:,1],[0,1]).all():
        raise ValueError('Invalid label matrix')
    train,cal,test=groups;y=labels[:,0]
    wt=m.weights(rows,train);wc=m.weights(rows,cal);we=m.weights(rows,test)
    designs=[m.features(rows,train,'duration','elapsed',full,labels) for full in (False,True)]
    result={}
    for key,penalty in zip(KEYS,PENALTIES):
        predictions=[];fits=[]
        for x in designs:
            beta=m.fit(x[train],y[train],wt,penalty);pred=x[test]@beta
            predictions.append(pred)
            fits.append(dict(penalty=penalty,calibration_loss=float(wc@((x[cal]@beta-y[cal])**2)),coefficients=beta.tolist()))
        losses=[(p-y[test])**2 for p in predictions]
        result[key]=dict(response='duration',cost='elapsed',test_keys=[rows[i]['key'] for i in test],
            train_keys=[rows[i]['key'] for i in train],calibration_keys=[rows[i]['key'] for i in cal],
            test_truth=y[test].tolist(),predictions=[p.tolist() for p in predictions],fits=fits,
            losses=[float(we@a) for a in losses],gain=float(we@(losses[0]-losses[1])),weight=we.tolist())
    return result


def native_oracles(rows):
    actual=compare(rows)
    train,_,_=m.partition(rows)[0];labels=m.label_array(rows);wt=m.weights(rows,train)
    for key,penalty in zip(KEYS,PENALTIES):
        oracle=FunctionType(m.compare.__code__,dict(m.compare.__globals__,PENALTIES=(penalty,)),argdefs=m.compare.__defaults__)
        if actual[key]!=oracle(rows,'duration','elapsed'):raise ValueError('Original fixed-penalty parity failed')
        for full in (False,True):
            x=m.features(rows,train,'duration','elapsed',full,labels)[train]
            ridge=np.diag(np.sqrt(np.r_[0.,np.full(x.shape[1]-1,penalty)]))
            design=np.vstack((np.sqrt(wt)[:,None]*x,ridge))
            target=np.r_[np.sqrt(wt)*labels[train,0],np.zeros(x.shape[1])]
            beta=np.linalg.lstsq(design,target,rcond=None)[0]
            if not np.allclose(beta,actual[key]['fits'][int(full)]['coefficients'],rtol=0,atol=1e-10):
                raise ValueError('Independent least-squares oracle failed')
    return True


def fits(groups,reference=None,seed=20261026):
    result={};worst=0.
    for index,(writer,rows) in enumerate(sorted(groups.items())):
        began=time.process_time();labels=None if reference is None else c.joint_labels(rows,reference,seed,index)
        curve=compare(rows,labels)
        result[writer]={key:dict(gain=v['gain'],added_coefficient=v['fits'][1]['coefficients'][-1],full_fit_sha256=digest(v)) for key,v in curve.items()}
        worst=max(worst,time.process_time()-began)
    return result,worst


def summarize(real,joint,fake,draws,seed):
    # The original aggregator is reused with its single declared response/cost.
    original=FunctionType(c.summarize.__code__,dict(c.summarize.__globals__,SETTINGS=(('duration','elapsed'),)),argdefs=c.summarize.__defaults__)
    def select(bank,key):return {w:{c.PRIMARY:v[key]} for w,v in bank.items()}
    if not joint or len(joint)!=len(fake):raise ValueError('Complete paired reference families required')
    return {key:original(select(real,key),[select(b,key) for b in joint],[select(b,key) for b in fake],draws,seed)[c.PRIMARY] for key in KEYS}


def analyze(output,label,rows,assignments,config,verifying=False):
    output=Path(output);groups,excluded=c.support(rows)
    if excluded or len(assignments)!=config['references']:raise ValueError('Fixed complete support required')
    for a in assignments:
        other,bad=c.support(c.reassigned(rows,a['assignment']))
        if bad or sorted(other)!=sorted(groups):raise ValueError('Reference roster changed before fits')
    worst=0.
    def fitted(name,groups,reference=None):
        nonlocal worst
        if (output.parent/'STOP').exists() or (output/'YIELD_REQUEST.json').exists():raise InterruptedError('D7.s fitted-arm yield')
        path=output/(label+'-'+name+'.json')
        if path.exists() and not verifying:return read(path)
        value,t=fits(groups,reference,config['seed']);worst=max(worst,t)
        if verifying:
            if read(path)!=value:raise ValueError('Fresh fitted-arm replay differs')
        else:write_equal(path,value)
        return value
    real=fitted('real',groups);joint=[];fake=[]
    for index,a in enumerate(assignments):
        joint.append(fitted('joint-'+str(index),groups,index))
        other,_=c.support(c.reassigned(rows,a['assignment']));fake.append(fitted('fake-'+str(index),other))
        atomic(output/'PROGRESS.json',dict(phase='verify' if verifying else 'execute',label=label,references_done=index+1,references_total=len(assignments)))
    return dict(curve=summarize(real,joint,fake,config['bootstrap_draws'],config['seed']),writers=len(groups),
        observations=len(rows),joint_draws=len(joint),conditional_draws=len(fake),
        fit_bank_sha256=digest(dict(real=real,joint=joint,fake=fake))),worst


def assess(worlds):
    if len(worlds)!=30:return dict(state='not_applicable',passes=False)
    result={}
    for key in KEYS:
        adapted=[dict(label=w['label'],regime=w['regime'],dose=w['dose'],analysis=dict(state='complete',summaries={c.PRIMARY:w['analysis']['curve'][key]})) for w in worlds]
        result[key]=c.assess(adapted)
    return dict(state='complete',passes=all(v['passes'] for v in result.values()),penalties=result)


def forecast(times,calibration):
    setup=max(t['setup_cpu_seconds'] for t in times);fitting=max(t['fitting_cpu_seconds'] for t in times)
    worst=max(t['max_complete_writer_cpu_seconds'] for t in times)
    writers=12 if calibration else 38;worlds=30 if calibration else 1;prefix_worlds=3 if calibration else 1
    unit=6*(setup+worst*writers*401*worlds+60)
    whole=6*(setup+fitting*401*worlds/(5*prefix_worlds))
    byte_forecast=max(t['fitted_arm_bytes'] for t in times)*401*worlds/(5*prefix_worlds)+16*1024**2
    return dict(full_cpu_seconds=max(unit,whole),complete_writer_forecast=unit,whole_implementation_forecast=whole,
        projected_output_bytes=byte_forecast,both_passes=True,safety_factor=3,human_scored=False)


def human_source(inputs,full):
    extra={'calibration_completion','cost_completion'} if full else set()
    if set(inputs)!=h.SOURCE_KEYS|{'support_completion'}|extra:raise ValueError('Exact D7.s inputs required')
    base={k:v for k,v in inputs.items() if k not in extra}
    rows,assignments,excluded=h.source(base)
    if full:
        _,cal=h.authenticated(inputs['calibration_completion'],__name__,configuration('calibration-full'))
        if not cal['calibration']['passes']:raise ValueError('Complete calibration failed')
        costroot,_=h.authenticated(inputs['cost_completion'],__name__,configuration('human-cost'))
        if read(costroot/'PLAN.json')['inputs']!=base:raise ValueError('Cost used different source')
    return rows,assignments,excluded


def calculate(output,inputs,config,verifying=False):
    if config!=configuration(config.get('mode')):raise ValueError('Frozen D7.s configuration required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True);start=time.process_time()
    binding=dict(config=config,inputs={k:filehash(v) for k,v in inputs.items()})
    checked(output/'BINDING.json',binding,verifying)
    mode=config['mode'];tasks=[];exclusions={};worlds=[]
    if mode.startswith('human'):
        rows,assignments,exclusions=human_source(inputs,mode=='human-full')
        if mode=='human-cost':rows=h.generated(rows,config['seed']);assignments=h.cost_assignments(rows,assignments)
        tasks=[('human' if mode=='human-full' else 'generated',rows,assignments,None,None)]
    else:
        if inputs:raise ValueError('Constructed phases require no human inputs')
        for regime in ('null','nuisance','signed'):
            for index in range(config['calibration_seeds']):
                seed=config['seed']+index;rows,dose=c.world(regime,seed,6 if mode=='constructed' else 12,index)
                assignments=h.h.bank(rows,draws=config['references'],seed=seed)['accepted']
                if mode=='constructed':native_oracles(c.support(rows)[0][sorted(c.support(rows)[0])[0]])
                tasks.append((regime+'-'+str(seed),rows,assignments,regime,dose))
    setup=time.process_time()-start;results={};worst=0.
    for label,rows,assignments,regime,dose in tasks:
        cfg=dict(config,seed=config['seed'] if regime is None else int(label.rsplit('-',1)[1]))
        analysis,t=analyze(output,label,rows,assignments,cfg,verifying);worst=max(worst,t);results[label]=analysis
        if regime:worlds.append(dict(label=label,regime=regime,dose=dose,analysis=analysis))
    record=dict(results=results,worlds=worlds,original_exclusions=exclusions)
    checked(output/'PRIVATE_ANALYSIS.json',record,verifying)
    summary=dict(card='D7.s',mode=mode,complete=True,penalties=list(PENALTIES),human_scored=mode=='human-full',
        calibration=assess(worlds),analysis_sha256=filehash(output/'PRIVATE_ANALYSIS.json'),
        references_per_family=config['references'],bootstrap_draws=config['bootstrap_draws'],no_descendants=True,causal_claim=False)
    elapsed=time.process_time()-start
    arm_bytes=sum(p.stat().st_size for p in output.glob('*.json') if any(x in p.name for x in ('-real.','-joint-','-fake-')))
    timing_path=output/('VERIFY_TIMING.json' if verifying else 'EXECUTE_TIMING.json')
    if not timing_path.exists():write_equal(timing_path,dict(cpu_seconds=elapsed,setup_cpu_seconds=setup,fitting_cpu_seconds=elapsed-setup,max_complete_writer_cpu_seconds=worst,fitted_arm_bytes=arm_bytes))
    checked(output/'SUMMARY.json',summary,verifying)
    if verifying and mode.endswith('cost'):
        write_equal(output/'FORECAST.json',forecast([read(output/n) for n in ('EXECUTE_TIMING.json','VERIFY_TIMING.json')],mode.startswith('calibration')))
    return dict(verified=True,full_fresh_fit_replay=True) if verifying else summary


def execute(output,inputs,config):
    with threadpool_limits(limits=1):return calculate(output,inputs,config)


def verify(output,inputs,config):
    with threadpool_limits(limits=1):return calculate(output,inputs,config,True)
