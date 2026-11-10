"""Actual small-model adoption plus native-identity, pin and manifest refusals."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import time
from . import week5_at_precision_migration as migration
from . import week5_at_precision_resume_fixture as fixture
from . import week5_at_precision_guard_v2 as guard
from . import week5_at_scoring_v5 as scorer
from .week5_at_scoring_v4_fixture import loader
from .week5_resume import output_manifest
from .timing_census import read,filehash
from .timing_p6 import write_equal
from runners.stage9.process_identity import native_identity


def refused(call):
    try:call()
    except ValueError:return
    raise ValueError('Invalid migration was accepted')


def run(output,inputs,config,verifying=False):
    if set(inputs)!={'failed_root','legacy_output'} or config:raise ValueError('Constructed local proof bundle required')
    fixture.fixture_inputs({'failed_root':inputs['failed_root']})
    legacy=Path(inputs['legacy_output']);original=read(legacy/'INITIAL_SCORE_HASHES.json')
    if fixture.preserved(legacy)!=original or not read(legacy/'INTENTIONAL_VERIFY_PAUSE.json')['fixture_only']:
        raise ValueError('Actual original-v4 complete/pause fixture required')
    root=Path(output);root.mkdir(parents=True,exist_ok=True);old=root/'predecessor';target=root/'successor/output'
    pins={str(p.resolve()):filehash(p) for p in Path(inputs['failed_root']).iterdir() if p.is_file()}
    for name in ('week5_at_precision_guard.py','week5_at_precision_case.py','week5_at_scoring_v4.py','week5_at_scoring.py'):
        path=Path(__file__).parent/name;pins[str(path.resolve())]=filehash(path)
    plan=dict(module=migration.OLD_MODULE,inputs={'failed_root':inputs['failed_root']},config={},family='AT',campaign='constructed-migration-proof',pins=pins)
    if not (old/'PLAN.json').exists():
        for name in output_manifest(legacy):
            destination=old/'output'/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(legacy/name,destination)
        write_equal(old/'PLAN.json',plan)
        child=subprocess.run([sys.executable,'-X','utf8','-B','-c',
            'import json;from runners.stage9.process_identity import native_identity;print(json.dumps(native_identity()))'],capture_output=True,text=True,check=True)
        write_equal(old/'OWNER.json',dict(plan_sha256=filehash(old/'PLAN.json'),native=json.loads(child.stdout)))
        write_equal(old/'PAUSED.json',dict(status='PAUSED',checkpoint_validation_required=True,checkpoint_outputs=output_manifest(old/'output'),fixture_only=True))
    elif read(old/'PLAN.json')!=plan:raise ValueError('Constructed predecessor plan changed')
    new_inputs=dict(failed_root=inputs['failed_root'],predecessor_root=str(old.resolve()))
    new_pins=dict(pins)
    for path in (old/'PLAN.json',old/'PAUSED.json',Path(migration.__file__)):
        new_pins[str(path.resolve())]=filehash(path)
    successor=dict(module=migration.__name__,inputs=new_inputs,config={},family=plan['family'],campaign=plan['campaign'],pins=new_pins)
    write_equal(target.parent/'PLAN.json',successor)
    migration.adopt(target,new_inputs)
    if fixture.preserved(target)!=original:raise ValueError('Original scoring bytes changed on migration')
    owner=old/'OWNER.json';saved=owner.read_bytes();value=read(owner);value['native']=native_identity();owner.write_text(json.dumps(value),encoding='utf8')
    try:refused(lambda:migration.adopt(target,new_inputs))
    finally:owner.write_bytes(saved)
    newplan=target.parent/'PLAN.json';saved=newplan.read_bytes();value=read(newplan);value['pins'].pop(next(iter(pins)));newplan.write_text(json.dumps(value),encoding='utf8')
    try:refused(lambda:migration.adopt(target,new_inputs))
    finally:newplan.write_bytes(saved)
    payload=old/'output/scores/SUMMARY.json';saved=payload.read_bytes();payload.write_text('{}\n',encoding='utf8')
    try:refused(lambda:migration.adopt(target,new_inputs))
    finally:payload.write_bytes(saved)
    original_memory,original_load=guard.memory,scorer.load_model
    guard.memory=lambda:dict(commit_headroom_bytes=30*2**30,ram_available_bytes=30*2**30)
    scorer.load_model=loader
    try:value=(migration.verify if verifying else migration.execute)(target,new_inputs,{})
    finally:guard.memory=original_memory;scorer.load_model=original_load
    if fixture.preserved(target)!=original:raise ValueError('Migrated fresh handler changed old scoring or cost bytes')
    receipt=dict(fixture_only=True,actual_original_v4_completed_scores=True,whole_output_manifest_preserved=True,
                 actual_exited_native_identity=True,live_predecessor_refused=True,dropped_pin_refused=True,
                 changed_output_refused=True,actual_guarded_tiny_neox_execution=True,
                 unchanged_numerical_binding=scorer.NUMERICAL_SPEC,independent_verification_required=True)
    if verifying:
        if value.get('verified') is not True or read(root/'FIXTURE.json')!=receipt:raise ValueError('Actual migrated fresh verification failed')
        return dict(verified=True,complete_narrow_migration_replay=True)
    write_equal(root/'FIXTURE.json',receipt);return dict(status='complete',fixture_only=True)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('failed_root');p.add_argument('legacy_output');p.add_argument('--verify',action='store_true');a=p.parse_args()
    began=time.process_time();value=(verify if a.verify else execute)(a.output,dict(failed_root=a.failed_root,legacy_output=a.legacy_output),{})
    write_equal(Path(a.output)/('NATIVE_VERIFY_CPU.json' if a.verify else 'NATIVE_EXECUTE_CPU.json'),dict(cpu_seconds=time.process_time()-began))
    print(json.dumps(value))
