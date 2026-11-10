"""Full-count native TR5 comparisons and checkpointed original learners."""
from pathlib import Path
import json,math,time
from . import week5_bk_tr5_analysis as card
from . import week5_bk_tr5_learners as learner
from . import week3_trust_analysis as old
from . import week3_trust_learners as original_learner
from .timing_census import read
from .timing_p6 import write_equal,gzread


def window(drop):
    return dict(acceptance_before=.6+drop/2,acceptance_after=.6-drop/2,request_rate_before=1+drop/2,request_rate_after=1-drop/2)


def world(effect,writers=24):
    pairs=[];sessions=[]
    for i in range(writers):
        writer='constructed-'+str(i)
        for j,bin_ in enumerate(('short','short','long','long')):
            delta=effect if bin_=='long' else 0
            pairs.append(dict(writer=writer,run_bin=bin_,failure=dict(window=window(.1+delta),strict_retyped=True),controls=[dict(window=window(.1))]))
            menu=[dict(handling='accept' if (k+j)%3 else 'dismiss',censored=False,temperature=.2+j*.2,origin=k,resolution=k) for k in range(10)]
            sessions.append(dict(writer=writer,session=writer+':'+str(j),timestamp=j,menu=menu))
    return dict(pairs=pairs,sessions=sessions,run_median=2,summary=dict(support=writers>=20,constructed=True))


def run(output,inputs,config,verifying=False):
    if inputs or config:raise ValueError('Constructed fixture has no human inputs')
    root=Path(output);cfg=dict(mode='constructed',max_wall_seconds=1500)
    for name,effect in [('positive',.4),('null',0.),('reversed',-.4)]:
        data=world(effect);source=root/(name+'.json');write_equal(source,data)
        (card.verify if verifying else card.execute)(root/name,dict(fixture=str(source)),cfg)
        actual=read(root/name/'RESULT.json');expected=old.analyze(data,old.CONFIG);expected.update(constructed_only=True,scientific_admission=False)
        if actual!=expected:raise ValueError('Full original primary and companion arithmetic changed')
        if (effect>0 and actual['primary']['ci95'][0]<=0) or (effect<0 and actual['primary']['ci95'][1]>=0) or (effect==0 and actual['primary']['ci95']!=[0,0]):
            raise ValueError('Signed matched drop control failed')
    data=world(.4,1);source=root/'single.json';write_equal(source,data)
    (card.verify if verifying else card.execute)(root/'single',dict(fixture=str(source)),cfg)
    single=read(root/'single/RESULT.json')
    if single['state']!='unsupported' or single['fallback']['primary']['ci95'] is not None or not math.isclose(single['fallback']['primary']['estimate'],.4):
        raise ValueError('Single-writer pooled point/uncertainty guard failed')
    train=[0]*80+[1]*80;test=[1]*40;native=root/'cross-block'
    expected=original_learner.fit(train,test)
    if not verifying:
        count=[0]
        def yield_after_first():count[0]+=1;return count[0]==2
        try:learner.fit(native,train,test,should_yield=yield_after_first)
        except learner.YieldCheckpoint:pass
        else:raise ValueError('Learner did not yield after first sealed block')
        if not (native/'train-adaptive-0/block-00000.json.gz').exists():raise ValueError('Learner yield lost sealed work')
    actual=learner.fit(native,train,test,verifying)
    if actual!=expected:raise ValueError('Checkpointed prequential fit changed original arithmetic')
    other=learner.fit(root/'heldout-reversal',train,[0]*40,verifying)
    if actual['frozen_training_selection']!=other['frozen_training_selection']:raise ValueError('Held-out outcomes tuned parameters')
    final=gzread(native/'train-change-0/block-00001.json.gz')
    if len(final['state']['weights'])!=161:raise ValueError('Change-point run lengths were pruned')
    if not math.isclose(original_learner.score(original_learner.Adaptive(.05,.5),[1]),math.log(.5)):raise ValueError('Target updated before prediction')
    seal=native/'train-adaptive-0/block-00000.json.seal.json';saved=seal.read_bytes()
    try:
        changed=read(seal);changed['sha256']='invalid';seal.write_text(json.dumps(changed)+'\n')
        try:learner.fit(native,train,test,True)
        except ValueError as error:
            if 'seal differs' not in str(error):raise
        else:raise ValueError('Mutated learner checkpoint accepted')
    finally:seal.write_bytes(saved)
    receipt=dict(fixture_only=True,full_original_bootstraps=2000,full_original_permutations=200,
                 complete_primary_and_all_companion_equivalence=True,positive_null_reversal=True,
                 checkpoint_yield_resume=True,all_state_transitions_replayed=True,unpruned_run_lengths=True,
                 train_only_selection=True,score_before_update=True,single_writer_points_without_intervals=True,tamper_refused=True)
    if verifying:
        if read(root/'FIXTURE.json')!=receipt:raise ValueError('Full TR5 fixture changed')
        return dict(verified=True,full_original_handler_and_checkpoint_replay=True)
    write_equal(root/'FIXTURE.json',receipt);return dict(status='complete',fixture_only=True)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--verify',action='store_true');a=p.parse_args();began=time.process_time()
    from threadpoolctl import threadpool_limits
    with threadpool_limits(limits=2):result=(verify if a.verify else execute)(a.output,{}, {})
    write_equal(Path(a.output)/('NATIVE_VERIFY_CPU.json' if a.verify else 'NATIVE_EXECUTE_CPU.json'),dict(cpu_seconds=time.process_time()-began))
    print(json.dumps(result))
