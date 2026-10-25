"""PP1 whole-design cost admission; outputs no pilot scientific scores.

Five full writer-refit bootstrap workloads and 100 profile permutations per
genre project the unchanged main counts and complete fresh replay. Prior jobs,
this pilot and source preparation remain charges the owner must add. A failed
fit is not retried or excluded to improve a forecast.
"""
from pathlib import Path
import time

from threadpoolctl import threadpool_limits

from . import week3_pause_instrument as main
from .timing_census import read
from .timing_p6 import write_equal

CONFIG=dict(mode='corpus',seed=20261026,bootstrap_draws=5,permutations=100)


def measure(output,inputs,config,verification=False):
    if set(config)!=set(CONFIG) or config['mode'] not in {'constructed','corpus'} or config['seed']!=20261026:
        raise ValueError('frozen PP1 timing configuration required')
    if config['mode']=='corpus' and config!=CONFIG:
        raise ValueError('full PP1 timing workload required')
    if min(config['bootstrap_draws'],config['permutations'])<2:
        raise ValueError('positive timing control denominator required')
    start=time.process_time(); rows=main.load(inputs,config['mode']);setup=time.process_time()-start
    times={g:{p:[] for p in ('observed','bootstrap','identification')} for g in ('creative','argumentative')}
    with threadpool_limits(limits=1):
        result,details=main.compute(output,rows,config,verification,lambda g,p,s:times[g][p].append(s))
    timing=dict(setup_cpu_seconds=setup,work_cpu_seconds=time.process_time()-start,fit_seconds=times)
    timing['projected_main_and_fresh_replay_cpu_seconds']=2*(setup+sum(max(t['observed'])+2000*max(t['bootstrap'])+1000/config['permutations']*max(t['identification']) for t in times.values()))
    work=dict(sessions=len(rows),genres=2,bootstrap_draws_per_genre=config['bootstrap_draws'],permutations_per_genre=config['permutations'],
              complete_work_sha256=main.json_digest(dict(result=result,details=details)))
    return work,timing


def execute(output,inputs,config):
    work,timing=measure(output,inputs,config)
    result=dict(card='PP1-cost-pilot',status='cost_probe_complete',scientific_admission=False,work=work,timing=timing,
                ceiling_cpu_seconds=3600,excludes='prior charges, this pilot and source preparation; owner adds all before admission')
    write_equal(Path(output)/'PP1_PILOT_RESULT.json',result)
    return result


def verify(output,inputs,config):
    work,timing=measure(output,inputs,config,True)
    if read(Path(output)/'PP1_PILOT_RESULT.json')['work']!=work:
        raise ValueError('PP1 complete pilot replay differs')
    return dict(verified=True,scientific_admission=False,verification_timing=timing)
