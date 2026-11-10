"""Native admission refusal, actual sealed-block yield and owned hard exit."""
from pathlib import Path
import time,subprocess,sys,json,os
from . import week5_at_precision_guard as guard
from . import week5_at_scoring_v4 as scorer
from .week5_at_scoring_v4_fixture import loader
from .timing_census import read
from .timing_p6 import write_equal


def run(output,inputs,config,verifying=False):
    if inputs or config:raise ValueError('Resource proof takes no human data')
    root=Path(output)/('verify-proof' if verifying else 'execute-proof');g=guard.GIB
    high=dict(commit_headroom_bytes=30*g,ram_available_bytes=30*g)
    low=dict(commit_headroom_bytes=int(6.5*g),ram_available_bytes=30*g)
    for snapshot,expected in [(high,'admit'),(dict(high,commit_headroom_bytes=25*g),'refuse')]:
        if guard.action(snapshot,admission=True)!=expected:raise ValueError('Native admission boundary differs')
    if guard.action(low)!='request_yield' or guard.action(dict(low,commit_headroom_bytes=5*g))!='terminate' or guard.action(high,60)!='terminate':
        raise ValueError('Floor or bounded grace differs')
    owned=guard.identity()
    if owned['pid']!=os.getpid() or not owned['creation_time'] or not owned['executable']:raise ValueError('Direct native identity missing')
    original_memory,original_invoke,original_loader,original_progress=guard.memory,guard.invoke,scorer.load_model,scorer.progress
    calls=[];state=[dict(high,commit_headroom_bytes=25*g)]
    guard.memory=lambda:state[0]
    def forbidden(*args):calls.append('forbidden_load');raise ValueError('Refusal reached model handler')
    guard.invoke=forbidden
    try:
        result=guard.execute(root/'refused',{}, {})
        if result.get('status')!='yielded' or result.get('model_loads')!=0 or calls:raise ValueError('Preload refusal failed')
        state[0]=high;scorer.load_model=loader
        rows=[dict(row_key=str(i),final_prefix='a '*i,target=' b') for i in range(18)]
        def invoke(out,inputs,config,verifying):
            calls.append('actual_tiny_handler')
            return scorer.score_batch(Path(out)/'scores',rows,dict(model='constructed-gpt2',family='gpt2',revision='fixture'),context_length=64)
        guard.invoke=invoke
        def progress(path,value):
            original_progress(path,value)
            if value['words']==8:
                state[0]=low;until=time.monotonic()+3
                while not (Path(path).parent/'YIELD_REQUEST.json').exists():
                    if time.monotonic()>until:raise ValueError('Native monitor did not request checkpoint yield')
                    time.sleep(.01)
        scorer.progress=progress
        result=guard.execute(root/'yielded',{}, {})
        if result.get('status')!='yielded' or result['completed']!=8 or calls!=['actual_tiny_handler']:
            raise ValueError('Actual scoring block did not yield with one model invocation')
        if not (root/'yielded/scores/block-00000.receipt.json').is_file():raise ValueError('Yield lost sealed block')
    finally:
        guard.memory=original_memory;guard.invoke=original_invoke;scorer.load_model=original_loader;scorer.progress=original_progress
    childroot=root/'owned-hard-exit'
    code="from runners.drive.cards.week5_at_precision_guard import identity,hard_exit; import sys; hard_exit(sys.argv[1],dict(identity=identity(),fixture_only=True,status='constructed_guard_exit'))"
    child=subprocess.run([sys.executable,'-X','utf8','-B','-c',code,str(childroot)],capture_output=True,text=True)
    if child.returncode!=75:raise ValueError('Constructed owned guard did not exit75')
    value=read(childroot/'NATIVE_GUARD_TERMINATION.json')
    if value['identity']['pid']==os.getpid() or not value['fixture_only']:raise ValueError('Hard exit ownership differs')
    receipt=dict(fixture_only=True,actual_native_identity=True,refusal_before_model_load=True,
                 actual_scoring_handler_sealed_yield=True,no_duplicate_model_load=True,owned_native_hard_exit75=True,
                 six_gib_floor_and_sixty_second_grace=True,limits=guard.LIMITS)
    final=Path(output)/'FIXTURE.json'
    if verifying:
        if read(final)!=receipt:raise ValueError('Native guard proof changed')
        return dict(verified=True,complete_native_guard_replay=True)
    write_equal(final,receipt);return dict(status='complete',fixture_only=True)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--verify',action='store_true');a=p.parse_args()
    print(json.dumps((verify if a.verify else execute)(a.output,{},{})))
