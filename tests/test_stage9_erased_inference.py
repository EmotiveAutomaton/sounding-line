import copy
import math

import pytest

from runners.stage9.artifact_view import support
from runners.stage9.erased_inference import artifact_likelihood, infer, process_likelihood
from runners.stage9.mark_program import neutral_program, policy, success_probabilities
from runners.stage9.program_inference import Budget
from tests.test_stage9_choice_fit import visible

A, B = 'write:s:one', 'check:s:one'


def program(write_share=.5, success=1.):
    p = neutral_program()
    p['available_types'] = ['write', 'check']
    p['purpose']['write'] = math.log(write_share/(1-write_share))
    p['stop'] = {'intercept': math.log(1/3), 'progress': 0., 'deadline': 0., 'self': 0.}
    p['action_noise'] = p['outcome_noise'] = 0.
    p['expertise']['success'] = {k: success for k in p['expertise']['success']}
    return p


def marked(marks, topic='fixture'):
    work = visible(topic=topic)['current']
    work['marks'] = sorted(marks)
    return work


def evidence(current, earlier=()):
    return {'version': 's9-visible-artifact-v1', 'view': 'artifact', 'current': current,
            'earlier': list(earlier), 'support': support(current, 'artifact')}


def recorded(marks, outcomes=None, stop=None):
    outcomes = outcomes or ['done']*len(marks)
    w = marked([a for a, outcome in zip(marks, outcomes) if outcome == 'done'])
    w['events'] = [dict(zip(('type', 'section', 'slot'), a.split(':')), i=i, outcome=outcome)
                   for i, (a, outcome) in enumerate(zip(marks, outcomes))]
    w['observed_stop'] = stop
    return w


def test_exact_erasure_adds_both_histories_with_independent_fraction():
    budget = Budget(100)
    result = artifact_likelihood(program(), marked([A, B]), budget)
    # Two legal orders, each (3/8)*(3/4); do not substitute a sorted path.
    assert math.exp(result['log_mass']) == pytest.approx(9/16)
    assert result['exact'] and result['orders'] == 2
    assert budget.used == 3
    assert math.exp(process_likelihood(program(), recorded([A, B]), Budget(10))['log_mass']) == pytest.approx(9/32)


def test_unobserved_failures_are_marginalized_as_actual_self_loops():
    # At either state: stop=1/4, total success=3/8, self-loop failure=3/8.
    # Summing failures makes first A/B=.3 each, then remaining mark=.6.
    result = artifact_likelihood(program(success=.5), marked([A, B]), Budget(100))
    assert math.exp(result['log_mass']) == pytest.approx(9/25)
    ordered = process_likelihood(program(success=.5), recorded([A, A, B], ['failed', 'done', 'done']), Budget(20))
    assert math.exp(ordered['log_mass']) == pytest.approx((3/16)*(3/16)*(3/8))
    terminal = process_likelihood(program(), recorded([A], stop=True), Budget(20))
    censored = process_likelihood(program(), recorded([A], stop=False), Budget(20))
    assert math.exp(terminal['log_mass']-censored['log_mass']) == pytest.approx(1/4)


def test_uniform_permutation_estimator_has_declared_proposal_and_error():
    result = artifact_likelihood(program(), marked([A, B]), Budget(100), exact_limit=0, permutations=20, seed=83)
    assert not result['exact']
    assert math.exp(result['log_mass']) == pytest.approx(9/16)
    assert result['relative_standard_error'] < 1e-7
    assert result['effective_samples'] == pytest.approx(20)
    # Noncommuting state-dependent action utility makes order matter. Across
    # independently seeded draws, the importance mean has the enumerated mean.
    p = program(.8)
    p['available_types'].append('revise')
    p['expertise']['progress']['write>check'] = 3.
    p['stop']['progress'] = 4.
    exact = artifact_likelihood(p, marked([A, B]), Budget(100))
    survival_after_one = 1/(1+math.exp(math.log(1/3)+.5))
    independent_mass = .5*survival_after_one*math.exp(3/8)/(1+math.exp(3/8)) + .125*survival_after_one*4/5
    assert math.exp(exact['log_mass']) == pytest.approx(independent_mass)
    estimates = [math.exp(artifact_likelihood(p, marked([A, B]), Budget(100), exact_limit=0,
                                             permutations=4, seed=i)['log_mass']) for i in range(400)]
    assert sum(estimates)/len(estimates) == pytest.approx(math.exp(exact['log_mass']), abs=.015)
    assert max(estimates)-min(estimates) > .01


def test_earlier_artifact_changes_future_prediction_without_repeated_confidence():
    candidates = {'a': program(.75), 'b': program(.25)}
    prior = {'a': .5, 'b': .5}
    query = evidence(marked([], 'future'), [marked([A], 'past')])
    result = infer(query, candidates, prior, Budget(100))
    assert result['weights'] == pytest.approx({'a': .75, 'b': .25})
    assert result['prediction'][A] == pytest.approx(15/32)
    repeated = evidence(query['current'], query['earlier']*3)
    again = infer(repeated, candidates, prior, Budget(100))
    assert again['prediction'] == result['prediction']
    assert again['weights'] == result['weights']
    assert again['duplicate_earlier_works_removed'] == 2
    # Compensating utility and habit are behaviorally identical in this context;
    # their separate names cannot manufacture identifiability.
    equivalent = copy.deepcopy(candidates['a'])
    equivalent['purpose']['write'] += 2
    equivalent['history']['write'] -= 2
    same = infer(query, {'x': candidates['a'], 'y': equivalent}, {'x': .3, 'y': .7}, Budget(100))
    assert same['weights'] == pytest.approx({'x': .3, 'y': .7})


def test_hierarchy_marginalizes_each_works_purpose_before_learning_shared_factor():
    candidates = {key: program(p) for key, p in [('g0a', .9), ('g0b', .1), ('g1a', .6), ('g1b', .4)]}
    prior = {key: .25 for key in candidates}
    groups = {key: key[:2] for key in candidates}
    query = evidence(marked([], 'future'), [marked([A], 'past one'), marked([B], 'past two')])
    hierarchical = infer(query, candidates, prior, Budget(100), shared_groups=groups)
    fixed = infer(query, candidates, prior, Budget(100))
    # The per-work marginal is 3/8 for every group. Keeping purpose fixed across
    # works instead favors balanced programs, with masses .09 and .24.
    assert hierarchical['persistent_weights'] == pytest.approx({'g0': .5, 'g1': .5})
    assert fixed['weights']['g1a'] + fixed['weights']['g1b'] == pytest.approx(8/11)


def test_context_belief_availability_and_external_outcomes_remain_distinct():
    p = neutral_program()
    p['action_noise'] = p['outcome_noise'] = 0.
    w = marked([])
    w['context']['tools']['library'] = False
    cid = 'cite:s:ref'
    assert policy(p, w)[cid] == 0
    p['context']['library'] = 'available'
    assert policy(p, w)[cid] > 0
    assert success_probabilities(p, w)[cid] == 0
    p['available_types'].remove('cite')
    assert policy(p, w)[cid] == 0
    p['available_types'].append('cite')
    w['context']['tools']['library'] = True
    p['expertise']['success']['cite'] = .3
    assert success_probabilities(p, w)[cid] == pytest.approx(.3)


def test_public_tool_requirements_match_actual_constructor_in_both_domains():
    from runners.stage9.mark_program import requirements
    from runners.stage9.recipes import POP, sampled_world
    seen = set()
    for domain in POP.DOMAINS:
        for i in range(4):
            world = sampled_world(POP.pop_lid(i, domain, 9989200), 'both')
            for action in world['inventory']:
                assert set(requirements(action['type'])) == set(action['requires'])
                seen.add(action['type'])
    assert seen == set(neutral_program()['available_types'])
    p = neutral_program()
    p['action_noise'] = p['outcome_noise'] = 0.
    for library in (False, True):
        for source in (False, True):
            w = marked([])
            w['context']['tools'] = {'library': library, 'source_access': source}
            forecast = policy(p, w)
            outcomes = success_probabilities(p, w)
            assert (forecast['cite:s:ref'] > 0) == library
            assert (forecast['consult:s:src'] > 0) == source
            assert forecast['probe:s:tech'] > 0
            assert outcomes['cite:s:ref'] == float(library)
            assert outcomes['consult:s:src'] == float(source)
            assert outcomes['probe:s:tech'] == 1.


def test_invalid_or_unrealized_inference_refuses_instead_of_returning_a_prior():
    query = evidence(marked([A, B]))
    with pytest.raises(ValueError, match='budget exhausted'):
        infer(query, {'p': program()}, {'p': 1.}, Budget(1))
    impossible = program()
    impossible['available_types'] = ['write']
    with pytest.raises(ValueError, match='all hypotheses contradict'):
        infer(query, {'p': impossible}, {'p': 1.}, Budget(100))
    bad = program()
    bad['future'] = 'forbidden'
    with pytest.raises(ValueError, match='incomplete mark program'):
        infer(query, {'p': bad}, {'p': 1.}, Budget(100))
