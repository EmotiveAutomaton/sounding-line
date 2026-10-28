import copy
import json

import numpy as np
import pytest

from runners.drive.cards import week3_fic1_scoring as s

W = [f'w{i}' for i in range(6)]
def scores(value): return dict.fromkeys(W, value)
def bank(value): return [scores(value) for _ in range(1000)]
def fixture(): return dict(constructed=True, writers=W)


def test_fingerprint_and_fractional_ties():
    assert s.gallery_scores(np.eye(6), np.eye(6), W) == scores(1.)
    assert s.gallery_scores(np.ones((6, 2)), np.ones((6, 2)), W) == scores(1/6)


def test_probe_does_not_set_gallery_scale():
    b = np.array([[0., 0.], [1., 0.], [2., 1.], [3., 1.], [4., 2.], [5., 2.]])
    a = b.copy(); a[0] = [1e9, -1e9]
    result = s.gallery_scores(a, b, W)
    assert [result[w] for w in W[1:]] == [1.] * 5


def test_absent_writer_is_not_a_smaller_gallery():
    a = np.eye(6); a[0] = np.nan
    assert s.gallery_scores(a, np.eye(6), W) is None


def test_null_is_exact_zero_and_not_admitted():
    out = s.compare(scores(.2), scores(.2), bank(.2), W)
    assert out['state'] == 'not_detected' and not out['numerical_pass']
    assert out['real_minus_context']['effect'] == 0
    assert out['real_minus_context']['ci_low'] == out['real_minus_context']['ci_high'] == 0
    assert out['permutation']['one_sided_p'] == 1


def test_known_positive_tail_and_direction():
    out = s.compare(scores(1.), scores(0.), bank(0.), W)
    assert out['numerical_pass'] and out['permutation']['one_sided_p'] == 1/1001
    opposite = s.compare(scores(0.), scores(1.), bank(0.), W)
    assert opposite['state'] == 'negative' and not opposite['numerical_pass']
    assert not out['scientific_admission'] and not out['control_construction_validated']


def test_tail_counts_ties():
    refs = bank(0.)
    refs[0] = scores(.5); refs[1] = scores(1.)
    out = s.compare(scores(.5), scores(0.), refs, W)
    assert out['permutation']['one_sided_p'] == 3/1001


def test_one_missing_reference_invalidates_whole_bank():
    refs = bank(0.); refs[2].pop(W[0])
    out = s.compare(scores(1.), scores(0.), refs, W)
    assert out['state'] == 'invalid' and out['missing_draws'] == [2]
    assert 'permutation' not in out


def test_bank_cannot_be_reduced():
    with pytest.raises(ValueError, match='complete frozen'):
        s.compare(scores(1.), scores(0.), bank(0.)[:999], W)


def test_mapping_order_is_not_an_analysis_choice():
    a = {w:i/5 for i, w in enumerate(W)}
    b = dict(reversed(list(a.items())))
    assert s.compare(a, scores(0.), bank(0.), W) == s.compare(b, scores(0.), bank(0.), W)


def test_exact_mcnemar_and_fractional_tie_refusal():
    out = s.genre_comparison(scores(1.), scores(0.), W)
    table = out['binary_table']
    assert table['cells'] == {'00':0, '01':0, '10':6, '11':0}
    assert table['exact_two_sided_mcnemar_p'] == .03125
    assert s.genre_comparison(scores(.5), scores(0.), W)['binary_table']['state'] == 'unsupported'


@pytest.mark.parametrize('values,state', [([0., .2, .6, 1.], 'rising'),
    ([1., 1., 1., 1.], 'nonrising_stop'), ([1., .6, .2, 0.], 'nonrising_stop'),
    ([0., 1., 0., .1], 'nonrising_stop')])
def test_length_condition_can_fail_at_ceiling_or_misleading_hump(values, state):
    out = s.length_curve({k:scores(v) for k,v in zip(s.LEVELS, values)}, W)
    assert out['state'] == state


def test_common_length_roster_cannot_drift():
    curves = {k:scores(i/3) for i,k in enumerate(s.LEVELS)}
    curves['1000'].pop(W[0])
    assert s.length_curve(curves, W)['state'] == 'unsupported'


@pytest.mark.parametrize('value', [float('nan'), float('inf'), -.01, 1.01, True, '1'])
def test_bad_scores_refuse(value):
    with pytest.raises(ValueError): s.score_array(scores(value), W)


def test_ambiguous_roster_refuses():
    with pytest.raises(ValueError): s.score_array(scores(0.), W[::-1])
    with pytest.raises(ValueError): s.score_array(scores(0.), W+[W[0]])


def test_constructed_handler_replay_and_immutable_reentry(tmp_path):
    src = tmp_path/'fixture.json'; src.write_text(json.dumps(fixture()), encoding='utf8')
    output = tmp_path/'output'; inputs = dict(fixture=str(src))
    s.execute(output, inputs, s.CONFIG)
    before = {p.name:p.read_bytes() for p in output.iterdir()}
    assert s.verify(output, inputs, s.CONFIG)['all_arithmetic_recomputed']
    s.execute(output, inputs, s.CONFIG)
    assert before == {p.name:p.read_bytes() for p in output.iterdir()}
    changed = json.loads((output/'ARITHMETIC.json').read_text())
    changed['null']['real'] = .8
    (output/'ARITHMETIC.json').write_text(json.dumps(changed), encoding='utf8')
    with pytest.raises(ValueError, match='replay differs'): s.verify(output, inputs, s.CONFIG)


def test_human_scope_is_not_accepted_by_native_handler(tmp_path):
    src = tmp_path/'fixture.json'; src.write_text(json.dumps(dict(constructed=False, writers=W)))
    with pytest.raises(ValueError, match='constructed input'):
        s.execute(tmp_path/'out', dict(fixture=str(src)), s.CONFIG)
    config = copy.deepcopy(s.CONFIG); config['mode'] = 'full'
    with pytest.raises(ValueError, match='constructed-only'):
        s.execute(tmp_path/'other', dict(fixture=str(src)), config)
