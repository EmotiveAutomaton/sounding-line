"""D7.m registered descriptive temporal stability of the novelty coefficient.

DESIGN CHECK: LESSONS3-5/CONTROLS1-7 reread 2026-11-04. Identical-design
stationarity yields zero drift; signed late changes must reverse correctly.
Both coefficient fits have independent least-squares oracles. Test outcomes
cannot change training transforms or penalty selection. No missing-bank salvage.
"""
from pathlib import Path
import math,time
import numpy as np
from threadpoolctl import threadpool_limits
from runners.stage14.common import read,filehash,digest,atomic
from . import week3_d7_models as m
from . import week4_d7_calibration as c
from . import week4_d7_human_h1 as h
from . import week4_d7_specification as s
from .timing_p6 import write_equal


def configuration(mode):
    v=s.configuration(mode)
    v.update(card='D7.m',primary='later-minus-earlier-novelty-coefficient')
    return v


def compare(rows,labels=None):
    groups,reason=m.partition(rows)
    if reason:raise ValueError('Unsupported writer: '+reason)
    labels=m.label_array(rows) if labels is None else np.asarray(labels,float)
    if labels.shape!=(len(rows),2) or not np.isfinite(labels).all() or np.any(labels[:,0]<0) or not np.isin(labels[:,1],[0,1]).all():
        raise ValueError('Invalid label matrix')
    train,cal,test=groups;y=labels[:,0]
    wt,wc,we=(m.weights(rows,ids) for ids in groups)
    x=m.features(rows,train,'duration','elapsed',True,labels)
    candidates=[]
    for penalty in m.PENALTIES:
        beta=m.fit(x[train],y[train],wt,penalty)
        candidates.append((float(wc@((x[cal]@beta-y[cal])**2)),penalty,beta))
    loss,penalty,early=min(candidates,key=lambda t:(t[0],t[1]))
    late=m.fit(x[test],y[test],we,penalty)
    return dict(train_keys=[rows[i]['key'] for i in train],calibration_keys=[rows[i]['key'] for i in cal],
        test_keys=[rows[i]['key'] for i in test],penalty=penalty,calibration_loss=loss,
        training_coefficients=early.tolist(),later_coefficients=late.tolist(),
        earlier=float(early[-1]),later=float(late[-1]),delta=float(late[-1]-early[-1]))


def native_oracles(rows):
    v=compare(rows);original=m.compare(rows,'duration','elapsed')['fits'][1]
    if v['training_coefficients']!=original['coefficients'] or v['penalty']!=original['penalty'] or v['calibration_loss']!=original['calibration_loss']:
        raise ValueError('Original augmented fit parity failed')
    groups,_=m.partition(rows);labels=m.label_array(rows)
    x=m.features(rows,groups[0],'duration','elapsed',True,labels)
    for ids,key in ((groups[0],'training_coefficients'),(groups[2],'later_coefficients')):
        weights=m.weights(rows,ids);ridge=np.diag(np.sqrt(np.r_[0.,np.full(x.shape[1]-1,v['penalty'])]))
        beta=np.linalg.lstsq(np.vstack((np.sqrt(weights)[:,None]*x[ids],ridge)),
            np.r_[np.sqrt(weights)*labels[ids,0],np.zeros(x.shape[1])],rcond=None)[0]
        if not np.allclose(beta,v[key],rtol=0,atol=1e-10):raise ValueError('Independent least-squares oracle failed')
    return True


def world(regime,seed,writers=12,ordinal=0):
    if regime not in ('null','nuisance','signed'):raise ValueError('Unknown regime')
    shift=0. if regime!='signed' else (.8 if ordinal%2==0 else -.8)
    source=m.world(seed=seed,writers=writers);rows=[]
    for wi,(writer,rr) in enumerate(m.writers(source).items()):
        template=[r for r in rr if r['session']==rr[0]['session']]
        slope=-.8+1.6*wi/(writers-1)
        for session in range(10):
            for j,r in enumerate(template):
                start=session*100000+wi*1000;v=dict(r,key=f'{writer}:{session}:{j}',session=f'{writer}:{session}',
                    prompt='0',session_start=start,session_end=start+900,open_at=start+j*10)
                if regime=='nuisance':
                    v['mean_novelty']=.15+.7*j/11
                    logtime=2+.3*float(v['accepted'])+.45*math.log1p(v['elapsed_seconds'])
                else:logtime=2+.3*float(v['accepted'])+(slope+(shift if session>=8 else 0))*(v['mean_novelty']-.5)
                v['dwell_seconds']=math.expm1(logtime);rows.append(v)
    return rows,shift


def fits(groups,reference=None,seed=20261026):
    result={};worst=0.
    for index,(writer,rows) in enumerate(sorted(groups.items())):
        began=time.process_time();labels=None if reference is None else c.joint_labels(rows,reference,seed,index)
        v=compare(rows,labels)
        result[writer]={k:v[k] for k in ('earlier','later','delta')}
        result[writer]['full_fit_sha256']=digest(v)
        worst=max(worst,time.process_time()-began)
    return result,worst


def correlation(a,b):
    a=np.asarray(a,float);b=np.asarray(b,float)
    if not np.isfinite(a).all() or not np.isfinite(b).all():raise ValueError('Nonfinite coefficients')
    if len(a)<3 or a.shape!=b.shape or np.ptp(a)==0 or np.ptp(b)==0:return None
    return float(np.corrcoef(a,b)[0,1])


def summarize(real,joint,fake,draws,seed):
    writers=sorted(real)
    if len(writers)<3 or not joint or len(joint)!=len(fake) or any(sorted(b)!=writers for b in joint+fake):
        raise ValueError('Complete paired reference roster required')
    arrays=[np.array([real[w][k] for w in writers]) for k in ('earlier','later','delta')]
    if not all(np.isfinite(a).all() for a in arrays):raise ValueError('Nonfinite coefficients')
    early,late,delta=arrays;point=float(delta.mean())
    indices=np.random.default_rng(seed).integers(0,len(writers),size=(draws,len(writers)))
    lo,hi=np.quantile(delta[indices].mean(1),[.025,.975])
    corr=correlation(early,late);boot=[correlation(early[i],late[i]) for i in indices]
    undefined=sum(v is None for v in boot)
    interval=None if undefined else [float(x) for x in np.quantile(boot,[.025,.975])]
    null=[float(np.mean([b[w]['delta'] for w in writers])) for b in joint]
    other=[float(np.mean([b[w]['delta'] for w in writers])) for b in fake]
    if not np.isfinite(null+other).all():raise ValueError('Nonfinite reference')
    tail=(1+sum(abs(v)>=abs(point) for v in null))/(len(null)+1);bias=abs(float(np.mean(null)))>.005
    return dict(delta=point,ci_low=float(lo),ci_high=float(hi),writers=len(writers),bootstrap_draws=draws,
        mean_earlier=float(early.mean()),mean_later=float(late.mean()),correlation=corr,
        correlation_interval=interval,correlation_undefined_resamples=undefined,
        joint_permutation=dict(attempted=len(null),invalid=0,mean=float(np.mean(null)),two_sided_p=tail,bias_flag=bias),
        fake_writer=dict(attempted=len(other),invalid=0,mean=float(np.mean(other)),scope='Population association may survive; not a personal-signal null'),
        directional_call=bool((lo>0 or hi<0) and tail<=.05 and not bias))


def analyze(output,label,rows,assignments,config,verifying=False):
    output=Path(output);groups,excluded=c.support(rows)
    if excluded or len(assignments)!=config['references']:raise ValueError('Fixed complete support required')
    for a in assignments:
        other,bad=c.support(c.reassigned(rows,a['assignment']))
        if bad or sorted(other)!=sorted(groups):raise ValueError('Reference roster changed before fits')
    worst=0.
    def fitted(name,group,reference=None):
        nonlocal worst
        if (output.parent/'STOP').exists() or (output/'YIELD_REQUEST.json').exists():raise InterruptedError('D7.m fitted-arm yield')
        path=output/(label+'-'+name+'.json')
        if path.exists() and not verifying:return read(path)
        value,t=fits(group,reference,config['seed']);worst=max(worst,t)
        s.checked(path,value,verifying);return value
    real=fitted('real',groups);joint=[];fake=[]
    for index,a in enumerate(assignments):
        joint.append(fitted('joint-'+str(index),groups,index))
        other,_=c.support(c.reassigned(rows,a['assignment']));fake.append(fitted('fake-'+str(index),other))
        atomic(output/'PROGRESS.json',dict(phase='verify' if verifying else 'execute',label=label,references_done=index+1,references_total=len(assignments)))
    return dict(summary=summarize(real,joint,fake,config['bootstrap_draws'],config['seed']),writers=len(groups),
        observations=len(rows),joint_draws=len(joint),conditional_draws=len(fake),
        fit_bank_sha256=digest(dict(real=real,joint=joint,fake=fake))),worst


def assess(worlds):
    if len(worlds)!=30:return dict(state='not_applicable',passes=False)
    counts={};stable=True;signed=True
    for regime in ('null','nuisance','positive','negative'):
        group=[w for w in worlds if (w['regime']==regime if w['dose']==0 else ('positive' if w['dose']>0 else 'negative')==regime)]
        expected=10 if regime in ('null','nuisance') else 5
        if len(group)!=expected:raise ValueError('Incomplete calibration regime')
        calls=sum(w['analysis']['summary']['directional_call'] for w in group)
        counts[regime]=dict(worlds=len(group),directional_calls=calls)
        if regime in ('null','nuisance'):
            stable &= calls<=1 and all(abs(w['analysis']['summary']['delta'])<1e-10 for w in group)
        else:
            good=sum(w['analysis']['summary']['directional_call'] and w['analysis']['summary']['delta']*w['dose']>0 for w in group)
            counts[regime]['correct_direction_calls']=good;signed &= good>=4
    return dict(state='complete',passes=bool(stable and signed),counts=counts,stationarity_exact=bool(stable),scope='Algebraic repeated-design calibration; no empirical human power')


def human_source(inputs,full):
    extra={'calibration_completion','cost_completion'} if full else set()
    if set(inputs)!=h.SOURCE_KEYS|{'support_completion'}|extra:raise ValueError('Exact D7.m inputs required')
    base={k:v for k,v in inputs.items() if k not in extra};rows,assignments,excluded=h.source(base)
    if full:
        _,cal=h.authenticated(inputs['calibration_completion'],__name__,configuration('calibration-full'))
        if not cal['calibration']['passes']:raise ValueError('Complete calibration failed')
        costroot,_=h.authenticated(inputs['cost_completion'],__name__,configuration('human-cost'))
        if read(costroot/'PLAN.json')['inputs']!=base:raise ValueError('Cost used different source')
    return rows,assignments,excluded


def calculate(output,inputs,config,verifying=False):
    if config!=configuration(config.get('mode')):raise ValueError('Frozen D7.m configuration required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True);start=time.process_time()
    s.checked(output/'BINDING.json',dict(config=config,inputs={k:filehash(v) for k,v in inputs.items()}),verifying)
    mode=config['mode'];tasks=[];exclusions={};worlds=[]
    if mode.startswith('human'):
        rows,assignments,exclusions=human_source(inputs,mode=='human-full')
        if mode=='human-cost':rows=h.generated(rows,config['seed']);assignments=h.cost_assignments(rows,assignments)
        tasks=[('human' if mode=='human-full' else 'generated',rows,assignments,None,None)]
    else:
        if inputs:raise ValueError('Constructed phases require no human inputs')
        for regime in ('null','nuisance','signed'):
            for index in range(config['calibration_seeds']):
                seed=config['seed']+index;rows,dose=world(regime,seed,6 if mode=='constructed' else 12,index)
                assignments=h.h.bank(rows,draws=config['references'],seed=seed)['accepted']
                if mode=='constructed':native_oracles(c.support(rows)[0][sorted(c.support(rows)[0])[0]])
                tasks.append((regime+'-'+str(seed),rows,assignments,regime,dose))
    setup=time.process_time()-start;results={};worst=0.
    for label,rows,assignments,regime,dose in tasks:
        cfg=dict(config,seed=config['seed'] if regime is None else int(label.rsplit('-',1)[1]))
        analysis,t=analyze(output,label,rows,assignments,cfg,verifying);worst=max(worst,t);results[label]=analysis
        if regime:worlds.append(dict(label=label,regime=regime,dose=dose,analysis=analysis))
    s.checked(output/'PRIVATE_ANALYSIS.json',dict(results=results,worlds=worlds,original_exclusions=exclusions),verifying)
    summary=dict(card='D7.m',mode=mode,complete=True,human_scored=mode=='human-full',calibration=assess(worlds),
        analysis_sha256=filehash(output/'PRIVATE_ANALYSIS.json'),references_per_family=config['references'],
        bootstrap_draws=config['bootstrap_draws'],no_descendants=True,causal_claim=False)
    elapsed=time.process_time()-start
    arm_bytes=sum(p.stat().st_size for p in output.glob('*.json') if any(x in p.name for x in ('-real.','-joint-','-fake-')))
    timing=output/('VERIFY_TIMING.json' if verifying else 'EXECUTE_TIMING.json')
    if not timing.exists():write_equal(timing,dict(cpu_seconds=elapsed,setup_cpu_seconds=setup,fitting_cpu_seconds=elapsed-setup,max_complete_writer_cpu_seconds=worst,fitted_arm_bytes=arm_bytes))
    s.checked(output/'SUMMARY.json',summary,verifying)
    if verifying and mode.endswith('cost'):write_equal(output/'FORECAST.json',s.forecast([read(output/n) for n in ('EXECUTE_TIMING.json','VERIFY_TIMING.json')],mode.startswith('calibration')))
    return dict(verified=True,full_fresh_fit_replay=True) if verifying else summary


def execute(output,inputs,config):
    with threadpool_limits(limits=1):return calculate(output,inputs,config)


def verify(output,inputs,config):
    with threadpool_limits(limits=1):return calculate(output,inputs,config,True)
