import copy
import json
from pathlib import Path
import pytest
from runners.drive.cards import engine_habits_input as card
from runners.drive.engine_habits_child import project
from runners.stage14.common import atomic,read,filehash
from tests.test_drive_engine_export_join import case

CONNECTIVES=('and','but','because','however','therefore','although','yet','so')


def fixture():
    records=[]
    for name in ('mixed','unicode'):
        record=copy.deepcopy(case(name)['record'])
        record['document']['keys']['session']='habit-known-'+name
        records.append(record)
    return dict(records=records)


def fake_values(docs):
    raw=dict(words=4,quotedWords=2,connectives={'and':1},punctuation={'!':2},sentenceCount=2,sentenceMean=2.,sentenceSpread=1.,repeats=[])
    return [dict(keys=d['keys'],variant=d['variant'],textSha256=d['textSha256'],inputRecordSha256=card.digest(d),habits=project(raw,CONNECTIVES)) for d in docs]


def test_exact_rate_arithmetic_and_quote_denominator():
    raw=dict(words=4,quotedWords=2,connectives={'and':1},punctuation={'!':2},sentenceCount=2,sentenceMean=2.,sentenceSpread=1.,repeats=[])
    value=project(raw,CONNECTIVES)
    assert value['ratesPer1000UnquotedWords']['and']==250
    assert value['ratesPer1000UnquotedWords']['!']==500
    assert value['quotedWordShare']==1/3
    assert value['sentenceMean']==2 and value['sentenceSpread']==1
    raw.update(words=0,quotedWords=0,sentenceCount=0)
    value=project(raw,CONNECTIVES)
    assert value['rateStatus']=='unsupported-empty-denominator'
    assert all(v is None for v in value['ratesPer1000UnquotedWords'].values())
    assert value['quotedWordShare'] is value['sentenceMean'] is value['sentenceSpread'] is None


def test_typed_boundaries_and_identical_complete_export():
    records=fixture()['records'];docs,fragments=card.documents(records)
    assert docs[1]['text']=='left\n\nright'
    assert '\U0001f600' in docs[2]['text'] and 'e\u0301' in docs[3]['text']
    values=fake_values(docs)
    reference={v['keys']['session']:{k:v[k] for k in ('keys','textSha256','inputRecordSha256','habits')} for v in values if v['variant']=='final-document'}
    rows=card.combine(records,fragments,values,reference)
    assert len(rows)==2 and rows[0]['typed_support']['typed_codepoints']==9
    reference[docs[0]['keys']['session']]['habits']=copy.deepcopy(reference[docs[0]['keys']['session']]['habits'])
    reference[docs[0]['keys']['session']]['habits']['sentenceMean']+=1
    with pytest.raises(ValueError,match='completed reader'):card.combine(records,fragments,values,reference)


def test_no_typed_text_stays_missing():
    import hashlib
    text='initial prompt'
    record=dict(document=dict(keys=dict(session='empty-typed',writer='known',prompt='p'),text=text,
        textSha256=hashlib.sha256(text.encode()).hexdigest(),variant='final-document',
        provenance=[dict(start=0,end=len(text),occurrenceId='initial',source='prompt')]),occurrences=[],
        support=dict(original_occurrences=0,intact_final_occurrences=0,original_words=0,intact_final_words=0))
    docs,fragments=card.documents([record]);assert len(docs)==1
    rows=card.combine([record],fragments,fake_values(docs),None)
    assert rows[0]['typed'] is None and rows[0]['typed_support']['typed_codepoints']==0


@pytest.mark.parametrize('field',['keys','textSha256','inputRecordSha256','duplicate','unexpected'])
def test_corrupted_export_refused(field):
    records=fixture()['records'];docs,fragments=card.documents(records);values=fake_values(docs)
    if field=='keys':values[0]['keys']=dict(values[0]['keys'],writer='changed')
    elif field=='duplicate':values.append(copy.deepcopy(values[0]))
    elif field=='unexpected':values.append(dict(values[0],keys=dict(values[0]['keys'],session='extra')))
    else:values[0][field]='0'*64
    with pytest.raises(ValueError):card.combine(records,fragments,values,None)


def test_full_handler_replay_immutable_reentry_and_output_corruption(tmp_path,monkeypatch):
    data=tmp_path/'fixture.json';atomic(data,fixture());script=tmp_path/'exporter.py';script.write_text('fixture')
    monkeypatch.setattr(card,'EXPORTER_SHA',filehash(script))
    inputs=dict(fixture=str(data),exporter=str(script),export_python=str(script))
    def extract(output,docs,inputs,operation):
        (output/operation).mkdir();return fake_values(docs)
    monkeypatch.setattr(card,'extract',extract)
    out=tmp_path/'output';first=card.execute(out,inputs,card.CONSTRUCTED)
    assert first['identification_not_run'] and not first['scientific_admission'] and not first['reader_executed']
    assert card.verify(out,inputs,card.CONSTRUCTED)['summary']==first
    monkeypatch.setattr(card,'extract',lambda *args:pytest.fail('must reuse completed extraction'))
    assert card.execute(out,inputs,card.CONSTRUCTED)==first
    (out/'SUMMARY.json').write_text('{}')
    with pytest.raises(ValueError):card.execute(out,inputs,card.CONSTRUCTED)


def test_input_corruption_and_unregistered_configuration(tmp_path,monkeypatch):
    data=tmp_path/'fixture.json';atomic(data,fixture());script=tmp_path/'exporter.py';script.write_text('fixture')
    monkeypatch.setattr(card,'EXPORTER_SHA',filehash(script));inputs=dict(fixture=str(data),exporter=str(script),export_python='unused')
    assert len(card.load(inputs,card.CONSTRUCTED)[0])==2
    with pytest.raises(ValueError):card.load(inputs,dict(card.CONSTRUCTED,expected_sessions=3))
    script.write_text('changed')
    with pytest.raises(ValueError,match='exporter'):card.load(inputs,card.CONSTRUCTED)


@pytest.mark.parametrize('stop',['STOP','output/YIELD_REQUEST.json'])
def test_owner_and_resource_stop_before_loading(tmp_path,stop):
    path=tmp_path/stop;path.parent.mkdir(exist_ok=True);atomic(path,{})
    with pytest.raises(RuntimeError):card.execute(tmp_path/'output',{},card.CONFIG)
