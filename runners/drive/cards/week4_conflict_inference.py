"""S6 complete known-answer banks, timing admission and human comparison.

DESIGN CHECK: LESSONS 3-5 / CONTROLS 1-7, 2026-11-04. Both primary models
use identical writer resamples. Known signed coefficients recover before human
fitting; incomplete banks, altered inputs and collinear focal terms refuse.
Cost mode substitutes outcomes and grants no scientific admission. Source
preparation, calibration, and human comparison have separate completion gates.
"""
from pathlib import Path
import time
import numpy as np
from threadpoolctl import threadpool_limits
from runners.stage14.common import atomic, digest, filehash, read
from . import week4_conflict_stats as stats
from .timing_p6 import gzread, write_equal
from .timing_pmap_source import completed
from .batch_runtime import check_files

MODES = ('constructed','calibration-cost','calibration-full','human-cost','human-full')


def configuration(mode):
    if mode not in MODES:
        raise ValueError('Unknown inference mode')
    return dict(card='W4-S6-inference',mode=mode,seed=20261102,draws=2000,permutations=200)


def authenticated(root):
    root = Path(root).resolve()
    c = read(root/'COMPLETE.json')
    if c['status'] != 'COMPLETE' or not c['fresh_process_verified']:
        raise ValueError('Dependency incomplete')
    for name, h in c['outputs'].items():
        if filehash(root/name) != h:
            raise ValueError('Dependency output changed')
    check_files(read(root/'PLAN.json')['pins'])
    return read(root/'output/SUMMARY.json')


def human_rows(inputs, full=False):
    keys = {'source_completion'} | ({'calibration_completion','cost_completion'} if full else set())
    if set(inputs) != keys:
        raise ValueError('Exact inference dependency bundle required')
    root = Path(inputs['source_completion']).resolve().parent
    summary = authenticated(root); plan=read(root/'PLAN.json')
    if plan['module'] != 'runners.drive.cards.week4_conflict_source' or plan['config']['mode'] != 'full':
        raise ValueError('Full authenticated conflict source required')
    rows = gzread(root/'output/PRIVATE_DESIGN.json.gz')
    if len(rows)!=summary['words'] or len({r['writer'] for r in rows})!=20:
        raise ValueError('Source support differs')
    if full:
        for key, mode in [('calibration_completion','calibration-full'),('cost_completion','human-cost')]:
            dep=Path(inputs[key]).resolve().parent; s=authenticated(dep);p=read(dep/'PLAN.json')
            if p['module']!=__name__ or p['config']!=configuration(mode):
                raise ValueError('Wrong validation producer')
            if key=='calibration_completion' and not s.get('calibration_pass'):
                raise ValueError('Complete calibration has not passed')
            if key=='cost_completion' and p['inputs']!={'source_completion':inputs['source_completion']}:
                raise ValueError('Cost used different source')
    return rows


def calibration_check(value, truth):
    if value['state']!='complete' or value['bootstrap_draws']!=2000 or value['permutation_draws']!=200:
        raise ValueError('Incomplete calibration bank')
    expected={'adjusted_own':truth['own_surprise'],'entropy':truth['entropy'],
              'negative_margin':truth['negative_margin']}
    for key,target in expected.items():
        if abs(value['point'][key]-target)>2e-8 or any(abs(r[key]-target)>2e-8 for r in value['bootstrap_values']):
            raise ValueError('Whole-bank analytic recovery failed: '+key)
    if any(r['invalid_draws'] for r in value['controls'].values()):
        raise ValueError('Calibration control fit undefined')
    return True


def one_pass(output, inputs, config, verifying=False):
    if config!=configuration(config.get('mode')):
        raise ValueError('Frozen inference configuration required')
    mode=config['mode']; output=Path(output); output.mkdir(parents=True,exist_ok=True)
    start=time.process_time(); binding=dict(config=config,inputs={k:filehash(v) for k,v in inputs.items()})
    if verifying:
        if read(output/'INPUTS.json')!=binding:
            raise ValueError('Inputs changed')
    else:
        write_equal(output/'INPUTS.json',binding)
    if mode=='constructed':
        if inputs:raise ValueError('No human input in native known-answer check')
        summary=dict(known_answers=stats.known_answers(),native_known_answers=True,human_scored=False)
        timings={}
    else:
        blocks=1 if mode.endswith('cost') else 10
        if mode.startswith('calibration'):
            if inputs:raise ValueError('Calibration takes no human input')
            tasks=[(name,*stats.world(name)) for name in stats.WORLDS]
        else:
            rows=human_rows(inputs,mode=='human-full')
            if mode=='human-cost':
                # Construct a full-rank timing response without fitting actual pauses.
                rng=np.random.default_rng(20261102)
                rows=[dict(r,log_pause=float(.2*r['own_surprise']+.1*r['entropy']+e))
                      for r,e in zip(rows,rng.normal(size=len(rows)))]
            tasks=[('human' if mode=='human-full' else 'human_shape_generated',rows,None)]
        setup=time.process_time()-start;timings={};results={};passed={}
        for name,rows,truth in tasks:
            began=time.process_time()
            def report(item):
                atomic(output/'PROGRESS.json',dict(phase='verify' if verifying else 'execute',world=name,**item))
            value=stats.run(rows,blocks=blocks,progress=report)
            timings[name]=time.process_time()-began
            if value.get('state') not in ('complete','cost_only'):
                # Keep invalidity as evidence; it must not be hidden by a timing probe.
                results[name]=value
            else:
                results[name]=value
                if mode=='calibration-full':passed[name]=calibration_check(value,truth)
            target=output/('PRIVATE_'+name+'.json')
            if verifying:
                if read(target)!=value:raise ValueError('Complete paired inference replay differs: '+name)
            else:write_equal(target,value)
        if mode.endswith('cost'):
            if any(v.get('state')!='cost_only' for v in results.values()):
                raise ValueError('Cost bank had undefined fits')
            summary=dict(mode=mode,worlds=len(tasks),blocks_per_world=1,human_scored=False,
                         full_reference_bank=False,scientific_admission=False)
        elif mode=='calibration-full':
            summary=dict(mode=mode,calibration_pass=len(passed)==6 and all(passed.values()),
                         worlds=len(tasks),bootstrap_draws_per_world=2000,reference_draws_per_family=200,
                         human_scored=False,algebraic_known_answers=True,empirical_power_established=False)
        else:
            value=results['human']
            summary=dict(mode=mode,state=value['state'],writers=20,observations=len(tasks[0][1]),
                         statistics=value.get('statistics'),controls=value.get('controls'),
                         primary=value.get('statistics',{}).get('adjusted_own'),
                         reason=value.get('reason'),human_scored=True,descriptive=True,
                         revision_extension='held on S2',causal_claim=False)
        timing=dict(setup_cpu_seconds=setup,work_cpu_seconds=timings)
        write_equal(output/('VERIFY_TIMING.json' if verifying else 'EXECUTE_TIMING.json'),timing)
        if verifying and mode.endswith('cost'):
            previous=read(output/'EXECUTE_TIMING.json')
            forecast=6*(max(setup,previous['setup_cpu_seconds'])+
                        10*sum(max(t,previous['work_cpu_seconds'][n]) for n,t in timings.items()))+30
            write_equal(output/'FORECAST.json',dict(full_cpu_seconds=forecast,safety_factor=3,
                        includes_fresh_replay=True,includes_all_banks=True))
    if verifying:
        if read(output/'SUMMARY.json')!=summary:raise ValueError('Inference summary differs')
    else:write_equal(output/'SUMMARY.json',summary)
    return dict(verified=True,full_fresh_replay=True,mode=mode) if verifying else summary


def execute(output,inputs,config):
    with threadpool_limits(limits=1):return one_pass(output,inputs,config)


def verify(output,inputs,config):
    with threadpool_limits(limits=1):return one_pass(output,inputs,config,True)
