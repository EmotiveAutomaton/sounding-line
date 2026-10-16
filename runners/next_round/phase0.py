"""Phase 0 local saved-output work. No provider or model calls.

DESIGN CHECK: LESSONS 2-5 / CONTROLS read 2026-10-14. NULL: label
permutations and constant forecasts cannot pass as informative; held-out or
unresolved labels cannot change a forecast. ALTERNATIVE: historical, planted
maker signal beats pooled frequencies. Empty/nonfinite or source-changed inputs
fail closed. Historically exposed CoAuthor supports descriptive screens only.
"""
from collections import Counter, defaultdict
import time
import numpy as np
from scipy.special import softmax
from runners.stage14.common import REPO, read, freeze, atomic, filehash, check_pins, digest
from runners.stage14_midweek.baselines import global_fit, intercept_fit, matrix, features
from runners.stage14_midweek.data import ACTIONS
from runners.stage14_midweek.analyze_modal import paired
from .statistics import losses, outer_fold, random_effects

BASE = REPO / 'results/gear3/G3-S14-MAKER-1/raw'


def verify_manifest(folder):
    d = read(folder/'COMPLETE.json')
    if d['status'].upper() != 'COMPLETE' or not d['outputs']:
        raise ValueError('not a complete input')
    for name, expected in d['outputs'].items():
        if filehash(folder/name) != expected: raise ValueError('saved input changed: ' + name)
    return d


def saved():
    verify_manifest(BASE/'modal-analysis-v2'); verify_manifest(BASE/'baselines-v1')
    p = read(BASE/'modal-analysis-v2/PREDICTIONS.json')
    rows = [r for r in read(BASE/'data-v2/EVALUATOR.json') if not r['pilot']]
    rows.sort(key=lambda r: r['key'])
    if {r['key'] for r in rows} != set(p): raise ValueError('target support changed')
    y = np.array([ACTIONS.index(r['handling']) for r in rows])
    return rows, p, y


def t0a(folder, guard):
    rows, p, y = saved(); groups = np.array([r['writer'] for r in rows])
    gains = np.array([p[r['key']]['B-pop']['scores']['half_brier'] -
                      p[r['key']]['B-mixlogit']['scores']['half_brier'] for r in rows])
    fit = random_effects(gains, groups); names = sorted(set(groups)); draws = []
    rng = np.random.default_rng(151014)
    for b in range(2000):
        sample = rng.choice(names, len(names)); x = []; g = []
        for i, name in enumerate(sample):
            values = gains[groups == name]; x.extend(values); g.extend([str(i)]*len(values))
        f = random_effects(x, g); draws.append([f['within_variance'], f['between_variance'], f['icc']])
        if b % 100 == 0: guard('T0a', dict(bootstrap=b, total=2000))
    fit['cluster_bootstrap_95'] = dict(zip(('within_variance','between_variance','icc'),
                                         np.quantile(draws, [.025,.975], axis=0).T.tolist()))
    fit['paired_gain'] = paired(rows, gains)
    fit['limitations'] = ['Unequal-size random-intercept ANOVA; not causal person signal.',
        'Prompt and shared-history dependence are not explained by this decomposition.',
        'Intervals resample makers; prompt-crossed gain sensitivity is separate.',
        'Observed maker spread does not prove that additional decisions cannot help.']
    freeze(folder/'SUMMARY.json', fit)
    freeze(folder/'PER_WRITER.json', [dict(writer=w, decisions=int(np.sum(groups==w)),
        mean_gain=float(gains[groups==w].mean())) for w in names])


def t0b(folder, guard):
    rows, saved_p, y = saved(); groups = np.array([r['writer'] for r in rows])
    base = np.array([saved_p[r['key']]['B-mixlogit']['probabilities'] for r in rows])
    predictions = {}; fits = {}; summary = {}
    for arm in ('R27.H0','R27.H1','R27.H2','R27.H3'):
        valid = np.array([saved_p[r['key']][arm]['valid'] for r in rows])
        p = np.array([saved_p[r['key']][arm]['probabilities'] if ok else [ .25 ]*4
                      for r, ok in zip(rows, valid)])
        for mode in ('EM_TS','BCTS'):
            name = arm+'.'+mode; corrected = np.zeros_like(base); stacked = np.zeros_like(base)
            audit = []
            for index, w in enumerate(sorted(set(groups))):
                guard('T0b', dict(arm=arm, method=mode, outer_writer=index, total_writers=len(set(groups))))
                fold = outer_fold(p, base, y, groups, w, mode, valid); m = groups == w
                corrected[m] = fold.pop('corrected'); stacked[m] = fold.pop('stacked')
                audit.append(dict(heldout_writer=w, outer_fit_writers=sorted(set(groups[~m])), **fold))
            cb, cl = losses(corrected, y, valid); sb, sl = losses(stacked, y)
            bb, bl = losses(base, y)
            comparisons = {'stack_minus_mix_gain': paired(rows, bb-sb),
                           'corrected_minus_mix_gain': paired(rows, bb-cb),
                           'stack_log_loss_gain': paired(rows, bl-sl),
                           'corrected_system_log_loss_gain': paired(rows, bl-cl)}
            for baseline in ('B-pop','B-writer','B-last','P04-effort-features','P04-E','P04-E-shuffle'):
                b = np.array([saved_p[r['key']][baseline]['scores']['half_brier'] for r in rows])
                comparisons['stack_gain_over_'+baseline] = paired(rows, b-sb)
            # Screen only; no e-LOND, fresh confirmation or engine admission.
            c = comparisons['stack_minus_mix_gain']
            comparisons['delta_screen'] = bool(c['interval'][0] > .01 and c['crossed_interval'][0] > .01)
            comparisons['invalid_retained'] = int((~valid).sum())
            predictions[name] = [dict(key=r['key'], writer=r['writer'], prompt=r['prompt'],
                raw_valid=bool(valid[i]), corrected=corrected[i].tolist(), stacked=stacked[i].tolist(),
                corrected_half_brier=float(cb[i]), stacked_half_brier=float(sb[i]),
                corrected_system_log_loss=float(cl[i]), stacked_log_loss=float(sl[i])) for i,r in enumerate(rows)]
            summary[name] = comparisons; fits[name] = audit
    for mode in ('EM_TS','BCTS'):
        own = np.array([r['stacked_half_brier'] for r in predictions['R27.H2.'+mode]])
        donor = np.array([r['stacked_half_brier'] for r in predictions['R27.H3.'+mode]])
        summary['own_over_donor_'+mode] = paired(rows, donor-own)
    freeze(folder/'PREDICTIONS.json', predictions); freeze(folder/'FITS.json', fits)
    freeze(folder/'SUMMARY.json', dict(comparisons=summary, engine_admission=False,
        limits=['Nested writer cross-fitting; exposed retrospective screen, not confirmation.',
        'EM_TS retains the requested EM then temperature arm; unverified label-shift assumptions.',
        'EM adapts to unlabelled complete held-out maker batches, not an online engine forecast.',
        'BCTS is a separately named class-bias calibration sensitivity, not an EM substitute.',
        'Intervals condition on fitted predictions, omit refitting uncertainty and are not simultaneous.',
        'Shared historical sources and prompt dependence prevent independent-family claims.',
        'Standalone invalid readers retain loss 1; stacks use the frozen baseline fallback.',
        'No posterior threshold is converted to an e-value and no promotion is issued.']))


def completed_before(sessions, current):
    cutoff = current['timestamp']
    return [s for s in sessions if s['session'] != current['session'] and s['end_at'] < cutoff]


def select_penalty(past, own, all_x, key_index):
    # Exact Stage 14 penalty grid, with historical last-20% calibration. A cold
    # writer has fixed penalty 1; no target-session outcomes choose a setting.
    if len(own) < 10: return 1., dict(mode='cold_fixed', calibration_keys=[])
    split_index = max(4, int(.8*len(own))); cal = own[split_index:]
    split = min(r['open_at'] for r in cal)
    fit = [r for r in past if r['resolved_at'] < split]
    fit_own = [r for r in fit if r['writer'] == own[0]['writer']]
    if len(fit) < 8 or not fit_own: return 1., dict(mode='cold_fixed', calibration_keys=[])
    take = lambda rs: all_x[[key_index[r['key']] for r in rs]]
    yy = lambda rs: np.array([ACTIONS.index(r['handling']) for r in rs])
    w = global_fit(take(fit), yy(fit)); values = []
    for penalty in (.01,.1,1.,10.):
        residual = intercept_fit(take(fit_own)@w, yy(fit_own), np.ones(len(fit_own)), penalty)
        q = softmax(take(cal)@w+residual, axis=1)
        values.append((float(losses(q, yy(cal))[0].mean()), penalty))
    return min(values)[1], dict(mode='past_only_grid', calibration_keys=[r['key'] for r in cal],
                              fit_keys_sha256=digest([r['key'] for r in fit]))


def prequential_session(sessions, current, all_x, key_index):
    """Session-start frozen fit; only completed sessions may train it."""
    history_sessions = completed_before(sessions, current)
    past = sorted([r for s in history_sessions for r in s['rows']], key=lambda r:(r['open_at'],r['key']))
    own = [r for r in past if r['writer'] == current['writer']]
    targets = sorted(current['rows'], key=lambda r:(r['open_at'],r['key']))
    cutoff = current['timestamp']
    if any(r['resolved_at'] >= cutoff for r in past): raise ValueError('future training label')
    if any(r['open_at'] < cutoff for r in targets): raise ValueError('target predates session')
    yy = lambda rs: np.array([ACTIONS.index(r['handling']) for r in rs], dtype=int)
    y = yy(past); oy = yy(own)
    pop = np.bincount(y, minlength=4)+1.; pop /= pop.sum()
    personal = np.bincount(oy, minlength=4)+4*pop; personal /= personal.sum()
    penalty, receipt = select_penalty(past, own, all_x, key_index)
    if len(past) < 8:
        probabilities = np.tile(personal, (len(targets),1)); receipt['pooled_fit']='cold_frequency'
    else:
        x = all_x[[key_index[r['key']] for r in past]]; w = global_fit(x,y)
        ox = all_x[[key_index[r['key']] for r in own]] if own else np.empty((0,x.shape[1]))
        residual = intercept_fit(ox@w, oy, np.ones(len(own)), penalty) if own else np.zeros(4)
        # These immutable features contain only decision-prefix text and the last
        # already resolved handling outcome, including earlier in this session.
        tx = all_x[[key_index[r['key']] for r in targets]]
        probabilities = softmax(tx@w + residual, axis=1); receipt['pooled_fit']='multinomial'
    own_prompts={s['prompt'] for s in history_sessions if s['writer']==current['writer']}
    global_prompts={s['prompt'] for s in history_sessions}
    forecasts=[]
    for row, p in zip(targets, probabilities):
        forecasts.append(dict(key=row['key'], writer=row['writer'], prompt=row['prompt'],
            session=current['session'], history_decisions=len(own), history_sessions=sum(s['writer']==current['writer'] for s in history_sessions),
            own_prompt_novel=row['prompt'] not in own_prompts, global_prompt_novel=row['prompt'] not in global_prompts,
            truth=row['handling'], probabilities={'B-pop':pop.tolist(),'B-writer':personal.tolist(),'B-mixlogit':p.tolist()}))
    return forecasts, dict(session=current['session'], cutoff=cutoff, train_decisions=len(past),
        own_decisions=len(own), max_training_resolution=max((r['resolved_at'] for r in past),default=None),
        train_sessions=[s['session'] for s in history_sessions],
        train_keys_sha256=digest([r['key'] for r in past]), penalty=penalty, **receipt)


def t0c(folder, guard, prepared):
    sessions = read(prepared/'SESSIONS.json')
    all_rows = sorted([r for s in sessions for r in s['rows']], key=lambda r:(r['open_at'],r['key']))
    keys = [r['key'] for r in all_rows]
    if len(set(keys)) != len(keys): raise ValueError('duplicate target')
    key_index = {k:i for i,k in enumerate(keys)}; x = matrix(all_rows, False)
    sessions.sort(key=lambda s:(s['timestamp'],s['session']))
    forecasts=[]; fits=[]
    for i,s in enumerate(sessions):
        guard('T0c', dict(sessions_processed=i, total_sessions=len(sessions), decisions=len(forecasts)))
        if not s['rows']: continue
        predicted, receipt = prequential_session(sessions, s, x, key_index)
        # Durable per-session checkpoint; a crash preserves it but never silently
        # resumes or mixes attempts. It is not a complete scientific cell.
        freeze(folder/'sessions'/f'{i:04d}.json',dict(predictions=predicted,fit=receipt))
        forecasts.extend(predicted); fits.append(receipt)
    if len(forecasts) != len(all_rows): raise ValueError('prequential coverage mismatch')
    summary = {}; bins=[(0,0),(1,9),(10,29),(30,99),(100,299),(300,10**9)]
    for subset in ('all','own_prompt_novel','global_prompt_novel'):
        for lo,hi in [(0,10**9)]+bins:
            rows=[r for r in forecasts if (subset=='all' or r[subset]) and lo<=r['history_decisions']<=hi]
            name=f'{subset}:{lo}-{hi}'
            if not rows: summary[name]=dict(status='empty',decisions=0); continue
            yy=np.array([ACTIONS.index(r['truth']) for r in rows])
            scores={a:losses([r['probabilities'][a] for r in rows],yy) for a in ('B-pop','B-writer','B-mixlogit')}
            summary[name]=dict(decisions=len(rows),writers=len({r['writer'] for r in rows}),
                gain_over_population=paired(rows,scores['B-pop'][0]-scores['B-mixlogit'][0]),
                gain_over_personal=paired(rows,scores['B-writer'][0]-scores['B-mixlogit'][0]),
                log_loss_gain_over_population=paired(rows,scores['B-pop'][1]-scores['B-mixlogit'][1]),
                log_loss_gain_over_personal=paired(rows,scores['B-writer'][1]-scores['B-mixlogit'][1]))
    freeze(folder/'PREDICTIONS.json',forecasts);freeze(folder/'FITS.json',fits)
    freeze(folder/'SUMMARY.json',dict(curves=summary,expected_decisions=len(all_rows),
        limits=['Historical public exposure; descriptive only.',
        'Models refit at session start using strictly earlier completed sessions; no concurrent unfinished session labels.',
        'Previous resolved handling is observed within-session; parameters remain fixed for the session.',
        'Past-only penalty selection uses the existing grid; cold histories use fixed penalty 1.',
        'Raw chronology exclusions are retained and reported; census counts are not assumed.',
        'Prompt novelty is reported both relative to own history and all training sessions.',
        'Bootstrap conditions on saved forecasts; shared evolving fits are not independent confirmations.']))


TASKS={'T0a':t0a,'T0b':t0b,'T0c':t0c}
