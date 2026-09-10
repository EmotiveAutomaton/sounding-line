"""Bounded earlier-work observations, followed by a separate unstarted target work.

DESIGN CHECK: M06/X02/X05/X06/X08; LESSONS 3--5, CONTROLS 6--7.
NULL: identical fitted programs retain prior odds and equal forecasts. The sum over
all finite-budget artifacts is one, including early stops and failed actions.
ALTERNATIVE: observed creation and stopping can distinguish fitted makers and help
predict another work. Neither hidden maker truth nor any future outcome is input.
One earlier work, at most three executed actions; incomplete unstopped records,
excess marks, changed target works or supports refuse the whole invocation. Exact
finite observation inference is within an approximate fitted mark model, not the
actual constructor's full historical law or the failed long-artifact estimator.
"""
import math

from .artifact_view import validate, validate_work
from .erased_inference import artifact_work, process_likelihood
from .mark_program import policy, success_probabilities, validate as validate_program
from .program_inference import (distribution, identity, log_probability, logsumexp,
                                normalize_logs, predictive_mixture)


def artifact_observation_likelihood(program, work, budget, maximum_actions):
    validate_work(work, 'artifact'); validate_program(program)
    if type(maximum_actions) is not int or not 1 <= maximum_actions <= 3:
        raise ValueError('declared one-to-three-action observation budget required')
    marks = work['marks']; n = len(marks)
    if n > maximum_actions:
        raise ValueError('more successful marks than observation opportunities')
    complete = (1 << n) - 1; live = {0: 1.}; absorbed = []; cache = {}
    for _ in range(maximum_actions):
        following = {}
        for mask, mass in live.items():
            if mask not in cache:
                current = artifact_work(work, [marks[i] for i in range(n) if mask & (1 << i)])
                budget.charge()
                cache[mask] = (policy(program, current), success_probabilities(program, current))
            p, success = cache[mask]
            if mask == complete:
                absorbed.append(mass * p['stop'])
            failed = math.fsum(p[a] * (1 - success[a]) for a in success)
            following[mask] = following.get(mask, 0.) + mass * failed
            for i, mark in enumerate(marks):
                if not mask & (1 << i):
                    target = mask | (1 << i)
                    following[target] = following.get(target, 0.) + mass * p[mark] * success[mark]
        live = following
    mass = math.fsum([*absorbed, live.get(complete, 0.)])
    if not math.isfinite(mass) or mass < 0 or mass > 1 + 1e-12:
        raise ValueError('invalid bounded observation probability')
    return {'log_mass': log_probability(min(1., mass)), 'exact': True,
            'algorithm': 'finite action-budget subset recurrence with absorbing stop and failure self-loops',
            'maximum_actions': maximum_actions, 'evaluated_visible_states': len(cache)}


def record_observation_likelihood(program, work, budget, maximum_actions):
    validate_work(work, 'process_record')
    if type(maximum_actions) is not int or not 1 <= maximum_actions <= 3:
        raise ValueError('declared one-to-three-action observation budget required')
    n = len(work['events'])
    if (n > maximum_actions or (n < maximum_actions and work['observed_stop'] is not True)
            or (n == maximum_actions and work['observed_stop'] is not None)):
        raise ValueError('record must end at an observed early stop or its declared censoring budget')
    return process_likelihood(program, work, budget)


def forecast(bundle, budget):
    if set(bundle) != {'evidences', 'maximum_actions', 'candidates', 'prior', 'shared_groups'}:
        raise ValueError('undeclared bounded creation inputs')
    evidences, candidates, prior, groups = (bundle[k] for k in ('evidences', 'candidates', 'prior', 'shared_groups'))
    maximum = bundle['maximum_actions']
    if type(maximum) is not int or not 1 <= maximum <= 3:
        raise ValueError('invalid bounded creation observation budget')
    if not isinstance(evidences, dict) or not 1 <= len(evidences) <= 8:
        raise ValueError('explicit bounded creation matrix required')
    if not candidates or len(candidates) > 64:
        raise ValueError('invalid fitted candidate support')
    for program in candidates.values(): validate_program(program)
    distribution(prior, candidates)
    if set(groups) != set(candidates) or any(not isinstance(g, str) or not g for g in groups.values()):
        raise ValueError('incomplete persistent maker grouping')
    members = {g: [c for c in candidates if groups[c] == g] for g in sorted(set(groups.values()))}
    masses = {g: math.fsum(prior[c] for c in cs) for g, cs in members.items()}
    if any(m <= 0 for m in masses.values()): raise ValueError('zero-mass maker group')
    conditional = {c: log_probability(prior[c] / masses[groups[c]]) for c in candidates}
    forecasts, predictions, cache = {}, {}, {}
    current = None
    for name, evidence in evidences.items():
        validate(evidence)
        work = artifact_work(evidence['current'])
        if work['marks'] or len(evidence['earlier']) != 1:
            raise ValueError('one bounded earlier work and an unstarted separate target required')
        if evidence['view'] == 'process_record' and evidence['current']['events']:
            raise ValueError('target observation must be empty')
        key = identity(work)
        if current is not None and key != current:
            raise ValueError('creation conditions must predict the same separate target work')
        current = key
        for c, program in candidates.items():
            if c not in forecasts:
                budget.charge(); forecasts[c] = policy(program, work)
        earlier = evidence['earlier'][0]
        # The source owner verifies distinct actual works. Equal visible empty
        # works are not duplicates of an observation: the earlier work was seen
        # under a finite action budget, while the current work is unstarted.
        likelihoods = {}
        for c, program in candidates.items():
            lk = (c, evidence['view'], identity(earlier))
            if lk not in cache:
                function = record_observation_likelihood if evidence['view'] == 'process_record' else artifact_observation_likelihood
                cache[lk] = function(program, earlier, budget, maximum)
            likelihoods[c] = cache[lk]
        flat, flat_mass = normalize_logs({c: log_probability(prior[c]) + likelihoods[c]['log_mass'] for c in candidates})
        # Purpose may differ between works. Preserve the maker posterior while
        # restoring each maker group's independent target-purpose prior.
        past = {g: log_probability(masses[g]) + logsumexp([
            conditional[c] + likelihoods[c]['log_mass'] for c in cs]) for g, cs in members.items()}
        hierarchical, hierarchical_mass = normalize_logs({c: past[groups[c]] + conditional[c] for c in candidates})
        routes = {'program_prior': prior, 'program_mixture': flat, 'differentiated_maker': hierarchical}
        predictions[name] = {
            'predictions': {route: predictive_mixture(weights, forecasts) for route, weights in routes.items()},
            'weights': {'program_mixture': flat, 'differentiated_maker': hierarchical},
            'log_evidence': {'program_mixture': flat_mass, 'differentiated_maker': hierarchical_mass},
            'likelihood_receipts': likelihoods, 'exact_within_declared_model': True,
            'distinct_earlier_works': 1, 'maximum_actions': maximum}
    return {'queries': predictions, 'evaluations_used': budget.used, 'information_sha256': identity(bundle),
            'assistance': 'independently fitted approximate process; bounded observation horizon supplied equally'}
