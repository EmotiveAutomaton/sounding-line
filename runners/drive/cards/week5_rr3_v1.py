"""RR3: pooled recent prediction errors versus distance from play start.

DESIGN CHECK: same qualified RR1 fixed actual-attempt cohort and eight controls;
one added strictly past covariate, full person resampling, independent formulas.
"""
from pathlib import Path
import hashlib
import json
import os
import time
for _key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_key] = '2'
import numpy as np
from . import week5_rr1 as previous
from . import week5_rr3_math_v1 as math
from . import week5_md3_bounded as fit
from . import week5_md_analysis as features
from . import week5_md12_bounded as bounded
from . import week5_md as core
from . import week5_engine_export_io as seal
from . import week5_qualification_io as io

MODULE = 'runners.drive.cards.week5_rr3_v1'
PANELS = ('pooled', '1', '2', '3', '4+')
BAR = .05


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def dependencies():
    modules = (previous, math, fit, features, bounded, core, seal, io)
    return {Path(m.__file__).as_posix(): io.sha(m.__file__) for m in modules} | {Path(__file__).as_posix(): io.sha(__file__)}


def settings(config):
    allowed = {'phase', 'draws', 'max_new_draws', 'max_wall_seconds'}
    if set(config)-allowed or config.get('phase') != 'RR3' or config.get('draws', 2000) != 2000:
        raise ValueError('RR3 requires the complete frozen 2000-draw configuration')
    if type(config.get('max_new_draws', 500)) is not int or config.get('max_new_draws', 500) <= 0:
        raise ValueError('Positive integer draw quantum required')
    if not np.isfinite(float(config.get('max_wall_seconds', 900))) or float(config.get('max_wall_seconds', 900)) <= 0:
        raise ValueError('Positive time quantum required')
    return {'phase': 'RR3', 'draws': 2000, 'reference': 'play_start',
            'primary': 'pooled observed plays in fixed actual-1/2/3 cohort',
            'secondary_actual_attempt_panels': list(PANELS[1:]), 'first_trial': 'excluded; no past outcome',
            'scale': 'original global first-play scales; common standing SD; global first-play RECENT SD',
            'bar': BAR, 'resampling': 'original RR1 whole-person seed stream 36'}


def load(inputs):
    if set(inputs) != {'rr1_run'}:
        raise ValueError('Exact complete RR1 configured parent required')
    root, plan, _ = seal.complete(inputs['rr1_run'], 'runners.drive.cards.week5_rr1')
    parent = seal.read(root/'output/RESULT.json')
    if parent.get('card') != 'RR1' or parent.get('complete_computation') is not True:
        raise ValueError('RR1 result is incomplete')
    previous.contract(plan['config'])
    task, md3, identity = previous.authenticate(plan['inputs'])
    data = features.load_verified(task)
    selected, census = previous.roster(data, plan['config'].get('participants'))
    if census != parent['census'] or parent['gamma'] != .65 or md3['primary']['gamma'] != .65:
        raise ValueError('Fixed RR1 population or inherited gamma differs')
    return data, selected, census, float(parent['standing_SD']), {
        'rr1_complete': io.sha(root/'COMPLETE.json'), 'rr1_result': io.sha(root/'output/RESULT.json'),
        'upstream': identity, 'implementation': dependencies()}


def prepare(data, selected, census, standing_sd, independent=False):
    fn = math.reference_recent if independent else math.recent
    original = features.dynamic_features(data['first'], .65)
    scale = original.reshape(-1, 8).std(axis=0, ddof=1).clip(1e-10)
    scale[3:5] = standing_sd
    recent_sd = float(fn(data['first'])[:, 1:].std(ddof=1))
    if not np.isfinite(scale).all() or np.any(scale <= 0) or not np.isfinite(recent_sd) or recent_sd <= 0:
        raise ValueError('Frozen reference scales must be finite and positive')
    plays = data['plays'][selected]
    old = features.dynamic_features(plays, .65)/scale
    new = fn(plays)/recent_sd
    xx = np.concatenate((old[:, 1:], new[:, 1:, None]), axis=2).reshape(-1, 9)
    yy = plays[:, 1:, 6].reshape(-1)
    person = np.repeat(data['person'][selected], 29)
    attempt = np.repeat(data['counter'][selected], 29)
    if not np.isfinite(xx).all() or not np.isin(yy, [0, 1]).all():
        raise ValueError('Complete finite covariates and binary choice required')
    support = {**census, 'analysed_choices': len(yy), 'first_trials_excluded_no_history': len(plays),
               'trials_with_one_prior': len(plays), 'trials_with_two_priors': len(plays),
               'trials_with_three_priors': 27*len(plays)}
    return {'x': xx, 'y': yy, 'person': person, 'attempt': attempt, 'census': support,
            'scales': list(map(float, scale))+[recent_sd]}


def summary(point, draws, people, independent=False):
    if point.get('failure'):
        return {'status': 'unsupported', 'reason': point['failure'], 'point': point,
                'participant_clusters': people, 'draws': 0, 'no_interval': True}
    if len(draws) != 2000:
        raise ValueError('Unfinished bank cannot be summarized')
    failed = [i for i, row in enumerate(draws) if row.get('failure')]
    if failed:
        return {'status': 'invalid_uncertainty', 'point': point['value'], 'failed_draws': failed,
                'participant_clusters': people, 'draws': 2000, 'no_interval': True}
    columns = list(zip(*(row['value'] for row in draws)))
    intervals, errors = zip(*(math.interval_and_se(x, independent) for x in columns))
    value = point['value']; interval = list(intervals[3]); se = errors[3]
    descriptive = people < 20 or point['informative_participants'] < 20
    outcome = ('below floor, descriptive' if descriptive else 'supports slope over level' if interval[0] > BAR
        else 'against slope over level' if interval[1] < -BAR
        else 'band-null' if interval[0] >= -BAR and interval[1] <= BAR else 'inconclusive')
    return {'status': 'ok', 'participant_clusters': people, 'informative_participants': point['informative_participants'],
        'draws': 2000, 'coefficients_recent_below_above': value[:3], 'coefficient_intervals': list(intervals[:3]),
        'primary': {'estimate': value[3], 'interval': interval, 'bar': BAR, 'bootstrap_SE': se,
            'sees': 2.8*se, 'supports_at': BAR+2.8*se, 'limited_sensitivity': 2.8*se > BAR,
            'degenerate_bootstrap': se == 0, 'normal_approximation_is_optimistic': True, 'outcome': outcome},
        'below_floor_descriptive': descriptive}


def panel(output, x, y, people, binding, budget, independent=False):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    keys, codes = np.unique(people, return_inverse=True)
    if not len(y):
        return {'status': 'unsupported', 'reason': 'no observed plays in actual-attempt panel', 'participant_clusters': 0}
    arrays = hashlib.sha256(np.ascontiguousarray(x).tobytes()+np.ascontiguousarray(y).tobytes()+np.ascontiguousarray(people).tobytes()).hexdigest()
    state = seal.state(output/'DRAWS.json', digest({'binding': binding, 'arrays': arrays, 'reference': independent}), {'draws': []})
    def one(weights=None):
        try:
            return math.evaluate(x, y, people, weights, independent)
        except bounded.YieldRequested:
            raise
        except (ValueError, np.linalg.LinAlgError, FloatingPointError) as exc:
            return {'failure': type(exc).__name__+': '+str(exc)}
    if 'point' not in state:
        state['point'] = one()
        seal.checkpoint(output/'DRAWS.json', state)
    if state['point'].get('failure'):
        return summary(state['point'], [], len(keys), independent)
    while len(state['draws']) < 2000:
        if budget['added'] >= budget['limit'] or bounded.wants_yield(fit.CLOCK):
            seal.checkpoint(output/'DRAWS.json', state)
            raise bounded.YieldRequested({'status': 'yielded', 'verified': False, 'phase': 'RR3_person_draws',
                'completed': len(state['draws']), 'total': 2000})
        draw = len(state['draws']); began = time.process_time()
        rng = np.random.default_rng(np.random.SeedSequence([core.SEED, draw, 36]))
        weights = np.bincount(rng.integers(0, len(keys), len(keys)), minlength=len(keys))
        try:
            state['draws'].append(one(weights))
        except bounded.YieldRequested:
            seal.checkpoint(output/'DRAWS.json', state)
            raise
        budget['added'] += 1
        if draw == 0 and not (output/'COST_PREFIX.json').exists():
            io.write_json(output/'COST_PREFIX.json', {'first_draw_CPU_seconds': time.process_time()-began,
                'excludes_source_IO_and_other_panels_and_replay': True})
        if (draw+1) % 10 == 0:
            seal.checkpoint(output/'DRAWS.json', state)
            io.write_json(output/'PROGRESS.json', {'phase': 'RR3_person_draws', 'completed': draw+1, 'total': 2000})
    seal.checkpoint(output/'DRAWS.json', state)
    return summary(state['point'], state['draws'], len(keys), independent)


def calculate(output, prepared, identity, config, independent=False):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    semantic = settings(config); binding = digest({'semantic': semantic, 'source': identity})
    state = seal.state(output/'PANELS.json', binding, {'panels': {}})
    budget = {'added': 0, 'limit': int(config.get('max_new_draws', 500))}
    x, y, people, attempts = (prepared[k] for k in ('x', 'y', 'person', 'attempt'))
    for name in PANELS:
        if name in state['panels']:
            saved = output/name.replace('+', 'plus')/'DRAWS.json'
            if state['panels'][name]['status'] in ('ok', 'invalid_uncertainty') and not saved.exists():
                raise ValueError('Completed panel bank is missing')
            if saved.exists():
                if io.sha(saved) != seal.read(saved.with_suffix('.seal.json'))['sha256']:
                    raise ValueError('Completed panel bank changed')
            continue
        take = np.ones(len(y), bool) if name == 'pooled' else (attempts >= 4 if name == '4+' else attempts == int(name))
        result = panel(output/name.replace('+', 'plus'), x[take], y[take], people[take], binding, budget, independent)
        result['observed_choices'] = int(take.sum())
        state['panels'][name] = result
        seal.checkpoint(output/'PANELS.json', state)
        io.write_json(output/'PROGRESS.json', {'phase': 'RR3_panels', 'completed': len(state['panels']), 'total': len(PANELS)})
    return {'card': 'RR3', 'record_kind': 'claim', 'theory_tags': ['H15-T6'], 'by_construction': False,
        'activation': [], 'activation_scope': 'No channel identity assigned: packet commissions game-score choices, not feeling measurements.',
        'complete_card': True, 'complete_computation': True, 'configuration': semantic, 'source_binding': binding,
        'census': prepared['census'], 'reference_scales': prepared['scales'], 'primary_panel': state['panels']['pooled'],
        'secondary_actual_attempt_panels': {k: state['panels'][k] for k in PANELS[1:]},
        'RECENT_distance_correlations': {'below': math.correlation(x[:, 8], x[:, 3], independent),
                                        'above': math.correlation(x[:, 8], x[:, 4], independent)},
        'scope': 'Pooled observed plays in the fixed RR1 actual-1/2/3 cohort; choices are not feelings; later missing saves stay unobserved.',
        'supporting_sources': 'R13-R15 and the referenced theory-thread handoff were absent at build; explicit packet formulas govern.'}


def operation(output, inputs, config, independent=False):
    settings(config); output = Path(output); output.mkdir(parents=True, exist_ok=True)
    data, selected, census, standing, identity = load(inputs)
    prepared = prepare(data, selected, census, standing, independent)
    old = fit.CLOCK; fit.CLOCK = bounded.clock_state(output, config); began = time.process_time()
    try:
        try:
            result = calculate(output, prepared, identity, config, independent)
        except bounded.YieldRequested as pause:
            result = {**pause.receipt, 'verified': False}
        if result.get('status') != 'yielded':
            io.write_json(output/'RESULT.json', result)
        io.write_json(output/'COST.json', {'process_CPU_seconds': time.process_time()-began,
            'status': result.get('status', 'complete'), 'all_source_IO_failed_work_and_replay_charge_externally': True})
        return result
    finally:
        fit.CLOCK = old


def execute(output, inputs, config):
    return operation(output, inputs, config)


def compare_record(left, right):
    if isinstance(left, dict):
        if not isinstance(right, dict) or set(left) != set(right):
            raise ValueError('Independent record fields differ')
        for key in left:
            compare_record(left[key], right[key])
    elif isinstance(left, list):
        if not isinstance(right, list) or len(left) != len(right):
            raise ValueError('Independent record vector differs')
        for a, b in zip(left, right, strict=True):
            compare_record(a, b)
    elif type(left) in (int, float) and type(right) in (int, float):
        if not np.isclose(left, right, rtol=0, atol=1e-7):
            raise ValueError('Independent record number differs')
    elif left != right:
        raise ValueError('Independent record value differs')


def verify(output, inputs, config):
    output = Path(output)
    replay = operation(output/'independent-replay', inputs, config, True)
    if replay.get('status') == 'yielded':
        return {**replay, 'verified': False}
    original = seal.read(output/'RESULT.json')
    compare_record(original, replay)
    if original['census'] != replay['census'] or original['configuration'] != replay['configuration']:
        raise ValueError('Independent RR3 support or semantic replay differs')
    for name in PANELS:
        relative = Path(name.replace('+', 'plus'))/'DRAWS.json'
        left_path, right_path = output/relative, output/'independent-replay'/relative
        if left_path.exists() != right_path.exists():
            raise ValueError('Independent panel inventory differs')
        if not left_path.exists():
            continue
        left, right = seal.read(left_path), seal.read(right_path)
        for a, b in zip([left['point'], *left['draws']], [right['point'], *right['draws']], strict=True):
            if bool(a.get('failure')) != bool(b.get('failure')):
                raise ValueError('Independent RR3 failure disposition differs')
            if 'value' in a and not np.allclose(a['value'], b['value'], rtol=0, atol=1e-7):
                raise ValueError('Independent history/coefficient contrast differs')
        if not left['point'].get('failure') and (len(left['draws']) != 2000 or len(right['draws']) != 2000):
            raise ValueError('Entire intended RR3 bank required')
        a = original['primary_panel'] if name == 'pooled' else original['secondary_actual_attempt_panels'][name]
        b = replay['primary_panel'] if name == 'pooled' else replay['secondary_actual_attempt_panels'][name]
        if a['status'] != b['status']:
            raise ValueError('Independent RR3 panel status differs')
        if a['status'] == 'ok':
            for key in ('estimate', 'interval', 'bootstrap_SE', 'sees', 'supports_at'):
                if not np.allclose(a['primary'][key], b['primary'][key], rtol=0, atol=1e-7):
                    raise ValueError('Independent RR3 interval/SE arithmetic differs')
    for key in ('below', 'above'):
        a, b = original['RECENT_distance_correlations'][key], replay['RECENT_distance_correlations'][key]
        if (a is None) != (b is None) or (a is not None and abs(a-b) > 1e-10):
            raise ValueError('Independent RECENT-distance correlation differs')
    return {'verified': True, 'all_required_panels_and_2000_draws_replayed': True,
            'independent_RECENT_contrast_interval_correlation_formulas': True,
            'qualified_grouped_likelihood_reused_unchanged': True}
