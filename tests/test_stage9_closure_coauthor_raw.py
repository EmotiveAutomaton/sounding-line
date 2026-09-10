"""Original mixed-agency source reconstruction and rejection of altered evidence."""
import copy
import json

import pytest

from runners.stage9 import closure_raw as subject, coauthor, common, queue
from runners.stage9.common import closure, digest, file_hash, read, write


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    for module in (subject, common, queue):
        monkeypatch.setattr(module, 'REPO', tmp_path)
    monkeypatch.setattr(queue, 'ROOT', tmp_path)
    prepared=tmp_path/'prepared';archive=tmp_path/'archive';raw=tmp_path/'raw/log.jsonl'
    raw.parent.mkdir();raw.write_text('original already-exposed event log')
    files={}
    for name in ('runners/stage9/coauthor.py','runners/stage9/common.py'):
        path=archive/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('original '+name)
        files[name]=file_hash(path)
    source={'files':files,'sha256':digest(files)};write(archive/'SOURCE.json',source)
    identity={'sources':source,'source_files':{'session':file_hash(raw)},
              'metadata_sources':{'creative':'original metadata'},'reserve':'none: previously exposed'}
    sessions={'one':{'final_document':'a😀Z\n','source_checks':{'query_count':False},
                     'events':[{'decision':'edit','usable':False,'logged_index_agrees':False}]}}
    write(prepared/'sessions/one.json',sessions['one'])
    ledger=[{'key':'one','usable':False,'reason':'published count differs'},
            {'key':'extra','usable':False,'reason':'local log absent from released task metadata'}]
    summary={'reserve_groups':0,'scientific_launch_accepted':False,'local_files':2,
             'published_sessions':1,'extra_local_files':1,'usable_sessions':0,
             'metadata_writers':1,'website_writers':2,'writer_count_reproduced':False}
    write(prepared/'IDENTITY.json',identity);write(prepared/'LEDGER.json',ledger)
    write(prepared/'COMPLETE.json',{'identity_sha256':digest(identity),**summary,'elapsed_seconds':1.,'completed_at':2.})
    monkeypatch.setattr(coauthor,'raw_inputs',lambda:([raw],{},
        {**copy.deepcopy(identity),'source_files':{'session':file_hash(raw)}}))
    monkeypatch.setattr(coauthor,'reconstruct',lambda *_:copy.deepcopy((sessions,ledger,summary)))
    return prepared,archive,raw


def change(path,key,value):
    row=read(path);row[key]=value;write(path,row)


def test_original_exclusions_count_disagreement_and_records_reconstruct_read_only(fixture):
    prepared,archive,raw=fixture;before=closure([prepared,archive,raw])
    row=subject.coauthor(prepared,archive)
    assert row['status']=='RECONSTRUCTED' and row['published_sessions']==1 and row['local_files']==2
    assert not row['writer_count_reproduced'] and row['usable_sessions']==0
    assert row['new_fits']==row['new_reader_calls']==row['new_reserve_openings']==0
    assert not row['scientific_admission'] and closure([prepared,archive,raw])==before


@pytest.mark.parametrize('fault',['raw','source','source_map','identity','reserve','admission',
    'ledger','extra_session','missing_session','handling','summary','time'])
def test_raw_session_audit_refuses_changed_inputs_or_saved_derivation(fixture,fault):
    prepared,archive,raw=fixture
    if fault=='raw':raw.write_text('changed event log')
    elif fault=='source':(archive/'runners/stage9/coauthor.py').write_text('changed source')
    elif fault=='source_map':write(archive/'SOURCE.json',{'files':{}})
    elif fault=='identity':change(prepared/'COMPLETE.json','identity_sha256','wrong')
    elif fault=='reserve':change(prepared/'COMPLETE.json','reserve_groups',1)
    elif fault=='admission':change(prepared/'COMPLETE.json','scientific_launch_accepted',True)
    elif fault=='ledger':write(prepared/'LEDGER.json',[])
    elif fault=='extra_session':write(prepared/'sessions/extra.json',{})
    elif fault=='missing_session':(prepared/'sessions/one.json').unlink()
    elif fault=='handling':change(prepared/'sessions/one.json','events',[{'decision':'accept','usable':True}])
    elif fault=='summary':change(prepared/'COMPLETE.json','writer_count_reproduced',True)
    else:change(prepared/'COMPLETE.json','elapsed_seconds',-1)
    with pytest.raises((ValueError,FileNotFoundError)):
        subject.coauthor(prepared,archive)


@pytest.mark.parametrize('fault',[None,'wrong_dataset','wrong_operation','unlinked_input'])
def test_raw_review_binds_actual_coauthor_case_producer(fixture,monkeypatch,tmp_path,fault):
    prepared,archive,raw=fixture
    job={'id':'cases','module':'runners.stage9.record_jobs','produces':'cases/COMPLETE.json'}
    plan={'raw_source_reviews':{'cases':{'kind':'coauthor','prepared':'prepared','source_archive':'archive'}}}
    write(tmp_path/'queue/STATUS.json',{'jobs':{'cases':{'status':'COMPLETE'}}})
    identity={'operation':'record-cases-v1','dataset':'coauthor',
              'prepared_complete_sha256':file_hash(prepared/'COMPLETE.json')}
    if fault=='wrong_dataset':identity['dataset']='scholawrite'
    elif fault=='wrong_operation':identity['operation']='record-fit-v1'
    elif fault=='unlinked_input':identity['prepared_complete_sha256']='different'
    write(tmp_path/'cases/IDENTITY.json',identity)
    monkeypatch.setattr(subject,'verify_committed',lambda *args:None)
    if fault:
        with pytest.raises(ValueError):subject.queue_audits(plan,tmp_path/'queue',{'cases':job})
    else:
        row=subject.queue_audits(plan,tmp_path/'queue',{'cases':job})['jobs']['cases']
        assert row['prepared_complete_sha256']==identity['prepared_complete_sha256']


def test_failed_raw_producer_does_not_open_original_sessions(fixture,monkeypatch,tmp_path):
    state={'status':'FAILED','reason':'original source refusal','disposition_sha256':'literal'}
    write(tmp_path/'queue/STATUS.json',{'jobs':{'cases':state}})
    monkeypatch.setattr(coauthor,'raw_inputs',lambda:pytest.fail('failed producer opened raw input'))
    plan={'raw_source_reviews':{'cases':{'kind':'coauthor','prepared':'prepared','source_archive':'archive'}}}
    prior={'cases':{'module':'runners.stage9.record_jobs'}}
    assert subject.queue_audits(plan,tmp_path/'queue',prior)['jobs']['cases']==state


def test_shared_constructor_preserves_unicode_missing_metadata_and_count_failure(tmp_path):
    rows=[{'eventName':'system-initialize','currentDoc':'a😀\n'},
          {'eventName':'suggestion-open','currentSuggestions':[{'index':0,'original':'Z','trimmed':'Z'}]},
          {'eventName':'suggestion-select','currentSuggestionIndex':0},
          {'eventName':'text-insert','eventSource':'api','textDelta':{'ops':[{'retain':3},{'insert':'Z'}]}}]
    own=tmp_path/'own.jsonl';extra=tmp_path/'extra.jsonl'
    own.write_text('\n'.join(json.dumps(r) for r in rows),encoding='utf-8');extra.write_text('not parsed: absent metadata')
    metadata={'own':{'writer':'00000000-writer','prompt':'prompt','domain':'creative',
                     'source_event_count':4,'source_selected_count':1,'source_query_count':2}}
    before=closure([own,extra]);sessions,ledger,summary=coauthor.reconstruct([extra,own],metadata)
    assert len(sessions)==1 and len(ledger)==2 and summary['extra_local_files']==1
    session=next(iter(sessions.values()))
    assert session['final_document']=='a😀Z\n' and session['reconstructed']
    assert not session['usable'] and not session['events'][0]['usable']
    assert summary['usable_sessions']==0 and not summary['writer_count_reproduced']
    assert closure([own,extra])==before


def test_metadata_object_is_hashed_before_parsing_or_session_replay(tmp_path,monkeypatch):
    monkeypatch.setattr(coauthor,'ROOT',tmp_path)
    write(tmp_path/'intake/COAUTHOR_TASK_SOURCE.json',{'metadata':{'sha256':'wrong-hash'}})
    path=tmp_path/'private/intake/objects/wrong-hash';path.parent.mkdir(parents=True);path.write_text('altered metadata')
    with pytest.raises(ValueError,match='metadata bytes'):
        coauthor.raw_inputs()
