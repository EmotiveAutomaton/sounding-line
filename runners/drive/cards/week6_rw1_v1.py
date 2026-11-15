"""Prospective RW1 association and whole-person, whole-pipeline bootstrap.

DESIGN CHECK: LESSONS 2,3. A factorial sentence corpus has partial correlation
-0.15 or zero after length and held-out bad-news share. No person's worry learns
her own vocabulary, including bootstrap copies. Both vocabularies are relearned
in every draw. Algebraic recovery is not a claim of sampling-model calibration.
Missing support, failed draws and unqualified semantic markers retain separate
states; none becomes a scientific null. No corpus IO or annotation fabrication.
"""
import hashlib
import json
import re

import numpy as np
from scipy.sparse import csr_matrix

from . import week6_rw1_intake_v1 as marker
from . import week6_rw1_source_v1 as source
from . import week6_rw1_context_v1 as context

SEED = 20261107
BAR = -.05
WORDS = 200
WORD = re.compile(r'[^\W\d_]+', re.UNICODE)
SEMANTIC = {
    'split': 'seed20261107; balanced random halves of sorted original person keys; fixed through bootstrap',
    'token': 'Unicode alphabetic runs; casefold; punctuation including apostrophes separates tokens',
    'length': 'raw word-token count in original long text',
    'word_association': 'largest signed Pearson correlation of person word presence with worry; lexical ties',
    'word_count': 200, 'word_filters': 'positive training association and variation; no stopwords, stemming or frequency floor',
    'bad_news': 'share of sentences containing any word selected using opposite-half worry',
    'primary': 'Pearson residual correlation of plan-sentence share and worry given intercept,length,bad-news share',
    'bootstrap': '2000 original-person multinomial draws; fixed halves; relearn both lists and refit all targets',
    'secondary': 'anxiety,fear,relaxation; worry additionally holding fear,sadness; paired time/place correlation difference',
    'time_place': 'finite literal lists qualified on the same 200 sentences; unmatched counted unknown-or-absent',
}
TARGETS = ('worry', 'anxiety', 'fear', 'relaxation', 'worry_beyond_fear_sadness',
           'time_place_named_worry', 'time_place_other_worry', 'time_place_difference')


class Unidentified(ValueError):
    """A specified statistic lacks support; never a small-effect result."""


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def tokens(text):
    return WORD.findall(text.replace('\u2019', "'").casefold())


def fixed_halves(people):
    if len(people) < 2 or len(set(people)) != len(people) or list(people) != sorted(people):
        raise ValueError('At least two unique canonically ordered original people required')
    order = np.random.default_rng(np.random.SeedSequence([SEED, 11])).permutation(len(people))
    half = np.ones(len(people), dtype=int); half[order[:len(people) // 2]] = 0
    return half


def prepare(records, time_place_qualified=False):
    rows = sorted(records, key=lambda r: r['person'])
    people = [r['person'] for r in rows]; halves = fixed_halves(people)
    if type(time_place_qualified) is not bool: raise ValueError('Explicit time/place qualification state required')
    sentence_sets, owners, person_sets, lengths, counts, plans, named, ratings = [], [], [], [], [], [], [], []
    all_sentence_ids = set(); dispositions = []; unknown_counts = []
    for i, row in enumerate(rows):
        if set(row['ratings']) != set(source.COLUMNS[1:]):
            raise ValueError('Only the five commissioned ratings are allowed')
        spans = source.sentence_spans(row['text_long'])
        sentences = row['sentences']
        if [(s['start'], s['end']) for s in sentences] != spans:
            raise ValueError('Original sentence offsets changed')
        word_set = set(); plan_count = named_count = unknown_count = 0
        for s in sentences:
            if s['id'] in all_sentence_ids or s['text'] != row['text_long'][s['start']:s['end']]:
                raise ValueError('Original sentence identity or bytes changed')
            all_sentence_ids.add(s['id']); words = set(tokens(s['text']))
            sentence_sets.append(words); owners.append(i); word_set.update(words)
            if marker.plan_candidate(s['text']):
                plan_count += 1
                classified = context.classify(s['text']); unknown_count += classified['unknown_or_absent']
                if time_place_qualified and classified['literal_named']:
                    named_count += 1
        number = len(sentences); length = len(tokens(row['text_long']))
        reasons = []
        if number == 0: reasons.append('no_nonempty_sentences')
        if length == 0: reasons.append('no_word_tokens')
        vals = []
        for key in source.COLUMNS[1:]:
            value = row['ratings'][key]
            if value is None:
                vals.append(np.nan); reasons.append('missing_' + key)
            elif type(value) is not int or not 1 <= value <= 9:
                raise ValueError('Projected author ratings must retain the integer 1-to-9 scale')
            else:
                vals.append(value)
        person_sets.append(word_set); lengths.append(length); counts.append(number)
        plans.append(plan_count / number if number else np.nan)
        named.append(named_count / number if time_place_qualified and number else np.nan)
        unknown_counts.append(unknown_count)
        ratings.append(vals); dispositions.append({'person': row['person'], 'reasons': reasons})
    vocabulary = sorted(set().union(*person_sets)); index = {word: i for i, word in enumerate(vocabulary)}
    def matrix(sets):
        rr, cc = [], []
        for i, words in enumerate(sets):
            for word in sorted(words): rr.append(i); cc.append(index[word])
        return csr_matrix((np.ones(len(rr)), (rr, cc)), shape=(len(sets), len(vocabulary)))
    return {'people': people, 'halves': halves, 'words': vocabulary,
            'person_words': matrix(person_sets), 'sentence_words': matrix(sentence_sets),
            'sentence_owner': np.asarray(owners, int), 'length': np.asarray(lengths, float),
            'sentences': np.asarray(counts, int), 'plan': np.asarray(plans),
            'named_plan': np.asarray(named), 'time_place_qualified_input': time_place_qualified,
            'literal_unknown_or_absent_plan_counts': unknown_counts,
            'ratings': np.asarray(ratings, float), 'dispositions': dispositions,
            'half_manifest_sha256': digest(list(zip(people, halves.tolist())))}


def weights_for(data, weights):
    w = np.asarray(weights, float)
    if w.shape != (len(data['people']),) or not np.isfinite(w).all() or (w < 0).any() or w.sum() <= 0:
        raise ValueError('Finite nonnegative original-person weights required')
    return w


def learned_vocabulary(data, weights, training_half):
    w = weights_for(data, weights).copy(); y = data['ratings'][:, 0]
    valid = (data['halves'] == training_half) & np.isfinite(y) & (data['sentences'] > 0) & (data['length'] > 0)
    w[~valid] = 0; yy = np.where(np.isfinite(y), y, 0); n = w.sum()
    if np.count_nonzero(w) < 2:
        raise Unidentified('fewer than two training people for worry vocabulary')
    sy = float(w @ yy); vy = float(w @ (yy * yy) - sy * sy / n)
    if vy <= 0: raise Unidentified('constant training worry for vocabulary')
    x = data['person_words']; sx = np.asarray(x.T @ w).ravel()
    vx = sx - sx * sx / n
    cov = np.asarray(x.T @ (w * yy)).ravel() - sx * sy / n
    possible = np.flatnonzero((vx > 0) & (cov > 0))
    if len(possible) < WORDS:
        raise Unidentified('fewer than 200 positive training-variable word types')
    association = cov[possible] / np.sqrt(vx[possible] * vy)
    order = sorted(range(len(possible)), key=lambda j: (-float(association[j]), data['words'][possible[j]]))[:WORDS]
    chosen = possible[order]; words = [data['words'][j] for j in chosen]
    return chosen, {'training_half': int(training_half), 'training_people': int(np.count_nonzero(w)),
        'training_weight': float(n), 'candidate_words': len(possible), 'words': words,
        'positive_selected_associations': int(np.sum(association[order] > 0)),
        'words_sha256': digest(words)}


def bad_news(data, weights, *, keep_words=False):
    shares = np.full(len(data['people']), np.nan); audit = []
    for training in (0, 1):
        selected, detail = learned_vocabulary(data, weights, training)
        hits = np.asarray(data['sentence_words'][:, selected].getnnz(axis=1) > 0, float)
        totals = np.bincount(data['sentence_owner'], weights=hits, minlength=len(shares))
        apply = (data['halves'] != training) & (data['sentences'] > 0)
        shares[apply] = totals[apply] / data['sentences'][apply]
        detail['applied_half'] = 1 - training
        if not keep_words: detail.pop('words')
        audit.append(detail)
    return shares, audit


def partial_correlation(x, y, controls, weights):
    """Weighted residual Pearson correlation; weights equal person multiplicities."""
    x, y, z, w = np.asarray(x, float), np.asarray(y, float), np.asarray(controls, float), np.asarray(weights, float)
    if z.ndim != 2 or x.ndim != 1 or y.shape != x.shape or w.shape != x.shape or len(z) != len(x):
        raise ValueError('Aligned person arrays required')
    if not np.isfinite(w).all() or (w < 0).any(): raise ValueError('Invalid weights')
    valid = np.isfinite(x) & np.isfinite(y) & np.isfinite(z).all(axis=1) & (w > 0)
    x, y, z, w = x[valid], y[valid], z[valid], w[valid]
    n = len(x)
    if n <= z.shape[1] + 2: raise Unidentified('too few complete distinct people')
    mean = np.average(z, axis=0, weights=w)
    scale = np.sqrt(np.average((z - mean) ** 2, axis=0, weights=w))
    if (scale == 0).any(): raise Unidentified('constant specified control')
    design = np.column_stack((np.ones(n), (z - mean) / scale)); sw = np.sqrt(w)
    weighted = design * sw[:, None]
    beta, _, rank, _ = np.linalg.lstsq(weighted, np.column_stack((x, y)) * sw[:, None], rcond=None)
    if rank != design.shape[1]: raise Unidentified('specified controls are rank deficient')
    for values in (x, y):
        if np.linalg.matrix_rank(np.column_stack((weighted, values * sw))) != rank + 1:
            raise Unidentified('plan or outcome has no residual variation')
    residual = np.column_stack((x, y)) - design @ beta
    ss = np.sum(w[:, None] * residual ** 2, axis=0)
    cross = float(w @ (residual[:, 0] * residual[:, 1]))
    r = float(cross / np.sqrt(ss[0] * ss[1]))
    if not np.isfinite(r) or abs(r) > 1 + 1e-10: raise Unidentified('invalid residual correlation')
    r = float(np.clip(r, -1, 1)); total = float(w @ ((y - np.average(y, weights=w)) ** 2))
    return {'status': 'ok', 'estimate': r, 'people': n, 'person_weight': float(w.sum()),
            'excluded_positive_weight_people': int(np.count_nonzero(np.asarray(weights) > 0)) - n,
            'incremental_R_squared': float(ss[1] * r * r / total), 'control_columns': int(z.shape[1])}


def estimate(data, weights, *, keep_words=False):
    weights = weights_for(data, weights)
    try:
        news, vocabularies = bad_news(data, weights, keep_words=keep_words)
    except Unidentified as error:
        return {'status': 'design cannot test', 'reason': str(error), 'targets': {
            name: {'status': 'unsupported', 'reason': str(error)} for name in TARGETS}}
    controls = np.column_stack((data['length'], news)); values = {}
    for name, column in (('worry', 0), ('anxiety', 1), ('fear', 2), ('relaxation', 3), ('worry_beyond_fear_sadness', 0)):
        z = np.column_stack((controls, data['ratings'][:, [2, 4]])) if name == 'worry_beyond_fear_sadness' else controls
        try: values[name] = partial_correlation(data['plan'], data['ratings'][:, column], z, weights)
        except Unidentified as error: values[name] = {'status': 'unsupported', 'reason': str(error)}
    for name, predictor in (('time_place_named_worry', data['named_plan']),
                            ('time_place_other_worry', data['plan'] - data['named_plan'])):
        if not data['time_place_qualified_input']:
            values[name] = {'status': 'instrument-held', 'reason': 'time/place semantics not qualified'}
        else:
            try: values[name] = partial_correlation(predictor, data['ratings'][:, 0], controls, weights)
            except Unidentified as error: values[name] = {'status': 'unsupported', 'reason': str(error)}
    a, b = values['time_place_named_worry'], values['time_place_other_worry']
    if a['status'] == b['status'] == 'ok':
        if a['people'] != b['people']: raise ValueError('Time/place comparisons must use identical people')
        values['time_place_difference'] = {'status': 'ok', 'estimate': a['estimate'] - b['estimate'], 'people': a['people']}
    else:
        values['time_place_difference'] = {'status': 'instrument-held' if not data['time_place_qualified_input'] else 'unsupported',
                                           'reason': 'both time/place comparisons required'}
    return {'status': 'ok', 'targets': values, 'vocabularies': vocabularies,
            'half_manifest_sha256': data['half_manifest_sha256']}


def bootstrap_draw(data, ordinal):
    if type(ordinal) is not int or ordinal < 0: raise ValueError('Nonnegative draw ordinal required')
    n = len(data['people']); rng = np.random.default_rng(np.random.SeedSequence([SEED, ordinal, 33]))
    weights = np.bincount(rng.integers(n, size=n), minlength=n)
    return estimate(data, weights)


def classify_interval(interval):
    a = np.asarray(interval, float)
    if a.shape != (2,) or not np.isfinite(a).all() or not -1 <= a[0] <= a[1] <= 1:
        raise ValueError('Ordered finite correlation interval required')
    if a[1] < BAR: return 'supports'
    if a[0] > 0 or (a[0] >= BAR and a[1] <= -BAR): return 'against'
    return 'inconclusive'


def summarize(point, bank):
    if len(bank) != 2000: raise ValueError('Complete 2000-person-draw bank required')
    result = {}
    for name in TARGETS:
        item = point['targets'][name]
        if item['status'] != 'ok':
            result[name] = {**item, 'outcome': None}; continue
        failed = [i for i, draw in enumerate(bank) if draw['targets'][name]['status'] != 'ok']
        if failed:
            result[name] = {**item, 'status': 'invalid uncertainty', 'outcome': None,
                            'failed_draw_ordinals': failed}; continue
        values = np.asarray([draw['targets'][name]['estimate'] for draw in bank])
        interval = np.quantile(values, [.025, .975]).tolist()
        se = float(np.std(values - values[0], ddof=1))
        status = 'below floor, descriptive' if item['people'] < 20 else 'degenerate, descriptive' if se == 0 else 'ok'
        result[name] = {**item, 'status': status, 'interval': interval, 'bootstrap_SE': se,
            'outcome': classify_interval(interval) if name == 'worry' and status == 'ok' else None,
            'scope': 'primary' if name == 'worry' else 'descriptive secondary; no additional primary decision'}
        if name == 'worry':
            result[name].update(bar=BAR, sees_magnitude=2.8 * se, supports_at=BAR - 2.8 * se)
    return result
