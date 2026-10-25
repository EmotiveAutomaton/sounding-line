"""WA1 whole-roster first-tenth timing; scores discarded, not admitted.

DESIGN CHECK: LESSONS 3-5. All86original cells, recalibration and both original
4000-draw intervals run. Only repeated worlds reduce from1000to100 for timing.
Fresh verification repeats the entire workload. This measures execution cost,
never sensitivity or corrected scientific results. Source/prep/pilot/full
execution and replay share the parent's7200CPU-second allowance.
"""
from pathlib import Path
import math
import time

from threadpoolctl import threadpool_limits

from . import week3_adapter_audit as analysis
from .timing_census import read,filehash
from .timing_p6 import write_equal,progress

CONFIG=dict(card='WA1-timing',schema=1,mode='full',worlds=100,seed=20261026)
CONSTRUCTED=dict(CONFIG,mode='constructed',worlds=8)


def run(output,inputs,config,verification=False):
    if config not in (CONFIG,CONSTRUCTED):raise ValueError('fixed complete-roster timing contract required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    main=analysis.CONFIG if config['mode']=='full' else analysis.CONSTRUCTED
    workload=dict(main,worlds=config['worlds'])
    def tick(phase,done,total):
        if (output.parent/'STOP').exists() or (output/'YIELD_REQUEST.json').exists():raise InterruptedError('WA1 cost stop requested')
        progress(output/'PROGRESS.json',dict(phase=('verify_' if verification else '')+phase,done=done,total=total))
    started=time.perf_counter();cpu=time.process_time()
    cells=analysis.load(inputs,main)
    with threadpool_limits(limits=1):summary,detail=analysis.analyze(cells,workload,tick)
    timing=dict(cpu_seconds=time.process_time()-cpu,wall_seconds=time.perf_counter()-started)
    if any(not math.isfinite(t) or t<=0 for t in timing.values()):raise ValueError('nonfinite or empty workload timing')
    counts=dict(cells=len(cells),population_groups=summary['population_groups'],worlds=config['worlds'],
        bootstrap_draws=main['bootstrap_draws'],plants=len(main['plants']),variants=len(analysis.VARIANTS),
        comparisons_per_variant=4)
    del summary,detail
    binding=dict(config=config,inputs={k:filehash(v) for k,v in inputs.items()})
    record=dict(work_counts=counts,source=binding,scientific_admission=False,
        result_policy='Whole-roster complete procedure at one tenth worlds; all computed scientific scores discarded.')
    if verification:
        if read(output/'WORK.json')!=record:raise ValueError('fresh full timing workload differs')
        write_equal(output/'VERIFY_TIME.json',timing)
        before=read(output/'EXECUTE_TIME.json');scale=main['worlds']/config['worlds']
        write_equal(output/'FORECAST.json',dict(
            pilot_charged_cpu_seconds=before['cpu_seconds']+timing['cpu_seconds'],
            projected_execute_plus_verify={k:scale*(before[k]+timing[k]) for k in timing},
            shared_cpu_ceiling_seconds=7200,scientific_admission=False,requires_owner_cumulative_budget_admission=True,
            projection='Linear first-tenth scaling includes fixed source/calibration work in every tenth; cached bootstrap setup is charged in both fresh processes.'))
        return dict(verified=True,cost_only=True)
    write_equal(output/'EXECUTE_TIME.json',timing)
    write_equal(output/'WORK.json',record)
    return dict(status='complete',cost_only=True)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
