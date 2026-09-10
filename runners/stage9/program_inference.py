"""Finite behavioral inference operations, with no constructor or filesystem access.

DESIGN CHECK: I05/M02/M05; LESSONS sections 3--5 read for this design.
NULL: identical behavioral likelihoods preserve prior odds; missing support, unknown
proposal densities and impossible evidence cannot manufacture an exact posterior.
ALTERNATIVE: independent likelihood tables recover planted finite hypotheses, and
new proposals can recover a hypothesis absent from the initial search. All reported
weights are conditional on an explicit finite model, never human mental-state truth.

Operation attributions (adaptations, not paper-level reproductions):
ROTE, arxiv.org/html/2510.01272v1 sections 3.1--3.2 and Algorithm 1: executable
stateful behavioral scripts, explicit action noise, likelihood-weighted mixtures.
Open-ended SIPS, arxiv.org/html/2407.16770v1 Algorithm 1: propose, replay full
evidence, reweight old particles, merge/resample/coalesce. Here equal estimator
bank weighting is explicit; finite particles remain an approximation.
LIRAS, arxiv.org/html/2506.16755v1 Appendix D: separate symbolic representation
from belief update, shortest-path action values and sequential inverse inference.
This finite graph DSL substitutes for PDDL synthesis, not for its benchmark.
"""
import copy
import hashlib
import heapq
import json
import math
import random


def identity(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def distribution(values, support=None):
    if (not isinstance(values, dict) or not values or
            any(not isinstance(k, str) or not isinstance(v, (int, float)) or
                isinstance(v, bool) or not math.isfinite(v) or v < 0 for k, v in values.items()) or
            abs(math.fsum(values.values()) - 1) > 1e-10 or
            (support is not None and set(values) != set(support))):
        raise ValueError('invalid or mismatched finite distribution')
    return values


def log_probability(value):
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError('invalid likelihood')
    return math.log(value) if value else -math.inf


def logsumexp(values):
    if not values or any(math.isnan(v) or v == math.inf for v in values):
        raise ValueError('invalid log weights')
    peak = max(values)
    return peak if peak == -math.inf else peak + math.log(math.fsum(math.exp(v-peak) for v in values))


def normalize_logs(values):
    total = logsumexp(list(values.values()))
    if total == -math.inf:
        raise ValueError('all hypotheses contradict evidence')
    return {k: math.exp(v-total) for k, v in values.items()}, total


class Budget:
    """Count actual evaluations; attempted calls consume the same explicit budget."""
    def __init__(self, limit):
        if type(limit) is not int or limit < 1:
            raise ValueError('positive evaluation budget required')
        self.limit, self.used = limit, 0

    def charge(self, count=1):
        if type(count) is not int or count < 0 or self.used + count > self.limit:
            raise ValueError('evaluation budget exhausted')
        self.used += count


def sequence_weights(prior, likelihood_rows, budget):
    """Exact Bayes only within the supplied fixed finite catalogue and likelihoods."""
    distribution(prior)
    weights = {k: log_probability(v) for k, v in prior.items()}
    path = [dict(prior)]
    for row in likelihood_rows:
        if set(row) != set(prior):
            raise ValueError('incomplete candidate likelihood row')
        budget.charge(len(prior))
        weights = {k: weights[k] + log_probability(row[k]) for k in weights}
        probabilities, _ = normalize_logs(weights)
        path.append(probabilities)
    return {'weights': path[-1], 'trajectory': path,
            'log_evidence': logsumexp(list(weights.values())),
            'meaning': 'exact conditional on supplied finite catalogue and likelihood model'}


def predictive_mixture(weights, forecasts):
    distribution(weights)
    if set(weights) != set(forecasts):
        raise ValueError('missing candidate execution')
    support = set(next(iter(forecasts.values())))
    for forecast in forecasts.values():
        distribution(forecast, support)
    return distribution({a: math.fsum(weights[k]*forecasts[k][a] for k in weights)
                         for a in sorted(support)}, support)


def noisy_action(action, support, epsilon):
    if not support or len(set(support)) != len(support) or action not in support or not 0 <= epsilon < 1:
        raise ValueError('invalid deterministic action or noise model')
    if len(support) == 1:
        return {action: 1.}
    return {a: 1-epsilon if a == action else epsilon/(len(support)-1) for a in support}


def script_forecasts(program, observations, observed_actions, query, budget):
    """Execute a declarative finite-state script; never eval generated Python.

    A rule reads current observed symbol and previous *observed* action. Its next
    internal state carries to the next step. Query execution never updates history.
    Every state has a declared fallback; malformed scripts are invalid, not uniform.
    """
    if set(program) != {'kind', 'states', 'initial', 'support', 'epsilon', 'rules', 'fallbacks'} or program['kind'] != 'finite_script_v1':
        raise ValueError('invalid script schema')
    states, support = program['states'], program['support']
    if (not states or len(set(states)) != len(states) or program['initial'] not in states or
            set(program['fallbacks']) != set(states) or len(observations) != len(observed_actions) or
            any(a not in support for a in observed_actions)):
        raise ValueError('invalid script history or state closure')
    for rule in program['rules']:
        if (set(rule) != {'state', 'symbol', 'previous', 'action', 'next'} or rule['state'] not in states or
                rule['action'] not in support or rule['next'] not in states or
                (rule['previous'] is not None and rule['previous'] not in support)):
            raise ValueError('invalid script rule')
    for rule in program['fallbacks'].values():
        if set(rule) != {'action', 'next'} or rule['action'] not in support or rule['next'] not in states:
            raise ValueError('invalid script fallback')
    state, previous, forecasts = program['initial'], None, []
    for index, symbol in enumerate([*observations, query]):
        budget.charge()
        matches = [r for r in program['rules'] if r['state'] == state and r['symbol'] == symbol and r['previous'] == previous]
        if len(matches) > 1:
            raise ValueError('ambiguous script rule')
        rule = matches[0] if matches else program['fallbacks'][state]
        forecasts.append(noisy_action(rule['action'], support, program['epsilon']))
        if index < len(observed_actions):
            state, previous = rule['next'], observed_actions[index]
    return forecasts[:-1], forecasts[-1]


def behavioral_mixture(programs, prior, observations, actions, query, budget):
    """ROTE defining execution/likelihood operation on supplied script proposals.

    Proposal generation is a separate upstream operation. A declared finite prior
    is not an LLM proposal probability. No top-k truncation is hidden here.
    """
    if set(programs) != set(prior):
        raise ValueError('program/prior catalogue differs')
    forecasts, likelihoods = {}, {k: [] for k in programs}
    for name, program in programs.items():
        history, forecasts[name] = script_forecasts(program, observations, actions, query, budget)
        likelihoods[name] = [p[a] for p, a in zip(history, actions)]
    posterior = sequence_weights(prior, [{k: likelihoods[k][i] for k in programs}
                                         for i in range(len(actions))], budget)
    return {**posterior, 'probs': predictive_mixture(posterior['weights'], forecasts),
            'representation_sha256': identity(programs), 'evaluations': budget.used}


class ParticleSearch:
    """Known-density replenishment with unbiased unnormalized estimator banks.

    The retained bank estimates prior times all observed likelihoods. Each new
    bank estimates the same target by prior*likelihood/(N*q). Equal bank mixing
    avoids treating normalized old weights as comparable to raw new weights.
    Multinomial resampling preserves total unnormalized mass in expectation.
    Output normalized weights are a finite-particle approximation, never exact.
    """
    def __init__(self, prior, count, seed, budget):
        distribution(prior)
        if type(count) is not int or count < 1:
            raise ValueError('positive particle count required')
        self.prior, self.count = dict(prior), count
        self.rng, self.budget = random.Random(seed), budget
        self.bank, self.rows, self.trace = {}, [], []

    def update(self, likelihood_row, proposal):
        if proposal is None:
            raise ValueError('unknown proposal density: exact importance weights forbidden')
        distribution(proposal, self.prior)
        if any(self.prior[k] > 0 and proposal[k] == 0 for k in self.prior):
            raise ValueError('proposal lacks target support')
        if set(likelihood_row) != set(self.prior):
            raise ValueError('incomplete likelihood support')
        for p in likelihood_row.values():
            log_probability(p)
        self.rows.append(dict(likelihood_row))
        old = {}
        for key, value in self.bank.items():
            self.budget.charge()
            old[key] = value + log_probability(likelihood_row[key])
        labels = sorted(proposal)
        draws = self.rng.choices(labels, [proposal[k] for k in labels], k=self.count)
        new = {}
        for key in draws:
            self.budget.charge(len(self.rows))
            value = (log_probability(self.prior[key]) + sum(log_probability(row[key]) for row in self.rows)
                     - math.log(proposal[key]) - math.log(self.count))
            new[key] = logsumexp([new.get(key, -math.inf), value])
        # Preserve the scale of one target estimator across successive arrivals.
        mixed = {k: logsumexp([old.get(k, -math.inf), new.get(k, -math.inf)]) - (math.log(2) if old else 0.)
                 for k in set(old) | set(new)}
        normalized, total = normalize_logs(mixed)
        labels = sorted(normalized)
        kept = self.rng.choices(labels, [normalized[k] for k in labels], k=self.count)
        counts = {k: kept.count(k) for k in set(kept)}
        self.bank = {k: total + math.log(n/self.count) for k, n in counts.items()}
        result = {'weights': {k: counts.get(k, 0)/self.count for k in self.prior},
                  'new_draws': draws, 'retained_counts': counts, 'log_target_mass_estimate': total,
                  'meaning': 'finite-particle approximation; known normalized proposal density',
                  'evaluations': self.budget.used}
        self.trace.append(copy.deepcopy(result))
        return result


def replenish_candidates(old, proposed, all_likelihoods, budget):
    """Unknown-density alternative: explicit heuristic search, not SIPS weighting.

    Unique candidates receive a fresh uniform finite-set prior and the full history
    is replayed once. Duplicate proposals do not multiply confidence. The posterior
    within this data-selected set is NOT an exact posterior over the search space.
    """
    candidates = sorted(set(old) | set(proposed))
    if not candidates:
        raise ValueError('empty proposal search')
    prior = {k: 1/len(candidates) for k in candidates}
    rows = [{k: row[k] for k in candidates} for row in all_likelihoods]
    result = sequence_weights(prior, rows, budget)
    result['meaning'] = 'heuristic data-selected finite-set reweighting; proposal densities unknown'
    result['candidates'] = candidates
    return result


def validate_graph(graph):
    if set(graph) != {'states', 'support', 'edges', 'observations'}:
        raise ValueError('invalid finite graph schema')
    states, support = graph['states'], graph['support']
    if (not states or len(states) != len(set(states)) or not support or len(support) != len(set(support)) or
            set(graph['observations']) != set(states) or set(graph['edges']) != set(states)):
        raise ValueError('incomplete graph closure')
    for state, edges in graph['edges'].items():
        if not set(edges) <= set(support) or any(target not in states for target in edges.values()):
            raise ValueError('invalid graph edge')
    return graph


def path_costs(graph, goal, costs, budget):
    """Reverse Dijkstra, separate from the fixture's exhaustive path enumeration."""
    validate_graph(graph)
    if goal not in graph['states'] or set(costs) != set(graph['support']) or any(
            not isinstance(c, (int, float)) or isinstance(c, bool) or not math.isfinite(c) or c <= 0 for c in costs.values()):
        raise ValueError('invalid goal or positive action costs')
    reverse = {s: [] for s in graph['states']}
    for state, edges in graph['edges'].items():
        for action, target in edges.items():
            reverse[target].append((state, costs[action]))
    distances = {s: math.inf for s in graph['states']}
    distances[goal] = 0.
    heap = [(0., goal)]
    while heap:
        distance, state = heapq.heappop(heap)
        if distance != distances[state]:
            continue
        for origin, cost in reverse[state]:
            budget.charge()
            candidate = distance + cost
            if candidate < distances[origin]:
                distances[origin] = candidate
                heapq.heappush(heap, (candidate, origin))
    return distances


def update_belief(graph, belief, observation, previous_action=None):
    distribution(belief)
    if not set(belief) <= set(graph['states']):
        raise ValueError('belief state outside graph')
    moved = {}
    for state, mass in belief.items():
        if not mass:
            continue
        if previous_action is None:
            target = state
        elif previous_action not in graph['edges'][state]:
            raise ValueError('observed action impossible under candidate belief')
        else:
            target = graph['edges'][state][previous_action]
        if graph['observations'][target] == observation:
            moved[target] = moved.get(target, 0.) + mass
    total = math.fsum(moved.values())
    if not total:
        raise ValueError('observation contradicts candidate belief')
    return {k: v/total for k, v in moved.items()}


def planning_policy(graph, belief, distances, costs, beta, budget):
    distribution(belief)
    if not isinstance(beta, (int, float)) or isinstance(beta, bool) or not math.isfinite(beta) or beta <= 0:
        raise ValueError('invalid rationality parameter')
    logweights = {}
    for action in graph['support']:
        budget.charge()
        expected = 0.
        for state, weight in belief.items():
            if not weight:
                continue
            target = graph['edges'][state].get(action)
            if target is None:
                expected = math.inf
                break
            expected += weight * (costs[action]+distances[target])
        logweights[action] = -beta * expected
    probabilities, _ = normalize_logs(logweights)
    return probabilities


def inverse_planning(graph, hypotheses, prior, observations, actions, query, budget):
    """LIRAS/SIAM operation adaptation on an explicitly supplied finite graph.

    Each hypothesis has goal, costs, beta and initial belief. Reward/goal-selection
    priors, if needed, must be supplied as actual normalized prior, never guessed.
    Artifact-only use needs its own observation projection; state symbols are
    process evidence and are never silently supplied to an artifact-only reader.
    """
    validate_graph(graph)
    distribution(prior, hypotheses)
    if len(observations) != len(actions):
        raise ValueError('unaligned observed sequence')
    # Once a candidate is eliminated, later rows are neutral. Earlier rows must
    # retain the information that was actually available at their boundary.
    rows = [{k: 1. for k in hypotheses} for _ in actions]
    forecasts = {}
    impossible = []
    for name, hypothesis in hypotheses.items():
        if set(hypothesis) != {'goal', 'costs', 'beta', 'belief'}:
            raise ValueError('incomplete finite planning hypothesis')
        distances = path_costs(graph, hypothesis['goal'], hypothesis['costs'], budget)
        belief, previous = hypothesis['belief'], None
        for i, observation in enumerate([*observations, query]):
            try:
                belief = update_belief(graph, belief, observation, previous)
            except ValueError as error:
                if str(error) not in ('observed action impossible under candidate belief', 'observation contradicts candidate belief'):
                    raise
                impossible.append({'hypothesis': name, 'step': i, 'reason': str(error)})
                # Eliminate at this boundary, never retroactively. A contradiction
                # at the query is represented in final_validity below.
                if i < len(actions):
                    rows[i][name] = 0.
                break
            forecast = planning_policy(graph, belief, distances, hypothesis['costs'], hypothesis['beta'], budget)
            if i < len(actions):
                if actions[i] not in forecast:
                    raise ValueError('observed action outside common support')
                rows[i][name] = forecast[actions[i]]
                previous = actions[i]
            else:
                forecasts[name] = forecast
    # Query observation is permitted current evidence, so its contradictions also
    # eliminate hypotheses even with no prior actions. Observation likelihoods are
    # otherwise conditioned upon, not assigned arbitrary generative probabilities.
    final_validity = {k: float(k in forecasts) for k in hypotheses}
    posterior = sequence_weights(prior, [*rows, final_validity], budget)
    active = {k: p for k, p in posterior['weights'].items() if k in forecasts}
    prediction = predictive_mixture(active, forecasts)
    return {**posterior, 'probs': prediction, 'impossible': impossible,
            'representation_sha256': identity({'graph': graph, 'hypotheses': hypotheses}),
            'evaluations': budget.used,
            'meaning': 'finite inverse policy inference conditioned on permitted state observations; no benchmark reproduction'}
