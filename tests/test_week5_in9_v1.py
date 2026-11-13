import json
import numpy as np
import pytest
from runners.drive.cards import week5_in9_v1 as study
from runners.drive.cards import week5_in9_fixture_v1 as fixture
from runners.drive.cards import week5_in9_cues_v1 as cues


def test_weighted_auc_hand_answer_with_ties():
    assert abs(study.math.auc([0, 1, 0, 1], [1, 1, 2, 3], [1, 2, 3, 1])-5/12) < 1e-14


def test_packet_4000_text_discriminability_worlds():
    points = fixture.packet_points()
    assert points['0']['observed_constructed_auc'] == .5


def test_writer_folds_do_not_split_any_writer():
    writers = np.array(['a', 'b', 'a', 'c', 'b', 'd', 'e', 'f', 'g', 'h'])
    folds, _, _ = study.math.fold_codes(writers)
    for person in np.unique(writers):
        assert len(np.unique(folds[writers == person])) == 1


def test_training_scaling_and_weighted_ridge_dense_certificate():
    rng = np.random.default_rng(19); raw = rng.normal(size=(90, 3))
    x = np.column_stack((np.ones(90), raw)); y = np.tile([0, 1], 45); weights = rng.integers(1, 4, 90)
    beta = study.math.ridge_fit(x, y, weights)
    gradient = x.T@(weights*(study.math.expit(x@beta)-y))+np.r_[0., beta[1:]]
    assert np.max(np.abs(gradient)) < 1e-8


def test_full_2000_null_handler_pause_and_independent_replay(tmp_path):
    proof = fixture.null_chain(tmp_path/'null')
    assert proof.get('passed') is True, proof
    saved = json.loads((tmp_path/'null/DRAWS.json').read_text())
    assert len(saved['draws']) == 2000 and all(v['value'][0] == .5 for v in saved['draws'])


def test_source_or_semantic_changes_cannot_reenter(tmp_path):
    frame = fixture.world(0, 200); config = {'phase': 'IN9-items', 'draws': 2000, 'max_new_draws': 1}
    with fixture.constructed_source(frame):
        assert study.execute(tmp_path, {}, config)['status'] == 'yielded'
    frame.loc[0, 'intensity'] += .1
    with fixture.constructed_source(frame), pytest.raises(ValueError, match='binding changed'):
        study.execute(tmp_path, {}, config)
    with pytest.raises(ValueError):
        study.settings({**config, 'draws': 200})


def test_count_floor_precedes_any_fit(tmp_path, monkeypatch):
    frame = fixture.world(0, 199)
    monkeypatch.setattr(study.math, 'evaluate', lambda *args: pytest.fail('fit below floor'))
    with fixture.constructed_source(frame):
        result = study.execute(tmp_path, {}, {'phase': 'IN9-items'})
        assert result['status'] == 'unsupported'
        assert study.verify(tmp_path, {}, {'phase': 'IN9-items'})['verified'] is True


def test_failed_draw_is_retained_and_no_verdict_escapes():
    point = {'value': [.7]+[0.]*6}
    draws = [point.copy() for _ in range(2000)]; draws[17] = {'failure': 'missing weighted class'}
    result = study.summaries(point, draws, {'guilt': 200, 'shame': 200}, 200)
    assert result['failed_draws'] == [17] and 'primary' not in result


def test_independent_percentile_and_se_hand_values():
    interval, se = study.reference.interval_and_se([0, 1, 2, 3])
    assert np.allclose(interval, [.075, 2.925]) and abs(se-np.sqrt(5/3)) < 1e-14


def test_frozen_cue_counts_and_independent_hand_answers():
    cases = [
        ('I hurt him and forgot. Everyone saw me.', [2, 1, 0, 0]),
        ('She was angry at me, then yelled at me.', [0, 0, 2, 0]),
        ('They laughed at me and made fun of me.', [0, 0, 0, 2]),
        ('In front of people I let down, I was embarrassed.', [1, 2, 0, 0]),
        ('A hurtful remark to somebody forgetful.', [0, 0, 0, 0]),
        ('He was not angry at me.', [0, 0, 1, 0]),
    ]
    for text, expected in cases:
        assert list(cues.count(text).values()) == expected
        assert cues.independent_count(text) == cues.count(text)
    assert cues.admission(.049, 100, 100).startswith('unsupported')
    assert cues.admission(.1, 100, 79) == 'instrument failed'
    assert cues.admission(.1, 100, 80) == 'qualified literal cue'
