from fractions import Fraction

import pytest

from runners.stage9.inference_runtime import execute
from tests.test_stage9_program_inference import alternating, graph_fixture


def test_real_inference_capsule_executes_script_mixture_and_rejects_budget(tmp_path):
    evidence = {'programs': {'a': alternating('a'), 'b': alternating('b')},
                'prior': {'a': .5, 'b': .5}, 'observations': ['x']*3,
                'actions': ['a', 'b', 'a'], 'query': 'x'}
    result = execute(evidence, 'behavioral_mixture', root=tmp_path / 'caps')
    assert result['accepted'], result
    expected = Fraction(27, 28)*Fraction(3, 4)+Fraction(1, 28)*Fraction(1, 4)
    assert result['prediction']['probs']['b'] == pytest.approx(float(expected), abs=1e-14)
    refused = execute(evidence, 'behavioral_mixture', budget=1, root=tmp_path / 'caps')
    assert not refused['accepted'] and refused['prediction'] is None
    assert 'budget exhausted' in refused['error']['traceback']


def test_real_inference_capsule_runs_symbolic_execution_with_closed_inputs(tmp_path):
    evidence = {'graph': graph_fixture(), 'hypotheses': {
        'cheap_a': {'goal': 'goal', 'costs': {'a': 1., 'b': 3.}, 'beta': 1., 'belief': {'start': 1.}}},
        'prior': {'cheap_a': 1.}, 'observations': [], 'actions': [], 'query': 'start'}
    result = execute(evidence, 'inverse_planning', root=tmp_path / 'caps')
    assert result['accepted'], result
    assert result['prediction']['probs']['a'] > .98
    evidence['hidden_truth'] = 'must not be admitted'
    refused = execute(evidence, 'inverse_planning', root=tmp_path / 'caps')
    assert not refused['accepted'] and refused['prediction'] is None
    assert 'undeclared' in refused['error']['traceback']


def test_actual_inference_capsule_refuses_existing_external_truth(tmp_path):
    hidden = tmp_path / 'hidden.json'
    hidden.write_text('keep private')
    result = execute(None, task={'probe': True, 'forbidden_paths': [str(hidden)], 'other_port': 65534},
                     root=tmp_path / 'caps')
    assert result['accepted'], result
    assert hidden.read_text() == 'keep private'
