"""Frozen D33 screen specification curve with authenticated parent design reuse.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-7 read 2026-10-29.
NULL: zero own effect remains zero absent confounding. ALTERNATIVE: positive
and reversed own effects retain sign in known-answer worlds. Removing nuisance
can expose confounding; every setting is descriptive and retained. Unchanged
source roster, complete banks, invalid fits and source mutation refusals guard
selection and successful-only inference. No causal or independent replication.
"""
from pathlib import Path
import time
from threadpoolctl import threadpool_limits
from . import timing_d33_supported_stats as stats
from .timing_census import read,filehash
from .timing_p6 import write_equal,gzread,progress
from .batch_runtime import check_files

SETTINGS={'screen_only':('session_surprisal',),
          'cache_only':('on_screen',),
          'neither':('on_screen','session_surprisal')}
BASE=dict(card='D33.pair-calibration-supported.s',schema=1,draws=2000,
          permutations=200,seed=20261018,settings=list(SETTINGS))


def configuration(mode):
    if mode not in ('cost','full'):raise ValueError('Unknown specification mode')
    return dict(BASE,mode=mode)


def adjust(rows,setting):
    if setting not in SETTINGS:raise ValueError('Unknown specification')
    return [dict(r,**{key:0. for key in SETTINGS[setting]}) for r in rows]


def load(inputs):
    if set(inputs)!={'parent_completion','parent_landing'}:raise ValueError('Exact parent inputs required')
    root=Path(inputs['parent_completion']).resolve().parent
    done,plan,landing=read(inputs['parent_completion']),read(root/'PLAN.json'),read(inputs['parent_landing'])
    if (done['status']!='COMPLETE' or not done['fresh_process_verified']
        or not landing['full_write_through'] or landing['id']!='S15-D33-CALIBRATION-SUPPORTED-20261029'
        or filehash(root/'COMPLETE.json')!=landing['completion_sha256']
        or filehash(root/'PLAN.json')!=landing['plan_sha256']):raise ValueError('Unverified parent')
    check_files(plan['pins'])
    for name,digest in done['outputs'].items():
        if filehash(root/name)!=digest:raise ValueError('Parent output changed: '+name)
    if not read(root/'VERIFIED.json')['full_matching_calibration_and_statistical_replay']:
        raise ValueError('Parent source reconstruction absent')
    rows=gzread(root/'output/DESIGN.json.gz');parent=read(root/'output/PRIMARY.json')
    if len(rows)!=parent['coverage']['retained_words'] or len({r['writer'] for r in rows})!=parent['coverage']['retained_writers']:
        raise ValueError('Parent design coverage mismatch')
    return rows,parent


def one_pass(output,inputs,config,verifying=False,loader=load):
    if config!=configuration(config.get('mode')):raise ValueError('Frozen configuration required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    started=time.process_time();rows,parent=loader(inputs);source_cpu=time.process_time()-started
    binding=dict(config=config,inputs={k:filehash(v) for k,v in inputs.items()})
    if verifying:
        if read(output/'INPUTS.json')!=binding:raise ValueError('Input binding changed')
    else:write_equal(output/'INPUTS.json',binding)
    # Refuse corrupted scientific-independent probe metadata before writing any
    # timing observation. Reverification must not mask that refusal with a clock.
    if config['mode']=='cost' and verifying:
        expected=dict(mode='cost-only',coverage=parent['coverage'],settings=list(SETTINGS),
                      blocks_per_setting=1,scientific_admission=False)
        if read(output/'PROBE.json')!=expected:raise ValueError('Fresh complete specification replay differs')
    results={};timings={}
    for setting in SETTINGS:
        progress(output/'PROGRESS.json',dict(phase='verify' if verifying else 'execute',setting=setting,mode=config['mode']))
        target=output/('verify-inference' if verifying else 'inference')/setting
        start=time.process_time();seen=[]
        def checkpoint(item):
            seen.append(item['blocks'])
            if config['mode']=='cost':return True
            return (output/'YIELD_REQUEST.json').exists()
        value=stats.run(adjust(rows,setting),draws=config['draws'],permutations=config['permutations'],
            seed=config['seed'],checkpoint=target,checkpoint_callback=checkpoint)
        timings[setting]=time.process_time()-start
        if config['mode']=='cost':
            if value!=dict(status='yielded',completed_blocks=1,total_blocks=10) or seen!=[1]:
                raise ValueError('Incomplete first block: '+str(value.get('reason')))
            block=read(target/'block-00.json')
            if len(block['samples'])!=200 or len(block['controls'])!=20:raise ValueError('Incomplete reference block')
            if verifying and block!=read(output/'inference'/setting/'block-00.json'):
                raise ValueError('Fresh cost block differs')
        elif value.get('status')=='yielded':return value
        else:results[setting]=value
    timing=dict(source_cpu_seconds=source_cpu,inference_cpu_seconds=timings)
    write_equal(output/('VERIFY_TIMING.json' if verifying else 'EXECUTE_TIMING.json'),timing)
    if config['mode']=='cost':
        summary=dict(mode='cost-only',coverage=parent['coverage'],settings=list(SETTINGS),blocks_per_setting=1,
                     scientific_admission=False)
        name='PROBE.json'
        if verifying:
            previous=read(output/'EXECUTE_TIMING.json')
            forecast=6*(max(source_cpu,previous['source_cpu_seconds'])+10*sum(max(t,previous['inference_cpu_seconds'][s]) for s,t in timings.items()))+60
            write_equal(output/'FORECAST.json',dict(full_cpu_seconds=forecast,safety_factor=3,both_passes=True,
                                                   all_settings=True,scientific_admission=False))
    else:
        summary=dict(coverage=parent['coverage'],specifications=dict(both=parent['statistics'],**results),
                     parent_reused=True,original_question_open=True,descriptive=True,
                     paired_streams=True,causal_claim=False)
        name='SUMMARY.json'
    if verifying:
        if read(output/name)!=summary:raise ValueError('Fresh complete specification replay differs')
    else:write_equal(output/name,summary)
    progress(output/'PROGRESS.json',dict(phase='complete',mode=config['mode']))
    return dict(verified=True,full_fresh_replay=True,complete_specifications=config['mode']=='full') if verifying else dict(status='complete',mode=config['mode'])


def execute(output,inputs,config):
    with threadpool_limits(limits=2):return one_pass(output,inputs,config)


def verify(output,inputs,config):
    with threadpool_limits(limits=2):return one_pass(output,inputs,config,True)
