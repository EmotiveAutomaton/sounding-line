"""TR1 back-half candidate: bounded real-structure controls before human inference.

DESIGN CHECK: LESSONS 2-5 and CONTROLS 6-7. Repaired source support is inherited;
qualification is a verdict, not a filename. All 2,000 participant draws and all
three 2,000-person constructed worlds must finish. No partial scientific result.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import time
for _key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_key] = '2'
import numpy as np
from . import week5_tr1_math as math
from . import week5_qualification_io as io
from . import week5_engine_export_io as sealed
from . import week5_md_source_h1 as source
from . import week5_md as original

SEED = 20261111
BLOCK = 256
MODULE = 'runners.drive.cards.week5_tr1'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def dependencies():
    return {Path(module.__file__).as_posix(): io.sha(module.__file__)
            for module in (math, io, sealed, source, original)} | {Path(__file__).as_posix(): io.sha(__file__)}


def authenticate(inputs):
    if set(inputs) != {'source_run', 'md3_run'}:
        raise ValueError('Exact repaired source and completed MD3 parent are required')
    sr, sp, sc = sealed.complete(inputs['source_run'], 'runners.drive.cards.week5_md_source_h1')
    mr, mp, mc = sealed.complete(inputs['md3_run'], 'runners.drive.cards.week5_md3_bounded')
    task = sr / 'output/task.npz'
    if Path(mp['inputs']['task']).resolve() != task.resolve():
        raise ValueError('TR1 and the MD3 repeat cohort have different sources')
    receipt = sealed.read(sr / 'output/SOURCE.json')
    if receipt['version'] != 'MD-source.h1' or receipt['archive_sha256'] != source.ZIP_SHA or receipt['mat_sha256'] != source.MAT_SHA:
        raise ValueError('Repaired source or original archive identity differs')
    if receipt['task_sha256'] != io.sha(task) or sealed.read(sr / 'output/VERIFIED.json').get('verified') is not True:
        raise ValueError('Every-value source projection replay is required')
    parent = sealed.read(mr / 'output/RESULT.json')
    if parent.get('complete_computation') is not True or parent['primary']['gamma'] != math.GAMMA:
        raise ValueError('Complete MD3 and frozen .65 forgetting factor required')
    return task, {'source_complete': io.sha(sr / 'COMPLETE.json'), 'md3_complete': io.sha(mr / 'COMPLETE.json'),
                  'source_task': io.sha(task), 'implementation': dependencies(), 'gamma': math.GAMMA}


def roster(data):
    people = np.asarray(data['person'])
    if len(data['repeat_eligible']) != len(people):
        raise ValueError('Source support mask length differs')
    keep, audit = [], {'ambiguous_people_excluded': 0, 'one_play_people_excluded': 0}
    if not len(people):
        return np.array([], int), np.array([], int), {**audit, 'people': 0, 'plays': 0}
    order = np.lexsort((data['counter'], people))
    starts = np.flatnonzero(np.r_[True, np.diff(people[order]) != 0])
    for ii in np.split(order, starts[1:]):
        if not data['repeat_eligible'][ii].all():
            audit['ambiguous_people_excluded'] += 1; continue
        if len(ii) < 2:
            audit['one_play_people_excluded'] += 1; continue
        if np.any(np.diff(data['counter'][ii]) <= 0):
            raise ValueError('Repeat-source attempted-play collision')
        keep.extend(ii)
    keep = np.asarray(keep, int)
    _, compact = np.unique(people[keep], return_inverse=True)
    audit.update(people=len(np.unique(compact)), plays=len(keep))
    return keep, compact, audit


class Budget:
    def __init__(self, output, config):
        self.root = Path(output); self.started = time.monotonic(); self.units = 0
        self.max_units = int(config.get('max_new_draws', 100))
        self.max_wall = float(config.get('max_wall_seconds', 900))
        if self.max_units <= 0 or self.max_wall <= 0:
            raise ValueError('Positive bounded work quantum required')

    def tick(self):
        self.units += 1

    def yield_requested(self):
        return (self.units >= self.max_units or time.monotonic() - self.started >= self.max_wall
                or any((p / 'YIELD_REQUEST.json').exists() for p in [self.root, *self.root.parents[:3]]))


def paused(phase, completed, total, **extra):
    return {'status': 'yielded', 'verified': False, 'phase': phase, 'completed': completed, 'total': total, **extra}


def fit_block(path, binding):
    if sealed.read(path.with_suffix('.sha256.json')) != {'binding': binding, 'sha256': io.sha(path)}:
        raise ValueError('Sealed TR1 numerical block changed')
    with np.load(path, allow_pickle=False) as archive:
        return {key: archive[key] for key in archive.files}


def build_projection(output, task, binding, clock):
    with np.load(task, allow_pickle=False) as archive:
        data = {key: archive[key] for key in ('plays', 'person', 'counter', 'day', 'repeat_eligible')}
    selected, compact, audit = roster(data)
    if audit['people'] < 20:
        return {'status': 'unsupported', 'reason': 'fewer than twenty repeat-person clusters', 'audit': audit}
    state_path = output / 'PROJECTION.json'
    state = sealed.state(state_path, binding, {'completed': 0, 'blocks': [], 'pilot_released': False})
    total = int(np.ceil(len(selected) / BLOCK)); pilot = max(1, int(np.ceil(total / 20)))
    for block in range(state['completed'], total):
        if clock.yield_requested():
            return paused('source_projection', block, total)
        sl = slice(block * BLOCK, (block + 1) * BLOCK); ii = selected[sl]
        x, y, total_luck = math.recent_luck(data['plays'][ii])
        path = output / 'projection' / f'{block:06d}.npz'
        values = {'x': x, 'y': y, 'person': compact[sl], 'counter': data['counter'][ii],
                  'day': data['day'][ii], 'total_luck': total_luck}
        if path.exists():
            old = fit_block(path, binding)
            if old.keys() != values.keys() or any(not np.array_equal(old[k], values[k], equal_nan=True) for k in old):
                raise ValueError('Existing complete play block differs')
        else:
            io.save_fit(path, binding, values)
        state['blocks'].append(path.relative_to(output).as_posix()); state['completed'] = block + 1
        sealed.checkpoint(state_path, state); clock.tick()
        io.write_json(output / 'PROGRESS.json', {'phase': 'source_projection', 'completed': block + 1, 'total': total})
        if block + 1 == pilot and not state['pilot_released']:
            state['pilot_released'] = True; sealed.checkpoint(state_path, state)
            return paused('source_cost_prefix', block + 1, total, first_fraction=.05,
                          cost_scope='projection only; controls, resampling and full independent replay remain')
    parts = [fit_block(output / name, binding) for name in state['blocks']]
    values = {key: np.concatenate([part[key] for part in parts]) for key in parts[0]}
    left, right = math.consecutive(values['person'], values['counter'])
    audit.update(consecutive_observed_pairs=len(left), missing_attempt_pairs=int(np.sum(values['counter'][right] - values['counter'][left] != 1)),
                 rating_count_per_play=12, total_rating_occasions=12 * len(selected),
                 negative_calendar_gap_pairs=int(np.sum(values['day'][right] < values['day'][left])))
    io.write_json(output / 'SUPPORT.json', audit)
    return values


def supported_pairs(data, table):
    left, right = math.consecutive(data['person'], data['counter'])
    good = table['valid'] & np.isfinite(table['half']).all(axis=(1, 2))
    supported = good[left] & good[right]
    return left[supported], right[supported], {'all_observed_pairs': len(left), 'unsupported_pairs': int((~supported).sum()),
            'people_in_supported_pairs': len(np.unique(data['person'][right[supported]])),
            'rule': 'both full and both six-rating half fits supported; no bridge over failed pairs'}


def planted_world(data, noise, target):
    """2000 whole real trial trajectories; unit input/noise scale, fixed dose."""
    people = np.unique(data['person'])
    rng = np.random.default_rng(np.random.SeedSequence([SEED, 71]))
    selected = rng.choice(people, 2000, replace=True)
    order = np.argsort(data['person'], kind='stable')
    starts = np.flatnonzero(np.r_[True, np.diff(data['person'][order]) != 0])
    groups = dict(zip(people, np.split(order, starts[1:])))
    xx, yy, pp, cc = [], [], [], []
    for synthetic, key in enumerate(selected):
        ii = groups[key]
        x = data['x'][ii]
        local = np.random.default_rng(np.random.SeedSequence([SEED, synthetic, 72]))
        innovations = local.normal(size=len(ii)); gains = np.empty(len(ii)); gains[0] = innovations[0]
        for j in range(1, len(ii)):
            gains[j] = target * gains[j - 1] + np.sqrt(1 - target ** 2) * innovations[j]
        gain_sd = noise['residual_sd'] / noise['within_play_luck_sd']
        level = 50 + 10 * local.normal()
        z = local.normal(size=x.shape); residual = np.empty_like(z); residual[:, 0] = z[:, 0]
        for j in range(1, x.shape[1]):
            residual[:, j] = noise['phi'] * residual[:, j - 1] + np.sqrt(1 - noise['phi'] ** 2) * z[:, j]
        y = level + gain_sd * gains[:, None] * x + noise['residual_sd'] * residual
        xx.append(x); yy.append(y); pp.extend([synthetic] * len(ii)); cc.extend(data['counter'][ii])
    world = {'x': np.concatenate(xx), 'y': np.concatenate(yy), 'person': np.asarray(pp), 'counter': np.asarray(cc)}
    matched = math.residual_noise(world['x'], world['y'])
    if matched['status'] != 'ok':
        return {method: {'status': 'unsupported', 'reason': 'constructed residual support failure'} for method in math.METHODS}
    table = math.play_table(world['x'], world['y'], matched['phi'])
    left, right, support = supported_pairs(world, table)
    result = {method: math.stability(table, left, right, np.ones(len(left)), method) for method in math.METHODS}
    result.update(target=target, synthetic_people=2000, support=support,
                  dose='one residual SD of response per pooled within-play luck SD; never tuned to recovered stability',
                  raw_gain_sd=gain_sd, phi_generated=noise['phi'], phi_estimated=matched['phi'],
                  clipped_ratings=False)
    return result


def summarize_draw(data, table, left, right, method, weights):
    pair_weights = weights[data['person'][right]]
    primary = math.stability(table, left, right, pair_weights, method)
    level = math.stability(table, left, right, pair_weights, method, column=0)
    scaled = math.stability(table, left, right, pair_weights, method, standardize=True)
    result = {'stability': primary.get('stability'), 'variance': primary.get('minimum_true_variance'),
              'primary_status': primary['status'], 'level_stability': level.get('stability'),
              'scaled_gain_stability': scaled.get('stability')}
    c = math.carryover(data['total_luck'], data['y'][:, 0], data['person'], left, right, weights)
    result['carryover'] = c['slope']
    gap = data['day'][right] - data['day'][left]
    for label, mask in (('gap_0_1', (gap >= 0) & (gap <= 1)), ('gap_1_7', (gap > 1) & (gap <= 7)), ('gap_over_7', gap > 7)):
        result[label] = math.carryover(data['total_luck'], data['y'][:, 0], data['person'], left, right, weights, mask)['slope']
    valid = table['valid']
    correlation = math.weighted_moments(table['coefficient'][valid, 0], table['coefficient'][valid, 1], weights[data['person'][valid]])
    result['level_gain_correlation'] = correlation[0] if correlation else None
    return result


def run(output, inputs, config):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    if set(config) - {'phase', 'draws', 'max_new_draws', 'max_wall_seconds'} or config.get('phase') != 'TR1' or config.get('draws', 2000) != 2000:
        raise ValueError('TR1 fixed semantic contract changed')
    task, identity = authenticate(inputs)
    binding = digest({'identity': identity, 'phase': 'TR1', 'draws': 2000, 'seed': SEED})
    clock = Budget(output, config)
    data = build_projection(output, task, binding, clock)
    if data.get('status') in ('yielded', 'unsupported'):
        if data['status'] == 'unsupported':
            io.write_json(output / 'RESULT.json', {'card': 'TR1', 'record_kind': 'run', 'theory_tags': ['H12-T7'],
                'by_construction': False, 'status': 'unsupported_source', 'source_support': data, 'human_inference': False})
        return data
    noise = math.residual_noise(data['x'], data['y']); io.write_json(output / 'NOISE.json', noise)
    if noise['status'] != 'ok':
        result = {'card': 'TR1', 'record_kind': 'run', 'theory_tags': ['H12-T7'], 'by_construction': False,
                  'status': 'estimator unqualified', 'noise': noise, 'human_inference': False}
        io.write_json(output / 'RESULT.json', result); return result
    control_path = output / 'CALIBRATION.json'
    control = sealed.state(control_path, binding, {'cases': {}})
    for target in (1., .5, 0.):
        key = str(target)
        if key in control['cases']:
            continue
        if clock.yield_requested():
            return paused('three_calibration_worlds', len(control['cases']), 3)
        control['cases'][key] = planted_world(data, noise, target)
        sealed.checkpoint(control_path, control); clock.tick()
        io.write_json(output / 'PROGRESS.json', {'phase': 'three_calibration_worlds', 'completed': len(control['cases']), 'total': 3})
    gate = math.choose_calibration(control['cases']); io.write_json(output / 'CALIBRATION_GATE.json', gate)
    if not gate['qualified']:
        result = {'card': 'TR1', 'record_kind': 'run', 'theory_tags': ['H12-T7'], 'by_construction': False,
                  'status': 'estimator unqualified', 'calibration': gate, 'human_inference': False}
        io.write_json(output / 'RESULT.json', result); return result
    table = math.play_table(data['x'], data['y'], noise['phi'])
    left, right, support = supported_pairs(data, table)
    if support['people_in_supported_pairs'] < 20:
        result = {'card': 'TR1', 'record_kind': 'run', 'theory_tags': ['H12-T7'], 'by_construction': False,
                  'status': 'unsupported_pair_population', 'support': support, 'human_inference': False}
        io.write_json(output / 'RESULT.json', result); return result
    method = gate['selected_method']; people = int(data['person'].max()) + 1
    point = summarize_draw(data, table, left, right, method, np.ones(people))
    state_path = output / 'BOOTSTRAP.json'
    state = sealed.state(state_path, binding, {'draws': [], 'cost_prefix_released': False})
    for draw in range(len(state['draws']), 2000):
        if clock.yield_requested():
            return paused('participant_bootstrap', draw, 2000)
        rng = np.random.default_rng(np.random.SeedSequence([SEED, draw, 73]))
        weights = np.bincount(rng.integers(0, people, people), minlength=people)
        draw_noise = math.residual_noise(data['x'], data['y'], weights[data['person']])
        if draw_noise['status'] != 'ok':
            draw_result = {'primary_status': 'unsupported_resampled_noise', 'reason': draw_noise['reason']}
        else:
            draw_table = math.play_table(data['x'], data['y'], draw_noise['phi'])
            draw_result = summarize_draw(data, draw_table, left, right, method, weights)
            draw_result['residual_phi'] = draw_noise['phi']
        state['draws'].append(draw_result)
        sealed.checkpoint(state_path, state); clock.tick()
        io.write_json(output / 'PROGRESS.json', {'phase': 'participant_bootstrap', 'completed': draw + 1, 'total': 2000})
        if draw + 1 == 100 and not state['cost_prefix_released']:
            state['cost_prefix_released'] = True; sealed.checkpoint(state_path, state)
            return paused('full_program_cost_prefix', 100, 2000, first_fraction=.05)
    variance = math.uncertainty(point['variance'], state['draws'], 'variance', 0.)
    primary = math.uncertainty(point['stability'], state['draws'], 'stability', .5)
    companions = {name: math.uncertainty(point[name], state['draws'], name, 0.) for name in
                  ('level_stability', 'scaled_gain_stability', 'carryover', 'gap_0_1', 'gap_1_7', 'gap_over_7', 'level_gain_correlation')}
    result = {'card': 'TR1', 'record_kind': 'claim', 'theory_tags': ['H12-T7'], 'by_construction': False,
              'complete_computation': True, 'human_inference': True, 'calibration': gate, 'support': support,
              'variance_gate': variance, 'primary': primary, 'secondary': companions,
              'outcome': math.decision(variance, primary, True),
              'primary_interpretable': variance.get('status') == 'ok' and variance['interval'][0] > 0,
              'variance_detection_floor_approximation': variance.get('sees'),
              'scope': 'consecutive observed completed plays, pair-weighted; participant-cluster uncertainty; conditional AR1 measurement model; unclipped ratios',
              'level_scope': 'rating-scale-use report, not a mood-trait identification',
              'failed_draw_policy': 'no redraws, clipping or finite-draw deletion', 'identity': identity}
    io.write_json(output / 'RESULT.json', result); return result


def execute(output, inputs, config):
    return run(output, inputs, config)


def verify(output, inputs, config):
    output = Path(output)
    result = run(output / 'independent-replay', inputs, config)
    if result.get('status') == 'yielded':
        return {**result, 'verified': False}
    if sealed.read(output / 'RESULT.json') != sealed.read(output / 'independent-replay/RESULT.json'):
        raise ValueError('TR1 complete aggregate independent replay differs')
    for name in ('SUPPORT.json', 'NOISE.json', 'CALIBRATION_GATE.json'):
        if (output / name).exists() and sealed.read(output / name) != sealed.read(output / 'independent-replay' / name):
            raise ValueError('TR1 source/control support replay differs')
    for name in ('CALIBRATION.json', 'BOOTSTRAP.json'):
        if (output / name).exists() and sealed.read(output / name) != sealed.read(output / 'independent-replay' / name):
            raise ValueError('TR1 complete retained worlds or draws differ')
    return {'verified': True, 'complete_source_controls_and_draw_replay': True, 'card': 'TR1'}
