"""Independent finite answers for the borrowed operations, not source benchmarks."""
import copy
import itertools
import math
from fractions import Fraction

import pytest

from runners.stage9.program_inference import (Budget, ParticleSearch, behavioral_mixture,
    inverse_planning, path_costs, planning_policy, predictive_mixture,
    replenish_candidates, script_forecasts, sequence_weights, update_belief)


def alternating(first):
    second = 'b' if first == 'a' else 'a'
    return {'kind': 'finite_script_v1', 'states': ['first', 'second'], 'initial': 'first',
            'support': ['a', 'b'], 'epsilon': .25, 'rules': [],
            'fallbacks': {'first': {'action': first, 'next': 'second'},
                          'second': {'action': second, 'next': 'first'}}}


def graph_fixture():
    return {'states': ['start', 'via', 'goal', 'other'], 'support': ['a', 'b'],
            'edges': {'start': {'a': 'via', 'b': 'other'},
                      'via': {'a': 'goal', 'b': 'start'},
                      'other': {'a': 'start', 'b': 'goal'},
                      'goal': {'a': 'goal', 'b': 'goal'}},
            'observations': {'start': 'start', 'via': 'via', 'other': 'other', 'goal': 'goal'}}


def test_stateful_executable_mixture_has_independent_fraction_answer():
    result = behavioral_mixture({'left': alternating('a'), 'right': alternating('b')},
                                {'left': .5, 'right': .5}, ['x']*3, ['a', 'b', 'a'], 'x', Budget(100))
    expected_weight = Fraction(3, 4)**3 / (Fraction(3, 4)**3+Fraction(1, 4)**3)
    expected_b = expected_weight*Fraction(3, 4)+(1-expected_weight)*Fraction(1, 4)
    assert result['weights']['left'] == pytest.approx(float(expected_weight), abs=1e-14)
    assert result['probs']['b'] == pytest.approx(float(expected_b), abs=1e-14)
    assert len(result['trajectory']) == 4
    assert result['evaluations'] == 14
    # Order and program names are not extra evidence.
    reordered = behavioral_mixture({'right': alternating('b'), 'left': alternating('a')},
                                   {'right': .5, 'left': .5}, ['x']*3, ['a', 'b', 'a'], 'x', Budget(100))
    assert reordered['probs'] == result['probs']


def test_script_uses_observed_previous_action_and_refuses_ambiguous_rule():
    program = alternating('a')
    rule = {'state': 'second', 'symbol': 'y', 'previous': 'b', 'action': 'a', 'next': 'first'}
    program['rules'] = [rule]
    _, query = script_forecasts(program, ['x'], ['b'], 'y', Budget(10))
    assert query['a'] == .75  # Previous action was b despite the script predicting a.
    program['rules'].append(dict(rule))
    with pytest.raises(ValueError, match='ambiguous'):
        script_forecasts(program, ['x'], ['b'], 'y', Budget(10))


def test_equifinal_null_keeps_prior_and_zero_evidence_never_fills_uniform():
    result = sequence_weights({'a': .2, 'b': .8}, [{'a': .1, 'b': .1}]*80, Budget(1000))
    assert result['weights'] == pytest.approx({'a': .2, 'b': .8}, abs=1e-13)
    with pytest.raises(ValueError, match='contradict'):
        sequence_weights({'a': .2, 'b': .8}, [{'a': 0., 'b': 0.}], Budget(10))
    with pytest.raises(ValueError, match='incomplete'):
        sequence_weights({'a': .2, 'b': .8}, [{'a': .3}], Budget(10))
    with pytest.raises(ValueError, match='mismatched'):
        predictive_mixture({'a': .5, 'b': .5}, {'a': {'x': 1.}, 'b': {'y': 1.}})
    with pytest.raises(ValueError, match='budget'):
        behavioral_mixture({'a': alternating('a')}, {'a': 1.}, ['x']*3, ['a']*3, 'x', Budget(2))


def test_replenishment_recovers_missing_candidate_after_contradiction():
    search = ParticleSearch({'a': .5, 'b': .5}, 8, 7, Budget(1000))
    initial = search.update({'a': .9, 'b': .1}, {'a': .999, 'b': .001})
    assert initial['retained_counts'] == {'a': 8}
    final = search.update({'a': 0., 'b': 1.}, {'a': .001, 'b': .999})
    assert final['weights'] == {'a': 0., 'b': 1.}
    assert sum(final['retained_counts'].values()) == 8
    assert len(search.trace) == 2
    with pytest.raises(ValueError, match='unknown proposal density'):
        search.update({'a': .5, 'b': .5}, None)
    with pytest.raises(ValueError, match='lacks target support'):
        search.update({'a': .5, 'b': .5}, {'a': 1., 'b': 0.})


def test_importance_mass_matches_exhaustive_fraction_expectation():
    # Enumerate every possible TWO-draw proposal bank. Exact expectation of the
    # unnormalized mass must be prior*likelihood, independent of proposal skew.
    prior = {'a': Fraction(1, 4), 'b': Fraction(3, 4)}
    likelihood = {'a': Fraction(9, 10), 'b': Fraction(3, 10)}
    proposal = {'a': Fraction(4, 5), 'b': Fraction(1, 5)}
    expectation = 0.
    for draws in itertools.product(('a', 'b'), repeat=2):
        class FixedDraws:
            calls = 0
            def choices(self, labels, weights, k):
                self.calls += 1
                # Resampling cannot change total mass; its composition is irrelevant here.
                return list(draws) if self.calls == 1 else [labels[0]]*k
        search = ParticleSearch({k: float(v) for k, v in prior.items()}, 2, 0, Budget(100))
        search.rng = FixedDraws()
        result = search.update({k: float(v) for k, v in likelihood.items()},
                               {k: float(v) for k, v in proposal.items()})
        expected_mass = sum(prior[k]*likelihood[k]/proposal[k]/2 for k in draws)
        mass = math.exp(result['log_target_mass_estimate'])
        assert mass == pytest.approx(float(expected_mass), abs=1e-14)
        expectation += float(proposal[draws[0]]*proposal[draws[1]])*mass
    assert expectation == pytest.approx(float(sum(prior[k]*likelihood[k] for k in prior)), abs=1e-14)


def test_unknown_density_search_is_explicit_and_duplicate_proposals_add_no_weight():
    rows = [{'a': .9, 'b': .1}, {'a': .01, 'b': .99}]
    result = replenish_candidates(['a'], ['b', 'b'], rows, Budget(100))
    expected_b = Fraction(1, 10)*Fraction(99, 100)/(Fraction(9, 10)*Fraction(1, 100)+Fraction(1, 10)*Fraction(99, 100))
    assert result['weights']['b'] == pytest.approx(float(expected_b), abs=1e-14)
    assert result['meaning'].startswith('heuristic')
    assert result == replenish_candidates(['a'], ['b'], rows, Budget(100))


def test_reverse_search_matches_independent_exhaustive_paths_with_cost_change():
    graph = graph_fixture()
    for costs in ({'a': 1., 'b': 3.}, {'a': 4., 'b': 1.}):
        exact = {}
        # Positive costs imply an optimum is a simple path. Enumerate action strings
        # independently of the tested reverse-graph/Dijkstra implementation.
        for initial in graph['states']:
            possible = [0.] if initial == 'goal' else []
            for length in range(1, len(graph['states'])):
                for actions in itertools.product(graph['support'], repeat=length):
                    state, cost = initial, 0.
                    for action in actions:
                        state = graph['edges'][state][action]
                        cost += costs[action]
                    if state == 'goal':
                        possible.append(cost)
            exact[initial] = min(possible)
        assert path_costs(graph, 'goal', costs, Budget(100)) == exact


def test_same_representation_executes_cost_and_goal_inference():
    graph = graph_fixture()
    hypotheses = {name: {'goal': 'goal', 'costs': costs, 'beta': 1., 'belief': {'start': 1.}}
                  for name, costs in [('a_cheap', {'a': 1., 'b': 3.}), ('b_cheap', {'a': 3., 'b': 1.})]}
    original = copy.deepcopy({'graph': graph, 'hypotheses': hypotheses})
    result = inverse_planning(graph, hypotheses, {'a_cheap': .5, 'b_cheap': .5},
                              ['start'], ['a'], 'via', Budget(1000))
    # First action costs: a_cheap Q(a)=-2,Q(b)=-6; reverse for b_cheap.
    first = 1/(1+math.exp(-4))
    # At via under a_cheap: a=-1,b=-(3+2)=-5. Under b_cheap:
    # a=-3,b=-(1+2)=-3. No state truth hidden in the evaluation function.
    expected = first*first+(1-first)*.5
    assert result['weights']['a_cheap'] == pytest.approx(first, abs=1e-14)
    assert result['probs']['a'] == pytest.approx(expected, abs=1e-14)
    assert {'graph': graph, 'hypotheses': hypotheses} == original
    reversed_result = inverse_planning(graph, hypotheses, {'a_cheap': .5, 'b_cheap': .5},
                                       ['start'], ['b'], 'other', Budget(1000))
    assert reversed_result['weights']['b_cheap'] == pytest.approx(first, abs=1e-14)
    assert reversed_result['representation_sha256'] == result['representation_sha256']


def test_belief_updates_and_impossible_observations_are_not_silent_fills():
    graph = graph_fixture()
    graph['observations']['via'] = 'middle'
    graph['observations']['other'] = 'middle'
    belief = update_belief(graph, {'via': .25, 'other': .75}, 'middle')
    assert belief == {'via': .25, 'other': .75}
    # After a, via reaches goal and other reaches start. Observation resolves belief.
    assert update_belief(graph, belief, 'goal', 'a') == {'goal': 1.}
    with pytest.raises(ValueError, match='contradicts'):
        update_belief(graph, belief, 'unobserved')
    distances = path_costs(graph, 'goal', {'a': 1., 'b': 3.}, Budget(100))
    policy = planning_policy(graph, belief, distances, {'a': 1., 'b': 3.}, 1., Budget(100))
    # Expected action costs: a=.25*1+.75*3=2.5; b=.25*5+.75*3=3.5.
    assert policy['a'] == pytest.approx(1/(1+math.exp(-1)), abs=1e-14)
    hypothesis = {'goal': 'goal', 'costs': {'a': 1., 'b': 3.}, 'beta': 1., 'belief': {'start': 1.}}
    with pytest.raises(ValueError, match='contradict'):
        inverse_planning(graph, {'only': hypothesis}, {'only': 1.}, [], [], 'unknown', Budget(1000))


def test_invalid_representation_and_unreachable_goal_do_not_become_predictions():
    graph = graph_fixture()
    graph['edges']['start']['a'] = 'secret'
    with pytest.raises(ValueError, match='edge'):
        path_costs(graph, 'goal', {'a': 1., 'b': 3.}, Budget(100))
    graph = graph_fixture()
    graph['edges']['via'] = {'a': 'start', 'b': 'start'}
    graph['edges']['other'] = {'a': 'start', 'b': 'start'}
    distances = path_costs(graph, 'goal', {'a': 1., 'b': 3.}, Budget(100))
    with pytest.raises(ValueError, match='contradict'):
        planning_policy(graph, {'start': 1.}, distances, {'a': 1., 'b': 3.}, 1., Budget(100))


@pytest.mark.parametrize('later_action', [False, True])
def test_late_contradiction_does_not_rewrite_prior_action_posterior(later_action):
    graph = graph_fixture()
    graph['observations']['other'] = 'start'
    graph['edges']['start'] = {'a':'via','b':'via'}
    graph['edges']['other'] = {'a':'goal','b':'goal'}
    graph['edges']['via'] = {'a':'goal','b':'goal'}
    # Both candidates see the same initial symbol and choose either action with
    # probability one half. Only the following observation distinguishes them.
    hypotheses = {name: {'goal':'goal','costs':{'a':1.,'b':1.},'beta':1.,'belief':{state:1.}}
                  for name,state in [('compatible','start'),('contradicted','other')]}
    observations = ['start','via'] if later_action else ['start']
    actions = ['a','a'] if later_action else ['a']
    query = 'goal' if later_action else 'via'
    result = inverse_planning(graph,hypotheses,{'compatible':.5,'contradicted':.5},
                              observations,actions,query,Budget(1000))
    assert result['trajectory'][1] == pytest.approx({'compatible':.5,'contradicted':.5})
    assert result['trajectory'][2] == pytest.approx({'compatible':1.,'contradicted':0.})
    assert result['weights'] == pytest.approx({'compatible':1.,'contradicted':0.})
    assert result['probs'] == pytest.approx({'a':.5,'b':.5})
    assert result['impossible'][0]['step'] == 1
