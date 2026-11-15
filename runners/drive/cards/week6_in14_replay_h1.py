"""Isolated exact FWL reference for IN14; unchanged V1 dense solver is authoritative.

DESIGN CHECK: a sufficient, conservative singular bound selects computation only.
All unproven cases use V1 rcond=1e-11; no support rule or outcome threshold changes.
"""
import numpy as np
from . import week6_in14_math_v1 as original

RCOND = 1e-11
FAST_RATIO = 1e-6


def dense(panel, counts):
    """Retain the actual old solver, including rank and unsupported dispositions."""
    return original.fit(panel, counts, independent=True)


def project_block(a, b):
    """Orthogonally remove a writer intercept without production demeaning."""
    n = len(b)
    if n == 0:
        raise ValueError('Empty writer block')
    u = np.ones(n) / np.sqrt(n)
    v = u.copy(); v[0] += 1.
    divisor = float(v @ v)
    transformed_x = a - np.outer(v, (2. / divisor) * (v @ a))
    transformed_y = b - v * ((2. / divisor) * (v @ b))
    return {'x': transformed_x[1:], 'y': transformed_y[1:], 'n': n,
            'mean': -transformed_x[0] / np.sqrt(n),
            'raw_x_squared': float(np.sum(a * a))}


def projected_blocks(panel):
    """Ephemeral cache for this freshly prepared panel; never a saved checkpoint."""
    identity = tuple((k, id(a), id(b), a.shape, b.shape)
                     for k, a, b in panel['raw_blocks'])
    saved = panel.get('_h1_reference_cache')
    if saved is not None and saved['identity'] == identity:
        return saved['blocks']
    result = {}
    for key, a, b in panel['raw_blocks']:
        # design() created these private copies. Protect the cache's raw inputs
        # against ordinary in-place mutation; replacement triggers a fresh cache.
        a.flags.writeable = False; b.flags.writeable = False
        value = project_block(a, b)
        for name in ('x', 'y', 'mean'):
            value[name].flags.writeable = False
        result[key] = value
    panel['_h1_reference_cache'] = {'identity': identity, 'blocks': result}
    return result


def rank_certificate(x, selected, p):
    """Lower/upper singular bound in the ORIGINAL augmented column units.

    A=[Z,D]T; T=[[I,0],[C,I]], and Z.T D=0. Thus
    smin(A)>=min(smin(Z),min(sqrt(w*n)))/(1+||C||F), smax(A)<=||A||F.
    The normalized reflector does not normalize the old dummy columns.
    """
    singular = np.linalg.svd(x, compute_uv=False)
    if len(singular) < p or p == 0:
        return 0., 0., 0.
    means_squared = sum(float(v['mean'] @ v['mean']) for _, v in selected)
    augmented_squared = sum(w * (v['raw_x_squared'] + v['n']) for w, v in selected)
    minimum_dummy = min(np.sqrt(w * v['n']) for w, v in selected)
    lower = min(float(singular[-1]), minimum_dummy) / (1. + np.sqrt(means_squared))
    upper = np.sqrt(augmented_squared)
    ratio = lower / upper if upper > 0 else 0.
    return float(lower), float(upper), float(ratio)


def fit(panel, counts=None, diagnostics=None):
    """Same answers as the dense reference, with a provably safe-rank fast path."""
    trace = diagnostics if diagnostics is not None else {}
    trace.clear()

    def fallback(reason):
        trace.update(path='dense', reason=reason)
        return dense(panel, counts)

    if panel is None:
        return fallback('no eligible rows')
    counts = dict.fromkeys(panel['keys'], 1) if counts is None else counts
    keys = [(k, int(counts.get(k, 0))) for k, _, _ in panel['raw_blocks']
            if counts.get(k, 0) > 0]
    if not keys:
        return fallback('no sampled writers')
    p = len(panel['terms']); reason = None
    try:
        cache = projected_blocks(panel)
        selected = [(w, cache[k]) for k, w in keys]
        x = np.vstack([v['x'] * np.sqrt(w) for w, v in selected])
        y = np.concatenate([v['y'] * np.sqrt(w) for w, v in selected])
        if not np.isfinite(x).all() or not np.isfinite(y).all():
            reason = 'nonfinite projected system'
        else:
            lower, upper, ratio = rank_certificate(x, selected, p)
            trace.update(projected_shape=list(x.shape), selected_writers=len(keys),
                         lower_singular_bound=lower, upper_singular_bound=upper,
                         bound_ratio=ratio)
            # Frozen before fixtures: 100,000 times original rcond. This strict
            # rule changes computation choice only, never scientific support.
            if not np.isfinite([lower, upper, ratio]).all() or ratio <= FAST_RATIO:
                reason = 'augmented rank not conservatively proven'
            else:
                beta, _, rank, _ = np.linalg.lstsq(x, y, rcond=RCOND)
                if rank != p or not np.isfinite(beta).all():
                    reason = 'projected solve did not certify a finite full-rank answer'
    except (np.linalg.LinAlgError, ValueError, FloatingPointError):
        reason = 'projected construction or solve failed'
    if reason is not None:
        return fallback(reason)
    trace['path'] = 'projected'
    answer = dict(zip(panel['terms'], map(float, beta)))
    if 'prompt' in answer and 'same_valence' in answer:
        answer['shape_minus_mood'] = answer['prompt'] - answer['same_valence']
    return answer, None
