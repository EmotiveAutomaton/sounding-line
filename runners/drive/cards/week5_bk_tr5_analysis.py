"""Original TR5 complete consumer plus explicitly pooled below-floor reports."""
from pathlib import Path
from types import FunctionType,SimpleNamespace
import time
import numpy as np
from runners.stage9.common import digest
from . import week3_trust_analysis as old
from . import week5_bk_tr5_learners as learners
from .week5_bk_outcome_features_v2 import interval
from .week5_bk_outcome_analysis import pooled
from .week5_at_source import authenticate
from .timing_census import read,filehash
from .timing_p6 import gzread,write_equal,progress


def pooled_contrast(rows,seed=20261026,draws=200):
    names=sorted({r['writer'] for r in rows})
    totals=np.array([[sum(r['delta'] for r in rows if r['writer']==w and r['bin']==b) for b in ('short','long')] for w in names])
    counts=np.array([[sum(r['writer']==w and r['bin']==b for r in rows) for b in ('short','long')] for w in names])
    def solve(ix):
        n=counts[ix].sum(0)
        if not np.all(n):return None
        m=totals[ix].sum(0)/n;return float(m[1]-m[0])
    point=solve(np.arange(len(names))) if names else None
    bank=[];missing=0
    if point is not None and len(names)>1:
        rng=np.random.default_rng(seed)
        for _ in range(draws):
            value=solve(rng.integers(len(names),size=len(names)))
            if value is None:missing+=1
            else:bank.append(value)
    return dict(state='below floor, descriptive',estimate=point,ci95=np.quantile(bank,[.025,.975]).tolist() if bank and not missing else None,
                writers=len(names),events=len(rows),draws=len(bank)+missing,missing_bin_resamples=missing,
                weighting='equal matched failure events; controls averaged within failure; whole-writer bootstrap',scientific_admission=False)


def temperature(sessions,rng,n):
    value=old.temperature(sessions,rng,n)
    if value.get('writers')==1 and 'ci95' in value:value.update(ci95=None,uncertainty='one writer; no population interval')
    return value


def compare(rows,rng,b,p):
    value=old.compare(rows,rng,b,p)
    if value.get('writers')==1 and 'ci95' in value:value.update(ci95=None,state='single_writer_descriptive',uncertainty='one writer; no population interval')
    return value


def analyze(data,fits):
    if data['summary']['support']:
        fn=FunctionType(old.analyze.__code__,dict(old.__dict__,learners=SimpleNamespace(by_writer=lambda unused:fits),interval=interval,compare=compare,temperature=temperature))
        return fn(data,old.CONFIG)
    rng=np.random.default_rng(20261026);rows=old.paired_rows(data)
    gains={key:interval([(r[key+'_log_likelihood']-r['fixed_log_likelihood'])/r['heldout_choices'] for r in fits['rows']],rng,200) for key in ('adaptive','changepoint')}
    return dict(card='TR5',state='unsupported',scientific_admission=False,source_summary=data['summary'],run_median=data['run_median'],
                fallback=dict(primary=pooled_contrast(rows),request=pooled_contrast(old.paired_rows(data,'request_rate')),
                    strict_retyped=pooled_contrast(old.paired_rows(data,strict=True)),
                    raw_drop={b:{k:pooled([r for r in rows if r['bin']==b],k) for k in ('failure','control')} for b in ('short','long')},
                    heldout_learner_gains_nats_per_choice=gains,temperature=temperature(data['sessions'],rng,200)),
                heldout_fit_records=fits,inference='Below-floor pooled observed handling; no personal identification or trust claim')


def load(inputs,config):
    if set(config)!={'mode','max_wall_seconds'} or config['mode'] not in ('full','pilot','constructed') or not 30<=config['max_wall_seconds']<=1500:
        raise ValueError('Fixed TR5 whole-statistic or first-writer cost plan required')
    if config['mode']=='constructed':
        if set(inputs)!={'fixture'}:raise ValueError('Constructed fixture required')
        return read(inputs['fixture'])
    if set(inputs)!={'source_completion'}:raise ValueError('Complete source required')
    root=authenticate(Path(inputs['source_completion']).parent);plan=read(root/'PLAN.json');binding=read(root/'output/BINDING.json')
    if plan['module']!='runners.drive.cards.week5_bk_tr5_source' or binding['config']['card']!='TR5-inputs' or binding['config']['mode']!='full' or binding['config']['expected_sessions']!=1399:
        raise ValueError('Full canonical TR5 R1 source required')
    data=gzread(root/'output/EVENTS.json.gz')
    if not data['summary']['full_population']:raise ValueError('Partial source cannot feed full TR5 consumer')
    return data


def run(output,inputs,config,verifying=False):
    started=time.monotonic();cpu=time.process_time();root=Path(output);root.mkdir(parents=True,exist_ok=True)
    data=load(inputs,config);binding=dict(config=config,inputs={k:filehash(v) for k,v in inputs.items()},source=digest(data))
    write_equal(root/'BINDING.json',binding)
    def should_yield():
        return (root/'YIELD_REQUEST.json').exists() or (not verifying and time.monotonic()-started>=config['max_wall_seconds'])
    sessions=data['sessions']
    if config['mode']=='pilot':
        writers=sorted({s['writer'] for s in sessions});sessions=[s for s in sessions if s['writer']==writers[0]] if writers else []
    try:fits=learners.by_writer(root/'learners',sessions,verifying,should_yield)
    except learners.YieldCheckpoint:
        return dict(status='yielded',reason='sealed TR5 prequential checkpoint',scientific_admission=False)
    progress(root/'PROGRESS.json',dict(phase='complete-learner-replay' if verifying else 'complete-learners',writers=len(fits['rows'])))
    result=analyze(data,fits) if config['mode']!='pilot' else dict(card='TR5-cost',state='timing_only',writers=len(fits['rows']),sessions=len(sessions),scientific_admission=False)
    if config['mode']=='constructed':result.update(constructed_only=True,scientific_admission=False)
    if binding['inputs']!={k:filehash(v) for k,v in inputs.items()}:raise ValueError('TR5 source changed during execution')
    if verifying:
        if read(root/'RESULT.json')!=result:raise ValueError('Complete original TR5 result replay differs')
    else:write_equal(root/'RESULT.json',result)
    timing=root/('VERIFY_TIME.json' if verifying else 'EXECUTE_TIME.json')
    if not timing.exists():write_equal(timing,dict(cpu_seconds=time.process_time()-cpu,wall_seconds=time.monotonic()-started,
        checkpoint_bytes=sum(p.stat().st_size for p in (root/'learners').rglob('*') if p.is_file()),excludes='prior segments and native startup; total native accounting remains authoritative'))
    return dict(verified=True,full_transition_and_statistic_replay=True) if verifying else dict(status='complete',scientific_admission=False)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
