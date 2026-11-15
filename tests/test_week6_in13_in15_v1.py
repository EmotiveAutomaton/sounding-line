import numpy as np
import pandas as pd
import pytest
from scipy.stats import norm
from sklearn.model_selection import GroupKFold
from runners.drive.cards import week6_in13_in15_common_v1 as common
from runners.drive.cards import week6_in13_v1 as in13
from runners.drive.cards import week6_in15_v1 as in15
from runners.drive.cards import week6_in13_in15_fixture_v1 as fixture


def test_packet_auc_analytic_marker_and_ratings_controls():
    y, writers, ratings, marker = fixture.packet_in13()
    assert abs(norm.cdf(.5/np.sqrt(2))-.638163) < 1e-6
    results = []
    for x in (ratings, marker[:, None], np.column_stack([ratings, marker])):
        values = []
        for tr, te in GroupKFold(5).split(x, y, writers):
            assert not set(writers[tr]) & set(writers[te])
            prediction = in13.numeric_predictions(x[tr], x[te], y[tr])
            values.append(in13.weighted_auc(y[te], prediction, np.ones(len(te))))
        results.append(float(np.mean(values)))
    assert np.allclose(results, [.649, .650, .761], atol=.012)
    assert in13.weighted_auc([0, 0, 1, 1], [0, 0, 0, 0], np.ones(4)) == .5


def test_auc_independent_weighted_ties_and_missing_class():
    y = np.array([0, 1, 1, 0, 1]); score = np.array([.2, .2, .4, .6, .7]); w = np.array([2, 3, 1, 0, 4])
    pairwise = sum(w[i]*w[j]*((score[i] > score[j])+.5*(score[i] == score[j]))
        for i in range(len(y)) for j in range(len(y)) if y[i] == 1 and y[j] == 0)/(w[y == 1].sum()*w[y == 0].sum())
    assert in13.weighted_auc(y, score, w) == pytest.approx(pairwise)
    assert in13.weighted_auc(y, score, w, True) == pytest.approx(pairwise)
    assert in13.weighted_auc(y, score, w*y) is None


def test_profiles_freeze_split_scales_signs_and_independent_rows():
    frame = fixture.profiles(); prepared = in13.prepare_profiles(frame)
    point = in13.profile_values(prepared, np.ones(len(prepared['keys'])))
    assert len(point) == 273
    index = next(i for i, p in enumerate(prepared['panels']) if p['label'] == 'fear' and p['item'] == 'urgency')
    assert point[index] > .5 and prepared['panels'][index]['direction'] == 1
    assert 'urgency' not in prepared['panels'][index]['style']
    for draw in range(4):
        w = common.resample(prepared['keys'], draw)
        common.compare(in13.profile_values(prepared, w), in13.profile_values(prepared, w, True))
    changed = frame.copy(); changed.loc[~changed.discovery_half, 'urgency'] -= 1.2*changed.loc[~changed.discovery_half, 'emotion'].eq('fear')
    altered = in13.prepare_profiles(changed)
    assert altered['panels'][index]['direction'] == 1
    assert altered['panels'][index]['scale_SD'] == prepared['panels'][index]['scale_SD']
    assert in13.profile_values(altered, np.ones(len(altered['keys'])))[index] < -.5


def test_in13a_full2000_planted_and_null_complete_execute_replay(tmp_path):
    for name, amplitude in [('planted', .6), ('null', 0.)]:
        proof = fixture.profile_chain(tmp_path/name, amplitude)
        assert proof['passed'] and proof['all_draw_values_checked']


def test_in13_full2000_null_replay_checkpoint_and_reference(tmp_path):
    # 24 writers gave omitted-fold bootstrap draws, correctly invalidating the
    # interval. Preserve that failure; 100 writers support this exact-null ruler.
    result = fixture.chain(in13, fixture.null_pairs(people=100), tmp_path/'in13', 'IN13B')
    primary = result['analyses']['None']['primary']
    assert primary['estimate'] == 0 and primary['interval'] == [0., 0.]
    assert primary['outcome'] == 'against'
    assert len(common.seal.read(tmp_path/'in13/DRAWS.json')['draws']) == 2000
    saved = common.seal.read(tmp_path/'in13/FOLDS.json')['fits']
    keys = sorted({writer for fit in saved for writer in fit['writers']})
    weights = np.zeros(len(keys)); weights[0] = len(keys)
    omitted = in13.pair_values(saved, keys, weights)
    assert omitted['mean_gap'] is None
    frame = fixture.null_pairs()
    with fixture.table_boundary(in13, frame):
        config = {'phase': 'IN13B', 'scope': 'analyst_all6600', 'max_new_draws': 2000}
        # Reference scope is tested via an existing hand-computed bank, not a second full run.
        assert in13.settings(config)['scope'] == 'analyst_all6600'


def test_part_c_is_unconditionally_source_and_primary_coder_gated():
    with pytest.raises(ValueError, match='Part C waits'):
        in13.settings({'phase': 'IN13C', 'scope': 'qualified_real_events'})
    with pytest.raises(ValueError):
        in13.load({}, {'phase': 'IN13C', 'scope': 'qualified_real_events', 'im1_primary_coder': 'unseen'})
    with pytest.raises(ValueError, match='only'):
        in13.settings({'phase': 'IN13A', 'scope': 'analyst_all6600'})


def test_part_c_constructed_motive_gain_and_separate_coder_signs():
    frame = fixture.null_pairs(people=100); rng = np.random.default_rng(1326)
    first = frame.emotion.eq('pride').to_numpy(float)
    for coder, direction in [('published_a', 1), ('published_b', -1)]:
        for motive in in13.MOTIVES:
            frame[f'{coder}__{motive}'] = (direction*2*first if motive != 'affiliation' else np.zeros(len(frame)))+rng.normal(0, .2, len(frame))
        fitted = in13.fit_pair(frame, ('pride', 'joy'), coder)
        keys = sorted(set(fitted['writers']))
        value = in13.pair_values([fitted], keys, np.ones(len(keys)))
        assert value['pairs'][0]['ratings'] == .5
        assert value['pairs'][0]['gap'] > .45
        part = frame.loc[frame.emotion.isin(['pride', 'joy'])]
        for motive in ('achievement', 'power'):
            gap = part.loc[part.emotion.eq('pride'), f'{coder}__{motive}'].mean()-part.loc[part.emotion.eq('joy'), f'{coder}__{motive}'].mean()
            assert np.sign(gap) == direction


def test_in15_packet_corrected_fixture_and_actual_twelve_prior_consumer():
    for slope, seed, expected in ((.4, 151, .395), (0., 150, .0005)):
        frame, oracle = fixture.packet_in15(slope, seed)
        assert abs(oracle-expected) < .002
        p = in15.prepare(frame); value = in15.evaluate(p, np.ones(len(p['keys'])))
        assert abs(value['primary']-expected) < .012
        common.compare(value, in15.evaluate(p, np.ones(len(p['keys'])), True))
        assert set(value['by_label']) == set(common.FEELINGS)
        assert 'no-emotion' not in value['by_label']


def test_in15_hand_means_repeated_reader_and_missing_feeling():
    frame, _ = fixture.packet_in15(reports=40)
    frame['emotion'] = 'no-emotion'; frame.loc[[0, 1, 5], 'emotion'] = 'anger'
    p = in15.prepare(frame); w = np.ones(len(p['keys'])); repeated = frame.prolific_id.iloc[0]
    w[p['keys'].index(repeated)] = 3
    result = in15.evaluate(p, w)
    values = []
    means = frame.anger.mean(); sd = frame.anger.std(ddof=1)
    for _, part in frame.groupby('text_id'):
        yes = part.emotion.eq('anger').to_numpy(); ww = np.where(part.prolific_id.eq(repeated), 3., 1.)
        if not yes.any() or yes.all(): continue
        zz = (part.anger.to_numpy()-means)/sd
        values.append(np.average(zz[yes], weights=ww[yes])-np.average(zz[~yes], weights=ww[~yes]))
    assert result['primary'] == pytest.approx(np.mean(values))
    common.compare(result, in15.evaluate(p, w, True))
    with pytest.raises(ValueError, match='Missing prior'):
        in15.prepare(frame.drop(columns=['fear']))
    duplicate = frame.copy(); duplicate.loc[1, 'prolific_id'] = duplicate.loc[0, 'prolific_id']
    with pytest.raises(ValueError, match='Duplicate reader'):
        in15.prepare(duplicate)


def test_in15_full2000_whole_reader_replay_and_draw_support(tmp_path):
    frame, _ = fixture.packet_in15(reports=60)
    result = fixture.chain(in15, frame, tmp_path/'in15', 'IN15')
    assert result['primary']['draws'] == 2000
    assert result['primary']['failed_draws'] == []
    assert len(set(result['cell_support']['every_draw'])) > 1
    assert len(result['cell_support']['every_draw']) == 2000


def test_failure_bank_and_unsupported_cells_cannot_be_silently_dropped():
    draws = [.2]*2000; draws[99] = None
    result = common.summary(.2, draws, 40, .1)
    assert result['failed_draws'] == [99] and 'interval' not in result
    assert common.summary(.2, [.2]*2000, 1, .1)['status'] == 'unsupported'
    assert 'outcome' not in common.summary(.2, [.2]*2000, 19, .1)
    with pytest.raises(ValueError): common.summary(.2, draws[:20], 40, .1)


def test_changed_source_and_serialized_checkpoint_refused(tmp_path):
    frame, _ = fixture.packet_in15(reports=40)
    cfg = {'phase': 'IN15', 'scope': 'qualified_real_events', 'max_new_draws': 1}
    with fixture.table_boundary(in15, frame): assert in15.execute(tmp_path, {}, cfg)['status'] == 'yielded'
    frame.loc[0, 'anger'] += .1
    with fixture.table_boundary(in15, frame), pytest.raises(ValueError, match='binding changed'):
        in15.execute(tmp_path, {}, cfg)
    with pytest.raises(ValueError): in15.settings({**cfg, 'draws': 200})
    with pytest.raises(ValueError): common.canonical_source({}, 'IN15', 'qualified_real_events')
