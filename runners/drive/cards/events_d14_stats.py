"""D14 probability slope with writer intercepts and fixed content controls.

DESIGN CHECK: LESSONS 3-5. Independent outcomes have zero adjusted slope;
known positive/reverse probability slopes must retain sign and magnitude.
The primary must be identified outside the nuisance span. Missing support or
an unidentified bootstrap draw is invalid, never a scientific negative.
No causal controller or internal set point follows from this descriptive slope.
"""
from collections import defaultdict
import math
import numpy as np
from . import states_v2 as states


def sufficient(rows, nuisance, *, shuffle_seed=None):
    """Equal writers, sessions within writers, menus within sessions, offers within menus."""
    nuisance = np.asarray(nuisance, float)
    if nuisance.ndim != 2 or len(nuisance) != len(rows) or not np.isfinite(nuisance).all():
        raise ValueError("invalid nuisance matrix")
    if not rows:
        raise ValueError("empty protection support")
    writers = sorted({r["writer"] for r in rows})
    sessions = defaultdict(set)
    menus = defaultdict(set)
    offers = defaultdict(int)
    for row in rows:
        sessions[row["writer"]].add(row["session"])
        menus[(row["writer"], row["session"])].add(row["key"])
        offers[(row["writer"], row["session"], row["key"])] += 1
    weights = np.array([1 / (len(sessions[r["writer"]]) * len(menus[(r["writer"], r["session"])])
                                * offers[(r["writer"], r["session"], r["key"])]) for r in rows])
    drift = np.array([r["topic_drift"] for r in rows], float)
    y = np.array([r["protected"] for r in rows], float)
    if not np.isfinite(drift).all() or not set(y) <= {0., 1.}:
        raise ValueError("invalid protection input")
    if shuffle_seed is not None:
        rng = np.random.default_rng(shuffle_seed)
        for writer in writers:
            ids = np.array([i for i, r in enumerate(rows) if r["writer"] == writer])
            drift[ids] = rng.permutation(drift[ids])
    scale = nuisance.std(0)
    scale = np.where(scale > 1e-12, scale, 1.)
    nuisance = (nuisance - nuisance.mean(0)) / scale
    x = np.c_[drift, nuisance]
    moments = []
    for writer in writers:
        ids = np.array([i for i, r in enumerate(rows) if r["writer"] == writer])
        w = weights[ids]
        if not np.isclose(w.sum(), 1.):
            raise ValueError("writer weight does not sum to one")
        xx = x[ids] - w @ x[ids]
        yy = y[ids] - w @ y[ids]
        moments.append(dict(writer=writer, gram=(xx.T @ (w[:, None] * xx)).tolist(),
                            rhs=(xx.T @ (w * yy)).tolist(), rows=len(ids), sessions=len(sessions[writer])))
    return moments


def fit_moments(gram, rhs):
    gram, rhs = np.asarray(gram, float), np.asarray(rhs, float)
    if gram.shape != (len(rhs), len(rhs)) or not np.isfinite(gram).all() or not np.isfinite(rhs).all():
        raise ValueError("invalid least-squares moments")
    eigenvalues, axes = np.linalg.eigh((gram + gram.T) / 2)
    tol = max(float(eigenvalues[-1]), 1.) * 1e-10
    active = eigenvalues > tol
    if not np.any(active) or np.linalg.norm(axes[0, ~active]) > 1e-7:
        raise ValueError("topic drift unidentified beyond controls")
    beta = axes[:, active] @ ((axes[:, active].T @ rhs) / eigenvalues[active])
    residual = float(np.max(np.abs(gram @ beta - rhs)))
    if residual > 1e-7 * max(1., float(np.max(np.abs(rhs)))):
        raise ValueError("least-squares certificate failed")
    return float(beta[0]), dict(rank=int(active.sum()), columns=len(rhs), normal_equation_gap=residual)


def fit_draw(moments, multiplicity=None):
    if len(moments) < 2:
        raise ValueError("fewer than two supported writers")
    multiplicity = np.ones(len(moments)) if multiplicity is None else np.asarray(multiplicity)
    grams = np.array([r["gram"] for r in moments])
    rhs = np.array([r["rhs"] for r in moments])
    return fit_moments(np.einsum("i,ijk->jk", multiplicity, grams), multiplicity @ rhs)


def summarize(point, draws, invalid=0):
    if point is None or invalid or not len(draws):
        return dict(effect=point, state="invalid", ci95=None, invalid_bootstrap=int(invalid))
    low, high = np.quantile(draws, [.025, .975]).tolist()
    se = float(np.std(draws, ddof=1))
    z = point / se if se > 0 else None
    return dict(effect=point, ci95=[low, high], standard_error=se, z=z,
        p_approx=math.erfc(abs(z) / math.sqrt(2)) if z is not None else None,
        p_method="two-sided normal-reference Wald approximation; descriptive, not permutation p",
        state=states.contrast_state(point, low, high), invalid_bootstrap=0,
        unit="probability change per unit paragraph-to-suggestion cosine distance")
