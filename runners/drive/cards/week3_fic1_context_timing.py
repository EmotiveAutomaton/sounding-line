"""Complete-source FIC1 context construction timing, without human scores.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-7 reread 2026-10-27.
NULL/ALTERNATIVE require identical source seals, exact observed reconstruction,
fixed original population, all donor rotations and fresh nuisance fits. Missing
donor coverage is retained, never silently filtered. Native construction checks
precede this measured cost pass; no identification or scientific admission.
"""
from pathlib import Path
import time
from threadpoolctl import threadpool_limits
from runners.stage14.common import read,filehash,freeze,atomic
from . import week3_fic1_context as context

CONFIG=dict(context.CONFIG,card='FIC1-context-timing',mode='timing',
            writers=24,sessions=990,word_limits=[500,1000,2000])
CONSTRUCTED=dict(context.CONFIG,card='FIC1-context-timing-native')


def run(output,inputs,config,verification=False):
    if config not in (CONFIG,CONSTRUCTED):raise ValueError('fixed context timing configuration required')
    start=time.process_time();output=Path(output);output.mkdir(parents=True,exist_ok=True)
    if config==CONSTRUCTED:
        if set(inputs)!={'fixture'}:raise ValueError('constructed fixture required')
        fp=Path(inputs['fixture']);data=read(fp);bindings={str(fp.resolve()):filehash(fp)}
    else:
        data,bindings=context.reconstruction.load(inputs,context.reconstruction.CONFIG)
    if len(data['units'])!=config['sessions'] or len({u['writer'] for u in data['units']})!=config['writers']:
        raise ValueError('complete original population required')
    loaded=time.process_time()-start
    atomic(output/'PROGRESS.json',dict(phase='verify-context' if verification else 'context',done=0,total=1))
    with threadpool_limits(limits=1):
        if config==CONFIG:
            observed=context.reconstruction.rebuild(data['units'],data['rows'],data['dictionary'],config['word_limits'])
            context.reconstruction.verify_observed(observed,data['profiles'],data['prefixes'])
        value=context.prepare(data,config)
    constructed=time.process_time()-start-loaded
    # Preparation support, not accuracy, is the only corpus-level readout here.
    coverage={name:{g:[r['context'][name][g]['state'] for r in value['rotations']] for g in context.gallery.GENRES} for name in value['rosters']}
    summary=dict(card=config['card'],constructed=config==CONSTRUCTED,sessions=config['sessions'],writers=config['writers'],
        complete_context_rebuilt=True,context_gallery_support=coverage,
        identification_computed=False,full_calibration_complete=False,scientific_admission=False)
    for name,v in [('CONTEXT.json',value),('SUMMARY.json',summary),('BINDING.json',dict(config=config,inputs=bindings))]:
        p=output/name
        if verification:
            if read(p)!=v:raise ValueError('complete context timing replay differs: '+name)
        else:freeze(p,v)
    cost=output/('VERIFY_COST.json' if verification else 'EXECUTE_COST.json')
    if not cost.exists():freeze(cost,dict(load_cpu_seconds=loaded,construction_cpu_seconds=constructed,total_cpu_seconds=time.process_time()-start))
    atomic(output/'PROGRESS.json',dict(phase='verify-context' if verification else 'context',done=1,total=1))
    if verification:return dict(verified=True,complete_context_rebuilt=True,all_inputs_replayed=True)
    return dict(status='complete',scientific_admission=False)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
