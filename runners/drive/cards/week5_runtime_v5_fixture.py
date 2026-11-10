"""Owner-authorized counted native integration, constructed/public-source only."""
from pathlib import Path
import argparse
import json
import time
from .batch_runtime import REPO, freeze, read, filehash
from . import week5_policy_v2 as policy
from .week5_resume_v2 import output_manifest
from .. import week5_launch_v5 as launch
from runners.theory_days.launch import closure
from runners.stage9.process_identity import is_same_live_process

PRIVATE=REPO/'.agent-state/drive-20261107'


def inputs(case,root):
    if case=='GO2':
        source=read(policy.ROOT/'GO2-source-h2-pilot/PLAN.json')['inputs']
        docs=read(source['documents'])['documents']
        chosen=[d for d in docs if d['repository']=='eips'][:2]
        assert len(chosen)==2
        path=root/'PUBLIC_DOCUMENTS.json';freeze(path,dict(documents=chosen))
        return {**source,'documents':str(path)},dict(phase='prepare',max_new_documents=1,max_cpu_seconds=900),dict(phase='prepare',max_new_documents=2,max_cpu_seconds=1800), 'GO', 'runners.drive.cards.week5_go_history_bounded_h2', PRIVATE/'go2-source-h2-native/FIXTURE.json'
    if case=='CA1':
        source=PRIVATE/'ca1-encoder-native-v2/source'
        model=REPO/'results/phase_2_4_stage_15/raw/drive-week3-20261025/CA1-model'
        return dict(prepared_summary=str(source/'output/SUMMARY.json'),prepared_complete=str(source/'COMPLETE.json'),model_summary=str(model/'output/SUMMARY.json'),model_complete=str(model/'COMPLETE.json')),dict(fixture=True,actual_encoder=False,max_new_chunks=1,max_wall_seconds=900),dict(fixture=True,actual_encoder=False,max_new_chunks=2,max_wall_seconds=900),'BK','runners.drive.cards.week5_bk_ca1_features',PRIVATE/'ca1-encoder-native-v2/FIXTURE.json'
    if case=='V1':
        bundle=read(PRIVATE/'v1-whole-native/positive/INPUTS.json')
        source={k:str((REPO/v).resolve()) for k,v in bundle['inputs'].items()}
        return source,dict(fixture=True,permutations=2,draws=2000,max_new_fits=1,max_wall_seconds=900),dict(fixture=True,permutations=2,draws=2000,max_new_fits=1000,max_wall_seconds=900),'BK','runners.drive.cards.week5_bk_v1',PRIVATE/'v1-whole-native/FIXTURE.json'
    raise ValueError(case)


def wait(root):
    deadline=time.monotonic()+1800
    while time.monotonic()<deadline:
        for name in ['COMPLETE','PAUSED','FAILED','MONITOR_FAILED']:
            path=root/(name+'.json')
            if path.exists():
                # A terminal is written just before the owner releases its lease.
                while is_same_live_process(read(root/'OWNER.json')['native']):
                    if time.monotonic()>deadline:raise TimeoutError('owner exit after terminal')
                    time.sleep(.2)
                return name,read(path)
        time.sleep(1)
    raise TimeoutError('constructed counted fixture terminal')


def main(case,commit,tag):
    evidence=PRIVATE/('runtime-v5-counted-'+case+'-'+tag)
    evidence.mkdir(parents=True,exist_ok=False)
    bundle,first,last,family,module,proof=inputs(case,evidence)
    design=REPO/'docs/design/stage-15/week5/RESUME_V2.md'
    paths=list(closure([module,*launch.MODULES,'runners.drive.week5_launch_v5']))
    paths += [design,proof,PRIVATE/'resume-v2-native/FIXTURE.json']
    paths += [Path(v) for v in bundle.values() if Path(v).is_file()]
    pins={str(p.resolve()):filehash(p) for p in paths}
    plan=dict(campaign='S15-WEEK5',module=module,family=family,inputs=bundle,config=first,
        design=str(design),reviewed_design_commit=commit,pins=pins,
        fixture_passed=True,owner_reviewed=True,validation_receipts=[str(proof),str(PRIVATE/'resume-v2-native/FIXTURE.json')],
        paid=False,gpu=False,ollama=False,numerical_threads=2,max_cpu_seconds=900,max_wall_seconds=1800,
        forecast_cpu_seconds=300,projected_peak_ram_GiB=1,
        premortem=dict(case_and_check='Only constructed rows or two pinned public documents; actual pause and changed-quantum resume must preserve all bytes and native identity.',
                      smaller_route='Retain failed fixture; do not launch or reinterpret a human analysis.'))
    suffix='' if tag=='v1' else '-'+tag
    old=policy.ROOT/('runtime-v5-fixture-'+case+suffix+'-pause');new=policy.ROOT/('runtime-v5-fixture-'+case+suffix+'-resume')
    old.mkdir();plan['card']=old.name;freeze(old/'PLAN.json',plan)
    freeze(evidence/'FIRST_LAUNCH.json',launch.launch(old))
    name,terminal=wait(old)
    if name!='PAUSED':raise ValueError('expected bounded native pause, got '+name)
    before={p.relative_to(old).as_posix():filehash(p) for p in old.rglob('*') if p.is_file()}
    plan={**plan,'card':new.name,'config':last,'resume':dict(root=str(old),plan_sha256=filehash(old/'PLAN.json'),paused_sha256=filehash(old/'PAUSED.json'))}
    new.mkdir();freeze(new/'PLAN.json',plan)
    freeze(evidence/'SECOND_LAUNCH.json',launch.launch(new))
    name,done=wait(new)
    if name!='COMPLETE':raise ValueError('expected complete independent native replay, got '+name)
    assert before=={p.relative_to(old).as_posix():filehash(p) for p in old.rglob('*') if p.is_file()}
    copied=read(new/'RESUMED_FROM.json')['copied']
    assert copied==terminal['checkpoint_outputs']==output_manifest(old/'output')
    for path,digest in done['outputs'].items():assert filehash(new/path)==digest
    assert read(new/'VERIFIED.json')['verified'] is True
    for run in [old,new]:
        owner=read(run/'OWNER.json')['native']
        assert not is_same_live_process(owner)
        assert not any(read(p).get('native')==owner for p in policy.lease_paths())
    receipt=dict(verified=True,case=case,scope='two pinned public source documents; no effects' if case=='GO2' else 'constructed fixture; no human rows',
        old_root=str(old),new_root=str(new),predecessor_unchanged=True,all_complete_output_hashes_verified=True,
        full_native_independent_replay=True,actual_owner_exited_and_lease_released=True,
        changed_operational_keys=sorted(k for k in first if first[k]!=last[k]),
        measured_cpu_seconds=terminal['cpu_seconds']+done['cpu_seconds'],
        charged_family=family,retained_overhead_allowance=60,
        paused_sha256=filehash(old/'PAUSED.json'),complete_sha256=filehash(new/'COMPLETE.json'),
        sources={str(p.relative_to(REPO)):filehash(p) for p in paths if p.suffix=='.py'})
    freeze(evidence/'FIXTURE.json',receipt)
    print(json.dumps(dict(verified=True,case=case,receipt=str(evidence/'FIXTURE.json'),measured_cpu_seconds=receipt['measured_cpu_seconds'])))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('case',choices=['GO2','CA1','V1']);parser.add_argument('commit');parser.add_argument('--tag',default='v1')
    args=parser.parse_args();main(args.case,args.commit,args.tag)
