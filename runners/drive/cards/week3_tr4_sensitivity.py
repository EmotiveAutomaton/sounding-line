"""First-generation TR4.ic known-drift worlds, with unchanged parent rules.

DESIGN CHECK: LESSONS 3-5 and CONTROLS read 2026-10-27. NULL latent probabilities
do not change; ALTERNATIVE total variation equals the frozen dose and oracle
excess loss is positive. Detection failures are results, never repair triggers.
Full references, undefined correlations and bias flags are retained unchanged.
"""
from pathlib import Path
import hashlib
import json
import time
import numpy as np
from . import week3_tr4_comparison as parent
from .timing_census import read,filehash
from .timing_pmap_source import completed
from .timing_p6 import write_equal,progress

DOSES=(0.,.15,.30)
SEEDS=(202610260,202610261,202610262,202610263)
CONFIGS={
 'constructed':dict(mode='constructed',worlds=[[.15,202610298]],outcomes=3,labels=3,bootstraps=11),
 'cost':dict(mode='cost',worlds=[[.30,202610299]],outcomes=200,labels=1000,bootstraps=2000),
 'main':dict(mode='main',worlds=[[dose,seed] for dose in DOSES for seed in SEEDS],outcomes=200,labels=1000,bootstraps=2000),
}


def construct(dose,seed):
    if dose not in DOSES or type(seed) is not int: raise ValueError('frozen dose and integer seed required')
    rng=np.random.default_rng(seed);rows=[];truth=[];writers={};oracle=[]
    for w in range(18):
        writer=f'w{w:02d}';half='discovery' if w<4 else 'test';writers[writer]=half
        initial=float(rng.uniform(.45,.55));direction=1 if w%2 else -1
        initial_p=np.array([initial]+[(1-initial)/3]*3)
        for j in range(24):
            accept=initial+(direction*dose if j>=12 else 0.)
            p=np.array([accept]+[(1-accept)/3]*3)
            if np.any(p<=0) or not np.isclose(p.sum(),1):raise ValueError('invalid latent probability')
            uniforms=rng.random(100);x=np.bincount(np.searchsorted(np.cumsum(p),uniforms),minlength=4)
            if len(x)!=4 or x.sum()!=100:raise ValueError('categorical construction coverage differs')
            sid=f'{writer}-{j:02d}'
            rows.append(dict(writer=writer,session=sid,prompt=str(j%2),half=half,start=j*3,end=j*3+1,counts=dict(zip(parent.CLASSES,x.tolist()))))
            truth.append(dict(session=sid,probabilities=p.tolist(),variation_from_initial=float(abs(p-initial_p).sum()/2)))
            if j>=12:oracle.append(float(np.sum(p*np.log(p/initial_p))))
    census=dict(rows=rows,split=dict(seed=parent.SEED,writers=writers,session_counts={w:24 for w in writers}))
    return dict(census=census,truth=truth,oracle_old_probability_penalty=float(np.mean(oracle)),dose=dose,seed=seed)


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def summarize(cells):
    rows=[]
    for dose in sorted({x['dose'] for x in cells}):
        selected=[x for x in cells if x['dose']==dose];prim=[x['result']['primary'] for x in selected]
        rows.append(dict(dose=dose,worlds=len(selected),positive=sum(p['status']=='positive' for p in prim),
                         positive_interval=sum(p['bootstrap']['supported'] and p['bootstrap']['interval'][0]>0 for p in prim),
                         biased_reference=sum(p['reference_biased'] is True for p in prim),
                         unsupported_reliability=sum(not x['result']['reliability']['paired_bootstrap']['supported'] for x in selected)))
    return dict(doses=rows,constructed=True,descriptive=True,scientific_admission=False,
                scope='Four worlds per final dose: conditional diagnostic only; no general size, power, human or preference claim')


def run(output,inputs,config,verification=False):
    mode=config.get('mode')
    if mode not in CONFIGS or config!=CONFIGS[mode]: raise ValueError('frozen sensitivity configuration required')
    expected={'parent_landing'}|({'cost_completion','cost_landing'} if mode=='main' else set())
    if set(inputs)!=expected:raise ValueError('parent/cost bindings required')
    landing=read(inputs['parent_landing'])
    if not landing['full_write_through'] or landing['id']!='S15-TR4-20261027':raise ValueError('complete parent landing required')
    if mode=='main':
        cost=Path(inputs['cost_completion']);gate=read(inputs['cost_landing'])
        completed(cost,cost.parent/'output/SUMMARY.json')
        if not gate['full_write_through'] or not gate['admitted'] or gate['cost_completion_sha256']!=filehash(cost):raise ValueError('complete admitted cost required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True);(output/'cells').mkdir(exist_ok=True)
    started=time.process_time();cells=[]
    for index,(dose,seed) in enumerate(config['worlds']):
        world=construct(dose,seed)
        def update(phase,done,total):
            progress(output/'PROGRESS.json',dict(phase=('verify-' if verification else '')+phase,world=index+1,worlds=len(config['worlds']),done=done,total=total))
            if (output.parent/'STOP').exists() or (output/'YIELD_REQUEST.json').exists():raise InterruptedError('TR4.ic reference-boundary yield')
        result,_=parent.run_analysis(world['census'],outcome_repetitions=config['outcomes'],label_repetitions=config['labels'],bootstraps=config['bootstraps'],progress=update)
        cell=dict(dose=dose,seed=seed,world=world,world_sha256=digest(world),result=result)
        path=output/'cells'/f'{index:02d}.json'
        if verification:
            if read(path)!=cell:raise ValueError('complete sensitivity cell replay differs')
        else:write_equal(path,cell)
        cells.append(cell)
    if len({x['world_sha256'] for x in cells})!=len(cells):raise ValueError('duplicate constructed evidence')
    payloads={'SUMMARY.json':summarize(cells),'BINDING.json':dict(config=config,inputs={k:filehash(v) for k,v in inputs.items()})}
    for name,value in payloads.items():
        if verification:
            if read(output/name)!=value:raise ValueError('sensitivity summary replay differs')
        else:write_equal(output/name,value)
    if not verification and not (output/'TIMING.json').exists():write_equal(output/'TIMING.json',dict(cpu_seconds=time.process_time()-started,worlds=len(cells)))
    if verification:return dict(verified=True,complete_input_replay=True,scientific_admission=False)
    return dict(status='complete',mode=mode,scientific_admission=False)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
