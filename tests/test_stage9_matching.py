import copy
import pytest
from runners.stage9.matching import audit, match_budget, target_positions


def row(key, n, prefix=2):
    ids = list(range(1, n+prefix+1))
    return {'key': key, 'input_ids': ids, 'labels': [-100]*prefix+ids[prefix:], 'lineages': [key], 'kind': 'fixture'}


def test_matching_preserves_inputs_context_masks_fixed_rows_and_exact_total():
    data = [row('fixed', 7), row('a', 3), row('b', 12)]
    before = copy.deepcopy(data)
    output = match_budget(data, 16, fixed_keys=['fixed'])
    assert data == before and output[0] == before[0]
    assert sum(len(target_positions(r)) for r in output) == 16
    for old, new in zip(before, output):
        assert old['input_ids'] == new['input_ids']
        assert all(new['labels'][i] == -100 for i, value in enumerate(old['labels']) if value == -100)
    assert output == match_budget(data, 16, fixed_keys=['fixed'])


def test_impossible_budget_and_mislabeled_context_refuse():
    with pytest.raises(ValueError):
        match_budget([row('a', 3)], 4)
    with pytest.raises(ValueError):
        match_budget([row('a', 3)], 0)
    bad = row('a', 3)
    bad['labels'][2] = 700
    with pytest.raises(ValueError):
        match_budget([bad], 3)


def test_equal_token_counts_cannot_hide_source_exposure_change():
    a, b = [row('a', 3)], [row('b', 3)]
    with pytest.raises(ValueError):
        audit({'original': a, 'changed_source': b})
