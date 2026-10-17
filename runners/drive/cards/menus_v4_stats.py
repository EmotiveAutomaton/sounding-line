"""Laplace marginal-likelihood random-coefficient logistic readers for V4.

The stipulated asymptotic references are diagnostics, not an assertion of
conservative size after direction/reader selection. V4's independent 20-world
session-identity permutation size check is compulsory.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit, logit
from scipy.stats import chi2


def conditional_mode(x, y, offset, variance):
    root = np.sqrt(variance); design = x * root
    a = np.zeros(x.shape[1])
    def objective(value):
        eta = offset + design @ value
        return float(np.sum(np.logaddexp(0., eta) - y * eta) + .5 * value @ value)
    for _ in range(100):
        eta = offset + design @ a; p = expit(eta)
        gradient = design.T @ (p - y) + a
        hessian = np.eye(len(a)) + design.T @ ((p * (1 - p))[:, None] * design)
        if np.max(np.abs(gradient), initial=0.) < 1e-7:
            break
        step = np.linalg.solve(hessian, gradient)
        # A Newton decrement certifies local objective error even where a large
        # design scale makes the raw gradient sensitive to floating point noise.
        if gradient @ step < 1e-14:
            break
        old = objective(a); scale = 1.
        while scale > 1e-10:
            candidate = a - scale * step
            if objective(candidate) <= old + 1e-12 - 1e-4 * scale * (gradient @ step):
                a = candidate; break
            scale *= .5
        else:
            raise ValueError("random-coefficient conditional mode did not descend")
    else:
        raise ValueError("random-coefficient conditional mode did not converge")
    eta = offset + design @ a; p = expit(eta)
    hessian = np.eye(len(a)) + design.T @ ((p * (1 - p))[:, None] * design)
    sign, logdet = np.linalg.slogdet(hessian)
    if sign != 1 or not np.isfinite(logdet):
        raise ValueError("invalid conditional Hessian")
    return -objective(a) - .5 * logdet, root * a


def variance_reader(x, truth, population_accept, writers, maxiter=100):
    x = np.asarray(x, float); y = np.asarray(truth, float); p = np.asarray(population_accept, float)
    writers = np.asarray(writers)
    if x.ndim != 2 or len(x) != len(y) or len(y) != len(p) or len(p) != len(writers) or not len(y):
        raise ValueError("invalid random-coefficient support")
    if not np.isfinite(x).all() or not np.all((y == 0) | (y == 1)) or not np.all((p > 0) & (p < 1)):
        raise ValueError("invalid random-coefficient values")
    # Variance optimization is invariant to predictor units. RMS scaling avoids
    # making a slow-decay kernel's naturally small amplitude a numerical bound.
    scale = np.sqrt(np.mean(x * x, axis=0)); scale[scale < 1e-12] = 1.
    x = x / scale
    names = sorted(set(writers)); groups = [np.flatnonzero(writers == name) for name in names]
    offset = logit(p)
    null_ll = float(np.sum(y * offset - np.logaddexp(0., offset)))
    def objective(variance):
        return -sum(conditional_mode(x[ids], y[ids], offset[ids], variance)[0] for ids in groups)
    k = x.shape[1]
    candidates = [(float(-null_ll), np.zeros(k), "exact_zero")]
    certificates = []
    for start in (.04, 1.):
        fit = minimize(objective, np.full(k, start), method="L-BFGS-B", bounds=[(0., None)] * k,
                       options=dict(maxiter=maxiter, ftol=1e-10, gtol=1e-5, maxls=40))
        certificates.append(dict(start=start, success=bool(fit.success), message=str(fit.message), objective=float(fit.fun)))
        if fit.success and np.isfinite(fit.fun) and np.isfinite(fit.x).all():
            candidates.append((float(fit.fun), fit.x, "optimized"))
    if len(candidates) == 1 and any(row["objective"] < -null_ll - 1e-8 for row in certificates):
        raise ValueError("better variance solution lacks an interior convergence certificate")
    if not any(row["success"] for row in certificates):
        raise ValueError("no certified variance optimization")
    value, variance, selected = min(candidates, key=lambda row: row[0])
    likelihood_ratio = max(0., 2 * (-value - null_ll))
    pvalue = 1. if likelihood_ratio == 0 else float((.5 if k == 1 else 1.) * chi2.sf(likelihood_ratio, k))
    coefficients = {str(name): (conditional_mode(x[ids], y[ids], offset[ids], variance)[1] / scale).tolist()
                    for name, ids in zip(names, groups)}
    return dict(variance=(variance / scale ** 2).tolist(), numerical_rms_scale=scale.tolist(), coefficients=coefficients, likelihood_ratio=likelihood_ratio,
                p_value=pvalue, detected=pvalue < .05, null_log_likelihood=null_ll,
                fitted_log_likelihood=-value, selected=selected, dimensions=k,
                reference="50:50 chi-square_0/chi-square_1" if k == 1 else f"chi-square_{k}",
                certificates=certificates, method="Laplace marginal likelihood; centered normal writer coefficients")


def predict(reader, x, population, writers):
    q = np.asarray(population, float).copy()
    shifts = np.asarray([np.asarray(row) @ reader["coefficients"].get(str(writer), np.zeros(x.shape[1]))
                         for row, writer in zip(x, writers)])
    accept = expit(logit(q[:, 0]) + shifts)
    q[:, 1:] *= ((1 - accept) / (1 - q[:, 0]))[:, None]
    q[:, 0] = accept
    return q


def taste_directions(features, truth, population_accept, writers, train, dimensions):
    """Shared directions estimated on early training only, never scored tail."""
    x = np.asarray(features, float); y = np.asarray(truth, float); p = np.asarray(population_accept, float)
    writer = np.asarray(writers); train = np.asarray(train, bool)
    moment = np.zeros((x.shape[1], x.shape[1]))
    for name in sorted(set(writer[train])):
        ids = np.flatnonzero(train & (writer == name))
        score = x[ids].T @ (y[ids] - p[ids])
        noise = x[ids].T @ ((p[ids] * (1 - p[ids]))[:, None] * x[ids])
        moment += np.outer(score, score) - noise
    _, directions = np.linalg.eigh(moment)
    return directions[:, -dimensions:][:, ::-1]
