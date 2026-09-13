import copy
from pathlib import Path
import pytest
from tests.test_stage10_revision import record,fake_model
from runners.stage10 import revision_source as source, revision_bank as bank, ollama
from runners.stage10.queue import read


def prepared_bank(tmp_path,monkeypatch):
    rows={}
    for lane,groups in [('train',['a','b','c']),('development',['d']),('evaluation',['e'])]:
        rows[lane]=[record(i,g,truth='PLANNING' if kind=='schola_category' else 'first_quarter',kind=kind)
                    for g in groups for i in [0,3,6] for kind in source.DESCRIPTIONS]
    monkeypatch.setattr(source,'inputs',lambda scope,fold:(rows,{'fixture':'known complete chronology'}))
    prepared=tmp_path/'prepared';source.prepare(prepared,per_project=3)
    selection=tmp_path/'selection';bank.select(prepared,selection)
    return prepared,selection


def test_complete_finite_bank_and_replay_never_opens_evaluation_answers(tmp_path,monkeypatch):
    calls=[];fake_model(monkeypatch,calls)
    monkeypatch.setattr(bank,'GPU_LOCK',tmp_path/'lock')
    monkeypatch.setattr(bank,'acquire_gpu_lock',lambda *a:None);monkeypatch.setattr(bank,'release_gpu_lock',lambda:None)
    prepared,selection=prepared_bank(tmp_path,monkeypatch)
    original=bank.read
    def guarded(path):
        if path.name=='evaluation-evaluator.json':raise AssertionError('producer opened held-out answers')
        return original(path)
    monkeypatch.setattr(bank,'read',guarded)
    pilot=tmp_path/'pilot';assert bank.predict(selection,pilot,'pilot')['admitted']
    dev=tmp_path/'development';bank.predict(selection,dev,'development',pilot)
    n=len(calls);policy=tmp_path/'policy';bank.fit(selection,dev,policy)
    assert len(calls)==n
    assert all(not c['admitted'] for c in read(policy/'FIT.json')['policy']['cells'])
    evaluation=tmp_path/'evaluation';bank.predict(selection,evaluation,'evaluation',pilot)
    adaptive=tmp_path/'adaptive';bank.adaptive(selection,policy,adaptive)
    def forbidden(*a,**k):raise AssertionError('replay made an API call')
    monkeypatch.setattr(ollama,'api',forbidden)
    assert bank.predict(selection,pilot,'pilot')['admitted']
    bank.predict(selection,dev,'development',pilot)
    bank.predict(selection,evaluation,'evaluation',pilot);bank.adaptive(selection,policy,adaptive)
    (evaluation/'unexpected.json').write_text('{}')
    with pytest.raises(ValueError,match='inventory'):bank.checked(evaluation)


def test_common_selection_discarded_boundaries_and_changed_training_refusal(tmp_path,monkeypatch):
    _,selection=prepared_bank(tmp_path,monkeypatch)
    declaration=read(selection/'SELECTION.json');excluded=set(declaration['excluded_pilot_boundaries'])
    assert len(excluded)==5
    for lane in ['train','development','evaluation']:
        ids=read(selection/(lane+'-identity.json'))['targets']
        assert not any(r['boundary'] in excluded for r in ids)
        assert len(ids)==12*(3 if lane=='train' else 1)
    (selection/'train-evaluator.json').write_text('{}')
    with pytest.raises(ValueError,match='inventory'):bank.load(selection)


def test_invalid_literal_pilot_cannot_admit_science(tmp_path,monkeypatch):
    calls=[];fake_model(monkeypatch,calls);api=ollama.api
    monkeypatch.setattr(bank,'GPU_LOCK',tmp_path/'lock')
    monkeypatch.setattr(bank,'acquire_gpu_lock',lambda *a:None);monkeypatch.setattr(bank,'release_gpu_lock',lambda:None)
    _,selection=prepared_bank(tmp_path,monkeypatch)
    def truncated(*a,**k):return {**api(*a,**k),'done_reason':'length'}
    monkeypatch.setattr(ollama,'api',truncated)
    pilot=tmp_path/'pilot';assert bank.predict(selection,pilot,'pilot')['admitted'] is False
    with pytest.raises(ValueError,match='literal admission'):bank.predict(selection,tmp_path/'science','evaluation',pilot)
