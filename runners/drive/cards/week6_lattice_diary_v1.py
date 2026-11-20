"""Array-only Form O primitives for the Round 29 diary extension.

DESIGN CHECK: LESSONS 3-5. Weighted fitting must match literal whole-person
replication. A separated, rank-deficient, one-class or nonconverged problem is
invalid, never a zero estimate. The supplied floor-shift and unequal-noise worlds
are retained: the latter is expected to produce a spurious context contrast.
These primitives cannot admit a source or emit a scientific verdict by themselves.
"""
import numpy as np
from scipy.special import expit


class InvalidFit(ValueError):
    pass


def weights(n, weight):
    w = np.ones(n, dtype=float) if weight is None else np.asarray(weight, dtype=float)
    if w.shape != (n,) or not np.isfinite(w).all() or (w < 0).any() or w.sum() <= 0:
        raise InvalidFit('Finite nonnegative row weights with positive mass required')
    return w


def within(values, people, weight=None):
    """Within-person residuals and repeated means; weighted pooled RMS scale.

    Production bootstrap weights must be constant within each person's rows.
    Complete-case populations are frozen by the card before this function.
    """
    y = np.asarray(values, dtype=float)
    ids = np.asarray(people)
    if y.ndim == 1:
        y = y[:, None]
    if y.ndim != 2 or ids.shape != (len(y),) or not np.isfinite(y).all():
        raise InvalidFit('Aligned finite values and person identifiers required')
    units, inverse = np.unique(ids, return_inverse=True)
    count = np.bincount(inverse, minlength=len(units))
    means = np.column_stack([np.bincount(inverse, y[:, j], minlength=len(units))/count
                             for j in range(y.shape[1])])
    residual = y - means[inverse]
    w = weights(len(y), weight)
    minimum = np.full(len(units), np.inf)
    maximum = np.full(len(units), -np.inf)
    np.minimum.at(minimum, inverse, w)
    np.maximum.at(maximum, inverse, w)
    if np.any(minimum != maximum):
        raise InvalidFit('Resample complete people, not their individual rows')
    scale = np.sqrt((w[:, None]*residual**2).sum(axis=0)/w.sum())
    if (scale <= np.finfo(float).eps).any():
        raise InvalidFit('Predictor has no within-person variation')
    return residual / scale, means[inverse], scale


def logit_fit(X, y, weight=None, *, max_iter=100, tolerance=1e-9):
    """Unpenalized weighted logistic MLE, with convergence and finite-fit checks."""
    X, y = np.asarray(X, float), np.asarray(y, float)
    if X.ndim != 2 or y.shape != (len(X),) or not np.isfinite(X).all():
        raise InvalidFit('Finite aligned design required')
    if not np.isfinite(y).all() or not np.isin(y, [0, 1]).all():
        raise InvalidFit('Binary occurrence required')
    w = weights(len(X), weight)
    keep = w > 0
    X, y, w = X[keep], y[keep], w[keep]
    if len(np.unique(y)) != 2 or np.linalg.matrix_rank(X) != X.shape[1]:
        raise InvalidFit('One-class response or rank-deficient design')
    mass = float(w.sum())
    b = np.zeros(X.shape[1])

    def objective(v):
        z = X @ v
        return float(np.dot(w, np.logaddexp(0, z) - y*z))

    for iteration in range(max_iter):
        p = expit(X @ b)
        gradient = X.T @ (w*(p-y))
        H = (X*(w*p*(1-p))[:, None]).T @ X
        if not np.isfinite(H).all() or np.linalg.cond(H) > 1e12:
            raise InvalidFit('Singular information or separation')
        try:
            step = np.linalg.solve(H, gradient)
        except np.linalg.LinAlgError as exc:
            raise InvalidFit('Singular information') from exc
        # A tiny score alone does not certify separated data: the Newton step
        # must also vanish, rather than continuing towards infinite coefficients.
        if np.max(np.abs(gradient))/mass <= tolerance and np.max(np.abs(step)) <= 1e-7:
            return b
        old = objective(b)
        descent = float(np.dot(gradient, step))
        rate = 1.
        for _ in range(40):
            candidate = b-rate*step
            if objective(candidate) <= old - 1e-4*rate*descent + 1e-12*max(1., old):
                b = candidate
                break
            rate *= .5
        else:
            raise InvalidFit('Line search failed')
        if not np.isfinite(b).all() or np.max(np.abs(b)) > 100:
            raise InvalidFit('Unbounded coefficients or separation')
    raise InvalidFit('Unpenalized fit did not converge')


def linear_fit(X, y, weight=None):
    X, y = np.asarray(X, float), np.asarray(y, float)
    if X.ndim != 2 or y.shape != (len(X),) or not np.isfinite(X).all() or not np.isfinite(y).all():
        raise InvalidFit('Aligned finite linear arrays required')
    w = weights(len(X), weight)
    a, b = X*np.sqrt(w)[:, None], y*np.sqrt(w)
    if np.linalg.matrix_rank(a) != X.shape[1]:
        raise InvalidFit('Rank-deficient linear design')
    return np.linalg.lstsq(a, b, rcond=None)[0]


def person_draw(people, *, source_seed, draw):
    """Canonical source roster and indexed draw: stable across cards and resumes.

    Callers must pass the same complete source roster for the secondary lattice
    reference, then select their frozen complete-case subset. A roster change is
    a different draw bank and must not be claimed as paired.
    """
    units, inverse = np.unique(np.asarray(people), return_inverse=True)
    if len(units) < 2 or type(draw) is not int or draw < 0:
        raise InvalidFit('At least two people and a nonnegative draw index required')
    rng = np.random.default_rng(np.random.SeedSequence([source_seed, draw]))
    counts = np.bincount(rng.integers(0, len(units), len(units)), minlength=len(units))
    return counts[inverse]
