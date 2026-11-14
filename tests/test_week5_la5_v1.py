import numpy as np
import pytest
from runners.drive.cards import week5_la5_v1 as study
from runners.drive.cards import week5_la5_fixture_v1 as fixture


def test_packet_four_speakers_two_events_hand_computed_shares():
    acts, laughs, speech, metadata = fixture.meeting(); meta = next(iter(metadata.values()))
    rows, _ = study.math.events(acts, laughs, speech, meta)
    assert [r['joined'] for r in rows] == [False, True]
    assert np.allclose([r['outcome'] for r in rows], [-.2, .2])
    assert np.isclose(rows[0]['outcome']-rows[1]['outcome'], -.4)
    assert [(r['before_target_words'], r['before_total_words'], r['after_target_words'], r['after_total_words']) for r in rows] == [(4, 10, 2, 10), (2, 10, 4, 10)]
    assert study.math.events(acts, laughs, speech, meta, True) == (rows, study.math.events(acts, laughs, speech, meta)[1])


def test_distinct_other_speakers_and_strict_onsets_not_overlapping_laughs():
    acts, laughs, speech, metadata = fixture.meeting(); meta = next(iter(metadata.values()))
    laughs[1]['speaker'] = 'B'
    assert len(study.math.events(acts, laughs, speech, meta)[0]) == 1
    laughs[1]['speaker'] = 'C'; laughs[1]['start'] = acts[0]['end']-.1; laughs[1]['end'] = acts[0]['end']+1
    assert len(study.math.events(acts, laughs, speech, meta)[0]) == 1


def test_join_window_and_word_window_boundary_rules():
    assert study.math.window_count([0, 1, 2, 3], 1, 3) == 2
    acts, laughs, speech, metadata = fixture.meeting(); meta = next(iter(metadata.values()))
    laughs[-1]['start'] = 304.5; laughs[-1]['end'] = 304.7
    assert study.math.events(acts, laughs, speech, meta)[0][1]['joined'] is True
    laughs[-1]['start'] = 304.5001; laughs[-1]['end'] = 304.7
    assert study.math.events(acts, laughs, speech, meta)[0][1]['joined'] is False


def test_source_exclusions_preserve_rows_and_annotation_marks_are_not_words():
    acts, laughs, speech, metadata = fixture.meeting(); meta = next(iter(metadata.values()))
    meta['speakers']['A']['person'] = None; meta['duration'] = 330
    rows, counts = study.math.events(acts, laughs, speech, meta)
    assert len(rows) == 2 and not any(r['model_eligible'] for r in rows)
    assert counts['missing_global_person_events'] == 2 and counts['window_outside_observed_meeting_span_events'] == 1
    acts[0]['words'][0]['annotation'] = 'laughter'
    assert study.math.word_count(acts[0]) == 2
    assert len(study.math.events(acts, laughs, speech, meta)[0]) == 1


def test_complete_two_meeting_source_pause_and_independent_replay(tmp_path):
    assert fixture.projection_chain(tmp_path/'source')['passed'] is True


def test_qualified_global_speaker_meeting_fit_matches_dense_oracle_with_repeated_people():
    rows = [r for r in fixture.model_rows(-.1) if r['corpus'] == 'AMI']; prepared = study.math.arrays(rows)
    meetings = sorted({r['meeting'] for r in rows}); weights = np.array([0, 1, 2, 1]*5)
    for multiplicities in (None, weights):
        estimate = study.math.estimate(prepared, multiplicities, meetings)
        assert abs(estimate+.1) < 1e-9
        assert abs(estimate-study.math.dense_reference(prepared, multiplicities, meetings)) < 1e-9


def test_full_null_2000_meeting_banks_and_independent_reentry(tmp_path):
    assert fixture.null_chain(tmp_path/'null')['passed'] is True


def test_unsupported_draws_are_retained_and_single_meeting_has_no_interval():
    rows = [r for r in fixture.model_rows() if r['corpus'] == 'AMI']; values = [0.]*2000; values[91] = None
    result = study.summarize(0., values, rows, 20)
    assert result['status'] == 'invalid_uncertainty' and result['failed_draws'] == [91] and 'interval' not in result
    one = study.summarize(0., [], rows, 1)
    assert one['interval'] is None and one['status'] == 'below floor, descriptive'
    with pytest.raises(ValueError):
        study.summarize(0., [0.]*10, rows, 20)


def test_primary_negative_direction_and_exact_null_classification():
    rows = [r for r in fixture.model_rows() if r['corpus'] == 'AMI']
    assert study.summarize(-.1, [-.1]*2000, rows, 20)['outcome'] == 'supports'
    assert study.summarize(.1, [.1]*2000, rows, 20)['outcome'] == 'against'
    assert study.summarize(0., [0.]*2000, rows, 20)['outcome'] == 'band-null'


def test_phase_scope_and_source_binding_refuse_changes(tmp_path):
    with pytest.raises(ValueError):
        study.settings({'phase': 'LA5', 'draws': 200})
    with pytest.raises(ValueError):
        study.load_source({})
    with pytest.raises(ValueError):
        study.load_prepared({})
    rows = fixture.model_rows(); config = {'phase': 'LA5', 'max_new_draws': 1}
    with fixture.table_boundary(rows):
        assert study.execute(tmp_path, {}, config)['status'] == 'yielded'
    rows[0]['outcome'] += .01
    with fixture.table_boundary(rows), pytest.raises(ValueError, match='binding changed'):
        study.execute(tmp_path, {}, config)
