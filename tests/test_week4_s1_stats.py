import pytest
from runners.drive.cards import week4_s1_stats as s

def test_all_known_signs_nuisance_and_unidentifiable_cases():
    assert all(s.known_checks().values())

def test_history_sentence_and_source_boundaries():
    d={'a','the'}
    seq=[['a','b','c','.','the','d','e','f'],['g','h','a']]
    assert s.history_grams(seq,d)=={('the','<content>','<content>','<content>')}
    assert s.history_grams([['b','c','d','e']],d)==set()

def test_repeated_target_grams_keep_occurrence_weights():
    a=('a','b','c','d');b=('e','f','g','h')
    assert s.recurrence([a,a,b],{a},{b})==pytest.approx(1/3)
    assert s.recurrence([a],{a},{a})==0

def test_support_refusal_precedes_scoring():
    rows=s.fixture('positive');summary,_=s.analyze([r for r in rows if r['writer']!='24'])
    assert summary['state']=='design cannot test' and not summary['scientific_effect_computed']

def test_complete_native_interface_and_mutation_refusal(tmp_path):
    from runners.drive.cards import week4_s1_recurrence as r
    c=r.configuration('constructed');r.execute(tmp_path,{},c)
    assert r.verify(tmp_path,{},c)['complete_statistical_replay']
    (tmp_path/'SUMMARY.json').write_text('{}')
    with pytest.raises(ValueError,match='replay'):r.verify(tmp_path,{},c)
