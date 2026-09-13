from dataclasses import asdict
import json
import pytest
from runners.stage10 import local_comparator as worker, human_memory as memory, human_memory_checks as fixture, revision_bank, ollama
from runners.stage10.contracts import digest
from runners.stage10.queue import read
from runners.stage10.ollama import write_new
from tests.test_stage10_revision import fake_model


def test_frozen_local_model_whole_bank_and_private_answer_refusal(tmp_path,monkeypatch):
    calls=[];fake_model(monkeypatch,calls)
    monkeypatch.setattr(revision_bank,'GPU_LOCK',tmp_path/'lock')
    monkeypatch.setattr(revision_bank,'acquire_gpu_lock',lambda *a:None);monkeypatch.setattr(revision_bank,'release_gpu_lock',lambda:None)
    training,answers=fixture.rows();prepared=tmp_path/'prepared';learned=tmp_path/'memory'
    for r in answers:r['prompt_component']='training-'+r['writer_component']
    test=asdict(fixture.task(900,4));pilot_task=asdict(fixture.task(901,3))
    evaluation={'tasks':[test]};labels={'targets':[{'task_id':test['task_id'],'correct_choice':test['choices'][0][0],
       'writer_component':'held-out','prompt_component':'held-out-prompt','source_event':'future-event'}]}
    frozen={'public_sha256':{'train':digest({'tasks':training}),'evaluation':digest(evaluation)},
            'evaluator_sha256':{'train':digest({'targets':answers}),'evaluation':digest(labels)}}
    for name,obj in [('FROZEN.json',frozen),('train-public.json',{'tasks':training}),('train-evaluator.json',{'targets':answers}),
                     ('evaluation-public.json',evaluation),('evaluation-evaluator.json',labels)]:write_new(prepared/name,obj)
    memory.fit(prepared,learned)
    pilot_source=tmp_path/'discarded';public={'tasks':[pilot_task]}
    write_new(pilot_source/'FROZEN.json',{'scope':'discarded legacy pilot writer, excluded from the scientific cohort','public_sha256':{'development':digest(public)}})
    write_new(pilot_source/'development-public.json',public)
    rival=tmp_path/'rival';write_new(rival/'FROZEN.json',{'fit':{'chosen':'R4-grounded','rule':'constructed development-only decision'},'input_files':{}})
    selection=tmp_path/'selection';worker.select(prepared,pilot_source,learned,rival,selection)
    default=ollama.MODEL
    pilot=tmp_path/'pilot';assert worker.run(selection,pilot,'pilot')['admitted']
    assert ollama.MODEL==default and all(r['model']==worker.MODEL for r in calls)
    original=worker.read
    def guard(path):
        if path.name=='evaluation-evaluator.json':raise AssertionError('evaluation producer opened target')
        return original(path)
    monkeypatch.setattr(worker,'read',guard)
    science=tmp_path/'science';worker.run(selection,science,'evaluation',pilot)
    monkeypatch.setattr(ollama,'api',lambda *a,**k:(_ for _ in ()).throw(AssertionError('replay called model')))
    worker.run(selection,science,'evaluation',pilot)
    (science/'extra.json').write_text('{}')
    with pytest.raises(ValueError,match='inventory'):worker.run(selection,science,'evaluation',pilot)


def test_model_profile_restores_on_exception():
    before=(ollama.MODEL,ollama.MODEL_DIGEST)
    with pytest.raises(RuntimeError):
        with worker.profile():
            assert ollama.MODEL==worker.MODEL
            raise RuntimeError('known fault')
    assert (ollama.MODEL,ollama.MODEL_DIGEST)==before
