"""D37 frozen three-entry reader core; no human execution admission here.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-7 read 2026-10-29.
NULL: identical readers give exact zero; independent targets contain no gain.
ALTERNATIVE: complementary calibrated forecasts can improve proper score;
wrong forecasts lose. All fits and priors use training only, calibration selects
weights, chronological prefixes update lawfully. Corruption, unsupported prior
or uncertified optimization refuses. Complete scientific calibration is separate.
"""
from itertools import combinations
from collections import defaultdict
import numpy as np
from scipy.special import softmax
from sklearn.decomposition import PCA
from . import menus_p4 as p4
from . import menus_d15 as d15
from . import menus_crossed_stats as crossed

CONFIG = dict(card='D37-readers', schema=1, seed=20261026, pca_dimensions=16)
ENTRIES = ('page', 'person', 'process')


def probabilities(a):
    a = np.asarray(a, float)
    if a.ndim != 2 or a.shape[1] != 4 or not np.isfinite(a).all() or np.any(a < 0) or not np.allclose(a.sum(1), 1, atol=1e-10, rtol=0):
        raise ValueError('Invalid four-class probability array')
    return a


def session_weights(rows):
    groups = defaultdict(list)
    for i, row in enumerate(rows):
        groups[row['session']].append(i)
    if not groups:
        raise ValueError('No scored sessions')
    weights = np.zeros(len(rows))
    for key in sorted(groups):
        weights[groups[key]] = 1 / (len(groups) * len(groups[key]))
    return weights


def combine_fit(readers, y, rows):
    """Exact three-variable convex quadratic, including all boundary faces."""
    x = np.stack([probabilities(p) for p in readers], axis=1)
    y = np.asarray(y, int)
    if x.shape != (len(rows), 3, 4) or y.shape != (len(rows),) or np.any((y < 0) | (y > 3)):
        raise ValueError('Combination support mismatch')
    v = session_weights(rows); truth = np.eye(4)[y]
    h = np.einsum('n,nic,njc->ij', v, x, x)
    b = np.einsum('n,nic,nc->i', v, x, truth)
    candidates = []
    for size in (1, 2, 3):
        for face in combinations(range(3), size):
            ids = np.array(face); hf = h[np.ix_(ids, ids)]
            system = np.block([[hf, np.ones((size, 1))], [np.ones((1, size)), np.zeros((1, 1))]])
            answer = np.linalg.lstsq(system, np.r_[b[ids], 1.], rcond=None)[0][:size]
            if np.min(answer) < -1e-10 or abs(answer.sum()-1) > 1e-10:
                continue
            w = np.zeros(3); w[ids] = np.maximum(answer, 0); w /= w.sum()
            gradient = h @ w-b
            gap = float(w @ gradient-gradient.min())
            if gap > 1e-9:
                continue
            loss = float(.5*np.sum(v[:, None]*(np.einsum('i,nic->nc', w, x)-truth)**2))
            candidates.append((loss, tuple(w), gap))
    if not candidates:
        raise ValueError('No certified convex combination')
    loss, w, gap = min(candidates)
    return np.array(w), dict(calibration_loss=loss, optimality_gap=gap)


def prior_fit(rows, y):
    """The handling-only V3 trace, on the caller's training slice only."""
    if len(rows) != len(y) or len({r['writer'] for r in rows}) < 3:
        raise ValueError('Insufficient training-only reliability support')
    coded = [dict(r, handling=p4.ACTIONS[int(label)]) for r, label in zip(rows, y)]
    matrix, groups, _ = d15.encode(coded)
    fitted = crossed.fit(matrix, groups, d15.GROUPS)
    rho, _ = crossed.icc(fitted)
    if rho is None or not np.isfinite(rho) or not 0 <= rho <= 1:
        raise ValueError('Undefined training-only reliability')
    population = matrix.mean(0)
    return dict(reliability=float(rho), prior_count=None if rho == 0 else float((1-rho)/rho),
                population=population.tolist(), condition=fitted['condition'],
                structural_constants=fitted['structural_constants'], training_rows=len(rows))


def prefix_counts(rows, y):
    if len({r['key'] for r in rows}) != len(rows) or len(y) != len(rows):
        raise ValueError('Duplicate or mismatched history keys')
    histories = defaultdict(list); counts = np.zeros((len(rows), 4)); sessions = np.zeros(len(rows), int)
    order = sorted(range(len(rows)), key=lambda i: (rows[i]['open_at'], rows[i]['key']))
    for i in order:
        r = rows[i]
        prior = [j for j in histories[r['writer']] if rows[j]['resolved_at'] <= r['open_at']
                 and (rows[j]['session'] == r['session'] or rows[j]['session_end'] < r['session_time'])]
        counts[i] = np.bincount(np.asarray(y, int)[prior], minlength=4)
        sessions[i] = len({rows[j]['session'] for j in prior if rows[j]['session'] != r['session']})
        histories[r['writer']].append(i)
    return counts, sessions


def person_probabilities(counts, prior):
    counts = np.asarray(counts, float); pop = np.asarray(prior['population'], float)
    if counts.ndim != 2 or counts.shape[1] != 4 or not np.isfinite(counts).all() or np.any(counts < 0):
        raise ValueError('Invalid history counts')
    if prior['reliability'] == 0:
        return np.tile(pop, (len(counts), 1))
    k = prior['prior_count']; denominator = counts.sum(1)+k
    return np.divide(counts+k*pop, denominator[:, None], out=np.tile(pop, (len(counts), 1)), where=denominator[:, None] > 0)


def partition_indices(rows, partition):
    groups = {}; session_set = {r['session'] for r in rows}
    for group in ('train', 'own_train', 'calibration', 'test'):
        names = partition[group]
        if len(set(names)) != len(names) or not set(names) <= session_set:
            raise ValueError('Invalid session partition')
        groups[group] = np.array([i for i, row in enumerate(rows) if row['session'] in set(names)], int)
        if not len(groups[group]):
            raise ValueError('Empty choice partition')
    if any(set(groups[a]) & set(groups[b]) for a, b in (('train', 'calibration'), ('train', 'test'), ('calibration', 'test'))):
        raise ValueError('Overlapping train/calibration/test')
    if not set(groups['own_train']) <= set(groups['train']):
        raise ValueError('Own training outside pooled training')
    if any(rows[i]['session_end'] >= partition['cutoff'] for i in groups['train']):
        raise ValueError('Future training session')
    if any(rows[i]['session_end'] >= partition['test_cutoff'] for i in groups['calibration']):
        raise ValueError('Future calibration session')
    return groups


def prepare(rows, arrays, partition, config=CONFIG):
    if config != CONFIG or set(arrays) != {'page', 'process', 'embedding'}:
        raise ValueError('Frozen reader configuration required')
    if any(a.ndim != 2 or len(a) != len(rows) or not np.isfinite(a).all() for a in arrays.values()):
        raise ValueError('Feature array support mismatch')
    groups = partition_indices(rows, partition); train = groups['train']
    dim = min(config['pca_dimensions'], len(train)-1, arrays['embedding'].shape[1])
    projection = PCA(n_components=dim, svd_solver='randomized', random_state=config['seed'])
    projection.fit(arrays['embedding'][train])
    page = np.c_[arrays['page'], projection.transform(arrays['embedding'])]
    out = {}
    for name, features in (('page', page), ('process', arrays['process'])):
        mean, sd = p4.standardize_fit(features[train])
        out[name] = np.c_[np.ones(len(rows)), (features-mean)/sd]
    return dict(groups=groups, matrices=out, pca_dimensions=dim)


def fit_recipient(rows, y, prepared, history):
    y = np.asarray(y, int)
    if y.shape != (len(rows),) or np.any((y < 0) | (y > 3)):
        raise ValueError('Invalid canonical targets')
    g = prepared['groups']; train, cal, test = (g[k] for k in ('train', 'calibration', 'test'))
    prior = prior_fit([rows[i] for i in train], y[train])
    forecasts = {}
    for name in ('page', 'process'):
        matrix = prepared['matrices'][name]
        coefficients = p4.global_fit(matrix[train], y[train])
        forecasts[name] = probabilities(softmax(matrix @ coefficients, axis=1))
    forecasts['person'] = probabilities(person_probabilities(history[0], prior))
    cal_rows = [rows[i] for i in cal]; weight = session_weights(cal_rows)
    losses = [float(weight @ p4.brier(forecasts[name][cal], y[cal])) for name in ENTRIES]
    best = min(range(3), key=lambda i: (losses[i], i))
    combination, certificate = combine_fit([forecasts[name][cal] for name in ENTRIES], y[cal], cal_rows)
    x = np.stack([forecasts[name][test] for name in ENTRIES], axis=1)
    stack = probabilities(np.einsum('i,nic->nc', combination, x))
    single = x[:, best, :]
    # Avoid accumulation artifacts for exact identity, including degenerate faces.
    identical = np.all(x == x[:, :1, :], axis=(1, 2))
    stack[identical] = single[identical]
    predicted = [dict(key=rows[i]['key'], writer=rows[i]['writer'], session=rows[i]['session'],
                      truth=int(y[i]), prior_sessions=int(history[1][i]),
                      entries=x[j].tolist(), single=single[j].tolist(), stack=stack[j].tolist()) for j, i in enumerate(test)]
    return predicted, dict(best_entry=ENTRIES[best], weights=combination.tolist(), calibration_losses=losses,
                           prior=prior, certificate=certificate, pca_dimensions=prepared['pca_dimensions'],
                           training_keys=[rows[i]['key'] for i in train], calibration_keys=[rows[i]['key'] for i in cal],
                           test_keys=[rows[i]['key'] for i in test])


def permute_targets(rows, y, seed):
    groups = defaultdict(list)
    for i, row in enumerate(rows):
        groups[row['writer']].append(i)
    changed = np.asarray(y, int).copy(); rng = np.random.default_rng(seed)
    for writer in sorted(groups):
        indices = sorted(groups[writer], key=lambda i: rows[i]['key'])
        changed[indices] = changed[rng.permutation(indices)]
    return changed
