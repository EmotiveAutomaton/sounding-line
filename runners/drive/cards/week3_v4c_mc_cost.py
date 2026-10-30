"""Cost-only complete R-both refits; no Monte Carlo scientific verdict.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-7 reread 2026-10-30.
NULL/ALTERNATIVE have the same complete-source retention and optimizer guards.
Three fixed outer worlds and one new null each time a full pipeline unit. Their
timings cannot replace the declared 110 by 199 reference matrix. Verification
rebuilds every fit and generated choice; modified source or output fails closed.
"""
from pathlib import Path
import time
from runners.stage14.common import read,freeze,atomic,filehash
from . import menus_v4_saved_diagnostics as source
from . import week3_v4c_mc_reference as core

CONFIG=dict(mode='cost',seed=20261030,optimizer_maxiter=100,reference_datasets=199,outer_worlds=110)
FIXTURE=dict(CONFIG,mode='constructed')


def load(inputs,config):
    if config not in (CONFIG,FIXTURE):raise ValueError('Frozen cost configuration required')
    s=source.load(inputs,dict(bootstrap_draws=2000,bootstrap_seed=20261017))
    constructed=bool(s['complete'].get('synthetic_fixture_only'))
    if constructed!=(config==FIXTURE):raise ValueError('Fixture/corpus source mismatch')
    selected=[w for w in s['worlds'] if not w['cell']['permuted'] and w['cell']['delta']==.4 and w['cell']['replicate']==0]
    if len(selected)!=3:raise ValueError('Complete three-plant cost roster required')
    s['selected']=selected[:1] if constructed else selected
    return s


def compute(output,inputs,config,verification=False):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);s=load(inputs,config)
    binding=dict(config=config,inputs=s['identity'],code={str(Path(m.__file__).resolve()):filehash(m.__file__) for m in (source,core)})
    def retain(name,v):
        p=output/name
        if verification:
            if read(p)!=v:raise ValueError('Fresh complete cost replay differs: '+name)
        else:freeze(p,v)
    retain('BINDING.json',binding)
    times=[];completed=[]
    for world in s['selected']:
        name=source.world_name(world['cell']);path=output/'worlds'/name
        if (output/'YIELD_REQUEST.json').exists() or (output.parent/'STOP').exists():raise InterruptedError('Whole-world boundary yield')
        construction,saved=source.load_world(s,world)
        rows=source.rebuild(s['sessions'],construction,s['plan']['config']['seed'])
        started=time.process_time();model=core.fit_null(rows,saved,s['base'],config['optimizer_maxiter']);fit_cpu=time.process_time()-started
        started=time.process_time();observed=core.statistic(rows,s['sessions'],saved,s['geometry'],s['base'],config['optimizer_maxiter']);observed_cpu=time.process_time()-started
        seed=config['seed']+1000*source.roster().index(world['cell'])
        started=time.process_time();generated,trace=core.generate(rows,s['base'],model,seed)
        null=core.statistic(generated,s['sessions'],saved,s['geometry'],s['base'],config['optimizer_maxiter']);null_cpu=time.process_time()-started
        retain('worlds/'+name+'/NULL_MODEL.json',model)
        retain('worlds/'+name+'/GENERATED.json',trace)
        retain('worlds/'+name+'/OBSERVED.json',observed)
        retain('worlds/'+name+'/NULL_STATISTIC.json',null)
        timer=path/'TIMING.json'
        if not verification and not timer.exists():freeze(timer,dict(fit_cpu_seconds=fit_cpu,observed_cpu_seconds=observed_cpu,null_cpu_seconds=null_cpu))
        times.append(read(timer));completed.append(name)
        atomic(output/'PROGRESS.json',dict(phase='verify' if verification else 'execute',done=len(completed),total=len(s['selected']),complete_whole_pipeline_units=2*len(completed)))
    # Use the slowest completed unit, never a selected faster plant. Both fresh
    # passes and a 50 percent timing margin; no overlap/parallel credit assumed.
    worst=max(t['fit_cpu_seconds']+t['observed_cpu_seconds']+199*t['null_cpu_seconds'] for t in times)
    summary=dict(status='complete',cost_only=True,scientific_admission=False,primary=None,config=config,worlds=completed,
        complete_pipeline_units=2*len(completed),source_sessions=len(s['sessions']),source_rows=sum(len(x['rows']) for x in s['sessions']),
        projected_full_cpu_seconds=3*110*worst,forecast='110 times maximum fixed-world (null fit + observed pipeline + 199 generated pipelines), times two fresh passes, times 1.5',
        constructed=config==FIXTURE,full_matrix_unrun=True,original_labels_unchanged=True)
    retain('SUMMARY.json',summary)
    return dict(verified=True,fresh_generation_and_fit_replay=True,cost_only=True) if verification else summary


def execute(output,inputs,config):
    try:return compute(output,inputs,config)
    except InterruptedError:return dict(status='yielded',cost_only=True)

def verify(output,inputs,config):return compute(output,inputs,config,True)
