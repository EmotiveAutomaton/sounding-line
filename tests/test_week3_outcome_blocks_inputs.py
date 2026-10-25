"""Canonical provenance, future-window boundaries and external-writer contexts."""
import copy
import json

import pytest

from runners.drive.cards import week3_outcome_blocks_inputs as card
from runners.drive.cards.timing_text import replay_words
from runners.stage9.coauthor import units


def session(sid='s0',writer='w0',deleted=True,prompt='p0',span='old useful words. '):
    events=[dict(eventName='system-initialize',eventTimestamp=0,currentDoc='\n',eventSource='system')]
    def add(name,source='system',ops=None):
        e=dict(eventName=name,eventTimestamp=len(events)*1000,eventSource=source)
        if ops is not None:e['textDelta']={'ops':ops}
        events.append(e)
    add('suggestion-open');add('suggestion-select')
    add('text-insert',ops=[{'insert':span}])
    if deleted:add('text-delete','user',[{'delete':len(units(span))}])
    text=' '.join(['word'+str(i) for i in range(62)])+'. '
    add('text-insert','user',[{'retain':0 if deleted else len(units(span))},{'insert':text}])
    final=('' if deleted else span)+text+'\n'
    canonical=dict(final_document=final,events=[dict(ordinal=1,usable=True,decision='accept',
        verified_insertion=True,matched_option_indices=[17],selected_index=99,
        options=[dict(index=99,original='different option'),dict(index=17,original=span)])])
    return dict(meta=dict(session=sid,writer=writer,prompt=prompt,timestamp=1),events=events,
                timeline=dict(final_document=final),canonical=canonical,p6=replay_words(events))


def fixture():
    return [session('s'+str(i),'w'+str(i//2),i%2==0) for i in range(6)]


def test_canonical_inserted_identity_ignores_logged_wrong_index_and_utf16():
    f=session(span='a\U0001f642bc')
    s=card.spans(f['events'],f['timeline'],f['canonical'])[0]
    assert s['canonical'] and s['text']=='a\U0001f642bc'
    assert s['original_codepoints']==4 and s['deleted_codepoints']==4
    assert s['failure_ordinal']==4 and s['retained_codepoints']==0
    assert s['unchosen']==['different option']


def test_eighty_percent_equality_and_crossing_count_once():
    f=session(span='abcde')
    f['events'][4]['textDelta']={'ops':[{'delete':4}]}
    f['events'][5]['textDelta']['ops'][0]={'retain':1}
    f['timeline']['final_document']='e'+f['timeline']['final_document']
    f['canonical']['final_document']=f['timeline']['final_document']
    s=card.spans(f['events'],f['timeline'],f['canonical'])
    assert len(s)==1 and s[0]['failure_ordinal']==4 and s[0]['deleted_codepoints']==4


def test_incorrect_actual_option_or_final_replay_refuses():
    f=session();f['canonical']['events'][0]['options'][1]['original']='wrong'
    with pytest.raises(ValueError,match='actual inserted'):card.spans(f['events'],f['timeline'],f['canonical'])
    f=session();f['timeline']['final_document']+='x'
    with pytest.raises(ValueError,match='final document'):card.spans(f['events'],f['timeline'],f['canonical'])


def test_sentence_start_and_complete_fifty_word_window_excludes_pre_event_words():
    words=[dict(index=i,ordinal=i,completed_ordinal=i+1,token=str(i),is_word=True,sentence_start=i in (0,12,22)) for i in range(80)]
    assert card.after(words,10)['word_indices']==list(range(12,62))
    assert card.after(words,10,False)['word_indices']==list(range(11,61))
    assert card.after(words,30) is None
    assert card.after(words,40,False) is None


def test_other_writer_prompt_control_exact_nearest_and_one_per_writer():
    e=dict(writer='a',prompt='p',window=dict(position=.5),sensitivity=None)
    windows=[dict(writer=w,prompt=p,position=x,session=s,first_ordinal=0) for w,p,x,s in
             [('a','p',.5,'own'),('b','p',.25,'b0'),('b','p',.75,'b1'),('c','q',.5,'wrong'),('d','p',.8,'d0')]]
    matches=card.match_context(e,windows)
    assert [x['session'] for x in matches]==['b0','d0']
    assert all(x['writer']!='a' and x['prompt']=='p' for x in matches)


def test_full_preparation_keeps_census_matches_and_is_unsupported_not_null():
    prepared=card.assemble([card.prepare_session(**f) for f in fixture()])
    assert prepared['summary']['sessions']==6
    assert prepared['summary']['audit']['legacy_failure_candidates']==3
    assert prepared['summary']['audit']['canonical_failure_candidates']==3
    assert prepared['summary']['complete_deleted_with_context']==3
    assert prepared['summary']['complete_deleted_with_kept_reference']==3
    assert not prepared['summary']['support']
    for e in prepared['events']:
        assert len(e['context'])==2 and e['window']['words']==50


def test_complete_handler_reentry_fresh_replay_and_source_corruption(tmp_path):
    src=tmp_path/'source.json';src.write_text(json.dumps(fixture()),encoding='utf8')
    inputs={'fixture':str(src)};out=tmp_path/'out'
    assert card.execute(out,inputs,card.CONSTRUCTED)['status']=='complete'
    assert card.execute(out,inputs,card.CONSTRUCTED)['status']=='complete'
    assert card.verify(out,inputs,card.CONSTRUCTED)['verified']
    src.write_text(src.read_text()+' ',encoding='utf8')
    with pytest.raises(ValueError,match='changed'):card.verify(out,inputs,card.CONSTRUCTED)


def test_noncanonical_original_failure_preserved_in_census():
    f=session();f['canonical']['events'][0]['usable']=False
    p=card.prepare_session(**f)
    assert p['audit']['legacy_failure_candidates']==1
    assert p['audit']['noncanonical_failure_candidates']==1 and p['events']==[]
