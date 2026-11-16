"""Prospective KP numerical primitives; never opens source files.

DESIGN CHECK: LESSONS 3-5 reviewed for this delivery. NULL logistic remainder
OR is one; positive/reversed plants retain their sign. Boundary-only confounding
must disappear with the declared covariates and remain visible in the raw trap.
Held-out responses never enter training centering. Singular focal contrasts,
separation, invalid fixed draws and unsupported folds remain explicit failures;
no redraw, success-only interval, ridge rescue or outcome-selected covariate.
These functions are unqualified until the owner runs the constructed harness.
"""
from __future__ import annotations

import math
import numpy as np
from scipy.optimize import minimize, minimize_scalar
from scipy.special import expit


def checked(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if x.ndim != 2 or y.ndim != 1 or len(x) != len(y) or not len(y):
        raise ValueError('Invalid design shape')
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError('Nonfinite design')
    return x, y


def centre(values, writers, *, usual=None, standardize=False):
    """Within-writer departures; supplied usual is training-only for prediction."""
    values = np.asarray(values, float)
    if values.ndim == 1:
        values = values[:, None]
    writers = np.asarray(writers)
    if len(values) != len(writers) or not np.isfinite(values).all():
        raise ValueError('Invalid centering inputs')
    out = np.empty_like(values)
    learned = {}
    for writer in sorted(set(writers)):
        ix = writers == writer
        if usual is None:
            mean = values[ix].mean(axis=0)
            scale = values[ix].std(axis=0, ddof=0) if standardize else np.ones(values.shape[1])
            if standardize and np.any(scale <= 0):
                raise ValueError('Within-writer scale has no support')
        else:
            if writer not in usual:
                raise ValueError('Writer has no training usual')
            mean, scale = map(np.asarray, usual[writer])
        learned[writer] = (mean.tolist(), scale.tolist())
        out[ix] = (values[ix] - mean) / scale
    return out, learned


def independent_columns(x, focal):
    """Preserve nuisance span, never silently drop a requested focal contrast."""
    scale = np.maximum(np.linalg.norm(x, axis=0), 1e-15)
    z = x / scale
    keep, omitted = [], []
    for j in [j for j in range(x.shape[1]) if j not in focal] + list(focal):
        supported = np.linalg.norm(x[:, j]) > 1e-10
        independent = supported and np.linalg.matrix_rank(z[:, keep + [j]], tol=1e-9) > len(keep)
        if independent:
            keep.append(j)
        elif j in focal:
            raise ValueError('Focal contrast not separately identifiable')
        else:
            omitted.append(j)
    return sorted(keep), omitted


def fixed_writer_design(x, writers):
    """No intercept column in x; one unpenalized intercept per writer."""
    writers = np.asarray(writers)
    ids = sorted(set(writers))
    intercepts = np.column_stack([writers == w for w in ids]).astype(float)
    return np.column_stack((x, intercepts)), ids


def logistic(x, y, *, focal=(0,)):
    x, y = checked(x, y)
    if not set(y) <= {0., 1.} or len(set(y)) != 2:
        raise ValueError('Binary response lacks both classes')
    keep, omitted = independent_columns(x, focal)
    a = x[:, keep]
    scale = np.maximum(np.linalg.norm(a, axis=0) / math.sqrt(len(y)), 1e-15)
    z = a / scale

    def objective(b):
        eta = z @ b
        return float(np.mean(np.logaddexp(0., eta) - y * eta)), z.T @ (expit(eta) - y) / len(y)

    fit = minimize(objective, np.zeros(len(keep)), jac=True, method='BFGS',
                   options={'gtol': 1e-9, 'maxiter': 500})
    value, gradient = objective(fit.x)
    if (not np.isfinite(fit.x).all() or not math.isfinite(value)
            or np.max(np.abs(gradient)) > 1e-7):
        raise ValueError('Logistic fit lacks finite score certificate')
    probability = expit(z @ fit.x)
    information = (z.T * (probability * (1 - probability))) @ z / len(y)
    if np.linalg.eigvalsh(information)[0] <= 1e-10:
        raise ValueError('Logistic separation or singular information')
    beta = np.zeros(x.shape[1]); beta[keep] = fit.x / scale
    return {'coefficients': beta.tolist(), 'omitted_columns': omitted,
            'max_abs_score': float(np.max(np.abs(gradient))), 'objective': value}


def linear(x, y, *, focal=(0,)):
    x, y = checked(x, y)
    keep, omitted = independent_columns(x, focal)
    b = np.linalg.lstsq(x[:, keep], y, rcond=None)[0]
    if not np.isfinite(b).all():
        raise ValueError('Nonfinite linear fit')
    beta = np.zeros(x.shape[1]); beta[keep] = b
    return {'coefficients': beta.tolist(), 'omitted_columns': omitted}


def mixed(x, y, writers, *, focal):
    """D33 Gaussian random-intercept ML objective, generalized column names.

    Same ratio bounds, optimizer tolerance, zero-variance comparison and exact
    nuisance span as the original D33 fit. The returned BLUP uses training rows.
    """
    x, y = checked(x, y); writers = np.asarray(writers)
    if len(writers) != len(y):
        raise ValueError('Writer shape differs')
    keep, omitted = independent_columns(x, focal)
    a = x[:, keep]
    groups = []
    for writer in sorted(set(writers)):
        ix = writers == writer; gx, gy = a[ix], y[ix]
        groups.append((writer, len(gy), gx.sum(axis=0), float(gy.sum())))
    xx, xy, yy = a.T @ a, a.T @ y, float(y @ y)

    def solve(ratio):
        aa, bb, cc = xx.copy(), xy.copy(), yy
        for _, n, sx, sy in groups:
            weight = ratio / (1 + n * ratio)
            aa -= weight * np.outer(sx, sx); bb -= weight * sx * sy; cc -= weight * sy * sy
        scale = np.sqrt(np.maximum(np.diag(aa), 1e-30))
        normalized = aa / np.outer(scale, scale)
        if np.linalg.matrix_rank(normalized, tol=1e-9) != len(keep):
            raise ValueError('Mixed design not identifiable')
        beta = np.linalg.solve(normalized, bb / scale) / scale
        rss = max(cc - float(beta @ bb), np.finfo(float).tiny)
        value = len(y) * np.log(rss / len(y)) + sum(np.log1p(n * ratio) for _, n, _, _ in groups)
        return float(value), beta

    fit = minimize_scalar(lambda r: solve(float(np.exp(r)))[0], bounds=(-15, 15),
                          method='bounded', options={'xatol': 1e-5})
    if not fit.success or not math.isfinite(float(fit.fun)):
        raise ValueError('Mixed variance optimizer failed')
    ratio = float(np.exp(fit.x))
    if solve(ratio)[0] >= solve(0.)[0]:
        ratio = 0.
    objective, b = solve(ratio)
    beta = np.zeros(x.shape[1]); beta[keep] = b
    intercepts = {str(w): float(ratio / (1 + n * ratio) * (sy - sx @ b)) for w, n, sx, sy in groups}
    return {'coefficients': beta.tolist(), 'writer_intercepts': intercepts,
            'variance_ratio': ratio, 'omitted_columns': omitted, 'objective': objective}


def interval(point, values, *, null=0., bar=0., control_threshold=None):
    """No failure discarded; equality at zero or bar never becomes support."""
    if point is None or not math.isfinite(point) or not values or any(v is None or not math.isfinite(v) for v in values):
        return {'state': 'invalid', 'point': point, 'attempted_draws': len(values),
                'invalid_draws': sum(v is None or not math.isfinite(v) for v in values)}
    low, high = map(float, np.quantile(values, [.025, .975]))
    if low > null and point > bar and (control_threshold is None or point > control_threshold):
        state = 'supported_association'
    elif high < null:
        state = 'opposite_association'
    elif low > null:
        state = 'positive_below_bar_or_control'
    else:
        state = 'unresolved'
    return {'state': state, 'point': point, 'ci_low': low, 'ci_high': high,
            'attempted_draws': len(values), 'invalid_draws': 0,
            'null': null, 'bar': bar, 'control_threshold': control_threshold}


def writer_draw(rows, selected, writers):
    """Duplicate bootstrap clusters get new intercept identities, never merged."""
    groups = {w: [r for r in rows if r['writer'] == w] for w in writers}
    return [dict(r, writer=f'bootstrap-{i:04d}') for i, k in enumerate(selected) for r in groups[writers[int(k)]]]


def fixed_bank(rows, fit_function, *, draws, seed):
    writers = sorted({r['writer'] for r in rows})
    if len(writers) < 2:
        raise ValueError('Writer bootstrap needs multiple writers')
    rng = np.random.default_rng(seed)
    results = []
    for index in range(draws):
        sample = writer_draw(rows, rng.integers(len(writers), size=len(writers)), writers)
        try:
            results.append({'draw': index, 'value': float(fit_function(sample)), 'failure': None})
        except (ValueError, np.linalg.LinAlgError) as error:
            results.append({'draw': index, 'value': None, 'failure': str(error)})
    return results
