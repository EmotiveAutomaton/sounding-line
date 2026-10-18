"""D4 soft correction votes and held-out conditional menu-choice scores.

DESIGN CHECK: LESSONS 3-5. A symmetric contradictory vote set gives zero
direction and uniform choices. Planted aligned/reversed preferences must retain
their score signs. Ridge supplies finite slack, never an intersection of hard
half-spaces. Calibration chooses only the fixed penalty; scored choices never
fit parameters. Unusable support and failed optimality are invalid, not null.
"""
import hashlib
import math
from collections import defaultdict
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit, softmax
from . import states_v2 as states

PENALTIES = (.01, .1, 1., 10.)


def stable_seed(seed, label):
    return seed + int(hashlib.sha256(label.encode()).hexdigest()[:8], 16)


def vote_objective(beta, units, penalty):
    linear = units @ beta
    value = np.logaddexp(0., -linear).mean() + penalty * (beta @ beta) / 2
    gradient = -(units.T @ expit(-linear)) / len(units) + penalty * beta
    return float(value), gradient


def fit_votes(units, penalty):
    units = np.asarray(units, float)
    if units.ndim != 2 or not len(units) or not np.isfinite(units).all():
        raise ValueError('invalid correction votes')
    if not np.allclose(np.linalg.norm(units, axis=1), 1., atol=1e-6, rtol=0):
        raise ValueError('correction votes are not unit directions')
    if penalty not in PENALTIES:
        raise ValueError('unfrozen penalty')
    result = minimize(vote_objective, np.zeros(units.shape[1]), args=(units, penalty), jac=True,
        method='L-BFGS-B', options=dict(maxiter=500, ftol=1e-14, gtol=1e-9, maxls=40))
    value, gradient = vote_objective(result.x, units, penalty)
    gap = float(np.max(np.abs(gradient)))
    if not result.success or not np.isfinite(result.x).all() or gap > 1e-7:
        raise ValueError('soft-vote optimizer lacks optimality certificate')
    return dict(penalty=penalty, coefficients=result.x.tolist(), objective=value,
                gradient_max=gap, iterations=int(result.nit))


def probabilities(options, coefficients):
    options, beta = np.asarray(options, float), np.asarray(coefficients, float)
    if options.ndim != 2 or options.shape[1] != len(beta) or len(options) < 2 or not np.isfinite(options).all():
        raise ValueError('invalid menu choice vectors')
    return softmax(options @ beta)


def half_brier(probability, chosen):
    p = np.asarray(probability, float)
    if p.ndim != 1 or not 0 <= chosen < len(p) or np.any(p < 0) or not np.isfinite(p).all() or not np.isclose(p.sum(), 1.):
        raise ValueError('invalid categorical prediction')
    return float((p @ p - 2 * p[chosen] + 1) / 2)


def session_mean(rows, values):
    groups = defaultdict(list)
    for row, value in zip(rows, values):
        groups[row['session']].append(float(value))
    if not groups or len(rows) != len(values):
        raise ValueError('empty or mismatched choice support')
    return float(np.mean([np.mean(groups[k]) for k in sorted(groups)]))


def permuted_choices(rows, seed):
    """Within writer/menu size, separately for each caller's chronological phase."""
    rows = [dict(row) for row in rows]
    by_size = defaultdict(list)
    for index, row in enumerate(rows):
        by_size[len(row['options'])].append(index)
    rng = np.random.default_rng(seed)
    changed = 0
    for size, indices in sorted(by_size.items()):
        before = np.array([rows[i]['chosen'] for i in indices])
        after = rng.permutation(before)
        changed += int(np.sum(before != after))
        for index, chosen in zip(indices, after):
            rows[index]['chosen'] = int(chosen)
    return rows, dict(rows=len(rows), changed=changed, singleton_size_strata=sum(len(v) == 1 for v in by_size.values()))


def select_model(models, calibration, vectors):
    losses = []
    for model in models:
        values = [half_brier(probabilities(vectors[r['options']], model['coefficients']), r['chosen']) for r in calibration]
        losses.append(session_mean(calibration, values))
    index = min(range(len(models)), key=lambda i: (losses[i], i))
    return index, losses


def score_pair(models, calibration, test, vectors):
    selected, losses = {}, {}
    for split in ('content', 'housekeeping'):
        selected[split], losses[split] = select_model(models[split], calibration, vectors)
    predictions = []
    for row in test:
        p = {split: probabilities(vectors[row['options']], models[split][selected[split]]['coefficients']).tolist()
             for split in selected}
        p['uniform'] = [1 / len(row['options'])] * len(row['options'])
        scores = {name: half_brier(value, row['chosen']) for name, value in p.items()}
        predictions.append(dict(**row, probabilities=p, half_brier=scores))
    result = dict(content_gain=session_mean(test, [r['half_brier']['uniform'] - r['half_brier']['content'] for r in predictions]),
        housekeeping_gain=session_mean(test, [r['half_brier']['uniform'] - r['half_brier']['housekeeping'] for r in predictions]))
    result['primary'] = result['content_gain'] - result['housekeeping_gain']
    return dict(selected=selected, calibration_losses=losses, predictions=predictions, scores=result)


def cross_session_cohesion(rows, units):
    grouped = defaultdict(list)
    for row, unit in zip(rows, units):
        grouped[row['session']].append(unit)
    keys = sorted(grouped)
    numerator, denominator = 0., 0
    for i, key in enumerate(keys):
        left = np.sum(grouped[key], axis=0)
        for other in keys[i + 1:]:
            numerator += float(left @ np.sum(grouped[other], axis=0))
            denominator += len(grouped[key]) * len(grouped[other])
    return numerator / denominator if denominator else None


def interval(values, bootstrap, seed):
    values = np.asarray(values, float)
    if len(values) < 2 or not np.isfinite(values).all():
        return dict(effect=None, ci95=None, state='invalid', writers=len(values), reason='fewer than two valid writers')
    rng = np.random.default_rng(seed)
    draws = np.mean(values[rng.integers(len(values), size=(bootstrap, len(values)))], axis=1)
    point = float(values.mean())
    low, high = np.quantile(draws, [.025, .975]).tolist()
    se = float(np.std(draws, ddof=1))
    z = point / se if se > 0 else None
    return dict(effect=point, ci95=[low, high], standard_error=se, z=z,
        p_approx=math.erfc(abs(z) / math.sqrt(2)) if z is not None else None,
        p_method='two-sided normal-reference Wald approximation; descriptive, not permutation p',
        state=states.contrast_state(point, low, high), writers=len(values))


def summarize(writers, config):
    output = {}
    for arm in ('model', 'model_outcome_shuffle', 'own', 'model_on_own_support'):
        supported = [r for r in writers if arm in r.get('arms', {})]
        output[arm] = {metric: interval([r['arms'][arm]['scores'][metric] for r in supported], config['bootstrap'], config['seed'])
                       for metric in ('primary', 'content_gain', 'housekeeping_gain')}
    cohesion = {}
    for origin in ('model', 'own'):
        for split in ('content', 'housekeeping'):
            key = origin + '_' + split
            values = [r['cohesion'][key] for r in writers if r.get('cohesion', {}).get(key) is not None]
            cohesion[key] = interval(values, config['bootstrap'], config['seed'])
    return dict(primary=output['model']['primary'], state=output['model']['primary']['state'],
        comparisons=output, correction_consistency=cohesion,
        conditional_extension='D4b own earlier typed style, not run', extension_run=False,
        weighting='Equal writers, equal scored sessions within writer, equal choice menus within session',
        probability_scope='Conditional on uniquely selected accept/edit menus with at least two displayed offers; no prediction of request or acceptance',
        shuffle='Chosen positions permuted within writer and menu size, separately in calibration and test; penalty selected again',
        interpretation='Prediction from prior corrections; no hard constraint, hidden intention or causal preference claim')
