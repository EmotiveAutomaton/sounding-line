"""Released-edit raw audit composition guards; actual full replay is separate."""
import copy

import pytest

from runners.stage9 import closure_raw as subject, scholawrite, common, queue
from runners.stage9.common import closure, digest, file_hash, read, write


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    for module in (subject, common, queue):
        monkeypatch.setattr(module, 'REPO', tmp_path)
    monkeypatch.setattr(queue, 'ROOT', tmp_path)
    prepared=tmp_path/'prepared';archive=tmp_path/'archive';raw=tmp_path/'raw/released.json'
    raw.parent.mkdir();raw.write_text('original already-exposed released rows')
    files={}
    for name in ('runners/stage9/scholawrite.py','runners/stage9/common.py'):
        path=archive/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('literal original source '+name)
        files[name]=file_hash(path)
    source={'files':files,'sha256':digest(files)};write(archive/'SOURCE.json',source)
    identity={'code':source,'source_files':closure([raw]),'exposure':'already exposed',
              'grouping':'project-scoped authors','rights':'private authorized fixture'}
    projects={'one':{'texts':{'t':'literal editor state'},'records':[
        {'source_ordinal':0,'usable':False,'exclusion':'time tie','next_source_ordinal':None}]}}
    write(prepared/'projects/one.json',projects['one'])
    ledger=[{'unit':'one','path':'projects/one.json','sha256':file_hash(prepared/'projects/one.json'),
             'attempted':1,'usable':0,'authors':1,'sessions':1}]
    summary={'source_counts_match':True,'reserve_groups':0,'projects':1,'source_rows':1,
             'project_scoped_author_ids':1,'global_people_count':'not inferable from project-scoped IDs',
             'exclusions':{'time tie':1}}
    write(prepared/'IDENTITY.json',identity);write(prepared/'LEDGER.json',ledger)
    write(prepared/'COMPLETE.json',{'identity_sha256':digest(identity),**summary,'elapsed_seconds':1.,'completed_at':2.})
    monkeypatch.setattr(scholawrite,'raw_inputs',lambda:(raw.parent,{**copy.deepcopy(identity),'source_files':closure([raw])}))
    monkeypatch.setattr(scholawrite,'reconstruct',lambda _:copy.deepcopy((projects,ledger,summary)))
    return prepared,archive,raw


def change(path,key,value):
    row=read(path);row[key]=value;write(path,row)


def test_all_released_payloads_and_source_scoped_identity_reconstruct_without_writes(fixture):
    prepared,archive,raw=fixture;before=closure([prepared,archive,raw])
    row=subject.scholawrite(prepared,archive)
    assert row['status']=='RECONSTRUCTED' and row['released_rows']==row['projects']==1
    assert row['global_people_count']=='not inferable from project-scoped IDs'
    assert row['new_fits']==row['new_reader_calls']==row['new_reserve_openings']==0
    assert not row['scientific_admission'] and closure([prepared,archive,raw])==before


@pytest.mark.parametrize('fault',['raw','source','source_map','identity','source_counts','reserve',
    'ledger','extra_project','missing_project','successor','summary','time'])
def test_released_edit_raw_audit_refuses_changed_source_or_saved_derivation(fixture,fault):
    prepared,archive,raw=fixture
    if fault=='raw':raw.write_text('changed released rows')
    elif fault=='source':(archive/'runners/stage9/scholawrite.py').write_text('changed source')
    elif fault=='source_map':write(archive/'SOURCE.json',{'files':{}})
    elif fault=='identity':change(prepared/'COMPLETE.json','identity_sha256','wrong')
    elif fault=='source_counts':change(prepared/'COMPLETE.json','source_counts_match',False)
    elif fault=='reserve':change(prepared/'COMPLETE.json','reserve_groups',1)
    elif fault=='ledger':write(prepared/'LEDGER.json',[])
    elif fault=='extra_project':write(prepared/'projects/extra.json',{})
    elif fault=='missing_project':(prepared/'projects/one.json').unlink()
    elif fault=='successor':change(prepared/'projects/one.json','records',[{'usable':True,'next_source_ordinal':1}])
    elif fault=='summary':change(prepared/'COMPLETE.json','global_people_count',1)
    else:change(prepared/'COMPLETE.json','elapsed_seconds',-1)
    with pytest.raises((ValueError,FileNotFoundError)):
        subject.scholawrite(prepared,archive)


@pytest.mark.parametrize('fault',[None,'wrong_dataset','wrong_operation','unlinked_input'])
def test_raw_review_binds_actual_scholawrite_case_producer(fixture,monkeypatch,tmp_path,fault):
    prepared,archive,raw=fixture
    job={'id':'cases','module':'runners.stage9.record_jobs','produces':'cases/COMPLETE.json'}
    plan={'raw_source_reviews':{'cases':{'kind':'scholawrite','prepared':'prepared','source_archive':'archive'}}}
    write(tmp_path/'queue/STATUS.json',{'jobs':{'cases':{'status':'COMPLETE'}}})
    identity={'operation':'record-cases-v1','dataset':'scholawrite',
              'prepared_complete_sha256':file_hash(prepared/'COMPLETE.json')}
    if fault=='wrong_dataset':identity['dataset']='coauthor'
    elif fault=='wrong_operation':identity['operation']='record-fit-v1'
    elif fault=='unlinked_input':identity['prepared_complete_sha256']='different'
    write(tmp_path/'cases/IDENTITY.json',identity)
    monkeypatch.setattr(subject,'verify_committed',lambda *args:None)
    if fault:
        with pytest.raises(ValueError):subject.queue_audits(plan,tmp_path/'queue',{'cases':job})
    else:
        row=subject.queue_audits(plan,tmp_path/'queue',{'cases':job})['jobs']['cases']
        assert row['prepared_complete_sha256']==identity['prepared_complete_sha256']


def test_failed_raw_producer_retains_disposition_without_opening_released_rows(fixture,monkeypatch,tmp_path):
    prepared,archive,raw=fixture
    state={'status':'FAILED','reason':'original source refusal','disposition_sha256':'literal'}
    write(tmp_path/'queue/STATUS.json',{'jobs':{'cases':state}})
    monkeypatch.setattr(scholawrite,'raw_inputs',lambda:pytest.fail('failed producer opened raw input'))
    plan={'raw_source_reviews':{'cases':{'kind':'scholawrite','prepared':'prepared','source_archive':'archive'}}}
    prior={'cases':{'module':'runners.stage9.record_jobs'}}
    assert subject.queue_audits(plan,tmp_path/'queue',prior)['jobs']['cases']==state
