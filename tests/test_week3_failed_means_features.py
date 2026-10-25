"""Full feature coverage, precise pilot separation and fresh replay."""
import json
from pathlib import Path

import pytest

from runners.drive.cards import week3_failed_means_features as card
from runners.drive.cards import week3_failed_means as stats
from tests.test_week3_failed_means import payload


def test_only_selected_deleted_and_their_matched_kept_references_are_encoded():
    p=payload();extra=dict(p['data']['events'][0],id='unused',kind='kept')
    p['data']['events'].append(extra)
    selected,texts=stats.required(p['data']['events'])
    assert len(selected)==32 and all(e['id']!='unused' for e in selected)
    assert texts==sorted(set(texts))


def test_constructed_feature_handler_second_entry_full_replay_and_tamper(tmp_path):
    f=tmp_path/'input.json';f.write_text(json.dumps(payload()['data']),encoding='utf8')
    inputs={'fixture':str(f)};out=tmp_path/'out'
    assert card.execute(out,inputs,card.CONSTRUCTED)['status']=='complete'
    assert card.execute(out,inputs,card.CONSTRUCTED)['status']=='complete'
    assert card.verify(out,inputs,card.CONSTRUCTED)['verified']
    summary=card.read(out/'SUMMARY.json')
    assert summary['encoded']==summary['required_unique_texts'] and not summary['analysis_ready']
    scopes=card.gzread(out/'SCOPES.json.gz')
    assert len(scopes)==summary['encoded'] and all(r['constructed_only'] for r in scopes.values())
    f.write_text(f.read_text()+' ',encoding='utf8')
    with pytest.raises(ValueError,match='encoding differs'):card.verify(out,inputs,card.CONSTRUCTED)


def test_pilot_or_constructed_completion_cannot_be_admitted_as_corpus_stats(tmp_path):
    out=tmp_path/'output';out.mkdir()
    for name,value in [('EVENTS.json.gz',dict(events=[])),('VECTORS.json.gz',{})]:card.gzip_equal(out/name,value)
    card.write_equal(out/'SUMMARY.json',dict(analysis_ready=False))
    complete=tmp_path/'COMPLETE.json'
    card.write_equal(complete,dict(status='COMPLETE',fresh_process_verified=True,
        outputs={p.relative_to(tmp_path).as_posix():card.filehash(p) for p in out.iterdir()}))
    with pytest.raises(ValueError,match='partial/constructed'):stats.load({'feature_completion':str(complete)},stats.CONFIG)


def test_invalid_vector_is_rejected_before_inference():
    p=payload();first=p['data']['events'][0]
    p['vectors'][first['window']['text']]=[0,0,0]
    with pytest.raises(ValueError,match='nonfinite/nonunit'):stats.analyze(p['data'],p['vectors'],stats.CONSTRUCTED)
