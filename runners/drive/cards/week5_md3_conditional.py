"""Exact conditional participant-logit objective for the MD3.p successor.

DESIGN CHECK: LESSONS 3-5, CONTROLS 6-7. Exact count-conditioned normalizers,
moments and curvature; no sampled denominator, penalty or predictor deletion.
This objective treats predictor rows as fixed. Dynamic-panel consistency is
not asserted. Enumeration and signed/dynamic native qualifications are pending.
"""
import os
for _key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_key] = '2'

import numpy as np


def conditional_moments(x, beta, counts, check=None):
    """Log elementary-symmetric polynomial and exact first/second moments.

    Recurrence is a log-space mixture of subsets excluding/including each row.
    Means and covariances are propagated under that same exact mixture.
    Each call is one bounded block of complete participants.
    """
    x = np.asarray(x, float)
    beta = np.asarray(beta, float)
    counts = np.asarray(counts, int)
    n, trials, columns = x.shape
    if counts.shape != (n,) or np.any(counts < 0) or np.any(counts > trials):
        raise ValueError('Invalid conditional choice counts')
    maximum = int(counts.max(initial=0))
    logz = np.full((n, maximum + 1), -np.inf)
    logz[:, 0] = 0.
    mean = np.zeros((n, maximum + 1, columns))
    covariance = np.zeros((n, maximum + 1, columns, columns))
    for trial in range(trials):
        if check is not None:
            check()
        upper = min(maximum, trial + 1)
        if not upper:
            continue
        row = x[:, trial]
        skip = logz[:, 1:upper + 1].copy()
        take = logz[:, :upper] + (row @ beta)[:, None]
        combined = np.logaddexp(skip, take)
        ratio = np.zeros_like(combined)
        valid = np.isfinite(combined)
        ratio[valid] = np.exp(take[valid] - combined[valid])
        excluding = mean[:, 1:upper + 1].copy()
        including = mean[:, :upper].copy() + row[:, None, :]
        delta = including - excluding
        r = ratio[..., None]
        new_mean = excluding + r * delta
        new_covariance = ((1 - r[..., None]) * covariance[:, 1:upper + 1]
                          + r[..., None] * covariance[:, :upper]
                          + (ratio * (1 - ratio))[..., None, None]
                          * delta[..., :, None] * delta[..., None, :])
        logz[:, 1:upper + 1] = combined
        mean[:, 1:upper + 1] = new_mean
        covariance[:, 1:upper + 1] = new_covariance
    at = np.arange(n)
    return logz[at, counts], mean[at, counts], covariance[at, counts]


def objective(beta, x, y, weights=None, check=None, block=128):
    """Complete participant conditional negative log likelihood and derivatives."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    n, trials, columns = x.shape
    if y.shape != (n, trials) or not np.isin(y, (0., 1.)).all():
        raise ValueError('Binary balanced conditional panel required')
    weights = np.ones(n) if weights is None else np.asarray(weights, float)
    if weights.shape != (n,) or not np.isfinite(weights).all() or np.any(weights < 0):
        raise ValueError('Invalid whole-participant weights')
    if not np.isfinite(x).all() or not np.isfinite(beta).all():
        raise ValueError('Nonfinite conditional inputs')
    counts = y.sum(axis=1).astype(int)
    use = np.flatnonzero((counts > 0) & (counts < trials) & (weights > 0))
    loss = 0.
    gradient = np.zeros(columns)
    hessian = np.zeros((columns, columns))
    for start in range(0, len(use), block):
        if check is not None:
            check()
        ix = use[start:start + block]
        # Centering subtracts the same count-dependent constant from every
        # conditioned sequence; it leaves likelihood and derivatives exact.
        xx = x[ix] - x[ix].mean(axis=1, keepdims=True)
        observed = np.einsum('nt,ntd->nd', y[ix], xx)
        logz, mean, covariance = conditional_moments(xx, beta, counts[ix], check)
        weight = weights[ix]
        loss += float(weight @ (logz - observed @ beta))
        gradient += np.einsum('n,nd->d', weight, mean - observed)
        hessian += np.einsum('n,ndk->dk', weight, covariance)
    return loss, gradient, (hessian + hessian.T) / 2, use


def fit(x, y, weights=None, check=None, tolerance=1e-6, max_iter=100):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    weights = np.ones(len(x)) if weights is None else np.asarray(weights, float)
    beta = np.zeros(x.shape[-1])
    for iteration in range(max_iter):
        loss, gradient, hessian, use = objective(beta, x, y, weights, check)
        if len(use) < 2:
            raise ValueError('Fewer than two informative conditional participants')
        denominator = float(weights[use].sum())
        if not np.isfinite(loss) or not np.isfinite(hessian).all():
            raise ValueError('Nonfinite conditional objective')
        smallest = float(np.linalg.eigvalsh(hessian)[0])
        if smallest <= 1e-8:
            raise ValueError('Conditional likelihood rank deficient')
        gap = float(np.max(np.abs(gradient)) / denominator)
        if gap < tolerance:
            informative = np.zeros(len(x), bool)
            informative[use] = True
            return dict(beta=beta, informative=informative, gradient=gap,
                        iterations=iteration + 1, min_curvature=smallest,
                        objective=loss, conditional_objective=True)
        direction = np.linalg.solve(hessian, gradient)
        step = 1.
        accepted = False
        while step >= 2. ** -25:
            candidate = beta - step * direction
            other = objective(candidate, x, y, weights, check)[0]
            if other <= loss - 1e-4 * step * float(gradient @ direction):
                beta = candidate
                accepted = True
                break
            step /= 2
        if not accepted:
            raise ValueError('Conditional likelihood line search failed')
    raise ValueError('Conditional likelihood gradient tolerance not reached')
