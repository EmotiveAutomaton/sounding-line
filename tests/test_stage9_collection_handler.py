"""Actual input-boundary guards shared by scientific and discarded collection."""
import copy
import pytest
from runners.stage9 import scientific_collector as collector,training_jobs as jobs
from runners.stage9.common import digest,file_hash,read,write
from runners.stage9.train import BASES


def pilot(tmp_path,monkeypatch):
    monkeypatch.setattr(collector,'ROOT',tmp_path)
    monkeypatch.setattr(collector,'parameter_partition',lambda w:w['partition'])
    pool={'examples':[{'key':str(i),'raw_record':{'domain':'a' if i<32 else 'b'}} for i in range(64)],
        'worlds':{str(i):{'partition':'training'} for i in range(64)}}
    write(tmp_path/'private/pilot-dose/qwen/POOL.json',pool)
    source=tmp_path/'discarded.json';write(source,{'identity':{'pool_sha256':digest(pool)}})
    monkeypatch.setattr(jobs,'rehearsal_input',lambda family:(source,{}))
    training=tmp_path/'private/training-handler-pilots/v2/qwen/fit'
    fitted={'family':'qwen','base':BASES['qwen'],'split':'pilot','seed':997901,'corpus_sha256':file_hash(source)}
    write(training/'IDENTITY.json',fitted);write(training/'COMPLETE.json',{'identity_sha256':digest(fitted)})
    write(training.parent/'COMPLETE.json',{'scope':'discarded-rehearsal','operation':'fit',
        'training_complete_sha256':file_hash(training/'COMPLETE.json')})
    return training


def test_discarded_checkpoint_never_enters_scientific_collection(tmp_path,monkeypatch):
    training=pilot(tmp_path,monkeypatch)
    _,_,pool,chosen=collector.collection_inputs('qwen','both',training,rehearsal=True)
    assert len(pool['candidate_examples'])==64 and len(chosen)==32
    with pytest.raises(ValueError,match='never a discarded pilot'):
        collector.collection_inputs('qwen','both',training)
    with pytest.raises(ValueError,match='original-law'):
        collector.collection_inputs('qwen','original',training,rehearsal=True)


def test_changed_pool_and_checkpoint_dispatch_refuse(tmp_path,monkeypatch):
    training=pilot(tmp_path,monkeypatch)
    path=tmp_path/'private/pilot-dose/qwen/POOL.json';old=read(path);changed=copy.deepcopy(old)
    changed['worlds']['0']['partition']='reserve';write(path,changed)
    with pytest.raises(ValueError,match='source worlds differ'):
        collector.collection_inputs('qwen','both',training,rehearsal=True)
    write(path,old)
    dispatch=read(training.parent/'COMPLETE.json');dispatch['training_complete_sha256']='changed'
    write(training.parent/'COMPLETE.json',dispatch)
    with pytest.raises(ValueError,match='actual completed'):
        collector.collection_inputs('qwen','both',training,rehearsal=True)


def test_namespace_and_identification_refuse_before_model_loading(tmp_path,monkeypatch):
    monkeypatch.setattr(collector,'ROOT',tmp_path);monkeypatch.setattr(jobs,'ROOT',tmp_path)
    monkeypatch.setattr(collector,'register',lambda:None)
    monkeypatch.setattr(collector,'collection_inputs',lambda *a,**k:pytest.fail('invalid scope reached model inputs'))
    monkeypatch.delenv('S9_CELL_IDENTITY',raising=False)
    with pytest.raises(ValueError,match='queue cell identity'):
        collector.run('qwen','both',tmp_path/'fit',tmp_path/'outside',rehearsal=True)
    monkeypatch.setenv('S9_CELL_IDENTITY','a'*64)
    with pytest.raises(ValueError,match='pilot namespace'):
        collector.run('qwen','both',tmp_path/'fit',tmp_path/'private/scientific-collection/qwen/both',rehearsal=True)
    with pytest.raises(ValueError,match='scientific collection output'):
        collector.run('qwen','both',tmp_path/'fit',tmp_path/'outside')


def test_actual_parameter_roles_are_never_relabeled_for_scientific_use(tmp_path,monkeypatch):
    training=pilot(tmp_path,monkeypatch)
    source=tmp_path/'private/scientific-recipes/qwen/original_expert.json';write(source,{'split':'training'})
    identity=read(training/'IDENTITY.json')|{'split':'training','seed':9001,'corpus_sha256':file_hash(source)}
    write(training/'IDENTITY.json',identity);write(training/'COMPLETE.json',{'identity_sha256':digest(identity)})
    pool={'candidate_examples':[{'key':str(i),'raw_record':{'domain':'a' if i<800 else 'b'}} for i in range(1600)],
        'private_worlds':{'0':{'partition':'reserve'}}}
    write(tmp_path/'private/training-pools/qwen/both.json',pool)
    with pytest.raises(ValueError,match='held-out parameter'):
        collector.collection_inputs('qwen','both',training)
    pool['private_worlds']['0']['partition']='training';write(tmp_path/'private/training-pools/qwen/both.json',pool)
    assert len(collector.collection_inputs('qwen','both',training)[3])==800
