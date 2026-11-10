"""Constructed native bank proof plus separately admitted counted arithmetic.

DESIGN CHECK: LESSONS 3-5. The isolated bank cases simulate occupancy, not
resource admission. The counted case uses the complete real admission policy.
No corpus, model, live lease or old runtime is changed.
"""
import argparse
import json
from pathlib import Path
import subprocess
import time
from .batch_runtime import REPO, PYTHON, read, freeze, filehash, native_identity
from . import week5_runtime_v6 as runtime
from .week5_runtime_v5_fixture import wait
from .. import week5_launch_v6 as launcher
from runners.theory_days.launch import closure
from runners.stage9.process_identity import is_same_live_process

PRIVATE=REPO/'.agent-state/drive-20261107'


def banks(root):
    started=time.process_time()
    root.mkdir(parents=True,exist_ok=False)
    cases=[('BK',(),0),('BK',(0,1,2),3),('BK',(0,1,2,3),None),
           ('GO',(),4),('MD',(4,5,6,7),0)]
    records=[]
    for index,(family,occupied,expected) in enumerate(cases):
        original=root/str(index)/'original';additional=root/str(index)/'additional'
        original.mkdir(parents=True);additional.mkdir()
        runtime.policy.OLD_SLOTS=original;runtime.policy.NEW_SLOTS=additional
        calls=[]
        def admission(plan):
            calls.append(dict(family=plan['family'],attempt_root=plan['attempt_root']))
            return dict(constructed_admission_stub=True)
        runtime.policy.admission=admission
        for slot in occupied:
            p=(additional if slot>=4 else original)/f'slot-{slot}.json'
            p.write_bytes(b'constructed occupied lease\n')
        before={str(p):p.read_bytes() for folder in (original,additional) for p in folder.glob('slot-*.json')}
        plan=dict(card='fixture',family=family,projected_peak_ram_GiB=.25)
        if expected is None:
            try:runtime.claim(root/str(index)/'attempt',plan)
            except RuntimeError as exc:assert str(exc)=='No free counted slot'
            else:raise AssertionError('BK claimed additional bank')
            assert not list(additional.glob('slot-*.json'))
        else:
            lease,_=runtime.claim(root/str(index)/'attempt',plan)
            assert lease[0]==(additional if expected>=4 else original)/f'slot-{expected}.json'
            assert lease[1]['native']==native_identity()
            assert read(lease[0])==lease[1]
            runtime.release_slot(*lease)
            assert not lease[0].exists()
        assert len(calls)==1
        assert all(Path(p).read_bytes()==raw for p,raw in before.items())
        records.append(dict(family=family,occupied=occupied,claimed=expected,occupied_bytes_retained=True))
    freeze(root/'BANK_PROOF.json',dict(verified=True,constructed_only=True,resource_admission_stub=True,
        native=native_identity(),cases=records,runtime_sha256=filehash(Path(runtime.__file__)),
        native_cpu_seconds=time.process_time()-started))


def prepare():
    evidence=PRIVATE/'runtime-v6-native-banks'
    t=time.process_time()
    completed=subprocess.run([str(PYTHON),'-X','utf8','-B','-m','runners.drive.cards.week5_runtime_v6_fixture','bank-child',str(evidence)],
        cwd=REPO,capture_output=True,check=True,timeout=60)
    proof=read(evidence/'BANK_PROOF.json')
    assert proof['verified'] and not is_same_live_process(proof['native'])
    freeze(evidence/'FIXTURE.json',dict(verified=True,constructed_only=True,bank_proof_sha256=filehash(evidence/'BANK_PROOF.json'),
        native_process_exited=True,source_sha256=filehash(Path(runtime.__file__)),
        parent_cpu_seconds=time.process_time()-t))
    print(json.dumps(dict(verified=True,proof=str(evidence/'FIXTURE.json'))))


def counted(commit):
    evidence=PRIVATE/'runtime-v6-native-counted'
    evidence.mkdir(parents=True,exist_ok=False)
    design=REPO/'docs/design/stage-15/week5/BK_SLOT_BANK.md'
    proof=PRIVATE/'runtime-v6-native-banks/FIXTURE.json'
    module='runners.drive.cards.week5_runtime_fixture_v2'
    paths=list(closure([module,*launcher.MODULES,'runners.drive.week5_launch_v6']))+[design,proof,Path(__file__).resolve()]
    root=runtime.policy.ROOT/'runtime-v6-bank-fixture'
    root.mkdir()
    plan=dict(card=root.name,campaign='S15-WEEK5',family='BK',module=module,inputs={},config={'fixture':True},
        pins={str(p.resolve()):filehash(p) for p in paths},design=str(design),reviewed_design_commit=commit,
        fixture_passed=True,owner_reviewed=True,validation_receipts=[str(proof)],paid=False,gpu=False,ollama=False,
        numerical_threads=2,max_cpu_seconds=60,max_wall_seconds=300,forecast_cpu_seconds=10,projected_peak_ram_GiB=.25,
        premortem=dict(case_and_check='Constructed exact arithmetic, complete real policy, original-bank lease and independent native replay.',
                      smaller_route='Wait for original-bank capacity; never borrow new bank or alter a live lease.'))
    freeze(root/'PLAN.json',plan)
    freeze(evidence/'LAUNCH.json',launcher.launch(root))
    name,complete=wait(root)
    assert name=='COMPLETE',name
    admission=read(root/'ADMISSION.json')
    lease=Path(admission['lease'])
    assert lease.parent==runtime.policy.OLD_SLOTS and lease.name in {f'slot-{x}.json' for x in range(4)}
    assert not lease.exists() or read(lease).get('native')!=read(root/'OWNER.json')['native']
    assert read(root/'VERIFIED.json')['verified'] is True
    for p,digest in complete['outputs'].items():assert filehash(root/p)==digest
    assert not is_same_live_process(read(root/'OWNER.json')['native'])
    freeze(evidence/'FIXTURE.json',dict(verified=True,constructed_only=True,complete_real_policy=True,
        original_bank_lease=str(lease),owner_exited_and_lease_released=True,fresh_process_verified=True,
        every_complete_output_hash_verified=True,measured_cpu_seconds=complete['cpu_seconds'],
        complete_sha256=filehash(root/'COMPLETE.json'),plan_sha256=filehash(root/'PLAN.json'),
        sources={str(p.relative_to(REPO)):filehash(p) for p in paths if p.suffix=='.py'}))
    print(json.dumps(dict(verified=True,proof=str(evidence/'FIXTURE.json'),cpu_seconds=complete['cpu_seconds'])))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['bank-child','prepare','counted']);parser.add_argument('argument',nargs='?')
    args=parser.parse_args()
    if args.mode=='bank-child':banks(Path(args.argument))
    elif args.mode=='prepare':prepare()
    else:counted(args.argument)
