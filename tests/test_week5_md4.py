import numpy as np
import pandas as pd
import pytest
import json
from runners.drive.cards import week5_md4_source as s,week5_md4_analysis as a
from runners.drive.cards.week5_md4_fixture import fixture_rows,construct,write_csv

def project(rows,cohort='Recovery1'):
    return s.event_projection(sorted(set().union(*(r.keys() for r in rows))),rows,cohort)

def test_author_clock_and_first_block():
    rows=fixture_rows('Recovery1','constructed',-.01);actual,counts=project(rows)
    assert len(actual)==19 and actual[-1]['minute']==9
    assert actual[1]['minute']==.5 and actual[1]['mood']==.695
    assert actual==s.event_projection(sorted(set().union(*(r.keys() for r in rows))),rows,'Recovery1',True)[0]

def test_local_join_preserves_large_numeric_codes():
    assert s.token('9007199254740993')=='9007199254740993'
    assert s.token('9007199254740992')!=s.token('9007199254740993')
    assert s.token('001.0')=='1' and s.token('NaN')==''

def test_random_string_choices_advance_clock():
    actual,_=project(fixture_rows('Stability01-RandomVer2','constructed',-.008),'Stability01-RandomVer2')
    assert abs(actual[-1]['minute']-3.9)<1e-12

def test_ordinal_default_frequency_and_missing_rt():
    rows=[{'blockHappyResp.keys':9,'freqMult':2},{'happyResp.keys':5,'returnLoop.ran':1}, {'happyResp.keys':1,'returnLoop.ran':1}]
    actual,counts=project(rows,'Numbers')
    assert [r['mood'] for r in actual]==[1,.5,0]
    assert actual[-1]['minute']==27/60 and counts['response_time_protocol_fallbacks']==3

def test_missing_event_and_metadata_refused():
    rows=fixture_rows('Recovery1','constructed',-.01);del rows[2]['happySlider.response']
    with pytest.raises(ValueError,match='missing planned'):project(rows)
    rows=fixture_rows('Motion','constructed',-.01);rows[0]['expName']='wrong'
    with pytest.raises(ValueError,match='metadata'):project(rows,'Motion')
    rows=fixture_rows('Stability01-RandomVer2','constructed',-.01);rows[0]['condition']='closed'
    with pytest.raises(ValueError,match='metadata'):project(rows,'Stability01-RandomVer2')

def test_completion_and_duplicate_integrity(tmp_path):
    inputs=construct(tmp_path/'source');output=tmp_path/'out';config={'constructed_fixture':True}
    s.execute(output,inputs,config);assert s.verify(output,inputs,config)['ratings']==72*19
    frame=pd.read_parquet(output/'PRIVATE_RATINGS.parquet');assert frame.person.nunique()==72
    assert all(len(x)==64 for x in frame.person.unique())

def test_equal_person_weighting_and_ols_oracle():
    rows=[]
    for p,n,b in [(0,4,-.01),(1,10,-.03)]:
        for i in range(n):rows.append(dict(person=str(p),cohort='Recovery1',condition='rest',rating_order=i,minute=float(i),mood=.8+b*i))
    frame=pd.DataFrame(rows);normal,_=a.slopes(frame);oracle,_=a.slopes(frame,independent=True)
    assert np.allclose([r['slope'] for r in normal],[r['slope'] for r in oracle])
    assert abs(a.summarize(normal,20)['conditions']['rest']['slope']+.02)<1e-12

def test_three_way_bar_and_floor():
    assert a.rule([.003,.004],[-.01,-.005])=='supports'
    assert a.rule([-.001,.001],[-.01,-.005])=='against'
    assert a.rule([-.004,-.003],[-.01,-.005])=='against'
    assert a.rule([.001,.003],[-.01,-.005])=='inconclusive'
    assert a.rule([.003,.004],[.001,.002])=='inconclusive'
    assert a.rule([.003,.004],[-.01,-.005],False)=='inconclusive'

def test_duplicate_conflict_and_completion_refusals(tmp_path):
    source=tmp_path/'source';inputs=construct(source);manifest=json.loads((source/'SANITIZATION_MANIFEST.json').read_text())
    copy=dict(manifest['files'][0]);copy['file']='working/duplicate.csv'
    write_csv(source/copy['file'],fixture_rows('Recovery1','0',-.01));copy['sha256']=s.sha(source/copy['file']);manifest['files'].append(copy)
    changed=dict(copy,file='working/conflict.csv');write_csv(source/changed['file'],fixture_rows('Recovery1','1',-.02));changed['sha256']=s.sha(source/changed['file']);manifest['files'].append(changed)
    mapping=json.loads((source/'cohort-map.json').read_text());check=mapping['cohort_data_checks']['Recovery1'];path=source/check['file']
    write_csv(path,[{'participant':str(i),'isComplete':str(i!=2)} for i in range(24)])
    check['sha256']=s.sha(path);s.save(source/'cohort-map.json',mapping);inputs['cohort_map_sha256']=s.sha(source/'cohort-map.json')
    s.save(source/'SANITIZATION_MANIFEST.json',manifest)
    counts=s.execute(tmp_path/'out',inputs,{'constructed_fixture':True})
    c=counts['cohorts']['Recovery1'];assert c['retained_people']==22 and c['identical_task_copies_collapsed']==1
    assert c['conflicting_task_copies_excluded']==2 and c['not_completed_in_DataCheck']==1
    assert s.verify(tmp_path/'out',inputs,{'constructed_fixture':True})['verified']

def test_source_pin_and_cooperative_yield(tmp_path):
    source=tmp_path/'source';inputs=construct(source);output=tmp_path/'yield';output.mkdir()
    s.save(output/'YIELD_REQUEST.json',{'reason':'constructed pause'})
    result=s.execute(output,inputs,{'constructed_fixture':True})
    assert result['status']=='yielded' and not (output/'SOURCE.json').exists()
    manifest=json.loads((source/'SANITIZATION_MANIFEST.json').read_text());path=source/manifest['files'][0]['file'];path.write_text('changed')
    with pytest.raises(ValueError,match='pin mismatch'):s.execute(tmp_path/'changed',inputs,{'constructed_fixture':True})

def test_invalid_time_and_mood_refused():
    rows=fixture_rows('Recovery1','constructed',-.01);rows[2]['iriDur']=30
    with pytest.raises(ValueError,match='changing timing'):project(rows)
    rows=fixture_rows('Recovery1','constructed',-.01);rows[2]['happySlider.response']=2
    with pytest.raises(ValueError,match='unit interval'):project(rows)

def test_consumer_cooperative_yield_and_output_authentication(tmp_path):
    inputs=construct(tmp_path/'source');config={'constructed_fixture':True,'draws':2000};source=tmp_path/'projection'
    s.execute(source,inputs,config);s.verify(source,inputs,config);analysis_inputs={'ratings':str(source/'PRIVATE_RATINGS.parquet')}
    output=tmp_path/'analysis';output.mkdir();s.save(output/'YIELD_REQUEST.json',{'reason':'constructed pause'})
    assert a.execute(output,analysis_inputs,config)['status']=='yielded'
    assert not (output/'SCIENCE.json').exists()
    receipt=json.loads((source/'SOURCE.json').read_text());receipt['ratings_sha256']='changed';s.save(source/'SOURCE.json',receipt)
    with pytest.raises(ValueError,match='changed'):a.load(analysis_inputs,config)
