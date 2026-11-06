"""Prompt exclusion, support-only selection and complete source replay."""
from copy import deepcopy
import pytest
from runners.drive.cards import week4_d33_prompt_source as card
from runners.drive.cards.timing_census import read
from runners.drive.cards.timing_p6 import gzread


def test_prompt_future_exclusion_and_exact_donor_budget():
    source = card.fixture()
    for unit in source.units['pair2'].values():
        proof = unit['proof']
        if not proof['supported']:
            continue
        target = source.lookup[proof['target_session']]
        for sid in proof['own_sessions']+proof['donor_sessions']:
            assert source.lookup[sid]['prompt'] != target['prompt']
            assert source.lookup[sid]['end_at'] < target['timestamp']
        assert proof['own_tokens'] == proof['donor_tokens']
        assert len(proof['own_sessions']) == len(proof['donor_sessions'])


def test_selection_ignores_outcomes_and_preserves_complete_partition():
    source = card.fixture()
    _, roster = card.roster_for(source)
    before = deepcopy(source.saved)
    for row in source.saved['rows']:
        row['log_pause'] = 1e99
        row['personal_surprise'] = -1e99
    assert card.roster_for(source)[1] == roster
    assert len(roster['retained_keys']) == 4
    assert len(roster['unsupported_keys']) == 2
    assert set(map(tuple, roster['retained_keys']+roster['unsupported_keys'])) == {
        (r['session'], r['index']) for r in before['rows']}


def test_absent_calibration_drops_only_explicit_unsupported_writer():
    source = card.fixture()
    source.units['pair2']['b3']['proof']['supported'] = False
    _, roster = card.roster_for(source)
    assert roster['calibration_unsupported_keys'] == [['b4', 0], ['b4', 1]]
    assert roster['retained_keys'] == [['a4', 0], ['a4', 1]]


def test_full_native_protocol_replays_and_copies_original_fields(tmp_path):
    config = card.configuration('constructed')
    card.execute(tmp_path, {}, config)
    assert card.verify(tmp_path, {}, config)['complete_source_replay']
    summary = read(tmp_path/'SUMMARY.json')
    assert summary['reused_covariate_sessions'] == summary['rebuilt_covariate_sessions'] == 1
    assert not summary['statistical_fit_computed']
    original = {(r['session'], r['index']): r for r in card.fixture().saved['rows']}
    for row in gzread(tmp_path/'DESIGN.json.gz'):
        prior = original[row['session'], row['index']]
        for key in prior.keys()-{'donor_surprise'}:
            assert row[key] == prior[key]
        assert row['original_personal_surprise'] == prior['personal_surprise']


def test_changed_output_refuses_complete_replay(tmp_path):
    config = card.configuration('constructed')
    card.execute(tmp_path, {}, config)
    (tmp_path/'CALIBRATION.json').write_text('{}', encoding='utf8')
    with pytest.raises(ValueError, match='Complete fresh source replay differs'):
        card.verify(tmp_path, {}, config)


def test_input_and_mode_changes_refuse(tmp_path):
    with pytest.raises(ValueError, match='Frozen source configuration'):
        card.execute(tmp_path, {}, dict(card.configuration('constructed'), seed=1))
    with pytest.raises(ValueError, match='Exact parent inputs'):
        card.authenticate({})


def test_missing_covariate_word_refuses_instead_of_silently_dropping(tmp_path, monkeypatch):
    original = card.fixture_covariate
    def damaged(source, sid):
        result = original(source, sid)
        result['words'].pop('0')
        return result
    monkeypatch.setattr(card, 'fixture_covariate', damaged)
    with pytest.raises(KeyError):
        card.execute(tmp_path, {}, card.configuration('constructed'))
