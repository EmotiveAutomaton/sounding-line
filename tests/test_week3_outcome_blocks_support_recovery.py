"""A valid singleton menu is retained; an absent comparator never becomes zero."""
import copy,json
from pathlib import Path

import pytest

from runners.drive.cards import week3_outcome_blocks_recovery as prior
from runners.drive.cards import week3_outcome_blocks_support_recovery as card
from runners.drive.cards.timing_census import read
from tests.test_week3_outcome_blocks_inputs import fixture,session
from tests.test_week3_outcome_blocks_recovery import equivalent

FIELDS={'option_count','comparator_supported','comparator_support'}


def singleton(f):
    f=copy.deepcopy(f);c=f['canonical']['events'][0]
    c['options']=[o for o in c['options'] if o['index'] in c['matched_option_indices']]
    return f


def original_fields(span):return {k:v for k,v in span.items() if k not in FIELDS}


@pytest.mark.parametrize('deleted',[True,False])
def test_single_option_retains_exact_atoms_and_survival(deleted):
    original=session(deleted=deleted,span='abc\U0001f642d')
    f=singleton(original)
    with pytest.raises(ValueError,match='no unchosen comparator'):prior.spans(f['events'],f['timeline'],f['canonical'])
    result=card.spans(f['events'],f['timeline'],f['canonical'])[0]
    expected=prior.spans(original['events'],original['timeline'],original['canonical'])[0]
    expected['unchosen']=[]
    assert original_fields(result)==expected
    assert result['canonical'] and result['option_count']==1
    assert not result['comparator_supported'] and result['comparator_support']=='single_option_menu'
    assert result['original_codepoints']==5
    assert result['retained_codepoints']==(0 if deleted else 5)


@pytest.mark.parametrize('encoding',['ordinary','shifted','replacement'])
def test_singleton_also_preserves_prior_canonical_append_repair(encoding):
    f=singleton(equivalent(encoding))
    result=card.spans(f['events'],f['timeline'],f['canonical'])[0]
    assert result['text']=='\n\nA \U0001f642 useful sentence.'
    assert result['failure_ordinal']==4 and result['deleted_codepoints']==len(result['text'])
    assert result['unchosen']==[] and not result['comparator_supported']


def test_duplicate_unchosen_options_retain_original_slot_weighting():
    f=session();c=f['canonical']['events'][0]
    c['options'].append(dict(index=18,original=c['options'][0]['original']))
    result=card.spans(f['events'],f['timeline'],f['canonical'])[0]
    assert result['unchosen']==['different option','different option']
    assert result['option_count']==3 and result['comparator_supported']
    assert original_fields(result)==prior.spans(f['events'],f['timeline'],f['canonical'])[0]


def test_ambiguous_duplicate_selected_options_still_refused():
    f=session();c=f['canonical']['events'][0]
    c['options'].append(dict(index=18,original=c['options'][1]['original']))
    c['matched_option_indices']=[17,18]
    with pytest.raises(ValueError,match='unique canonical choice'):card.spans(f['events'],f['timeline'],f['canonical'])


def test_all_valid_original_events_unchanged_except_explicit_support_metadata():
    for f in fixture():
        result=card.spans(f['events'],f['timeline'],f['canonical'])
        assert [original_fields(s) for s in result]==prior.spans(f['events'],f['timeline'],f['canonical'])
        assert all(s['comparator_supported'] for s in result)


def test_singleton_does_not_remove_primary_event_or_rematch_kept_reference():
    fs=fixture();fs[0]=singleton(fs[0]);fs[3]=singleton(fs[3])
    data=card.assemble([card.prepare_session(**f) for f in fs])
    census=data['summary'];support=census['comparator_support']
    assert len(data['events'])==6 and census['context_window_count']==6
    assert census['complete_deleted_with_context']==3
    assert census['complete_deleted_with_kept_reference']==3
    assert support['single_option_events']==['s0:1','s3:1']
    assert support['complete_deleted_without_unchosen_events']==['s0:1']
    assert support['paired_reference_without_unchosen_events']==['s0:1','s2:1']
    assert support['all_event_primary']=='unsupported' and support['all_event_paired_ratio']=='unsupported'
    row=next(e for e in data['events'] if e['id']=='s2:1')
    assert row['kept_reference']['id']=='s3:1'  # No opportunistic rematch.
    assert census['audit']['all_accepted_spans']==6
    assert census['audit']['single_option_accepted_spans']==2
    assert census['audit']['single_option_failure_candidates']==1


def test_unverified_source_is_not_reclassified_as_singleton_support():
    f=singleton(session());f['canonical']['events'][0]['usable']=False
    result=card.spans(f['events'],f['timeline'],f['canonical'])[0]
    assert not result['canonical'] and result['option_count'] is None
    assert result['comparator_support']=='noncanonical_choice'
    assert card.prepare_session(**f)['audit']['single_option_accepted_spans']==0


def test_actual_singleton_source_is_real_and_complete_session_retained():
    path=Path('.agent-state/drive-20261025/WC2_MISSING_COMPARATOR_FIXTURE.json')
    if not path.exists():pytest.skip('private actual-source regression fixture not distributed')
    f=read(path);opening=f['events'][766]
    assert opening['eventName']=='suggestion-open' and len(opening['currentSuggestions'])==1
    assert str(opening['currentN'])=='5'
    with pytest.raises(ValueError,match='no unchosen comparator'):prior.spans(f['events'],f['timeline'],f['canonical'])
    result=card.spans(f['events'],f['timeline'],f['canonical'])
    assert len(result)==sum(e['eventName']=='suggestion-select' for e in f['events'])
    row=next(s for s in result if s['origin']==766)
    assert row['canonical'] and row['option_count']==1 and row['unchosen']==[]
    assert not row['comparator_supported']
    prepared=card.prepare_session(**f)
    assert prepared['audit']['all_accepted_spans']==len(result)


def test_actual_prior_append_failure_remains_repaired():
    path=Path('.agent-state/drive-20261025/WC2_ACTUAL_FAILURE_FIXTURE.json')
    if not path.exists():pytest.skip('private actual-source regression fixture not distributed')
    f=read(path)
    assert [original_fields(s) for s in card.spans(f['events'],f['timeline'],f['canonical'])]==prior.spans(f['events'],f['timeline'],f['canonical'])


def test_complete_handler_reentry_and_fresh_source_replay(tmp_path):
    fs=fixture();fs[0]=singleton(equivalent('shifted'));fs[3]=singleton(fs[3])
    path=tmp_path/'fixture.json';path.write_text(json.dumps(fs),encoding='utf8')
    out=tmp_path/'out';inputs=dict(fixture=str(path))
    assert card.execute(out,inputs,card.CONSTRUCTED)['status']=='complete'
    assert card.execute(out,inputs,card.CONSTRUCTED)['status']=='complete'
    assert card.verify(out,inputs,card.CONSTRUCTED)['verified']
    summary=read(out/'SUMMARY.json')
    assert summary['sessions']==6 and summary['comparator_support']['all_event_primary']=='unsupported'
    path.write_text(path.read_text()+' ',encoding='utf8')
    with pytest.raises(ValueError,match='changed'):card.verify(out,inputs,card.CONSTRUCTED)
