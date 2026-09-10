from runners.stage9.reconcile_groups import reconcile


def test_transitive_exposure_removes_reserve_without_new_replacements():
    allocation = {'a': 'train', 'b': 'discovery', 'c': 'reserve', 'd': 'reserve'}
    mapping, updated, _ = reconcile(allocation, [{'groups':['a','b']}, {'groups':['b','c']}])
    assert updated[mapping['c']] == 'train'
    assert updated['d'] == 'reserve'
    assert sum(v=='reserve' for v in updated.values()) == 1


def test_unexposed_alias_joins_existing_reserve_and_unknown_domain_stays_provenance():
    mapping, updated, components = reconcile({'unknown:paper': 'discovery', 'arxiv:paper':'reserve'}, [{'groups':['unknown:paper','arxiv:paper']}])
    assert mapping['unknown:paper'] == 'arxiv:paper'
    assert updated == {'arxiv:paper':'reserve'}
    assert set(components['arxiv:paper']) == {'unknown:paper','arxiv:paper'}
