import copy
import json

import pytest

from runners.drive.cards import week6_tr2_v1 as card
from runners.drive.cards import week6_tr2_fixture_v1 as fixture


def manifest(tmp_path):
    evidence = tmp_path / 'constructed-census.json'
    evidence.write_text('{"by_construction":true}\n', encoding='utf8')
    return dict(schema='TR2-support-v1', source_kind='constructed',
                source_pins={'census': {'path': evidence.name, 'sha256': card.sha(evidence)}},
                settings=[dict(id=name, measurement='constructed measurement', unit='constructed person',
                               mapping_frozen=True, holds=[], checks=[dict(id='paired_support', status='passed',
                               count=32, floor=20, unit='constructed people', evidence='census')]) for name in card.SETTINGS])


def test_support_distinguishes_failed_from_unresolved(tmp_path):
    value = manifest(tmp_path)
    value['settings'][0]['mapping_frozen'] = False
    value['settings'][0]['holds'] = ['Measurement mapping awaits owner review']
    value['settings'][1]['checks'][0].update(status='failed', count=19)
    answer = card.support_report(value, tmp_path)
    assert [r['status'] for r in answer['settings']] == ['source-held', 'unsupported', 'support-declared; source-specific estimator still required']
    assert not answer['scientific_admission']
    assert all(r['scientific_verdict'] is None for r in answer['settings'])


@pytest.mark.parametrize('mutation', ['duplicate', 'missing', 'substitute', 'false_count', 'pending_count', 'boolean_count', 'pin', 'extra'])
def test_strict_support_boundary(tmp_path, mutation):
    value = manifest(tmp_path)
    if mutation == 'duplicate': value['settings'][1]['id'] = 'refusing'
    if mutation == 'missing': value['settings'].pop()
    if mutation == 'substitute': value['settings'][0]['id'] = 'replacement_source'
    if mutation == 'false_count': value['settings'][0]['checks'][0]['count'] = 1
    if mutation == 'pending_count': value['settings'][0]['checks'][0]['status'] = 'pending'
    if mutation == 'boolean_count': value['settings'][0]['checks'][0]['count'] = True
    if mutation == 'pin': value['source_pins']['census']['sha256'] = '0' * 64
    if mutation == 'extra': value['settings'][0]['demographics'] = []
    with pytest.raises(ValueError): card.support_report(value, tmp_path)


def test_json_duplicate_and_nonfinite_refuse(tmp_path):
    path = tmp_path / 'bad.json'
    for text in ('{"x":1,"x":2}', '{"x":NaN}'):
        path.write_text(text, encoding='utf8')
        with pytest.raises(ValueError): card.read(path)


def test_hash_halves_are_whole_balanced_order_invariant():
    units = ['session-a', 'session-b', 'session-c', 'session-d', 'session-e']
    split = card.whole_unit_halves(units, 'refusing')
    assert split == card.whole_unit_halves(reversed(units), 'refusing')
    assert sorted(split.values()) == [0, 0, 0, 1, 1]
    with pytest.raises(ValueError): card.whole_unit_halves(['same', 'same'], 'refusing')
    with pytest.raises(ValueError): card.whole_unit_halves(['single'], 'refusing')


def test_wc4_grammatical_denominator_and_missing_opportunity():
    tokens = [('Ada', 'PROPN'), ('cat', 'NOUN'), ('runs', 'VERB'), ('bright', 'ADJ'),
              ('quickly', 'ADV'), ('is', 'AUX'), ('the', 'DET'), ('42', 'NUM'), ('!', 'PUNCT')]
    result = card.grammatical_counts([[dict(text=t, pos=p) for t, p in tokens]])
    assert result['counts'] == dict(nouns=2, verbs=1, adjectives=1, adverbs=1)
    assert result['letter_bearing_tokens'] == 7
    assert result['fractions']['nouns'] == 2/7
    assert all(v is None for v in card.grammatical_counts([])['fractions'].values())


@pytest.mark.parametrize('variance,stability,qualified,complete,expected', [
    ([1, 2], [.9, 1.1], False, True, 'estimator unqualified'),
    ([0, 2], [.9, 1.1], True, True, 'no between-person differences'),
    ([-1, 2], [.9, 1.1], True, True, 'no between-person differences'),
    (None, [.9, 1.1], True, True, 'no between-person differences'),
    ([1, 2], [.9, 1.1], True, False, 'invalid uncertainty'),
    ([1, 2], None, True, True, 'invalid uncertainty'),
    ([1, 2], [.50001, 1.3], True, True, 'supports a stable sensitivity'),
    ([1, 2], [-.3, .19999], True, True, 'not stable at the registered band'),
    ([1, 2], [.2, .5], True, True, 'partly stable'),
    ([1, 2], [.5, .5], True, True, 'partly stable'),
    ([1, 2], [.5, .6], True, True, 'inconclusive'),
    ([1, 2], [.1, .2], True, True, 'inconclusive'),
])
def test_variance_gate_precedes_unclipped_stability(variance, stability, qualified, complete, expected):
    assert card.reporting_gate(variance, stability, qualified=qualified, complete_uncertainty=complete).startswith(expected)


@pytest.mark.parametrize('interval', [[2, 1], [0, float('nan')], [True, 1]])
def test_invalid_intervals_refuse(interval):
    with pytest.raises(ValueError): card.reporting_gate(interval, [.6, .7], qualified=True, complete_uncertainty=True)


def test_complete_constructed_execute_and_independent_replay(tmp_path):
    answer = card.execute(tmp_path, {}, {'mode': 'constructed'})
    assert answer['bootstrap_draws'] == 0
    assert not answer['scientific_admission']
    assert card.verify(tmp_path, {}, {'mode': 'constructed'})['verified']
    changed = copy.deepcopy(answer)
    changed['cases']['0.5']['sampling']['stability'] += .01
    (tmp_path / 'RESULT.json').write_text(json.dumps(changed), encoding='utf8')
    with pytest.raises(ValueError): card.verify(tmp_path, {}, {'mode': 'constructed'})


def test_human_outcome_execution_has_no_path(tmp_path):
    with pytest.raises(ValueError): card.execute(tmp_path, {}, {'mode': 'human'})
    with pytest.raises(ValueError): card.execute(tmp_path, {'source': 'human'}, {'mode': 'constructed'})


def test_complete_support_metadata_replay_and_source_mutation(tmp_path, monkeypatch):
    value = manifest(tmp_path)
    for setting in value['settings']:
        setting['checks'][0].update(status='pending', count=None)
        setting['mapping_frozen'] = False
    path = tmp_path / 'support.json'
    path.write_text(json.dumps(value), encoding='utf8')
    monkeypatch.setattr(card, 'ROOT', tmp_path)
    # Explicit base is captured by support_report; use a bounded constructed base.
    original = card.support_report
    monkeypatch.setattr(card, 'support_report', lambda item: original(item, tmp_path))
    inputs = dict(manifest=path.name, manifest_sha256=card.sha(path))
    output = tmp_path / 'output'
    result = card.execute(output, inputs, {'mode': 'support_metadata'})
    assert all(s['status'] == 'source-held' for s in result['settings'])
    assert card.verify(output, inputs, {'mode': 'support_metadata'})['verified']
    (tmp_path / 'constructed-census.json').write_text('{"changed":true}', encoding='utf8')
    with pytest.raises(ValueError): card.verify(output, inputs, {'mode': 'support_metadata'})
