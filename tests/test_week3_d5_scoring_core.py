"""Independent numerical oracles and refusal checks for the frozen D5 reader."""
import copy
import numpy as np
import pytest
from runners.stage14.common import read, freeze
from runners.drive.cards import week3_d5_scoring_core as c
from runners.drive.cards import week3_d5_scoring_validation as v
from runners.drive.cards.timing_pmap_stats import identify


def test_constructed_end_to_end_and_serialized_replay(tmp_path):
    assert v.execute(tmp_path, {}, v.CONFIG)['status'] == 'complete'
    assert v.verify(tmp_path, {}, v.CONFIG)['full_fresh_numerical_replay']
    s = read(tmp_path/'SUMMARY.json'); assert len(s['cases']) == 16 and not s['human_outcomes_computed']
    s['signed_slope_checks'] = 0
    (tmp_path/'SUMMARY.json').unlink(); freeze(tmp_path/'SUMMARY.json', s)
    with pytest.raises(ValueError, match='replay differs'): v.verify(tmp_path, {}, v.CONFIG)


def test_process_matches_canonical_partial_missing_and_probe_independence():
    a = np.array([[0, np.nan, 99, 2], [1, 4, 30, 3], [2, 2, 40, 4]], float)
    b = np.array([[0, 2, np.nan, 1], [1, np.nan, np.nan, 1], [2, 4, np.nan, 1]], float)
    scores, m = c.process_scores(a, b, np.arange(3))
    assert scores.tolist() == identify(a, b)['scores']
    assert (m['used_features'], m['absent_gallery_features'], m['constant_gallery_features']) == (2, 1, 1)
    extra = np.vstack([a, [1e12, -1e12, 0, 0]])
    assert np.array_equal(c.process_scores(extra, b, np.array([0,1,2,0]))[0][:3], scores)
    # The third noisy probe is nearest gallery 1 after B-only scaling.
    assert np.array_equal(c.process_scores(a, b, np.array([2,0,1]))[0], [0.,0.,1.])
    assert np.array_equal(c.process_scores(np.eye(3), np.eye(3), np.array([2,0,1]))[0], np.zeros(3))


def test_profile_weights_explicit_oracle_and_roles():
    rows, folds, roster = v.fixture(); rng = np.random.default_rng(9)
    x = rng.uniform(.1, 2, (len(rows), 7)); k = x@x.T
    for fold in [None, 0, 1, 2]:
        plan = c.profile_plan(rows, folds, roster, 'final', donor_fold=fold)
        context = 'literal' if fold is None else 'independent'
        def explicit(i):
            target = rows[i]
            chosen = [j for j, r in enumerate(rows) if r['prompt'] == target['prompt'] and
                (r['writer'] != target['writer'] if fold is None else folds[r['writer']] == fold)]
            if fold is not None: assert not {rows[j]['writer'] for j in chosen} & set(plan['gallery'])
            return x[chosen].mean(0)
        aa = np.array([explicit(i) for i in plan['probes']])
        bb = np.array([np.mean([explicit(i) for i in g], 0) for g in plan['groups']])
        sim = aa@bb.T / np.outer(np.linalg.norm(aa, axis=1), np.linalg.norm(bb, axis=1))
        ties = np.isclose(sim, sim.max(1)[:, None], rtol=1e-12, atol=1e-12)
        expected = ties[np.arange(len(aa)), plan['truth']]/ties.sum(1)
        assert np.array_equal(c.score_character(rows, folds, plan, k, np.ones(len(rows), bool), context), expected)
        a, b = c.process_profiles(rows, folds, plan, {'final': x}, context)
        assert np.allclose(a, aa) and np.allclose(b, bb)


def test_bootstrap_explicit_cluster_oracle_and_undefined_draws():
    roster = ['a', 'b', 'c']; writers = ['a']*4+['b']*3+['c']*2
    bins = ['0','1','2','3','0','0','missing','1','3']; scores = [.8,.4,.5,.1,.3,.7,.9,.8,.2]
    result = c.slope_interval(writers, bins, scores, roster)
    draws = np.random.default_rng(20261026).integers(3, size=(2000,3))
    expected = []
    for sampled in draws:
        num = den = 0.
        for index in sampled:
            selected = [(int(b)+.5, y) for w,b,y in zip(writers,bins,scores) if w == roster[index] and b != 'missing']
            x,y = np.array(selected).T; x = x/4
            for xx,yy in zip(x,y):
                num += (xx-x.mean())*(yy-y.mean())/len(x); den += (xx-x.mean())**2/len(x)
        expected.append(None if den == 0 else num/den)
    assert result['undefined_draws'] == sum(x is None for x in expected) > 0
    assert result['interval'] is None and result['support']['missing_bin_probes'] == 1
    assert all(a is b if a is None or b is None else np.isclose(a,b) for a,b in zip(expected,result['draws']))


def test_missing_evidence_and_invalid_identities_refuse():
    rows, folds, roster = v.fixture(); broken = copy.deepcopy(rows)
    for r in broken:
        if r['writer'] == 'w0': r['support']['final'] = False
    with pytest.raises(ValueError, match='Unsupported'): c.profile_plan(broken, folds, roster, 'final')
    with pytest.raises(ValueError, match='Fixed truth'): c.process_scores([[1,2]], [[1,2],[2,3]], [.5])
    with pytest.raises(ValueError, match='Whole missing'): c.process_scores([[np.nan,np.nan]], [[1,2],[2,3]], [0])
    with pytest.raises(ValueError, match='Whole missing'): c.process_scores([[np.inf,2]], [[1,2],[2,3]], [0])
    plan = c.profile_plan(rows, folds, roster, 'selection')
    with pytest.raises(ValueError, match='support mismatch'): c.process_profiles(rows, folds, plan, {'selection': np.full((48,2),np.nan)}, 'real')
    with pytest.raises(ValueError, match='share bin'): c.slope_terms(['a'], ['4'], [.5], ['a'])


def test_all_constant_ties_and_yield(tmp_path):
    scores, m = c.process_scores(np.ones((7,3)), np.ones((4,3)), np.zeros(7,dtype=int))
    assert np.array_equal(scores, np.full(7,.25)) and m['used_features'] == 0
    freeze(tmp_path/'YIELD_REQUEST.json', {'why':'test'})
    assert v.execute(tmp_path, {}, v.CONFIG)['status'] == 'yielded'
    assert not (tmp_path/'SUMMARY.json').exists()
