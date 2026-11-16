"""Constructed source/admission boundaries; mocked identities are not native proof.

Run only in an owner counted child after installation. No human file input.
The separate native rehearsal exercises the real dispatch/replay/exit chain.
"""
from pathlib import Path
import copy
import hashlib
import json
import math
import pytest
from runners.drive.cards import week6_kp_fixture_source_v1 as literal
from runners.drive.cards import week6_kp_source_stage_v1 as stage
from runners.drive.cards import week6_kp_capsule_source_v1 as capsule
from runners.drive.cards import week6_kp_native_rehearsal_v1 as rehearsal
from runners.drive.cards import week6_kp_riders_v1 as original_rider
from runners.drive.cards import week6_kp_riders_capsule_v1 as capsule_rider


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(stage.canonical(value))


def args(tmp_path):
    proof=tmp_path/'qualification.json'
    write(proof,dict(status='COMPLETE',qualification_status='passed',expected_cases=24,
                     verified_cases=24,constructed_only=True))
    inputs=dict(qualification_complete=str(proof),data_access='constructed-fixture-only')
    config=dict(owner_reviewed=True,source_decisions=stage.DECISIONS,
        qualification_complete_sha256=stage.original.digest(proof),
        source_kind='constructed-literal-walsh-v1',fixture_only=True)
    return inputs,config


def terminal(tmp_path,monkeypatch):
    inputs,config=args(tmp_path)
    root=tmp_path/'invented-native-evidence';stage.execute(root/'output',inputs,config)
    write(root/'PLAN.json',dict(module='runners.drive.cards.week6_kp_source_stage_v1',inputs=inputs,config=config))
    for i,name in enumerate(('OWNER','EXECUTE_NATIVE','VERIFY_NATIVE','EXECUTE_CHILD','VERIFY_CHILD')):
        value=dict(native=dict(pid=1000000+i,created_ticks=100+i,executable='constructed-only'))
        if name=='OWNER':value['plan_sha256']=stage.original.digest(root/'PLAN.json')
        write(root/(name+'.json'),value)
    for op in ('EXECUTE','VERIFY'):
        write(root/(op+'_JOB_USAGE.json'),dict(cpu_seconds=1.,exit_code=0,
            includes_all_descendants_and_exited_processes=True,termination_margin_cpu_seconds=0.))
        write(root/(op+'_ENVIRONMENT.json'),dict(threads=2,pools=[dict(num_threads=2)]))
    write(root/'VERIFIED.json',dict(verified=True,full_independent_source_projection=True))
    write(root/'ADMISSION.json',dict(lease=str(tmp_path/'lease.json')))
    def reseal():
        files={x.relative_to(root).as_posix():stage.original.digest(x)
               for x in root.rglob('*') if x.is_file() and x.name!='COMPLETE.json'}
        write(root/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,
                                        cpu_seconds=2.,outputs=files))
        return dict(data_access='constructed-fixture-only',source_stage_complete=str(root/'COMPLETE.json'),
            source_stage_complete_sha256=stage.original.digest(root/'COMPLETE.json'),
            source_stage_seal_sha256=stage.original.digest(root/'output/SEAL.json'),
            original_source_completion_sha256='constructed-literal-walsh-v1')
    monkeypatch.setattr(capsule,'native_identity',lambda pid:None)
    return root,reseal,reseal()


def load(inputs):return capsule.load_authenticated(inputs,decisions=stage.DECISIONS)


def test_literal_walsh_independent_known_answer():
    # Derivation uses literal orthogonality, not fitted handler output.
    columns=[[literal.walsh(i,j) for i in range(16)] for j in range(1,11)]
    assert all(sum(c)==0 for c in columns)
    assert all(sum(a*b for a,b in zip(columns[j],columns[k]))==0
               for j in range(10) for k in range(j))
    base=sum((.5*columns[0][i]+.25*columns[9][i])**2 for i in range(16))/16
    own=sum((.25*columns[9][i])**2 for i in range(16))/16
    assert base==5/16 and own==1/16 and 100*(base-own)/base==80


def test_literal_full_denominator_and_order():
    value=stage.validate(literal.corpus(),'constructed-literal-walsh-v1')
    assert len(value['rows'])==640
    assert len({r['writer'] for r in value['rows']})==20
    assert len({r['session'] for r in value['rows']})==40


def test_duplicate_source_row_refuses():
    value=literal.corpus();value['rows'].append(copy.deepcopy(value['rows'][0]))
    with pytest.raises(ValueError,match='Duplicate'):stage.validate(value,'authenticated-D33')


def test_missing_source_field_refuses():
    value=literal.corpus();del value['rows'][0]['log_pause']
    with pytest.raises(ValueError,match='Missing'):stage.validate(value,'authenticated-D33')


def test_changed_canonical_order_refuses():
    value=literal.corpus();value['rows'].reverse()
    with pytest.raises(ValueError,match='order'):stage.validate(value,'authenticated-D33')


def test_unknown_source_kind_refuses():
    with pytest.raises(ValueError,match='kind'):stage.validate(literal.corpus(),'unreviewed')


def test_changed_literal_source_refuses():
    value=literal.corpus();value['rows'][0]['log_pause']+=1
    with pytest.raises(ValueError,match='Literal'):stage.validate(value,'constructed-literal-walsh-v1')


def test_nonfinite_source_refuses():
    value=literal.corpus();value['rows'][0]['log_pause']=math.nan
    with pytest.raises(ValueError):stage.validate(value,'authenticated-D33')


def test_incomplete_original_qualification_refuses(tmp_path):
    inputs,config=args(tmp_path);p=Path(inputs['qualification_complete'])
    row=stage.original.read(p);row['verified_cases']=23;write(p,row)
    config['qualification_complete_sha256']=stage.original.digest(p)
    with pytest.raises(ValueError,match='24-case'):stage.qualification(inputs,config)


def test_changed_qualification_pin_refuses(tmp_path):
    inputs,config=args(tmp_path);config['qualification_complete_sha256']='0'*64
    with pytest.raises(ValueError,match='pin'):stage.qualification(inputs,config)


def test_fixture_branch_cannot_take_human_mode(tmp_path):
    inputs,config=args(tmp_path);inputs['data_access']='original-D33-only'
    with pytest.raises(ValueError,match='constructed-only'):stage.project(inputs,config)


def test_full_constructed_source_projection_and_replay(tmp_path):
    inputs,config=args(tmp_path);output=tmp_path/'output'
    assert stage.execute(output,inputs,config)['rows']==640
    assert stage.verify(output,inputs,config)['full_independent_source_projection'] is True


def test_mocked_terminal_capsule_roundtrip(tmp_path,monkeypatch):
    _,_,inputs=terminal(tmp_path,monkeypatch)
    assert load(inputs)==literal.corpus()


def test_capsule_output_tamper_refuses(tmp_path,monkeypatch):
    root,_,inputs=terminal(tmp_path,monkeypatch)
    (root/'output/CORPUS.json.gz').write_bytes(b'changed')
    with pytest.raises(ValueError,match='artifact'):load(inputs)


def test_capsule_cannot_be_substituted_as_real(tmp_path,monkeypatch):
    _,_,inputs=terminal(tmp_path,monkeypatch);inputs['data_access']='original-D33-only'
    with pytest.raises(ValueError,match='substitution'):load(inputs)


def test_live_source_native_refuses(tmp_path,monkeypatch):
    root,_,inputs=terminal(tmp_path,monkeypatch);owner=stage.original.read(root/'OWNER.json')['native']
    monkeypatch.setattr(capsule,'native_identity',lambda pid:owner)
    with pytest.raises(ValueError,match='live'):load(inputs)


def test_unknown_native_state_propagates(tmp_path,monkeypatch):
    _,_,inputs=terminal(tmp_path,monkeypatch)
    def inaccessible(pid):raise PermissionError('constructed unknown identity')
    monkeypatch.setattr(capsule,'native_identity',inaccessible)
    with pytest.raises(PermissionError):load(inputs)


def test_nonzero_native_exit_refuses(tmp_path,monkeypatch):
    root,reseal,_=terminal(tmp_path,monkeypatch)
    row=stage.original.read(root/'VERIFY_JOB_USAGE.json');row['exit_code']=1
    write(root/'VERIFY_JOB_USAGE.json',row)
    with pytest.raises(ValueError,match='whole-Job'):load(reseal())


def test_excess_numerical_threads_refuse(tmp_path,monkeypatch):
    root,reseal,_=terminal(tmp_path,monkeypatch)
    write(root/'VERIFY_ENVIRONMENT.json',dict(threads=2,pools=[dict(num_threads=3)]))
    with pytest.raises(ValueError,match='threads'):load(reseal())


def test_rider_body_only_changes_source_import():
    before=Path(original_rider.__file__).read_text(encoding='utf8')
    after=Path(capsule_rider.__file__).read_text(encoding='utf8')
    assert after==before.replace('from . import week6_kp_source_v1 as source',
                                'from . import week6_kp_capsule_source_v1 as source',1)


def test_rehearsal_rejects_reduced_bank():
    config=dict(card='KP2',seed=20261115,max_new_draws=100,bootstrap_draws=1999,permutations=200)
    with pytest.raises(ValueError,match='complete-bank'):
        rehearsal.require(dict(data_access='constructed-fixture-only'),config)


def test_rehearsal_reentry_requires_actual_resume_receipt(tmp_path):
    work=tmp_path/'output/actual-rider';write(work/'CHECKPOINT_0099.json',dict(draws=100))
    config=dict(card='KP2',seed=20261115,max_new_draws=100,bootstrap_draws=2000,permutations=200)
    with pytest.raises(FileNotFoundError):
        rehearsal.execute(tmp_path/'output',dict(data_access='constructed-fixture-only'),config)


def test_owned_source_lease_must_release(tmp_path,monkeypatch):
    root,_,inputs=terminal(tmp_path,monkeypatch)
    write(tmp_path/'lease.json',stage.original.read(root/'OWNER.json'))
    with pytest.raises(ValueError,match='lease'):load(inputs)


def test_capsule_decompressed_length_refuses(tmp_path,monkeypatch):
    root,reseal,_=terminal(tmp_path,monkeypatch);seal=stage.original.read(root/'output/SEAL.json')
    seal['json_bytes']-=1;write(root/'output/SEAL.json',seal)
    with pytest.raises(ValueError,match='decompressed'):load(reseal())
