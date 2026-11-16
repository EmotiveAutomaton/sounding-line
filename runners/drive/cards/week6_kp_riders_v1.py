"""Prospective KP1/KP2/KP3 shared handler over authenticated private rows.

DESIGN CHECK: LESSONS 3-5. Under NULL, repair OR=1, prediction difference=0,
recency slope=0. Under ALTERNATIVE signs follow the planted carrier and recency.
One fixed writer bank, no discarded undefined fits. KP1 support needs all three
packet conditions, KP2 needs a signed interval, KP3 its bar and positive interval.
No scientific claim is made before all registered inference and replay finish.
Source interpretations and session-fold centering await explicit owner review.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import uuid
import numpy as np

from . import week6_kp_core_v1 as core
from . import week6_kp_source_v1 as source
from .timing_d33_supported_stats import NAMES as D33_NAMES

COVARIATES = tuple(n for n in D33_NAMES if n != 'intercept')
VARIANTS = ('deletion', 'deletion_earlier_typed', 'deletion_word_or_following',
            'continuation_surprise', 'deletion_nonboundary', 'continuation_nonboundary',
            'deletion_raw_log_pause', 'continuation_raw_log_pause',
            'deletion_nonboundary_raw_log_pause', 'continuation_nonboundary_raw_log_pause')


def remainder(rows, frozen_fit):
    beta = frozen_fit['coefficients']; ratio = float(frozen_fit['variance_ratio'])
    predicted = np.asarray([sum(float(r[n]) * beta.get(n, 0.) for n in COVARIATES)
                            + beta.get('intercept', 0.) for r in rows])
    y = np.asarray([r['log_pause'] for r in rows]); writers = np.asarray([r['writer'] for r in rows])
    for writer in sorted(set(writers)):
        ix = writers == writer; n = int(ix.sum())
        predicted[ix] += ratio / (1 + n * ratio) * float((y[ix] - predicted[ix]).sum())
    z, _ = core.centre(y - predicted, writers, standardize=True)
    raw, _ = core.centre(y, writers, standardize=True)
    return [dict(r, remainder=float(z[i, 0]), raw_log_pause_z=float(raw[i, 0])) for i, r in enumerate(rows)]


def kp1_rows(rows, variant='deletion'):
    if variant not in VARIANTS:
        raise ValueError('Unregistered KP1 variant')
    continuation = variant.startswith('continuation')
    reason = 'continuation_exclusions' if continuation else 'kp1_exclusions'
    return [r for r in rows if not r[reason] and ('_nonboundary' not in variant
            or not r['sentence_start'] and not r['after_punctuation'])]


def kp1_fit(rows, variant='deletion'):
    kept = kp1_rows(rows, variant)
    continuation = variant.startswith('continuation')
    target = ('continuation_surprise' if continuation else variant
              if variant in ('deletion_earlier_typed', 'deletion_word_or_following') else 'deletion')
    if not kept:
        raise ValueError('KP1 variant has no supported rows')
    writers = np.asarray([r['writer'] for r in kept])
    predictor = 'raw_log_pause_z' if variant.endswith('_raw_log_pause') else 'remainder'
    x = np.asarray([[r[predictor]] + [r[c] for c in COVARIATES] for r in kept], float)
    x, _ = core.centre(x, writers)
    design, _ = core.fixed_writer_design(x, writers)
    y = np.asarray([r[target] for r in kept], float)
    if continuation:
        y = core.centre(y, writers)[0][:, 0]
        fit = core.linear(design, y)
        value = fit['coefficients'][0]
    else:
        fit = core.logistic(design, y)
        value = math.exp(fit['coefficients'][0])
    return {'value': value, 'rows': len(kept), 'writers': len(set(writers)), 'fit': fit}


def support(rows):
    return {'words': len(rows), 'writers': len({r['writer'] for r in rows}),
            'floor': 20, 'below_floor': len({r['writer'] for r in rows}) < 20}


def pooled_fallback(rows, *, card, variant='deletion'):
    """Inherited below-floor descriptive fit; no interval-based support claim."""
    if card == 'KP2':
        return {'value': kp2_contrast(rows), 'method': 'pooled paired held-out squared errors'}
    if card == 'KP1':
        kept = kp1_rows(rows, variant)
        continuation = variant.startswith('continuation')
        target = ('continuation_surprise' if continuation else variant
                  if variant in ('deletion_earlier_typed', 'deletion_word_or_following') else 'deletion')
        predictor = 'raw_log_pause_z' if variant.endswith('_raw_log_pause') else 'remainder'
        names = (predictor,) + COVARIATES
    elif card == 'KP3':
        kept = [r for r in rows if not r['kp3_exclusions']]
        continuation = True; target = 'log_pause'
        names = ('log1p_hours_since_last_use',) + COVARIATES + ('log_earlier_count',)
    else:
        raise ValueError('Unknown fallback card')
    if not kept:
        raise ValueError('No rows for pooled descriptive fallback')
    writers = [r['writer'] for r in kept]
    x = core.centre([[r[n] for n in names] for r in kept], writers)[0]
    x = np.column_stack((x, np.ones(len(kept))))
    y = np.asarray([r[target] for r in kept], float)
    if continuation:
        y = core.centre(y, writers)[0][:, 0]
        value = core.linear(x, y)['coefficients'][0]
    else:
        value = math.exp(core.logistic(x, y)['coefficients'][0])
    return {'value': float(value), 'method': 'pooled descriptive fit on within-writer centered continuous measures',
            'limit': 'Binary response stays binary; pooled fallback does not identify writer-adjusted logistic association'}


def kp2_errors(rows):
    """Leave one complete evaluation session out; training-only writer usual.

    The packet's original source cohort is retained in dispositions. Folds whose
    writer has no other evaluation session are explicitly unsupported, not
    centered using their held-out outcomes. This rule is awaiting owner review.
    """
    if len({(r['session'], r['index']) for r in rows}) != len(rows):
        raise ValueError('KP2 duplicate row identity')
    sessions = sorted({r['session'] for r in rows}); errors = []; exclusions = Counter()
    names = ('log_pause',) + COVARIATES
    columns = {n: i for i, n in enumerate(names)}
    base_names = [n for n in COVARIATES if n not in ('own_surprise', 'donor_surprise')]
    for session in sessions:
        train = [r for r in rows if r['session'] != session]
        test = [r for r in rows if r['session'] == session]
        train_writers = {r['writer'] for r in train}
        supported = [r for r in test if r['writer'] in train_writers]
        exclusions['writer_without_training_session_words'] += len(test) - len(supported)
        if not supported:
            continue
        training, usual = core.centre([[r[n] for n in names] for r in train], [r['writer'] for r in train])
        testing, _ = core.centre([[r[n] for n in names] for r in supported], [r['writer'] for r in supported], usual=usual)
        results = {}
        for arm, extra in (('base', []), ('own', ['own_surprise']), ('donor', ['donor_surprise'])):
            chosen = [columns[n] for n in base_names + extra]
            x = np.column_stack((np.ones(len(train)), training[:, chosen]))
            focal = (len(chosen),) if extra else ()
            fit = core.mixed(x, training[:, 0], [r['writer'] for r in train], focal=focal)
            z = np.column_stack((np.ones(len(supported)), testing[:, chosen]))
            prediction = z @ fit['coefficients']
            prediction += np.asarray([fit['writer_intercepts'][str(r['writer'])] for r in supported])
            results[arm] = (testing[:, 0] - prediction) ** 2
        for i, row in enumerate(supported):
            errors.append({'writer': row['writer'], 'session': row['session'], 'index': row['index'],
                           **{arm: float(values[i]) for arm, values in results.items()}})
    return {'errors': errors, 'exclusions': dict(exclusions), 'folds': len(sessions)}


def kp2_contrast(errors):
    if not errors:
        raise ValueError('KP2 has no supported held-out words')
    base = sum(r['base'] for r in errors)
    if not math.isfinite(base) or base <= 0:
        raise ValueError('Undefined base error denominator')
    return 100. * sum(r['donor'] - r['own'] for r in errors) / base


def kp3_fit(rows):
    kept = [r for r in rows if not r['kp3_exclusions']]
    if not kept:
        raise ValueError('No earlier-session word uses')
    names = COVARIATES + ('log_earlier_count', 'log1p_hours_since_last_use')
    writers = [r['writer'] for r in kept]
    matrix, _ = core.centre([[r['log_pause']] + [r[n] for n in names] for r in kept], writers)
    x = np.column_stack((np.ones(len(kept)), matrix[:, 1:]))
    # Count and recency both remain identifiable, as do original own/donor terms.
    fit = core.mixed(x, matrix[:, 0], writers, focal=(1, 2, len(names) - 1, len(names)))
    return {'value': fit['coefficients'][-1], 'rows': len(kept), 'writers': len(set(writers)), 'fit': fit}


def safe_value(function, rows):
    try:
        value = function(rows)
        if not math.isfinite(value):
            raise ValueError('Nonfinite estimate')
        return {'value': float(value), 'failure': None}
    except (ValueError, np.linalg.LinAlgError) as error:
        return {'value': None, 'failure': str(error)}


def inference_unit(rows, frozen_fit, *, card, draw, seed):
    """One restartable fixed draw, including KP1 control work in first 200 draws."""
    rng = np.random.default_rng(np.random.SeedSequence([seed, draw, 0]))
    writers = sorted({r['writer'] for r in rows})
    if card == 'KP1':
        prepared = remainder(rows, frozen_fit)
        sampled = core.writer_draw(prepared, rng.integers(len(writers), size=len(writers)), writers)
        values = {v: safe_value(lambda r, v=v: kp1_fit(r, v)['value'], sampled) for v in VARIANTS}
        control = None
        if draw < 200:
            control_rng = np.random.default_rng(np.random.SeedSequence([seed, draw, 1]))
            shuffled = [dict(r) for r in prepared]
            for writer in writers:
                positions = [i for i, r in enumerate(shuffled) if r['writer'] == writer]
                values_before = [shuffled[i]['remainder'] for i in positions]
                for i, value in zip(positions, control_rng.permutation(values_before)):
                    shuffled[i]['remainder'] = float(value)
            control = safe_value(lambda r: kp1_fit(r)['value'], shuffled)
        return {'draw': draw, 'variants': values, 'control': control}
    if card == 'KP2':
        # Held-out model fits are cached separately; bootstrap uncertainty is on
        # paired writer-held prediction errors, not a row resample or test refit.
        sampled = core.writer_draw(rows, rng.integers(len(writers), size=len(writers)), writers)
        return {'draw': draw, 'estimate': safe_value(kp2_contrast, sampled)}
    if card == 'KP3':
        sampled = core.writer_draw(rows, rng.integers(len(writers), size=len(writers)), writers)
        return {'draw': draw, 'estimate': safe_value(lambda r: kp3_fit(r)['value'], sampled)}
    raise ValueError('Unregistered KP card')


def immutable(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(value, sort_keys=True, allow_nan=False, separators=(',', ':')) + '\n').encode()
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError('Immutable KP output differs')
    else:
        with path.open('xb') as stream:
            stream.write(data)


def execute(output, inputs, config):
    """Private proposal; refuses production unless all explicit owner bindings exist."""
    if config.get('owner_reviewed') is not True or config.get('qualification_complete_sha256') is None:
        raise ValueError('KP owner review and complete native qualification required')
    if config.get('bootstrap_draws') != 2000 or config.get('permutations') != 200:
        raise ValueError('Fixed full inference required')
    if config.get('source_decisions') is None or config.get('fold_rule') != 'leave_one_session_out_train_only_centering':
        raise ValueError('Exact prospective definitions required')
    proof = Path(inputs['qualification_complete'])
    if source.digest(proof) != config['qualification_complete_sha256'] or source.read(proof).get('status') != 'COMPLETE':
        raise ValueError('Constructed qualification proof changed or incomplete')
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    bound = {'inputs': inputs, 'config': config}
    immutable(output / 'BINDING.json', bound)
    corpus = source.load_authenticated(inputs, decisions=config['source_decisions'])
    card = config['card']; rows = corpus['rows']; frozen_fit = corpus['frozen_fit']
    immutable(output / 'COVERAGE.json', {k: v for k, v in corpus.items() if k not in ('rows', 'frozen_fit')})
    if card == 'KP2':
        projected = kp2_errors(rows)
        immutable(output / 'PREDICTION_ERRORS.json', projected)
        rows = projected['errors']
        point = safe_value(kp2_contrast, rows)
        supports = support(rows)
    elif card == 'KP3':
        point = safe_value(lambda r: kp3_fit(r)['value'], rows)
        supports = support([r for r in rows if not r['kp3_exclusions']])
    elif card == 'KP1':
        prepared = remainder(rows, frozen_fit)
        point = {v: safe_value(lambda r, v=v: kp1_fit(r, v)['value'], prepared) for v in VARIANTS}
        supports = {v: support(kp1_rows(prepared, v)) for v in VARIANTS}
    else:
        raise ValueError('Unregistered KP card')
    immutable(output / 'POINT.json', point)
    immutable(output / 'SUPPORT.json', supports)
    empty = (all(v['words'] == 0 for v in supports.values()) if card == 'KP1' else supports['words'] == 0)
    if empty:
        immutable(output / 'SUMMARY.json', {'card': card, 'state': 'unsupported', 'support': supports,
            'reason': 'No eligible observations for this registered comparison',
            'complete_draws': 0, 'association_only': True})
        return {'status': 'complete', 'card': card, 'draws': 0, 'summary': 'SUMMARY.json'}
    records = []
    new = 0
    binding = hashlib.sha256(json.dumps(bound, sort_keys=True).encode()).hexdigest()
    for draw in range(2000):
        path = output / 'draws' / f'{draw:04d}.json'
        if path.exists():
            value = source.read(path)
            seal = source.read(path.with_suffix('.receipt.json'))
            if (seal['sha256'] != source.digest(path) or value['binding'] != binding
                    or value['draw'] != draw):
                raise ValueError('Retained draw binding differs')
        else:
            value = inference_unit(rows, frozen_fit, card=card, draw=draw, seed=config['seed'])
            value['binding'] = binding; immutable(path, value)
            immutable(path.with_suffix('.receipt.json'), {'sha256': source.digest(path)})
            new += 1
        records.append(value)
        if draw < 1999 and (new >= config.get('max_new_draws', 100) or (output / 'YIELD_REQUEST.json').exists()):
            immutable(output / f'CHECKPOINT_{draw:04d}.json', {'draws': draw + 1, 'binding': binding})
            return {'status': 'yielded', 'reason': 'fixed_draw_boundary', 'completed_units': draw + 1,
                    'checkpoint': f'CHECKPOINT_{draw:04d}.json'}
    if card == 'KP1':
        controls = [v['control']['value'] for v in records[:200]]
        valid_control = all(v is not None and math.isfinite(v) for v in controls)
        threshold = float(np.quantile(controls, .975)) if valid_control else None
        result = {'variants': {}, 'controls': {'attempted': 200, 'valid': valid_control,
                                             'q975': threshold, 'values': controls}}
        for variant in VARIANTS:
            continuation = variant.startswith('continuation')
            result['variants'][variant] = core.interval(point[variant]['value'],
                [v['variants'][variant]['value'] for v in records], null=0. if continuation else 1.,
                bar=.02 if continuation else 1.10, control_threshold=threshold if variant == 'deletion' else None)
        if not valid_control:
            result['variants']['deletion']['state'] = 'invalid_control'
        for variant in VARIANTS:
            if supports[variant]['below_floor']:
                fallback = safe_value(lambda r, v=variant: pooled_fallback(r, card=card, variant=v)['value'], prepared)
                result['variants'][variant] = {'state': 'below_floor_descriptive',
                    'support': supports[variant], 'fallback': fallback,
                    'superseded_inferential_classification': result['variants'][variant]['state']}
    else:
        result = core.interval(point['value'], [v['estimate']['value'] for v in records], bar=.01 if card == 'KP3' else 0.)
        if card == 'KP2' and result['state'] == 'positive_below_bar_or_control':
            raise ValueError('Impossible KP2 interval classification')
        if supports['below_floor']:
            fallback = safe_value(lambda r: pooled_fallback(r, card=card)['value'], rows)
            result = {'state': 'below_floor_descriptive', 'support': supports, 'fallback': fallback}
    result.update(card=card, complete_draws=2000, association_only=True,
                  source_scope='frozen D33 supported cohort with per-rider exclusions disclosed',
                  state_detail='No attention, schema-switch or causal readiness mechanism identified')
    immutable(output / 'SUMMARY.json', result)
    return {'status': 'complete', 'card': card, 'draws': 2000, 'summary': 'SUMMARY.json'}


def verify(output, inputs, config):
    """Independent process must recompute all fixed draws, never trust their values."""
    output = Path(output)
    if source.read(output / 'BINDING.json') != {'inputs': inputs, 'config': config}:
        raise ValueError('KP input binding differs')
    # A new namespace on every verifier invocation guarantees no draw is reused.
    # Exactly one complete statistical replay, including source and aggregation.
    sibling = output / ('independent-replay-' + uuid.uuid4().hex)
    replay_config = dict(config, max_new_draws=2000)
    result = execute(sibling, inputs, replay_config)
    for name in ('POINT.json', 'COVERAGE.json', 'SUPPORT.json', 'SUMMARY.json'):
        if source.read(output / name) != source.read(sibling / name):
            raise ValueError('Independent aggregate replay differs: ' + name)
    if config['card'] == 'KP2' and source.read(output / 'PREDICTION_ERRORS.json') != source.read(sibling / 'PREDICTION_ERRORS.json'):
        raise ValueError('Independent held-out prediction differs')
    for draw in range(result['draws']):
        name = f'draws/{draw:04d}.json'
        saved, replayed = source.read(output / name), source.read(sibling / name)
        saved.pop('binding'); replayed.pop('binding')
        if saved != replayed:
            raise ValueError('Independent full fixed-draw replay differs')
    return {'verified': True, 'full_independent_replay': True, 'draws': result['draws']}
