"""Counted-ready actual execute/guard-pause/reexecute/fresh-verify fixture.

The only permitted inputs are an explicitly constructed failed-case plan and
literal character-token rows. Resource snapshots are constructed; native PID,
real tiny-model forwards and guard state transitions are actual.
"""
from pathlib import Path
from types import FunctionType
import json
import time
from . import week5_at_precision_guard as old_guard
from . import week5_at_precision_case as old_case
from . import week5_at_scoring_v4 as old_score
from . import week5_at_precision_guard_v2 as guard
from . import week5_at_scoring_v5 as scorer
from .week5_at_scoring_v4_fixture import loader
from .timing_census import read,filehash
from .timing_p6 import gzread,write_equal


def fixture_inputs(inputs):
    if set(inputs)!={'failed_root'}:raise ValueError('Only the declared constructed case is permitted')
    root=Path(inputs['failed_root']);plan=read(root/'PLAN.json')
    if read(root/'FAILED.json')!={'fixture_only':True,'reason':'constructed original-v3 failure marker'}:
        raise ValueError('Real failed cases prohibited in this fixture')
    manifest=read(plan['inputs']['model_manifest']);rows=gzread(plan['inputs']['rows'])
    expected=[dict(row_key=str(i),final_prefix='a '*i,target=' b') for i in range(18)]
    if rows!=expected or manifest!=dict(model='constructed-neox',family='neox',revision='fixture'):
        raise ValueError('Only literal tiny-model fixture inputs permitted')
    if plan['module']!='runners.drive.cards.week5_at_scoring_v3' or plan['config']!={'context_length':64}:
        raise ValueError('Constructed original numerical contract changed')


def preserved(output):
    root=Path(output)/'scores'
    names=['COST.json','BINDING.json','INDEX.json','SUMMARY.json']
    names+=sorted(p.name for p in root.glob('block-*.json'))
    return {name:filehash(root/name) for name in names}


def run(output,inputs,config,verifying=False):
    fixture_inputs(inputs)
    if config!={'mode':'counted_resume'}:raise ValueError('Declared counted resume fixture required')
    root=Path(output);root.mkdir(parents=True,exist_ok=True)
    high=dict(commit_headroom_bytes=30*old_guard.GIB,ram_available_bytes=30*old_guard.GIB)
    low=dict(high,commit_headroom_bytes=25*old_guard.GIB)
    checkpoint=root/'INITIAL_SCORE_HASHES.json';pause=root/'INTENTIONAL_VERIFY_PAUSE.json'
    previous=read(checkpoint) if checkpoint.exists() else None
    initial=previous is None
    original_load,successor_load=old_score.load_model,scorer.load_model
    old_score.load_model=loader;scorer.load_model=loader
    try:
        if verifying and not pause.exists():
            write_equal(pause,dict(fixture_only=True,stage='after complete execution before verification',model_loads_permitted=0))
            def forbidden(*args):raise ValueError('Guard refusal reached model invocation')
            call=FunctionType(old_guard.run.__code__,dict(old_guard.run.__globals__,memory=lambda:low,invoke=forbidden),
                               old_guard.run.__name__,old_guard.run.__defaults__,old_guard.run.__closure__)
            value=call(root,inputs,{},True)
            if value.get('status')!='yielded' or value.get('model_loads')!=0:
                raise ValueError('Completed execution did not pause before model loading')
            if preserved(root)!=previous:raise ValueError('Guard pause changed completed scoring bytes')
            return value
        invoke=(lambda out,i,c,v:old_case.run(out,i,c,v)) if initial else guard.invoke
        call=FunctionType(old_guard.run.__code__,dict(old_guard.run.__globals__,memory=lambda:high,invoke=invoke),
                           old_guard.run.__name__,old_guard.run.__defaults__,old_guard.run.__closure__)
        value=call(root,inputs,{},verifying)
    finally:
        old_score.load_model=original_load;scorer.load_model=successor_load
    if initial:
        if verifying or value.get('status')!='complete':raise ValueError('Expected complete original-v4 execution')
        write_equal(checkpoint,preserved(root))
    elif preserved(root)!=previous:raise ValueError('Idempotent successor changed old score or cost bytes')
    if verifying:
        if not value.get('verified') or not pause.exists():raise ValueError('Required actual pause/fresh replay missing')
        receipts=[read(p) for p in (root/'scores/invocation_costs').glob('*.json')]
        if not any(r['phase']=='execute' and r['status']=='complete' for r in receipts):
            raise ValueError('Resumed complete execution cost missing')
        if not any(r['phase']=='verify' and r['status']=='verified' for r in receipts):
            raise ValueError('Fresh verification cost missing')
        write_equal(root/'RESUME_FIXTURE.json',dict(fixture_only=True,legacy_complete_cost_preserved=True,
                    complete_execute_guard_pause_resume=True,unchanged_score_bytes=True,
                    actual_fresh_forward_count=value['fresh_forward_count'],numerical_spec=scorer.NUMERICAL_SPEC,
                    runtime_counted_chain_required=True))
        return dict(verified=True,actual_complete_pause_resume_replay=True)
    return dict(status='complete',fixture_only=True)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('failed_root');p.add_argument('--verify',action='store_true');a=p.parse_args()
    began=time.process_time();value=(verify if a.verify else execute)(a.output,dict(failed_root=a.failed_root),dict(mode='counted_resume'))
    write_equal(Path(a.output)/'native_fixture_costs'/f'{time.time_ns()}.json',dict(process_cpu_seconds=time.process_time()-began,result=value))
    print(json.dumps(value))
