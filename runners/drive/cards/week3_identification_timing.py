"""WA0 whole-design first-tenth CPU timing; no scientific output or admission.

DESIGN CHECK: LESSONS 3-5 reread 2026-10-25. Exact fixed source population,
all original/h1 channels and both genre arms run through one tenth of their
draws. Timing cannot license a result or replace the complete 1000-draw run.
Source change and nonfinite cost refuse completion. Fresh verification repeats
the same workload but compares deterministic aggregate work counts, not clocks.
"""
from pathlib import Path
import math
import time

from . import week3_identification as literal
from . import week3_identification_crossfit as corrected
from .timing_census import read,filehash
from .timing_p6 import write_equal,progress

CONFIG=dict(card='WA0-timing',schema=1,mode='full',draws=100,bootstrap_draws=2000,seed=20261026)
CONSTRUCTED=dict(CONFIG,mode='constructed',draws=8,bootstrap_draws=200)


def run(output,inputs,config,verification=False):
    if config not in (CONFIG,CONSTRUCTED):raise ValueError('fixed whole-design cost pilot required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    original=literal.CONFIG if config['mode']=='full' else literal.CONSTRUCTED
    data=literal.load(inputs,original)
    binding=dict(config=config,inputs={k:filehash(v) for k,v in sorted(inputs.items())})
    counts={};times={}
    for name,module in [('literal',literal),('independent',corrected)]:
        frozen=module.CONFIG if config['mode']=='full' else module.CONSTRUCTED
        pilot=dict(frozen,permutations=config['draws'],genre_permutations=config['draws'],bootstrap_draws=config['bootstrap_draws'])
        started=time.perf_counter();cpu=time.process_time()
        def checkpoint(phase,done,total):
            if (output.parent/'STOP').exists() or (output/'YIELD_REQUEST.json').exists():raise InterruptedError('cost pilot stop/yield requested')
            if done%25==0 or done==total:progress(output/'PROGRESS.json',dict(phase=name+'-'+phase,done=done,total=total))
        result,detail=module.analyze(data,pilot,checkpoint)
        times[name]=dict(wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu)
        counts[name]=dict(channels=len(result['channels']),genres=len(result['genres']),
                          genre_contrasts=len(result['genre_sensitivity']),draws=config['draws'])
        del result,detail
    if not all(math.isfinite(t[k]) and t[k]>0 for t in times.values() for k in t):raise ValueError('invalid whole-design timing')
    phase='VERIFY' if verification else 'EXECUTE'
    write_equal(output/(phase+'_TIME.json'),dict(times=times,source=binding))
    expected=dict(work_counts=counts,source=binding,scientific_admission=False,
                  result_policy='cost-only; all computed scores discarded; complete1000-draw main remains required')
    if verification:
        if read(output/'WORK.json')!=expected:raise ValueError('complete cost workload replay differs')
        execute=read(output/'EXECUTE_TIME.json')['times']
        scale=1000/config['draws'] if config['mode']=='full' else 64/config['draws']
        projection={name:{k:scale*(execute[name][k]+times[name][k]) for k in times[name]} for name in times}
        write_equal(output/'FORECAST.json',dict(projected_execute_plus_verify=projection,
            total_projected_cpu_seconds=sum(x['cpu_seconds'] for x in projection.values()),
            pilot_charged_cpu_seconds=sum(x['cpu_seconds'] for x in execute.values())+sum(x['cpu_seconds'] for x in times.values()),
            scientific_admission=False,requires_owner_cumulative_budget_admission=True,
            forecast='first-tenth whole-design cost scaled linearly; source and fixed setup repeated, conservative'))
        return dict(verified=True,cost_only=True)
    write_equal(output/'WORK.json',expected)
    return dict(status='complete',cost_only=True)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
