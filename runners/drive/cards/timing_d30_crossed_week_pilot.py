"""Measure corrected D30.p cost on the whole fixed design, not scientific scores.

DESIGN CHECK: LESSONS 3-5 October 19. Whole design and exact optimizer must
reconstruct, every attempted fit must converge without dropping a draw, and
unchanged original point must agree to 1e-6. Under both null and alternative,
cost and parity admission are identical. Small draw counts carry no interval or
scientific state. Over-budget work stays operationally unadmitted.
"""
import math
import time
from pathlib import Path

from . import timing_d30_crossed_week as main
from .timing_census import read, filehash
from .timing_stats import bind, check_binding
from .timing_p6 import gzip_equal, gzread
from runners.stage14.common import freeze, atomic

CONFIG=dict(card='D30.p-week-pilot',bootstrap_pilot_draws=5,permutation_pilot_draws=5,seed=20261017,permutation_seed=20261018)


def source(inputs,config):
    if config!=CONFIG or any(type(config.get(k)) is not type(v) for k,v in CONFIG.items()):
        raise ValueError('exact corrected pilot configuration required')
    return main.source(inputs,main.CONFIG)


def computation(matrices,output=None):
    timings=[]
    def fit(matrix):
        started=time.monotonic();value=main.checked_fit(matrix)
        timings.append(time.monotonic()-started)
        if output:
            atomic(Path(output)/'FIT_PROGRESS.json',dict(completed_fits=len(timings),at=time.time()))
        return value
    cfg=dict(main.CONFIG,bootstrap_draws=CONFIG['bootstrap_pilot_draws'],permutations=CONFIG['permutation_pilot_draws'])
    return main.compute(matrices,cfg,fit_function=fit),timings


def execute(output,inputs,config):
    output=Path(output);started=time.monotonic()
    if (output/'TIMING_BINDINGS.json').exists():return verify(output,inputs,config)['primary']
    matrices,evidence=source(inputs,config);source_seconds=time.monotonic()-started
    fitted,times=computation(matrices,output)
    delta=fitted['points']['primary']['effect']-evidence['pilot_point']['effect']
    if abs(delta)>1e-6:raise ValueError('stable estimate differs materially from original pilot')
    active=sum(matrices[k] is not None for k in main.ARMS)
    count=active*(main.CONFIG['bootstrap_draws']+1)+main.CONFIG['permutations']
    projected=2*source_seconds+2*count*max(times)
    elapsed=time.monotonic()-started
    report=dict(instrument_only=True,scientific_main_admitted=False,card=config['card'],
        completed_fits=len(times),active_arms=active,source_seconds=source_seconds,fit_seconds=times,
        projected_main_execution_replay_seconds=projected,projection_method='two source reconstructions plus twice every fit at slowest measured whole-design fit',
        original_pilot_seconds=evidence['charged_pilot_seconds'],execute_seconds=elapsed,
        main_fits_per_execution=count,point_parity=True,point_absolute_difference=abs(delta),
        main_total_ceiling_seconds=main.CAP_SECONDS,
        limitation='Five bootstrap and five permutation draws measure cost and numerical behavior only; no scientific scores')
    gzip_equal(output/'DESIGNS.json.gz',dict(matrices=matrices,evidence=evidence))
    freeze(output/'FITS.json',fitted);freeze(output/'PILOT.json',report)
    bind(output,inputs,config,['DESIGNS.json.gz','FITS.json','PILOT.json'])
    return report


def verify(output,inputs,config):
    output=Path(output);check_binding(output,inputs,config)
    matrices,evidence=source(inputs,config)
    if gzread(output/'DESIGNS.json.gz')!=dict(matrices=matrices,evidence=evidence):raise ValueError('pilot source replay differs')
    fitted,_=computation(matrices)
    if fitted!=read(output/'FITS.json'):raise ValueError('pilot numerical replay differs')
    report=read(output/'PILOT.json');times=report['fit_seconds']
    count=sum(matrices[k] is not None for k in main.ARMS)*(main.CONFIG['bootstrap_draws']+1)+main.CONFIG['permutations']
    if (not times or any(not math.isfinite(t) or t<=0 for t in times)
            or report['projected_main_execution_replay_seconds']!=2*report['source_seconds']+2*count*max(times)
            or report['completed_fits']!=len(times) or report['main_fits_per_execution']!=count):
        raise ValueError('pilot cost projection does not reconstruct')
    return dict(verified=True,primary=report,fresh_replayed_fits=len(times))
