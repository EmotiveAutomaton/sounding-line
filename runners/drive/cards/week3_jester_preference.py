"""Separate CA5.r lexical-topic preference recurrence; full populations only.

DESIGN CHECK: LESSONS 3-5, CONTROLS 1-7, 2026-10-26. Sparse additive
person/item null must cancel exactly; stable topic preference is positive and
half reversal negative. Every reference refits nuisance effects on the same
observed cells. Constant profiles contribute zero, never cause person deletion.
See the frozen CA5R_PREFERENCE_20261026 design for exhaustive decision bands.
"""
from __future__ import annotations
import hashlib
import warnings
from pathlib import Path
import numpy as np
from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.exceptions import ConvergenceWarning
from .timing_census import read, filehash
from .timing_p6 import write_equal
from . import week3_jester_support as support

SEED = 20261026
K = 8


def text_features(records):
    """Only text enters this function; all tokens, no rating-dependent choices."""
    if (len(records) != 150 or sorted(r['joke_id'] for r in records) != list(range(1, 151))
            or any(not isinstance(r['text'], str) or not r['text'].strip() for r in records)):
        raise ValueError('all unique nonempty joke texts required')
    records = sorted(records, key=lambda r: r['joke_id'])
    vectorizer = TfidfVectorizer(lowercase=True, stop_words='english', ngram_range=(1, 2),
        min_df=2, max_df=.95, sublinear_tf=True, norm='l2')
    x = vectorizer.fit_transform([r['text'] for r in records])
    if x.shape[1] < K or np.any(np.asarray(x.sum(axis=1)).ravel() == 0):
        raise ValueError('text representation unsupported')
    model = NMF(n_components=K, init='nndsvda', solver='cd', beta_loss='frobenius',
        max_iter=2000, tol=1e-5, random_state=SEED)
    with warnings.catch_warnings():
        warnings.simplefilter('error', ConvergenceWarning)
        w = model.fit_transform(x)
    if np.any(w.sum(1) <= 0) or not np.isfinite(w).all():
        raise ValueError('empty/nonfinite topic representation')
    w /= w.sum(1, keepdims=True)
    soft = np.exp(4 * (w - w.max(1, keepdims=True)))
    soft /= soft.sum(1, keepdims=True)
    vocab = vectorizer.get_feature_names_out().tolist()
    return dict(joke_ids=list(range(1, 151)), weights=soft.tolist(), vocabulary=vocab,
        idf=vectorizer.idf_.tolist(), components=model.components_.tolist(),
        iterations=int(model.n_iter_), top_terms=[[vocab[j] for j in np.argsort(-row, kind='stable')[:12]]
            for row in model.components_], seed=SEED, features_from_text_only=True,
        scope='Eight lexical topic proxies; not validated psychological categories.')


class Half:
    """Exact observed-cell two-way projection, cached by exposure mask."""
    def __init__(self, mask, features):
        self.mask = np.asarray(mask, bool)
        self.w = self.mask.astype(float)
        self.features = np.asarray(features, float)
        self.n = self.w.sum(1)
        if (np.any(self.n == 0) or self.w.shape[1] != len(self.features)
                or self.features.shape[1] != K or not np.isfinite(self.features).all()
                or np.any(self.features <= 0)):
            raise ValueError('unsupported half or invalid topic weights')
        normal = np.diag(self.w.sum(0)) - self.w.T @ (self.w / self.n[:, None])
        self.inverse = np.linalg.pinv(normal, rcond=1e-12, hermitian=True)
        self.weight = self.w @ self.features
        self.rows, self.cols = np.where(self.mask)
        self.by_item = [np.flatnonzero(self.mask[:, j]) for j in range(self.mask.shape[1])]
        self.by_count = {int(c): np.flatnonzero(self.n == c) for c in np.unique(self.n)}

    def residuals(self, y):
        if y.shape != self.mask.shape or not np.isfinite(y[self.mask]).all():
            raise ValueError('changed ratings shape or nonfinite observed value')
        y = np.where(self.mask, y, 0.)
        mean = y.sum(1) / self.n
        b = y.sum(0) - self.w.T @ mean
        beta = self.inverse @ b
        alpha = (y.sum(1) - self.w @ beta) / self.n
        e = np.where(self.mask, y - alpha[:, None] - beta, 0.)
        tol = 1e-8 * max(1., float(np.max(np.abs(y))))
        if max(np.max(np.abs(e.sum(0)) / np.maximum(1, self.w.sum(0))),
               np.max(np.abs(e.sum(1)) / self.n)) > tol:
            raise ValueError('additive least-squares certificate failed')
        e[np.abs(e) < 1e-10] = 0.
        return e

    def profiles(self, residuals):
        p = (residuals @ self.features) / self.weight
        return p - p.mean(1, keepdims=True)

    def shuffle(self, residuals, rng, kind):
        out = np.zeros_like(residuals)
        if kind == 'item':
            for j, ix in enumerate(self.by_item):
                out[ix, j] = residuals[rng.permutation(ix), j]
        elif kind == 'person':
            # Group equal row counts so no missing value can enter a permutation.
            for count, ix in self.by_count.items():
                col = np.where(self.mask[ix])[1].reshape(len(ix), count)
                source = residuals[ix[:, None], col]
                order = np.argsort(rng.random(source.shape), axis=1)
                out[ix[:, None], col] = np.take_along_axis(source, order, axis=1)
        else:
            raise ValueError('unknown permutation')
        return self.residuals(out)


def correlations(left, right):
    a, b = left - left.mean(1, keepdims=True), right - right.mean(1, keepdims=True)
    den = np.sqrt((a*a).sum(1) * (b*b).sum(1))
    zero = den <= 1e-18
    return np.divide((a*b).sum(1), den, out=np.zeros(len(a)), where=~zero), zero


def prepare(y, weights):
    if y.ndim != 2 or y.shape[1] != len(weights) or np.isinf(y).any():
        raise ValueError('invalid rating matrix')
    halves = [Half(np.isfinite(y[:, h::2]), weights[h::2]) for h in (0, 1)]
    return halves, [part.residuals(y[:, h::2]) for h, part in enumerate(halves)]


def reference(halves, residuals, draws, kind):
    sums = np.zeros(len(residuals[0])); means = []
    for d in range(draws):
        rng = np.random.default_rng(SEED + (0 if kind == 'item' else 100000) + d)
        profiles = [h.profiles(h.shuffle(e, rng, kind)) for h, e in zip(halves, residuals)]
        v, _ = correlations(*profiles)
        sums += v; means.append(float(v.mean()))
    return sums / draws, np.asarray(means)


def paired_interval(real, reference_mean, draws=2000):
    delta = real - reference_mean
    rng = np.random.default_rng(SEED + 200000)
    boot = np.empty(draws)
    for i in range(draws):
        boot[i] = delta[rng.integers(0, len(delta), len(delta))].mean()
    return np.quantile(boot, [.025, .975]).tolist()


def bank_summary(real, null_people, null_means, bootstrap_draws=2000):
    mean = float(real.mean()); mu = float(null_means.mean()); sd = float(null_means.std(ddof=1))
    interval = paired_interval(real, null_people, bootstrap_draws)
    p = float((1 + np.count_nonzero(null_means >= mean)) / (len(null_means) + 1))
    reverse_p = float((1 + np.count_nonzero(null_means <= mean)) / (len(null_means) + 1))
    if interval[0] > 0 and p < .05:
        state = 'positive'
    elif interval[1] < 0 and reverse_p < .05:
        state = 'negative'
    elif min(p, reverse_p) < .10:
        state = 'marginal'
    else:
        state = 'null'
    return dict(real_mean=mean, reference_mean=mu, reference_sd=sd,
        reference_interval=np.quantile(null_means, [.025, .975]).tolist(),
        paired_difference=float(np.mean(real-null_people)), paired_interval=interval,
        p=p, reverse_p=reverse_p, state=state, draws=len(null_means),
        mean_bias_flag=bool(abs(mu) > .25*sd if sd > 0 else abs(mu) > 1e-12),
        reference_draws=null_means.tolist())


def calculate(y, weights, item_draws=1000, person_draws=200, bootstrap_draws=2000):
    if len(y) < 4:
        return dict(state='unsupported', reason='fewer than four persons')
    halves, residuals = prepare(y, weights)
    real, zero = correlations(*(h.profiles(e) for h,e in zip(halves,residuals)))
    result = dict(persons=len(y), observed=int(np.isfinite(y).sum()), all_persons_retained=True,
        constant_profiles=int(zero.sum()))
    for kind, draws in [('item', item_draws), ('person', person_draws)]:
        people, means = reference(halves, residuals, draws, kind)
        result[kind] = bank_summary(real, people, means, bootstrap_draws)
    result['state'] = result['item']['state']
    result['control_status'] = 'biased reference' if result['person']['mean_bias_flag'] else 'passes'
    return result


def load_ratings(inputs, config):
    source_inputs = {k: inputs[k] for k in support.INPUTS}
    summary, bindings = support.census(source_inputs, config)
    root = Path(inputs['source_complete']).resolve().parent/'output'
    ix = read(root/'RATINGS_INDEX.json')
    y = np.concatenate([np.load(root/r['file'], allow_pickle=False) for r in ix['chunks']])
    return y, summary, bindings


def planted_world(effect=4., reverse=False, seed=33, n=160):
    """Paired text coordinates/exposure give a known consistent or reversed target.

    Distinct synthetic items have identical feature coordinates in paired halves;
    the full corpus's unequal coordinates are checked separately, never altered.
    """
    rng = np.random.default_rng(seed)
    base = np.exp(rng.normal(size=(20,K))); base /= base.sum(1,keepdims=True)
    weights = np.repeat(base,2,axis=0)
    person = rng.normal(size=(n,1)); item = rng.normal(size=(1,40))
    mask = rng.random((n,20)) < 1/(1+np.exp(-person))
    mask[:,:4] = True; mask = np.repeat(mask,2,axis=1)
    taste = rng.normal(size=(n,K)) @ weights.T
    if reverse: taste[:,1::2] *= -1
    y = person+item+effect*taste+rng.normal(size=(n,40))*.08
    return np.where(mask,y,np.nan),weights
