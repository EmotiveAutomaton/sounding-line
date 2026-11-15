"""Bounded LA6 consumer of the complete all-utterance prepared table.

DESIGN CHECK: LESSONS 2,3. Explicit owner review binds source and conventions;
all two-thousand whole-meeting draws and both registered arms must finish.
Invalid category support is retained, never redrawn. Fresh replay uses a new
checkpoint namespace and compares every field, not a preselected headline.
"""
from pathlib import Path
import time

import numpy as np
from sklearn.metrics import roc_auc_score

from . import week6_la6_v1 as math
from . import week6_la6_source_v1 as source
from . import week5_engine_export_io as seal
from . import week5_qualification_io as io
from . import week5_rr3_v1 as compare

MODULE = 'runners.drive.cards.week6_la6_runner_v1'


def classify_interval(interval):
    """Week 5 three-way rule on LA6's unchanged raw AUC scale."""
    bounds = np.asarray(interval, float)
    if bounds.shape != (2,) or not np.isfinite(bounds).all() or not 0 <= bounds[0] <= bounds[1] <= 1:
        raise ValueError('Ordered finite AUC interval in [0,1] required')
    if bounds[0] > math.BAR:
        return 'supports'
    # AUC cannot be below zero; the generic +/-bar region reduces to upper<=bar.
    if bounds[1] <= math.BAR:
        return 'against'
    return 'inconclusive'


def review_contract(complete_hash):
    return {'admission': 'LA6-source-and-statistic-v1', 'approved': True,
            'prepared_complete_sha256': complete_hash, 'all_original_utterances': True,
            'math_sha256': io.sha(math.__file__), 'runner_sha256': io.sha(__file__),
            'source_adapter_sha256': io.sha(source.__file__),
            'conventions': 'all-vocal-labels-left1-right2;start-distance30;replacement;observed-span;C1;meeting-CV5'}


def load(inputs):
    if set(inputs) != {'prepared_run', 'owner_review'}:
        raise ValueError('Complete prepared source and exact owner review required')
    root, _, _ = seal.complete(inputs['prepared_run'], source.MODULE)
    review = seal.read(inputs['owner_review'])
    expected = review_contract(io.sha(root / 'COMPLETE.json'))
    if review != expected:
        raise ValueError('Owner source/statistic review does not bind this implementation')
    result = seal.read(root / 'output' / 'RESULT.json')
    table_path = root / 'output' / 'TABLE.json'
    if result.get('complete_preparation') is not True or io.sha(table_path) != result['table_sha256']:
        raise ValueError('Incomplete or changed all-utterance table')
    table = seal.read(table_path)
    return table['rows'], {'prepared_complete': expected['prepared_complete_sha256'],
                           'table_sha256': result['table_sha256'], 'owner_review': review}


def point(rows):
    result = {}
    for include in (True, False):
        cv = math.held_out(rows, include)
        model, template = math.fitted(rows, include)
        offset = 9 if include else 8
        result[str(include)] = {'auc': cv['auc'], 'predictions': cv['predictions'].tolist(),
            'folds': cv['folds'], 'categories': template[0],
            'coefficients': model.coef_[0][offset:].tolist()}
    return result


def one_draw(rows, base, ordinal):
    meetings = sorted({r['meeting'] for r in rows}); code = {m: i for i, m in enumerate(meetings)}
    group = np.asarray([code[r['meeting']] for r in rows]); y = [r['label'] for r in rows]
    rng = np.random.default_rng(np.random.SeedSequence([math.SEED, ordinal, 6]))
    w = np.bincount(rng.integers(len(meetings), size=len(meetings)), minlength=len(meetings))[group]
    result = {}
    for include in (True, False):
        previous = base[str(include)]
        auc = float(roc_auc_score(y, previous['predictions'], sample_weight=w))
        if {r['act_type'] for i, r in enumerate(rows) if w[i] > 0} != set(previous['categories']):
            coefficients = None
        else:
            model, _ = math.fitted(rows, include, w)
            coefficients = model.coef_[0][9 if include else 8:].tolist()
        result[str(include)] = {'auc': auc, 'coefficients': coefficients}
    return result


def summarize(base, bank, meetings):
    if len(bank) != 2000:
        raise ValueError('Incomplete whole-meeting draw bank')
    output = {}
    for include, name in ((True, 'with_laugh_history'), (False, 'without_laugh_history')):
        arm = base[str(include)]; draws = [r[str(include)] for r in bank]
        values = [r['auc'] for r in draws]
        interval = np.quantile(values, [.025, .975]).tolist()
        se = float(np.std(np.asarray(values) - values[0], ddof=1))
        failed = [i for i, r in enumerate(draws) if r['coefficients'] is None]
        odds = {arm['categories'][0]: {'odds_ratio': 1., 'reference': True}}
        for i, category in enumerate(arm['categories'][1:]):
            odds[category] = {'odds_ratio': float(np.exp(arm['coefficients'][i])), 'reference': False,
                'interval': None if failed else np.exp(np.quantile([r['coefficients'][i] for r in draws], [.025, .975])).tolist()}
        status = 'below floor, descriptive' if meetings < 20 else 'degenerate, descriptive' if se == 0 else 'ok'
        outcome = classify_interval(interval) if status == 'ok' else None
        output[name] = {'auc': arm['auc'], 'interval': interval, 'bar': math.BAR, 'bootstrap_SE': se,
                       'sees_above_chance': 2.8 * se, 'supports_at': math.BAR + 2.8 * se,
                       'act_odds': odds, 'act_interval_failed_draws': failed, 'status': status, 'outcome': outcome,
                       'folds': arm['folds']}
    return output


def settings(config):
    if set(config) - {'phase', 'draws', 'max_new_draws', 'max_wall_seconds'} or config.get('phase') != 'LA6' or config.get('draws', 2000) != 2000:
        raise ValueError('Exact LA6 two-thousand-draw phase required')
    limit, seconds = config.get('max_new_draws', 10), float(config.get('max_wall_seconds', 600))
    if type(limit) is not int or limit <= 0 or not np.isfinite(seconds) or not 0 < seconds <= 1200:
        raise ValueError('Positive bounded draw quantum required')
    return limit, seconds


def operation(output, inputs, config):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    limit, seconds = settings(config); began = time.monotonic(); cpu = time.process_time()
    rows, identity = load(inputs); meetings = len({r['meeting'] for r in rows})
    binding = source.digest({'source': identity, 'module': io.sha(__file__)})
    state = seal.state(output / 'DRAWS.json', binding, {'draws': []})
    if meetings < 2:
        pooled = {}
        if rows:
            for include in (True, False):
                model, template = math.fitted(rows, include)
                pooled[str(include)] = {'reference_act': template[0][0],
                    'act_coefficients': model.coef_[0][9 if include else 8:].tolist()}
        result = {'card': 'LA6', 'complete_computation': True, 'status': 'below floor, descriptive',
                  'reason': 'fewer than two matched meetings', 'pooled_descriptive': pooled,
                  'meetings': meetings, 'draws': 0, 'source_identity': identity}
    else:
        if 'point' not in state:
            state['point'] = point(rows); seal.checkpoint(output / 'DRAWS.json', state)
        added = 0
        while len(state['draws']) < 2000:
            if added >= limit or source.requested(output, began, seconds):
                return {'status': 'yielded', 'verified': False, 'phase': 'LA6_meeting_draws',
                        'completed': len(state['draws']), 'total': 2000}
            state['draws'].append(one_draw(rows, state['point'], len(state['draws'])))
            seal.checkpoint(output / 'DRAWS.json', state); added += 1
        result = {'card': 'LA6', 'complete_computation': True, 'status': 'complete',
                  'meetings': meetings, 'draws': 2000, 'source_identity': identity,
                  'arms': summarize(state['point'], state['draws'], meetings)}
    result.update(record_kind='claim', theory_tags=['H18-S5'], by_construction=False, activation=[])
    io.write_json(output / 'RESULT.json', result)
    io.write_json(output / 'COST.json', {'process_CPU_seconds': time.process_time() - cpu,
                                       'scope': 'this invocation; total process/native charges remain external'})
    return result


def execute(output, inputs, config):
    return operation(output, inputs, config)


def verify(output, inputs, config):
    output = Path(output); result = operation(output / 'independent-replay', inputs, config)
    if result.get('status') == 'yielded':
        return result
    compare.compare_record(seal.read(output / 'RESULT.json'), result)
    return {'verified': True, 'both_arms_and_every_draw_replayed': True,
            'replay_kind': 'fresh reconstruction with frozen solver; independent AUC/matching rulers are fixture checks'}
