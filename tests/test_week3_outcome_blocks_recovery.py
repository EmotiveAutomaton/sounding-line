"""Canonical whole-document identity survives equivalent Quill delta encodings."""
import copy
import json
from pathlib import Path

import pytest

from runners.drive.cards import week3_outcome_blocks_inputs as old
from runners.drive.cards import week3_outcome_blocks_recovery as card
from runners.drive.cards.timing_census import read
from runners.stage9.coauthor import units
from tests.test_week3_outcome_blocks_inputs import session,fixture


def equivalent(encoding):
    f=session(span='\n\nA \U0001f642 useful sentence.')
    prefix='Earlier \U0001f642 retained text.\n'
    f['events'][0]['currentDoc']=prefix
    text=f['canonical']['events'][0]['options'][1]['original']
    if encoding=='ordinary':ops=[{'retain':len(units(prefix))-1},{'insert':text}]
    elif encoding=='shifted':ops=[{'retain':len(units(prefix))},{'insert':text[1:]+'\n'}]
    else:ops=[{'delete':len(units(prefix))},{'insert':prefix[:-1]+text+'\n'}]
    f['events'][3]['textDelta']={'ops':ops}
    f['events'][4]['textDelta']={'ops':[{'retain':len(units(prefix))-1},{'delete':len(units(text))}]}
    f['events'][5]['textDelta']['ops'][0]={'retain':len(units(prefix))-1}
    f['timeline']['final_document']=prefix[:-1]+f['timeline']['final_document']
    f['canonical']['final_document']=f['timeline']['final_document']
    return f


def test_original_valid_fixtures_unchanged_exactly():
    for f in fixture():
        assert card.spans(f['events'],f['timeline'],f['canonical'])==old.spans(f['events'],f['timeline'],f['canonical'])


def test_equivalent_quill_encodings_have_identical_accepted_atoms():
    results=[]
    for encoding in ('ordinary','shifted','replacement'):
        f=equivalent(encoding)
        results.append(card.spans(f['events'],f['timeline'],f['canonical']))
    assert results[0]==results[1]==results[2]
    span=results[0][0]
    assert span['original_codepoints']==len('\n\nA \U0001f642 useful sentence.')
    assert span['deleted_codepoints']==span['original_codepoints'] and span['retained_codepoints']==0
    assert span['failure_ordinal']==4


def test_old_extractor_reproduces_actual_newline_failure_class():
    f=equivalent('shifted')
    with pytest.raises(ValueError,match='actual inserted span'):old.spans(f['events'],f['timeline'],f['canonical'])


def test_full_replacement_preserves_earlier_accepted_provenance():
    first='abcde';second='next \U0001f642 offer'
    events=[dict(eventName='system-initialize',eventTimestamp=0,currentDoc='\n',eventSource='system')]
    def add(name,ops=None,who='api'):
        e=dict(eventName=name,eventTimestamp=len(events)*1000,eventSource=who)
        if ops is not None:e['textDelta']={'ops':ops}
        events.append(e)
    add('suggestion-open');add('suggestion-select');add('text-insert',[{'insert':first}])
    add('suggestion-open');add('suggestion-select')
    add('text-insert',[{'delete':6},{'insert':first+second+'\n'}])
    add('text-delete',[{'delete':4}],who='user')
    final='e'+second+'\n'
    canonical=dict(final_document=final,events=[dict(ordinal=i,usable=True,decision='edit',
        verified_insertion=True,matched_option_indices=[0],options=[dict(index=0,original=t),dict(index=1,original='other')]) for i,t in [(1,first),(4,second)]])
    spans=card.spans(events,dict(final_document=final),canonical)
    assert spans[0]['deleted_codepoints']==4 and spans[0]['failure_ordinal']==7 and spans[0]['retained_codepoints']==1
    assert spans[1]['deleted_codepoints']==0 and spans[1]['failure_ordinal'] is None and spans[1]['retained_codepoints']==len(second)


@pytest.mark.parametrize('defect',['choice','prefix','ambiguous','unverified','final'])
def test_recovery_preserves_strict_identity_guards(defect):
    f=equivalent('shifted');c=f['canonical']['events'][0]
    if defect=='choice':c['options'][1]['original']+='!'
    if defect=='prefix':f['events'][3]['textDelta']['ops']=[{'delete':1},{'retain':len(units(f['events'][0]['currentDoc']))-1},{'insert':c['options'][1]['original'][1:]+'\n'}]
    if defect=='ambiguous':c['matched_option_indices']=[17,99]
    if defect=='unverified':c['verified_insertion']=False
    if defect=='final':f['timeline']['final_document']+='!'
    with pytest.raises(ValueError):card.spans(f['events'],f['timeline'],f['canonical'])


def test_complete_recovery_source_and_fresh_replay(tmp_path):
    f=fixture();f[0]=equivalent('shifted');f[0]['meta']=dict(f[0]['meta'],session='s0',writer='w0')
    path=tmp_path/'fixture.json';path.write_text(json.dumps(f),encoding='utf8')
    inputs=dict(fixture=str(path));out=tmp_path/'out'
    assert card.execute(out,inputs,card.CONSTRUCTED)['status']=='complete'
    assert card.verify(out,inputs,card.CONSTRUCTED)['verified']
    path.write_text(path.read_text()+' ',encoding='utf8')
    with pytest.raises(ValueError,match='changed'):card.verify(out,inputs,card.CONSTRUCTED)


def test_retained_actual_failure_session_replays_without_exclusion():
    path=Path('.agent-state/drive-20261025/WC2_ACTUAL_FAILURE_FIXTURE.json')
    if not path.exists():pytest.skip('private actual-source regression fixture not distributed')
    f=read(path)
    with pytest.raises(ValueError,match='actual inserted span'):old.spans(f['events'],f['timeline'],f['canonical'])
    actual=card.spans(f['events'],f['timeline'],f['canonical'])
    assert len(actual)==sum(e['eventName']=='suggestion-select' for e in f['events'])
    found=next(r for r in actual if r['origin']==192)
    selected=next(e for e in f['canonical']['events'] if e['ordinal']==192)
    text=next(o['original'] for o in selected['options'] if o['index']==3)
    assert found['text']==card.normalized(text) and found['canonical']
