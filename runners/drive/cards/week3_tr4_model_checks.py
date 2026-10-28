"""Constructed native execution of all TR4 models, never human inference.

DESIGN CHECK: LESSONS 3-5 read 2026-10-27. Equal-share NULL is exactly zero;
stable skew must not reward adaptation. Both planted directions of persistent
change must reward tracking. Missing records retain missing loss. Failed known
answers refuse, not a scientific negative. Exact full replay is mandatory.
"""
from pathlib import Path
import time
import numpy as np
from . import week3_tr4_models as models
from .timing_census import read
from .timing_p6 import write_equal, progress

CONFIG = dict(card='TR4-model-checks',seed=20261026,sessions=24)


def checks():
    uniform=[250]*4; high=[850,50,50,50]
    patterns=dict(uniform=[uniform]*24,stable=[high]*24,
                  rising=[uniform]*12+[high]*12,falling=[high]*12+[uniform]*12)
    values={}
    for name,sequence in patterns.items():
        forecasts=models.forecast(sequence)
        losses={key:[models.log_loss(x,r['probabilities'][key]) for x,r in zip(sequence,forecasts)] for key in models.NAMES}
        gain=float(np.mean(np.asarray(losses['whole'][16:])-np.asarray(losses['kalman'][16:])))
        values[name]=dict(counts=sequence,forecasts=forecasts,losses=losses,gain=gain)
    gates=dict(exact_uniform=values['uniform']['gain']==0.,stable_not_improved=values['stable']['gain']<=0.,
               rising_tracked=values['rising']['gain']>.05,falling_tracked=values['falling']['gain']>.05)
    if not all(gates.values()):raise ValueError('TR4 constructed model gate failed: '+str(gates))
    return dict(cases=values,gates=gates,scientific_admission=False,scope='Deterministic model checks only; statistical calibration and all human comparisons remain separate')


def run(output,inputs,config,verification=False):
    if inputs or config!=CONFIG:raise ValueError('frozen constructed model checks required')
    started=time.process_time();output=Path(output);output.mkdir(parents=True,exist_ok=True)
    value=checks()
    for name,data in [('CHECKS.json',value),('BINDING.json',dict(config=config,inputs=inputs))]:
        if verification:
            if read(output/name)!=data:raise ValueError('complete constructed model replay differs')
        else:write_equal(output/name,data)
    progress(output/'PROGRESS.json',dict(phase='verified' if verification else 'complete',done=4,total=4))
    if verification:return dict(verified=True,complete_input_replay=True,scientific_admission=False)
    if not (output/'TIMING.json').exists():write_equal(output/'TIMING.json',dict(cpu_seconds=time.process_time()-started))
    return dict(status='complete',scientific_admission=False,gates=value['gates'])


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
