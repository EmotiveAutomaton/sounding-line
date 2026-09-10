"""I04: exact attribution fixtures through the actual likelihood implementation.

DESIGN CHECK: Stage 9 sections 6/I04 and 7.1; LESSONS 3--5; CONTROLS 6--7.
NULL: indistinguishable makers retain prior identity odds and equal forecasts;
rare maker-independent failures supply surprise, not identity information.
ALTERNATIVE: a predictable signature changes identity odds and prospective
probabilities by independently enumerated Bayes calculations. Reversing the
observed choice reverses the odds update. A constant/prior-only answer fails.
Every equality uses an explicit numerical tolerance; any mismatch fails, with
no scientific verdict band. These are exact finite instrument fixtures, not
independent sampled makers, natural-frequency calibration, or human evidence.

Fresh fixture lineage: s9-i04-executed-attribution-v1. No historical cases,
discovery/reserve data, trained model, or mocked likelihood is used. Two maker
programs choose write/revise at known odds; two slots per type, stop chance 1/2,
and one opportunity per earlier work. Current observations condition on execution.
The reference arithmetic below does not call a production likelihood or policy.

The entry extension uses fresh lineage s9-i04-executed-entry-v1. It enumerates
the shared/independent maker joint and every possible next observation before
testing actual acquisition. Noiseless signatures must yield positive expected
future gain; independent or identical makers must yield zero. Observation cost
must reverse buying across that independently calculated gain. These are
construction and null-population controls, not another scientific experiment.
"""
import copy
import math
from fractions import Fraction as F

import pytest

from runners.stage9 import comparison_runtime, familiarity_reader, selection_reader
from runners.stage9.artifact_view import support
from runners.stage9.mark_program import neutral_program
from runners.stage9.program_inference import Budget
from runners.stage9.scoring import individual_quantities


ACTIONS = ('write:s:a', 'write:s:b', 'revise:s:a', 'revise:s:b')


def program(write_probability, *, success=1., purpose_route=False):
    p = neutral_program()
    p['available_types'] = ['write', 'revise']
    p['action_noise'] = p['outcome_noise'] = 0.
    p['stop'] = dict.fromkeys(p['stop'], 0.)
    p['expertise']['success'] = dict.fromkeys(p['expertise']['success'], success)
    p['purpose' if purpose_route else 'history']['write'] = math.log(
        float(write_probability / (1 - write_probability)))
    return p


def work(action, *, view='artifact', topic='current'):
    w = {'context': {'topic': topic, 'audience': 'peer',
         'tools': {'library': True, 'source_access': True}, 'deadline': 'loose',
         'sections': [{'name': 's', 'slots': ['a', 'b']}]},
         'marks': [] if action is None else [action]}
    if view == 'process_record':
        assert action is not None
        kind, section, slot = action.split(':')
        w.update(events=[{'i': 0, 'type': kind, 'section': section, 'slot': slot,
                          'outcome': 'done'}], observed_stop=None)
    return w


def bundle(archive='write:s:a', current='write:s:a', *, view='artifact',
           probabilities=(F(9, 10), F(1, 10)), same_prior=F(1, 2), success=1.):
    now = work(current, view=view)
    evidence = {'version': 's9-visible-artifact-v1', 'view': view,
                'current': now, 'earlier': [work(archive, view=view, topic='prior')],
                'support': support(now, view)}
    return {'evidences': {'q': evidence}, 'maximum_actions': 1,
            'candidates': {key: program(p, success=success)
                           for key, p in zip(('a', 'b'), probabilities)},
            'prior': {'a': .5, 'b': .5}, 'shared_groups': {'a': 'a', 'b': 'b'},
            'same_prior': float(same_prior),
            'population_types': dict.fromkeys(neutral_program()['purpose'], 1/8)}


def action_mass(p, action):
    return (p if action.startswith('write:') else 1-p) / 2


def reference(archive, current, *, same_prior=F(1, 2),
              probabilities=(F(9, 10), F(1, 10))):
    # Enumerate the two latent makers. Independent means an independent draw;
    # it can coincidentally equal the earlier maker, as in the declared model.
    old = [F(1, 2) if archive is None else action_mass(p, archive)/2
           for p in probabilities]
    new = [action_mass(p, current) for p in probabilities]
    old_mass = sum(old)/2
    old_weights = [p/(2*old_mass) for p in old]
    same_mass = sum(w*l for w, l in zip(old_weights, new))
    independent_mass = sum(new)/2
    observation_mass = same_prior*same_mass + (1-same_prior)*independent_mass
    recognition = same_prior*same_mass/observation_mass
    same = [w*l/same_mass for w, l in zip(old_weights, new)]
    different = [l/(2*independent_mass) for l in new]
    return {'recognition': recognition, 'observation_mass': observation_mass,
            'joint_mass': old_mass*observation_mass, 'archive': old_weights,
            'weights': {'assume_same': same, 'assume_different': different,
                        'program_prior': [F(1, 2), F(1, 2)],
                        'recognition_mixture': [recognition*a+(1-recognition)*b
                                               for a, b in zip(same, different)]}}


def future_reference(p, current, offered):
    weights = {a: action_mass(p, a) for a in ACTIONS if a != current}
    total = sum(weights.values())
    return {a: F(1, 2) if a == 'stop' else weights.get(a, 0)/(2*total)
            for a in offered}


@pytest.mark.parametrize('view', ['artifact', 'process_record'])
@pytest.mark.parametrize('current', ['write:s:a', 'revise:s:a'])
def test_actual_signature_likelihood_and_future_match_independent_reference(view, current):
    b = bundle(current=current, view=view)
    out = familiarity_reader.forecast(b, Budget(10000))['queries']['q']
    exact = reference('write:s:a', current)
    assert out['recognition']['same'] == pytest.approx(float(exact['recognition']), abs=1e-13)
    assert out['raw_observation_surprise_nats'] == pytest.approx(
        -math.log(float(exact['observation_mass'])), abs=1e-13)
    assert out['archive_maker_weights'] == pytest.approx({'a': .9, 'b': .1}, abs=1e-13)
    offered = b['evidences']['q']['support']
    futures = [future_reference(p, current, offered) for p in (F(9, 10), F(1, 10))]
    for route, weights in exact['weights'].items():
        expected = {a: float(sum(w*f[a] for w, f in zip(weights, futures))) for a in offered}
        assert out['predictions'][route] == pytest.approx(expected, abs=1e-13)
    # Expected future gain under the conditional generator, not a selected
    # realized target or a reversed surprise statistic.
    posterior = out['predictions']['recognition_mixture']
    prior = out['predictions']['program_prior']
    gain = sum(p*individual_quantities(prior, posterior, a)['individual_uplift']
               for a, p in posterior.items() if p > 0)
    assert gain > 0
    assert (out['recognition']['same'] > .5) == current.startswith('write:')


@pytest.mark.parametrize('same_prior', [F(3, 10), F(1, 2)])
def test_complete_finite_observation_space_recovers_joint_identity_mass(same_prior):
    total = recovered_same = F(0)
    for archive in (None, *ACTIONS):
        for current in ACTIONS:
            exact = reference(archive, current, same_prior=same_prior)
            b = bundle(archive, current, same_prior=same_prior)
            out = familiarity_reader.forecast(b, Budget(10000))['queries']['q']
            assert out['recognition']['same'] == pytest.approx(float(exact['recognition']), abs=1e-13)
            total += exact['joint_mass']
            recovered_same += exact['joint_mass'] * exact['recognition']
    assert total == 1
    assert recovered_same == same_prior


@pytest.mark.parametrize('view', ['artifact', 'process_record'])
def test_no_individuality_preserves_prior_and_equal_future_forecasts(view):
    b = bundle(view=view, probabilities=(F(1, 2), F(1, 2)), same_prior=F(3, 10))
    out = familiarity_reader.forecast(b, Budget(10000))['queries']['q']
    assert out['recognition'] == pytest.approx({'same': .3, 'different': .7}, abs=1e-13)
    for prediction in out['predictions'].values():
        assert prediction == pytest.approx(out['predictions']['program_prior'], abs=1e-13)


def test_rare_erased_failure_is_surprising_but_does_not_identify_maker():
    b = bundle(None, None, success=.99, same_prior=F(3, 10))
    out = familiarity_reader.forecast(b, Budget(10000))['queries']['q']
    assert out['recognition'] == pytest.approx({'same': .3, 'different': .7}, abs=1e-13)
    assert out['raw_observation_surprise_nats'] == pytest.approx(-math.log(.01), abs=1e-12)
    for prediction in out['predictions'].values():
        assert prediction == pytest.approx(out['predictions']['program_prior'], abs=1e-13)


def test_equifinal_purpose_and_habit_preserve_ambiguity_and_relabeling():
    b = bundle(probabilities=(F(9, 10), F(9, 10)), same_prior=F(3, 10))
    b['candidates']['b'] = program(F(9, 10), purpose_route=True)
    assert b['candidates']['a'] != b['candidates']['b']
    out = familiarity_reader.forecast(b, Budget(10000))['queries']['q']
    assert out['archive_maker_weights'] == pytest.approx({'a': .5, 'b': .5}, abs=1e-13)
    assert out['recognition'] == pytest.approx({'same': .3, 'different': .7}, abs=1e-13)
    changed = copy.deepcopy(b)
    changed['candidates'] = {'renamed-b': b['candidates']['b'], 'renamed-a': b['candidates']['a']}
    changed['prior'] = {'renamed-b': .5, 'renamed-a': .5}
    changed['shared_groups'] = {'renamed-b': 'other', 'renamed-a': 'another'}
    second = familiarity_reader.forecast(changed, Budget(10000))['queries']['q']
    assert second['recognition'] == pytest.approx(out['recognition'], abs=1e-13)
    for route in out['predictions']:
        assert second['predictions'][route] == pytest.approx(out['predictions'][route], abs=1e-13)


def test_positive_attribution_runs_inside_actual_capsule_and_refuses_hidden_truth(tmp_path):
    b = bundle()
    result = comparison_runtime.execute(b, operation='maker_familiarity', budget=10000,
                                        root=tmp_path/'positive')
    assert result['accepted']
    exact = reference('write:s:a', 'write:s:a')
    assert result['prediction']['queries']['q']['recognition']['same'] == pytest.approx(
        float(exact['recognition']), abs=1e-13)
    denied = comparison_runtime.execute({**b, 'true_maker': 'a'}, operation='maker_familiarity',
                                        budget=10000, root=tmp_path/'hidden-truth')
    assert not denied['accepted']


def entry_bundle(current='write:s:a', *, view='artifact', probabilities=(F(9, 10), F(1, 10))):
    b = bundle(current=current, view=view, probabilities=probabilities)
    return {'view': view, 'current': b['evidences']['q']['current'],
            'pool': {'o': work('write:s:a', view=view, topic='prior')}, 'purchases': {},
            **{k: b[k] for k in ('candidates', 'prior', 'shared_groups')},
            'strategy': 'future_prediction', 'allow_stop': True, 'cost_nats': 0., 'seed': 1}


def entry_reference(current, offered, *, probabilities=(F(9, 10), F(1, 10)), same_prior=F(1, 2)):
    # Both first actions condition on execution. Enumerate six prior states,
    # retaining coincident independent draws. The next decision includes stop.
    masses = {}
    for c, cp in enumerate(probabilities):
        for a, ap in enumerate(probabilities):
            observed = action_mass(cp, current) * action_mass(ap, 'write:s:a')
            masses['different', c, a] = (1-same_prior) * observed / 4
            if c == a:
                masses['same', c, a] = same_prior * observed / 2
    total = sum(masses.values())
    weights = {h: w/total for h, w in masses.items() if w}
    futures = [future_reference(p, current, offered) for p in probabilities]
    symbols = ('stop', 'write:s:b', 'revise:s:a', 'revise:s:b')
    kernels = [future_reference(p, 'write:s:a', symbols) for p in probabilities]

    def project(ws):
        return {
            'recognition': {r: sum(w for h, w in ws.items() if h[0] == r)
                            for r in ('same', 'different')},
            'current_maker_weights': {k: sum(w for h, w in ws.items() if h[1] == i)
                                      for i, k in enumerate(('a', 'b'))},
            'archive_maker_weights': {k: sum(w for h, w in ws.items() if h[2] == i)
                                      for i, k in enumerate(('a', 'b'))},
            'prediction': {y: sum(w*futures[h[1]][y] for h, w in ws.items()) for y in offered}}

    before = project(weights)
    outcomes = {}
    model_gain = future_gain = observation_entropy = 0.
    for symbol in symbols:
        mass = sum(w*kernels[h[2]][symbol] for h, w in weights.items())
        updated = {h: w*kernels[h[2]][symbol]/mass for h, w in weights.items()}
        after = project(updated)
        outcomes[symbol] = {'mass': mass, 'after': after}
        observation_entropy -= float(mass) * math.log(float(mass))
        model_gain += float(mass) * sum(float(w)*math.log(float(w/weights[h]))
                                       for h, w in updated.items() if w)
        future_gain += float(mass) * sum(float(p)*math.log(float(p/before['prediction'][y]))
                                        for y, p in after['prediction'].items() if p)
    return {'before': before, 'outcomes': outcomes,
            'calculations': {'observation_entropy_nats': observation_entropy,
                             'expected_model_information_nats': model_gain,
                             'expected_future_log_gain_nats': future_gain}}


def purchase_for(preview, symbol, view):
    bought = copy.deepcopy(preview)
    if symbol == 'stop':
        if view == 'process_record':
            bought['observed_stop'] = True
    else:
        bought['marks'].append(symbol)
        bought['marks'].sort()
        if view == 'process_record':
            kind, section, slot = symbol.split(':')
            bought['events'].append({'i': 1, 'type': kind, 'section': section,
                                      'slot': slot, 'outcome': 'done'})
    return bought


def assert_entry_projection(actual, expected):
    for key, values in expected.items():
        assert actual[key] == pytest.approx({k: float(v) for k, v in values.items()}, abs=1e-13)


@pytest.mark.parametrize('view', ['artifact', 'process_record'])
@pytest.mark.parametrize('current', ['write:s:a', 'revise:s:a'])
def test_actual_entry_acquisition_and_every_purchase_match_exact_joint(view, current):
    b = entry_bundle(current, view=view)
    exact = entry_reference(current, support(b['current'], view))
    before = selection_reader.familiarity_forecast(b, Budget(10000))
    assert_entry_projection(before, exact['before'])
    assert before['calculations']['o'] == pytest.approx(exact['calculations'], abs=1e-13)
    gain = exact['calculations']['expected_future_log_gain_nats']
    assert gain > 0 and before['selected'] == 'o' and not before['stop']
    assert before['purchased_observations'] == 0 and not b['purchases']
    assert sum(row['mass'] for row in exact['outcomes'].values()) == 1
    for symbol, row in exact['outcomes'].items():
        changed = copy.deepcopy(b)
        changed['purchases']['o'] = purchase_for(b['pool']['o'], symbol, view)
        after = selection_reader.familiarity_forecast(changed, Budget(10000))
        assert_entry_projection(after, row['after'])
        assert after['purchased_observations'] == 1 and after['stop']
    for multiplier, should_stop in ((.5, False), (2., True)):
        costed = selection_reader.familiarity_forecast({**b, 'cost_nats': multiplier*gain}, Budget(10000))
        assert costed['stop'] is should_stop


@pytest.mark.parametrize('view', ['artifact', 'process_record'])
def test_actual_entry_independent_or_identical_makers_have_no_future_gain(view):
    for probabilities, same_prior in (((F(9, 10), F(1, 10)), F(0)), ((F(1, 2), F(1, 2)), F(1, 2))):
        b = entry_bundle(view=view, probabilities=probabilities)
        exact = entry_reference('write:s:a', support(b['current'], view),
                                probabilities=probabilities, same_prior=same_prior)
        out = selection_reader.forecast(b, Budget(10000), same_prior=float(same_prior))
        assert_entry_projection(out, exact['before'])
        assert out['calculations']['o'] == pytest.approx(exact['calculations'], abs=1e-13)
        assert out['calculations']['o']['expected_future_log_gain_nats'] == 0 and out['stop']
        # Information about an unrelated archive can still change archive beliefs.
        if same_prior == 0:
            assert out['calculations']['o']['expected_model_information_nats'] > 0


def test_actual_positive_entry_capsule_buys_then_updates_without_hidden_truth(tmp_path):
    b = entry_bundle()
    exact = entry_reference('write:s:a', support(b['current'], 'artifact'))
    before = comparison_runtime.execute(b, operation='select_familiar_observation',
                                        budget=10000, root=tmp_path/'before')
    assert before['accepted'] and before['prediction']['selected'] == 'o'
    assert_entry_projection(before['prediction'], exact['before'])
    b['purchases']['o'] = purchase_for(b['pool']['o'], 'revise:s:a', 'artifact')
    after = comparison_runtime.execute(b, operation='select_familiar_observation',
                                       budget=10000, root=tmp_path/'after')
    assert after['accepted'] and after['prediction']['purchased_observations'] == 1
    assert_entry_projection(after['prediction'], exact['outcomes']['revise:s:a']['after'])
    denied = comparison_runtime.execute({**b, 'recognition_target': 'same'},
                                         operation='select_familiar_observation',
                                         budget=10000, root=tmp_path/'truth')
    assert not denied['accepted']
