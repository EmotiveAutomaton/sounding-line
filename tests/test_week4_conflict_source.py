import copy
import pytest
from runners.drive.cards import week4_conflict_source as m


def test_known_answers():
    assert m.known_answers()['verified']


def test_sparse_all_contexts():
    model = m.KneserNey([['a', 'a', 'c'], ['b', 'c'], ['d', 'a']]*4)
    fast = m.Conflict(model)
    for a in sorted(model.vocabulary)+['new']:
        for b in sorted(model.vocabulary)+['new']:
            assert fast([a, b]) == pytest.approx(m.dense(model, [a, b]), abs=2e-12)


def test_ties_and_single_outcome():
    model = m.KneserNey([['a'], ['b']]*8)
    fast = m.Conflict(model)
    assert fast([])['top_two_margin'] == 0
    assert fast([])['entropy'] > 0
    assert fast(['not-in-vocabulary']) == pytest.approx(m.dense(model, ['not-in-vocabulary']), abs=2e-12)


def test_selection_preserves_floor_and_is_order_independent():
    rows = [dict(writer=str(i)) for i in range(30)]
    assert m.selection(rows) == m.selection(list(reversed(rows)))
    assert len(m.selection(rows)['selected_writers']) == 20
    with pytest.raises(ValueError, match='floor'):
        m.selection(rows[:19])


def test_constructed_replay_and_tampering(tmp_path):
    config = m.configuration('constructed')
    m.execute(tmp_path, {}, config)
    assert m.verify(tmp_path, {}, config)['full_fresh_replay']
    m.atomic(tmp_path/'SUMMARY.json', {'verified': True})
    with pytest.raises(ValueError, match='summary differs'):
        m.verify(tmp_path, {}, config)


def test_feature_identity_and_probability_refusal(tmp_path):
    records = [dict(writer=str(i), session=str(i), training_sequences=[['a', 'b', 'a']], words=[])
               for i in range(3)]
    model = m.KneserNey([['a', 'b', 'a']]*2)
    p = model.score('a', [])
    records[0]['words'] = [dict(index=0, token='a', context=[], population_probability=p)]
    rows = [dict(writer='0', session='0', index=0, population_surprisal=-m.math.log(p))]
    result = m.features(rows, records, ['0'], tmp_path)
    assert len(result) == 1 and result[0]['writer'] == '0'
    changed = copy.deepcopy(records); changed[0]['words'][0]['population_probability'] *= .99
    with pytest.raises(ValueError, match='probability differs'):
        m.features(rows, changed, ['0'], tmp_path)
