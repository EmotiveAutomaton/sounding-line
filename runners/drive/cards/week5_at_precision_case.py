"""Native replay of an entire retained failed AT2 chunk under scoring v4.

This is an engineering control on a previously dispatched scoring chunk, not
a new source selection or a scientific model comparison. All source rows and
the seeded fresh-forward sample remain exactly those in the failed plan.
"""
from pathlib import Path
from . import week5_at_scoring_v4 as scorer
from .timing_census import read,filehash
from .timing_p6 import write_equal


def run(output,inputs,config,verifying=False):
    if set(inputs)!={'failed_root'} or config:raise ValueError('Exact failed native case required')
    old=Path(inputs['failed_root']);plan=read(old/'PLAN.json')
    if not (old/'FAILED.json').is_file() or plan['module']!='runners.drive.cards.week5_at_scoring_v3':
        raise ValueError('Retained original scoring-v3 failure required')
    root=Path(output)
    binding=dict(original_plan_sha256=filehash(old/'PLAN.json'),original_failure_sha256=filehash(old/'FAILED.json'),
                 original_rows_sha256=filehash(plan['inputs']['rows']),
                 original_model_manifest_sha256=filehash(plan['inputs']['model_manifest']),numerical_spec=scorer.NUMERICAL_SPEC)
    write_equal(root/'CASE_BINDING.json',binding)
    value=(scorer.verify if verifying else scorer.execute)(root/'scores',plan['inputs'],plan['config'])
    if value.get('status')=='yielded':return value
    receipt=dict(engineering_replay_only=True,entire_original_chunk=True,unchanged_seeded_fresh_sample=True,
                 model=read(plan['inputs']['model_manifest'])['model'],words=read(root/'scores/SUMMARY.json')['words'],
                 numerical_spec=scorer.NUMERICAL_SPEC,original_failure_preserved=True)
    if verifying:
        if read(root/'FIXTURE.json')!=receipt:raise ValueError('Precision case replay differs')
        return dict(verified=True,**{k:v for k,v in value.items() if k!='verified'})
    write_equal(root/'FIXTURE.json',receipt)
    return dict(status='complete',engineering_replay_only=True)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)


if __name__=='__main__':
    import argparse,json,time,psutil
    p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('failed_root');p.add_argument('--verify',action='store_true');a=p.parse_args()
    from threadpoolctl import threadpool_limits
    began=time.process_time();wall=time.monotonic()
    with threadpool_limits(limits=2):
        result=(verify if a.verify else execute)(a.output,dict(failed_root=a.failed_root),{})
    mi=psutil.Process().memory_info()
    cost=dict(cpu_seconds=time.process_time()-began,wall_seconds=time.monotonic()-wall,
              peak_working_set_bytes=getattr(mi,'peak_wset',mi.rss),result=result)
    write_equal(Path(a.output)/('VERIFY_COST.json' if a.verify else 'EXECUTE_COST.json'),cost)
    print(json.dumps(cost))
