from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from collections import Counter
import json
import pytest
from runners.stage14.common import read, freeze, filehash
from runners.stage9.coauthor import units, replay
from runners.drive.cards import week3_d5_inputs_h1 as card
from runners.drive.cards.week3_insertion_provenance_h1 import fixture as raw_fixture
from runners.drive.cards.timing_p6 import gzip_equal, training_sequences
from runners.drive.cards.timing_text import tokens


def records(parts):
    spans=[]; cursor=0
    for i,(origin,text) in enumerate(parts):
        spans.append(dict(start_utf16=cursor, end_utf16=cursor+len(units(text)), origin=origin, insertion_ordinal=i, text=text))
        cursor+=len(units(text))
    timeline=dict(session='s',writer='w',prompt='p',final_document=''.join(t for _,t in parts),final_spans=spans)
    p6=dict(session='s',writer='w',prompt='p',timestamp=0,end_at=10,
        words=[dict(token='deleted',is_word=True)], training_sequences=training_sequences(timeline))
    process=dict(session='s',writer='w',prompt='p',timestamp=0,typed_words=1,word_counts={'deleted':1},source_hashes={})
    meta=dict(session='s',writer='w',prompt='p',timestamp=0,end_at=10)
    return timeline,p6,process,meta


def known():
    args=records([('prompt','P'),('typed','ab'),('typed','c'),('accepted_edited','\U0001f600'),('typed','xy')])
    value=card.text_views(*args)
    assert [g['text'] for g in value['final_typed_groups']]==['abc','xy']
    assert value['utf16_by_origin']['accepted_edited']==2
    assert value['codepoints_by_origin']['accepted_edited']==1
    assert value['model_share']==1/6 and value['final_typed_codepoints']==5
    assert value['production_tokens'][0]['token']=='deleted'
    assert value['final_typed_token_sequences']==[['abc'],['xy']]


def test_known_origins_boundaries_and_production(): known()


def test_unknown_and_empty_remain_explicit():
    v=card.text_views(*records([('prompt','p'),('api_unknown','?'),('accepted','ok')]))
    assert v['model_share'] is None and v['known_accepted_fraction']==2/3
    assert v['model_share_missing_reason']=='unknown_api_origin' and not v['final_typed_groups']
    v=card.text_views(*records([('prompt','p')]))
    assert v['model_share'] is None and v['model_share_missing_reason']=='empty_nonprompt_text'


@pytest.mark.parametrize('fault',['offset','join','chronology','tokens','origin','process'])
def test_source_defects_refuse(fault):
    args=list(records([('typed','abc')]))
    if fault=='offset':args[0]['final_spans'][0]['end_utf16']=4
    elif fault=='join':args[1]['writer']='other'
    elif fault=='chronology':args[3]['end_at']=-1
    elif fault=='tokens':args[1]['training_sequences']=[['wrong']]
    elif fault=='origin':args[0]['final_spans'][0]['origin']='guessed'
    else:args[2]['typed_words']=2
    with pytest.raises(ValueError):card.text_views(*args)


def source_fixture(directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    events,timeline=raw_fixture('edited')
    raw=directory/'raw.jsonl'
    if not raw.exists():raw.write_text(''.join(json.dumps(e)+'\n' for e in events),encoding='utf8')
    identity=dict(session='s',writer='w',prompt='p')
    timeline.update(identity,source_sha256=filehash(raw))
    meta=dict(identity,timestamp=0,end_at=10000,rows=fixture_rows(events))
    p6=dict(identity,timestamp=0,end_at=10000,words=[dict(token='x',is_word=True)],training_sequences=training_sequences(timeline))
    process=dict(identity,timestamp=0,typed_words=1,word_counts={'x':1},source_hashes={'raw':filehash(raw)})
    freeze(directory/'timeline.json',timeline);freeze(directory/'p6.json',p6);gzip_equal(directory/'process.json.gz',process)
    source=SimpleNamespace(inputs=dict(session_index=str(directory/'index.json'),p6_index=str(directory/'index.json')),
        p2={'s':dict(file='timeline.json',sha256=filehash(directory/'timeline.json'))},
        p6={'s':dict(file='p6.json',sha256=filehash(directory/'p6.json'))},
        root=directory,roster={'s':dict(path='raw.jsonl')},meta={'s':meta},session=lambda sid:deepcopy(process))
    return source,{'s':(directory/'process.json.gz',process)}


def native(output,inputs,config,verification=False):
    if config!=card.CONFIG:raise ValueError('Fixture configuration differs')
    output=Path(output);sources=source_fixture(output/'constructed-source')
    with patch.object(card,'load',return_value=sources):
        if verification:return dict(card.verify(output/'constructed-output',inputs,config),constructed=True)
        known();card.execute(output/'constructed-output',inputs,config)
        return dict(card.execute(output/'constructed-output',inputs,config),constructed=True)


def execute(output,inputs,config):return native(output,inputs,config)
def verify(output,inputs,config):return native(output,inputs,config,True)


def test_whole_timeline_replay_refuses_changed_origin():
    events,timeline=raw_fixture('edited');timeline.update(session='s',writer='w',prompt='p',source_sha256='fake')
    meta=dict(rows=fixture_rows(events))
    card.replay_timeline(events,meta,timeline)
    timeline['final_spans'][0]['origin']='typed'
    with pytest.raises(ValueError,match='Whole raw timeline'):card.replay_timeline(events,meta,timeline)


def fixture_rows(events):
    return [dict(key=str(r['ordinal']),ordinal=r['ordinal'],end_ordinal=len(events),handling=r['decision'],menu=r['options'])
            for r in replay(events)['events'] if r['usable']]


def test_complete_handler_reentry_fresh_replay_and_tamper(tmp_path):
    execute(tmp_path,{},card.CONFIG);assert verify(tmp_path,{},card.CONFIG)['full_fresh_source_replay']
    p=tmp_path/'constructed-output/SUMMARY.json';v=read(p);v['sessions']=99;p.write_text(json.dumps(v),encoding='utf8')
    with pytest.raises(ValueError,match='Complete D5 source'):verify(tmp_path,{},card.CONFIG)


def test_resource_yield_and_configuration_refusal(tmp_path):
    freeze(tmp_path/'constructed-output/YIELD_REQUEST.json',dict(stop=True))
    assert execute(tmp_path,{},card.CONFIG)['status']=='yielded'
    assert not (tmp_path/'constructed-output/SUMMARY.json').exists()
    with pytest.raises(ValueError,match='configuration'):card.execute(tmp_path,{},dict(card.CONFIG,schema=2))


def test_changed_plan_refuses_actual_schema(tmp_path):
    freeze(tmp_path/'PLAN.json',dict(inputs={}))
    freeze(tmp_path/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,outputs={'PLAN.json':'0'*64}))
    with pytest.raises(ValueError,match='Process plan changed'):card.load(dict(pmap_complete=str(tmp_path/'COMPLETE.json')))


def test_actual_producer_and_complete_session_integration():
    from runners.stage14.common import REPO
    path=REPO/'results/phase_2_4_stage_15/raw/drive-wave-20261017-w1/PMAP-recovery/COMPLETE.json'
    source,saved=card.load(dict(pmap_complete=str(path)))
    sid=sorted(saved)[0];_,old=saved[sid];fresh=source.session(sid)
    assert fresh==old
    timeline=card.bound_record(source.inputs['session_index'],source.p2[sid])
    p6=card.bound_record(source.inputs['p6_index'],source.p6[sid])
    raw=source.root/source.roster[sid]['path']
    events=[json.loads(line) for line in raw.read_text(encoding='utf8').splitlines()]
    card.replay_timeline(events,source.meta[sid],timeline)
    row=card.text_views(timeline,p6,fresh,source.meta[sid])
    assert row['source_only'] and not row['scientific_admission']


def test_every_retained_session_payload_parity():
    from runners.stage14.common import REPO
    source,saved=card.load(dict(pmap_complete=str(REPO/'results/phase_2_4_stage_15/raw/drive-wave-20261017-w1/PMAP-recovery/COMPLETE.json')))
    paths=sorted((REPO/'results/phase_2_4_stage_15/raw/drive-week3-20261025/D5-inputs-v2/output/sessions').glob('*.json.gz'))
    assert len(paths)>=140
    for path in paths:
        old=card.gzread(path);sid=old['session'];_,process=saved[sid]
        timeline=card.bound_record(source.inputs['session_index'],source.p2[sid])
        p6=card.bound_record(source.inputs['p6_index'],source.p6[sid])
        assert card.text_views(timeline,p6,process,source.meta[sid])==old
