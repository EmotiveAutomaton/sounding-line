import copy

import numpy as np
import pytest

from runners.stage9.artifact_view import TYPES, support
from runners.stage9.choice_features import action_features, cheap_adaptation, predict
from runners.stage9.choice_fit import design, fit, objective


def visible(deadline='loose', topic='fixture'):
    work = {'context': {'topic': topic, 'audience': 'peer', 'tools': {'library': True, 'source_access': True},
                        'deadline': deadline, 'sections': [{'name': 's', 'slots': ['one']}]}, 'marks': []}
    return {'version': 's9-visible-artifact-v1', 'view': 'artifact', 'current': work,
            'earlier': [], 'support': support(work, 'artifact')}


def records():
    return [{'unit': 'one', 'evidence': visible('tight'), 'target': 'stop'},
            {'unit': 'two', 'evidence': visible('loose'), 'target': 'write:s:one'}]


def test_conditional_choice_gradient_matches_central_differences():
    matrix, starts, targets, sample_weights, columns = design(records())
    weights = np.linspace(-.2, .2, len(columns))
    loss, gradient = objective(weights, matrix, starts, targets, sample_weights, .03)
    assert np.isfinite(loss)
    delta = 1e-5
    for j in range(len(weights)):
        plus, minus = weights.copy(), weights.copy()
        plus[j] += delta
        minus[j] -= delta
        numerical = (objective(plus, matrix, starts, targets, sample_weights, .03)[0]-
                     objective(minus, matrix, starts, targets, sample_weights, .03)[0])/(2*delta)
        assert gradient[j] == pytest.approx(numerical, abs=2e-9)


def test_planted_context_signal_learned_and_no_topic_or_unit_id_can_leak():
    parameters, receipt = fit(records(), l2=.0001)
    assert receipt['converged']
    for deadline, target in [('tight', 'stop'), ('loose', 'write:s:one')]:
        actual = predict(visible(deadline, topic='new topic'), parameters)
        assert actual[target] > .98
        assert set(actual) == set(visible()['support'])
        assert predict(visible(deadline, topic='another arbitrary topic'), parameters) == actual
    assert all('one' not in k and 'two' not in k for k in parameters['weights'])


def test_unit_weighting_is_invariant_to_exact_repetition_within_unit():
    base = records()
    params, _ = fit(base)
    repeated, _ = fit([base[0], base[0], base[0], base[1]])
    assert predict(visible('tight'), params) == pytest.approx(predict(visible('tight'), repeated), abs=1e-9)


def test_cheap_individual_adaptation_deduplicates_artifacts_and_is_separate():
    current = visible()
    previous = copy.deepcopy(current['current'])
    previous['marks'] = ['write:s:one']
    current['earlier'] = [previous]
    reference = {t: 1/len(TYPES) for t in TYPES}
    adjustment = cheap_adaptation(current, reference)
    assert adjustment['write'] > 0 and adjustment['check'] < 0
    original = action_features(current, 'write:s:one', individual=True)
    current['earlier'] = [previous, previous, previous]
    assert cheap_adaptation(current, reference) == adjustment
    assert action_features(current, 'write:s:one', individual=True) == original
    assert not any('history:' in k for k in action_features(current, 'write:s:one'))


def test_missing_truth_or_failed_optimization_cannot_produce_fitted_parameters():
    bad = records()
    bad[0]['target'] = 'hidden:inventory:only'
    with pytest.raises(ValueError, match='target outside'):
        fit(bad)
    with pytest.raises(ValueError, match='optimization failed'):
        fit(records(), l2=.0001, max_iterations=1)
