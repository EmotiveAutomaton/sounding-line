"""Counted runtime qualification of the frozen GO3 source using constructed XML.

DESIGN CHECK: LESSONS 3-5. Actual runtime identity, authenticated immutable
copy, producer pause and independent-verifier pause must all pass. The
fixture changes only archive/licence pins for its known constructed inputs.
No source projection or scientific comparator is changed.
"""
from pathlib import Path
import argparse,json
import pyarrow.parquet as pq
from . import week5_go3_source_checkpointed as source
from . import week5_runtime_v6 as runtime
from .batch_runtime import REPO,freeze,read,filehash
from .week5_runtime_v5_fixture import wait
from .week5_resume_v2 import output_manifest
from .. import week5_launch_v6 as launch
from runners.theory_days.launch import closure
from runners.stage9.process_identity import is_same_live_process

PRIVATE=REPO/'.agent-state/drive-20261107'
NATIVE=PRIVATE/'go3-checkpoint-native-v2'


def configure(inputs):
    expected=read(inputs['fixture_manifest'])
    if expected.get('constructed_only') is not True:raise ValueError('Constructed fixture manifest required')
    for key in ('archive','salt','license','reference'):
        if filehash(Path(inputs[key]))!=expected['sha256'][key]:raise ValueError('Fixture input pin differs')
    source.base.ARCHIVES['writers']=expected['sha256']['archive']
    source.base.LICENSE_SHA=expected['sha256']['license']
    return {k:inputs[k] for k in ('archive','salt','license')}


def execute(output,inputs,config):
    if config!={'phase':'prepare','site':'writers','max_wall_seconds':300}:raise ValueError('Frozen fixture config required')
    return source.execute(Path(output),configure(inputs),config)


def verify(output,inputs,config):
    value=source.verify(Path(output),configure(inputs),config)
    if value.get('status')=='yielded':return value
    if not value.get('verified'):raise ValueError('Full source verification required')
    if not pq.read_table(Path(output)/'edits.parquet').equals(pq.read_table(inputs['reference'])):
        raise ValueError('Known original projection differs')
    return {**value,'constructed_original_projection_exact':True}


def prepare():
    target=PRIVATE/'go3-counted-inputs.json'
    inputs={k:str(NATIVE/v) for k,v in dict(archive='fixture.7z',salt='salt',license='license.txt',reference='original/edits.parquet').items()}
    freeze(target,dict(constructed_only=True,sha256={k:filehash(Path(v)) for k,v in inputs.items()}))
    print(json.dumps(dict(manifest=str(target),inputs=inputs)))


def main(commit):
    evidence=PRIVATE/'go3-counted-native'
    evidence.mkdir(parents=True,exist_ok=False)
    inputs={k:str(NATIVE/v) for k,v in dict(archive='fixture.7z',salt='salt',license='license.txt',reference='original/edits.parquet').items()}
    inputs['fixture_manifest']=str(PRIVATE/'go3-counted-inputs.json')
    design=REPO/'docs/design/stage-15/week5/GO3-source-checkpointed.md'
    proof=NATIVE/'FIXTURE.json';module='runners.drive.cards.week5_go3_counted_fixture'
    paths=list(closure([module,*launch.MODULES,'runners.drive.week5_launch_v6']))+[design,proof,*map(Path,inputs.values())]
    plan=dict(campaign='S15-WEEK5',family='GO',module=module,inputs=inputs,
        config=dict(phase='prepare',site='writers',max_wall_seconds=300),design=str(design),reviewed_design_commit=commit,
        pins={str(p.resolve()):filehash(p) for p in paths},fixture_passed=True,owner_reviewed=True,
        validation_receipts=[str(proof)],paid=False,gpu=False,ollama=False,numerical_threads=2,
        max_cpu_seconds=120,max_wall_seconds=600,forecast_cpu_seconds=30,projected_peak_ram_GiB=1,
        premortem=dict(case_and_check='Constructed archive: exact byte pilot, authentic copy, independent replay pilot, complete row identity.',
                      smaller_route='Retain failed attempt; do not run human source.'))
    previous=None;prior_tree=None;records=[]
    for stage in ('source-pilot','verify-pilot','complete'):
        root=runtime.policy.ROOT/('GO3-counted-fixture-'+stage);root.mkdir()
        current={**plan,'card':root.name}
        if previous:
            current['resume']=dict(root=str(previous),plan_sha256=filehash(previous/'PLAN.json'),paused_sha256=filehash(previous/'PAUSED.json'))
        freeze(root/'PLAN.json',current);freeze(evidence/(stage+'-launch.json'),launch.launch(root))
        name,terminal=wait(root)
        if name!=('COMPLETE' if stage=='complete' else 'PAUSED'):raise ValueError('Unexpected counted fixture terminal: '+name)
        if previous:
            if prior_tree!={p.relative_to(previous).as_posix():filehash(p) for p in previous.rglob('*') if p.is_file()}:
                raise ValueError('Predecessor changed')
            if read(root/'RESUMED_FROM.json')['copied']!=read(previous/'PAUSED.json')['checkpoint_outputs']:
                raise ValueError('Full stopped manifest was not copied')
        owner=read(root/'OWNER.json')['native']
        if is_same_live_process(owner) or any(read(p).get('native')==owner for p in runtime.policy.lease_paths()):
            raise ValueError('Counted owner/lease did not exit')
        if name=='PAUSED' and terminal['checkpoint_outputs']!=output_manifest(root/'output'):raise ValueError('Incomplete pause manifest')
        records.append(dict(root=str(root),terminal=name,cpu_seconds=terminal['cpu_seconds'],native=owner,
                            terminal_sha256=filehash(root/(name+'.json')),plan_sha256=filehash(root/'PLAN.json')))
        previous=root;prior_tree={p.relative_to(root).as_posix():filehash(p) for p in root.rglob('*') if p.is_file()}
        print(json.dumps(dict(stage=stage,terminal=name,cpu_seconds=terminal['cpu_seconds'])),flush=True)
    done=read(previous/'COMPLETE.json')
    for name,digest in done['outputs'].items():
        if filehash(previous/name)!=digest:raise ValueError('Complete output hash differs')
    if read(previous/'VERIFIED.json').get('verified') is not True:raise ValueError('Fresh verification absent')
    freeze(evidence/'FIXTURE.json',dict(verified=True,constructed_only=True,complete_real_runtime_policy=True,
        actual_counted_pause_copy_resume_and_verify_pause=True,all_predecessor_bytes_retained=True,
        every_complete_output_hash_verified=True,all_native_owners_exited_and_leases_released=True,
        measured_cpu_seconds=sum(r['cpu_seconds'] for r in records),attempts=records,
        sources={str(p.relative_to(REPO)):filehash(p) for p in paths if p.suffix=='.py'}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','run']);parser.add_argument('commit',nargs='?');args=parser.parse_args()
    if args.mode=='prepare':prepare()
    else:main(args.commit)
