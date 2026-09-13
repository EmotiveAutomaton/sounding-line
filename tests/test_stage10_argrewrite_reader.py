from dataclasses import asdict
import copy
import pytest
from runners.stage10 import argrewrite_reader as worker,revision_bank,ollama,comparison_bank
from runners.stage10.contracts import digest
from runners.stage10.queue import read
from runners.stage10.ollama import write_new
from tests.test_stage10_revision import fake_model


def test_whole_cycle_context_does_not_use_future_location_and_complete_anchor(tmp_path,monkeypatch):
    calls=[];fake_model(monkeypatch,calls)
    monkeypatch.setattr(revision_bank,'GPU_LOCK',tmp_path/'lock')
    monkeypatch.setattr(revision_bank,'acquire_gpu_lock',lambda *a:None);monkeypatch.setattr(revision_bank,'release_gpu_lock',lambda:None)
    essays=[]
    for i in range(8):
        essays.append({'group':str(i),'future_usable':True,'drafts':{'1':'first line\nold claim','2':'first line\nnew claim','3':'future unavailable'},
          'units':[{'key':digest([i,cycle,j]),'fine':c,'usable':True,'cycle':cycle} for cycle in ['12','23'] for j,c in enumerate(['claim','evidence'])]})
    old=worker.project(essays[0],'process-record');changed=copy.deepcopy(essays[0]);changed['drafts']['3']='different future';changed['units'][-1]['fine']='organization'
    assert worker.project(changed,'process-record').public()==old.public()
    assert 'explicit_earlier_diff' in old.evidence
    root=tmp_path/'canonical';identity={'fixture':True};write_new(root/'IDENTITY.json',identity)
    write_new(root/'COMPLETE.json',{'identity_sha256':digest(identity),'historical_v4_exact':True,'essay_student_lineages':8})
    for i,e in enumerate(essays):write_new(root/'essays'/f'{i}.json',e)
    prepared=tmp_path/'prepared';worker.prepare(prepared,root=root)
    pilot=tmp_path/'pilot';assert worker.run(prepared,pilot,'pilot')['admitted']
    prediction=tmp_path/'prediction';worker.run(prepared,prediction,'evaluation',pilot)
    n=len(calls);monkeypatch.setattr(ollama,'api',lambda *a,**k:(_ for _ in ()).throw(AssertionError('new call')))
    worker.run(prepared,prediction,'evaluation',pilot)
    output=tmp_path/'analysis-inputs';worker.analyze(prepared,prediction,output)
    result=comparison_bank.analyze(read(output/'BUNDLE.json'))
    assert len(calls)==n and len(result['results'])==2
    assert all(c['paired']['R2 vs R0']['brier']['estimate']==0 for c in result['results'])
    assert all(c['costs']['R0']['model_calls']==2 for c in result['results'])
