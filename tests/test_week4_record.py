"""Known-answer source tests; no scientific effect is inferred."""
import copy
import pytest
from runners.drive.cards import week4_record as r

def test_all_three_historical_failures_before_successor():
    rows=r.historical_checks()
    assert len(rows)==3 and all(x['new_passed'] for x in rows)

def test_known_unicode_and_original_survival():
    events,timeline=r.old_fixture('edited')
    value=r.census(events,r.replay(events))
    assert value['exact']
    assert value['accepted_original_codepoints']==3
    assert value['accepted_surviving_codepoints']==2
    assert value['character_counts']==dict(typed=1,accepted=0,accepted_edited=2,prompt=2,api_unknown=0)
    assert sum(value['character_counts'].values())==len(timeline['final_document'])

def test_bad_source_is_explicit_exclusion_not_patched():
    events,_=r.old_fixture('plain');canonical=r.replay(events)
    canonical['final_document']+='bad'
    result=r.census(events,canonical)
    assert not result['exact'] and 'mismatch' in result['reason']
    canonical['errors']=['known failed reconstruction']
    result=r.census(events,canonical)
    assert not result['exact'] and result['errors']

def test_missing_comparator_retained_not_zeroed():
    events,timeline=r.old_fixture('plain')
    value=r.spans(events,timeline,r.replay(events))[0]
    assert value['canonical'] and not value['comparator_supported']
    assert value['unchosen']==[] and value['comparator_support']=='single_option_menu'

@pytest.mark.parametrize('card',['R1','R2'])
def test_complete_serialization_replay_and_corruption(tmp_path,card):
    config=dict(card=card,mode='constructed',expected_sessions=7)
    r.execute(tmp_path,{},config)
    assert r.verify(tmp_path,{},config)['verified']
    p=tmp_path/'SUMMARY.json';text=p.read_text();p.write_text(text.replace('"sessions":7','"sessions":6').replace('"sessions": 7','"sessions": 6'))
    assert p.read_text()!=text
    with pytest.raises(ValueError,match='aggregation'):r.verify(tmp_path,{},config)

def test_population_cannot_be_silently_shortened(tmp_path):
    with pytest.raises(ValueError,match='population'):r.execute(tmp_path,{},dict(card='R1',mode='full',expected_sessions=12))
