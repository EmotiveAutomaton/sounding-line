"""Saved main-cell analysis. No inference, fitting, selection or provider access.

DESIGN CHECK: LESSONS 3-5, CONTROLS. NULL: identical paired losses give zero
gain and p=1; balanced uninformed vectors give half-Brier .375. ALTERNATIVE:
positive rival-minus-reader loss with both a positive writer interval and Holm
support identifies a conditional forecast advantage. Invalids cost one, never
disappear from system loss. Missing API tests remain unavailable in a family of
eleven. Wide intervals are unresolved, not parity. Fixed descriptive sensitivities
do not select a model, roster, control, gate or subsequent provider request.
"""
import math
from collections import Counter
from pathlib import Path

import numpy as np

from runners.stage14.common import REPO, read, freeze, filehash
from .data import RAW, ROOT, ACTIONS
from .protocol import parse, verify_rows

SEED = 20261014
DRAWS = 10000


def histogram(values):
    """JSON-stable histogram keys, including on immutable reentry."""
    return {str(k): v for k, v in Counter(values).items()}


def score(probabilities, truth, choice=None):
    if probabilities is None:
        return dict(half_brier=1., log_loss=None, system_log_loss=-math.log(.01), accuracy=0.)
    p = np.asarray(probabilities, dtype=float)
    if p.shape != (4,) or not np.isfinite(p).all() or (p < 0).any() or not math.isclose(float(p.sum()), 1., abs_tol=1e-12):
        raise ValueError('invalid scored vector')
    if choice is None:
        choice = int(p.argmax())
    loss = -math.log(max(float(p[truth]), 1e-300))
    return dict(half_brier=float(.5 * np.sum((p - np.eye(4)[truth]) ** 2)),
                log_loss=loss, system_log_loss=loss, accuracy=float(choice == truth))


def writer_values(rows, values):
    if not rows or len(rows) != len(values) or not np.isfinite(values).all():
        raise ValueError('invalid comparison support')
    writers = sorted({r['writer'] for r in rows})
    return writers, np.array([np.mean([v for r, v in zip(rows, values) if r['writer'] == w]) for w in writers])


def paired(rows, values, p_value=False):
    writers, means = writer_values(rows, values)
    n = len(writers)
    rng = np.random.default_rng(SEED)
    boot = rng.choice(means, size=(DRAWS, n)).mean(axis=1)
    prompts = sorted({r['prompt'] for r in rows})
    sums = np.zeros((n, len(prompts)))
    counts = np.zeros_like(sums)
    wi, pi = {w: i for i, w in enumerate(writers)}, {p: i for i, p in enumerate(prompts)}
    for r, v in zip(rows, values):
        i, j = wi[r['writer']], pi[r['prompt']]
        sums[i, j] += v
        counts[i, j] += 1
    # Independent multinomial resampling of writers and fixed prompt clusters.
    rng = np.random.default_rng(SEED)
    wc = rng.multinomial(n, np.full(n, 1/n), size=DRAWS)
    pc = rng.multinomial(len(prompts), np.full(len(prompts), 1/len(prompts)), size=DRAWS)
    den = pc @ counts.T
    present = den > 0
    per_writer = np.divide(pc @ sums.T, den, out=np.zeros_like(den), where=present)
    weight = wc * present
    good = weight.sum(axis=1) > 0
    cross = (per_writer[good] * weight[good]).sum(axis=1) / weight[good].sum(axis=1)
    out = dict(mean=float(means.mean()), interval=np.quantile(boot, [.025, .975]).tolist(),
               crossed_interval=np.quantile(cross, [.025, .975]).tolist(),
               crossed_nonempty_draws=int(good.sum()), writers=n, targets=len(rows), prompts=len(prompts))
    if p_value:
        signs = np.random.default_rng(SEED).choice([-1., 1.], size=(DRAWS, n))
        randomized = np.abs((signs * means).mean(axis=1))
        out['p_raw'] = float((1 + np.sum(randomized >= abs(means.mean()) - 1e-15)) / (DRAWS + 1))
    return out


def holm(pvalues, family):
    if set(pvalues) - set(family) or len(set(family)) != len(family):
        raise ValueError('unexpected or duplicate primary contrast')
    ordered = sorted(family, key=lambda k: (pvalues.get(k, 1.), k))
    maximum = 0.
    adjusted = {}
    for i, name in enumerate(ordered):
        maximum = min(1., max(maximum, (len(family) - i) * pvalues.get(name, 1.)))
        adjusted[name] = maximum if name in pvalues else None
    return adjusted


def calibration(probabilities, choices, truths, weights):
    if not probabilities:
        return None
    weights = np.asarray(weights, dtype=float)
    weights /= weights.sum()
    bins = [dict(lower=i/10, upper=(i+1)/10, n=0, weight=0., confidence=0., accuracy=0.) for i in range(10)]
    mismatches = 0
    for p, choice, truth, weight in zip(probabilities, choices, truths, weights):
        confidence = float(p[choice])
        b = bins[min(9, int(confidence * 10))]
        b['n'] += 1
        b['weight'] += float(weight)
        b['confidence'] += float(weight) * confidence
        b['accuracy'] += float(weight) * (choice == truth)
        mismatches += p[choice] < max(p) - 1e-12
    ece = 0.
    for b in bins:
        if b['weight']:
            b['confidence'] /= b['weight']
            b['accuracy'] /= b['weight']
            ece += b['weight'] * abs(b['confidence'] - b['accuracy'])
        else:
            b['confidence'] = b['accuracy'] = None
    return dict(ece=float(ece), bins=bins, choice_argmax_mismatches=int(mismatches))


def compare(rows, predictions, arm, rival, metric, p_value=False):
    kept = [r for r in rows if predictions[r['key']][arm]['scores'][metric] is not None
            and predictions[r['key']][rival]['scores'][metric] is not None]
    if not kept:
        return dict(arm=arm, rival=rival, metric=metric, available=False)
    values = [predictions[r['key']][rival]['scores'][metric] - predictions[r['key']][arm]['scores'][metric] for r in kept]
    return dict(arm=arm, rival=rival, metric=metric, available=True,
                excluded_targets=len(rows)-len(kept), **paired(kept, values, p_value))


def run(out=None):
    out = Path(out) if out else RAW / 'modal-analysis-v2'
    data, producer = RAW / 'data-v2', RAW / 'modal-main-v1'
    files = [ROOT/'PLAN.json', producer/'COMPLETE.json', producer/'restored/TERMINAL.json',
             RAW/'MODAL_REQUESTS.json', RAW/'baselines-v1/COMPLETE.json', RAW/'baselines-v1/PREDICTIONS.json',
             RAW/'SM1_STAGE14_EXPOSURE.json', *sorted(data.glob('*.json')),
             Path(__file__), REPO/'runners/stage14_midweek/protocol.py', REPO/'runners/stage14/common.py']
    config = dict(source_pins={p.relative_to(REPO).as_posix(): filehash(p) for p in files}, seed=SEED, draws=DRAWS,
        implementation_timing='v1 frozen and known-answer tested postcollection before first scoring; v2 only makes histogram keys JSON-stable after v1 reentry refusal; all statistics unchanged',
        primary='writer-mean system half-Brier; positive gain favors reader',
        log_loss='pairwise identical valid support; invalid sensitivity at -log(.01); saved baseline probabilities unchanged',
        p_values='two-sided writer sign-flip, 10000 Monte Carlo signs with plus-one correction; shared-history dependence limits',
        holm='eleven frozen primary slots; missing API slots conservatively occupy p=1, but are reported unavailable',
        calibration='10 literal bins [0,.1),...,[.9,1]; confidence in stated choice, not maximum when they differ; valid support equal-writer weighted',
        sensitivity='full-sixteen own histories; donor character ratio [.85,1.15]; both conditions; fixed before scoring',
        claims='completed Modal cell only; unfinished API comparisons remain unavailable; final-packet policy')
    freeze(out/'ANALYSIS_PLAN.json', config)
    plan = read(ROOT/'PLAN.json')
    for path, expected in plan['source_pins'].items():
        if filehash(REPO/path) != expected:
            raise ValueError('source binding changed: '+path)
    for name, expected in read(RAW/'baselines-v1/COMPLETE.json')['outputs'].items():
        if filehash(RAW/'baselines-v1'/name) != expected:
            raise ValueError('baseline output changed')
    terminal = read(producer/'restored/TERMINAL.json')
    requests = read(RAW/'MODAL_REQUESTS.json')['main']
    valid = verify_rows(terminal['rows'], requests)
    if terminal['status'] != 'COMPLETE' or sum(valid) != read(producer/'COMPLETE.json')['valid']:
        raise ValueError('unfinished or inconsistent producer')
    rows = [r for r in read(data/'EVALUATOR.json') if not r['pilot']]
    targets = {r['key']: r for r in rows}
    bundles = {r['id']: r for r in read(data/'READER.json') if not r['pilot'] and r['arm'] in ('H0', 'H1', 'H2', 'H3')}
    if len(bundles) != len(requests) or {r['target'] for r in bundles.values()} != set(targets):
        raise ValueError('main roster differs')
    predictions = {r['key']: {} for r in rows}
    for row, ok in zip(terminal['rows'], valid):
        b = bundles[row['id']]
        parsed = parse(row['response'].get('response', '')) if ok else None
        p = parsed['probabilities'] if parsed else None
        choice = ACTIONS.index(parsed['choice']) if parsed else None
        predictions[b['target']]['R27.'+b['arm']] = dict(valid=ok, probabilities=p, choice=choice,
            scores=score(p, ACTIONS.index(targets[b['target']]['handling']), choice))
    baseline = read(RAW/'baselines-v1/PREDICTIONS.json')
    if len(baseline) != len(rows) or {r['key'] for r in baseline} != set(targets):
        raise ValueError('baseline support differs')
    for b in baseline:
        t = targets[b['key']]
        if (b['writer'], b['prompt'], b['pilot']) != (t['writer'], t['prompt'], False):
            raise ValueError('baseline target binding')
        for arm, p in b['probabilities'].items():
            s = score(p, ACTIONS.index(t['handling']))
            if any(not math.isclose(s[k], v, abs_tol=1e-12) for k, v in b['scores'][arm].items()):
                raise ValueError('saved baseline score differs')
            predictions[b['key']][arm] = dict(valid=True, probabilities=p, choice=int(np.argmax(p)), scores=s)
    arms = sorted(next(iter(predictions.values())))
    if any(sorted(p) != arms for p in predictions.values()):
        raise ValueError('missing prediction arm')
    arm_reports = []
    for arm in arms:
        report = dict(arm=arm, valid=sum(predictions[r['key']][arm]['valid'] for r in rows), targets=len(rows))
        for metric in ('half_brier', 'log_loss', 'system_log_loss', 'accuracy'):
            kept = [r for r in rows if predictions[r['key']][arm]['scores'][metric] is not None]
            values = [predictions[r['key']][arm]['scores'][metric] for r in kept]
            report[metric] = paired(kept, values) if kept else None
        kept = [r for r in rows if predictions[r['key']][arm]['valid']]
        counts = Counter(r['writer'] for r in kept)
        weights = [1/counts[r['writer']] for r in kept]
        ps = [predictions[r['key']][arm]['probabilities'] for r in kept]
        choices = [predictions[r['key']][arm]['choice'] for r in kept]
        truths = [ACTIONS.index(r['handling']) for r in kept]
        report['calibration'] = calibration(ps, choices, truths, weights)
        report['valid_class_marginals'] = dict(predicted=np.average(ps, axis=0, weights=weights).tolist(),
            observed=np.average(np.eye(4)[truths], axis=0, weights=weights).tolist(),
            choices=np.average(np.eye(4)[choices], axis=0, weights=weights).tolist()) if kept else None
        arm_reports.append(report)
    pairs = {(a, b) for a in arms if a.startswith('R27.') for b in ('B-pop', 'B-writer', 'B-last', 'B-mixlogit')}
    pairs.update([('R27.H1','R27.H2'), ('R27.H2','R27.H3'), ('R27.H2','R27.H0')])
    contrasts = []
    per_writer = []
    for arm, rival in sorted(pairs):
        for metric in ('half_brier', 'log_loss', 'system_log_loss'):
            result = compare(rows, predictions, arm, rival, metric, metric == 'half_brier')
            result['name'] = arm+'-'+rival
            result['primary'] = metric == 'half_brier' and result['name'] in plan['primary_contrasts']
            contrasts.append(result)
            kept = [r for r in rows if all(predictions[r['key']][a]['scores'][metric] is not None for a in (arm, rival))]
            if kept:
                ws, values = writer_values(kept, [predictions[r['key']][rival]['scores'][metric]-predictions[r['key']][arm]['scores'][metric] for r in kept])
                per_writer.extend(dict(writer=w, arm=arm, rival=rival, metric=metric, gain=float(v)) for w,v in zip(ws, values))
    primary = [c for c in contrasts if c['primary']]
    adjusted = holm({c['name']:c['p_raw'] for c in primary}, plan['primary_contrasts'])
    for c in primary:
        c['p_holm_11'] = adjusted[c['name']]
        c['direction'] = ('reader_better' if c['interval'][0]>0 else 'reader_worse' if c['interval'][1]<0 else 'unresolved')
        c['affirmative_advantage'] = c['interval'][0]>0 and c['p_holm_11']<.05
    training = read(data/'TRAINING.json')
    sensitivities = []
    predicates = {'full_sixteen':lambda c:len(c['h2'])==16,
                  'donor_length_matched':lambda c:.85<=c['donor_length_ratio']<=1.15,
                  'both':lambda c:len(c['h2'])==16 and .85<=c['donor_length_ratio']<=1.15}
    for subset, predicate in predicates.items():
        selected = [r for r in rows if predicate(training[r['writer']])]
        for c in primary:
            sensitivities.append(dict(subset=subset, **compare(selected, predictions, c['arm'], c['rival'], 'half_brier')))
    roster = [r for r in read(data/'ROSTER.json') if not r['pilot']]
    writers = {r['writer'] for r in rows}
    summary = dict(status='COMPLETE_MODAL_CELL_API_UNAVAILABLE', writers=len(writers), targets=len(rows),
        prompts=len({r['prompt'] for r in rows}), attempted=len(valid), valid=sum(valid), invalid=len(valid)-sum(valid),
        arms=arm_reports, contrasts=contrasts, primary_family=plan['primary_contrasts'],
        unavailable_primary=[n for n in plan['primary_contrasts'] if n not in {c['name'] for c in primary}],
        unavailable_secondary=['RS/RH H2e-H2','RS/RH M1-M0','RS/RH compression share','RH/RS/RO H2-H3 ladder'],
        sensitivities=sensitivities, observed_classes=dict(Counter(r['handling'] for r in rows)),
        target_counts_per_writer=histogram(sum(r['writer']==w for r in rows) for w in writers),
        own_history_counts=histogram(len(training[w]['h2']) for w in writers),
        donor_history_counts=histogram(len(training[w]['h3']) for w in writers),
        unmatched_donor_writers=sum(not .85<=training[w]['donor_length_ratio']<=1.15 for w in writers),
        frozen_exposure=dict(Counter(r['exposure'] for r in roster)),
        exposure_note='Stage14 supplement is an additional positive witness only; absent witnesses never imply fresh evidence',
        analysis_plan_sha256=filehash(out/'ANALYSIS_PLAN.json'), inference_calls=0,
        limits='historical exposed/unknown human process records; fixed prompts; shared own/donor histories; writer independence not established; conditional comparisons are not causal value identification or proof of absent personal information')
    freeze(out/'PREDICTIONS.json', predictions)
    freeze(out/'PER_WRITER.json', per_writer)
    freeze(out/'SUMMARY.json', summary)
    freeze(out/'COMPLETE.json', dict(status='COMPLETE', outputs={n:filehash(out/n) for n in ('ANALYSIS_PLAN.json','PREDICTIONS.json','PER_WRITER.json','SUMMARY.json')}, inference_calls=0))
    return dict(status='COMPLETE', writers=len(writers), targets=len(rows), inference_calls=0)


if __name__ == '__main__':
    print(run())
