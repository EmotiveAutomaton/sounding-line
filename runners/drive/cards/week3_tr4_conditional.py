"""Separate TR4.h1 conditional temporal-order control; original stays immutable.

DESIGN CHECK: LESSONS 3-5, TR4.ic correction and CONTROLS 5-7 reread 2026-10-29.
NULL is joint invariance within writer/prompt/count cells, not zero mean gain.
ALTERNATIVE is useful within-cell temporal order. Rank and positive gain both
must pass; absent movable support is unsupported, never a selected population.
"""
from collections import defaultdict
import numpy as np
from . import week3_tr4_comparison as parent

SEED = 20261029


def cells(group):
    pools = defaultdict(list)
    for i, (row, counts) in enumerate(zip(group['rows'], group['data'])):
        total = int(counts.sum())
        if total:
            pools[(row['prompt'], total)].append(i)
    return list(pools.values())


def movable(group):
    return any(len(np.unique(group['data'][indices], axis=0)) > 1
               for indices in cells(group))


def shuffle(group, rng):
    data = group['data'].copy()
    for indices in cells(group):
        data[indices] = group['data'][rng.permutation(indices)]
    return data


def probability(observed, reference):
    reference = np.asarray(reference, float)
    if reference.size < 1 or not np.isfinite(reference).all() or not np.isfinite(observed):
        raise ValueError('finite statistic and nonempty reference required')
    # Conservative numerical ties, including exact identity/duplicate draws.
    exceed = (reference >= observed) | np.isclose(reference, observed, rtol=1e-12, atol=1e-12)
    return float((1 + np.count_nonzero(exceed)) / (len(reference) + 1))


def analyze(census, repetitions=200, bootstraps=2000, progress=None):
    if min(repetitions, bootstraps) < 1:
        raise ValueError('positive draw counts required')
    groups, retained = parent.prepare(census)
    test = [g for g in groups if g['half'] == 'test' and g['mask'].any()]
    measured = [dict(writer=g['writer'], movable=movable(g), **parent.primary(g)) for g in test]
    gains = np.asarray([r['gain'] for r in measured])
    estimate = float(gains.mean()) if len(gains) else None
    rng = np.random.default_rng(SEED)
    reference = []
    for i in range(repetitions):
        values = [parent.primary(g, shuffle(g, rng))['gain'] for g in test]
        reference.append(float(np.mean(values)) if values else float('nan'))
        if progress:
            progress('conditional-reference', i + 1, repetitions)
    rng = np.random.default_rng(SEED + 1)
    boot = [float(gains[rng.integers(len(gains), size=len(gains))].mean())
            for _ in range(bootstraps)] if len(gains) >= 2 else [float('nan')] * bootstraps
    uncertainty = parent.distribution(boot)
    distribution = parent.distribution(reference)
    n_movable = sum(r['movable'] for r in measured)
    supported = n_movable >= 3 and uncertainty['supported'] and distribution['supported']
    p = probability(estimate, reference) if estimate is not None and distribution['supported'] else None
    legacy = (abs(distribution['mean']) > .25 * distribution['sd']) if distribution['supported'] else None
    status = ('unsupported' if not supported else
              'positive_conditional_order' if uncertainty['interval'][0] > 0 and p < .05 else
              'negative_forecast_advantage' if uncertainty['interval'][1] < 0 else 'not_detected')
    return dict(primary=dict(estimate=estimate, probability=p, bootstrap=uncertainty,
                             reference=distribution, legacy_zero_center_flag=legacy,
                             writers=len(test), movable_writers=n_movable, status=status),
                writer_losses=measured, retained=retained,
                reference=[parent.finite(v) for v in reference],
                counts=dict(all_sessions=len(retained), all_writers=len(groups),
                            scoreable_test_sessions=sum(r['sessions'] for r in measured)),
                scientific_admission=False, descriptive=True,
                scope='Conditional temporal-order comparison; not preference age or current endorsement; original reliability remains unchanged')
