"""TR5 matched failure drop, frozen run bins and handling-learner comparison.

DESIGN CHECK: LESSONS3-5 and controls read2026-10-25. Positive/reversed known
matched drops must change sign; shared regression in failure/control cancels.
Real writers carry both arms through every bootstrap. Within-writer run-bin
permutations retain matched controls. Raw drops alone carry no trust inference.
Whole-session holdout learners score each unseen choice before updating.
"""
from collections import defaultdict
from pathlib import Path
import time

import numpy as np

from . import week3_trust_learners as learners
from .week3_frames_stats import interval
from .timing_pmap_source import completed
from .timing_census import read,filehash
from .timing_p6 import gzread,write_equal

CONFIG=dict(card='TR5',mode='full',seed=20261026,bootstraps=2000,permutations=200)
PILOT=dict(CONFIG,mode='pilot')
CONSTRUCTED=dict(CONFIG,mode='constructed',bootstraps=200,permutations=200)


def drop(window,key):
    a,b=window[key+'_before'],window[key+'_after']
    return None if a is None or b is None else a-b


def paired_rows(data,key='acceptance',strict=False):
    rows=[]
    for p in data['pairs']:
        if strict and not p['failure']['strict_retyped']:continue
        a=drop(p['failure']['window'],key);b=[drop(c['window'],key) for c in p['controls']]
        if a is None or any(v is None for v in b):continue
        rows.append(dict(writer=p['writer'],bin=p['run_bin'],failure=a,control=float(np.mean(b)),delta=a-float(np.mean(b))))
    return rows


def writer_cells(rows,labels=None):
    by=defaultdict(lambda:defaultdict(list))
    for i,r in enumerate(rows):by[r['writer']][labels[i] if labels is not None else r['bin']].append(r['delta'])
    names=sorted(by)
    values=np.asarray([[np.mean(by[w][b]) if by[w][b] else np.nan for b in ('short','long')] for w in names])
    return names,values


def statistic(values):
    if not len(values) or not np.isfinite(values).any(0).all():return None
    means=[float(np.mean(values[np.isfinite(values[:,j]),j])) for j in (0,1)]
    return means[1]-means[0]


def compare(rows,rng,bootstraps,permutations):
    names,values=writer_cells(rows);observed=statistic(values)
    if observed is None:return dict(state='unsupported_bins',rows=len(rows),writers=len(names))
    bootstrap=[statistic(values[rng.integers(0,len(names),len(names))]) for _ in range(bootstraps)]
    missing=sum(v is None for v in bootstrap)
    indices={w:[i for i,r in enumerate(rows) if r['writer']==w] for w in names};labels=np.asarray([r['bin'] for r in rows])
    reference=[]
    for _ in range(permutations):
        shuffled=labels.copy()
        for idx in indices.values():shuffled[idx]=rng.permutation(shuffled[idx])
        reference.append(statistic(writer_cells(rows,shuffled)[1]))
    reference=np.asarray(reference,float);mean=float(reference.mean());sd=float(reference.std(ddof=1))
    biased=abs(mean)>.25*sd if sd else mean!=0
    return dict(state='unsupported_cluster_resampling' if missing else 'estimated',rows=len(rows),writers=len(names),
                estimate=observed,ci95=None if missing else np.quantile(bootstrap,[.025,.975]).tolist(),
                missing_bin_resamples=missing,reference=dict(mean=mean,sd=sd,ci95=np.quantile(reference,[.025,.975]).tolist(),
                    one_sided_p=float((1+np.sum(reference>=observed))/(permutations+1)),biased_reference=bool(biased)),
                weighting='equal writers within each bin; writer-bootstrap retains all failures and matched controls together')


def temperature(sessions,rng,bootstraps):
    groups=defaultdict(list)
    for s in sessions:
        for j,m in enumerate(s['menu']):
            if m['temperature'] is not None and not m['censored']:
                t=m['temperature'];time_=j/max(1,len(s['menu'])-1)
                groups[s['writer']].append(([t,time_,t*time_],int(m['handling'] in ('accept','edit'))))
    moments=[]
    for w,rows in sorted(groups.items()):
        x=np.asarray([r[0] for r in rows],float);y=np.asarray([r[1] for r in rows],float)
        x-=x.mean(0);y-=y.mean();moments.append((x.T@x,x.T@y))
    def solve(chosen):
        xx=sum(moments[i][0] for i in chosen);xy=sum(moments[i][1] for i in chosen)
        return None if np.linalg.matrix_rank(xx)<3 else np.linalg.solve(xx,xy)
    if not moments:return dict(state='unsupported_missing_settings')
    observed=solve(range(len(moments)))
    if observed is None:return dict(state='unsupported_setting_variation',writers=len(moments))
    bank=[solve(rng.integers(0,len(moments),len(moments))) for _ in range(bootstraps)]
    missing=sum(v is None for v in bank)
    return dict(state='descriptive_observational',writers=len(moments),estimates=observed.tolist(),
                ci95=None if missing else np.quantile(bank,[.025,.975],axis=0).T.tolist(),nonestimable_resamples=missing,
                coefficients=['temperature','session_position','temperature_times_position'],
                model='writer-demeaned linear probability regression; assignment mechanism unverified')


def analyze(data,config):
    rng=np.random.default_rng(config['seed']);b=config['bootstraps'];p=config['permutations']
    if not data['summary']['support']:
        return dict(card='TR5',state='unsupported',source_summary=data['summary'],scientific_admission=False)
    rows=paired_rows(data);primary=compare(rows,rng,b,p)
    secondary_request=compare(paired_rows(data,'request_rate'),rng,b,p)
    secondary_strict=compare(paired_rows(data,strict=True),rng,b,p)
    heldout=learners.by_writer(data['sessions']);gains={}
    for key in ('adaptive','changepoint'):
        values=[(r[key+'_log_likelihood']-r['fixed_log_likelihood'])/r['heldout_choices'] for r in heldout['rows']]
        gains[key]=interval(values,rng,b)
    if primary['state']!='estimated':state=primary['state']
    elif primary['reference']['biased_reference']:state='descriptive_only_biased_reference'
    elif primary['ci95'][0]>0 and primary['reference']['one_sided_p']<.05:state='positive'
    elif primary['ci95'][1]<0:state='negative'
    else:state='not_detected_sensitivity_unquantified'
    raw={}
    for bin_ in ('short','long'):
        selected=[r for r in rows if r['bin']==bin_];by=defaultdict(list)
        for r in selected:by[r['writer']].append(r)
        raw[bin_]={key:float(np.mean([np.mean([r[key] for r in rr]) for rr in by.values()])) if by else None for key in ('failure','control')}
    return dict(card='TR5',state=state,source_summary=data['summary'],run_median=data['run_median'],primary=primary,
                raw_drop_descriptives=raw,secondary_request=secondary_request,secondary_strict_retyped=secondary_strict,
                heldout_learner_gains_nats_per_choice=gains,heldout_support=dict(writers=len(heldout['rows']),unsupported_writers=len(heldout['unsupported_writers'])),
                heldout_fit_records=heldout,temperature=temperature(data['sessions'],rng,b),
                scientific_admission=state in ('positive','negative'),descriptive_probabilities_only=True,
                inference='history-modulated observed handling; no direct measurement of an internal trust state',
                sensitivity='null contrast sensitivity remains unquantified until a separate instrument check')


def load(inputs,config):
    if config not in (CONFIG,PILOT,CONSTRUCTED):raise ValueError('frozen TR5 configuration required')
    if config==CONSTRUCTED:
        if set(inputs)!={'fixture'}:raise ValueError('constructed fixture required')
        return read(inputs['fixture'])
    if set(inputs)!={'source_completion'}:raise ValueError('verified complete source required')
    parent=Path(inputs['source_completion']).parent
    for name in ('BINDING.json','EVENTS.json.gz','SUMMARY.json'):completed(inputs['source_completion'],parent/'output'/name)
    binding=read(parent/'output/BINDING.json')
    if binding['config']['card']!='TR5-inputs' or binding['config']['mode']!='full' or binding['config']['expected_sessions']!=1399:
        raise ValueError('full canonical TR5 population required')
    return gzread(parent/'output/EVENTS.json.gz')


def run(output,inputs,config,verification=False):
    started=time.process_time();output=Path(output);output.mkdir(parents=True,exist_ok=True)
    data=load(inputs,config);binding=dict(config=config,inputs={k:filehash(v) for k,v in sorted(inputs.items())})
    # The cost pilot runs the exact whole local statistic once; both phases
    # count against the card. It is cheap relative to its source extraction.
    result=analyze(data,config)
    if config==PILOT:result=dict(card='TR5-cost-pilot',state='timing_only',scientific_admission=False)
    if config==CONSTRUCTED:result.update(constructed_only=True,scientific_admission=False)
    if binding['inputs']!={k:filehash(v) for k,v in sorted(inputs.items())}:raise ValueError('source changed during TR5 analysis')
    for name,value in (('BINDING.json',binding),('RESULT.json',result)):
        if verification:
            if read(output/name)!=value:raise ValueError('TR5 complete replay differs')
        else:write_equal(output/name,value)
    name='VERIFY_TIME.json' if verification else 'EXECUTE_TIME.json'
    if not (output/name).exists():write_equal(output/name,dict(cpu_seconds=time.process_time()-started,
        projected_full_execute_and_replay_cpu_seconds=2*(time.process_time()-started),
        excludes='prior/native/pilot and source extraction; original parent ceiling7200seconds'))
    return dict(verified=True,complete_fresh_replay=True) if verification else result


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
