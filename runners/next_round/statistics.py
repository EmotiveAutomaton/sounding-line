"""Saved-output estimators; no scientific admission from exposed data.

DESIGN CHECK: LESSONS 2-5 and CONTROLS read 2026-10-14.
NULL: constant forecasts cannot create discrimination; no maker variance returns
zero between-maker variance. ALTERNATIVE: planted maker offsets are recovered;
miscalibrated informative probabilities improve on held-out makers. Outer labels
cannot change predictions. Invalid forecasts retain a fixed system penalty.
Intervals are descriptive, conditional on frozen predictions, not e-values.
"""
import os
for _k in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_k] = '1'
import numpy as np
from scipy.optimize import minimize, minimize_scalar
from scipy.special import softmax


def simplex(p):
    p = np.asarray(p, dtype=float)
    if p.ndim != 2 or p.shape[1] != 4 or not np.isfinite(p).all() or (p < 0).any():
        raise ValueError('invalid probabilities')
    if not np.allclose(p.sum(1), 1, atol=1e-6):
        raise ValueError('probabilities do not sum to one')
    p = np.maximum(p, 1e-8)
    return p / p.sum(1, keepdims=True)


def losses(p, y, valid=None):
    p = simplex(p); y = np.asarray(y, dtype=int)
    b = .5 * ((p - np.eye(4)[y]) ** 2).sum(1)
    ll = -np.log(p[np.arange(len(y)), y])
    if valid is not None:
        b = np.where(valid, b, 1.)
        ll = np.where(valid, ll, -np.log(.01))
    return b, ll


def fit_calibrator(p, y, groups, bias=True):
    """Equal-maker NLL; bounded scale and small, fixed L2 on class biases."""
    p = simplex(p); y = np.asarray(y); groups = np.asarray(groups)
    z = np.log(p); weights = np.array([1 / np.sum(groups == g) for g in groups])
    weights /= weights.sum()
    def objective(v):
        a = np.exp(v[0]); b = np.r_[v[1:], 0.] if bias else np.zeros(4)
        q = softmax(a * z + b, axis=1)
        value = -np.sum(weights * np.log(np.maximum(q[np.arange(len(y)), y], 1e-300)))
        grad = q.copy(); grad[np.arange(len(y)), y] -= 1; grad *= weights[:, None]
        penalty = .001 * np.sum(b * b)
        jac = [np.sum(grad * z) * a]
        if bias: jac.extend(grad.sum(0)[:3] + .002 * b[:3])
        return value + penalty, np.asarray(jac)
    bounds = [(-3., 3.)] + ([(-8., 8.)] * 3 if bias else [])
    result = minimize(objective, np.zeros(len(bounds)), jac=True, bounds=bounds,
                      method='L-BFGS-B', options={'maxiter': 300, 'ftol': 1e-11})
    if not result.success: raise ValueError('calibration did not converge: ' + result.message)
    return dict(scale=float(np.exp(result.x[0])),
                bias=(np.r_[result.x[1:], 0.] if bias else np.zeros(4)).tolist())


def calibrate(p, fit):
    return softmax(np.log(simplex(p)) * fit['scale'] + np.asarray(fit['bias']), axis=1)


def em_shift(p, source_prior, tolerance=1e-8, maxiter=2000):
    """Saerens EM; target labels are not an argument. Assumption sensitivity only.

    The denominator is mean training predictions, not an invented LLM training
    prior. This presumes label shift with invariant class-conditionals, unverified
    here. Adaptation uses the entire held-out maker's unlabelled forecast batch.
    """
    p = simplex(p); source = np.asarray(source_prior, dtype=float)
    if source.shape != (4,) or (source <= 0).any() or not np.isclose(source.sum(), 1):
        raise ValueError('invalid source prior')
    prior = source.copy()
    for step in range(maxiter):
        q = p * (prior / source); q /= q.sum(1, keepdims=True)
        updated = q.mean(0)
        if np.max(abs(updated - prior)) < tolerance:
            return q, dict(iterations=step+1, converged=True, prior=updated.tolist())
        prior = updated
    return q, dict(iterations=maxiter, converged=False, prior=prior.tolist())


def stack_weight(base, candidate, y, groups):
    """Simplex-constrained two-model stacking, minimized equal-maker half Brier."""
    base = simplex(base); candidate = simplex(candidate)
    groups = np.asarray(groups)
    weight = np.array([1 / np.sum(groups == g) for g in groups]); weight /= weight.sum()
    residual = base - np.eye(4)[y]; delta = candidate - base
    denominator = np.sum(weight[:, None] * delta * delta)
    if denominator < 1e-15: return 0.
    return float(np.clip(-np.sum(weight[:, None] * residual * delta) / denominator, 0, 1))


def fit_predict(train_p, train_y, train_groups, test_p, mode):
    if mode == 'BCTS':
        fit = fit_calibrator(train_p, train_y, train_groups, True)
        return calibrate(test_p, fit), dict(calibrator=fit)
    if mode != 'EM_TS': raise ValueError('unknown method')
    # On the training population EM is the identity by construction. The scalar
    # temperature is fitted without the held-out writer's outcomes.
    fit = fit_calibrator(train_p, train_y, train_groups, False)
    adjusted, record = em_shift(test_p, simplex(train_p).mean(0))
    return calibrate(adjusted, fit), dict(calibrator=fit, em=record)


def outer_fold(p, base, y, groups, heldout, mode='BCTS', valid=None):
    """Nested leave-one-writer-out: meta weights see only inner OOF probabilities."""
    p = simplex(p); base = simplex(base); y = np.asarray(y); groups = np.asarray(groups)
    valid = np.ones(len(y), bool) if valid is None else np.asarray(valid, bool)
    test = groups == heldout; train = ~test
    if len(set(groups[train])) < 2: raise ValueError('nested fit needs three writers')
    inner = base.copy(); audit = []
    for g in sorted(set(groups[train])):
        validation = train & (groups == g); fitmask = train & (groups != g) & valid
        if not fitmask.any(): raise ValueError('no valid calibration support')
        inner[validation], receipt = fit_predict(p[fitmask], y[fitmask], groups[fitmask], p[validation], mode)
        inner[validation & ~valid] = base[validation & ~valid]
        audit.append(dict(validation_writer=str(g), fit_writers=sorted(set(groups[fitmask])), **receipt))
    weight = stack_weight(base[train], inner[train], y[train], groups[train])
    fitmask = train & valid
    corrected, receipt = fit_predict(p[fitmask], y[fitmask], groups[fitmask], p[test], mode)
    candidate = corrected.copy(); candidate[~valid[test]] = base[test][~valid[test]]
    stacked = (1 - weight) * base[test] + weight * candidate
    return dict(corrected=corrected, stacked=stacked, weight=weight, audit=audit, final=receipt)


def random_effects(values, groups):
    """Unequal-size random-intercept ANOVA components (descriptive, not causal)."""
    values = np.asarray(values, float); groups = np.asarray(groups)
    names = sorted(set(groups)); n = np.array([np.sum(groups == g) for g in names], float)
    if len(names) < 2 or len(values) <= len(names): raise ValueError('insufficient variance support')
    means = np.array([values[groups == g].mean() for g in names])
    sse = sum(np.sum((values[groups == g] - m) ** 2) for g, m in zip(names, means))
    within = sse / (len(values) - len(names))
    between_ms = np.sum(n * (means - values.mean()) ** 2) / (len(names) - 1)
    n0 = (len(values) - np.sum(n*n) / len(values)) / (len(names) - 1)
    raw = (between_ms - within) / n0
    between = max(0., float(raw)); total = within + between
    return dict(within_variance=float(within), between_variance=between,
                untruncated_between_variance=float(raw), icc=float(between/total) if total > 0 else 0.,
                writers=len(names), decisions=len(values), effective_cluster_size=float(n0),
                writer_mean_gain=float(means.mean()),
                observed_writer_mean_sd=float(np.std(means, ddof=1)))
