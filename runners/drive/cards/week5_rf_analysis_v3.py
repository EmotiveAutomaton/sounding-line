"""RF1 signed-three/paired-two consumer with candidate-preserving checkpoints.

DESIGN CHECK: explicit reviewed elections and a fully qualified lexical instrument
precede grouping. Signed primary remains V2. The six-presence-rate against-comment
contrast is descriptive; it cannot replace or subset the primary. All 2,000 draws
are kept, including unsupported fits. No human source is admitted by this module.
"""
from collections import Counter
from pathlib import Path
import hashlib
import json
import math
import os
import numpy as np
from . import week5_rf_statistics_v2 as stats
from . import week5_rf_qualified_v1 as qualified
from . import week5_rf_cp_source_v1 as source

MODULE = 'runners.drive.cards.week5_rf_analysis_v3'
DRAWS = 2000
DRAW_BLOCK = 4


class YieldRequested(Exception):
    pass


def read(path):
    return json.loads(Path(path).read_text('utf8'))


def check_yield(output):
    explicit = os.environ.get('SOUNDING_LINE_YIELD_FILE')
    # Nested constructed handlers and fresh replay must see their owned native
    # root's signal too. The search is bounded; it does not enumerate files.
    candidates = [Path(output), *list(Path(output).parents)[:5]]
    if any((p/'YIELD_REQUEST.json').exists() for p in candidates) or (explicit and Path(explicit).exists()):
        raise YieldRequested()


def independent_weights(rows, index):
    """Counter oracle, independent of the production bincount projection."""
    candidates = sorted({r['candidate'] for r in rows})
    seed = int.from_bytes(hashlib.sha256(f'RF1-bootstrap|20261107|{index}'.encode()).digest()[:8], 'big')
    rng = np.random.Generator(np.random.PCG64(seed))
    counts = Counter(candidates[int(i)] for i in rng.integers(0, len(candidates), size=len(candidates)))
    return np.array([counts[r['candidate']] for r in rows], dtype=float)


def primary_case(rows):
    if not rows:
        return {'present': False, 'reason': 'no qualified eligible elections', 'residual_read_rank': 0}
    x, _ = stats.design(rows, 'THREE')
    controls, reads = x[:, :-3], x[:, -3:]
    rank = int(np.linalg.matrix_rank(x)-np.linalg.matrix_rank(controls))
    return {'present': rank == 3, 'residual_read_rank': rank,
        'reason': None if rank == 3 else 'source cannot distinguish three signed reads beyond shared controls'}


def primary(rows, weights=None, pooled=False, callback=lambda: None, reference=False):
    if not rows:
        raise stats.Unsupported('no qualified eligible elections')
    weights = np.ones(len(rows)) if weights is None else np.asarray(weights, dtype=float)
    if weights.shape != (len(rows),) or not np.isfinite(weights).all() or (weights < 0).any() or weights.sum() <= 0:
        raise ValueError('Invalid complete-candidate weights')
    case = primary_case([r for r, w in zip(rows, weights) if w > 0])
    if not case['present']:
        raise stats.Unsupported(case['reason'])
    y = np.array([r['later_support'] for r in rows], dtype=float)
    n = np.array([r['later_support']+r['later_oppose'] for r in rows], dtype=float)
    assignment = np.zeros(len(rows), dtype=int) if pooled else stats.folds([r['candidate'] for r in rows])
    means, fits = {}, {}
    for model in stats.MODELS:
        x, names = stats.design(rows, model)
        loss = np.full(len(rows), np.nan)
        diagnostics = []
        for fold in (range(1) if pooled else range(5)):
            callback()
            test = (assignment == fold) & (weights > 0)
            train = weights > 0 if pooled else (assignment != fold) & (weights > 0)
            if not test.any():
                continue
            fit = stats.fit_binomial(x[train], y[train], n[train], weights[train])
            eta = stats.predict_eta(x[test], fit)
            loss[test] = np.logaddexp(0, eta)-(y[test]/n[test])*eta
            if reference:
                direct = np.array([math.log1p(math.exp(-abs(float(e))))+max(float(e), 0)-float(yy/nn)*float(e)
                    for e, yy, nn in zip(eta, y[test], n[test])])
                if not np.allclose(direct, loss[test], rtol=0, atol=1e-10):
                    raise ValueError('Independent per-election binomial loss disagrees')
            diagnostics.append({'fold': fold, 'train_elections': int(train.sum()), 'test_elections': int(test.sum()),
                'iterations': fit['iterations'], 'gradient_max': fit['gradient_max']})
        if not np.isfinite(loss[weights > 0]).all():
            raise stats.Unsupported('Incomplete candidate-fold predictions')
        means[model] = float(np.sum(loss[weights > 0]*weights[weights > 0])/weights.sum())
        if reference:
            direct_mean = math.fsum(float(loss[i])*float(weights[i]) for i in range(len(rows)) if weights[i] > 0)/float(weights.sum())
            if abs(direct_mean-means[model]) > 1e-10:
                raise ValueError('Independent equal-election weighting disagrees')
        fits[model] = diagnostics
    best = min(stats.MODELS[:3], key=lambda m: means[m])
    return {'primary': means[best]-means['THREE'], 'mean_election_log_losses': means,
        'best_two': best, 'candidate_clusters': len({r['candidate'] for r in rows}),
        'folds': fits, 'representation': 'signed_rates',
        'mode': 'pooled_descriptive' if pooled else 'candidate_out_of_fold', 'case': case}


def against(rows, weights=None, callback=lambda: None):
    """One extra against-comment on a previously neither-polarity comment.

    Six presence-rate coefficients are fit on the full primary cohort. Only the
    counterfactual evaluation uses the common feasible subset for all three reads.
    For-count, overlap and N stay fixed. It is a fitted association, not an effect.
    """
    weights = np.ones(len(rows)) if weights is None else np.asarray(weights, dtype=float)
    feasible = np.array([all(r['early']['comments']-(c['for_comments']+c['against_comments']-c['overlap_comments']) >= 1
        for c in r['early']['reads'].values()) for r in rows], dtype=bool)
    evaluation = feasible & (weights > 0)
    count = len({r['candidate'] for r, ok in zip(rows, feasible) if ok})
    base = {'common_feasible_elections': int(feasible.sum()), 'excluded_elections': int((~feasible).sum()),
        'common_feasible_candidate_clusters': count, 'fitted_population': 'full primary cohort',
        'evaluation_population': 'common feasible subset', 'denominator_and_overlap_fixed': True,
        'causal_interpretation': False, 'contrast_unit': 'one additional early against-comment'}
    if not evaluation.any():
        return dict(base, status='unsupported', reason='no common feasible election', contrasts={k: None for k in stats.READS})
    callback()
    try:
        x, names = stats.design(rows, 'THREE', 'separate_polarities')
        y = np.array([r['later_support'] for r in rows], dtype=float)
        n = np.array([r['later_support']+r['later_oppose'] for r in rows], dtype=float)
        fit = stats.fit_binomial(x, y, n, weights)
        eta = stats.predict_eta(x[evaluation], fit)
        before = np.exp(-np.logaddexp(0, -eta))
        contrasts, unsupported = {}, {}
        for key in stats.READS:
            position = names.index(key+'_against')
            if position not in fit['selected']:
                contrasts[key] = None
                unsupported[key] = 'constant/unidentified against coefficient'
                continue
            coefficient = float(fit['coefficients'][fit['selected'].index(position)])
            denom = np.array([r['early']['comments'] for r, ok in zip(rows, evaluation) if ok], dtype=float)
            after = np.exp(-np.logaddexp(0, -(eta+coefficient/denom)))
            contrasts[key] = float(np.average(after-before, weights=weights[evaluation]))
        return dict(base, status='descriptive', contrasts=contrasts, unsupported=unsupported)
    except stats.Unsupported as error:
        return dict(base, status='unsupported', reason=str(error), contrasts={k: None for k in stats.READS})


def evaluate(rows, weights=None, callback=lambda: None, reference=False):
    clusters = len({r['candidate'] for r in rows})
    try:
        fitted = primary(rows, weights, pooled=clusters < 20, callback=callback, reference=reference)
    except stats.Unsupported as error:
        fitted = {'primary': None, 'candidate_clusters': clusters, 'mode': 'pooled_descriptive' if clusters < 20 else 'candidate_out_of_fold',
            'status': 'design_cannot_test', 'reason': str(error), 'case': primary_case(rows)}
    secondary = against(rows, weights, callback) if rows else {'status': 'unsupported', 'reason': 'no elections',
        'contrasts': {k: None for k in stats.READS}, 'common_feasible_candidate_clusters': 0}
    return {'primary_fit': fitted, 'against_comment': secondary}


def select_rows(rows, inputs, config):
    selection = config.get('whole_candidate_sample')
    if selection is None:
        return rows
    if selection.get('authorization') != 'measured_amendment_E':
        raise ValueError('Candidate sampling requires the measured cost route')
    receipt, review = Path(inputs['sample_cost_receipt']), Path(inputs['sample_review'])
    if source.sha(receipt) != selection['cost_receipt_sha256'] or source.sha(review) != selection['review_sha256']:
        raise ValueError('Measured sample evidence changed')
    evidence, owner = read(receipt), read(review)
    if evidence.get('observed_cpu_seconds', 0) <= 0 or owner.get('decision') != 'qualified_measured_whole_candidate_sample' or owner.get('cost_receipt_sha256') != source.sha(receipt) or owner.get('size') != selection['size']:
        raise ValueError('Sample size is not covered by actual cost and owner review')
    unique = sorted({r['candidate'] for r in rows}, key=lambda c: hashlib.sha256(f'RF1-sample|20261112|{c}'.encode()).digest())
    size = selection['size']
    if type(size) is not int or not 20 <= size <= len(unique):
        raise ValueError('Whole-candidate sample is outside its declared support')
    chosen = set(unique[:size])
    return [r for r in rows if r['candidate'] in chosen]


def interval(values, estimate, clusters):
    valid = [v for v in values if v is not None and math.isfinite(v)]
    result = {'estimate': estimate, 'interval': None, 'se': None, 'valid_draws': len(valid), 'requested_draws': DRAWS}
    if estimate is None:
        return dict(result, status='unsupported')
    if clusters < 20:
        return dict(result, status='below_floor_descriptive')
    if len(valid) != DRAWS:
        return dict(result, status='unsupported_or_incomplete_uncertainty')
    bounds = np.quantile(valid, [.025, .975], method='linear')
    return dict(result, interval=[float(v) for v in bounds], se=float(np.std(valid, ddof=1)), status='descriptive')


def summarize(point, draws):
    fitted = point['primary_fit']
    if fitted['primary'] is None:
        primary_result = {'estimate': None, 'bar': .002, 'interval': None, 'se': None, 'sees': None, 'supports_at': None,
            'status': 'design_cannot_test', 'reason': fitted['reason'], 'valid_draws': 0, 'requested_draws': DRAWS}
    else:
        primary_result = stats.uncertainty(fitted, [{'primary': d['value']['primary_fit']['primary']} for d in draws])
    sec = point['against_comment']
    secondary = {k: interval([d['value']['against_comment']['contrasts'][k] for d in draws], sec['contrasts'][k], sec['common_feasible_candidate_clusters']) for k in stats.READS}
    differences = {}
    for a, b in (('trust', 'respect'), ('trust', 'liking'), ('respect', 'liking')):
        estimate = None if sec['contrasts'][a] is None or sec['contrasts'][b] is None else sec['contrasts'][a]-sec['contrasts'][b]
        values = []
        for draw in draws:
            current = draw['value']['against_comment']['contrasts']
            values.append(None if current[a] is None or current[b] is None else current[a]-current[b])
        differences[a+'_minus_'+b] = interval(values, estimate, sec['common_feasible_candidate_clusters'])
    return {'primary': primary_result, 'against_comment': secondary, 'against_pairwise_descriptive': differences}


def produce(output, inputs, config, reference=False):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    try:
        check_yield(output)
        original, mapping, source_support = qualified.load(inputs, config)
        population, support = qualified.ordered_elections(original, mapping)
        rows = select_rows(population, inputs, config)
        frozen_config = {k: v for k, v in config.items() if k not in ('max_new_draw_blocks',)}
        binding = {'schema': 'RF1-ANALYSIS-BINDING-3', 'config': frozen_config,
            'analysis_sha256': source.sha(__file__), 'qualified_source_sha256': source.sha(qualified.__file__),
            'statistics_sha256': source.sha(stats.__file__), 'source_support': source_support,
            'population_elections': len(population), 'selected_elections': len(rows),
            'selected_rows_sha256': hashlib.sha256(source.canonical(rows)).hexdigest(),
            'bootstrap_draws': DRAWS, 'bootstrap_seed': 20261107, 'candidate_fold_seed': 20261112,
            'draw_block': DRAW_BLOCK, 'primary_representation': 'signed_rates',
            'secondary': 'six comment-presence rates; one additional against-comment; fixed N/for-count/overlap'}
        source.write_equal(output/'BINDING.json', binding)
        source.write_equal(output/'ELECTION_SUPPORT.json', support)
        pin = source.sha(output/'BINDING.json')
        callback = lambda: check_yield(output)
        point = evaluate(rows, callback=callback, reference=reference)
        source.write_equal(output/'POINT.json', point)
        clusters = len({r['candidate'] for r in rows})
        target = DRAWS if clusters >= 20 and (point['primary_fit']['primary'] is not None or any(v is not None for v in point['against_comment']['contrasts'].values())) else 0
        draws, names, new = [], [], 0
        for start in range(0, target, DRAW_BLOCK):
            callback()
            stop = min(start+DRAW_BLOCK, target)
            path = output/f'draw-{start:04d}.json'
            names.append(path.name)
            if path.exists():
                block = read(path)
                if read(path.with_suffix('.seal.json'))['sha256'] != source.sha(path) or block['binding_sha256'] != pin or block['indices'] != list(range(start, stop)):
                    raise ValueError('RF1 checkpoint source, bytes or global indices changed')
            else:
                if new >= config.get('max_new_draw_blocks', 10**9):
                    raise YieldRequested()
                values = []
                for index in range(start, stop):
                    callback()
                    weights = stats.bootstrap_weights([r['candidate'] for r in rows], index)
                    if reference and not np.array_equal(weights, independent_weights(rows, index)):
                        raise ValueError('Whole-candidate bootstrap oracle differs')
                    values.append({'index': index, 'weights_sha256': hashlib.sha256(weights.astype('<f8').tobytes()).hexdigest(),
                        'value': evaluate(rows, weights, callback, reference)})
                block = {'binding_sha256': pin, 'indices': list(range(start, stop)), 'values': values}
                source.write_equal(path, block)
                source.write_equal(path.with_suffix('.seal.json'), {'sha256': source.sha(path)})
                new += 1
            if [v['index'] for v in block['values']] != list(range(start, stop)):
                raise ValueError('RF1 draw values do not preserve global indices')
            draws.extend(block['values'])
        observed = sorted(p.name for p in output.glob('draw-*.json') if '.seal.' not in p.name)
        if observed != sorted(names):
            raise ValueError('Unexpected bootstrap checkpoint belongs to another scope')
        result = {'schema': 'RF1-RESULT-3', 'binding_sha256': pin, 'point': point, 'uncertainty': summarize(point, draws),
            'population_elections': len(population), 'selected_elections': len(rows), 'candidate_clusters': clusters,
            'bootstrap_draws': len(draws), 'sample_scoped': config.get('whole_candidate_sample') is not None,
            'below_floor_fallback': 'pooled descriptive fit' if clusters < 20 else None,
            'record_kind': 'claim', 'theory_tags': ['H15-T3'], 'by_construction': bool(config.get('constructed_fixture')),
            'activation': [{'channel': 'social reads of a candidate', 'setpoint': 'unmeasured',
                'what_moved': 'early respect, trust and liking words', 'action': 'later support or oppose votes',
                'observation': 'lexical comments and office-election choices',
                'says_nothing_about': 'felt emotion, causal reputation changes or general three-read ontology'}],
            'scientific_admission': False}
        source.write_equal(output/'RESULT.json', result)
        source.write_equal(output/'ANALYSIS_COMPLETE.json', {'binding_sha256': pin,
            'result_sha256': source.sha(output/'RESULT.json'), 'draws': {name: source.sha(output/name) for name in names}})
        return {'status': 'complete', 'scientific_admission': False, 'result_sha256': source.sha(output/'RESULT.json')}
    except YieldRequested:
        return {'status': 'yielded', 'reason': 'sealed_RF1_candidate_checkpoint_or_requested_quantum', 'scientific_admission': False}


def execute(output, inputs, config):
    return produce(output, inputs, config)


def verify(output, inputs, config):
    output = Path(output)
    if not (output/'ANALYSIS_COMPLETE.json').exists():
        raise ValueError('Incomplete RF1 cannot verify')
    replay = output/'independent-replay'
    result = produce(replay, inputs, config, reference=True)
    if result['status'] == 'yielded':
        return dict(result, verified=False)
    complete = read(output/'ANALYSIS_COMPLETE.json')
    for name in ('BINDING.json', 'ELECTION_SUPPORT.json', 'POINT.json', 'RESULT.json', 'ANALYSIS_COMPLETE.json', *complete['draws']):
        if (output/name).read_bytes() != (replay/name).read_bytes():
            raise ValueError('Full RF1 fresh replay differs')
    return {'verified': True, 'full_election_and_candidate_refit_replay': True,
        'candidate_weight_and_binomial_loss_oracles': True, 'scientific_admission': False}
