"""Exact WC4 profile comparison, with pooled descriptive variance fallback."""
from pathlib import Path
from collections import defaultdict
import time
import numpy as np
from . import week3_stability_stats as stats
from .week3_stability_analysis import CONFIG,PILOT
from .week3_stability_inputs import PROPERTIES
from .week5_at_source import authenticate
from .timing_census import read,filehash
from .timing_p6 import gzread,write_equal


def pooled_variance(rows,key,draws=200,seed=20261026):
    eligible=[r for r in rows if r['event_eligible'] and r['properties'][key] is not None]
    groups=defaultdict(list)
    for r in eligible:groups[r['writer']].append(r)
    names=sorted(groups)
    def calculate(items):
        if len(items)<2:return None
        prompt=defaultdict(list)
        for r in items:prompt[r['prompt']].append(float(r['properties'][key]))
        centers={p:float(np.mean(v)) for p,v in prompt.items()}
        return float(np.var([r['properties'][key]-centers[r['prompt']] for r in items],ddof=1))
    point=calculate(eligible);bank=[];invalid=0
    if len(names)>1 and point is not None:
        rng=np.random.default_rng(seed)
        for _ in range(draws):
            ix=rng.integers(len(names),size=len(names));value=calculate([r for j in ix for r in groups[names[j]]])
            if value is None:invalid+=1
            else:bank.append(value)
    return dict(variance=point,ci95=np.quantile(bank,[.025,.975]).tolist() if bank and not invalid else None,
                sessions=len(eligible),writers=len(names),draws=len(bank)+invalid,nonestimable_draws=invalid,
                meaning='pooled prompt-adjusted session variability; no individual stability or controlled-goal identification')


def run(output,inputs,config,verifying=False):
    if set(config)!={'mode'} or config['mode'] not in ('full','pilot','constructed'):raise ValueError('Fixed WC4 consumer required')
    began=time.process_time();root=Path(output)
    if config['mode']=='constructed':
        if set(inputs)!={'fixture'}:raise ValueError('Constructed source required')
        rows=read(inputs['fixture'])
    else:
        if set(inputs)!={'source_completion'}:raise ValueError('Complete WC4 R1 source required')
        source=authenticate(Path(inputs['source_completion']).parent);plan=read(source/'PLAN.json');binding=read(source/'output/BINDING.json')
        if plan['module']!='runners.drive.cards.week5_bk_wc4_source' or binding['config']['card']!='WC4-inputs' or binding['config']['mode']!='full' or binding['config']['expected_sessions']!=1399:
            raise ValueError('Complete original WC4 population required')
        rows=gzread(source/'output/EVENTS.json.gz')['sessions']
    cfg=PILOT if config['mode']=='pilot' else CONFIG
    result=stats.analyze(rows,cfg)
    if result['state'].startswith('unsupported'):
        result['fallback']=dict(state='below floor or unidentified, descriptive',scientific_admission=False,
            properties={k:pooled_variance(rows,k) for k in PROPERTIES},identification='Pooled variability cannot recover an unidentifiable across-writer correlation')
    if config['mode']=='pilot':result=dict(card='WC4-cost',state='timing_only',scientific_admission=False)
    if config['mode']=='constructed':result.update(constructed_only=True,scientific_admission=False)
    binding=dict(config=config,inputs={k:filehash(v) for k,v in inputs.items()})
    for name,value in [('BINDING.json',binding),('RESULT.json',result)]:
        if verifying:
            if read(root/name)!=value:raise ValueError('Full WC4 result replay differs')
        else:write_equal(root/name,value)
    cost=root/('VERIFY_TIME.json' if verifying else 'EXECUTE_TIME.json')
    if not cost.exists():write_equal(cost,dict(cpu_seconds=time.process_time()-began,excludes='source and prior/native charges; original3600CPU ceiling applies'))
    return dict(verified=True,full_original_wc4_and_pooled_replay=True) if verifying else dict(status='complete',scientific_admission=False)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
