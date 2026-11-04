"""PP1.ic exact array-cache implementation, frozen before calibration.

DESIGN CHECK: LESSONS 3-5; CONTROLS 6. Whole-writer bootstrap preserves each
copied writer's within-word median. Cache only those raw normalized arrays,
not a fit. Null/alternative/gates and full draw counts remain the original's.
Parity failure refuses under every scientific state; no successful-only draws.
"""
from pathlib import Path
import time
import numpy as np
from threadpoolctl import threadpool_limits
from . import week4_pp1_ic as original
from . import week3_pause_model as model
from .timing_p6 import write_equal,gzip_equal,gzread
from runners.stage14.common import atomic,read


def prepare(rows):
    a=model.arrays(rows)
    names=sorted(set(a['writers']))
    groups=[np.flatnonzero(np.array(a['writers'])==w) for w in names]
    return a,groups


def gather(prepared,selected):
    a,groups=prepared
    indices=np.concatenate([groups[int(i)] for i in selected])
    b={k:a[k][indices] for k in ('log_interval','raw_interval','location','mechanical','training','time','order')}
    b['writers']=[f'copy-{n}' for n,i in enumerate(selected) for _ in groups[int(i)]]
    b['prompts']=[a['prompts'][i] for i in indices]
    return b


def contrasts(a):
    mechanical,_=model.mechanics(a)
    posterior,_=model.mixture(a['log_interval']-mechanical*a['mechanical'])
    loc=a['location']
    x=np.column_stack([loc=='before_sentence',loc=='before_paragraph',loc=='before_revision',loc=='within_word',a['mechanical'],a['time'],a['order']])
    beta,_=model.full_fit(x,posterior[:,1],a['writers'],a['prompts'])
    if not np.isfinite(beta[:3]).all():raise ValueError('Required boundary contrast absent')
    return dict(sentence_minus_word=float(beta[0]),paragraph_minus_sentence=float(beta[1]-beta[0]),revision_minus_sentence=float(beta[2]-beta[0]))


def compute(output,config):
    results=[];bank=[];timings=[]
    for seed in original.SEEDS:
        for dose in original.DOSES:
            rows,truth=original.world(seed,dose);t=time.process_time();prepared=prepare(rows);observed=contrasts(prepared[0]);times=[time.process_time()-t]
            rng=np.random.default_rng(config['seed']);draws=[]
            for index in range(config['bootstrap_draws']):
                selected=rng.integers(0,20,20);t=time.process_time()
                draws.append(contrasts(gather(prepared,selected)));times.append(time.process_time()-t)
                atomic(Path(output)/'PROGRESS.json',dict(seed=seed,dose=dose,done=index+1,total=config['bootstrap_draws']))
                if (Path(output).parent/'STOP').exists() or (Path(output)/'YIELD_REQUEST.json').exists():raise InterruptedError('PP1.ic.h1 yield at complete fit')
            timings.append(dict(seed=seed,dose=dose,fit_cpu_seconds=times))
            if config['mode']!='cost':
                lo,hi=np.quantile([d['sentence_minus_word'] for d in draws],[.025,.975])
                results.append(dict(**truth,effect=observed['sentence_minus_word'],ci_low=float(lo),ci_high=float(hi),state=original.classify(lo,hi),draws=len(draws)))
                bank.append(dict(seed=seed,dose=dose,draws=draws))
    if config['mode']=='cost':return dict(card='PP1.ic.h1-cost',scientific_admission=False,projected_execute_and_replay_cpu_seconds=2*sum(max(t['fit_cpu_seconds'])*2001 for t in timings)+60,timings=timings),None
    return dict(card='PP1.ic.h1',scientific_admission=False,constructed=True,full_calibration=config['mode']=='calibration',worlds=results,scope='Six fixed constructed worlds; no population power or human sensitivity claim'),bank


def run(output,inputs,config,verification=False):
    original.configuration(config)
    if inputs:raise ValueError('No external data accepted')
    with threadpool_limits(limits=1):result,bank=compute(output,config)
    output=Path(output)
    if verification:
        if config['mode']=='cost':
            saved=read(output/'RESULT.json')
            if saved['card']!='PP1.ic.h1-cost' or len(saved['timings'])!=6 or saved['projected_execute_and_replay_cpu_seconds']<=0:raise ValueError('Invalid cost receipt')
            atomic(output/'VERIFY_COST.json',result)
        elif read(output/'RESULT.json')!=result or gzread(output/'BOOTSTRAPS.json.gz')!=bank:raise ValueError('PP1.ic.h1 reconstruction differs')
        return dict(verified=True,full_replay=True,constructed=True)
    write_equal(output/'RESULT.json',result)
    if bank is not None:gzip_equal(output/'BOOTSTRAPS.json.gz',bank)
    return result


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
