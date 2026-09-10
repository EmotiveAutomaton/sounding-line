"""Split and evidence-projection failures on known independent units."""
from runners.stage9.data import grouped_allocation, union_duplicates, visible_revision, paper_key


def test_exact_reserve_excludes_prior_exposure_and_is_order_invariant():
    groups = ['group-' + str(i) for i in range(103)]
    exposed = groups[:3]
    first = grouped_allocation(groups, exposed)
    assert first == grouped_allocation(reversed(groups), reversed(exposed))
    assert sum(s == 'reserve' for s in first.values()) == 30
    assert all(first[g] == 'pilot' for g in exposed)


def test_duplicate_merges_are_transitive_across_whole_lineages():
    rows = [{'group': 'a', 'before': 'first', 'artifact': 'same'},
            {'group': 'b', 'before': ' SAME ', 'artifact': 'later'},
            {'group': 'c', 'before': 'Later', 'artifact': 'last'}]
    unions, merges = union_duplicates(rows)
    assert len(set(unions.values())) == 1
    assert len(merges) == 2
    assert paper_key('https://arxiv.org/abs/1912.05372v2', 'arxiv') == 'arxiv:1912.05372'


def test_primary_view_never_carries_labels_markup_ids_or_future():
    record = {'artifact': 'finished words', 'before': 'draft words', 'group': 'secret maker',
              'labels': ['style'], 'raw_votes': ['style'], 'edits': ['secret operation'],
              'future': 'unseen continuation', 'source_line': 123}
    primary = visible_revision(record, 'artifact')
    assert set(primary) == {'text', 'context'}
    assert 'draft words' not in str(primary)
    assert 'secret' not in str(primary)
    assert set(visible_revision(record, 'process_pair')) == {'before', 'after', 'context'}
