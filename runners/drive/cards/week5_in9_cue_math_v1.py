"""IN9 literal-cue odds, with exact cell support and whole-writer resampling.

DESIGN CHECK: zero cells remain unsupported; no pseudocount, clipping or redraw.
Independent replay uses row weights and conditional label odds, not cell products.
These directed secondaries have no newly invented practical bar or verdict.
"""
import math
import numpy as np

SEED = 20261113
FAMILIES = ('VICTIM', 'AUDIENCE', 'ANGRY_AT_ME', 'LAUGHED_AT')


def cells(labels, presence, weights, independent=False):
    if independent:
        answer = [0, 0, 0, 0]
        for label, hit, count in zip(labels, presence, weights):
            index = (0 if hit else 2) + (0 if label else 1)
            answer[index] += int(count)
        return answer
    return [int(weights[(labels == label) & (presence == hit)].sum())
            for hit, label in ((True, True), (True, False), (False, True), (False, False))]


def odds(cell, independent=False):
    a, b, c, d = map(int, cell)
    if min(a, b, c, d) <= 0:
        return {'failure': 'zero cell: finite unpenalized cue contrast unsupported', 'cells': [a, b, c, d]}
    if a*d == b*c:
        value = 0.0
    elif independent:
        hit_probability, absent_probability = a/(a+b), c/(c+d)
        value = (math.log(hit_probability)-math.log1p(-hit_probability)
                 -math.log(absent_probability)+math.log1p(-absent_probability))
    else:
        value = math.log(a)+math.log(d)-math.log(b)-math.log(c)
    return {'log_odds_ratio': value, 'cells': [a, b, c, d]}


def prepare(frame):
    if frame.text_id.duplicated().any() or frame[['text_id', 'prolific_id']].isna().any().any():
        raise ValueError('Exact unique private text and writer keys required')
    if not frame.emotion.isin(['shame', 'guilt']).all():
        raise ValueError('Only the two declared prompts may enter cue comparison')
    raw = frame[list(FAMILIES)].to_numpy(float)
    if not np.isfinite(raw).all() or np.any(raw < 0) or np.any(raw != np.floor(raw)):
        raise ValueError('Cue counts must be finite nonnegative integers')
    keys, codes = np.unique(frame.prolific_id.to_numpy(str), return_inverse=True)
    return {'keys': keys, 'codes': codes, 'labels': frame.emotion.eq('shame').to_numpy(),
            'presence': raw > 0}


def draw_weights(codes, writers, index):
    rng = np.random.default_rng(np.random.SeedSequence([SEED, index, 913]))
    return np.bincount(rng.integers(0, writers, writers), minlength=writers)[codes]


def evaluate(prepared, weights, families, independent=False):
    return {name: odds(cells(prepared['labels'], prepared['presence'][:, FAMILIES.index(name)],
                             weights, independent), independent) for name in families}


def interval_se(values, independent=False):
    values = [float(v) for v in values]
    if len(values) != 2000 or not all(math.isfinite(v) for v in values):
        raise ValueError('Exactly2000 finite retained values required')
    if independent:
        ordered = sorted(values)
        def quantile(p):
            place = p*(len(ordered)-1); lo = int(math.floor(place)); hi = int(math.ceil(place))
            return ordered[lo]+(place-lo)*(ordered[hi]-ordered[lo])
        mean = math.fsum(values)/len(values)
        se = math.sqrt(math.fsum((v-mean)**2 for v in values)/(len(values)-1))
        return [quantile(.025), quantile(.975)], se
    array = np.asarray(values)
    return np.quantile(array, [.025, .975]).tolist(), float(array.std(ddof=1))


def summarize(point, draws, writers, independent=False):
    failed = [i for i, value in enumerate(draws) if 'failure' in value]
    if 'failure' in point:
        return {'status': 'unsupported', 'reason': point['failure'], 'cells': point['cells'], 'failed_draws': failed}
    result = {'log_odds_ratio': point['log_odds_ratio'], 'odds_ratio': math.exp(point['log_odds_ratio']),
              'cells': point['cells'], 'cell_order': ['shame_hit', 'guilt_hit', 'shame_absent', 'guilt_absent'],
              'writers': writers, 'failed_draws': failed, 'draws': len(draws), 'no_practical_bar_assigned': True}
    if writers < 20:
        return {**result, 'status': 'below floor, descriptive', 'population_interval': None}
    if len(draws) != 2000:
        raise ValueError('Full2000 writer draws required before uncertainty')
    if failed:
        return {**result, 'status': 'invalid uncertainty', 'population_interval': None,
                'reason': 'all unsupported resamples retained; no deletion, redraw or continuity correction'}
    interval, se = interval_se([d['log_odds_ratio'] for d in draws], independent)
    if se == 0:
        return {**result, 'status': 'degenerate empirical uncertainty, descriptive', 'population_interval': None,
                'empirical_interval': interval, 'bootstrap_SE': se}
    return {**result, 'status': 'complete directed secondary', 'log_odds_interval': interval,
            'odds_ratio_interval': [math.exp(v) for v in interval], 'bootstrap_SE': se,
            'sees_log_odds': 2.8*se, 'supports_at': None,
            'approximation': 'normal; slightly optimistic; no commissioned cue practical bar'}
