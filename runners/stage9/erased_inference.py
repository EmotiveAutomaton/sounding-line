"""Inference over programs from visible marks or separately declared process records.

DESIGN CHECK: M01/M02/M04/M05/X01/X02/X06; LESSONS 3--5. NULL: equivalent
likelihoods preserve odds; copying a work cannot increase dose. ALTERNATIVE: exact
subset summation agrees with independent enumeration, and informative earlier works
change future forecasts. Budget exhaustion refuses rather than returning a prior.

Artifact likelihood sums all orders of the observed successful marks and integrates
any number of self-loop failures before each success. Observation is censored after
the visible successes; it does not assert an unobserved stop. Exact subset summation
is bounded. The long-artifact route averages explicitly uniform permutation proposal
weights, reports uncertainty and is only an approximate conditional inference.
"""
import math
import random

from .artifact_view import action_id, validate, validate_work
from .mark_program import policy, success_probabilities, validate as validate_program
from .program_inference import Budget, distribution, identity, log_probability, logsumexp, normalize_logs, predictive_mixture


def artifact_work(work, marks=None):
    return {'context': work['context'], 'marks': list(work['marks'] if marks is None else sorted(marks))}


def transition(program, work, budget):
    budget.charge()
    forecast = policy(program, work)
    success = success_probabilities(program, work)
    # Sum the geometric series of failures that leave the visible state fixed.
    denominator = forecast['stop'] + math.fsum(forecast[a]*success[a] for a in success)
    if denominator <= 0:
        raise ValueError('candidate can neither stop nor produce a visible mark')
    return {a: forecast[a]*success[a]/denominator for a in success}


def artifact_likelihood(program, work, budget, *, exact_limit=10, permutations=32, seed=0):
    validate_work(work, 'artifact')
    validate_program(program)
    if type(exact_limit) is not int or not 0 <= exact_limit <= 16 or type(permutations) is not int or permutations < 2:
        raise ValueError('invalid erased-history evaluation envelope')
    marks = work['marks']
    n = len(marks)
    if n <= exact_limit:
        weights = {0: 0.}
        for mask in range((1 << n)-1):
            current_log = weights.get(mask, -math.inf)
            if current_log == -math.inf:
                continue
            current = artifact_work(work, [marks[i] for i in range(n) if mask & (1 << i)])
            probabilities = transition(program, current, budget)
            for i, mark in enumerate(marks):
                if not mask & (1 << i):
                    target = mask | (1 << i)
                    proposal = current_log + log_probability(probabilities[mark])
                    weights[target] = logsumexp([weights.get(target, -math.inf), proposal])
        return {'log_mass': weights.get((1 << n)-1, -math.inf), 'exact': True,
                'algorithm': 'subset sum with geometric failure marginalization', 'orders': math.factorial(n),
                'relative_standard_error': 0., 'effective_samples': None}
    rng = random.Random(seed)
    logs = []
    for _ in range(permutations):
        order = list(marks)
        rng.shuffle(order)
        observed = []
        value = math.lgamma(n+1)  # reciprocal of uniform permutation q = 1/n!
        for mark in order:
            probabilities = transition(program, artifact_work(work, observed), budget)
            value += log_probability(probabilities[mark])
            observed.append(mark)
        logs.append(value)
    total = logsumexp(logs)
    if total == -math.inf:
        return {'log_mass': total, 'exact': False, 'algorithm': 'uniform permutation importance mean',
                'orders': permutations, 'relative_standard_error': None, 'effective_samples': 0.}
    scaled = [math.exp(v-total) for v in logs]
    square_sum = math.fsum(v*v for v in scaled)
    relative_se = math.sqrt(max(0., (permutations*square_sum-1)/(permutations-1)))
    return {'log_mass': total-math.log(permutations), 'exact': False,
            'algorithm': 'uniform permutation importance mean', 'orders': permutations,
            'relative_standard_error': relative_se, 'effective_samples': 1/square_sum}


def process_likelihood(program, work, budget):
    validate_work(work, 'process_record')
    validate_program(program)
    marks = []
    value = 0.
    for event in work['events']:
        budget.charge()
        current = artifact_work(work, marks)
        forecast = policy(program, current)
        aid = action_id(event)
        success = success_probabilities(program, current)[aid]
        value += log_probability(forecast[aid]) + log_probability(success if event['outcome'] == 'done' else 1-success)
        if event['outcome'] == 'done':
            marks.append(aid)
    # False/None denotes censoring, not evidence that an unobserved next action
    # continued. Only an actual recorded terminal stop contributes a stop factor.
    if work['observed_stop'] is True:
        budget.charge()
        value += log_probability(policy(program, artifact_work(work))['stop'])
    return {'log_mass': value, 'exact': True, 'algorithm': 'recorded event likelihood',
            'orders': 1, 'relative_standard_error': 0., 'effective_samples': None}


def infer(evidence, candidates, prior, budget, *, exact_limit=10, permutations=32, seed=0, shared_groups=None):
    """Fixed behavior mixture or shared-maker/per-work-purpose finite hierarchy.

    shared_groups maps each joint candidate to its persistent maker factor. A group's
    per-work program prior is its original conditional prior; earlier works update
    group weight after marginalizing their individual purpose. Current purpose stays
    uncertain. Without groups the complete candidate persists across works. These are
    distinct assumptions; field labels do not independently establish a true purpose.
    """
    validate(evidence)
    distribution(prior, candidates)
    if not candidates or len(candidates) > 64:
        raise ValueError('invalid candidate budget')
    for program in candidates.values():
        validate_program(program)
    current_hash = identity(evidence['current'])
    unique = {}
    for work in evidence['earlier']:
        key = identity(work)
        if key != current_hash:
            unique.setdefault(key, work)
    works = [*unique.values(), evidence['current']]
    receipts = {}
    forecasts = {}
    all_exact = True
    for cid, program in candidates.items():
        receipts[cid] = []
        for work in works:
            result = (process_likelihood(program, work, budget) if evidence['view'] == 'process_record' else
                      artifact_likelihood(program, work, budget, exact_limit=exact_limit, permutations=permutations,
                                          seed=str(seed)+':'+identity(work)))
            receipts[cid].append(result)
            all_exact &= result['exact']
        budget.charge()
        forecasts[cid] = policy(program, artifact_work(evidence['current']))
    group_posterior = None
    if shared_groups is None:
        logs = {cid: log_probability(prior[cid])+math.fsum(r['log_mass'] for r in rows)
                for cid, rows in receipts.items()}
    else:
        if set(shared_groups) != set(candidates) or any(not isinstance(v, str) or not v for v in shared_groups.values()):
            raise ValueError('incomplete persistent-maker grouping')
        groups = sorted(set(shared_groups.values()))
        members = {g: [c for c in candidates if shared_groups[c] == g] for g in groups}
        masses = {g: math.fsum(prior[c] for c in members[g]) for g in groups}
        if any(m <= 0 for m in masses.values()):
            raise ValueError('each persistent-maker group requires positive prior mass')
        conditional = {c: log_probability(prior[c]/masses[shared_groups[c]]) for c in candidates}
        earlier = {g: log_probability(masses[g]) + math.fsum(
            logsumexp([conditional[c]+receipts[c][j]['log_mass'] for c in members[g]])
            for j in range(len(works)-1)) for g in groups}
        logs = {c: earlier[shared_groups[c]]+conditional[c]+receipts[c][-1]['log_mass'] for c in candidates}
    posterior, mass = normalize_logs(logs)
    if shared_groups is not None:
        group_posterior = {g: math.fsum(posterior[c] for c in members[g]) for g in groups}
    return {'prediction': predictive_mixture(posterior, forecasts), 'weights': posterior,
            'persistent_weights': group_posterior, 'log_evidence': mass, 'likelihood_receipts': receipts,
            'distinct_earlier_works': len(unique), 'duplicate_earlier_works_removed': len(evidence['earlier'])-len(unique),
            'evaluations_used': budget.used, 'exact_within_declared_model': all_exact,
            'meaning': 'fixed finite set-valued program model; approximation to actual maker process; no unique history claim'}
