"""Compiled scalar oracle; independent Newton solver remains in the frozen V3 code.

DESIGN CHECK: LESSONS 3-5. Explicit scalar sums and centered moments must match
the preserved Python oracle on null, signed, ragged and invalid constructed
inputs. No fast-math, parallel reduction, primary likelihood or source sampling.
"""
import math
import types
import numpy as np
from numba import njit
from . import week6_ch14_math_v3 as original


@njit(cache=False, fastmath=False)
def scalar_sum(values):
    # Non-overlapping partials retain low-order terms. The final correction
    # handles a same-signed remaining tail at a half-even rounding boundary.
    partials = np.empty(len(values), dtype=np.float64)
    count = 0
    for value in values:
        x = value
        used = 0
        for index in range(count):
            y = partials[index]
            if abs(x) < abs(y):
                x, y = y, x
            high = x + y
            low = y - (high - x)
            if low != 0.:
                partials[used] = low
                used += 1
            x = high
        partials[used] = x
        count = used + 1
    if not count:
        return 0.
    high = partials[count - 1]
    count -= 1
    low = 0.
    while count:
        x = high
        y = partials[count - 1]
        count -= 1
        high = x + y
        low = y - (high - x)
        if low != 0.:
            break
    if count and ((low < 0. and partials[count - 1] < 0.) or
                  (low > 0. and partials[count - 1] > 0.)):
        y = low * 2.
        x = high + y
        if y == x - high:
            high = x
    return high


@njit(cache=False, fastmath=False)
def scalar_kernel(x, starts, selected, beta, weights, total, need_hessian):
    n = len(starts)
    p = len(beta)
    ll = np.empty(n, dtype=np.float64)
    gradient = np.zeros(p, dtype=np.float64)
    information = np.zeros((p, p), dtype=np.float64)
    products = np.empty(p, dtype=np.float64)
    for i in range(n):
        begin = starts[i]
        end = starts[i + 1] if i + 1 < n else len(x)
        length = end - begin
        utility = np.empty(length, dtype=np.float64)
        terms = np.empty(length, dtype=np.float64)
        for k in range(length):
            for j in range(p):
                products[j] = x[begin + k, j] * beta[j]
            utility[k] = scalar_sum(products)
        peak = np.max(utility)
        for k in range(length):
            terms[k] = math.exp(utility[k] - peak)
        denominator = scalar_sum(terms)
        probability = terms / denominator
        ll[i] = utility[selected[i] - begin] - peak - math.log(denominator)
        expected = np.empty(p, dtype=np.float64)
        for j in range(p):
            for k in range(length):
                terms[k] = probability[k] * x[begin + k, j]
            expected[j] = scalar_sum(terms)
            gradient[j] += weights[i] * (x[selected[i], j] - expected[j])
        if need_hessian:
            for k in range(length):
                weight = weights[i] * probability[k]
                for j in range(p):
                    for q in range(p):
                        outer = (x[begin + k, j] - expected[j]) * (x[begin + k, q] - expected[q])
                        information[j, q] += weight * outer
    return ll, gradient / total, information / total


def likelihood(data, beta, weights, reference=False, need_hessian=False):
    if not reference:
        return original.likelihood(data, beta, weights, False, need_hessian)
    if not len(data['starts']):
        return None
    w = np.asarray(weights, float)[data['person']]
    total = float(w.sum())
    if not total:
        return None
    return scalar_kernel(data['x'], data['starts'], data['selected'],
                         np.asarray(beta, float), w, total, need_hessian)


# Bind the unchanged solver and comparison bytecode to an isolated namespace.
# Never mutate the original module or its globals, which historical runs pin.
_scope = dict(vars(original), likelihood=likelihood)
fit = types.FunctionType(original.fit.__code__, _scope, 'fit', original.fit.__defaults__)
_scope['fit'] = fit
draw = types.FunctionType(original.draw.__code__, _scope, 'draw', original.draw.__defaults__)
prepare = original.prepare
model_sets = original.model_sets
result = original.result
