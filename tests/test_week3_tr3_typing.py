import copy
import json
import pytest
from runners.drive.cards import week3_tr3_typing as m


def fixture():
    identity=dict(session='s',writer='w',prompt='p')
    events=[dict(eventName='system-initialize',eventTimestamp=0,currentDoc='\n'),
        dict(eventName='text-insert',eventTimestamp=1,eventSource='user',textDelta={'ops':[{'insert':'A\U0001f600 B'}]}),
        dict(eventName='text-insert',eventTimestamp=2,eventSource='api',textDelta={'ops':[{'retain':6},{'insert':'API'}]}),
        dict(eventName='text-insert',eventTimestamp=3,eventSource='user',textDelta={'ops':[{'retain':1},{'delete':2},{'insert':'Z'}]}),
        dict(eventName='text-insert',eventTimestamp=4,eventSource=None,textDelta={'ops':[{'insert':'?'}]})]
    return dict(sessions=[dict(meta=dict(**identity,timestamp=0,end_at=5),events=events,
        timeline=dict(**identity,final_document='?AZ B\nAPI'),
        canonical=dict(final_document='?AZ B\nAPI'),
        exposure=dict(**identity,start=0,end=5,typed_inserted_characters=5))])


def test_unicode_sources_deleted_production_and_actual_context():
    r=m.prepare(**fixture()['sessions'][0])
    assert r['user_inserted_characters']==5 and r['final_user_characters']==4
    assert r['final_document']=='?AZ B\nAPI'
    assert len(r['edits'])==4 and r['edits'][0]['operations'][0]['insert']=='A\U0001f600 B'
    assert r['edits'][2]['operations']==[{'retain':1},{'delete':2},{'insert':'Z'}]
    assert sum(x['characters'] for x in r['final_ownership_runs'] if x['source']=='api')==3
    assert r['final_ownership_runs'][0]['source'] is None
    assert not r['outcome_features_prepared']


@pytest.mark.parametrize('fault',['final','identity','count','clock','surrogate','repeat-init'])
def test_invalid_source_refused(fault):
    f=copy.deepcopy(fixture()['sessions'][0])
    if fault=='final':f['canonical']['final_document']='different'
    elif fault=='identity':f['exposure']['writer']='different'
    elif fault=='count':f['exposure']['typed_inserted_characters']=4
    elif fault=='clock':f['events'][2]['eventTimestamp']=0
    elif fault=='repeat-init':f['events'][2]['eventName']='system-initialize'
    else:f['events'][3]['textDelta']['ops'][1]['delete']=1
    with pytest.raises((ValueError,UnicodeError)):m.prepare(**f)


def test_empty_document_and_no_edit_retained():
    f=fixture()['sessions'][0];f['events']=f['events'][:1]
    f['events'][0]['currentDoc']='';f['timeline']['final_document']='';f['canonical']['final_document']=''
    f['exposure']['typed_inserted_characters']=0
    r=m.prepare(**f)
    assert r['edits']==[] and r['final_ownership_runs']==[] and r['user_inserted_characters']==0


def test_complete_serialized_replay_and_tamper(tmp_path):
    f=tmp_path/'fixture.json';f.write_text(json.dumps(fixture()),encoding='utf8')
    inputs={'fixture':str(f)};config=dict(mode='constructed',seed=20261026);out=tmp_path/'output'
    first=m.execute(out,inputs,config)
    assert m.execute(out,inputs,config)==first
    assert m.verify(out,inputs,config)['complete_typing_replay']
    (out/'SUMMARY.json').write_text('{}')
    with pytest.raises(ValueError,match='aggregate'):m.verify(out,inputs,config)
