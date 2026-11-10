from copy import deepcopy
import numpy as np
import pytest
from runners.drive.cards import week5_bk_s2_source as source,week5_bk_s2_analysis as analysis
from runners.drive.cards.week5_bk_s2_fixture import fixture_data,model_world
from runners.drive.cards.timing_text import replay_words
from runners.drive.cards.week4_revision_source_h1 import extract

def projection(fixture):return source.project(fixture['events'],fixture['p6'],fixture['intervals'],fixture['revision'])

def test_typed_mixed_future_and_deleted_denominator():
    rows,counts,_=projection(fixture_data())
    assert len(rows)==4 and counts['first_complete_typed_sentences']==4
    assert [len(r['later_revisions']) for r in rows]==[1,1,0,0]
    assert rows[0]['intervening_nonuser_edit'] and not rows[0]['later_revisions'][0]['current_target_fully_typed']
    assert rows[1]['later_revisions'][0]['current_target_fully_typed']
    assert 0<=rows[0]['start_seconds']<1

def test_ai_only_changes_not_user_outcome():
    f=fixture_data()
    for e in f['events']:
        if any(op.get('insert')=='very ' for op in source.delta_ops(e.get('textDelta'))):e['eventSource']='api'
    f['p6']=replay_words(f['events']);f['revision']=extract(f['events'])
    for w in f['p6']['words']:w['population_log_frequency']=-2
    rows,_,_=projection(f)
    assert rows[0]['intervening_nonuser_edit'] and rows[0]['later_revisions']==[]

@pytest.mark.parametrize('order',['delete-first','insert-first'])
def test_whole_replacement_inherits_lineage_in_either_delta_order(order):
    rows,_,_=projection(fixture_data(order))
    assert len(rows)==4 and rows[0]['intervening_nonuser_edit']
    assert len(rows[0]['later_revisions'])==1
    assert not rows[0]['later_revisions'][0]['current_target_fully_typed']

def test_first_onset_excluded_break_and_internal_absence():
    f=fixture_data();first=next(w['ordinal'] for w in f['p6']['words'] if w['is_word'])
    f['intervals']=[r for r in f['intervals'] if r['ordinal']!=first]
    assert projection(f)[0][0]['timing_state']=='eligible'
    second=[w['ordinal'] for w in f['p6']['words'] if w['is_word']][1]
    g=deepcopy(f)
    for r in g['intervals']:
        if r['ordinal']==second:r['interval_seconds']=61
    assert projection(g)[0][0]['timing_state']=='break'
    f['intervals']=[r for r in f['intervals'] if r['ordinal']!=second]
    assert projection(f)[0][0]['timing_state']=='missing_onset_timing'

def test_changed_source_and_clock_refuse():
    f=fixture_data();f['revision']['final_document_sha256']='bad'
    with pytest.raises(ValueError,match='final document'):projection(f)
    f=fixture_data();f['events'][3]['eventTimestamp']=0
    with pytest.raises(ValueError,match='chronology'):projection(f)

def test_paragraph_threshold_from_original_delta_anchor():
    f=fixture_data();previous=''
    for e in f['events']:
        ops=source.delta_ops(e.get('textDelta'))
        for op in ops:
            if op.get('insert')==' ' and previous=='.':op['insert']='\n';break
            if 'insert' in op:previous=op['insert']
        else:continue
        break
    f['p6']=replay_words(f['events']);f['revision']=extract(f['events'])
    for w in f['p6']['words']:w['population_log_frequency']=-2
    rows,_,_=projection(f);assert rows[0]['later_revisions'][0]['paragraph_nonlocal']

def test_known_sign_null_and_exact_bootstrap_coefficients():
    for sign in (-1,0,1):
        rows,counts=analysis.select(model_world(sign));bundle=analysis.arrays(rows)
        assert counts['distinct_nonlocal_events']>=300
        assert abs(analysis.coefficient(bundle)-.6*sign)<1e-10
        assert abs(analysis.coefficient(bundle,[0]*30)-.6*sign)<1e-10
        fit=analysis.random_intercept_fit(bundle)
        assert abs(fit['effect']-.6*sign)<1e-10

def test_declared_texture_and_followup_censoring():
    data=model_world();rows,counts=analysis.select(data,'within_two_minutes');assert counts['distinct_nonlocal_events']==0
    assert analysis.select(data,'later_than_two_minutes')[1]['distinct_nonlocal_events']>=300
    for s in data:
        for r in s['sentences']:r['remaining_seconds']=90
    assert analysis.select(data,'within_two_minutes')[1]['rows']==0

def test_missing_control_and_unidentified_flow_refused():
    data=model_world();del data[0]['sentences'][0]['controls']['mean_word_length']
    with pytest.raises(ValueError,match='controls'):analysis.select(data)
    rows,_=analysis.select(model_world());bundle=analysis.arrays(rows)
    for item in bundle['stats']:item['xx'][:]=0
    with pytest.raises(ValueError,match='unidentified'):analysis.coefficient(bundle)

def test_label_reference_and_complete_native_analysis():
    result=analysis.analyse(model_world(1),draws=200,permutations=200)
    assert result['support_gate'] and result['interval'][0]>.5
    assert abs(result['reference']['mean'])<.03
    assert len(result['private_bootstrap'])==200 and len(result['private_reference'])==200
