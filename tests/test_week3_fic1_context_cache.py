from copy import deepcopy
import pytest
from runners.drive.cards import week3_fic1_context_cache as m
from tests.test_week3_fic1_context import fixture


@pytest.mark.parametrize('capacity', [1, 2, 128])
def test_complete_outputs_and_reassignments_equal_original(capacity):
    data = fixture(); config = m.original.CONFIG
    cache = m.ContextCache(data, config, capacity)
    for index in [None, 0, 1, 7, 0, None]:
        labels = (m.original.role_assignment(data['units'], cache._folds, index, config['seed'])
                  if index is not None else None)
        assert m.canonical(cache.prepare(labels)) == m.canonical(m.original.prepare(data, config, labels))
        assert len(cache._cache) <= capacity


def test_snapshot_and_returned_output_cannot_poison_cache():
    data = fixture(); config = deepcopy(m.original.CONFIG)
    expected = m.canonical(m.original.prepare(data, config)); cache = m.ContextCache(data, config)
    data['units'][0]['whole']['word_counts'] = {'changed':999}
    config['seed'] = -1
    result = cache.prepare(); result['rosters'].clear(); result['writer_folds'].clear()
    result['rotations'][0]['context_profiles'].clear()
    assert m.canonical(cache.prepare()) == expected


def test_missing_donors_and_instances_remain_separate():
    data = fixture(); old = m.ContextCache(data, m.original.CONFIG)
    expected = m.canonical(old.prepare())
    changed = deepcopy(data)
    for unit in changed['units']:
        if unit['writer'] == 'w0': unit['prompt'] = 'isolated-prompt'
    for row in changed['rows']:
        if row['writer'] == 'w0': row['prompt'] = 'isolated-prompt'
    new = m.ContextCache(changed, m.original.CONFIG)
    assert m.canonical(new.prepare()) == m.canonical(m.original.prepare(changed, m.original.CONFIG))
    assert m.canonical(old.prepare()) == expected
    assert any(not r for r in old.prepare()['rosters'].values())


def test_cache_hits_reuse_only_exact_donor_membership():
    data = fixture(); cache = m.ContextCache(data, m.original.CONFIG)
    keys = sorted(cache._units)
    first = cache._measure(keys[:1], False, None)
    second = cache._measure(keys[:2], False, None)
    assert cache.misses == 2 and cache.hits == 0
    assert cache._measure(keys[:1], False, None) == first
    assert cache.hits == 1
    assert first['donor_sessions'] == 1 and second['donor_sessions'] == 2
    assert cache._measure(keys[:1], False, 8) is None


def test_wrong_roles_and_invalid_capacities_refused():
    data = fixture(); cache = m.ContextCache(data, m.original.CONFIG)
    labels = {u['session']:u['writer'] for u in data['units']}
    sid = data['units'][0]['session']; own = labels[sid]
    labels[sid] = next(w for w in cache._folds if cache._folds[w] != cache._folds[own])
    with pytest.raises(ValueError, match='roles'): cache.prepare(labels)
    for capacity in [0, 129, True, 2.0]:
        with pytest.raises(ValueError, match='capacity'): m.ContextCache(data, m.original.CONFIG, capacity)


def test_native_handler_refuses_human_configuration(tmp_path):
    with pytest.raises(ValueError, match='constructed-only'):
        m.execute(tmp_path, {}, dict(m.CONFIG, mode='human'))
