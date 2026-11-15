"""Bounded coefficient-level TR2 engineering worlds, not source qualification.

DESIGN CHECK: orthogonal true coefficients and orthogonal half-errors make the
three target correlations analytically attainable. Zero true variance must not
produce a stability claim. No corpus, source roster or human value is read.
"""
from __future__ import annotations

import math
import os


def vectors(target):
    # Six distinct Walsh columns on 32 rows: zero means and exact orthogonality.
    columns = [[1. if (row & mask).bit_count() % 2 else -1. for row in range(32)]
               for mask in range(1, 7)]
    x, y, e1, e2, e3, e4 = columns
    left_true = x if target is not None else [0.] * 32
    right_true = [target*a + math.sqrt(1-target*target)*b for a, b in zip(x, y)] if target is not None else [0.] * 32
    halves = [[t+e for t, e in zip(truth, error)]
              for truth, error in ((left_true, e1), (left_true, e2), (right_true, e3), (right_true, e4))]
    values = [[(a+b)/2 for a, b in zip(halves[i], halves[i+1])] for i in (0, 2)]
    return values, halves


def reference(target, method):
    """Scalar raw-moment oracle independent of TR1's array implementation."""
    values, halves = vectors(target)
    def covariance(a, b):
        n = len(a)
        return (sum(x*y for x, y in zip(a, b)) - sum(a)*sum(b)/n)/(n-1)
    def correlation(a, b):
        return covariance(a, b)/math.sqrt(covariance(a, a)*covariance(b, b))
    observed = [covariance(v, v) for v in values]
    reliabilities = []
    for side in range(2):
        if method == 'sampling':
            reliabilities.append((observed[side] - .5*32/31)/observed[side])
        else:
            r = correlation(halves[2*side], halves[2*side+1])
            reliabilities.append(2*r/(1+r))
    true = [v*r for v, r in zip(observed, reliabilities)]
    raw = correlation(*values)
    return dict(status='ok' if min(reliabilities) > 0 else 'nonpositive_reliability',
                raw_correlation=raw, reliabilities=reliabilities, true_variances=true,
                minimum_true_variance=min(true),
                stability=raw/math.sqrt(math.prod(reliabilities)) if min(reliabilities) > 0 else None,
                method=method,
                **({} if min(reliabilities) > 0 else {'reason': 'corrected between-person variance is not positive'}))


def production(target, method):
    for key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[key] = '2'
    import numpy as np
    from .week5_tr1_math import stability
    values, halves = vectors(target)
    table = dict(coefficient=np.zeros((64, 2)), sampling_variance=np.zeros((64, 2)),
                 half=np.zeros((64, 2, 2)))
    table['coefficient'][:, 1] = np.asarray(values).reshape(-1)
    table['sampling_variance'][:, 1] = .5*32/31
    table['half'][:32, :, 1] = np.asarray(halves[:2]).T
    table['half'][32:, :, 1] = np.asarray(halves[2:]).T
    return stability(table, np.arange(32), np.arange(32, 64), np.ones(32), method)


def run(independent=False):
    estimate = reference if independent else production
    cases = {str(target): {method: estimate(target, method) for method in ('sampling', 'split_half')}
             for target in (0., .5, 1.)}
    no_variance = {method: estimate(None, method) for method in ('sampling', 'split_half')}
    for target, methods in cases.items():
        for result in methods.values():
            if result['status'] != 'ok' or abs(result['stability'] - float(target)) > 1e-12:
                raise ValueError('Hand-known coefficient correction failed')
    if any(r['stability'] is not None or r['minimum_true_variance'] > 0 for r in no_variance.values()):
        raise ValueError('No-variance world falsely admits stability')
    return dict(card='TR2', result_kind='constructed_coefficient_fixture', by_construction=True,
                source_kind='constructed', cases=cases, no_true_variance=no_variance,
                clusters=32, bootstrap_draws=0, human_outcomes_loaded=False,
                human_inference_computed=False, production_adapter_implemented=False,
                scientific_admission=False,
                qualification_scope='exact coefficient algebra only; source sampling/noise models remain unqualified')
