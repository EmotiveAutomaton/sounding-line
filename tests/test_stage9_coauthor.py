import pytest
from runners.stage9.coauthor import apply_delta, units, text_of, replay, project


def event(name, **kwargs):
    return {'eventName': name, **kwargs}


def options(text='XYZ'):
    return [{'index':0,'original':text,'trimmed':text}]


def base(text='ab\n', selected='XYZ'):
    return [event('system-initialize',currentDoc=text),
            event('suggestion-open',currentSuggestions=options(selected)),
            event('suggestion-select',currentSuggestionIndex=0),
            event('suggestion-close',eventSource='api'),
            event('text-insert',eventSource='api',textDelta={'ops':[{'retain':len(units(text))-1},{'insert':selected}]})]


def test_unicode_utf16_and_unrelated_shift_then_overlapping_delete():
    rows=base('a😀b\n')
    rows += [event('text-insert',eventSource='user',textDelta={'ops':[{'insert':'long'}]}),
             event('text-delete',eventSource='user',textDelta={'ops':[{'retain':7},{'delete':3}]})]
    result=replay(rows)
    assert result['reconstructed'] and result['events'][0]['decision']=='edit'
    assert result['final_document']=='longa😀Z\n'


def test_second_edit_operation_counts_but_continuation_does_not():
    rows=base()
    rows.append(event('text-insert',eventSource='user',textDelta={'ops':[{'retain':5},{'insert':'more'}]}))
    assert replay(rows)['events'][0]['decision']=='accept'
    rows.append(event('text-delete',eventSource='user',textDelta={'ops':[{'delete':1},{'retain':2},{'delete':1}]}))
    assert replay(rows)['events'][0]['decision']=='edit'


def test_dismiss_reopen_accept_is_one_opportunity():
    rows=[event('system-initialize',currentDoc='ab\n'),event('suggestion-open',currentSuggestions=options()),
          event('suggestion-close',eventSource='user'),event('suggestion-reopen',currentSuggestions=options())]
    rows += base()[2:]
    result=replay(rows)
    assert result['reconstructed'] and len(result['events'])==1
    assert result['events'][0]['decision']=='accept' and result['events'][0]['reopens']==1


def test_ignore_and_dismiss_are_explicit():
    rows=base()[:2]+[event('suggestion-open',currentSuggestions=options('ABC')),event('suggestion-close'),
        event('text-insert',eventSource='user',textDelta={'ops':[{'retain':2},{'insert':'!'}]})]
    assert [r['decision'] for r in replay(rows)['events']]==['ignore','dismiss']


def test_invalid_delta_does_not_become_literal_text_or_a_valid_session():
    for delta in ('not-json',{'ops':[{'retain':99}]},{'ops':[{'insert':{'image':'x'}}]},
                  {'ops':[{'delete':-1}]},{'ops':[{'retain':1,'delete':1}]}):
        rows=base()+[event('text-insert',eventSource='user',textDelta=delta)]
        result=replay(rows)
        assert not result['reconstructed'] and not result['events'][0]['usable']


def test_selected_text_must_match_and_missing_insertion_is_retained():
    rows=base();rows[-1]['textDelta']['ops'][-1]['insert']='different'
    result=replay(rows)
    assert result['reconstructed'] and not result['events'][0]['usable']
    assert result['final_document']=='abdifferent\n'
    result=replay(base()[:-1])
    assert result['events'][0]['exclusion']=='selected suggestion lacks a verified insertion'


def test_current_outcome_never_enters_evidence():
    row=replay(base())['events'][0]
    visible=project(row,'artifact');row['decision']='dismiss';row['selected_index']=99
    assert project(row,'artifact')==visible
    with pytest.raises(ValueError):project(row,'record',[row])


def test_surrogate_split_is_rejected():
    doc=units('a😀b')
    with pytest.raises(UnicodeError):
        apply_delta(doc,[None]*len(doc),{'ops':[{'retain':1},{'delete':1}]})


def test_editor_normalized_newlines_and_delta_alignment_are_not_text_mismatches():
    rows=base(selected='\r\nXYZ')
    # The original terminal newline remains before the inserted text and Quill's
    # delta places a new newline after it, although the full transform is exact.
    rows[-1]['textDelta']={'ops':[{'retain':3},{'insert':'XYZ\n'}]}
    result=replay(rows)
    assert result['reconstructed'] and result['events'][0]['verified_insertion']
    assert result['final_document']=='ab\nXYZ\n'


def test_logged_index_disagreement_is_retained_beside_verified_actual_suggestion():
    rows=base();rows[1]['currentSuggestions'] += [{'index':1,'original':'another','trimmed':'another'}]
    rows[2]['currentSuggestionIndex']=1
    result=replay(rows);row=result['events'][0]
    assert result['reconstructed'] and row['usable']
    assert row['matched_option_indices']==[0] and row['logged_index_agrees'] is False
