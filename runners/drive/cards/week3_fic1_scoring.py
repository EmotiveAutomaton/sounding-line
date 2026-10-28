"""FIC1 fixed-support arithmetic; native handler is constructed-only.

DESIGN CHECK: LESSONS 3-5, CONTROLS 1-7 reread 2026-10-27.
NULL identical arms give exact zero, p=1 and no admission. ALTERNATIVE stable
fingerprints can clear the upper-tail and paired-context rules; reverse effects
cannot. Missing fixed writers or any missing draw invalidate the bank. Fractional
ties never fabricate a binary McNemar table. A nonrising raw common-support
length curve stops interpretation, including ceiling saturation. These arithmetic
checks do not establish correctness of an unbuilt control generator.
"""
from pathlib import Path

import numpy as np
from threadpoolctl import threadpool_limits

from runners.stage14.common import read, filehash, freeze
from . import timing_pmap_stats as pmap
from . import week3_identification as base

CONFIG = dict(card='FIC1-scoring-native', schema=1, mode='constructed',
              permutations=1000, bootstrap_draws=2000, seed=20261026)
LEVELS = ('500', '1000', '2000', 'full')


def roster_check(writers):
    if (not isinstance(writers, list) or len(writers) < 3
            or any(not isinstance(w, str) or not w for w in writers)
            or len(writers) != len(set(writers)) or writers != sorted(writers)):
        raise ValueError('fixed sorted unique writer roster of at least three required')


def score_array(values, writers):
    """None/missing fixed rows are unsupported, never silently excluded."""
    roster_check(writers)
    if values is None:
        return None
    if not isinstance(values, dict) or set(values)-set(writers):
        raise ValueError('unexpected score-map schema or writers')
    if set(values) != set(writers) or any(values[w] is None for w in writers):
        return None
    if any(type(values[w]) not in (int, float) for w in writers):
        raise ValueError('scores must be finite numbers, not flags or strings')
    x = np.asarray([values[w] for w in writers], float)
    if not np.isfinite(x).all() or (x < 0).any() or (x > 1).any():
        raise ValueError('scores outside finite unit interval')
    return x


def gallery_scores(a, b, writers):
    roster_check(writers)
    a, b = np.asarray(a, float), np.asarray(b, float)
    if a.ndim != 2 or a.shape != b.shape or len(a) != len(writers) or a.shape[1] == 0:
        raise ValueError('declared fixed gallery dimensions differ')
    if np.isinf(a).any() or np.isinf(b).any():
        raise ValueError('infinite gallery feature')
    if not np.isfinite(a).any(1).all() or not np.isfinite(b).any(1).all():
        return None
    result = pmap.identify(a, b)
    return dict(zip(writers, result['scores']))


def interval(x, config):
    return base.paired_interval(np.asarray(x, float), config)


def compare(real, context, bank, writers, config=CONFIG):
    if config != CONFIG or not isinstance(bank, list) or len(bank) != config['permutations']:
        raise ValueError('complete frozen reference bank required')
    a, b = score_array(real, writers), score_array(context, writers)
    draws = [score_array(x, writers) for x in bank]
    if a is None or b is None:
        return dict(state='unsupported', numerical_pass=False, reason='fixed observed/context support missing')
    missing = [i for i, x in enumerate(draws) if x is None]
    if missing:
        return dict(state='invalid', numerical_pass=False, missing_draws=missing,
                    reason='fixed reference support missing; no redraw or successful-only inference')
    null = base.null_summary([float(x.mean()) for x in draws], float(a.mean()))
    ci = interval(a-b, config)
    passed = null['one_sided_p'] < .05 and ci['ci_low'] > 0
    state = 'positive' if passed else 'negative' if ci['ci_high'] < 0 else 'not_detected'
    return dict(state=state, numerical_pass=bool(passed), real=float(a.mean()),
                context=float(b.mean()), permutation=null, real_minus_context=ci,
                writers=writers, control_construction_validated=False,
                scientific_admission=False)


def genre_comparison(creative, argumentative, writers, config=CONFIG):
    if config != CONFIG:
        raise ValueError('frozen inference settings required')
    a, b = score_array(creative, writers), score_array(argumentative, writers)
    if a is None or b is None:
        return dict(state='unsupported', reason='complete fixed paired genre support required')
    return dict(state='complete', paired_difference=interval(a-b, config),
                binary_table=base.paired_table(a, b), writers=writers,
                scientific_admission=False)


def length_curve(scores, writers, config=CONFIG):
    if config != CONFIG or not isinstance(scores, dict) or set(scores) != set(LEVELS):
        raise ValueError('all four frozen raw length levels required')
    arrays = [score_array(scores[level], writers) for level in LEVELS]
    if any(x is None for x in arrays):
        return dict(state='unsupported', continue_interpretation=False,
                    reason='same fixed all-length writer population required')
    x = np.asarray(arrays)
    means = x.mean(1)
    positions = np.arange(4, dtype=float)-1.5
    slope = float(positions @ means / (positions @ positions))
    gain = interval(x[-1]-x[0], config)
    rising = gain['effect'] > 0 and slope > 0
    return dict(state='rising' if rising else 'nonrising_stop',
                continue_interpretation=bool(rising), levels=list(LEVELS),
                accuracy=means.tolist(), full_minus_500=gain, ordered_slope=slope,
                writers=writers, scientific_admission=False,
                rule='raw fixed common-support profiles; positive endpoint gain and ordered slope; both genres required')


def constructed_checks(data):
    if set(data) != {'constructed', 'writers'} or data['constructed'] is not True:
        raise ValueError('explicit constructed input required')
    writers = data['writers']
    roster_check(writers)
    n = len(writers)
    tied = gallery_scores(np.ones((n, 2)), np.ones((n, 2)), writers)
    fingerprint = gallery_scores(np.eye(n), np.eye(n), writers)
    wrong = gallery_scores(np.roll(np.eye(n), 1, axis=0), np.eye(n), writers)
    bank = [tied] * CONFIG['permutations']
    null = compare(tied, tied, bank, writers)
    plant = compare(fingerprint, tied, bank, writers)
    reverse = compare(wrong, fingerprint, bank, writers)
    broken = bank.copy(); broken[17] = None
    incomplete = compare(fingerprint, tied, broken, writers)
    curve = length_curve({level:dict.fromkeys(writers, i/3) for i, level in enumerate(LEVELS)}, writers)
    flat = length_curve({level:fingerprint for level in LEVELS}, writers)
    assert null['state'] == 'not_detected' and null['real_minus_context']['effect'] == 0
    assert null['permutation']['one_sided_p'] == 1 and not null['numerical_pass']
    assert plant['numerical_pass'] and reverse['state'] == 'negative' and not reverse['numerical_pass']
    assert incomplete['state'] == 'invalid' and incomplete['missing_draws'] == [17]
    assert curve['continue_interpretation'] and not flat['continue_interpretation']
    return dict(null=null, plant=plant, reverse=reverse, incomplete=incomplete,
                rising_curve=curve, flat_curve=flat,
                genre=genre_comparison(fingerprint, wrong, writers),
                fractional_genre=genre_comparison(tied, fingerprint, writers))


def run(output, inputs, config, verification=False):
    if config != CONFIG or set(inputs) != {'fixture'}:
        raise ValueError('constructed-only handler; human scoring not admitted')
    source = Path(inputs['fixture']).resolve()
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    with threadpool_limits(limits=1):
        result = constructed_checks(read(source))
    summary = dict(card=CONFIG['card'], constructed=True, arithmetic_checks_passed=True,
                   fixed_support_required=True, incomplete_bank_refused=True,
                   human_identification_computed=False, full_pipeline_calibration_complete=False,
                   control_construction_validated=False, scientific_admission=False)
    for name, value in [('ARITHMETIC.json', result), ('SUMMARY.json', summary),
                        ('BINDING.json', dict(config=config, inputs={str(source):filehash(source)}))]:
        path = output/name
        if verification:
            if read(path) != value:
                raise ValueError('complete arithmetic replay differs: '+name)
        else:
            freeze(path, value)
    if verification:
        return dict(verified=True, all_arithmetic_recomputed=True, constructed=True)
    return dict(status='complete', scientific_admission=False)


def execute(output, inputs, config): return run(output, inputs, config)
def verify(output, inputs, config): return run(output, inputs, config, True)
