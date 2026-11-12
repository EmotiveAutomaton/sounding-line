from copy import deepcopy
import hashlib
import json
import pytest

from runners.drive.cards import week5_ex1 as ex
from runners.drive.cards import week5_ex1_fixture as fixture


def test_unicode_known_answers():
    assert fixture.check_normalization()['complete_cases']==4
    actual,ancestry=ex.normalize_with_origins('e\u0301\U0001f642\r\n')
    assert actual=='\u00e9\U0001f642' and ancestry==[frozenset((0,1)),frozenset((2,))]


def test_all_sources_and_mixed_are_preserved():
    assert fixture.check_projection()['mixed_preserved']


def test_constructed_handler_full_reentry_and_verify(tmp_path):
    fixture.execute(tmp_path,{},{});assert fixture.verify(tmp_path,{},{})['verified']
    bundle=tmp_path/'consumer/bundle'
    content=''.join(p.read_text(encoding='utf8') for p in (bundle/'sessions').glob('*.json'))
    assert 'alpha' not in content and 'beta' not in content and 'cafe' not in content
    values=[ex.read(p) for p in (bundle/'sessions').glob('*.json')]
    for writer in {v['hashed_writer_id'] for v in values}:
        assert len({v['writer_fold'] for v in values if v['hashed_writer_id']==writer})==1


def test_changed_parent_refuses(tmp_path):
    inputs=fixture.prepare(tmp_path/'source');target=tmp_path/'out'
    ex.execute(target,inputs,{'max_new_documents':1})
    p=tmp_path/'source/timing/output/PRIVATE_ROSTER.json';p.write_text('[]',encoding='utf8')
    with pytest.raises(ValueError):ex.execute(target,inputs,{})


def test_changed_checkpoint_refuses(tmp_path):
    inputs=fixture.prepare(tmp_path/'source');target=tmp_path/'out'
    ex.execute(target,inputs,{'max_new_documents':1})
    state=ex.read(target/'CHECKPOINT.json');state['files']={};ex.io.write_json(target/'CHECKPOINT.json',state)
    with pytest.raises(ValueError,match='contiguous'):ex.execute(target,inputs,{})


def test_changed_output_refuses(tmp_path):
    inputs=fixture.prepare(tmp_path/'source');target=tmp_path/'out'
    ex.execute(target,inputs,{'max_new_documents':1})
    p=target/'bundle/sessions/session-0000.json';value=ex.read(p);value['words'][0]['start']+=1
    ex.io.write_json(p,value)
    with pytest.raises(ValueError,match='changed'):ex.execute(target,inputs,{})


def test_repeated_spelling_does_not_borrow_pause():
    events=fixture.typed_events('one one')
    events.insert(1,fixture.event(1,'text-change',source='user',delta={'ops':[{'retain':1}]}))
    for n,event in enumerate(events):
        event['eventNum']=n;event['eventTimestamp']=1000*(n+1)
    words=fixture.replay_words(events)['words']
    writer=hashlib.sha256(b'writer').hexdigest();posts=fixture.posterior(words)
    # Keep only the first occurrence's timing. The second has no timing label.
    posts=posts[:1]
    value=ex.session_projection('constructed',writer,1,events,words,posts)
    typed=[r for r in value['words'] if r['source']=='typed']
    assert len(typed)==2 and typed[-1]['stop'] is None


def test_stop_threshold_is_strict_and_interval_identity_checked():
    events=fixture.typed_events('first second');words=fixture.replay_words(events)['words']
    posts=fixture.posterior(words);posts[-1]['fast']=.5
    writer=hashlib.sha256(b'w').hexdigest()
    value=ex.session_projection('constructed',writer,0,events,words,posts)
    assert value['words'][-1]['stop'] is False
    posts[-1]['interval_seconds']+=1
    with pytest.raises(ValueError,match='differs'):ex.session_projection('constructed',writer,0,events,words,posts)


def test_nfc_composition_preserves_mixed_codepoint_ancestry():
    events=[fixture.event(0,'system-initialize',currentDoc='e\n'),
        fixture.event(1,'text-insert',source='user',delta={'ops':[{'retain':1},{'insert':'\u0301'}]})]
    words=fixture.replay_words(events)['words']
    value=ex.session_projection('constructed',hashlib.sha256(b'w').hexdigest(),0,events,words,[])
    assert value['normalized_text_sha256']==hashlib.sha256('\u00e9'.encode()).hexdigest()
    assert value['words'][0]['source'] is None and value['words'][0]['mixed_provenance']
    assert value['words'][0]['source_codepoint_counts']=={'prompt':1,'typed':1}
    assert (value['words'][0]['start'],value['words'][0]['end'])==(0,1)


def test_unknown_api_is_unresolved_not_suggestion():
    events=fixture.typed_events('test')
    events[-1]['eventSource']='api'
    # Replace a whole token's first typed character with an unselected API edit.
    for row in events[1:]:row['eventSource']='api'
    value=ex.session_projection('constructed',hashlib.sha256(b'w').hexdigest(),0,events,[],[])
    assert value['words'][-1]['source'] is None and value['words'][-1]['unresolved_provenance']


def test_export_schema_rejects_extra_text():
    events=fixture.typed_events();words=fixture.replay_words(events)['words']
    value=ex.session_projection('constructed',hashlib.sha256(b'w').hexdigest(),0,events,words,[])
    value['words'][0]['text']='private'
    with pytest.raises(ValueError,match='field'):ex.validate_projection(value)


def test_invalid_unicode_refuses():
    with pytest.raises(UnicodeError):ex.normalize_with_origins('\ud800')


@pytest.mark.parametrize('config',[{'max_new_documents':0},{'max_wall_seconds':0},{'sample':5}])
def test_invalid_configuration_refuses(tmp_path,config):
    with pytest.raises(ValueError):ex.execute(tmp_path,{},config)


def test_outside_repo_copy_refuses(tmp_path):
    with pytest.raises(ValueError,match='named local'):ex.export_local(tmp_path,tmp_path/'outside')
