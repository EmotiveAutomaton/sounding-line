"""Additive IN16 REML numerical repair candidate; not yet qualified.

DESIGN CHECK: LESSONS 3/4/5, CONTROLS 6/7. Exact balanced REML and zero
worlds, direct covariance replay, weighted duplicate writers and constant
response shifts must agree at the existing 1e-7 tolerance. This changes the
numerical optimum calculation only, never the source, model or acceptance bar.
"""
import math
import numpy as np
from scipy.optimize import brentq, minimize_scalar
from . import week6_in16_math_v1 as frozen

fixed_table = frozen.fixed_table
matrix = frozen.matrix
prepare = frozen.prepare
clearing = frozen.clearing


def profile(blocks, p, log_ratio, independent=False):
    """Return the original profiled REML objective and its analytic derivative.

    t=log(1+lambda), V=I+lambda*11', D=dV/dt=exp(t)*11'.
    F=log|V|+log|X'V^-1 X|+(n-p)*log(r'V^-1 r/(n-p)).
    F'=tr(V^-1 D)-tr(A^-1 X'V^-1 D V^-1 X)
       -(n-p)*(r'V^-1 D V^-1 r)/(r'V^-1 r).
    Each bootstrap multiplicity counts an independent copy of its writer.
    """
    ratio = float(np.expm1(log_ratio)); derivative = float(np.exp(log_ratio))
    n = sum(w*b['n'] for b, w in blocks)
    a = np.zeros((p, p)); rhs = np.zeros(p)
    derivative_a = np.zeros((p, p)); logdet_parts = []; trace_parts = []
    work = []
    for block, weight in blocks:
        size = block['n']; x = block['x']; y = block['y']
        if independent:
            covariance = np.eye(size)+ratio*np.ones((size, size))
            d_covariance = derivative*np.ones((size, size))
            inverse_x = np.linalg.solve(covariance, x)
            inverse_y = np.linalg.solve(covariance, y)
            a += weight*(x.T@inverse_x)
            rhs += weight*(x.T@inverse_y)
            derivative_a += weight*(inverse_x.T@d_covariance@inverse_x)
            logdet_parts.append(weight*float(np.linalg.slogdet(covariance)[1]))
            trace_parts.append(weight*float(np.trace(np.linalg.solve(covariance, d_covariance))))
            work.append((block, weight, covariance, d_covariance))
        else:
            denominator = 1.+size*ratio
            shrink = ratio/denominator
            a += weight*(block['xx']-shrink*np.outer(block['sx'], block['sx']))
            rhs += weight*(block['xy']-shrink*block['sx']*block['sy'])
            derivative_a += weight*derivative*np.outer(block['sx'], block['sx'])/denominator**2
            logdet_parts.append(weight*float(np.log1p(size*ratio)))
            trace_parts.append(weight*size*derivative/denominator)
            work.append((block, weight, denominator, None))
    if n <= p or np.linalg.matrix_rank(a, tol=1e-9) != p:
        return float('inf'), float('nan')
    sign, determinant = np.linalg.slogdet(a)
    if sign <= 0:
        return float('inf'), float('nan')
    beta = np.linalg.solve(a, rhs)
    residual_parts = []; derivative_residual_parts = []
    for block, weight, operator, d_covariance in work:
        residual = block['y']-block['x']@beta
        if independent:
            inverse_residual = np.linalg.solve(operator, residual)
            residual_parts.append(weight*float(residual@inverse_residual))
            derivative_residual_parts.append(weight*float(inverse_residual@d_covariance@inverse_residual))
        else:
            # Orthogonal within-writer deviations plus the mean avoid subtracting
            # two large fitted sums of squares. This equals r'V^-1 r exactly.
            mean = float(residual.mean()); centered = residual-mean
            residual_parts.append(weight*(float(centered@centered)+block['n']*mean*mean/operator))
            derivative_residual_parts.append(weight*derivative*(block['n']*mean/operator)**2)
    residual_ss = math.fsum(residual_parts)
    if not np.isfinite(residual_ss) or residual_ss <= 1e-12:
        return float('inf'), float('nan')
    objective = math.fsum(logdet_parts)+float(determinant)+(n-p)*math.log(residual_ss/(n-p))
    score = (math.fsum(trace_parts)-float(np.trace(np.linalg.solve(a, derivative_a)))
             -(n-p)*math.fsum(derivative_residual_parts)/residual_ss)
    return float(objective), float(score)


def polish(evaluate, seed):
    """Refine only the bounded optimizer's local minimum, refusing unknowns.

    A bounded expanding derivative bracket stays within 0.01 log-ratio units
    of the original optimum. No basin-wide replacement or tolerances are added.
    """
    if not np.isfinite(seed) or not 0. <= seed <= 12.:
        return None, 'nonfinite or out-of-range REML seed'
    for radius in (2e-6, 4e-6, 8e-6, 1.6e-5, 3.2e-5, 6.4e-5,
                   1.28e-4, 2.56e-4, 5.12e-4, .001024, .002048, .004096, .008192, .01):
        left = max(0., seed-radius); right = min(12., seed+radius)
        _, lo = evaluate(left); _, hi = evaluate(right)
        if not np.isfinite(lo) or not np.isfinite(hi):
            return None, 'nonfinite REML derivative bracket'
        if lo <= 0. <= hi:
            try:
                root, result = brentq(lambda value: evaluate(value)[1], left, right,
                                     xtol=1e-12, rtol=4*np.finfo(float).eps,
                                     maxiter=100, full_output=True, disp=False)
            except (ValueError, RuntimeError):
                return None, 'REML derivative root failed'
            if not result.converged or not np.isfinite(root):
                return None, 'REML derivative root failed'
            return float(root), None
        if left == 0. and lo >= 0. and hi >= 0.:
            return 0., None
        if right == 12. and lo <= 0. and hi <= 0.:
            return None, 'REML optimum reached fixed upper bracket'
    return None, 'REML derivative minimum unbracketed near original optimum'


def writer_share(panel, counts, independent=False):
    if panel is None:
        return None, 'no writer-share support'
    blocks = [(b, int(counts.get(b['key'], 0))) for b in panel['blocks'] if counts.get(b['key'], 0)>0]
    n = sum(w*b['n'] for b, w in blocks); p = panel['p']
    if len(blocks)<2 or n<=p:
        return None, 'fewer than two independent writers or residual degrees of freedom'
    evaluate = lambda value: profile(blocks, p, value, independent)
    fit = minimize_scalar(lambda value: evaluate(value)[0], bounds=(0., 12.), method='bounded',
                          options={'xatol': 1e-9, 'maxiter': 200})
    if not fit.success or not np.isfinite(fit.fun):
        return None, 'REML failed or rank deficient'
    optimum, reason = polish(evaluate, float(fit.x))
    if reason:
        return None, reason
    zero = evaluate(0.)[0]; candidate = evaluate(optimum)[0]
    if not np.isfinite(candidate):
        return None, 'nonfinite polished REML objective'
    optimum = 0. if zero <= candidate+1e-9 else optimum
    if optimum >= 12.-1e-5:
        return None, 'REML optimum reached fixed upper bracket'
    return float(-np.expm1(-optimum)), None


def evaluate(prepared, counts, independent=False):
    values = {}; failures = {}
    for name, function in [('clearing', clearing), ('writer_share', writer_share)]:
        panel = prepared['clearing' if name=='clearing' else 'share']
        try:
            value, reason = function(panel, counts.get(name, counts), independent)
        except np.linalg.LinAlgError:
            value, reason = None, 'numerical linear algebra failure'
        values[name] = value
        if reason:
            failures[name] = reason
    values['clearing_per_N_SD'] = None if values['clearing'] is None else values['clearing']*prepared['N_writer_SD']
    return {'value': values, 'failures': failures}
