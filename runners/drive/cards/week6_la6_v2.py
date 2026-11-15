"""LA6 matched utterance trigger table; pure in-memory builder, no source IO.

DESIGN CHECK: LESSONS 2,3. Act type must remain free to vary in a pair.
Known binary-act odds recover the analytic AUC; label-identical worlds have
AUC one half. Meetings, including reused controls, stay intact in folds/draws.
No production admission follows from these constructed checks.
"""
from bisect import bisect_left, bisect_right, insort
from collections import Counter, defaultdict
import re
import warnings

import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from threadpoolctl import threadpool_limits

BAR = .60
SEED = 20261107
NUMERIC = ('word_count', 'speaker_changed', 'overlap_previous_two',
           'repeats_previous_speaker', 'first_person_singular', 'negation',
           'question', 'meeting_tenth', 'seconds_since_last_laugh')
TOKEN = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)?")
FIRST = {'i', 'me', 'my', 'mine', 'myself'}
NEGATIVE = {'no', 'not', 'never', 'none', 'nobody', 'nothing', 'neither', 'nor'}


def tokens(text):
    return [word.lower().replace('’', "'") for word in TOKEN.findall(text)]


def validate(rows):
    keys = []
    for row in rows:
        keys.append((row['meeting'], row['id']))
        if type(row['laughed_after']) is not bool:
            raise ValueError('Boolean prepared laugh label required')
        if (not np.isfinite([row['start'], row['end']]).all()
                or row['end'] < row['start'] or not isinstance(row['text'], str)):
            raise ValueError('Finite ordered utterance timing and laugh-safe text required')
        if not row['speaker'] or not row['act_type']:
            raise ValueError('Speaker and act type are required')
    if len(keys) != len(set(keys)):
        raise ValueError('Duplicate meeting/utterance identity')


def match(rows):
    """Nearest eligible control by start time; ties use start then source ID.

    Matching is with replacement; the packet imposes no uniqueness constraint.
    Every case and every unsupported case receives a disposition.
    """
    validate(rows)
    pools = defaultdict(list)
    for row in rows:
        if not row['laughed_after']:
            pools[(row['meeting'], row['speaker'])].append(row)
    for pool in pools.values():
        pool.sort(key=lambda r: (r['start'], r['id']))
    times = {key: [r['start'] for r in value] for key, value in pools.items()}
    pairs, unsupported = [], []
    for row in sorted(rows, key=lambda r: (r['meeting'], r['start'], r['id'])):
        if not row['laughed_after']:
            continue
        key = row['meeting'], row['speaker']
        pool, clock = pools[key], times.get(key, [])
        left = bisect_right(clock, row['start'] - 30) - 1
        right = bisect_left(clock, row['start'] + 30)
        candidate = []
        if left >= 0:
            # For tied timestamps the lexically first source ID wins.
            candidate.append(pool[bisect_left(clock, clock[left])])
        if right < len(pool):
            candidate.append(pool[right])
        if not candidate:
            unsupported.append({'meeting': row['meeting'], 'case': row['id'],
                                'reason': 'no_same_speaker_nonlaugh_at_least_30_seconds_away'})
            continue
        control = min(candidate, key=lambda r: (abs(r['start'] - row['start']), r['start'], r['id']))
        pairs.append({'meeting': row['meeting'], 'case': row['id'], 'control': control['id'],
                      'distance_seconds': abs(control['start'] - row['start'])})
    reuse = Counter((p['meeting'], p['control']) for p in pairs)
    return pairs, {'cases': sum(r['laughed_after'] for r in rows), 'matched': len(pairs),
                   'unsupported': unsupported, 'unique_controls': len(reuse),
                   'reused_control_copies': sum(n - 1 for n in reuse.values())}


def feature_rows(rows, laughs):
    """Prior context consists only of utterances completed by this start time.

    `laughs` is the source-pinned event table used for prepared laugh labels.
    Only completed past laughs enter the elapsed-time feature.
    """
    validate(rows)
    groups, laugh_ends = defaultdict(list), defaultdict(list)
    for row in rows:
        groups[row['meeting']].append(row)
    for event in laughs:
        if not np.isfinite([event['start'], event['end']]).all() or event['end'] < event['start']:
            raise ValueError('Finite ordered source laugh timing required')
        laugh_ends[event['meeting']].append(event['end'])
    output = {}
    for meeting in sorted(groups):
        acts = sorted(groups[meeting], key=lambda r: (r['start'], r['end'], r['id']))
        by_end = sorted(acts, key=lambda r: (r['end'], r['start'], r['id']))
        first, last = min(r['start'] for r in acts), max(r['end'] for r in acts)
        ends, completed, cursor = sorted(laugh_ends[meeting]), [], 0
        lookup = {r['id']: r for r in acts}
        for row in acts:
            while cursor < len(by_end) and by_end[cursor]['end'] <= row['start']:
                prior = by_end[cursor]
                insort(completed, (prior['start'], prior['end'], prior['id']))
                cursor += 1
            # Exclude self and tied zero-duration acts not strictly earlier.
            preceding = [lookup[key[2]] for key in completed
                         if key < (row['start'], row['end'], row['id'])]
            words, current = tokens(row['text']), set(tokens(row['text']))
            word_count = row.get('word_count', len(words))
            if type(word_count) is not int or word_count < 0:
                raise ValueError('Original parser word count must be a nonnegative integer')
            two = set().union(*(set(tokens(p['text'])) for p in preceding[-2:]))
            previous_other = next((p for p in reversed(preceding) if p['speaker'] != row['speaker']), None)
            other_words = set(tokens(previous_other['text'])) if previous_other else set()
            at = bisect_right(ends, row['start']) - 1
            elapsed = row['start'] - (ends[at] if at >= 0 else first)
            numeric = [word_count, int(bool(preceding) and preceding[-1]['speaker'] != row['speaker']),
                       len(current & two) / max(1, len(current)), int(bool(current & other_words)),
                       int(any(w in FIRST or w.startswith("i'") for w in words)),
                       int(any(w in NEGATIVE or w.endswith("n't") for w in words)),
                       int('?' in row['text']), min(9, int(10 * (row['start'] - first) / max(last - first, 1e-12))),
                       elapsed]
            output[(meeting, row['id'])] = {'meeting': meeting, 'id': row['id'],
                'act_type': row['act_type'], 'numeric': numeric, 'label': int(row['laughed_after'])}
    return output


def matched_table(rows, laughs):
    pairs, audit = match(rows)
    features = feature_rows(rows, laughs)
    table = []
    for pair in pairs:
        for role in ('case', 'control'):
            table.append(dict(features[(pair['meeting'], pair[role])], pair=pair['case'], role=role))
    return table, audit


def encoding(rows, include_laugh=True, template=None):
    if not rows:
        raise ValueError('No matched utterances')
    numeric = np.asarray([r['numeric'] for r in rows], float)[:, :9 if include_laugh else 8]
    if not np.isfinite(numeric).all():
        raise ValueError('Nonfinite predictor')
    if template is None:
        categories = sorted({r['act_type'] for r in rows})
        mean, scale = numeric.mean(axis=0), numeric.std(axis=0)
        scale[scale == 0] = 1
        template = (categories, mean, scale)
    categories, mean, scale = template
    one_hot = np.asarray([[float(r['act_type'] == c) for c in categories[1:]] for r in rows])
    return np.column_stack(((numeric - mean) / scale, one_hot)), template


def fitted(rows, include_laugh=True, weights=None):
    x, template = encoding(rows, include_laugh)
    y = np.asarray([r['label'] for r in rows], int)
    if set(y) != {0, 1}:
        raise ValueError('Both case and control required')
    # Fixed L2 regularization, no tuning; it also makes absent resampled acts explicit.
    with threadpool_limits(limits=2), warnings.catch_warnings():
        warnings.simplefilter('error', ConvergenceWarning)
        model = LogisticRegression(C=1., solver='lbfgs', max_iter=2000, tol=1e-9)
        model.fit(x, y, sample_weight=weights)
    return model, template


def held_out(rows, include_laugh=True):
    meetings = sorted({r['meeting'] for r in rows})
    if len(meetings) < 2:
        return {'status': 'below floor, descriptive', 'auc': None, 'reason': 'fewer than two meetings'}
    # Round-robin groups give exactly min(5,M) nonempty meeting-disjoint folds.
    folds = {meeting: i % min(5, len(meetings)) for i, meeting in enumerate(meetings)}
    predictions = np.full(len(rows), np.nan)
    audit = []
    for fold in sorted(set(folds.values())):
        train = [i for i, r in enumerate(rows) if folds[r['meeting']] != fold]
        test = [i for i, r in enumerate(rows) if folds[r['meeting']] == fold]
        model, template = fitted([rows[i] for i in train], include_laugh)
        x, _ = encoding([rows[i] for i in test], include_laugh, template)
        predictions[test] = model.decision_function(x)
        audit.append({'fold': fold, 'training_meetings': sorted({rows[i]['meeting'] for i in train}),
                      'test_meetings': sorted({rows[i]['meeting'] for i in test})})
    return {'status': 'ok', 'auc': float(roc_auc_score([r['label'] for r in rows], predictions)),
            'predictions': predictions, 'folds': audit}


def analyze(rows, draws=2000):
    """Meeting-bootstrap held-out AUC and fitted act odds, in both feature arms.

    Held-out predictions stay frozen during their cluster bootstrap; coefficient
    intervals refit each whole-meeting draw. Missing act support invalidates that
    act's interval rather than treating an absent category as a measured zero.
    """
    if type(draws) is not int or draws < 2:
        raise ValueError('At least two complete fixture draws required')
    meetings = sorted({r['meeting'] for r in rows})
    if len(meetings) < 2:
        return {'status': 'below floor, descriptive', 'reason': 'fewer than two meetings', 'draws': 0}
    code = {m: i for i, m in enumerate(meetings)}
    group = np.asarray([code[r['meeting']] for r in rows])
    y = np.asarray([r['label'] for r in rows])
    result = {'card': 'LA6', 'meetings': len(meetings), 'draws': draws,
              'below_floor_descriptive': len(meetings) < 20, 'arms': {}}
    for include in (True, False):
        cv = held_out(rows, include)
        model, template = fitted(rows, include)
        categories = template[0]
        offset = 9 if include else 8
        coefficients = model.coef_[0][offset:]
        auc_bank, odds_bank, failed = [], [], []
        for draw in range(draws):
            rng = np.random.default_rng(np.random.SeedSequence([SEED, draw, 6]))
            multiplicity = np.bincount(rng.integers(len(meetings), size=len(meetings)), minlength=len(meetings))
            w = multiplicity[group]
            auc_bank.append(float(roc_auc_score(y, cv['predictions'], sample_weight=w)))
            selected = [r for i, r in enumerate(rows) if w[i] > 0]
            if {r['act_type'] for r in selected} != set(categories):
                failed.append(draw)
                odds_bank.append(None)
                continue
            refit, _ = fitted(rows, include, w)
            odds_bank.append(refit.coef_[0][offset:].tolist())
        interval = np.quantile(auc_bank, [.025, .975]).tolist()
        se = float(np.std(np.asarray(auc_bank) - auc_bank[0], ddof=1))
        odds = {categories[0]: {'odds_ratio': 1., 'reference': True}}
        for i, category in enumerate(categories[1:]):
            odds[category] = {'odds_ratio': float(np.exp(coefficients[i])), 'reference': False,
                'interval': None if failed else np.exp(np.quantile(np.asarray(odds_bank)[:, i], [.025, .975])).tolist()}
        result['arms']['with_laugh_history' if include else 'without_laugh_history'] = {
            'auc': cv['auc'], 'interval': interval, 'bar': BAR, 'bootstrap_SE': se,
            'sees_above_chance': 2.8 * se, 'supports_at': BAR + 2.8 * se,
            'degenerate_bootstrap': se == 0, 'act_odds': odds,
            'act_interval_failed_draws': failed, 'folds': cv['folds']}
    return result
