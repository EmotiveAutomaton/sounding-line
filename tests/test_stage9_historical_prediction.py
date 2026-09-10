"""Original-source replay, independently calculated normalization and complete gates."""
import copy
import math
from collections import Counter
import pytest
from runners.stage9 import historical_prediction as subject
from runners.stage9.common import digest, read, write
from runners.stage9.neural_operations import unit_result, generation_settings
from runners.stage9.generation_policy import GREEDY


@pytest.fixture(scope='module')
def archive():
    return subject.archived_cases()


def fixtures(probability=.5, scope='pilot'):
    cases = []
    for population, n in [('POP', 1 if scope == 'pilot' else 23), ('PU', 1 if scope == 'pilot' else 25)]:
        for domain in subject.original.POP.DOMAINS:
            for i in range(n):
                uid = f'{population}|{domain}|{i}'
                cases.append({'unit': uid, 'lineage': uid, 'population': population,
                              'source_worlds': [{'domain': domain}], 'target': 'a', 'baseline': {'a': .5, 'b': .5}})
    predictions = [{'target': 'a', 'call': {'accepted': True}, 'next_action': {'a': probability, 'b': 1-probability}} for c in cases]
    return cases, predictions


def test_original_archive_and_normalized_baselines(archive):
    cases, source = archive
    assert len(cases) == 96 and len(source['files']) == 195
    assert Counter((c['population'], c['source_worlds'][0]['domain']) for c in cases) == {
        (f, d): n for f, n in [('POP', 23), ('PU', 25)] for d in subject.original.POP.DOMAINS}
    for case in cases:
        evidence = subject.choice_input(case)
        assert set(evidence) == {'prefix', 'options'}
        assert set(evidence['options']) == set(case['baseline']) | {'stop'}
        assert case['target'] is None or case['target'] in case['baseline']
    assert sum(c['target'] is None for c in cases) == 13
    assert generation_settings('historical_prediction') == (32, GREEDY)


def test_preparation_reentry_and_source_tampering(tmp_path, monkeypatch, archive):
    monkeypatch.setattr(subject, 'archived_cases', lambda: copy.deepcopy(archive))
    monkeypatch.setattr(subject, 'ROOT', tmp_path)
    monkeypatch.setattr(subject, 'inside', lambda p: p.resolve())
    monkeypatch.setenv('S9_CELL_IDENTITY', 'd'*64)
    out = tmp_path/'private/historical-prediction-pilots/v1'
    done = subject.prepare(out, 'pilot')
    cases, role, sha = subject.checked_inputs(out, 'pilot')
    assert len(cases) == 4 and role == 'pilot' and done['original_worlds'] == 96
    before = read(out/'COMPLETE.json'); assert subject.prepare(out, 'pilot') == before
    assert not done['scientific_admission'] and not done['confirmation_eligible']
    with pytest.raises(ValueError, match='identity'): subject.checked_inputs(out, 'scientific')
    with pytest.raises(ValueError, match='scope'): subject.prepare(tmp_path/'elsewhere', 'pilot')
    plan = read(out/'WORLD_PLAN.json'); plan['cases'][0]['target'] = 'invented'
    write(out/'WORLD_PLAN.json', plan)
    with pytest.raises(ValueError, match='outputs'): subject.checked_inputs(out, 'pilot')


def test_original_render_and_hidden_future_invariance(archive):
    case = copy.deepcopy(archive[0][0]); evidence = subject.choice_input(case)
    changed = copy.deepcopy(case); changed['source_worlds'][0]['hidden'] = {'future': 'SECRET'}
    changed['baseline'] = {'SECRET': 1.}
    assert subject.choice_input(changed) == evidence
    assert 'SECRET' not in evidence['prefix']
    calls = []
    def call(e, task, index):
        calls.append((e, task, index))
        return {'accepted': True, 'prediction': {'components': [
            {'option_id': key, 'logprob': -3.} for key in e['options']]}}
    case['role'] = 'pilot'
    result = unit_result(case, 'historical_prediction', call)
    assert calls == [(evidence, {'operation': 'choice'}, 'historical-next-action')]
    n = len(case['baseline'])
    assert result['result']['next_action'] == {key: 1/n for key in case['baseline']}
    assert result['case_sha256'] == digest(case)


def raw(stop=-.01):
    return {'accepted': True, 'prediction': {'components': [
        {'option_id': 'b', 'logprob': -1002.}, {'option_id': 'a', 'logprob': -1000.},
        {'option_id': 'stop', 'logprob': stop}]}}


def test_original_action_only_normalization_ignores_stop_weight():
    expected = 1/(1+math.exp(-2))
    actual = subject.action_forecast(raw(), ['a', 'b'])
    assert actual['a'] == pytest.approx(expected) and sum(actual.values()) == 1
    assert actual == subject.action_forecast(raw(-2000.), ['a', 'b'])
    assert subject.action_forecast({'accepted': False}, ['a', 'b']) is None


@pytest.mark.parametrize('mutation', ['missing', 'duplicate', 'nan', 'infinite', 'positive', 'bool', 'extra'])
def test_invalid_components_refuse(mutation):
    result = raw(); rows = result['prediction']['components']
    if mutation == 'missing': rows.pop()
    elif mutation == 'duplicate': rows.append(dict(rows[0]))
    elif mutation == 'extra': rows.append({'option_id': 'new', 'logprob': -1.})
    else: rows[0]['logprob'] = {'nan': math.nan, 'infinite': -math.inf, 'positive': 1., 'bool': True}[mutation]
    with pytest.raises(ValueError, match='components'): subject.action_forecast(result, ['a', 'b'])


@pytest.mark.parametrize('scope', ['pilot', 'scientific'])
def test_equal_forecasts_and_original_threshold(scope):
    result = subject.summarize(*fixtures(scope=scope), scope, draws=100)
    assert result['prediction_criterion_pass'] and result['groups']['all']['historical_clipped']['mean'] == 0
    assert len(result['groups']) == 5 and not result['scientific_admission']
    below = subject.summarize(*fixtures(.5*math.exp(-.051), scope), scope, draws=100)
    assert not below['prediction_criterion_pass']
    assert below['groups']['all']['historical_clipped']['mean'] == pytest.approx(-.051)


def test_original_floor_is_separate_from_proper_score_and_invalid_cohort():
    cases, predictions = fixtures(0.)
    result = subject.summarize(cases, predictions, 'pilot', draws=100)
    assert result['groups']['all']['historical_clipped']['mean'] == pytest.approx(math.log(1e-9)-math.log(.5))
    proper = result['groups']['all']['proper_unfloored']
    assert proper['extended_mean'] == 'negative_infinity' and proper['excluded_targets'] == 0
    predictions[0] = {'target': 'a', 'call': {'accepted': False}, 'next_action': None}
    invalid = subject.summarize(cases, predictions, 'pilot', draws=100)
    assert invalid['assigned_units'] == 4 and not invalid['prediction_criterion_pass']
    assert invalid['groups']['all']['historical_clipped'] is None


def test_terminal_boundaries_stay_assigned_and_unscored():
    cases, predictions = fixtures()
    cases[0]['target'] = predictions[0]['target'] = None
    result = subject.summarize(cases, predictions, 'pilot', draws=100)
    group = result['groups']['all']
    assert group['assigned'] == 4 and group['scored_targets'] == 3 and group['unscored_terminal_boundaries'] == 1
    assert result['prediction_criterion_pass'] and group['historical_clipped']['mean'] == 0
    # A failed terminal call is still an invalid assigned call, never removable.
    predictions[0]['call']['accepted'] = False
    assert not subject.summarize(cases, predictions, 'pilot', draws=100)['prediction_criterion_pass']
    for c, p in zip(cases, predictions): c['target'] = p['target'] = None; p['call']['accepted'] = True
    empty = subject.summarize(cases, predictions, 'pilot', draws=100)
    assert not empty['prediction_criterion_pass'] and empty['groups']['all']['scored_targets'] == 0


def test_original_archived_reader_point_reproduces_with_terminal_rows(archive):
    cases = archive[0]; predictions = []
    for case in cases:
        name = 'FM_adapter-fm_qwen_' + case['lineage'].replace('|', '-') + '.json'
        path = subject.ARCHIVE/'predictions/E03'/name
        original = read(path)
        predictions.append({'target': case['target'], 'call': {'accepted': True},
                            'next_action': original['targets']['next_action']})
    result = subject.summarize(cases, predictions, 'scientific', draws=100)
    expected = read(subject.ARCHIVE/'E03/metrics.json')['readers']['adapter:fm_qwen']['gap']
    assert result['groups']['all']['scored_targets'] == 83
    assert result['groups']['all']['historical_clipped']['mean'] == pytest.approx(expected, abs=1e-12)


@pytest.mark.parametrize('mutation', ['missing', 'duplicate', 'allocation', 'target', 'support', 'normalization', 'scope'])
def test_full_cohort_guards(mutation):
    cases, predictions = fixtures(); scope = 'pilot'
    if mutation == 'missing': predictions.pop()
    elif mutation == 'duplicate': cases[1]['lineage'] = cases[0]['lineage']
    elif mutation == 'allocation': cases[0]['population'] = 'PU'
    elif mutation == 'target': predictions[0]['target'] = 'b'
    elif mutation == 'support': predictions[0]['next_action'] = {'x': 1.}
    elif mutation == 'normalization': predictions[0]['next_action']['a'] = .9
    else: scope = 'scientific'
    with pytest.raises(ValueError): subject.summarize(cases, predictions, scope, draws=100)
