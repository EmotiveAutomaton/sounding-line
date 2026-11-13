"""TR1's frozen candidate arithmetic; no source loading or admission side effects.

DESIGN CHECK: LESSONS 2-5; CONTROLS 6-7. Measurement error and instability
are distinct. Ratios and corrected variances are never clipped. Unsupported
draws remain failed draws; every resample selects complete people.
"""
from __future__ import annotations
import numpy as np

GAMMA = .65
METHODS = ('sampling', 'split_half')


def recent_luck(plays):
    plays = np.asarray(plays, float)
    if plays.ndim != 3 or plays.shape[1:] != (30, 15):
        raise ValueError('TR1 requires the original thirty-trial task')
    ev = (plays[:, :, 3] + plays[:, :, 4]) / 2
    luck = (plays[:, :, 7] - ev) * plays[:, :, 6]
    history = np.zeros((len(plays), 31))
    for trial in range(30):
        history[:, trial + 1] = GAMMA * history[:, trial] + luck[:, trial]
    indices = [np.flatnonzero(np.isfinite(play[:, 9])) for play in plays]
    if any(len(index) != 12 or index[0] != 0 or index[-1] != 29 for index in indices):
        raise ValueError('TR1 requires all twelve documented rating occasions')
    indices = np.asarray(indices)
    observed = indices + 1
    observed[:, 0] = 0  # First stored rating precedes trial 1; later ones follow their row.
    return history[np.arange(len(plays))[:, None], observed], plays[np.arange(len(plays))[:, None], indices, 9], luck.sum(axis=1)


def ols(x, y):
    """Vectorized exact two-column OLS; rank failures remain explicit NaNs."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    if x.shape != y.shape or x.ndim != 2 or x.shape[1] < 3:
        raise ValueError('Paired rating arrays required')
    xc = x - x.mean(axis=1, keepdims=True)
    den = np.sum(xc * xc, axis=1)
    valid = np.isfinite(x).all(axis=1) & np.isfinite(y).all(axis=1) & (den > 1e-12)
    gain = np.full(len(x), np.nan)
    gain[valid] = np.sum(xc[valid] * y[valid], axis=1) / den[valid]
    level = y.mean(axis=1) - gain * x.mean(axis=1)
    coefficient = np.column_stack((level, gain))
    residual = y - level[:, None] - gain[:, None] * x
    return coefficient, residual, valid


def residual_noise(x, y, weights=None):
    _, residual, valid = ols(x, y)
    weights = np.ones(len(x)) if weights is None else np.asarray(weights, float)
    if len(weights) != len(x) or np.any(weights < 0):
        raise ValueError('Invalid whole-play noise multiplicities')
    valid &= weights > 0
    residual = residual[valid]
    weights = weights[valid]
    if len(residual) < 2:
        return {'status': 'unsupported', 'reason': 'fewer than two supported play residual series'}
    den = float(weights @ np.sum(residual[:, :-1] ** 2, axis=1))
    if den <= 0:
        return {'status': 'unsupported', 'reason': 'no residual noise variance'}
    raw = float(weights @ np.sum(residual[:, :-1] * residual[:, 1:], axis=1) / den)
    phi = float(np.clip(raw, -.95, .95))
    scale = float(np.sqrt(weights @ np.mean(residual ** 2, axis=1) / weights.sum()))
    xscale = float(np.sqrt(weights @ np.mean((x[valid] - x[valid].mean(axis=1, keepdims=True)) ** 2, axis=1) / weights.sum()))
    return {'status': 'ok', 'phi_raw': raw, 'phi': phi, 'phi_truncated': raw != phi,
            'residual_sd': scale, 'within_play_luck_sd': xscale,
            'rating_count': int(x.shape[1]), 'supported_plays': int(valid.sum()),
            'rank_failed_plays': int((~valid).sum())}


def play_table(x, y, phi):
    coefficient, residual, valid = ols(x, y)
    n, occasions = x.shape
    covariance = np.full((n, 2), np.nan)
    half = np.full((n, 2, 2), np.nan)
    for side, sl in enumerate((slice(0, occasions // 2), slice(occasions // 2, occasions))):
        half[:, side], _, _ = ols(x[:, sl], y[:, sl])
    xx = x[valid]
    centered = xx - xx.mean(axis=1, keepdims=True)
    gain_row = centered / np.sum(centered * centered, axis=1)[:, None]
    level_row = 1 / occasions - xx.mean(axis=1)[:, None] * gain_row
    a = np.stack((level_row, gain_row), axis=1)
    design = np.stack((np.ones_like(xx), xx), axis=2)
    correlation = phi ** np.abs(np.arange(occasions)[:, None] - np.arange(occasions)[None, :])
    hat = np.einsum('nri,nis->nrs', design, a)
    denominator = occasions - np.einsum('nij,ji->n', hat, correlation)
    if np.any(denominator <= 0):
        raise ValueError('Nonpositive projected AR1 residual degrees of freedom')
    sigma2 = np.sum(residual[valid] ** 2, axis=1) / denominator
    covariance[valid] = sigma2[:, None] * np.einsum('nir,rs,nis->ni', a, correlation, a)
    return {'coefficient': coefficient, 'sampling_variance': covariance, 'half': half,
            'rating_sd': np.std(y, axis=1, ddof=1), 'valid': valid}


def weighted_moments(x, y, weight):
    weight = np.asarray(weight, float)
    if len(x) != len(y) or len(x) != len(weight) or np.any(weight < 0):
        raise ValueError('Invalid complete-unit multiplicities')
    use = weight > 0
    x, y, weight = np.asarray(x)[use], np.asarray(y)[use], weight[use]
    if len(x) < 2 or not np.isfinite(x).all() or not np.isfinite(y).all():
        return None
    total = weight.sum()
    if total <= 1:
        return None
    xm, ym = weight @ x / total, weight @ y / total
    vx, vy = weight @ (x - xm) ** 2 / (total - 1), weight @ (y - ym) ** 2 / (total - 1)
    if vx <= 0 or vy <= 0:
        return None
    covariance = weight @ ((x - xm) * (y - ym)) / (total - 1)
    return float(covariance / np.sqrt(vx * vy)), float(vx), float(vy)


def stability(table, left, right, pair_weight, method, column=1, standardize=False):
    if method not in METHODS:
        raise ValueError('Unregistered reliability estimator')
    values = table['coefficient'][:, column].copy()
    error = table['sampling_variance'][:, column].copy()
    halves = table['half'][:, :, column].copy()
    if standardize:
        with np.errstate(divide='ignore', invalid='ignore'):
            values /= table['rating_sd']
            error /= table['rating_sd'] ** 2
            halves /= table['rating_sd'][:, None]
    moments = weighted_moments(values[left], values[right], pair_weight)
    if moments is None:
        return {'status': 'unsupported', 'reason': 'nonfinite, zero-variance or insufficient paired fits'}
    raw, vl, vr = moments
    reliability = []
    variances = []
    for indices, observed in ((left, vl), (right, vr)):
        if method == 'sampling':
            use = pair_weight > 0
            if not np.isfinite(error[indices][use]).all():
                return {'status': 'unsupported', 'reason': 'nonfinite sampling variance'}
            noise = float(pair_weight[use] @ error[indices][use] / pair_weight[use].sum())
            true = observed - noise
            rel = true / observed
        else:
            h = weighted_moments(halves[indices, 0], halves[indices, 1], pair_weight)
            if h is None or h[0] <= -1:
                return {'status': 'unsupported', 'reason': 'unsupported split-half correlation'}
            rel = 2 * h[0] / (1 + h[0])
            true = observed * rel
        reliability.append(float(rel)); variances.append(float(true))
    answer = {'status': 'ok', 'raw_correlation': raw, 'reliabilities': reliability,
              'true_variances': variances, 'minimum_true_variance': min(variances),
              'stability': None, 'method': method}
    if min(reliability) <= 0:
        answer.update(status='nonpositive_reliability', reason='corrected between-person variance is not positive')
    else:
        answer['stability'] = float(raw / np.sqrt(np.prod(reliability)))
    return answer


def consecutive(person, counter):
    """Consecutive observed completed plays, preserving missing-attempt counts."""
    order = np.lexsort((counter, person))
    use = person[order[:-1]] == person[order[1:]]
    left, right = order[:-1][use], order[1:][use]
    if np.any(counter[right] - counter[left] <= 0):
        raise ValueError('Ambiguous attempt order')
    return left, right


def carryover(total_luck, first_rating, person, left, right, weights, mask=None):
    mask = np.ones(len(left), bool) if mask is None else np.asarray(mask, bool)
    code = person[right[mask]]
    x, y = total_luck[left[mask]], first_rating[right[mask]]
    n = len(weights)
    count = np.bincount(code, minlength=n)
    sx = np.bincount(code, weights=x, minlength=n)
    sy = np.bincount(code, weights=y, minlength=n)
    ss = np.bincount(code, weights=x*x, minlength=n) - sx*sx / np.maximum(count, 1)
    cross = np.bincount(code, weights=x*y, minlength=n) - sx*sy / np.maximum(count, 1)
    valid = (count >= 2) & (ss > 1e-12) & (weights > 0)
    numerator = float(weights[valid] @ cross[valid]); denominator = float(weights[valid] @ ss[valid])
    informative = int(valid.sum())
    return {'status': 'ok' if denominator > 0 else 'unsupported',
            'slope': numerator / denominator if denominator > 0 else None,
            'informative_people': informative}


def choose_calibration(cases):
    """Among estimators passing every world, choose the smaller .5 error."""
    if set(cases) != {'0.0', '0.5', '1.0'}:
        raise ValueError('All three fixed calibration worlds are required')
    errors = {}
    for method in METHODS:
        value = cases['0.5'][method]
        if value.get('status') == 'ok' and value.get('stability') is not None:
            errors[method] = abs(value['stability'] - .5)
    if not errors:
        return {'qualified': False, 'selected_method': None, 'reason': 'no supported middle-world estimator'}
    per_method = {method: all(cases[key][method].get('status') == 'ok'
                      and abs(cases[key][method]['stability'] - float(key)) <= .1 for key in cases)
                  for method in METHODS}
    eligible = [method for method in METHODS if per_method[method]]
    selected = min(eligible, key=lambda method: (errors[method], METHODS.index(method))) if eligible else None
    return {'qualified': bool(eligible), 'selected_method': selected,
            'middle_world_absolute_errors': errors, 'all_worlds_within_point_one': per_method,
            'selection': 'among methods passing all three worlds, smaller absolute error at .5; sampling wins exact ties; freeze before human inference'}


def uncertainty(point, records, field, bar):
    values = [record.get(field) for record in records]
    failed = [i for i, value in enumerate(values) if value is None or not np.isfinite(value)]
    if failed or len(values) != 2000:
        return {'status': 'invalid_uncertainty', 'failed_draws': failed, 'draws': len(values),
                'expected_draws': 2000, 'estimate': point, 'interval': None}
    values = np.asarray(values)
    se = float(np.std(values, ddof=1))
    return {'status': 'ok', 'estimate': point, 'interval': np.quantile(values, [.025, .975]).tolist(),
            'bootstrap_se': se, 'draws': 2000, 'sees': 2.8 * se, 'supports_at': bar + 2.8 * se,
            'bar': bar, 'limited_sensitivity': 2.8 * se > bar,
            'sensitivity_scope': 'optimistic normal approximation; not measured population power'}


def decision(variance, primary, qualified):
    if not qualified:
        return 'estimator unqualified'
    if variance.get('status') != 'ok' or variance['interval'][0] <= 0:
        return 'no between-person differences in sensitivity could be measured in this task'
    if primary.get('status') != 'ok':
        return 'invalid uncertainty; no stability inference'
    lo, hi = primary['interval']
    if lo > .5:
        return 'supports a stable sensitivity'
    if hi < .2:
        return 'not stable at the registered band'
    if lo >= .2 and hi <= .5:
        return 'partly stable'
    return 'inconclusive across the registered stability bands'
