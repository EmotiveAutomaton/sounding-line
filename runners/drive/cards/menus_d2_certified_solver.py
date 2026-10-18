"""Bounded numerical refinement of the unchanged D2 convex choice objective.

DESIGN CHECK 2026-10-18: LESSONS 3-5, CONTROLS and D2 canonical contract.
NULL: uniform balanced choices have zero coefficients. ALTERNATIVE: a planted
choice rule is recovered. Invalid/nonfinite fits still fail; neither labels nor
the original 1e-6 gradient certificate change. Previously certified fits return
byte-identical values. Only an uncertified original solve enters bounded Newton
refinement, with an exact Hessian and objective-decreasing backtracking.
"""
import numpy as np
from . import menus_d2 as old


def hessian(beta, data, penalty):
    x, sizes, starts, _ = data
    z = x @ beta
    ez = np.exp(z - np.repeat(np.maximum.reduceat(z, starts), sizes))
    prob = ez / np.repeat(np.add.reduceat(ez, starts), sizes)
    means = np.add.reduceat(prob[:, None] * x, starts, axis=0)
    return ((x.T @ (prob[:, None] * x) - means.T @ means) / len(sizes)
            + penalty * np.eye(x.shape[1]))


def refine(data, penalty, beta, original_iterations=0):
    if not np.isfinite(penalty) or penalty <= 0:
        raise ValueError('Positive finite original penalty required')
    beta = np.array(beta, dtype=float, copy=True)
    initial_loss, _ = old.objective(beta, data, penalty)
    for iteration in range(51):
        loss, gradient = old.objective(beta, data, penalty)
        if not np.isfinite(loss) or not np.isfinite(gradient).all():
            raise ValueError('Nonfinite choice objective or gradient')
        gap = float(np.max(np.abs(gradient)))
        if gap <= 1e-8:
            return beta, dict(objective=loss, gradient_max=gap,
                iterations=original_iterations + iteration,
                refinement='exact_hessian_newton_v1', refinement_steps=iteration,
                initial_objective=initial_loss, original_gradient_limit=1e-6)
        if iteration == 50:
            break
        step = np.linalg.solve(hessian(beta, data, penalty), gradient)
        descent = float(gradient @ step)
        if not np.isfinite(step).all() or descent <= 0:
            raise ValueError('Uncertified Newton descent')
        for shrink in range(40):
            rate = 2.0 ** -shrink
            candidate = beta - rate * step
            new_loss, _ = old.objective(candidate, data, penalty)
            if np.isfinite(new_loss) and new_loss <= loss - 1e-4 * rate * descent:
                beta = candidate
                break
        else:
            raise ValueError('Choice refinement line search exhausted')
    raise ValueError('Choice refinement iteration bound exhausted')


def fit(data, penalty):
    try:
        return old.fit(data, penalty)
    except ValueError as exc:
        if not str(exc).startswith('uncertified choice fit:'):
            raise
    # Repeat the exact original solve to retain its candidate without changing
    # the original implementation or any other card that imports it.
    result = old.minimize(old.objective, np.zeros(data[0].shape[1]),
        args=(data, penalty), jac=True, method='L-BFGS-B',
        options=dict(maxiter=2000, ftol=1e-13, gtol=1e-8))
    return refine(data, penalty, result.x, int(result.nit))
