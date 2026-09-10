"""Selection among permitted observations, separated from their hidden outcomes.

DESIGN CHECK: I05/S01--S04; LESSONS sections 3--5. NULL: pure observation
noise has entropy but zero expected predictive gain; irrelevant latent information
may reduce model uncertainty without improving the target. ALTERNATIVE: a target
discriminator has positive independently calculable gain; costs can reverse buying.
Zero gain and zero regret are valid boundaries, not numerical errors or support.

Environment Design for IRL, arxiv.org/html/2210.14972v3 section 4.1 Eq.1,
motivates maximin Bayesian regret. This module exactly selects from supplied finite
policy-value tables; it does not learn rewards or reproduce the paper's MDPs.
The separate future-information criterion is an explicit local adaptation.
"""
import math
import random

from .program_inference import Budget, distribution, identity, predictive_mixture


def entropy(probabilities):
    distribution(probabilities)
    return -math.fsum(p*math.log(p) for p in probabilities.values() if p)


def divergence(left, right):
    distribution(left)
    distribution(right, left)
    terms = []
    for key, p in left.items():
        if not p:
            continue
        if not right[key]:
            return math.inf
        terms.append(p*math.log(p/right[key]))
    value = math.fsum(terms)
    if value < -1e-12:
        raise ValueError('negative divergence beyond arithmetic tolerance')
    return max(0., value)


def acquisition(prior, observations, future, budget, *, conditional_independence):
    """Exact finite expected gain under O independent of Y conditional on H.

    Callers must supply the model, not outcome labels. The explicit factorization
    is an assumption; correlated repeated evidence must not be fed as fresh data.
    Returns an expected quantity, never realized performance of a selected view.
    """
    if conditional_independence != 'observation_and_future_given_hypothesis':
        raise ValueError('explicit joint-model factorization required')
    distribution(prior)
    if set(observations) != set(prior) or set(future) != set(prior):
        raise ValueError('hypothesis supports differ')
    prediction = predictive_mixture(prior, future)
    outcome_prior = predictive_mixture(prior, observations)
    model_gain, future_gain, outcomes = 0., 0., {}
    for outcome, marginal in outcome_prior.items():
        if not marginal:
            outcomes[outcome] = {'probability': 0., 'posterior': None, 'future': None}
            continue
        budget.charge(len(prior))
        posterior = distribution({h: prior[h]*observations[h][outcome]/marginal for h in prior})
        updated = predictive_mixture(posterior, future)
        hg, yg = divergence(posterior, prior), divergence(updated, prediction)
        model_gain += marginal*hg
        future_gain += marginal*yg
        outcomes[outcome] = {'probability': marginal, 'posterior': posterior, 'future': updated}
    return {'observation_entropy_nats': entropy(outcome_prior),
            'expected_model_information_nats': model_gain,
            'expected_future_log_gain_nats': future_gain, 'outcomes': outcomes,
            'current_future': prediction, 'evaluations': budget.used,
            'factorization': conditional_independence}


def choose_observation(prior, offers, future, objective, budget, *, seen=(), seed=0):
    """Freeze the selection before buying; duplicate content cannot be bought twice.

    Offer values: content_id (canonical evidence identity), likelihoods, and explicit
    cost in target log-score nats. A cost conversion must be frozen by the consumer.
    Stable lexical identity breaks ties; arbitrary identifiers carry no target truth.
    """
    choices = {'entropy': 'observation_entropy_nats', 'model_information': 'expected_model_information_nats',
               'future_prediction': 'expected_future_log_gain_nats', 'random': None}
    if objective not in choices:
        raise ValueError('unknown selection objective')
    if not offers:
        raise ValueError('no declared observation offers')
    costs, calculations, excluded, content = {}, {}, {}, {}
    for name, offer in sorted(offers.items()):
        if set(offer) != {'content_id', 'likelihoods', 'cost_nats'} or not offer['content_id']:
            raise ValueError('invalid observation offer')
        cost = offer['cost_nats']
        if not isinstance(cost, (int, float)) or isinstance(cost, bool) or not math.isfinite(cost) or cost < 0:
            raise ValueError('invalid declared information cost')
        key = offer['content_id']
        signature = identity(offer['likelihoods'])
        if key in content and content[key] != signature:
            raise ValueError('same evidence identity with conflicting likelihood model')
        duplicate = key in content
        content[key] = signature
        if key in seen or duplicate:
            excluded[name] = 'already observed' if key in seen else 'duplicate offered evidence'
            continue
        calculations[name] = acquisition(prior, offer['likelihoods'], future, budget,
            conditional_independence='observation_and_future_given_hypothesis')
        costs[name] = cost
    if not calculations:
        return {'selected': None, 'stop': True, 'reason': 'no new eligible evidence', 'excluded': excluded,
                'scores': {}, 'evaluations': budget.used}
    if objective == 'random':
        # Random is a fixed-budget acquisition rival, not an uncertainty-based stop rule.
        scores = {key: None for key in calculations}
        selected = random.Random(seed).choice(sorted(calculations))
    else:
        scores = {key: value[choices[objective]] - costs[key] for key, value in calculations.items()}
        selected = min(scores, key=lambda k: (-scores[k], k))
        if scores[selected] <= 0:
            selected = None
    return {'selected': selected, 'stop': selected is None, 'objective': objective,
            'scores': scores, 'calculations': calculations, 'excluded': excluded,
            'evaluations': budget.used, 'meaning': 'predicted information before outcome acquisition'}


def maximin_regret(prior, environments, budget):
    """Exact max_T min_policy E_H[max_policy V(H,T)-V(H,T,policy)].

    Policy randomization cannot improve this finite linear objective over its best
    pure policy. This is scoped to the complete supplied policy catalogue; it says
    nothing about omitted policies, learned reward truth, or infinite-horizon MDPs.
    """
    distribution(prior)
    if not environments:
        raise ValueError('empty declared environment set')
    results = {}
    for name, values in sorted(environments.items()):
        if set(values) != set(prior):
            raise ValueError('environment hypothesis support mismatch')
        policies = set(next(iter(values.values())))
        if not policies or any(set(row) != policies for row in values.values()):
            raise ValueError('missing shared policy value')
        if any(not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v)
               for row in values.values() for v in row.values()):
            raise ValueError('invalid policy return')
        budget.charge(len(prior)*len(policies))
        oracle = math.fsum(prior[h]*max(values[h].values()) for h in prior)
        expected = {p: math.fsum(prior[h]*values[h][p] for h in prior) for p in sorted(policies)}
        best = min(expected, key=lambda p: (-expected[p], p))
        regret = oracle-expected[best]
        if regret < -1e-12:
            raise ValueError('negative regret beyond arithmetic tolerance')
        results[name] = {'minimum_bayesian_regret': max(0., regret),
                         'best_shared_policy': best, 'mean_policy_returns': expected,
                         'mean_hypothesis_optimum': oracle}
    selected = min(results, key=lambda k: (-results[k]['minimum_bayesian_regret'], k))
    return {'selected': selected, 'environments': results, 'evaluations': budget.used,
            'meaning': 'exact maximin regret on supplied finite policy/value tables'}
