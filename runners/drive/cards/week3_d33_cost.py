"""Exact first-block D33 cost probe, with no scientific verdict.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-7 reread 2026-10-29.
NULL/ALTERNATIVE use identical source selection and unchanged inference. Stop
after one whole block, reconstruct it freshly, and preserve every invalid fit.
Changed inputs, incomplete blocks or unequal fresh values refuse admission.
"""
from pathlib import Path
import time
from threadpoolctl import threadpool_limits
from . import timing_d33_calibrated as base
from .timing_census import read,filehash
from .timing_p6 import write_equal,progress

CONFIG = dict(card='D33-week3-cost',schema=1,base_config=base.CONFIG)


def one_pass(output,inputs,config,verifying=False,prepare=base.prepared):
    if config!=CONFIG:raise ValueError('Frozen first-block probe required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    start=time.process_time()
    rows,roster,tuning,covariates=prepare(output,inputs,base.CONFIG,verifying)
    source_cpu=time.process_time()-start
    progress(output/'PROGRESS.json',dict(phase='verify-first-block' if verifying else 'first-block',rows=len(rows)))
    observed=[]
    def stop(item):
        if item['blocks']!=1:raise ValueError('Probe exceeded first complete block')
        observed.append(item)
        return True
    # Verification uses a distinct directory: no retained inferential block is reused.
    target=output/('verify-inference' if verifying else 'inference')
    start=time.process_time()
    stats=base.original.run(rows,draws=base.CONFIG['bootstrap_draws'],permutations=base.CONFIG['permutations'],
        seed=base.CONFIG['seed'],checkpoint=target,checkpoint_callback=stop)
    inference_cpu=time.process_time()-start
    if stats!=dict(status='yielded',completed_blocks=1,total_blocks=10) or len(observed)!=1:
        raise ValueError('First inference block did not complete: '+str(stats.get('reason')))
    block=read(target/'block-00.json')
    if len(block['samples'])!=200 or len(block['controls'])!=20:
        raise ValueError('Incomplete fixed inference block')
    if filehash(target/'block-00.json')!=read(target/'block-00.receipt.json')['sha256']:
        raise ValueError('Block seal changed')
    result=dict(mode='cost-only',coverage=roster['coverage'],complete_blocks=1,total_blocks=10,
                bootstrap_draws_timed=200,permutations_per_family_timed=20,scientific_admission=False,
                input_hashes={k:filehash(v) for k,v in inputs.items()},config=config)
    if verifying:
        if read(output/'PROBE.json')!=result or read(output/'inference/block-00.json')!=block:
            raise ValueError('Fresh first-block replay differs')
    else:write_equal(output/'PROBE.json',result)
    timing=dict(source_cpu_seconds=source_cpu,inference_cpu_seconds=inference_cpu)
    write_equal(output/('VERIFY_TIMING.json' if verifying else 'EXECUTE_TIMING.json'),timing)
    if verifying:
        first=read(output/'EXECUTE_TIMING.json')
        forecast=6*(max(source_cpu,first['source_cpu_seconds'])+10*max(inference_cpu,first['inference_cpu_seconds']))+120
        write_equal(output/'FORECAST.json',dict(full_cpu_seconds=forecast,both_passes=True,safety_factor=3,
                    full_blocks=10,scientific_admission=False,full_execution_admitted=False))
    return dict(verified=True,complete_first_block_replay=True) if verifying else dict(status='complete',timing_only=True)


def execute(output,inputs,config):
    with threadpool_limits(limits=2):return one_pass(output,inputs,config)


def verify(output,inputs,config):
    with threadpool_limits(limits=2):return one_pass(output,inputs,config,True)
