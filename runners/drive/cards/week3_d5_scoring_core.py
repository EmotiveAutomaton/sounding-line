"""D5 numerical reader, used on constructed validation only until admission.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-7 read 2026-11-01.
NULL: identical observations tie at fixed-gallery chance. ALTERNATIVE: unique
person profiles identify and signed within-writer plants reverse the slope.
Missing evidence/undefined resamples refuse or remain invalid, never redraw.
Context donor roles and probe/gallery masks remain unchanged under either law.
"""
from collections import defaultdict
import numpy as np
from .timing_pmap_stats import split_sessions
from .week3_d5_reader_cache import cosine_scores
from .week3_d5_context_support import inspect_support


def mean_rows(matrix):
    x = np.asarray(matrix, float)
    if x.ndim != 2 or not len(x) or np.isinf(x).any():
        raise ValueError('Nonempty finite-or-missing component rows required')
    count = np.isfinite(x).sum(0)
    return np.divide(np.nansum(x, axis=0), count, out=np.full(x.shape[1], np.nan), where=count > 0)


def process_scores(probes, galleries, truth):
    """Gallery-only canonical PMAP scaling with session probes, fixed gallery."""
    a, b, truth = np.asarray(probes, float), np.asarray(galleries, float), np.asarray(truth)
    if a.ndim != 2 or b.ndim != 2 or a.shape[1] != b.shape[1] or len(b) < 2 or not len(a):
        raise ValueError('Fixed nonempty probe/gallery required')
    if np.isinf(a).any() or np.isinf(b).any() or np.any(~np.isfinite(a).any(1)) or np.any(~np.isfinite(b).any(1)):
        raise ValueError('Whole missing or infinite process profile')
    if truth.shape != (len(a),) or not np.issubdtype(truth.dtype, np.integer) or (truth < 0).any() or (truth >= len(b)).any():
        raise ValueError('Fixed truth/gallery identities required')
    count = np.isfinite(b).sum(0); mean = mean_rows(b)
    # All-absent coordinates are omitted, not imputed into observed evidence.
    fill = np.where(count > 0, mean, 0.)
    aa, bb = np.where(np.isfinite(a), a, fill), np.where(np.isfinite(b), b, fill)
    scale = bb.std(0); keep = (count > 0) & (scale > 1e-12)
    aa, bb = (aa[:, keep]-fill[keep])/scale[keep], (bb[:, keep]-fill[keep])/scale[keep]
    distance = np.sum((aa[:, None, :]-bb[None, :, :])**2, axis=2)
    ties = np.isclose(distance, distance.min(1)[:, None], atol=1e-12, rtol=1e-12)
    scores = ties[np.arange(len(a)), truth]/ties.sum(1)
    return scores, dict(features=len(fill), used_features=int(keep.sum()),
        absent_gallery_features=int((count == 0).sum()), constant_gallery_features=int(((count > 0) & ~keep).sum()),
        missing_probe_cells=int((~np.isfinite(a)).sum()), missing_gallery_cells=int((~np.isfinite(b)).sum()),
        tied_probes=int((ties.sum(1) > 1).sum()))


def profile_plan(rows, folds, roster, channel, assignment=None, donor_fold=None):
    """Same eligible probes and galleries for real and context comparisons."""
    assignment = assignment or {r['session']: r['writer'] for r in rows}
    if len(set(roster)) != len(roster) or not set(roster) <= set(folds):
        raise ValueError('Fixed candidate roster required')
    independent = donor_fold is not None
    if independent and donor_fold not in (0, 1, 2):
        raise ValueError('Invalid donor rotation')
    state = inspect_support(rows, folds, roster, assignment, independent)
    rotation = state['rotations'][donor_fold if independent else 0]
    if not rotation['channels'][channel]['supported']:
        raise ValueError('Unsupported fixed real/context comparison')
    halves, _ = split_sessions(rows, assignment)
    index = {r['session']: i for i, r in enumerate(rows)}
    if len(index) != len(rows): raise ValueError('Duplicate session')
    gallery = rotation['gallery_writers']; probe_writers = rotation['probe_writers']
    from .week3_d5_gallery_support import COMPONENTS
    components = COMPONENTS[channel]
    groups = [[index[r['session']] for r in halves[w][1]] for w in gallery]
    probes = [index[r['session']] for w in probe_writers for r in halves[w][0]
              if all(r['support'][c] for c in components)]
    truth = [gallery.index(assignment[rows[i]['session']]) for i in probes]
    return dict(gallery=gallery, groups=groups, probes=probes, truth=truth,
        assignment=assignment, components=components, donor_fold=donor_fold)


def donors(rows, folds, plan, target, component, context):
    if context not in ('real', 'literal', 'independent'): raise ValueError('Unknown context mode')
    if context == 'real': return [target]
    r = rows[target]; writer = plan['assignment'][r['session']]
    if context == 'independent' and plan['donor_fold'] is None: raise ValueError('Independent donor fold required')
    result = [i for i, d in enumerate(rows) if d['prompt'] == r['prompt'] and d['support'][component]
              and (folds[plan['assignment'][d['session']]] == plan['donor_fold'] if context == 'independent'
                   else plan['assignment'][d['session']] != writer)]
    if not result: raise ValueError('Missing context donor term')
    return result


def character_weights(rows, folds, plan, component, context):
    cache = {}
    def row(i):
        r = rows[i]
        key = (i,) if context == 'real' else (r['prompt'], plan['assignment'][r['session']] if context == 'literal' else plan['donor_fold'])
        if key not in cache:
            members = donors(rows, folds, plan, i, component, context)
            value = np.zeros(len(rows)); value[members] = 1/len(members); cache[key] = value
        return cache[key]
    a = np.asarray([row(i) for i in plan['probes']])
    b = []
    for group in plan['groups']:
        selected = [i for i in group if rows[i]['support'][component]]
        if not selected: raise ValueError('Missing fixed character candidate')
        b.append(np.mean([row(i) for i in selected], axis=0))
    return a, np.asarray(b)


def process_profiles(rows, folds, plan, values, context):
    if set(values) != set(plan['components']): raise ValueError('Exact process components required')
    arrays = {c: np.asarray(values[c], float) for c in plan['components']}
    for c, x in arrays.items():
        if x.ndim != 2 or len(x) != len(rows) or np.isinf(x).any(): raise ValueError('Invalid complete process matrix')
        if any(bool(np.isfinite(x[i]).any()) != rows[i]['support'][c] for i in range(len(rows))):
            raise ValueError('Process feature/support mismatch')
    cache = {}
    def row(i, c):
        r = rows[i]
        key = (c, i) if context == 'real' else (c, r['prompt'], plan['assignment'][r['session']] if context == 'literal' else plan['donor_fold'])
        if key not in cache: cache[key] = mean_rows(arrays[c][donors(rows, folds, plan, i, c, context)])
        if not np.isfinite(cache[key]).any(): raise ValueError('Whole missing context component')
        return cache[key]
    a = np.asarray([np.concatenate([row(i, c) for c in plan['components']]) for i in plan['probes']])
    b = []
    for group in plan['groups']:
        parts = []
        for c in plan['components']:
            selected = [i for i in group if rows[i]['support'][c]]
            if not selected: raise ValueError('Missing fixed process candidate')
            parts.append(mean_rows([row(i, c) for i in selected]))
        b.append(np.concatenate(parts))
    return a, np.asarray(b)


def score_character(rows, folds, plan, kernel, valid, context='real'):
    if len(plan['components']) != 1: raise ValueError('One character component required')
    a, b = character_weights(rows, folds, plan, plan['components'][0], context)
    return cosine_scores(kernel, valid, a, b, np.asarray(plan['truth'], int))


def score_process(rows, folds, plan, values, context='real'):
    a, b = process_profiles(rows, folds, plan, values, context)
    return process_scores(a, b, np.asarray(plan['truth'], int))


def slope_terms(writers, bins, scores, roster):
    if len(writers) != len(bins) or len(bins) != len(scores) or len(set(roster)) != len(roster):
        raise ValueError('Aligned probes and fixed writer roster required')
    if not set(writers) <= set(roster) or not set(bins) <= {'0', '1', '2', '3', 'missing'}:
        raise ValueError('Unexpected writer or share bin')
    scores = np.asarray(scores, float)
    if not np.isfinite(scores).all() or (scores < 0).any() or (scores > 1).any():
        raise ValueError('Finite fractional correctness required')
    groups = defaultdict(list)
    for w, b, y in zip(writers, bins, scores):
        if b != 'missing': groups[w].append(((int(b)+.5)/4, y))
    numerator = []; denominator = []; counts = []
    for w in roster:
        if not groups[w]: numerator.append(0.);denominator.append(0.);counts.append(0);continue
        x, y = np.asarray(groups[w]).T; dx, dy = x-x.mean(), y-y.mean()
        numerator.append(float(np.mean(dx*dy)));denominator.append(float(np.mean(dx*dx)));counts.append(len(x))
    return np.asarray(numerator), np.asarray(denominator), dict(known_bin_probes=counts, missing_bin_probes=sum(b == 'missing' for b in bins), fixed_writers=len(roster))


def slope_interval(writers, bins, scores, roster, draws=2000, seed=20261026):
    n, d, support = slope_terms(writers, bins, scores, roster)
    if not len(roster) or type(draws) is not int or draws < 1: raise ValueError('Nonempty fixed bootstrap required')
    sampled = np.random.default_rng(seed).integers(len(roster), size=(draws, len(roster)))
    nn, dd = n[sampled].sum(1), d[sampled].sum(1)
    bank = np.divide(nn, dd, out=np.full(draws, np.nan), where=dd > 0)
    invalid = int((~np.isfinite(bank)).sum()); estimate = float(n.sum()/d.sum()) if d.sum() > 0 else None
    interval = list(map(float, np.quantile(bank, [.025, .975]))) if not invalid else None
    return dict(estimate=estimate, interval=interval, undefined_draws=invalid,
        draws=[None if not np.isfinite(x) else float(x) for x in bank],
        degenerate_empirical_interval=bool(interval is not None and interval[0] == interval[1]),
        state='undefined' if estimate is None else 'invalid_interval' if invalid else 'descriptive', support=support)
