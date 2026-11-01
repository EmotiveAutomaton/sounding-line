"""D5 constructed numerical instrument checks; no human inputs or scores.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-7 read for this build.
Identical NULL profiles tie; distinct ALTERNATIVE profiles match. Signed slope
plants reverse, missing evidence refuses, and undefined draws remain invalid.
Passing is numerical validation only, not scientific size/power admission.
"""
from pathlib import Path
import numpy as np
from runners.stage14.common import read, freeze
from . import week3_d5_scoring_core as core
from .week3_d5_gallery_support import COMPONENTS

CONFIG = dict(card='D5-numerical-validation', schema=1, seed=20261026, bootstrap=2000)


def fixture():
    rows = [dict(session=f'w{w}p{p}', writer=f'w{w}', prompt=f'p{p}', timestamp=float(p),
        share_bin=str(p % 4), support={c: True for c in COMPONENTS if c != 'process'})
        for w in range(6) for p in range(8)]
    folds = {f'w{w}': w % 3 for w in range(6)}
    return rows, folds, sorted(folds)


def checks():
    rows, folds, roster = fixture()
    x = np.eye(6)[[roster.index(r['writer']) for r in rows]]
    valid = np.ones(len(rows), bool)
    cases = []
    for fold in [None, 0, 1, 2]:
        ch = core.profile_plan(rows, folds, roster, 'final', donor_fold=fold)
        pr = core.profile_plan(rows, folds, roster, 'process', donor_fold=fold)
        context = 'literal' if fold is None else 'independent'
        for kind, matrix in [('identical', np.ones_like(x)), ('person', x)]:
            for mode in ['real', context]:
                a = core.score_character(rows, folds, ch, matrix @ matrix.T, valid, mode)
                b, meta = core.score_process(rows, folds, pr, dict(selection=matrix, rhythm=matrix), mode)
                expected = 1/len(ch['gallery']) if kind == 'identical' or mode == 'independent' else 1.
                if not np.allclose(a, expected, atol=1e-12, rtol=1e-12) or not np.allclose(b, expected, atol=1e-12, rtol=1e-12):
                    raise ValueError('Known identity answer differs')
                cases.append(dict(rotation=fold, construction=kind, context=mode,
                    probes=len(a), gallery=len(ch['gallery']), known_answer_verified=True,
                    process_features=meta))
        reverse = dict(ch, truth=[(t+1) % len(ch['gallery']) for t in ch['truth']])
        if np.any(core.score_character(rows, folds, reverse, x@x.T, valid)):
            raise ValueError('Reversed identity was accepted')
    writers = [w for w in roster for _ in range(4)]; bins = list('0123') * len(roster)
    for sign in [-1, 1]:
        scores = [.5+sign*((int(b)+.5)/4-.5) for b in bins]
        result = core.slope_interval(writers, bins, scores, roster)
        if not np.isclose(result['estimate'], sign) or result['undefined_draws'] or not result['degenerate_empirical_interval']:
            raise ValueError('Known signed slope answer differs')
    undefined = core.slope_interval(['a', 'a', 'b'], ['0', '3', '0'], [1., 0., 1.], ['a', 'b'])
    if not 0 < undefined['undefined_draws'] < CONFIG['bootstrap'] or undefined['interval'] is not None:
        raise ValueError('Undefined reference draws not retained')
    return dict(cases=cases, signed_slope_checks=2, undefined_draws_retained=True,
        scientific_admission=False, human_outcomes_computed=False,
        scope='Constructed numerical identities only; empirical size and sensitivity remain untested')


def compute(output, inputs, config, verification=False):
    if inputs or config != CONFIG: raise ValueError('Frozen constructed-only validation required')
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    if (output/'YIELD_REQUEST.json').exists() or (output.parent/'STOP').exists():
        if verification: raise InterruptedError('Constructed validation yield')
        return dict(status='yielded')
    value = checks(); path = output/'SUMMARY.json'
    if verification:
        if read(path) != value: raise ValueError('Fresh constructed numerical replay differs')
        return dict(verified=True, full_fresh_numerical_replay=True)
    freeze(path, value)
    return dict(status='complete', human_outcomes_computed=False)


def execute(output, inputs, config): return compute(output, inputs, config)
def verify(output, inputs, config): return compute(output, inputs, config, True)
