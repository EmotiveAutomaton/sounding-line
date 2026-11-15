"""DC1 array instrument and explicit rating/next-choice timing projection.

DESIGN CHECK: LESSONS 2,3. Preserve the distinct frozen TR1 and RR3 terms.
Primary has two required signed differences, never their sum as a substitute.
Continuous preflight arithmetic is tested separately from standardized binary
choices. No source loader or production execute entry point is supplied until
the owner reviews the availability of next-offer controls at rating time.
"""
from collections import Counter
import warnings

import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from threadpoolctl import threadpool_limits

from . import week5_md_analysis as history
from . import week5_rr3_math_v1 as rr3

BAR = .05
SEED = 20261107
TERMS = ('sure_positive', 'sure_negative', 'gamble_minus_sure_EV',
         'below_start', 'above_start', 'prior_gambles', 'trial_index',
         'decaying_outcomes', 'recent_luck')
RECENT, LEVEL, BELOW = 8, 4, 3
CONTROLS = (0, 1, 2, 3, 5, 6, 7)
TIMING_HOLD = 'Owner review of next-offer controls at rating time and common eligible occasions required'


def common_roster(tr1_people, rr3_people, source_people):
    """The packet explicitly requests this intersection; do not hide exclusions."""
    tr, rr, source = set(tr1_people), set(rr3_people), set(source_people)
    if not tr <= source or not rr <= source:
        raise ValueError('Frozen roster contains people absent from the authenticated source')
    common = sorted(tr & rr)
    return common, {'TR1_people': len(tr), 'RR3_people': len(rr), 'common_people': len(common),
                    'TR1_only': len(tr - rr), 'RR3_only': len(rr - tr),
                    'source_outside_both': len(source - (tr | rr))}


def timing_table(plays, people, attempts, tr1_people, rr3_people, rr3_scales, reference=None):
    """First plays only: post-trial k rating -> choice k+1, history through k.

    Initial rating is actually before trial zero. The final rating has no next
    choice. Both are preserved in dispositions. Offer controls 0:3 come from
    k+1, so their availability is explicitly held for owner review, never assumed.
    """
    plays = np.asarray(plays, float)
    people, attempts = np.asarray(people), np.asarray(attempts)
    if plays.ndim != 3 or plays.shape[1:] != (30, 15) or len(plays) != len(people) or len(plays) != len(attempts):
        raise ValueError('Aligned qualified thirty-trial source plays required')
    scales = np.asarray(rr3_scales, float)
    if scales.shape != (9,) or not np.isfinite(scales).all() or np.any(scales <= 0):
        raise ValueError('All nine frozen RR3 reference scales required')
    if not np.isclose(scales[BELOW], scales[LEVEL], rtol=0, atol=0):
        raise ValueError('RR3 below/above terms require the same standing scale')
    common, audit = common_roster(tr1_people, rr3_people, people)
    selected = [i for i in range(len(plays)) if people[i] in common and attempts[i] == 1]
    count = Counter(people[i] for i in selected)
    if any(count[p] != 1 for p in common):
        raise ValueError('Every common person requires exactly one actual first play')
    if reference is not None:
        reference = np.asarray(reference, float)
        if reference.shape != (len(plays),) or not np.isfinite(reference).all():
            raise ValueError('Complete finite prior-reference vector required')
        reference = reference[selected]
    x = np.concatenate((history.dynamic_features(plays[selected], .65, reference), rr3.recent(plays[selected])[:, :, None]), axis=2)
    rows, dispositions = [], []
    for j, i in enumerate(selected):
        play = plays[i]
        occasions = np.flatnonzero(np.isfinite(play[:, 9]))
        if len(occasions) != 12 or occasions[0] != 0 or occasions[-1] != 29:
            raise ValueError('All twelve documented rating occasions are required')
        for k in occasions:
            identity = {'person': people[i].item() if hasattr(people[i], 'item') else people[i],
                        'attempt': 1, 'stored_rating_trial': int(k)}
            reason = ('initial_rating_before_first_trial_no_recent_history' if k == 0 else
                      'final_rating_has_no_next_choice' if k == 29 else 'paired_pending_control_timing_review')
            dispositions.append({**identity, 'reason': reason})
            if k in (0, 29):
                continue
            covariates = x[j, k + 1] / scales
            if not np.isfinite(covariates).all() or play[k + 1, 6] not in (0, 1):
                raise ValueError('Nonfinite next-choice predictors or nonbinary choice')
            rows.append({**identity, 'next_choice_trial': int(k + 1),
                         'history_last_trial': int(k), 'x': covariates.tolist(),
                         'rating': float(play[k, 9]), 'choice': int(play[k + 1, 6]),
                         'controls_requiring_timing_review': list(TERMS[:3])})
    return rows, {'roster': audit, 'dispositions': dispositions, 'production_admitted': False,
                  'hold': TIMING_HOLD, 'scales': scales.tolist(), 'terms': list(TERMS)}


def fixed_effect(x, y, people, weights=None, standardize=True):
    """Weighted within-person OLS. Whole-person multiplicities preserve intercepts."""
    x, y, people = np.asarray(x, float), np.asarray(y, float), np.asarray(people)
    if x.ndim != 2 or y.ndim != 1 or len(x) != len(y) or len(y) != len(people):
        raise ValueError('Aligned design, outcome and participant vectors required')
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError('Finite observed rows required')
    keys, codes = np.unique(people, return_inverse=True)
    w = np.ones(len(keys)) if weights is None else np.asarray(weights, float)
    if w.shape != (len(keys),) or not np.isfinite(w).all() or np.any(w < 0) or np.count_nonzero(w) < 2:
        raise ValueError('At least two positively weighted participant clusters required')
    roww = w[codes]
    total = roww.sum()
    mean = float(roww @ y / total)
    sd = float(np.sqrt(roww @ ((y - mean) ** 2) / (total - 1)))
    if standardize and sd <= 0:
        raise ValueError('Standardized outcome has no variation')
    yy = (y - mean) / sd if standardize else y.copy()
    xc, yc = x.copy(), yy.copy()
    for code in range(len(keys)):
        ii = codes == code
        xc[ii] -= x[ii].mean(axis=0)
        yc[ii] -= yy[ii].mean()
    gram, rhs = (xc * roww[:, None]).T @ xc, xc.T @ (roww * yc)
    if np.linalg.matrix_rank(gram) != x.shape[1]:
        raise ValueError('Within-person design is rank deficient')
    beta = np.linalg.solve(gram, rhs)
    return {'beta': beta, 'outcome_SD': sd, 'people': len(keys),
            'normal_equation_error': float(np.max(np.abs(gram @ beta - rhs)) / max(1, total))}


def primary(x, ratings, choices, people, weights=None):
    if not np.isin(choices, [0, 1]).all():
        raise ValueError('DC1 primary requires binary choices; continuous preflight is a separate ruler')
    x = np.asarray(x, float)
    if x.ndim != 2 or x.shape[1] != len(TERMS):
        raise ValueError('All nine frozen RR3 terms required')
    rating = fixed_effect(x, ratings, people, weights)
    choice = fixed_effect(x, choices, people, weights)
    br, bc = rating['beta'], choice['beta']
    return {'parts': [float(br[RECENT] - br[LEVEL]), float(bc[LEVEL] - bc[RECENT])],
            'rating_coefficients': br.tolist(), 'choice_coefficients': bc.tolist(),
            'rating_SD': rating['outcome_SD'], 'choice_SD': choice['outcome_SD'],
            'below_start_beside_primary': [float(br[BELOW]), float(bc[BELOW])]}


def classify_interval(interval):
    """Week 5 three-way rule for either positive-directed registered part."""
    bounds = np.asarray(interval, float)
    if bounds.shape != (2,) or not np.isfinite(bounds).all() or bounds[0] > bounds[1]:
        raise ValueError('Ordered finite contrast interval required')
    if bounds[0] > BAR:
        return 'supports'
    if bounds[1] < 0 or (bounds[0] >= -BAR and bounds[1] <= BAR):
        return 'against'
    return 'inconclusive'


def summarize(point, draws, people):
    if len(draws) != 2000:
        raise ValueError('Primary inference requires all two thousand person draws')
    failed = [i for i, row in enumerate(draws) if row is None]
    if failed:
        return {'status': 'invalid_uncertainty', 'point': point, 'failed_draws': failed, 'draws': len(draws)}
    values = np.asarray([row['parts'] for row in draws])
    intervals = np.quantile(values, [.025, .975], axis=0).T
    errors = (values - values[0]).std(axis=0, ddof=1)
    parts = []
    for name, estimate, interval, se in zip(('ratings_recent_minus_level', 'choices_level_minus_recent'), point['parts'], intervals, errors):
        status = 'below floor, descriptive' if people < 20 else 'degenerate, descriptive' if se == 0 else 'ok'
        outcome = classify_interval(interval) if status == 'ok' else None
        parts.append({'name': name, 'estimate': estimate, 'interval': interval.tolist(), 'bar': BAR,
                      'bootstrap_SE': float(se), 'sees': float(2.8 * se),
                      'supports_at': float(BAR + 2.8 * se), 'status': status, 'outcome': outcome})
    return {'status': 'ok', 'point': point, 'parts': parts, 'draws': 2000,
            'both_required': True, 'both_supported': all(p['outcome'] == 'supports' for p in parts)}


def sufficient_statistics(x, ratings, choices, people):
    """Precompute exact whole-person normal equations for bounded resampling."""
    x, y = np.asarray(x, float), np.column_stack((ratings, choices)).astype(float)
    people = np.asarray(people)
    if x.shape != (len(y), 9) or len(people) != len(y) or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError('Complete aligned finite RR3 design required')
    if not np.isin(y[:, 1], [0, 1]).all():
        raise ValueError('Binary next choice required')
    keys = np.unique(people)
    n, total, squares, gram, rhs = [], [], [], [], []
    for key in keys:
        a, b = x[people == key], y[people == key]
        ac, bc = a - a.mean(axis=0), b - b.mean(axis=0)
        n.append(len(a)); total.append(b.sum(axis=0)); squares.append((b ** 2).sum(axis=0))
        gram.append(ac.T @ ac); rhs.append(ac.T @ bc)
    return {'keys': keys, 'n': np.asarray(n), 'total': np.asarray(total),
            'squares': np.asarray(squares), 'gram': np.asarray(gram), 'rhs': np.asarray(rhs)}


def from_statistics(stats, weights):
    w = np.asarray(weights, float)
    if w.shape != (len(stats['keys']),) or not np.isfinite(w).all() or np.any(w < 0) or np.count_nonzero(w) < 2:
        raise ValueError('At least two positive whole-person weights required')
    n, total, squares = float(w @ stats['n']), w @ stats['total'], w @ stats['squares']
    variance = (squares - total ** 2 / n) / (n - 1)
    if np.any(variance <= 0):
        raise ValueError('Outcome standardization is unsupported')
    sd = np.sqrt(variance)
    gram = np.einsum('n,nij->ij', w, stats['gram'])
    if np.linalg.matrix_rank(gram) != 9:
        raise ValueError('Within-person bootstrap design is rank deficient')
    beta = np.linalg.solve(gram, np.einsum('n,nij->ij', w, stats['rhs'])) / sd
    br, bc = beta[:, 0], beta[:, 1]
    return {'parts': [float(br[RECENT] - br[LEVEL]), float(bc[LEVEL] - bc[RECENT])],
            'rating_coefficients': br.tolist(), 'choice_coefficients': bc.tolist(),
            'rating_SD': float(sd[0]), 'choice_SD': float(sd[1]),
            'below_start_beside_primary': [float(br[BELOW]), float(bc[BELOW])]}


def bootstrap_draw(stats, ordinal):
    """One resumable deterministic draw; invalid draws are never silently redrawn."""
    if type(ordinal) is not int or not 0 <= ordinal < 2000:
        raise ValueError('Primary draw ordinal must be within the frozen bank')
    rng = np.random.default_rng(np.random.SeedSequence([SEED, ordinal, 1]))
    n = len(stats['keys'])
    weights = np.bincount(rng.integers(n, size=n), minlength=n)
    try:
        return from_statistics(stats, weights)
    except (ValueError, np.linalg.LinAlgError):
        return None


def prediction_row(x, ratings, choices, people):
    """Five participant-held-out folds; unseen-person intercept is the population mean.

    Training-only scaling; each one-term model retains RR3's other controls.
    Ratings use exact within-person slopes. Choices use fixed C=1 regularized
    person-intercept logistic fits for finite unseen-person log scores. This
    prediction convention requires owner review with the timing mapping.
    """
    x, ratings, choices, people = map(np.asarray, (x, ratings, choices, people))
    keys = sorted(set(people.tolist()))
    if len(keys) < 2 or not np.isin(choices, [0, 1]).all():
        raise ValueError('At least two people and binary choice required')
    groups = {p: i % min(5, len(keys)) for i, p in enumerate(keys)}
    outcome = {}
    for label, focal in (('RECENT', RECENT), ('LEVEL', LEVEL)):
        columns = [focal, *CONTROLS]
        rpred, cpred = np.empty(len(people)), np.empty(len(people))
        rtruth = np.empty(len(people))
        for fold in sorted(set(groups.values())):
            te = np.asarray([groups[p] == fold for p in people]); tr = ~te
            a, b = np.asarray(x[tr][:, columns], float), np.asarray(x[te][:, columns], float)
            mu, scale = a.mean(axis=0), a.std(axis=0)
            scale[scale == 0] = 1
            a, b = (a - mu) / scale, (b - mu) / scale
            rm, rs = ratings[tr].mean(), ratings[tr].std(ddof=1)
            if rs <= 0:
                raise ValueError('Training rating scale is degenerate')
            yr = (ratings[tr] - rm) / rs
            beta = fixed_effect(a, yr, people[tr], standardize=False)['beta']
            rpred[te] = b @ beta + np.mean(yr - a @ beta)
            rtruth[te] = (ratings[te] - rm) / rs
            train_people = sorted(set(people[tr].tolist()))
            dummies = np.column_stack([people[tr] == p for p in train_people]).astype(float)
            with threadpool_limits(limits=2), warnings.catch_warnings():
                warnings.simplefilter('error', ConvergenceWarning)
                model = LogisticRegression(C=1., max_iter=2000, tol=1e-9)
                model.fit(np.column_stack((a, dummies)), choices[tr])
            cpred[te] = model.predict_proba(np.column_stack((b, np.zeros((len(b), len(train_people))))))[:, 1]
        outcome[label] = {'rating_standardized_MSE': float(np.mean((rtruth - rpred) ** 2)),
                          'choice_mean_log_score': -float(log_loss(choices, cpred, labels=[0, 1]))}
    outcome['scope'] = 'held-out people; unseen intercept population mean; fixed regularized choice prediction'
    return outcome


def corrected_person_correlation(rating_sensitivity, choice_recent_slope, tr1_stability):
    """Disattenuate the rating side only; no clipping and no invented choice reliability."""
    a, b = np.asarray(rating_sensitivity, float), np.asarray(choice_recent_slope, float)
    if len(a) != len(b) or len(a) < 3 or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('Aligned complete person slopes required')
    if not np.isfinite(tr1_stability) or tr1_stability <= 0 or a.std() == 0 or b.std() == 0:
        return {'status': 'unsupported', 'reason': 'nonpositive stability or absent between-person variation'}
    raw = float(np.corrcoef(a, b)[0, 1])
    return {'status': 'ok', 'raw': raw, 'corrected': float(raw / np.sqrt(tr1_stability)),
            'TR1_stability': float(tr1_stability), 'choice_reliability_unmeasured': True,
            'correction_above_one_retained': abs(raw / np.sqrt(tr1_stability)) > 1}


def preflight_reference(seed=16, n=200000):
    """Exact supplied continuous, unstandardized design; never a binary-choice test."""
    rng = np.random.default_rng(seed)
    z = rng.multivariate_normal([0, 0], [[1, .28], [.28, 1]], n)
    rating = .3 * z[:, 0] + .1 * z[:, 1] + rng.normal(0, 1, n)
    continuous_choice = .1 * z[:, 0] + .3 * z[:, 1] + rng.normal(0, 1, n)
    design = np.column_stack((np.ones(n), z))
    br = np.linalg.lstsq(design, rating, rcond=None)[0][1:]
    bc = np.linalg.lstsq(design, continuous_choice, rcond=None)[0][1:]
    return {'rating_part': float(br[0] - br[1]), 'continuous_choice_part': float(bc[1] - bc[0]),
            'sum': float(br[0] - br[1] + bc[1] - bc[0]), 'production_binary_validation': False}
