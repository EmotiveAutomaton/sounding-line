"""Shared exact scores and conservative, exhaustive resource decisions.

DESIGN CHECK: LESSONS 3-5, CONTROLS read 2026-10-16. NULL: constant calibrated
forecasts have zero resolution; within-bin covariance can make residual negative.
ALTERNATIVE: deterministic correct forecasts attain zero loss. Singletons cannot
receive a finite-sample correction. Invalid/negative/zero/positive bands explicit.
"""
import math
import numpy as np


def probabilities(p, y):
    p = np.asarray(p, dtype=float); y = np.asarray(y)
    if p.ndim != 2 or p.shape[1] < 2 or len(p) == 0 or y.shape != (len(p),):
        raise ValueError('nonempty aligned multiclass rows required')
    if not np.isfinite(p).all() or np.any(p < 0) or np.any(p > 1) or not np.allclose(p.sum(1), 1, atol=1e-10, rtol=0):
        raise ValueError('invalid probability simplex')
    if y.dtype.kind not in 'iu' or np.any(y < 0) or np.any(y >= p.shape[1]):
        raise ValueError('invalid class index')
    return p, np.eye(p.shape[1])[y]


def half_brier(p, y):
    p, target = probabilities(p, y)
    return .5 * ((p - target)**2).sum(axis=1)


def merged_bins(f, minimum=2):
    """Fixed deciles; merge sparse adjacent occupied bins, lower on a distance tie."""
    ids = np.minimum((np.asarray(f)*10).astype(int), 9)
    groups = [np.flatnonzero(ids == k) for k in range(10) if np.any(ids == k)]
    while len(groups) > 1:
        small = next((i for i, g in enumerate(groups) if len(g) < minimum), None)
        if small is None: break
        if small == 0: other = 1
        elif small == len(groups)-1: other = small-1
        else:
            mid = float(np.mean(np.asarray(f)[groups[small]]))
            other = min((small-1, small+1), key=lambda i: (abs(float(np.mean(np.asarray(f)[groups[i]]))-mid), i))
        lo, hi = sorted((small, other)); groups[lo] = np.concatenate((groups[lo], groups[hi])); del groups[hi]
    return groups


def decomposition(p, y, exact_vectors=False):
    p, target = probabilities(p, y); n, k = p.shape
    exact = .5 * float(np.mean(np.sum((p-target)**2, axis=1)))
    if exact_vectors:
        _, ids = np.unique(p, axis=0, return_inverse=True)
        common = [np.flatnonzero(ids == i) for i in range(ids.max()+1)]
    rel = res = unc = residual = correction = 0.; correctable = True; bins = []
    for j in range(k):
        f, z = p[:, j], target[:, j]; mean = z.mean(); unc += mean*(1-mean)
        groups = common if exact_vectors else merged_bins(f)
        details = []
        for g in groups:
            m = len(g); w = m/n; fb, ob = f[g].mean(), z[g].mean()
            rel += w*(fb-ob)**2; res += w*(ob-mean)**2
            residual += w*(np.var(f[g])-2*np.mean((f[g]-fb)*(z[g]-ob)))
            if m > 1: correction += w*ob*(1-ob)/(m-1)
            else: correctable = False
            details.append(dict(n=m, forecast=float(fb), observed=float(ob)))
        bins.append(details)
    rel, res, unc, residual, correction = [float(v/2) for v in (rel, res, unc, residual, correction)]
    reconstructed = rel-res+unc+residual
    if not math.isclose(exact, reconstructed, abs_tol=1e-10): raise ArithmeticError('decomposition does not close')
    return dict(half_brier=exact, reliability=rel, resolution=res, uncertainty=unc,
        binning_residual=residual, reconstructed=reconstructed, bins=bins,
        correction_iid=correction if correctable else None,
        corrected_reliability_iid=rel-correction if correctable else None,
        correction_valid_for_clusters=False, mode='exact_vectors' if exact_vectors else 'merged_deciles')


def cluster_interval(values, clusters, seed=161016, draws=2000):
    values = np.asarray(values, float); clusters = np.asarray(clusters)
    if values.shape != clusters.shape or not np.isfinite(values).all(): raise ValueError('invalid cluster rows')
    groups = [values[clusters == c] for c in np.unique(clusters)]
    if len(groups) < 2: raise ValueError('two independent clusters required')
    rng = np.random.default_rng(seed); means = []
    for _ in range(draws):
        picked = rng.integers(len(groups), size=len(groups))
        means.append(float(np.concatenate([groups[i] for i in picked]).mean()))
    return dict(estimate=float(values.mean()), interval95=np.quantile(means,[.025,.975]).tolist(),
                clusters=len(groups), bootstrap_draws=draws, seed=seed, selection_adjusted=False)


def futility(fraction, gain, standard_error):
    if fraction not in (.2, .5, 1.): raise ValueError('unplanned look')
    if not math.isfinite(gain) or not math.isfinite(standard_error) or standard_error < 0:
        return dict(action='STOP_INVALID', z=None)
    if standard_error == 0:
        return dict(action='STOP_FUTILITY' if gain <= 0 else ('FINAL_REVIEW' if fraction == 1 else 'CONTINUE'), z=None)
    z = gain / standard_error
    stop = (fraction == .2 and z < -.5) or (fraction == .5 and z < 0)
    return dict(action='STOP_FUTILITY' if stop else ('FINAL_REVIEW' if fraction == 1 else 'CONTINUE'), z=z)


def extension(estimate, interval, valid=True):
    if not valid: return dict(outcome='invalid', extend=False)
    low, high = interval
    if not all(math.isfinite(x) for x in (estimate, low, high)) or not low <= estimate <= high:
        raise ValueError('invalid effect interval')
    outcome = 'positive' if low > 0 else 'negative' if high < 0 else 'marginal' if estimate > 0 else 'null'
    return dict(outcome=outcome, extend=outcome in ('positive','marginal'))
