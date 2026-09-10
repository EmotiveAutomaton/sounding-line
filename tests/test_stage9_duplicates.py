from runners.stage9.duplicate_audit import audit


def row(key, group, split, text):
    return {'key': key, 'independent_unit': group, 'split': split, 'before': text, 'artifact': text}


def test_copies_and_contained_long_text_link_reserve_without_reallocating():
    text = ' '.join('word'+str(i) for i in range(200))
    values = [row('a','paper-a','train',text), row('b','paper-b','reserve',text+' additional ending'),
              row('c','paper-c','development','completely unrelated words')]
    result = audit(values)
    assert result['cross_split_edges'] == 1
    assert result['reserve_groups_linked_to_other_splits'] == ['paper-b']
    assert not result['scientific_split_accepted']
    assert values[1]['split'] == 'reserve'


def test_unrelated_and_same_lineage_revisions_are_not_duplicate_independent_units():
    values = [row('a','same-paper','train','a revision about making text'),
              row('b','same-paper','train','a revision about making better text'),
              row('c','different-paper','reserve','a completely separate source')]
    assert audit(values)['edges'] == []


def test_missing_domain_does_not_hide_same_modern_arxiv_id():
    values = [row('a','arxiv:1912.05372','train','first draft'),
              row('b','unknown:1912.05372v3','reserve','differently rendered draft')]
    result = audit(values)
    assert result['cross_split_edges'] == 1
    assert result['edges'][0]['reason'].startswith('same modern arXiv')
