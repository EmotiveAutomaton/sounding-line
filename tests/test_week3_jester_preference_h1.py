from pathlib import Path
import json
import numpy as np
import pytest
from threadpoolctl import threadpool_limits
from tests.test_week3_jester_preference import fixture as original_fixture,text_fixture
from runners.drive.cards import week3_jester_preference as original
from runners.drive.cards import week3_jester_topics_h1 as topics
from runners.drive.cards import week3_jester_comparison_h1 as runner

@pytest.fixture(autouse=True)
def threads():
    with threadpool_limits(limits=2):yield

def fixture(root):
    inp=original_fixture(root)
    p=Path(inp['topics_plan']);plan=json.loads(p.read_text())
    plan['module']='runners.drive.cards.week3_jester_topics_h1'
    p.write_text(json.dumps(plan),encoding='utf8')
    t=Path(inp['topics']);t.write_text(json.dumps(topics.build(plan['inputs'],plan['config'])),encoding='utf8')
    c=Path(inp['topics_complete']);obj=json.loads(c.read_text());obj['outputs']['output/TOPICS.json']=original.filehash(t)
    c.write_text(json.dumps(obj),encoding='utf8')
    return inp

def test_represented_features_exactly_unchanged():
    before=original.text_features(text_fixture());after=topics.text_features(text_fixture())
    assert all(after[k]==v for k,v in before.items())
    assert after['empty_vocabulary_items']==[]

def test_zero_support_uniform_without_dropping_item(tmp_path):
    rows=text_fixture();rows[76]['text']='quizzaciously uniquelexeme zyxw'
    r=topics.text_features(rows)
    assert 77 in r['empty_vocabulary_items'] and 77 in r['zero_component_items']
    assert r['weights'][76]==[.125]*8 and len(r['weights'])==150
    text=tmp_path/'text.json';text.write_text(json.dumps(rows),encoding='utf8')
    inp={'jester_texts':str(text)};cfg={'source_sha256':original.filehash(text)}
    topics.execute(tmp_path/'out',inp,cfg)
    assert topics.verify(tmp_path/'out',inp,cfg)['verified']
    before=(tmp_path/'out/TOPICS.json').read_bytes();topics.execute(tmp_path/'out',inp,cfg)
    assert (tmp_path/'out/TOPICS.json').read_bytes()==before
    text.write_text('[]',encoding='utf8')
    with pytest.raises(ValueError,match='changed'):topics.build(inp,cfg)

def test_full_consumer_and_original_parent_refusal(tmp_path):
    inp=fixture(tmp_path/'fixture');y,w,s,b=runner.load(inp,{'mode':'constructed'})
    assert y.shape==(160,150) and runner.mask_calibration(np.isfinite(y),w)['exact_additive_zero']
    p=Path(inp['topics_plan']);plan=json.loads(p.read_text());plan['module']='runners.drive.cards.week3_jester_topics'
    p.write_text(json.dumps(plan),encoding='utf8')
    with pytest.raises(ValueError,match='unadmitted'):runner.load(inp,{'mode':'constructed'})
