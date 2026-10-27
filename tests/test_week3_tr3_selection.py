import copy
import json
import math

import pytest
from runners.drive.cards import week3_tr3_selection as m


def fixture():
    roster = []; banks = {'model': {}, 'human': {}}
    for i in range(5):
        sid = str(i); writer = 'writer'+sid
        row = dict(session=sid, writer=writer, prompt='p', half='discovery')
        roster.append(row)
        banks['model'][sid] = dict(row, feature_counts={'w1:capture': 20, 'w1:common': 5})
        banks['human'][sid] = dict(row, feature_counts={'w1:capture': 1, 'w1:common': 100})
    roster.append(dict(session='test', writer='unseen', prompt='p', half='test'))
    split = dict(seed=20261026, writers={r['writer']: r['half'] for r in roster},
                 session_counts={r['writer']: 1 for r in roster})
    result = dict(census=dict(roster=roster), split=split)
    for bank in banks:
        agg, _ = m.aggregate(list(banks[bank].values()), roster[:-1])
        result[bank] = dict(sessions=banks[bank], aggregate=agg)
    return result


def arguments(f):
    _, writers = m.aggregate(list(f['model']['sessions'].values()), f['census']['roster'][:-1])
    return f['model']['aggregate'], f['human']['aggregate'], writers


def test_equal_banks_select_nothing():
    f = fixture(); model, _, writers = arguments(f)
    assert m.select(model, model, writers)['features'] == []


def test_planted_recurrent_feature_matches_analytic_value():
    result = m.select(*arguments(fixture()))
    assert [r['feature'] for r in result['features']] == ['w1:capture']
    row = result['features'][0]
    pm = 100.5/126; ph = 5.5/506
    assert row['model_pmi'] == pytest.approx(math.log(2*pm/(pm+ph)))
    assert row['model_writers'] == row['model_sessions'] == 5
    assert row['frequency_decile'] == 5
    assert not result['families']['p']['supported']


@pytest.mark.parametrize('field', ['count', 'sessions', 'writers'])
def test_sparse_support_refuses_selection(field):
    model, human, writers = arguments(fixture())
    if field == 'count':
        model['counts']['w1:capture'] = 9
    elif field == 'sessions':
        model['session_support']['w1:capture'] = 4
    else:
        writers['w1:capture'] = 4
    assert m.select(model, human, writers)['features'] == []


def test_frequency_ties_never_split_and_families_are_separate():
    rows = [dict(feature='w1:'+str(i), family='w1', pooled_count=i//2) for i in range(10)]
    rows.append(dict(feature='p:.', family='p', pooled_count=999))
    m.deciles(rows)
    assert [r['frequency_decile'] for r in rows] == [1,1,3,3,5,5,7,7,9,9,5]


def test_missing_human_family_is_unsupported():
    model, _, writers = arguments(fixture())
    result = m.select(model, dict(counts={}, session_support={}), writers)
    assert result['features'] == [] and not result['families']['w1']['supported']


@pytest.mark.parametrize('bad', [-1, 0, 1.1, True])
def test_malformed_counts_refuse(bad):
    with pytest.raises(ValueError, match='positive integer'):
        m.checked_counts({'w1:x': bad})


def test_identity_or_missing_population_refuses():
    f = fixture(); rows = list(f['model']['sessions'].values()); roster = f['census']['roster'][:-1]
    with pytest.raises(ValueError, match='population'):
        m.aggregate(rows[:-1], roster)
    rows[0]['writer'] = 'different'
    with pytest.raises(ValueError, match='identity'):
        m.aggregate(rows, roster)


def test_full_handler_reentry_replay_tamper_and_aggregate(tmp_path):
    f = fixture(); path = tmp_path/'fixture.json'; path.write_text(json.dumps(f), encoding='utf8')
    out = tmp_path/'output'; inputs = dict(fixture=str(path)); config = dict(mode='constructed', seed=20261026)
    m.execute(out, inputs, config)
    before = {p.name: p.read_bytes() for p in out.iterdir() if p.name != 'PROGRESS.json'}
    assert m.verify(out, inputs, config)['complete_selection_replay']
    m.execute(out, inputs, config)
    assert before == {p.name: p.read_bytes() for p in out.iterdir() if p.name != 'PROGRESS.json'}
    assert json.loads((out/'SUMMARY.json').read_text())['test_payloads_read'] == 0
    (out/'SELECTION.json').write_text('{}')
    with pytest.raises(ValueError, match='selection replay'):
        m.verify(out, inputs, config)
    f['human']['aggregate']['counts']['w1:common'] += 1
    path.write_text(json.dumps(f), encoding='utf8')
    with pytest.raises(ValueError, match='aggregate differs'):
        m.execute(tmp_path/'changed', inputs, config)


def test_unknown_feature_family_refuses():
    with pytest.raises(ValueError, match='positive integer'):
        m.checked_counts({'unknown:x': 1})
