import math

import numpy as np
import pytest

from runners.stage9.erased_inference import infer
from runners.stage9.mark_program import neutral_program, policy
from runners.stage9.program_fit import decode, design, encode, fit, fit_library, objective
from runners.stage9.program_inference import Budget
from tests.test_stage9_choice_fit import visible
from tests.test_stage9_erased_inference import A, B


def records():
    return [{'unit': 'one', 'evidence': visible('tight'), 'target': 'stop'},
            {'unit': 'two', 'evidence': visible('loose'), 'target': A}]


def test_noisy_program_objective_matches_executor_and_gradient():
    template = neutral_program()
    template['expertise']['fluency'] = .7
    template['history']['write'] = .2
    data = design(records(), template)
    weights = np.linspace(-.3, .3, len(encode(template)))
    actual_program = decode(weights, template)
    loss, gradient = objective(weights, data, .03)
    expected = -sum(math.log(policy(actual_program, r['evidence']['current'])[r['target']])/2 for r in records())
    expected += .5*.03*float(weights@weights)
    assert loss == pytest.approx(expected, abs=1e-12)
    for j in range(len(weights)):
        positive, negative = weights.copy(), weights.copy()
        positive[j] += 1e-5
        negative[j] -= 1e-5
        numerical = (objective(positive, data, .03)[0]-objective(negative, data, .03)[0])/2e-5
        assert gradient[j] == pytest.approx(numerical, abs=2e-9)


def test_program_fit_learns_planted_rule_through_portable_execution():
    trained, receipt = fit(records(), l2=.0001)
    assert receipt['converged']
    for row in records():
        assert policy(trained, row['evidence']['current'])[row['target']] > .98
    repeated, _ = fit([records()[0]]*3+[records()[1]], l2=.0001)
    assert policy(repeated, visible()['current']) == pytest.approx(policy(trained, visible()['current']), abs=1e-9)


def test_unavailable_and_empty_action_cases_match_exact_executor():
    template = neutral_program()
    template['available_types'] = []
    data = design(records(), template)
    weights = encode(template)
    value, gradient = objective(weights, data, 0.)
    assert value == pytest.approx(-sum(math.log(policy(template, r['evidence']['current'])[r['target']])/2 for r in records()))
    assert np.max(np.abs(gradient)) == 0
    template['action_noise'] = 0
    with pytest.raises(ValueError, match='impossible'):
        objective(encode(template), design(records(), template), 0.)


def test_library_uses_only_training_units_and_executes_inferred_candidates():
    rows = []
    for maker, target in [('training-cohort-one', A), ('training-cohort-two', B)]:
        for i in range(4):
            rows.append({'unit': f'{maker}-{i}', 'evidence': visible(), 'target': target,
                         'maker_group': maker, 'purpose_group': 'training-purpose'})
    units = {r['unit'] for r in rows}
    library, receipt = fit_library(rows, units, minimum_units=4, l2=.001)
    assert receipt['units'] == 8
    assert set(library['shared_groups'].values()) == {'maker0', 'maker1'}
    assert not receipt['training_labels_in_reader_input']
    result = infer(visible(), library['candidates'], library['prior'], Budget(100), shared_groups=library['shared_groups'])
    assert set(result['prediction']) == set(visible()['support'])
    with pytest.raises(ValueError, match='outside permitted training'):
        fit_library(rows, {next(iter(units))}, minimum_units=4)
    with pytest.raises(ValueError, match='insufficient independent'):
        fit_library(rows, units, minimum_units=5)
    with pytest.raises(ValueError, match='optimization failed'):
        fit(records(), l2=.0001, max_iterations=1)
