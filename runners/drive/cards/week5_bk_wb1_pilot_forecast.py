"""Frozen conservative forecast from the complete original five-percent pilot."""
from pathlib import Path
import math
from runners.stage14.common import read,filehash
from . import week5_bk_wb1_source as source
from . import week5_bk_wb1_coverage_pilot as pilot


def run(output,inputs,config,verifying=False):
    if set(inputs)!={'pilot_root'} or config:raise ValueError('One verified original coverage pilot required')
    root,plan=source.completed(inputs['pilot_root'],pilot.__name__)
    receipt=read(root/'output/COVERAGE_PILOT.json')
    if receipt['work_fraction']!=.05 or receipt['references_per_scope_side']!=10 or receipt['total_per_scope_side']!=200 or len(receipt['reference_work'])!=40:
        raise ValueError('Incomplete five-percent global reference work')
    costs={phase:read(root/'output'/(phase+'_COST.json'))['process_cpu_seconds'] for phase in ('EXECUTE','VERIFY')}
    if any(type(c) not in (float,int) or not math.isfinite(c) or c<=0 for c in costs.values()):
        raise ValueError('Positive complete measured work required before projection')
    forecast=dict(pilot_complete_sha256=filehash(root/'COMPLETE.json'),phase_costs=costs,
        projected_full_coverage_cpu_seconds=2*3*max(costs.values())/.05,
        both_passes=True,safety_multiplier=3,work_fraction=.05,
        includes_full_bootstrap_upward_scaling=True,
        excluded_additional='All prior charges, source, effects cost probe, effects encoding/kernels, interpreter startup and runtime coordination',
        scientific_admission=False,automatically_authorizes_start=False)
    source.checked(Path(output)/'FORECAST.json',forecast,verifying)
    return dict(verified=True,exact_frozen_forecast=True) if verifying else dict(status='complete',scientific_admission=False)


def execute(output,inputs,config):return source.timed(run,output,inputs,config,False)
def verify(output,inputs,config):return source.timed(run,output,inputs,config,True)
