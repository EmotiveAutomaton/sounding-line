"""S6 paired joint fits and complete references on fixed onset support.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-7, 2026-11-04. Known zero,
positive and negative personal effects keep their values; conflict-only
confounding is removed by the adjusted model. Collinear focal terms and any
undefined draw invalidate rather than redraw. Every paired draw uses identical
writers. No p-value from a successful subset or unfinished reference bank.
"""
from types import FunctionType
import math
import numpy as np
from . import timing_d33_supported_stats as original
from .timing_stats import sufficient

NAMES = original.NAMES+('entropy', 'negative_margin')


def copied(function, **changes):
    return FunctionType(function.__code__, dict(function.__globals__, **changes),
                        function.__name__, function.__defaults__, function.__closure__)


_basis = copied(original.basis, NAMES=NAMES)


def basis(groups):
    keep, omitted = _basis(groups)
    if any(n in omitted for n in NAMES[-2:]):
        raise ValueError('Conflict coefficients not separately identifiable')
    return keep, omitted


adjusted_fit = copied(original.fit, NAMES=NAMES, basis=basis)


def design(rows):
    x, y, w = original.design(rows)
    conflict = np.asarray([[r['entropy'], r['negative_margin']] for r in rows], float)
    if not np.isfinite(conflict).all():
        raise ValueError('Nonfinite conflict features')
    return np.column_stack([x, conflict]), y, w


def paired_fit(groups, base_groups):
    a, b = adjusted_fit(groups), original.fit(base_groups)
    return dict(adjusted_own=a['own'], original_own=b['own'],
                paired_difference=a['own']-b['own'], entropy=a['coefficients']['entropy'],
                negative_margin=a['coefficients']['negative_margin'],
                adjusted=a, original=b)


MEASURES = ('adjusted_own', 'original_own', 'paired_difference', 'entropy', 'negative_margin')


def run(rows, blocks=10, progress=None, seed=20261102):
    if blocks not in (1, 10):
        raise ValueError('Only first tenth or complete inference')
    x, y, w = design(rows); writers = sorted(set(w))
    if len(writers) != 20:
        raise ValueError('Exactly twenty frozen writers required')
    groups, base = sufficient(x, y, w), sufficient(x[:, :10], y, w)
    try:
        point = paired_fit(groups, base)
    except ValueError as exc:
        return dict(state='invalid', reason=str(exc), attempted_bootstraps=0)
    rng = np.random.default_rng(seed); draws = []; controls = []
    ix_by_writer = [np.flatnonzero(w == writer) for writer in writers]
    for block in range(blocks):
        for _ in range(200):
            ids = rng.integers(0, len(writers), len(writers))
            try:
                draws.append(paired_fit([groups[i] for i in ids], [base[i] for i in ids]))
            except ValueError as exc:
                return dict(state='invalid', reason='undefined paired bootstrap: '+str(exc),
                            attempted_bootstraps=len(draws)+1)
        source_rng = np.random.default_rng(np.random.SeedSequence([seed, block, 1]))
        outcome_rng = np.random.default_rng(np.random.SeedSequence([seed, block, 2]))
        for _ in range(20):
            xx, yy = x.copy(), y.copy()
            for ix in ix_by_writer:
                xx[ix, 0] = source_rng.permutation(x[ix, 0])
                yy[ix] = outcome_rng.permutation(y[ix])
            item = {}
            for name, a, b in [('own_surprise', xx, y), ('outcome', x, yy)]:
                try:
                    item[name] = dict(effect=adjusted_fit(sufficient(a, b, w))['own'], reason=None)
                except ValueError as exc:
                    item[name] = dict(effect=None, reason=str(exc))
            controls.append(item)
        if progress is not None:
            progress(dict(blocks=block+1, total_blocks=blocks, bootstraps=len(draws), permutations=len(controls)))
    statistics = {k: original.interval(point[k], [r[k] for r in draws]) for k in MEASURES}
    reference = {k: original.null_summary([r[k]['effect'] for r in controls], point['adjusted_own'])
                 for k in ('own_surprise', 'outcome')}
    return dict(state='complete' if blocks==10 else 'cost_only', point=point,
                statistics=statistics, controls=reference, bootstrap_draws=len(draws),
                permutation_draws=len(controls), writer_count=len(writers), observations=len(rows),
                complete_banks=blocks==10, bootstrap_values=[{k:r[k] for k in MEASURES} for r in draws],
                reference_values=controls, causal_claim=False)


WORLDS = ('null', 'own', 'reverse', 'conflict_only', 'own_and_conflict', 'donor_only')


def world(name):
    if name not in WORLDS:
        raise ValueError('Unknown calibration world')
    rng = np.random.default_rng(20261102); rows = []
    beta = np.array([0., .25 if name=='donor_only' else 0., .4, .1, .08, -.1, .1, -.1, .2, .1, 0., 0.])
    beta[0] = .4 if name in ('own', 'own_and_conflict') else -.4 if name=='reverse' else 0.
    if name in ('conflict_only', 'own_and_conflict'):
        beta[-2:] = [.6, .4]
    for wi in range(20):
        x = rng.normal(size=(80, 12)); x[:, 2] = 1.
        x[:, -2] = np.exp(.25*x[:, -2]); x[:, -1] = -1/(1+np.exp(x[:, -1]))
        x[:, 0] += 2*x[:, -2]
        # Equal covariate means in every cluster keep its random intercept
        # orthogonal to slopes; orthogonal residuals alone do not ensure this.
        for j in range(12):
            if j != 2:
                x[:, j] -= x[:, j].mean()
        x[:, -2] += 1.; x[:, -1] -= .5
        # Centering and orthogonal residuals are a known-answer construction, not an empirical
        # sensitivity estimate. Within-writer orthogonality survives resampling.
        noise = rng.normal(size=len(x))
        noise -= x@np.linalg.lstsq(x, noise, rcond=None)[0]
        y = x@beta+.3*noise+.2*rng.normal()
        for i in range(len(x)):
            r = dict(zip(NAMES, x[i].tolist()))
            r.update(writer=f'w{wi:02}', log_pause=float(y[i]), original_personal_surprise=r['own_surprise'])
            rows.append(r)
    return rows, dict(zip(NAMES, beta.tolist()))


def known_answers():
    results = {}
    for name in WORLDS:
        rows, truth = world(name); x, y, w = design(rows)
        groups = sufficient(x, y, w); fit = adjusted_fit(groups)
        for key in ('own_surprise', 'donor_surprise', 'entropy', 'negative_margin'):
            if abs(fit['coefficients'][key]-truth[key]) > 2e-8:
                raise ValueError('Known coefficient failed: '+name+'/'+key)
        # Independent dense GLS inversion at the fitted variance ratio.
        ratio = fit['variance_ratio']; a = np.zeros((12,12)); b = np.zeros(12)
        for writer in sorted(set(w)):
            xx, yy = x[w==writer], y[w==writer]
            inverse = np.eye(len(yy))-ratio/(1+len(yy)*ratio)*np.ones((len(yy), len(yy)))
            a += xx.T@inverse@xx; b += xx.T@inverse@yy
        dense = np.linalg.solve(a,b)
        if not np.allclose(dense, [fit['coefficients'][n] for n in NAMES], atol=2e-8, rtol=0):
            raise ValueError('Dense GLS coefficient mismatch')
        base = original.fit(sufficient(x[:, :10], y, w))
        if name=='conflict_only' and base['own'] <= .02:
            raise ValueError('Constructed confounding not realized')
        results[name] = dict(truth={k:truth[k] for k in ('own_surprise','entropy','negative_margin')},
                             verified=True, dense_gls_verified=True)
    return results
