"""Counted first-tenth pilots for each frozen WA0.h1 follow-up; no scores saved.

DESIGN CHECK: LESSONS3-5, 2026-10-25. Every fixed member, full source cohort,
null-rebuild and bootstrap path runs. Pilot outcomes cannot select a member or
license a finding. Fresh replay repeats all work, and setup is conservatively
included in the linear forecast. Every card has its own cumulative 5400CPU cap.
"""
from pathlib import Path
import math,time
from threadpoolctl import threadpool_limits
from . import week3_identification_followups as followup
from .timing_census import read,filehash
from .timing_p6 import write_equal,progress

CONFIGS={k:dict(card='WA0.h1.'+k+'-timing',schema=1,mode='full',followup=k,draws=100)
         for k in followup.CONFIGS}
CONSTRUCTED={k:dict(v,mode='constructed',draws=8) for k,v in CONFIGS.items()}


def run(output,inputs,config,verification=False):
    if config not in [*CONFIGS.values(),*CONSTRUCTED.values()]:raise ValueError('fixed first-tenth follow-up workload required')
    started=time.perf_counter();cpu=time.process_time()
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    kind=config['followup'];original=(followup.CONFIGS if config['mode']=='full' else followup.CONSTRUCTED)[kind]
    data,expected=followup.load(inputs,original)
    pilot=dict(original,permutations=config['draws'])
    binding=dict(config=config,inputs={k:filehash(v) for k,v in sorted(inputs.items())})
    def checkpoint(member,fold,done,total):
        if (output.parent/'STOP').exists() or (output/'YIELD_REQUEST.json').exists():raise InterruptedError('cost pilot stop/yield requested')
        if done%25==0 or done==total:progress(output/'PROGRESS.json',dict(phase='verify' if verification else 'execute',member=member,fold=fold,done=done,total=total))
    with threadpool_limits(limits=2):result,detail=followup.analyze(data,pilot,checkpoint,expected)
    counts=dict(members={k:len(v) for k,v in result['members'].items()},sessions=result['corpus_sessions'],
        primary_writers=result['primary_writers'],folds_per_member=3,draws_per_fold=config['draws'])
    del result,detail
    timing=dict(wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu)
    if not all(math.isfinite(x) and x>0 for x in timing.values()):raise ValueError('invalid cost receipt')
    if binding['inputs']!={k:filehash(v) for k,v in sorted(inputs.items())}:raise ValueError('source changed during cost pilot')
    phase='VERIFY' if verification else 'EXECUTE'
    write_equal(output/(phase+'_TIME.json'),timing)
    work=dict(source=binding,work_counts=counts,scientific_admission=False,
        policy='all fixed members run; all scientific scores discarded; no pilot selection')
    if verification:
        if read(output/'WORK.json')!=work:raise ValueError('full fixed cost workload differs')
        prior=read(output/'EXECUTE_TIME.json');scale=original['permutations']/config['draws']
        write_equal(output/'FORECAST.json',dict(projected_execute_plus_verify={k:scale*(prior[k]+timing[k]) for k in timing},
            pilot_charged_cpu_seconds=prior['cpu_seconds']+timing['cpu_seconds'],cpu_ceiling_seconds=5400,
            scientific_admission=False,requires_owner_cumulative_cost_admission=True,
            scope='first-tenth linear forecast includes source load and fixed inference work conservatively; add every prior card charge'))
        return dict(verified=True,cost_only=True)
    write_equal(output/'WORK.json',work)
    return dict(status='complete',cost_only=True)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
