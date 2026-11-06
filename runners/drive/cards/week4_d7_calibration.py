"""D7 complete constructed-world calibration with both reference banks.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-7 reread 2026-11-04.
NULL/no-novelty and nuisance-only worlds should not acquire positive duration
prediction; signed novelty should improve prediction with its coefficient sign
preserved. Fake writers preserve a population law, so their positive gain is
not failure. All allocation support is checked before fits. Missing draws or
support changes invalidate a bank; no redraw or successful-only probability.
Human evidence is not read by this module.
"""
from collections import defaultdict
from pathlib import Path
import math
import time
import numpy as np
from threadpoolctl import threadpool_limits
from runners.stage14.common import read, atomic, digest
from . import week3_d7_models as m
from .timing_p6 import write_equal

SETTINGS=tuple((response,cost) for response in m.RESPONSES for cost in m.COSTS)
PRIMARY='duration/elapsed'


def configuration(mode):
    if mode not in ('constructed','timing','calibration'):
        raise ValueError('Unknown calibration mode')
    return dict(card='D7-complete-calibration',mode=mode,seed=20261026,
                seeds=1 if mode!='calibration' else 10,
                permutations=2 if mode!='calibration' else 200,
                bootstrap_draws=20 if mode=='constructed' else 2000,
                writers=6 if mode=='constructed' else 12,sessions=10,menus=12,
                regimes=['null','nuisance','signed'],primary=PRIMARY)


def world(regime,seed,writers=12,ordinal=0):
    if regime not in ('null','nuisance','signed'):raise ValueError('Unknown regime')
    dose=0. if regime!='signed' else (.8 if ordinal%2==0 else -.8)
    rows=m.world(seed=seed,writers=writers,dose=dose)
    if regime=='nuisance':
        rng=np.random.default_rng(np.random.SeedSequence([seed,747]))
        for r in rows:
            r['mean_novelty']=float(np.clip(.15+.7*r['menu_ordinal']/11+rng.normal(0,.03),0,1))
            logtime=math.log1p(r['dwell_seconds'])+.45*math.log1p(r['elapsed_seconds'])
            r['dwell_seconds']=math.expm1(logtime)
    return rows,dose


def support(rows):
    groups=m.writers(rows);valid={};excluded={}
    for w,rr in groups.items():
        _,reason=m.partition(rr)
        if reason:excluded[w]=reason
        else:valid[w]=rr
    return valid,excluded


def session_assignment(rows,index,seed):
    sessions={};blocks=defaultdict(list)
    for r in rows:
        meta=(r['writer'],r['prompt'])
        if r['session'] in sessions and sessions[r['session']]!=meta:
            raise ValueError('Session ownership or prompt changed')
        sessions[r['session']]=meta
    for s,(w,prompt) in sorted(sessions.items()):blocks[prompt].append((s,w))
    rng=np.random.default_rng(np.random.SeedSequence([seed,index,171]))
    assignment={}
    for prompt,block in sorted(blocks.items()):
        for (s,_),w in zip(block,rng.permutation([w for s,w in block])):
            assignment[s]=str(w)
    return assignment


def reassigned(rows,assignment):
    if set(assignment)!={r['session'] for r in rows}:raise ValueError('Incomplete assignment')
    return [dict(r,writer=assignment[r['session']]) for r in rows]


def audit_bank(rows,draws,seed):
    groups,excluded=support(rows);roster=sorted(groups)
    checks=[]
    for index in range(draws):
        assignment=session_assignment(rows,index,seed)
        other,bad=support(reassigned(rows,assignment))
        checks.append(dict(draw=index,assignment_sha256=digest(assignment),
                           same_supported_writers=sorted(other)==roster,
                           supported_writers=len(other),exclusions=bad))
    return dict(writers=roster,exclusions=excluded,draws=checks,
                complete=len(checks)==draws,valid=all(r['same_supported_writers'] for r in checks))


def joint_labels(rows,index,seed,writer_index):
    labels=m.label_array(rows);observed=np.array([i for i,r in enumerate(rows) if r['dwell_observed']],int)
    rng=np.random.default_rng(np.random.SeedSequence([seed,index,writer_index,273]))
    changed=labels.copy();changed[observed]=labels[rng.permutation(observed)]
    return changed


def fits(groups,reference=None,seed=20261026):
    receipts={};max_unit=0.
    for wi,(w,rows) in enumerate(sorted(groups.items())):
        began=time.process_time();labels=None if reference is None else joint_labels(rows,reference,seed,wi)
        values={}
        for response,cost in SETTINGS:
            fit=m.compare(rows,response,cost,labels)
            values[response+'/'+cost]=dict(gain=fit['gain'],full_fit_sha256=digest(fit),
                added_coefficient=fit['fits'][1]['coefficients'][-1])
        receipts[w]=values;max_unit=max(max_unit,time.process_time()-began)
    return receipts,max_unit


def summarize(real,joint,fake,draws,seed):
    writers=sorted(real)
    if len(writers)<3 or any(sorted(bank)!=writers for bank in joint+fake):
        raise ValueError('Entire fixed reference roster required')
    rng=np.random.default_rng(seed);indices=rng.integers(0,len(writers),size=(draws,len(writers)))
    result={}
    for response,cost in SETTINGS:
        key=response+'/'+cost;g=np.array([real[w][key]['gain'] for w in writers])
        point=float(g.mean());boot=g[indices].mean(1);lo,hi=np.quantile(boot,[.025,.975])
        null=[float(np.mean([b[w][key]['gain'] for w in writers])) for b in joint]
        fake_means=[float(np.mean([b[w][key]['gain'] for w in writers])) for b in fake]
        p=(1+sum(v>=point for v in null))/(len(null)+1)
        if not np.isfinite(g).all() or not np.isfinite(null+fake_means).all():
            raise ValueError('Nonfinite complete reference')
        result[key]=dict(gain=point,ci_low=float(lo),ci_high=float(hi),bootstrap_draws=draws,
            writers=len(writers),joint_permutation=dict(attempted=len(null),invalid=0,mean=float(np.mean(null)),
                one_sided_p=p,positive_bias_flag=bool(np.mean(null)>.005)),
            fake_writer=dict(attempted=len(fake_means),invalid=0,mean=float(np.mean(fake_means)),
                scope='Population association may survive; not a personal-signal null'),
            positive=bool(lo>0 and p<=.05 and np.mean(null)<=.005),
            mean_added_coefficient=float(np.mean([real[w][key]['added_coefficient'] for w in writers])))
    return result


def analyze(rows,config,seed,checkpoint=lambda *args:None):
    audit=audit_bank(rows,config['permutations'],seed)
    if not audit['valid']:
        return dict(state='invalid',reason='Reference changes supported writers before any fit',support=audit),0.
    groups,excluded=support(rows)
    real,worst=fits(groups,seed=seed);joint=[];fake=[]
    checkpoint(1,1+2*config['permutations'])
    for index in range(config['permutations']):
        a,t=fits(groups,index,seed);joint.append(a);worst=max(worst,t)
        changed=reassigned(rows,session_assignment(rows,index,seed));other,_=support(changed)
        b,t=fits(other,seed=seed);fake.append(b);worst=max(worst,t)
        checkpoint(3+2*index,1+2*config['permutations'])
    return dict(state='complete',support=audit,primary=PRIMARY,
                summaries=summarize(real,joint,fake,config['bootstrap_draws'],seed),
                private_fit_receipts=dict(real=real,joint=joint,fake=fake)),worst


def assess(worlds):
    if len(worlds)!=30:return dict(state='not_applicable',reason='Timing/engineering prefix only')
    invalid=[r['label'] for r in worlds if r['analysis']['state']!='complete']
    if invalid:return dict(state='invalid',invalid_worlds=invalid,passes=False)
    groups=defaultdict(list)
    for r in worlds:
        a=r['analysis']['summaries'][PRIMARY]
        category=r['regime'] if r['dose']==0 else ('positive' if r['dose']>0 else 'negative')
        groups[category].append(a)
    counts={k:dict(worlds=len(v),detected=sum(r['positive'] for r in v)) for k,v in sorted(groups.items())}
    correct_sign=all(r['analysis']['summaries'][PRIMARY]['mean_added_coefficient']*r['dose']>0 for r in worlds if r['dose'])
    passes=(counts['null']['detected']<=1 and counts['nuisance']['detected']<=1 and
            counts['positive']['detected']>=4 and counts['negative']['detected']>=4 and correct_sign)
    return dict(state='complete',passes=bool(passes),counts=counts,signed_coefficients_correct=bool(correct_sign),
                scope='Constructed primary duration recovery only; no human sensitivity or acceptance calibration')


def calculate(output,inputs,config,verification=False):
    if inputs or config!=configuration(config.get('mode')):raise ValueError('Frozen constructed-only contract required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    write_equal(output/'BINDING.json',dict(config=config,inputs=inputs))
    worlds=[];times=[];start=time.process_time()
    for regime in config['regimes']:
        for ordinal in range(config['seeds']):
            seed=config['seed']+ordinal;label=f'{regime}-{seed}';path=output/(label+'.json')
            # A completed world is an execution checkpoint; verification always rebuilds it.
            if path.exists() and not verification:
                record=read(path)
                if record['label']!=label or record['config']!=config:raise ValueError('Checkpoint binding changed')
                worlds.append(record);continue
            rows,dose=world(regime,seed,config['writers'],ordinal)
            def progress(done,total):
                if (output.parent/'STOP').exists() or (output/'YIELD_REQUEST.json').exists():
                    raise InterruptedError('D7 calibration boundary yield')
                atomic(output/'PROGRESS.json',dict(phase=('verify-' if verification else '')+label,
                    world_completed=len(worlds),world_total=config['seeds']*3,arms_done=done,arms_total=total))
            analysis,worst=analyze(rows,config,seed,progress);times.append(worst)
            record=dict(label=label,regime=regime,dose=dose,config=config,analysis=analysis)
            if verification:
                if read(path)!=record:raise ValueError('Fresh complete fitted world differs: '+label)
            else:write_equal(path,record)
            worlds.append(record)
    summary=dict(card=config['card'],mode=config['mode'],worlds=len(worlds),calibration=assess(worlds),
                 config=config,worlds_sha256=digest(worlds),scientific_human_admission=False)
    name='VERIFY_TIMING.json' if verification else 'EXECUTE_TIMING.json'
    if not (output/name).exists():
        write_equal(output/name,dict(cpu_seconds=time.process_time()-start,max_complete_writer_cpu_seconds=max(times,default=0.)))
    if verification:
        if read(output/'SUMMARY.json')!=summary:raise ValueError('Complete calibration summary differs')
        if config['mode']=='timing':
            timings=[read(output/n) for n in ('EXECUTE_TIMING.json','VERIFY_TIMING.json')]
            worst=max(t['max_complete_writer_cpu_seconds'] for t in timings)
            unit_forecast=6*(worst*12*401*30+60)
            whole_forecast=6*max(t['cpu_seconds'] for t in timings)*(401/5)*10
            write_equal(output/'FORECAST.json',dict(calibration_cpu_seconds=max(unit_forecast,whole_forecast),
                complete_writer_forecast=unit_forecast,whole_pipeline_forecast=whole_forecast,
                full_worlds=30,reference_arms=401,both_passes=True,safety_factor=3,
                worst_complete_writer_cpu_seconds=worst,human_admission=False))
    else:write_equal(output/'SUMMARY.json',summary)
    return dict(verified=True,full_fresh_fit_replay=True,all_reference_draws_retained=True) if verification else summary


def execute(output,inputs,config):
    with threadpool_limits(limits=2):return calculate(output,inputs,config)


def verify(output,inputs,config):
    with threadpool_limits(limits=2):return calculate(output,inputs,config,True)
