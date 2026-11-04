import copy,json,os,subprocess,sys
from pathlib import Path
import pytest
from runners.drive.cards.week4_revision_source import extract,fixture,sentences,touches,execute,verify,configuration
from runners.stage9.coauthor import units
from runners.drive.cards.timing_p6 import gzread,gzip_equal


def test_known_nonlocal_edits_and_future_immutability():
    events=fixture();r=extract(events)
    assert r['census']['candidate_nonlocal_events']==2
    assert [e['ordinal'] for e in r['events'] if any(t['candidate_nonlocal_typed'] for t in e['targets'])]==[2,3]
    first=r['events'][0]['targets'][0]
    assert first['text']=='First \U0001f600 typed sentence. '
    assert first['typed_insertion_ordinals']==[1] and first['distance_sentences']==2
    assert first==extract(events[:3])['events'][0]['targets'][0]


def test_unicode_interior_boundary_and_multi_sentence_delete():
    text='One \U0001f600. Two complete. Last fragment';doc=units(text);s=sentences(doc,[1]*len(doc))
    assert s[0]['end_utf16']==8 and not s[-1]['complete']
    assert touches([{'retain':6},{'insert':'a'}],s).keys()=={0}
    assert not touches([{'retain':7},{'insert':'a'}],s)
    assert touches([{'retain':5},{'delete':8}],s).keys()=={0,1}
    assert touches([{'retain':len(doc)},{'insert':' end'}],s)=={}
    ops=[{'retain':5},{'delete':8}];lazy=sentences(doc,[1]*len(doc),ops)
    assert [lazy[i] for i in touches(ops,lazy)]==[s[0],s[1]]


def test_prompt_and_api_are_not_typed_and_cursor_is_not_the_anchor():
    events=fixture();events[1]['eventSource']='api'
    r=extract(events);assert r['census'].get('candidate_nonlocal_events',0)==0
    events=fixture();events[2]['currentCursor']=100000
    r=extract(events);assert r['census']['candidate_nonlocal_events']==2
    assert not r['events'][0]['recorded_cursor_valid_post_edit']
    events[2]['eventSource']='api'
    assert extract(events)['census'].get('candidate_nonlocal_events',0)==0 # Next target is now mixed.


def test_invalid_order_and_broken_surrogate_refuse():
    e=fixture();e[-1]['eventTimestamp']=-1
    with pytest.raises(ValueError,match='chronology'):extract(e)
    e=fixture();e[2]['textDelta']={'ops':[{'retain':6},{'delete':1}]}
    with pytest.raises(UnicodeError):extract(e)


def test_complete_reentry_and_corruption(tmp_path):
    cfg=configuration('constructed');execute(tmp_path,{},cfg);assert verify(tmp_path,{},cfg)['complete_source_replay']
    execute(tmp_path,{},cfg)
    p=next((tmp_path/'sessions').glob('*.gz'));v=gzread(p);v['census']['candidate_nonlocal_events']=999
    import gzip
    p.write_bytes(gzip.compress(json.dumps(v).encode()))
    with pytest.raises(ValueError,match='replay differs'):verify(tmp_path,{},cfg)


def test_fresh_process_all_output_replay(tmp_path):
    cfg=configuration('constructed');execute(tmp_path,{},cfg)
    code='from runners.drive.cards.week4_revision_source import verify,configuration; import sys; assert verify(sys.argv[1],{},configuration("constructed"))["complete_source_replay"]'
    env=dict(os.environ,PYTHONHASHSEED='271',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
    subprocess.run([sys.executable,'-X','utf8','-B','-c',code,str(tmp_path)],check=True,env=env)
