"""Separate proper scores, uncertainty, and claim dispositions.

DESIGN CHECK: LESSONS sections 3 and 5; CONTROLS section 6; Stage 9 section 7.
NULL: identical predictions give zero paired gain, including predictable/noisy cases.
ALTERNATIVE: an informative individual predictor improves its held-out proper score.
gates: invalid distributions/empty groups fail before aggregation. Exhaustive bands:
invalid, descriptive, practical equivalence, inconclusive, counterevidence, or support
candidate. Confirmed status is assigned only by the independent frozen-confirmation path.
"""
from __future__ import annotations

from collections import defaultdict
import math
from statistics import NormalDist

from runners.stage9.common import distribution

DISPOSITIONS = {
    "IMPLEMENTATION INVALID": "INSTRUMENT_FAILED",
    "INCONCLUSIVE": "INCONCLUSIVE",
    "PRACTICALLY SMALL": "VALID_NULL",
    "COUNTEREVIDENCE": "COUNTEREVIDENCE",
    "SUPPORT CANDIDATE": "SUPPORT_CANDIDATE",
    "CONFIRMED WITHIN SCOPE": "SUPPORT_CANDIDATE",
    "DESCRIPTIVE": "DESCRIPTIVE",
    "NOT RUN WITH REASON": "NOT_RUN",
}
# Confirmed claims additionally require warrant=CONFIRMED_MODEL_BOUNDED and a valid
# frozen confirmation receipt. An outcome enum alone can never grant confirmation.


def log_score(probabilities, truth):
    distribution(probabilities)
    if truth not in probabilities:
        raise ValueError("target missing from declared support")
    # Log score applies to the actual normalized forecast. A floor applied only
    # at the realized label is not a proper probability score. Any smoothing
    # belongs in the declared forecast for ALL options, before outcome access.
    return math.log(probabilities[truth]) if probabilities[truth] > 0 else -math.inf


def individual_quantities(population, individual, truth):
    if set(population) != set(individual):
        raise ValueError('paired forecasts require identical declared support')
    left, right = log_score(individual, truth), log_score(population, truth)
    difference = None if left == right == -math.inf else left-right
    return score_json({"raw_surprise": -right,
                       "individual_log_score": left,
                       "population_log_score": right,
                       "individual_uplift": difference,
                       "uplift_status": 'undefined_both_zero' if difference is None else
                           'finite' if math.isfinite(difference) else 'infinite'})


def score_json(value):
    """JSON-safe exact extended scores. No outcome-dependent flooring or dropping.

    Finite legacy records keep their numeric values. Infinities get explicit tagged
    objects; NaN is always an unhandled arithmetic defect. Undefined log differences
    must be represented deliberately as None with a reason by their producer.
    """
    if isinstance(value, float):
        if math.isnan(value):
            raise ValueError('NaN score must be resolved explicitly, never serialized')
        if math.isinf(value):
            return {'extended_real': 'positive_infinity' if value > 0 else 'negative_infinity'}
        return value
    if isinstance(value, dict):
        return {k:score_json(v) for k,v in value.items()}
    if isinstance(value, (tuple,list)):
        return [score_json(v) for v in value]
    return value


def paired_extended(rows, value='difference', unit='unit', **kwargs):
    """Retain every target and refuse finite inference on nonfinite contrasts.

    +/- infinity is a valid realized log-score failure of one forecast. None means
    both forecasts assigned zero to the recorded target. Neither licenses a finite
    bootstrap, normal-power calculation, or promotion. No finite-only subset is used.
    """
    rows = list(rows)
    if not rows:
        raise ValueError('no paired attempts')
    counts = defaultdict(int)
    for row in rows:
        x = row[value]
        if x is None:
            counts['undefined_both_zero'] += 1
        elif not isinstance(x,(int,float)) or isinstance(x,bool) or math.isnan(x):
            raise ValueError('invalid paired target')
        elif math.isinf(x):
            counts['positive_infinity' if x>0 else 'negative_infinity'] += 1
        else:
            counts['finite'] += 1
    if counts['finite'] == len(rows):
        return paired_interval(rows,value=value,unit=unit,**kwargs) | {'finite_estimate':True}
    status = ('undefined' if counts['undefined_both_zero'] or
              (counts['positive_infinity'] and counts['negative_infinity']) else
              'positive_infinity' if counts['positive_infinity'] else 'negative_infinity')
    return {'mean':None,'ci':None,'finite_estimate':False,'extended_mean':status,
            'n_targets':len(rows),'n_units':len({str(r[unit]) for r in rows}),
            'score_counts':dict(counts),'excluded_targets':0,
            'uncertainty':'finite cluster interval and normal-power calculation undefined; all targets retained',
            'promotion_eligible':False,'disposition':'DESCRIPTIVE'}


def paired_log_comparison(rows, *, left='individual', right='population', unit='unit', **kwargs):
    """Evaluator API for frozen complete forecasts on a common support and target."""
    scored = []
    for row in rows:
        if set(row[left]) != set(row[right]):
            raise ValueError('paired forecasts require identical declared support')
        a,b = log_score(row[left],row['truth']),log_score(row[right],row['truth'])
        scored.append(row | {'difference':None if a == b == -math.inf else a-b})
    return paired_extended(scored,unit=unit,**kwargs)


def brier(probabilities, selections):
    if len(probabilities) != len(selections) or not selections:
        raise ValueError("aligned nonempty Bernoulli opportunities required")
    if any(not math.isfinite(p) or p < 0 or p > 1 for p in probabilities) or any(y not in (0, 1) for y in selections):
        raise ValueError("invalid Bernoulli probability or outcome")
    return math.fsum((p - y)**2 for p, y in zip(probabilities, selections)) / len(selections)


def paired_interval(rows, value="difference", unit="unit", second_cluster=None, seed=9011, draws=4000):
    """Average targets within independent units FIRST, then paired cluster bootstrap.

    For crossed person/stimulus data, independent multiplicity weights on both groups
    implement a pigeonhole bootstrap, retaining equal weight for each sampled person.
    Stimuli are averaged within people before people are averaged. Counts and the
    small-number-of-stimuli limitation are retained explicitly.
    """
    import numpy as np
    if not isinstance(draws, int) or draws < 100:
        raise ValueError("at least 100 resamples required")
    rows = list(rows)
    cells = defaultdict(list)
    for row in rows:
        x = row[value]
        if not isinstance(x, (int, float)) or isinstance(x, bool) or not math.isfinite(x):
            raise ValueError("invalid paired target")
        key = (str(row[unit]), str(row[second_cluster]) if second_cluster else "")
        cells[key].append(float(x))
    if not cells:
        raise ValueError("no independent units")
    keys = sorted(cells)
    values = np.array([math.fsum(cells[k]) / len(cells[k]) for k in keys])
    first = sorted({k[0] for k in keys})
    second = sorted({k[1] for k in keys})
    ai = np.array([first.index(k[0]) for k in keys])
    unit_values = np.array([values[ai == i].mean() for i in range(len(first))])
    estimate = float(unit_values.mean())
    receipt = {"mean": estimate, "n_units": len(first), "n_targets": len(rows), "n_cells": len(cells),
               "second_groups": len(second) if second_cluster else None,
               "seed": seed, "draws": draws, "method": "paired cluster percentile bootstrap" if not second_cluster else "two-way pigeonhole percentile bootstrap"}
    if len(first) < 2 or (second_cluster and len(second) < 2):
        return {**receipt, "ci": None, "uncertainty": "insufficient independent groups"}
    rng = np.random.default_rng(seed)
    samples = []
    if second_cluster:
        bi = np.array([second.index(k[1]) for k in keys])
        for _ in range(draws):
            a = rng.multinomial(len(first), np.full(len(first), 1 / len(first)))
            b = rng.multinomial(len(second), np.full(len(second), 1 / len(second)))
            # Unequal observed stimulus counts must not give a person more weight.
            stimulus_weights = b[bi]
            denominators = np.bincount(ai, weights=stimulus_weights, minlength=len(first))
            numerators = np.bincount(ai, weights=stimulus_weights * values, minlength=len(first))
            observed = (denominators > 0) & (a > 0)
            if observed.any():
                samples.append(float(np.average(numerators[observed] / denominators[observed], weights=a[observed])))
    else:
        # With one cluster each key is exactly one independent unit.
        for _ in range(draws):
            samples.append(float(values[rng.integers(0, len(values), len(values))].mean()))
    if len(samples) < 0.95 * draws:
        return {**receipt, "ci": None, "uncertainty": "too many empty crossed-cluster resamples"}
    return {**receipt, "ci": [float(v) for v in np.quantile(samples, [0.025, 0.975])],
            "standard_deviation": float(unit_values.std(ddof=1)), "effective_resamples": len(samples),
            "estimand": "equal independent-unit mean of within-unit stimulus means"}


def classify(result, threshold=0.05, descriptive=False, valid=True):
    if not math.isfinite(threshold) or threshold <= 0:
        raise ValueError("positive predeclared practical threshold required")
    if not valid:
        return "IMPLEMENTATION INVALID"
    if descriptive or result.get("ci") is None:
        return "DESCRIPTIVE"
    low, high = result["ci"]
    if not all(math.isfinite(x) for x in (low, high, result["mean"])) or low > high:
        return "IMPLEMENTATION INVALID"
    if low >= -threshold and high <= threshold:
        return "PRACTICALLY SMALL"
    if low > 0 and result["mean"] >= threshold:
        return "SUPPORT CANDIDATE"
    if high < 0 and result["mean"] <= -threshold:
        return "COUNTEREVIDENCE"
    return "INCONCLUSIVE"


def confirmation_size(discovery_sd, effect=0.05, power=0.90, family=3):
    """Two-sided normal planning; Bonferroni bound conservatively supports Holm's first test.

    Size is chosen ONCE from discovery cluster variance, before opening any reserve.
    The confirmation executor must decline if that many independent reserve units do
    not exist; it cannot replace the declared effect with the observed effect.
    """
    if not math.isfinite(discovery_sd) or discovery_sd <= 0 or not math.isfinite(effect) or effect <= 0 or family != 3 or not 0.5 < power < 1:
        raise ValueError("positive discovery variance/effect and the frozen family of three required")
    normal = NormalDist()
    n = math.ceil(((normal.inv_cdf(1 - 0.05 / (2 * family)) + normal.inv_cdf(power)) * discovery_sd / effect)**2)
    return {"n": max(60, n), "power": power, "effect": effect, "familywise_alpha": 0.05,
            "family": family, "discovery_sd": discovery_sd, "planning": "two-sided normal with Bonferroni sizing; Holm evaluation"}


def holm(p_values, alpha=0.05, family=3):
    if not 0 <= len(p_values) <= family:
        raise ValueError("confirmation family overflow")
    if any(not math.isfinite(p) or not 0 <= p <= 1 for p in p_values.values()):
        raise ValueError("invalid p-value")
    ordered = sorted(p_values, key=lambda k: (p_values[k], k))
    out, previous, stopped = {}, 0.0, False
    for rank, key in enumerate(ordered):
        threshold = alpha / (family - rank)
        adjusted = min(1.0, max(previous, (family - rank) * p_values[key]))
        stopped = stopped or p_values[key] > threshold
        out[key] = {"raw_p": p_values[key], "adjusted_p": adjusted, "threshold": threshold, "reject": not stopped}
        previous = adjusted
    return out
