"""Full-size constructed IN3/IN4 sensitivity through counted native resumes.

DESIGN CHECK: LESSONS 3-5. All five fixed doses have 100 worlds and 2,000
actual cluster-refitted draws. Exact nulls recover zero, signed known effects
recover their dose, and the prespecified high-noise design fails sensitivity.
Only fixture operational quanta change after the first 25 completed worlds.
"""
from pathlib import Path
import argparse,json
import numpy as np
from . import week5_in_followup as follow
from . import week5_runtime_v6 as runtime
from .batch_runtime import REPO,freeze,read,filehash
from .week5_runtime_v5_fixture import wait
from .week5_resume_v2 import output_manifest
from .. import week5_launch_v6 as launch
from runners.theory_days.launch import closure
from runners.stage9.process_identity import is_same_live_process

PRIVATE=REPO/'.agent-state/drive-20261107'
NATIVE=PRIVATE/'in-followup-native'
INPUTS=PRIVATE/'in-sensitivity-full-inputs'


def perform(output,inputs,config):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    if set(config)!={'case','worlds','draws'} or config['worlds']!=100 or config['draws']!=2000:
        raise ValueError('Full frozen sensitivity qualification required')
    case=config['case']
    if case not in ('IN3','IN4','FAILURE'):raise ValueError('Unknown constructed case')
    manifest=read(inputs['fixture_manifest'])
    if manifest.get('constructed_only') is not True or manifest['case']!=case:raise ValueError('Constructed input identity differs')
    for key,digest in manifest['sha256'].items():
        if filehash(Path(inputs[key]))!=digest:raise ValueError('Constructed input changed')
    completed=len(list((output/'worlds').glob('*.json')))//2
    cfg=dict(worlds=100,draws=2000,max_new_worlds=25 if completed<25 else 500)
    if case=='FAILURE':
        with np.load(inputs['noise'],allow_pickle=False) as data:
            result=follow.calibrate(data['x'],data['y'],data['clusters'],data['contrast'],.1,cfg,output)
        result['card']='constructed-noise'
        if result.get('status')!='yielded':follow.core.write_json(output/'RESULT.json',result)
    else:
        result=follow.execute(output,{k:v for k,v in inputs.items() if k!='fixture_manifest'},{**cfg,'phase':case+'.ic'})
    completed=len(list((output/'worlds').glob('*.json')))//2
    follow.core.write_json(output/'PROGRESS.json',dict(phase='constructed_sensitivity',completed=completed,total=500))
    if result.get('status')=='yielded':return result
    if result.get('status')!='ok' or completed!=500:raise ValueError('Full sensitivity grid did not complete')
    if result['sensitivity_pass']!=(case!='FAILURE'):raise ValueError('Known sensitivity pass/failure differs')
    if case!='FAILURE':
        for dose in result['effects']:
            if not np.allclose(dose['estimate_quantiles'],dose['injected_contrast'],rtol=0,atol=1e-8):
                raise ValueError('Known signed/null contrast differs')
    return result


def execute(output,inputs,config):return perform(output,inputs,config)


def verify(output,inputs,config):
    result=perform(Path(output)/'independent-replay',inputs,config)
    if result.get('status')=='yielded':return {**result,'verified':False}
    if result!=read(Path(output)/'RESULT.json'):raise ValueError('Full fixed-world replay differs')
    return dict(verified=True,full_100_worlds_per_effect_and_2000_draws=True,constructed_only=True)


def prepare():
    INPUTS.mkdir(parents=True,exist_ok=False)
    rng=np.random.default_rng(99)
    np.savez(INPUTS/'noise.npz',x=np.column_stack([np.ones(120),rng.normal(size=(120,2))]),
             y=rng.normal(0,1000,120),clusters=np.repeat(np.arange(40),3),contrast=np.array([0.,1.,0.]))
    for case in ('IN3','IN4','FAILURE'):
        inputs=bundle(case)
        freeze(INPUTS/(case+'.json'),dict(constructed_only=True,case=case,sha256={k:filehash(Path(v)) for k,v in inputs.items() if k!='fixture_manifest'}))


def bundle(case):
    if case=='IN3':value=dict(generation=str(NATIVE/'in3.parquet'))
    elif case=='IN4':value=dict(generation=str(NATIVE/'in4-g.parquet'),validation=str(NATIVE/'in4-v.parquet'))
    elif case=='FAILURE':value=dict(noise=str(INPUTS/'noise.npz'))
    else:raise ValueError(case)
    return {**value,'fixture_manifest':str(INPUTS/(case+'.json'))}


def main(case,commit,selected_stage):
    evidence=PRIVATE/('in-sensitivity-full-counted-'+case)
    evidence.mkdir(parents=True,exist_ok=selected_stage!='source-pilot')
    inputs=bundle(case);design=REPO/'docs/design/stage-15/week5/IN-sensitivity-qualification.md'
    proof=NATIVE/'FIXTURE.json';module='runners.drive.cards.week5_in_sensitivity_counted_fixture'
    paths=list(closure([module,*launch.MODULES,'runners.drive.week5_launch_v6']))+[design,proof,*map(Path,inputs.values())]
    plan=dict(campaign='S15-WEEK5',family='IN',module=module,inputs=inputs,config=dict(case=case,worlds=100,draws=2000),
        design=str(design),reviewed_design_commit=commit,pins={str(p.resolve()):filehash(p) for p in paths},
        fixture_passed=True,owner_reviewed=True,validation_receipts=[str(proof)],paid=False,gpu=False,ollama=False,numerical_threads=2,
        max_cpu_seconds=1200,max_wall_seconds=2400,forecast_cpu_seconds=500,projected_peak_ram_GiB=1,
        premortem=dict(case_and_check='Constructed100worlds per signed dose, full2kdraws;25world pilot, full authentic continuation and fresh replay.',
                      smaller_route='Retain source/outputs if measured forecast does not fit; owner review before increasing finite cap.'))
    stages=('source-pilot','verify-pilot','complete')
    previous=None;prior_tree=None;records=[]
    if selected_stage!='source-pilot':
        previous=runtime.policy.ROOT/('IN-sensitivity-fixture-'+case+'-'+stages[stages.index(selected_stage)-1])
        prior_tree={p.relative_to(previous).as_posix():filehash(p) for p in previous.rglob('*') if p.is_file()}
    for stage in (selected_stage,):
        root=runtime.policy.ROOT/('IN-sensitivity-fixture-'+case+'-'+stage);root.mkdir()
        current={**plan,'card':root.name}
        if previous:current['resume']=dict(root=str(previous),plan_sha256=filehash(previous/'PLAN.json'),paused_sha256=filehash(previous/'PAUSED.json'))
        freeze(root/'PLAN.json',current);freeze(evidence/(stage+'-launch.json'),launch.launch(root))
        name,terminal=wait(root)
        if name!=('COMPLETE' if stage=='complete' else 'PAUSED'):raise ValueError('Unexpected fixture terminal: '+name)
        if previous:
            if prior_tree!={p.relative_to(previous).as_posix():filehash(p) for p in previous.rglob('*') if p.is_file()}:raise ValueError('Predecessor changed')
            if read(root/'RESUMED_FROM.json')['copied']!=read(previous/'PAUSED.json')['checkpoint_outputs']:raise ValueError('Stopped manifest differs')
        owner=read(root/'OWNER.json')['native']
        if is_same_live_process(owner) or any(read(p).get('native')==owner for p in runtime.policy.lease_paths()):raise ValueError('Owner or lease still live')
        if name=='PAUSED' and terminal['checkpoint_outputs']!=output_manifest(root/'output'):raise ValueError('Pause incomplete')
        records.append(dict(root=str(root),terminal=name,cpu_seconds=terminal['cpu_seconds'],native=owner,
                            terminal_sha256=filehash(root/(name+'.json')),plan_sha256=filehash(root/'PLAN.json')))
        previous=root;prior_tree={p.relative_to(root).as_posix():filehash(p) for p in root.rglob('*') if p.is_file()}
        print(json.dumps(dict(case=case,stage=stage,terminal=name,cpu_seconds=terminal['cpu_seconds'])),flush=True)
    if selected_stage!='complete':return
    records=[]
    for stage in stages:
        attempt=runtime.policy.ROOT/('IN-sensitivity-fixture-'+case+'-'+stage)
        name='COMPLETE' if stage=='complete' else 'PAUSED';terminal=read(attempt/(name+'.json'))
        records.append(dict(root=str(attempt),terminal=name,cpu_seconds=terminal['cpu_seconds'],
                            native=read(attempt/'OWNER.json')['native'],terminal_sha256=filehash(attempt/(name+'.json')),
                            plan_sha256=filehash(attempt/'PLAN.json')))
    done=read(previous/'COMPLETE.json')
    for name,digest in done['outputs'].items():
        if filehash(previous/name)!=digest:raise ValueError('Complete output changed')
    if read(previous/'VERIFIED.json').get('verified') is not True:raise ValueError('Full independent verification absent')
    freeze(evidence/'FIXTURE.json',dict(verified=True,constructed_only=True,case=case,worlds_per_effect=100,draws=2000,
        all_predecessor_bytes_retained=True,every_complete_output_hash_verified=True,full_real_runtime_policy=True,
        actual_native_owners_exited_and_leases_released=True,known_answer_pass_or_failure_verified=True,
        measured_cpu_seconds=sum(r['cpu_seconds'] for r in records),attempts=records,
        sources={str(p.relative_to(REPO)):filehash(p) for p in paths if p.suffix=='.py'}))


if __name__=='__main__':
    from threadpoolctl import threadpool_limits
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','run']);parser.add_argument('--case',choices=['IN3','IN4','FAILURE']);parser.add_argument('--commit')
    parser.add_argument('--stage',choices=['source-pilot','verify-pilot','complete'],default='source-pilot');args=parser.parse_args()
    with threadpool_limits(limits=2):
        if args.mode=='prepare':prepare()
        else:main(args.case,args.commit,args.stage)
