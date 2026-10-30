from itertools import product
import numpy as np
import pytest
from runners.drive.cards import week3_dr1_ranks as card


def test_exact_sum_matches_exhaustive_small_uniform_rank_enumeration():
    values = [sum(t) for t in product(range(1, 5), repeat=3)]
    observed = np.bincount(np.array(values)-3)/len(values)
    np.testing.assert_allclose(card.uniform_sum(3, 4), observed, atol=1e-15)


def test_ties_are_uniform_over_the_entire_tie_block_and_midrank_is_fixed():
    rng = np.random.default_rng(7)
    rows = [card.rank_one(5, [5]*200, rng) for _ in range(10000)]
    assert min(r['randomized_rank'] for r in rows) == 1
    assert max(r['randomized_rank'] for r in rows) == 201
    assert {r['midrank'] for r in rows} == {101}
    assert abs(np.mean([r['randomized_rank'] for r in rows])-101) < 2


def test_tail_direction_mid_p_and_seeded_replay():
    result = card.rank_test([1]*5, [[4]*200]*5)
    assert result == card.rank_test([1]*5, [[4]*200]*5)
    assert result['lower_tail'] and result['mid_p'] <= result['inclusive_p']
    reverse = card.rank_test([9]*5, [[4]*200]*5)
    assert not reverse['lower_tail'] and reverse['mean_rank'] == 201


@pytest.mark.parametrize('bad', [[1]*199, [1.]*200, [0]*200])
def test_malformed_banks_refuse(bad):
    with pytest.raises(ValueError): card.rank_one(1, bad, np.random.default_rng(1))


@pytest.mark.parametrize('kind,direction', [('constant', 0), ('early', -1), ('late', 1), ('tied', 0)])
def test_complete_style_prefix_known_answer_world(kind, direction):
    result = card.style_world(kind)
    assert np.sign(result['rank']['mean_midrank']-101) == direction
    assert len(result['complete_flags']) == 3
    assert all(len(v) == 202 for v in result['complete_flags'])
    if kind == 'tied': assert result['endpoints'] == [13]*3


def test_mutated_configuration_and_human_data_in_constructed_refuse(tmp_path):
    with pytest.raises(ValueError): card.execute(tmp_path, {}, dict(card.CONFIGS['constructed'], calibration_worlds=2))
    with pytest.raises(ValueError): card.execute(tmp_path, {'human':'forbidden'}, card.CONFIGS['constructed'])
