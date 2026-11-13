"""Constructed retirement contracts only; no real PID or campaign evidence."""
from pathlib import Path
import pytest

from runners.drive.cards import week5_reader_retirement_v1 as gate
from runners.drive.cards import week5_reader_retirement_fixture_v1 as fixture


@pytest.mark.parametrize('status,operation,cpu', [
    ('COMPLETE','execute',3.), ('PAUSED','execute',1.),
    ('PAUSED','verify',3.), ('FAILED','execute',1.)])
def test_exact_terminal_contract_is_read_only_without_pid_query(tmp_path, monkeypatch, status, operation, cpu):
    from runners.stage9 import process_identity
    def forbidden(*_):
        raise AssertionError('Historical or unrelated PID query is forbidden')
    monkeypatch.setattr(process_identity, 'native_identity', forbidden)
    monkeypatch.setattr(process_identity, 'is_same_live_process', forbidden)
    case=fixture.make_case(tmp_path/'case',status,operation)
    before=fixture.snapshot(case['repository'])
    proof=fixture.inspect(case)
    assert proof['accounting_reader_retired'] is True
    assert proof['native_owner_exit_verified'] is False
    assert proof['campaign_transition_admitted'] is False
    assert proof['checkpoint_copy_authorized'] is False
    assert proof['retained_cpu_seconds']==cpu==proof['child_job_cpu_seconds']
    assert proof['existing_accounting_supervisor_charge_seconds']==30
    assert proof['constructed_evidence'] is True
    assert fixture.snapshot(case['repository'])==before


@pytest.mark.parametrize('mutation,message',[
    ('undercharge','undercounts'), ('failure_pending','accounting remains unresolved'),
    ('compatibility_label','Compatibility-label'), ('entrypoint','actual entrypoint')])
def test_authenticated_but_invalid_semantics_refuse(tmp_path,mutation,message):
    case=fixture.make_case(tmp_path/'case','FAILED' if mutation=='failure_pending' else 'COMPLETE')
    name=case['terminal_name']
    target=case['root']/name
    value=fixture.read(target)
    if mutation=='undercharge': value['cpu_seconds']=0
    elif mutation=='failure_pending': value['accounting_reconciliation_required']=True
    elif mutation=='compatibility_label':
        target=case['root']/'PLAN.json';value=fixture.read(target);value['accounting_runtime']='week5-v11'
    else:
        target=case['launch_path'];value=fixture.read(target);value['runtime_module']='some.other.runtime'
    fixture.write(target,value);fixture.repin(case)
    with pytest.raises(gate.RetirementRefusal,match=message): fixture.inspect(case)


@pytest.mark.parametrize('missing',['ATTEMPT.claim','OWNER.json','COMPLETE.json'])
def test_unclaimed_starting_and_nonterminal_refuse(tmp_path,missing):
    case=fixture.make_case(tmp_path/'case')
    (case['root']/missing).unlink()
    with pytest.raises(gate.RetirementRefusal): fixture.inspect(case)


def test_unknown_profile_is_not_inferred_from_source_capsule(tmp_path):
    case=fixture.make_case(tmp_path/'case')
    value=fixture.read(case['authority_path']);value['profile']='unreviewed-v7'
    fixture.write(case['authority_path'],value);case['authority_sha256']=fixture.sha(case['authority_path'])
    with pytest.raises(gate.RetirementRefusal,match='scope/profile'): fixture.inspect(case)


def test_changed_control_flow_bytes_refuse(tmp_path):
    case=fixture.make_case(tmp_path/'case')
    source=case['root']/'source_capsule/runners/drive/cards/week5_runtime_v8.py'
    with source.open('ab') as stream: stream.write(b'\n# changed\n')
    with pytest.raises(gate.RetirementRefusal,match='Changed or unauthenticated'): fixture.inspect(case)


def test_terminal_before_lease_release_refuses_same_native_birth(tmp_path):
    case=fixture.make_case(tmp_path/'case')
    altered_exe=dict(case['native'],executable=str(case['repository']/'another-name.exe'))
    fixture.write(case['lease_path'],dict(native=altered_exe,attempt_root=str(case['root']),card='constructed-retirement'))
    authority=fixture.read(case['authority_path'])
    authority['other_lease_sha256']={case['lease_path'].relative_to(case['repository']).as_posix():fixture.sha(case['lease_path'])}
    fixture.write(case['authority_path'],authority);fixture.repin(case)
    with pytest.raises(gate.RetirementRefusal,match='Attempt-owned lease'): fixture.inspect(case)


def test_exact_successor_lease_is_preserved_without_process_inspection(tmp_path):
    case=fixture.make_case(tmp_path/'case')
    fixture.write(case['lease_path'],dict(native=dict(case['native'],pid=2002,created_ticks=200_000_002),
          attempt_root=str(case['root'].parent/'other-attempt'),card='other-card'))
    with pytest.raises(gate.RetirementRefusal,match='Unreviewed occupied'): fixture.inspect(case)
    authority=fixture.read(case['authority_path'])
    authority['other_lease_sha256']={case['lease_path'].relative_to(case['repository']).as_posix():fixture.sha(case['lease_path'])}
    fixture.write(case['authority_path'],authority);fixture.repin(case)
    original=case['lease_path'].read_bytes()
    assert fixture.inspect(case)['accounting_reader_retired'] is True
    assert case['lease_path'].read_bytes()==original


def test_denied_bank_enumeration_cannot_be_empty(tmp_path,monkeypatch):
    case=fixture.make_case(tmp_path/'case')
    original=gate.os.scandir
    def deny(path):
        if Path(path)==case['repository']/gate.BANKS[0]: raise PermissionError('constructed denial')
        return original(path)
    monkeypatch.setattr(gate.os,'scandir',deny)
    with pytest.raises(gate.RetirementRefusal,match='unavailable'): fixture.inspect(case)


def test_changed_root_inventory_refuses(tmp_path,monkeypatch):
    case=fixture.make_case(tmp_path/'case')
    original=gate.Reader.stable
    def changed(reader):
        original(reader)
        fixture.write(case['root']/'LATE_CHILD.json',dict(constructed=True))
    monkeypatch.setattr(gate.Reader,'stable',changed)
    with pytest.raises(gate.RetirementRefusal,match='inventory changed'): fixture.inspect(case)


def test_observed_native_exit_is_a_separate_stronger_route(tmp_path):
    case=fixture.make_case(tmp_path/'case')
    assert fixture.inspect(case)['native_owner_exit_verified'] is False
    proof_path=fixture.native_exit_record(case)
    proof=gate.inspect_observed_exit(case['root'],repository=case['repository'],
         authority_path=case['authority_path'],authority_sha256=case['authority_sha256'],
         exit_path=proof_path,exit_sha256=fixture.sha(proof_path),constructed=True)
    assert proof['native_owner_exit_verified'] is True
    assert proof['checkpoint_copy_authorized'] is False
    value=fixture.read(proof_path);value['identities'][0]['signalled_exit']=False
    fixture.write(proof_path,value)
    with pytest.raises(gate.RetirementRefusal,match='Incomplete exact native-exit'):
        gate.inspect_observed_exit(case['root'],repository=case['repository'],
             authority_path=case['authority_path'],authority_sha256=case['authority_sha256'],
             exit_path=proof_path,exit_sha256=fixture.sha(proof_path),constructed=True)


def test_constructed_authority_cannot_use_default_production_mode(tmp_path):
    case=fixture.make_case(tmp_path/'case')
    with pytest.raises(gate.RetirementRefusal,match='Constructed evidence'):
        gate.inspect_post_reader(case['root'],repository=case['repository'],
             authority_path=case['authority_path'],authority_sha256=case['authority_sha256'])


def test_constructed_handler_and_independent_fixture_replay(tmp_path):
    result=fixture.execute(tmp_path/'fixture',{},dict(constructed_only=True))
    assert result['reader_retired'] and not result['native_owner_exit_verified']
    assert fixture.verify(tmp_path/'fixture',{},dict(constructed_only=True))['verified'] is True


@pytest.mark.parametrize('mode',['prechild','forced'])
def test_unresolved_child_history_is_not_healed_by_terminal(tmp_path,mode):
    case=fixture.make_case(tmp_path/'case','FAILED')
    if mode=='prechild':
        value=fixture.read(case['authority_path']);value['started_operations']=[]
        fixture.write(case['authority_path'],value)
    else:
        path=case['root']/'EXECUTE_JOB_USAGE.json';value=fixture.read(path)
        value.update(exit_code=None,termination_margin_cpu_seconds=2.,cpu_seconds=3.)
        fixture.write(path,value)
    fixture.repin(case)
    with pytest.raises(gate.RetirementRefusal): fixture.inspect(case)


def test_conflicting_terminal_names_refuse_before_identity_lookup(tmp_path):
    case=fixture.make_case(tmp_path/'case')
    fixture.write(case['root']/'PAUSED.json',dict(status='PAUSED'))
    with pytest.raises(gate.RetirementRefusal,match='Unique terminal'): fixture.inspect(case)


def test_authority_mutation_during_review_refuses(tmp_path,monkeypatch):
    case=fixture.make_case(tmp_path/'case')
    original=gate.Reader.stable
    def changed(reader):
        with case['authority_path'].open('ab') as stream: stream.write(b'\n')
        original(reader)
    monkeypatch.setattr(gate.Reader,'stable',changed)
    with pytest.raises(gate.RetirementRefusal,match='Changed or unauthenticated'): fixture.inspect(case)
