"""T4 descriptive covariates from the complete WA0.h1 and S1 sources.

DESIGN CHECK: LESSONS 2-5 and CONTROLS 1-7 reread 2026-11-04.
NULL and ALTERNATIVE retain the same whole-writer sample, independent-role
galleries and all timing-eligible windows. No temperature or choice fit is
read. Distances reproduce original B-only imputation/scaling and fractional
ties. Wrong sources, changed original scores or missing primary writers
refuse; missing auxiliary support is explicit, never silently intersected.
"""
from collections import defaultdict
from pathlib import Path
import math
import numpy as np
from threadpoolctl import threadpool_limits
from runners.stage14.common import read, filehash
from . import week3_identification as base
from . import week3_identification_crossfit as cross
from . import week4_t4_sample_cost as sample
from . import week4_typed_windows as windows_source
from .timing_pmap_source import completed
from .timing_p6 import gzread, write_equal


def configuration(mode):
    if mode not in ('constructed', 'full'):
        raise ValueError('Unknown mode')
    return dict(card='T4-descriptive-covariates', mode=mode,
                channel='EV3.final.residual', seed=20261102,
                margin='negative squared B-standardized distance: true minus best other',
                hesitancy='mean of all timing-eligible S1 windows across all sessions')


def distances(a, b):
    """Exact WA0 metric; auxiliary margin does not replace fractional scores."""
    original = base.pmap.identify(a, b)
    a, b = np.asarray(a, float), np.asarray(b, float)
    have = np.isfinite(b).sum(0)
    mean = np.divide(np.nansum(b, axis=0), have,
                     out=np.zeros(b.shape[1]), where=have > 0)
    aa, bb = np.where(np.isfinite(a), a, mean), np.where(np.isfinite(b), b, mean)
    scale = bb.std(0)
    keep = (have > 0) & (scale > 1e-12)
    aa, bb = (aa[:, keep]-mean[keep])/scale[keep], (bb[:, keep]-mean[keep])/scale[keep]
    d = np.sum((aa[:, None, :]-bb[None, :, :])**2, axis=2)
    nearest = np.isclose(d, d.min(1)[:, None], atol=1e-12, rtol=1e-12)
    scores = nearest.diagonal()/nearest.sum(1)
    if scores.tolist() != original['scores']:
        raise ValueError('Original fractional ties differ')
    other = d.copy()
    np.fill_diagonal(other, np.inf)
    margins = other.min(1)-d.diagonal()
    if not np.isfinite(margins).all():
        raise ValueError('Nonfinite margin')
    return margins.tolist(), scores.tolist(), int(keep.sum())


def reconstruct(rows, detail):
    channel = 'EV3.final.residual'; original = 'EV3.final'
    rows = sorted(rows, key=lambda r: r['session'])
    folds = cross.writer_folds(rows, cross.CONFIG['seed'])
    if detail['writer_folds'] != folds:
        raise ValueError('Original writer folds differ')
    roster = detail['variants'][channel]['writers']; result = {}
    if len(detail['folds']) != 3:
        raise ValueError('All original folds required')
    for f, saved in enumerate(detail['folds']):
        if saved['calibration'] != f:
            raise ValueError('Fold order differs')
        rr = [r for r in rows if folds[r['writer']] != f]
        x, slices = base.feature_matrix(rr)
        writers, groups, halves, excluded = base.split(rr)
        residual, coefficients = base.residualize(
            x, np.asarray([r.get('accepted_share', 0.) for r in rr]), groups, slices)
        prior = saved['detail']
        if coefficients != prior['nuisance_coefficients'] or halves != prior['halves']:
            raise ValueError('Original gallery nuisance or halves differ')
        profiles = base.means(residual, groups, writers)
        gallery = saved['gallery_writers'][original]
        expected_gallery = [w for w in roster if folds[w] != f]
        probes = [w for w in roster if folds[w] == (f+1) % 3]
        if gallery != expected_gallery or saved['probe_writers'][original] != probes:
            raise ValueError('Original probe/gallery roles differ')
        p = profiles[[writers.index(w) for w in gallery], :, slices[original]]
        margins, scores, used = distances(p[:, 0, :], p[:, 1, :])
        v = prior['variants'][channel]
        if v['writers'] != gallery or v['real']['scores'] != scores:
            raise ValueError('Original completed identification scores differ')
        for w in probes:
            if w in result:
                raise ValueError('Duplicate probe')
            i = gallery.index(w)
            result[w] = dict(margin=margins[i], fractional_score=scores[i],
                             gallery_writers=len(gallery), used_features=used, fold=f)
    if sorted(result) != roster:
        raise ValueError('Original complete probe roster differs')
    if [result[w]['fractional_score'] for w in roster] != detail['variants'][channel]['real']['scores']:
        raise ValueError('Joined original scores differ')
    return result


def join(writers, margins, windows):
    if writers != sorted(set(writers)):
        raise ValueError('Unique canonical sample required')
    values = defaultdict(list); sessions = set()
    for row in sorted(windows, key=lambda r: r['session']):
        if row['session'] in sessions:
            raise ValueError('Duplicate timing session')
        sessions.add(row['session'])
        for window in row['windows']:
            h = window['hesitancy']
            if h is None or not math.isfinite(h):
                raise ValueError('Invalid eligible window hesitancy')
            values[row['writer']].append(float(h))
    records = []
    for w in writers:
        mm = margins.get(w); vv = values.get(w, [])
        records.append(dict(writer=w, identification=mm,
                            mean_hesitancy=math.fsum(vv)/len(vv) if vv else None,
                            eligible_windows=len(vv),
                            missing_identification=mm is None, missing_hesitancy=not bool(vv)))
    return records


def known_answers():
    a = [[0., 7., np.nan], [2., 7., 3.], [4., 7., 5.]]
    b = [[0., 7., np.nan], [2., 7., 3.], [4., 7., 5.]]
    margins, scores, used = distances(a, b)
    if scores != [1., 1., 1.] or used != 2 or not all(v > 0 for v in margins):
        raise ValueError('Known matched profiles fail')
    tied = distances([[1.], [1.], [1.]], [[1.], [1.], [1.]])
    if tied != ([0., 0., 0.], [1/3]*3, 0):
        raise ValueError('Constant gallery must tie with zero margin')
    negative = distances([[4.], [2.], [0.]], [[0.], [2.], [4.]])[0]
    if not negative[0] < 0 or not negative[1] > 0 or not negative[2] < 0:
        raise ValueError('Margin direction fails')
    rows = [dict(session='s1', writer='a', windows=[dict(hesitancy=1.),dict(hesitancy=3.)]),
            dict(session='s2', writer='a', windows=[dict(hesitancy=8.)])]
    joined = join(['a','b'], {'a': {'margin':2.}}, rows)
    if joined[0]['mean_hesitancy'] != 4. or not joined[1]['missing_hesitancy']:
        raise ValueError('Known complete-window denominator differs')
    rows = [dict(session=f'w{w}-s{s}',writer=f'w{w}',prompt=f'p{s//2}',timestamp=float(s),
                 features={'EV3.final':[float(w),float(w*w)]}, accepted_share=.25)
            for w in range(12) for s in range(8)]
    _, detail = cross.analyze_group(rows,dict(cross.CONSTRUCTED,permutations=2,bootstrap_draws=4))
    recovered = reconstruct(rows,detail)
    if len(recovered)!=12 or any(r['margin']<=0 or r['fractional_score']!=1. for r in recovered.values()):
        raise ValueError('Exact role-fold reconstruction failed')
    return dict(verified=True, signed_margin=True, fractional_ties=True,
                gallery_only_scaling=True, all_windows=True, missing_support_explicit=True,
                original_role_fold_reconstruction=True)


def load(inputs):
    if set(inputs) != {'sample_completion','wa0_completion','s1_completion'}:
        raise ValueError('Exact completed bundle required')
    sc, wc, hc = (Path(inputs[k]).resolve() for k in ('sample_completion','wa0_completion','s1_completion'))
    for c in (sc, wc, hc):
        completed(c, c.parent/'PLAN.json')
    sp, wp, hp = (read(c.parent/'PLAN.json') for c in (sc,wc,hc))
    if sp['module'] != 'runners.drive.cards.week4_t4_sample_cost' or sp['config'] != sample.configuration('cost'):
        raise ValueError('Frozen complete sample cost required')
    packed, selection = sample.load(sp['inputs'])
    completed(sc, sc.parent/'output/PRIVATE_SELECTION.json')
    if read(sc.parent/'output/PRIVATE_SELECTION.json') != selection:
        raise ValueError('Frozen sample changed')
    if wp['module'] != 'runners.drive.cards.week3_identification_crossfit' or wp['config'] != cross.CONFIG:
        raise ValueError('Original complete cross-fit required')
    completed(wc, wc.parent/'output/DETAIL.json.gz')
    data = base.load(wp['inputs'], base.CONFIG)
    completed(hc, hc.parent/'output/WINDOWS.json.gz')
    if hp['card'] != 'W4-S1-inputs-full' or hp['module'] != 'runners.drive.cards.week4_typed_windows' or hp['config'] != windows_source.CONFIG:
        raise ValueError('Original S1 windows required')
    return packed['writers'], data['rows'], gzread(wc.parent/'output/DETAIL.json.gz')['main'], gzread(hc.parent/'output/WINDOWS.json.gz')


def calculate(output, inputs, config, saving):
    if config != configuration(config.get('mode')):
        raise ValueError('Frozen configuration required')
    checks = known_answers()
    if config['mode'] == 'constructed':
        if inputs: raise ValueError('No human inputs in fixture')
        return checks
    writers, rows, detail, windows = load(inputs)
    margins = reconstruct(rows, detail)
    records = join(writers, margins, windows)
    path = Path(output)/'PRIVATE_COVARIATES.json'
    if saving: write_equal(path, records)
    elif read(path) != records: raise ValueError('Complete covariate reconstruction differs')
    return dict(card=config['card'], mode='full', writers=len(writers),
                original_identification_writers=len(margins),
                writers_with_margin=sum(not r['missing_identification'] for r in records),
                writers_with_hesitancy=sum(not r['missing_hesitancy'] for r in records),
                eligible_windows=sum(r['eligible_windows'] for r in records),
                input_hashes={k:filehash(v) for k,v in inputs.items()},
                private_covariates_sha256=filehash(path), checks=checks,
                scientific_effect_computed=False, config=config)


def execute(output, inputs, config):
    Path(output).mkdir(parents=True, exist_ok=True)
    with threadpool_limits(limits=1): value=calculate(output,inputs,config,True)
    write_equal(Path(output)/'SUMMARY.json',value)
    return value


def verify(output, inputs, config):
    with threadpool_limits(limits=1): value=calculate(output,inputs,config,False)
    if read(Path(output)/'SUMMARY.json') != value:
        raise ValueError('Complete source replay differs')
    return dict(verified=True, full_fresh_source_replay=True, no_temperature_read=True)
