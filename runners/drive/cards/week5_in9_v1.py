"""IN9 items-first table card, isolated two-day packet implementation.

DESIGN CHECK: LESSONS 2-5, CONTROLS 6-7; writer folds never split a person.
Every resample refits all five training-only ridge fits. Text cues are separate.
Independent verification uses a different likelihood solver and AUC algorithm.
"""
from pathlib import Path
import hashlib
import json
import os
import time
for _key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_key] = '2'
import numpy as np
import pandas as pd
from . import week5_in as source
from . import week5_in9_math_v1 as math
from . import week5_in9_reference_v1 as reference
from . import week5_engine_export_io as seal
from . import week5_qualification_io as io

SOURCE_PIN = '196fe2a4f72b36ae91516ee5caf762cb3ba04f7d69b6da4e53958587d44c1638'
ITEMS = tuple(source.APPRAISALS)+('intensity',)
SECONDARY = ('suddenness', 'predict_event', 'self_responsblt', 'standards', 'social_norms', 'other_control')
ACTIVATION = [dict(channel='SHAME', set_point='seen as competent or kind (proposal)',
    what_moved='self-reported appraisals under the shame versus guilt prompt',
    what_could_be_done='not measured by the items-first classifier',
    observed='pending complete result', relation='says nothing about tissue or two feelings'),
    dict(channel='CARE', set_point=None, what_moved='guilt prompt appraisal profile',
    what_could_be_done='not measured by the items-first classifier',
    observed='pending complete result', relation='guilt-as-CARE remains the thread proposal')]


def dependencies():
    return {Path(m.__file__).as_posix(): io.sha(m.__file__) for m in
            (source, math, reference, seal, io)} | {Path(__file__).as_posix(): io.sha(__file__)}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def load(inputs):
    if set(inputs) != {'source_run'}:
        raise ValueError('Only the landed IN source table is an input')
    root, plan, _ = seal.complete(inputs['source_run'], 'runners.drive.cards.week5_in')
    if plan['config']['phase'] != 'prepare':
        raise ValueError('Input must be the complete original source projection')
    table = root/'output/generation.parquet'
    if io.sha(table) != SOURCE_PIN:
        raise ValueError('Qualified generation table pin differs')
    cols = ['emotion', 'text_id', 'prolific_id', *ITEMS]
    frame = pd.read_parquet(table, columns=cols)
    frame = frame.loc[frame.emotion.isin(['shame', 'guilt'])].sort_values('text_id').reset_index(drop=True)
    if frame.text_id.duplicated().any() or frame[['text_id', 'prolific_id']].isna().any().any():
        raise ValueError('Missing or duplicate private source keys')
    if not np.isfinite(frame[list(ITEMS)].to_numpy(float)).all():
        raise ValueError('Nonfinite qualified appraisal items')
    return frame, {'table_sha256': SOURCE_PIN, 'source_complete_sha256': io.sha(root/'COMPLETE.json')}


def settings(config):
    if set(config)-{'phase', 'draws', 'max_new_draws', 'max_wall_seconds'}:
        raise ValueError('Undeclared IN9 settings')
    if config.get('phase') != 'IN9-items' or config.get('draws', 2000) != 2000:
        raise ValueError('Exact primary phase and full2000-draw uncertainty required')
    if int(config.get('max_new_draws', 100)) <= 0 or float(config.get('max_wall_seconds', 900)) <= 0:
        raise ValueError('Positive operational bound required')


def summaries(point, draws, counts, writers):
    failure = [i for i, d in enumerate(draws) if d.get('failure')]
    base = {'draws': len(draws), 'failed_draws': failure, 'prompt_counts': counts, 'writers': writers}
    if failure or point.get('failure'):
        return {**base, 'status': 'invalid uncertainty', 'reason': 'all failures retained; no redrawing'}
    value = float(point['value'][0]); a = np.asarray([d['value'] for d in draws])
    interval = np.quantile(a, [.025, .975], axis=0).T
    se = a.std(axis=0, ddof=1)
    lower, upper = interval[0]
    outcome = ('different prompt appraisal profiles' if lower > .60 else
               'inside appraisal equivalence band' if lower >= .45 and upper <= .55 else 'inconclusive')
    primary = dict(estimate=value, interval=interval[0].tolist(), bar=.60,
        equivalence_band=[.45, .55], outcome=outcome, bootstrap_SE=float(se[0]),
        effect_above_chance=value-.5, practical_gain_above_chance=.10,
        sees=float(2.8*se[0]), sees_absolute_auc=float(.5+2.8*se[0]),
        supports_at=float(.60+2.8*se[0]), limited_sensitivity=bool(2.8*se[0] > .1),
        approximation='normal; slightly optimistic; sees is gain above chance',
        degenerate_bootstrap=bool(se[0] == 0))
    if writers < 20:
        primary.pop('outcome')
        primary['interpretation'] = 'below writer floor, descriptive'
    secondary = {name: dict(estimate=point['value'][j+1], interval=interval[j+1].tolist(),
                           bootstrap_SE=float(se[j+1]), direction='shame minus guilt; raw rating points')
                 for j, name in enumerate(SECONDARY)}
    return {**base, 'status': 'complete', 'primary': primary, 'secondary': secondary}


def calculate(frame, output, identity, config, independent=False):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    settings(config); counts = {k: int(frame.emotion.eq(k).sum()) for k in ('shame', 'guilt')}
    base = dict(card='IN9-items', record_kind='claim', theory_tags=['H15-T5'], by_construction=False,
        activation=ACTIVATION, scope='adult prompted self-report; discriminates prompt use, not feelings or tissue',
        source_support=counts, source_gap='R13-R15 handoffs and underlying theory-thread turns absent; packet formulas govern')
    if min(counts.values()) < 200:
        return {**base, 'status': 'unsupported', 'reason': 'fewer than200 texts in either prompt', 'complete_card': True}
    x = frame[list(ITEMS)].to_numpy(float); y = frame.emotion.eq('shame').to_numpy(int)
    folds, codes, keys = math.fold_codes(frame.prolific_id.to_numpy(str))
    if len(keys) < 5:
        return {**base, 'status': 'unsupported', 'reason': 'fewer than5 writers cannot supply five writer-held-out folds',
                'complete_card': True, 'writer_count': len(keys)}
    positions = [ITEMS.index(k) for k in SECONDARY]
    binding = digest({'identity': identity, 'modules': dependencies(), 'draws': 2000,
        'items': ITEMS, 'folds_sha': hashlib.sha256(folds.tobytes()).hexdigest(), 'ridge': math.RIDGE,
        'independent_replay': independent})
    saved = seal.state(output/'DRAWS.json', binding, {'draws': [], 'point': None})
    evaluate = reference.evaluate if independent else math.evaluate
    def one(weight):
        try:
            value = evaluate(x, y, folds, weight, positions)
            if not np.isfinite(value).all():
                raise ValueError('nonfinite fitted value')
            return {'value': value}
        except (ValueError, np.linalg.LinAlgError) as error:
            return {'failure': str(error)}
    if saved['point'] is None:
        saved['point'] = one(np.ones(len(y)))
        seal.checkpoint(output/'DRAWS.json', saved)
    started = time.monotonic(); cpu = time.process_time(); added = 0
    request_root = output.parent if output.name == 'independent-replay' else output
    while len(saved['draws']) < 2000:
        if (added >= int(config.get('max_new_draws', 100)) or
            time.monotonic()-started >= float(config.get('max_wall_seconds', 900)) or
            any((request_root/p).exists() for p in ('YIELD_REQUEST.json', 'STOP_REQUEST.json'))):
            seal.checkpoint(output/'DRAWS.json', saved)
            return {'status': 'yielded', 'verified': False, 'phase': 'IN9_writer_draws',
                    'completed': len(saved['draws']), 'total': 2000}
        saved['draws'].append(one(math.draw_weights(codes, len(saved['draws'])))); added += 1
        if added == 1 and not (output/'COST_PREFIX.json').exists():
            io.write_json(output/'COST_PREFIX.json', {'first_draw_CPU_seconds': time.process_time()-cpu,
                'scope': 'counted actual first writer draw; does not include complete replay or source IO'})
        if len(saved['draws']) % 10 == 0:
            seal.checkpoint(output/'DRAWS.json', saved)
            io.write_json(output/'PROGRESS.json', {'phase': 'IN9_writer_draws', 'completed': len(saved['draws']), 'total': 2000})
    seal.checkpoint(output/'DRAWS.json', saved)
    result = summaries(saved['point'], saved['draws'], counts, len(keys))
    result.update(base, complete_card=True, uncertainty='complete whole-writer resampling with all CV models refitted',
                  ridge=math.RIDGE, folds=5, text_cues='separate, unqualified until cue instrument passes')
    observed = ({'auc': result['primary']['estimate'], 'interval': result['primary']['interval'],
                 'prompt_counts': counts} if 'primary' in result else {'status': result['status']})
    result['activation'] = [dict(a, observed=observed,
        relation='says nothing about biological channel identity') for a in ACTIVATION]
    return result


def execute(output, inputs, config):
    settings(config); frame, identity = load(inputs)
    result = calculate(frame, output, identity, config)
    if result.get('status') != 'yielded':
        io.write_json(Path(output)/'RESULT.json', result)
    return result


def verify(output, inputs, config):
    settings(config); output = Path(output); frame, identity = load(inputs)
    replay = calculate(frame, output/'independent-replay', identity, config, independent=True)
    if replay.get('status') == 'yielded':
        return {**replay, 'verified': False}
    original = seal.read(output/'RESULT.json')
    if replay['status'] != original['status'] or replay['source_support'] != original['source_support']:
        raise ValueError('Independent source support/status differs')
    if (output/'DRAWS.json').exists():
        left = seal.read(output/'DRAWS.json'); right = seal.read(output/'independent-replay/DRAWS.json')
        for a, b in zip([left['point'], *left['draws']], [right['point'], *right['draws']], strict=True):
            if bool(a.get('failure')) != bool(b.get('failure')):
                raise ValueError('Independent failure disposition differs')
            if 'value' in a and not np.allclose(a['value'], b['value'], atol=2e-6, rtol=0):
                raise ValueError('Independent ridge/CV/AUC or item formula differs')
        if len(left['draws']) != 2000 or len(right['draws']) != 2000:
            raise ValueError('Full intended draw bank required')
        if not any(row.get('failure') for row in right['draws']) and not right['point'].get('failure'):
            for j, name in enumerate(('primary', *SECONDARY)):
                interval, se = reference.interval_and_se([row['value'][j] for row in right['draws']])
                reported = original['primary'] if name == 'primary' else original['secondary'][name]
                if not np.allclose(interval, reported['interval'], atol=2e-6, rtol=0) or abs(se-reported['bootstrap_SE']) > 2e-6:
                    raise ValueError('Independent interval or bootstrap-SE formula differs')
    io.write_json(output/'independent-replay/RESULT.json', replay)
    return {'verified': True, 'independent_optimizer_and_auc': True,
            'full_writer_bank_replayed': (output/'DRAWS.json').exists(), 'unsupported_has_no_inference': replay['status']=='unsupported'}
