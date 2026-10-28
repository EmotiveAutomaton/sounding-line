"""Frozen complete TR4 consumer, constructed checks and full-population cost.

DESIGN CHECK: LESSONS 3-5 and CONTROLS reread 2026-10-27. Known NULL returns
zero, not a positive; known change rewards adaptive tracking. Undefined and
biased references retain their limits. Full controls and fresh replay are in
the cost forecast. Missing/changed completion bindings refuse execution.
"""
from pathlib import Path
import time
from . import week3_tr4_comparison as c
from .timing_census import read,filehash
from .timing_pmap_source import completed
from .timing_p6 import write_equal,progress

CONFIGS={
    'constructed':dict(mode='constructed',seed=c.SEED,outcome_repetitions=5,label_repetitions=5,bootstraps=31),
    'cost':dict(mode='cost',seed=c.SEED,outcome_repetitions=2,label_repetitions=2,bootstraps=20),
    'main':dict(mode='main',seed=c.SEED,outcome_repetitions=200,label_repetitions=1000,bootstraps=2000),
}


def constructed(pattern):
    rows=[];writers={}
    for w in range(6):
        writer=str(w);writers[writer]='discovery' if w<2 else 'test'
        for j in range(24):
            x=[250]*4 if pattern=='uniform' or j<12 else [850,50,50,50]
            rows.append(dict(writer=writer,session=f'{w}-{j}',prompt=str(j%2),half=writers[writer],
                             start=j*3,end=j*3+1,counts=dict(zip(c.CLASSES,x))))
    return dict(rows=rows,split=dict(seed=c.SEED,writers=writers,session_counts={w:24 for w in writers}))


def projection(timing):
    # Bootstrap reference work grows in both repeats and reference profiles.
    serial=(timing['forecasts']+timing['profiles']+100*timing['outcome']+
            500*timing['labels']+100*500*timing['uncertainty'])
    return dict(execute_and_fresh_verify_cpu_seconds=3*serial,safety_factor=1.5,
                full_config=CONFIGS['main'],includes_full_population=True,
                includes_all_reference_banks=True,includes_fresh_replay=True)


def run(output,inputs,config,verification=False):
    mode=config.get('mode')
    if mode not in CONFIGS or config!=CONFIGS[mode]: raise ValueError('frozen analysis configuration required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True);started=time.process_time()
    def update(phase,done,total):
        progress(output/'PROGRESS.json',dict(phase=('verify-' if verification else '')+phase,done=done,total=total))
        if (output.parent/'STOP').exists() or (output/'YIELD_REQUEST.json').exists():
            raise InterruptedError('TR4 yields at completed reference boundary')
    sizes={k:config[k] for k in ('outcome_repetitions','label_repetitions','bootstraps')}
    if mode=='constructed':
        if inputs: raise ValueError('constructed checks have no human input')
        values={};timings={}
        for name in ('uniform','change'):
            values[name],timings[name]=c.run_analysis(constructed(name),**sizes,progress=update)
        null=values['uniform']['primary'];alt=values['change']['primary']
        gates=dict(exact_uniform=null['estimate']==0 and null['reference']['mean']==0,
                   no_false_positive=null['probability']==1 and null['bootstrap']['interval']==[0,0],
                   undefined_reliability_retained=values['uniform']['reliability']['real'] is None,
                   change_tracked=alt['estimate']>.05,
                   bias_not_bypassed=not alt['reference_biased'] or alt['status']=='descriptive_only_biased_reference')
        if not all(gates.values()): raise ValueError('TR4 complete constructed consumer gate failed')
        result=dict(cases=values,gates=gates,scientific_admission=False)
    else:
        expected={'source_completion'} | ({'cost_completion','cost_landing'} if mode=='main' else set())
        if set(inputs)!=expected: raise ValueError('complete analysis bindings required')
        parent=Path(inputs['source_completion']).parent;source=parent/'output/CENSUS.json'
        completed(inputs['source_completion'],source);census=read(source)
        if not census['summary']['full_population']: raise ValueError('full source population required')
        if mode=='main':
            cost=Path(inputs['cost_completion']).parent/'output/COST.json'
            completed(inputs['cost_completion'],cost);gate=read(inputs['cost_landing'])
            if not gate['full_write_through'] or not gate['admitted'] or gate['cost_completion_sha256']!=filehash(inputs['cost_completion']):
                raise ValueError('full cost landing required')
            if gate['source_completion_sha256']!=filehash(inputs['source_completion']): raise ValueError('changed source')
            if read(cost)['full_config']!=config: raise ValueError('costed configuration differs')
        result,timings=c.run_analysis(census,**sizes,progress=update)
        result['scientific_admission']=False
    payloads={'RESULTS.json':result,'BINDING.json':dict(config=config,inputs={k:filehash(v) for k,v in inputs.items()})}
    for name,value in payloads.items():
        if verification:
            if read(output/name)!=value: raise ValueError('complete TR4 independent replay differs')
        else: write_equal(output/name,value)
    # Timings are measured once; a fresh replay verifies evidence, not clock values.
    if not verification and not (output/'TIMING.json').exists():
        write_equal(output/'TIMING.json',dict(phases=timings,cpu_seconds=time.process_time()-started))
    if mode=='cost':
        expected_cost=projection(read(output/'TIMING.json')['phases'])
        if verification:
            if read(output/'COST.json')!=expected_cost: raise ValueError('cost arithmetic differs')
        else: write_equal(output/'COST.json',expected_cost)
    update('complete',1,1)
    if verification:return dict(verified=True,complete_input_replay=True,scientific_admission=False)
    return dict(status='complete',scientific_admission=False,mode=mode)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
