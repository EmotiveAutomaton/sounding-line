"""Focused operation-metadata regression; no corpus or native-authority claim."""
import json
from pathlib import Path
import pytest
from runners.drive.cards import week5_ex4_v2 as original
from runners.drive.cards import week5_ex4_v3 as study
from runners.drive.cards import week5_ex4_fixture_v2 as fixture


def operation(value):
    assert value['record_kind'] == 'run'
    assert value['theory_tags'] == []
    assert value['by_construction'] is False
    assert value['activation'] == []


def chain(root, monkeypatch, module):
    with monkeypatch.context() as patch:
        patch.setattr(fixture, 'study', module)
        return fixture.constructed_chain(root, patch)


def test_v2_content_parity_and_all_success_pause_replay_records(tmp_path, monkeypatch):
    old_path, old, _, _ = chain(tmp_path/'old', monkeypatch, original)
    new_path, new, proof, terminals = chain(tmp_path/'new', monkeypatch, study)
    for result in [new, proof, *terminals]:
        operation(result)
    assert {k:v for k,v in new.items() if k != 'activation'} == old
    assert new['session_status'] == {'complete': 1, 'replay_parse_failed': 1}
    for relative in ['INDEX.json', 'README.md', 'sessions/00000.json']:
        assert (old_path/'bundle'/relative).read_bytes() == (new_path/'bundle'/relative).read_bytes()
    for relative in ['bundle/SUMMARY.json', 'RESULT.json']:
        operation(json.loads((new_path/relative).read_text()))
    old_manifest=json.loads((old_path/'bundle/MANIFEST.json').read_text())
    new_manifest=json.loads((new_path/'bundle/MANIFEST.json').read_text())
    assert {k:v for k,v in old_manifest['files'].items() if k!='SUMMARY.json'} == {
        k:v for k,v in new_manifest['files'].items() if k!='SUMMARY.json'}
    assert proof['verified'] is True
    assert any(r.get('status') == 'yielded' for r in terminals)


def bind_one(monkeypatch, tmp_path, record):
    root=tmp_path/'source'
    index=[dict(ordinal=0,session=record['session'])]
    monkeypatch.setattr(fixture,'study',study)
    monkeypatch.setattr(study,'authenticate',lambda inputs:(root/'COMPLETE.json',root,index,
        dict(constructed_only=True,module_sha256=study.io.sha(study.__file__))))
    monkeypatch.setattr(study.source,'source_record',lambda *args:record)


@pytest.mark.parametrize('case',['intake_parse_failed','replay_parse_failed','no_supported_timing'])
def test_unsupported_content_stays_operational_and_explicit(tmp_path,monkeypatch,case):
    session=fixture.Session()
    if case=='intake_parse_failed':
        record=dict(session='constructed',status='parse_failed',reason='constructed parse failure')
    elif case=='replay_parse_failed':
        session.type('bad');record=session.record('constructed');record['final_text']='different\n'
    else:
        session.add('Input','bulk',4);record=session.record('constructed')
    bind_one(monkeypatch,tmp_path,record)
    config=dict(phase='EX4',max_new_draws=1,max_wall_seconds=30)
    first=tmp_path/'first';second=tmp_path/'second';third=tmp_path/'third'
    prefix=study.execute(first/'output',{},config);operation(prefix)
    assert prefix['status']=='yielded' and prefix['completed']==1
    fixture.continuation(first,second,'execute')
    result=study.execute(second/'output',{},config);operation(result)
    verification_prefix=study.verify(second/'output',{},config);operation(verification_prefix)
    assert verification_prefix['verified'] is False
    fixture.continuation(second,third,'verify')
    operation(study.execute(third/'output',{},config))
    proof=study.verify(third/'output',{},config);operation(proof)
    assert proof['verified'] is True and result['source_sessions']==1
    if case!='no_supported_timing':
        assert result['session_status']=={case:1}
        assert not (third/'output/bundle/sessions/00000.json').exists()
    else:
        value=json.loads((third/'output/bundle/sessions/00000.json').read_text())
        assert len(value['words'])==1 and value['words'][0]['pause_seconds'] is None
        assert value['words'][0]['stop_2_seconds'] is None
        assert value['words'][0]['stop_essay_p80'] is None
    assert result['scientific_inference'] is False


def test_current_owner_yield_returns_operation_metadata(tmp_path,monkeypatch):
    session=fixture.Session();session.type('word');bind_one(monkeypatch,tmp_path,session.record())
    output=tmp_path/'run/output'
    study.io.write_json(output/'YIELD_REQUEST.json',dict(reason='constructed current request'))
    result=study.execute(output,{},dict(phase='EX4',max_new_draws=1,max_wall_seconds=30))
    operation(result)
    assert result['status']=='yielded' and result['phase']=='session_replay' and result['completed']==0
    assert not (output/'RESULT.json').exists()


def test_integrity_exception_is_not_converted_to_metadata_success(tmp_path,monkeypatch):
    session=fixture.Session();session.type('word');bind_one(monkeypatch,tmp_path,session.record())
    def bad_record(*args):
        raise ValueError('Changed native source hash')
    monkeypatch.setattr(study.source,'source_record',bad_record)
    output=tmp_path/'run/output'
    with pytest.raises(ValueError,match='Changed native source hash'):
        study.execute(output,{},dict(phase='EX4'))
    assert not (output/'RESULT.json').exists()


def test_v2_checkpoint_cannot_cross_to_v3(tmp_path,monkeypatch):
    first=tmp_path/'first';second=tmp_path/'second'
    original.sealed.checkpoint(first/'output/CHECKPOINT.json',dict(binding='fixed',rows=[],pilot_released=True,operation='execute'))
    monkeypatch.setattr(fixture,'study',original)
    fixture.continuation(first,second,'execute')
    with pytest.raises(ValueError,match='producer differs'):
        study.resume_state(second/'output/CHECKPOINT.json','fixed')
