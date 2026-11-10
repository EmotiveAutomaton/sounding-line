"""Immutable MD3.s/.m/.p descendants with complete dynamic-null calibration.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 6-7. Every signed/full-null control,
all 2,000 participant draws, support failures and independent replay are
required. Partial checkpoints carry no scientific verdict. Not qualified.
"""
from pathlib import Path
import hashlib
import json
import math
import os
import time
for _key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_key] = '2'
import numpy as np
from scipy.special import expit
from . import week5_md as core
from . import week5_md_analysis as original
from . import week5_md3_conditional as conditional
from .week5_md12_bounded import atomic_replace, YieldRequested

CARDS = ('MD3.s', 'MD3.m', 'MD3.p')
GAMMAS = (.25, .50, .75)
DRAW_COUNT = 2000
NULL_COUNT = 20
PILOT_DRAWS = 100
SEED = 20261107


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text('utf8'))


def dependencies():
    return {Path(module.__file__).name: core.sha(module.__file__)
            for module in (core, original, conditional)} | {Path(__file__).name: core.sha(__file__)}


def authenticate_parent(root, task):
    root = Path(root).resolve()
    terminal = read(root / 'COMPLETE.json')
    if terminal.get('status') != 'COMPLETE' or terminal.get('fresh_process_verified') is not True:
        raise ValueError('Complete independently verified MD3 dependency required')
    for name, expected in terminal['outputs'].items():
        path = (root / name).resolve()
        path.relative_to(root)
        if core.sha(path) != expected:
            raise ValueError('MD3 dependency output changed')
    plan = read(root / 'PLAN.json')
    if core.sha(plan['inputs']['task']) != core.sha(task):
        raise ValueError('Descendant source differs from parent source')
    result = read(root / 'output/RESULT.json')
    if result.get('card') != 'MD3' or not result.get('complete_computation'):
        raise ValueError('Complete MD3 computation required')
    if read(root / 'VERIFIED.json').get('verified') is not True:
        raise ValueError('Parent explicit verification required')
    primary = result['primary']
    if primary['gamma'] != .65:
        raise ValueError('Frozen parent discount changed')
    return result, core.sha(root / 'COMPLETE.json')


def features(plays, gamma, scale, curved=False):
    value = original.dynamic_features(plays, gamma) / scale
    if curved:
        state = value[:, :, 3] + value[:, :, 4]
        value = np.concatenate([value, state[:, :, None] ** 2], axis=2)
    return value


def fixed_fit(x, y, weights=None, check=None):
    """Parent fixed-intercept IRLS, with cooperative iteration boundaries.

    Arithmetic, rank threshold and convergence tolerance are preserved. This
    separately implemented copy must match original.logistic_fixed natively.
    """
    n, trials, columns = x.shape
    weights = np.ones(n) if weights is None else np.asarray(weights, float)
    if weights.shape != (n,) or np.any(weights < 0) or not np.isfinite(weights).all():
        raise ValueError('Invalid participant weights')
    use = (y.sum(axis=1) > 0) & (y.sum(axis=1) < trials) & (weights > 0)
    xx, yy, ww = x[use], y[use], weights[use]
    if len(xx) < 2:
        raise ValueError('Fewer than two informative participants')
    alpha = np.log((yy.sum(axis=1) + .5) / (trials - yy.sum(axis=1) + .5))
    beta = np.zeros(columns)
    objective = np.inf
    for iteration in range(100):
        if check is not None:
            check()
        eta = alpha[:, None] + np.einsum('nti,i->nt', xx, beta)
        probability = expit(eta)
        variance = (probability * (1 - probability)).clip(1e-9)
        working = eta + (yy - probability) / variance
        total = variance.sum(axis=1)
        xm = np.einsum('nt,nti->ni', variance, xx) / total[:, None]
        zm = np.sum(variance * working, axis=1) / total
        centered, zc = xx - xm[:, None, :], working - zm[:, None]
        gram = np.einsum('n,nt,nti,ntj->ij', ww, variance, centered, centered, optimize=True)
        rhs = np.einsum('n,nt,nti,nt->i', ww, variance, centered, zc, optimize=True)
        if np.linalg.matrix_rank(gram, tol=1e-8) < columns:
            raise ValueError('Fixed-effect logistic rank deficient')
        new_beta = np.linalg.solve(gram, rhs)
        new_alpha = zm - xm @ new_beta
        step = 1.
        while step > 1e-8:
            b, a = beta + step * (new_beta - beta), alpha + step * (new_alpha - alpha)
            linear = a[:, None] + np.einsum('nti,i->nt', xx, b)
            loss = float(np.sum(ww[:, None] * (np.logaddexp(0, linear) - yy * linear)))
            if loss <= objective + 1e-8:
                break
            step *= .5
        beta, alpha, objective = b, a, loss
        residual = yy - expit(linear)
        gradient = np.einsum('n,nti,nt->i', ww, xx, residual, optimize=True)
        gap = float(np.max(np.abs(gradient)) / max(1, ww.sum()))
        if max(gap, np.max(np.abs(np.sum(residual, axis=1)))) < 1e-6:
            all_alpha = np.full(n, np.nan)
            all_alpha[use] = alpha
            return dict(beta=beta, alpha=all_alpha, informative=use,
                        gradient=gap, iterations=iteration + 1)
    raise ValueError('Fixed-effect logistic gradient tolerance not reached')


def smooth_null_fit(x, y, check=None):
    if x.shape[-1] != 9:
        raise ValueError('Curved standing design required')
    transform = np.zeros((9, 8))
    for destination, source in enumerate((0, 1, 2, 3, 5, 6, 7, 8)):
        transform[source, destination] = 1.
    transform[4, 3] = 1.
    fit = fixed_fit(x @ transform, y, check=check)
    fit['beta'] = transform @ fit['beta']
    return fit


def trajectory(plays, gamma, fit, scale, seed, curved=False, zero_standing=False, check=None):
    """Regenerate choices AND every downstream choice/outcome-dependent history."""
    rng = np.random.default_rng(seed)
    out = plays.copy()
    n = len(plays)
    standing, prior, recent = np.zeros(n), np.zeros(n), np.zeros(n)
    beta = np.asarray(fit['beta'], float).copy()
    if zero_standing:
        beta[3:5] = 0.
    alpha = fit['alpha']
    valid = np.isfinite(alpha)
    fixed_choice = (plays[:, :, 6].mean(axis=1) > .5).astype(float)
    for trial in range(30):
        if check is not None:
            check()
        row = out[:, trial]
        raw = np.column_stack([row[:, 2] > 0, row[:, 2] < 0,
                               (row[:, 3] + row[:, 4]) / 2 - row[:, 2],
                               np.minimum(standing, 0), np.maximum(standing, 0),
                               prior, np.full(n, trial), recent]) / scale
        if curved:
            raw = np.column_stack([raw, (standing / scale[3]) ** 2])
        probability = expit(alpha[valid] + raw[valid] @ beta)
        choice = fixed_choice.copy()
        choice[valid] = (rng.random(valid.sum()) < probability).astype(float)
        coin = rng.random(n) < .5
        outcome = np.where(choice, np.where(coin, row[:, 3], row[:, 4]), row[:, 2])
        out[:, trial, 6], out[:, trial, 7] = choice, outcome
        standing += outcome
        prior += choice
        recent = gamma * recent + outcome
    return out


def support(plays, gamma):
    raw = original.dynamic_features(plays, gamma)
    state = raw[:, :, 3] + raw[:, :, 4]
    both = (state.min(axis=1) < 0) & (state.max(axis=1) > 0)
    rescue = (state < 0) & (state + plays[:, :, 3] >= 0) & (state + plays[:, :, 2] < 0)
    return dict(both_sides_participants=int(both.sum()), rescue_choices=int(rescue.sum()),
                participant_clusters=len(plays))


def vector(fit):
    beta = fit['beta']
    result = [float(beta[3]), float(beta[4]), float(beta[3] - beta[4])]
    if len(beta) == 9:
        result.append(float(beta[8]))
    return result


def classify(interval, threshold, case_counts):
    if case_counts['both_sides_participants'] < 10000 or case_counts['rescue_choices'] < 10000:
        return 'below floor, descriptive'
    lo, hi = interval
    return 'supports' if lo > threshold else 'against' if hi < -threshold else 'inconclusive'


class RunClock:
    def __init__(self, output, config):
        self.start = time.monotonic()
        self.maximum = float(config.get('max_wall_seconds', 900))
        self.draw_limit = int(config.get('max_new_draws', DRAW_COUNT * 3))
        if not math.isfinite(self.maximum) or self.maximum <= 0 or self.draw_limit <= 0:
            raise ValueError('Positive bounded operating quantum required')
        self.output = Path(output)
        self.completed = 0
        self.phase = 'setup'
        self.total = 1

    def check(self):
        if any((parent / 'YIELD_REQUEST.json').exists() for parent in (self.output, *list(self.output.parents)[:2])) or time.monotonic() - self.start >= self.maximum:
            raise YieldRequested(dict(status='yielded', complete_card=False,
                                      phase=self.phase, completed=self.completed, total=self.total,
                                      reason='bounded MD3 descendant checkpoint'))


def save_record(path, binding, value):
    core.save_json(path, dict(binding=binding, value=value))
    core.save_json(path.with_suffix('.sha256.json'), dict(sha256=core.sha(path)))


def load_record(path, binding):
    if not path.exists():
        if path.with_suffix('.sha256.json').exists():
            raise ValueError('Orphan MD3 descendant checkpoint seal')
        return None
    if core.sha(path) != read(path.with_suffix('.sha256.json'))['sha256']:
        raise ValueError('MD3 descendant checkpoint hash changed')
    saved = read(path)
    if saved['binding'] != binding:
        raise ValueError('MD3 descendant checkpoint binding changed')
    return saved['value']


def save_fit(path, binding, fit):
    arrays = {key: np.asarray(value) for key, value in fit.items()}
    temp = path.with_suffix('.tmp.npz')
    np.savez_compressed(temp, **arrays)
    atomic_replace(temp, path)
    core.save_json(path.with_suffix('.sha256.json'), dict(binding=binding, sha256=core.sha(path)))


def load_fit(path, binding):
    if not path.exists():
        return None
    seal = read(path.with_suffix('.sha256.json'))
    if seal['binding'] != binding or core.sha(path) != seal['sha256']:
        raise ValueError('MD3 descendant fit seal changed')
    with np.load(path, allow_pickle=False) as data:
        return {key: data[key] for key in data.files}


def get_fit(path, binding, fit_function):
    value = load_fit(path, binding)
    if value is None:
        value = fit_function()
        save_fit(path, binding, value)
    return value


def safe_fit(function):
    try:
        result = function()
        return dict(status='ok', values=vector(result), gradient=float(result['gradient']),
                    informative_participants=int(np.asarray(result['informative']).sum()))
    except ValueError as error:
        return dict(status='fit_failure', reason=str(error))


def cell_setup(output, plays, gamma, scale, card, binding, clock):
    output.mkdir(parents=True, exist_ok=True)
    curved = card == 'MD3.m'
    x = features(plays, gamma, scale, curved)
    y = plays[:, :, 6]
    fitter = conditional.fit if card == 'MD3.p' else fixed_fit
    clock.phase = 'point_fit'
    clock.check()
    point = get_fit(output / 'POINT.npz', binding, lambda: fitter(x, y, check=clock.check))
    null_fit = point
    if card == 'MD3.m':
        null_fit = get_fit(output / 'NULL_FIT.npz', binding, lambda: smooth_null_fit(x, y, clock.check))
    elif card == 'MD3.p':
        null_fit = get_fit(output / 'NULL_FIT.npz', binding, lambda: fixed_fit(x, y, check=clock.check))
    namespace = 303 if curved else 33
    nulls = []
    for index in range(NULL_COUNT):
        clock.phase, clock.completed, clock.total = 'dynamic_nulls', index, NULL_COUNT
        clock.check()
        path = output / f'null-{index:02d}.json'
        saved = load_record(path, binding)
        if saved is None:
            simulated = trajectory(plays, gamma, null_fit, scale, np.random.SeedSequence([SEED, index, namespace]),
                                   curved=curved, zero_standing=not curved, check=clock.check)
            xx = features(simulated, gamma, scale, curved)
            saved = safe_fit(lambda: fitter(xx, simulated[:, :, 6], check=clock.check))
            saved['trajectory_sha256'] = hashlib.sha256(np.ascontiguousarray(simulated).tobytes()).hexdigest()
            save_record(path, binding, saved)
        nulls.append(saved)
        core.save_json(output / 'PROGRESS.json', dict(phase='dynamic_nulls', completed=index + 1, total=NULL_COUNT))
    return dict(output=output, x=x, y=y, fit=point, nulls=nulls, binding=binding,
                gamma=gamma, scale=scale, fitter=fitter, curved=curved)


def draws_completed(cell):
    return sum((cell['output'] / f'draw-{index:04d}.json').exists() for index in range(DRAW_COUNT))


def draw_stage(cells, target, clock):
    new = 0
    total = DRAW_COUNT * len(cells)
    completed = sum(draws_completed(c) for c in cells)
    for cell in cells:
        for index in range(target):
            path = cell['output'] / f'draw-{index:04d}.json'
            saved = load_record(path, cell['binding'])
            if saved is not None:
                continue
            clock.phase, clock.total = 'participant_bootstrap', total
            clock.completed = completed
            clock.check()
            rng = np.random.default_rng(np.random.SeedSequence([SEED, index, 304 if cell['curved'] else 34]))
            n = len(cell['y'])
            weights = np.bincount(rng.integers(0, n, n), minlength=n)
            saved = safe_fit(lambda: cell['fitter'](cell['x'], cell['y'], weights, check=clock.check))
            save_record(path, cell['binding'], saved)
            new += 1
            completed += 1
            clock.completed = completed
            core.save_json(clock.output / 'PROGRESS.json', dict(phase=clock.phase, completed=clock.completed, total=total))
            if new >= clock.draw_limit and clock.completed < total:
                raise YieldRequested(dict(status='yielded', complete_card=False, phase=clock.phase,
                                          completed=clock.completed, total=total, reason='draw operating quantum'))


def cell_result(cell, card, counts):
    draws = [load_record(cell['output'] / f'draw-{index:04d}.json', cell['binding']) for index in range(DRAW_COUNT)]
    if any(value is None for value in draws):
        raise ValueError('Incomplete MD3 descendant draw bank')
    failed_draws = [i for i, value in enumerate(draws) if value['status'] != 'ok']
    failed_nulls = [i for i, value in enumerate(cell['nulls']) if value['status'] != 'ok']
    base = dict(gamma=cell['gamma'], draws=DRAW_COUNT, nulls=NULL_COUNT, support=counts,
                point=vector(cell['fit']), informative_participants=int(cell['fit']['informative'].sum()),
                failed_draws=failed_draws, failed_nulls=failed_nulls)
    if failed_draws or failed_nulls:
        return base | dict(status='invalid', reason='Full draw or null bank contains failed fits')
    values = np.asarray([value['values'] for value in draws])
    contrast = 2 if card == 'MD3.m' else 0
    null_values = np.asarray([value['values'][contrast] for value in cell['nulls']])
    threshold = max(.01, 2 * float(np.mean(np.abs(null_values))) + 3 * float(np.std(null_values, ddof=1)))
    intervals = np.quantile(values, [.025, .975], axis=0).T.tolist()
    return base | dict(status='ok', intervals_lower_upper_contrast_quadratic=intervals,
                       dynamic_null_primary_values=null_values.tolist(), threshold=threshold,
                       outcome=classify(intervals[contrast], threshold, counts),
                       diagnostic_direction=classify(intervals[contrast], threshold,
                                                     dict(both_sides_participants=10000, rescue_choices=10000)))


def perform(output, plays, parent_primary, card, config, source_binding, constructed=False):
    """Shared complete numerical handler. Public execute authenticates its sources."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    if card not in CARDS or int(config.get('draws', DRAW_COUNT)) != DRAW_COUNT:
        raise ValueError('Registered MD3 descendant and full uncertainty required')
    plays = np.asarray(plays)
    if plays.ndim != 3 or plays.shape[1:] != (30, 15):
        raise ValueError('Complete 30-trial first plays required')
    if not np.isfinite(plays[:, :, [2, 3, 4, 6, 7]]).all() or not np.isin(plays[:, :, 6], (0, 1)).all():
        raise ValueError('Invalid numerical MD3 task panel')
    # The parent common standing scale is held fixed, also on an admitted sample.
    standing_sd = float(parent_primary['standing_sd'])
    if not math.isfinite(standing_sd) or standing_sd <= 0:
        raise ValueError('Finite positive parent standing scale required')
    semantic = {key: value for key, value in config.items() if key not in ('max_wall_seconds', 'max_new_draws')}
    base_binding = digest(dict(card=card, source=source_binding, semantic=semantic, code=dependencies(),
                               standing_sd=standing_sd, panel_sha256=hashlib.sha256(plays.tobytes()).hexdigest()))
    clock = RunClock(output, config)
    gammas = GAMMAS if card == 'MD3.s' else (.65,)
    counts = support(plays, .65)
    cells = []
    try:
        for gamma in gammas:
            scale = original.dynamic_features(plays, gamma).reshape(-1, 8).std(axis=0, ddof=1).clip(1e-10)
            scale[3:5] = standing_sd
            binding = digest(dict(base=base_binding, gamma=gamma, scale=scale.tolist()))
            directory = output / f'gamma-{gamma:.2f}'
            try:
                cells.append(cell_setup(directory, plays, gamma, scale, card, binding, clock))
            except ValueError as error:
                if any(word in str(error).lower() for word in ('checkpoint', 'seal', 'binding', 'changed', 'orphan')):
                    raise
                failure = dict(card=card, status='unsupported' if 'rank deficient' in str(error) or 'informative' in str(error) else 'invalid',
                               phase='point_or_null_fit', reason=str(error), gamma=gamma, support=counts,
                               complete_card=True, no_directional_claim=True,
                               uncomputed_cells=[g for g in gammas if g != gamma],
                               outcome='No full specification claim; point-fit failure retained')
                core.save_json(output / 'RESULT.json', failure)
                return failure
        pilot = load_record(output / 'PILOT.json', base_binding)
        if pilot is None:
            draw_stage(cells, PILOT_DRAWS, clock)
            save_record(output / 'PILOT.json', base_binding, dict(per_cell=PILOT_DRAWS, cells=len(cells)))
            return dict(status='yielded', complete_card=False, phase='participant_bootstrap',
                        completed=PILOT_DRAWS * len(cells), total=DRAW_COUNT * len(cells), reason='first five percent draw pilot')
        draw_stage(cells, DRAW_COUNT, clock)
    except YieldRequested as request:
        return request.receipt
    result = dict(card=card, status='complete', complete_card=True, constructed_only=constructed,
                  cells=[cell_result(cell, card, counts) for cell in cells], parent_gamma=.65,
                  standing_sd=standing_sd, draws=DRAW_COUNT, dynamic_nulls_per_cell=NULL_COUNT,
                  source_binding=source_binding, specification_gammas=list(gammas),
                  scope='First-play game-score reference, observational dynamic panel; descendant of the preserved MD3 primary')
    if card == 'MD3.p':
        result['limitation'] = 'Count-conditioned fixed-design objective on choice-dependent predictors; no consistency or causal claim'
    core.save_json(output / 'RESULT.json', result)
    return result


def execute(output, inputs, config):
    allowed = {'phase', 'draws', 'participants', 'max_new_draws', 'max_wall_seconds'}
    if set(config) - allowed or set(inputs) != {'task', 'parent_run'}:
        raise ValueError('Exact MD3 descendant inputs/config required')
    card = config.get('phase')
    parent, parent_sha = authenticate_parent(inputs['parent_run'], inputs['task'])
    data = original.load_verified(inputs['task'])
    plays = data['first']
    if len(plays) != parent['primary']['analysed_first_plays']:
        raise ValueError('Parent first-play roster scope differs')
    source_n = len(plays)
    if 'participants' in config:
        count = int(config['participants'])
        if count < 2 or count > source_n:
            raise ValueError('Invalid prospective whole-person sample size')
        order = np.random.default_rng(SEED).permutation(source_n)
        plays = plays[np.sort(order[:count])]
    source_binding = dict(task_sha256=core.sha(inputs['task']), parent_complete_sha256=parent_sha,
                          source_first_plays=source_n, analysed_first_plays=len(plays))
    return perform(output, plays, parent['primary'], card, config, source_binding)


def compare_complete(output):
    output = Path(output)
    replay = output / 'independent-replay'
    if read(output / 'RESULT.json') != read(replay / 'RESULT.json'):
        raise ValueError('Complete MD3 descendant summary differs')
    original_files = [path for path in output.rglob('*') if path.is_file() and replay not in path.parents]
    for path in original_files:
        if path.name.startswith(('draw-', 'null-')) and not path.name.endswith('.sha256.json'):
            if read(path) != read(replay / path.relative_to(output)):
                raise ValueError('Full MD3 descendant fit bank differs')
        elif path.name in ('POINT.npz', 'NULL_FIT.npz'):
            with np.load(path, allow_pickle=False) as left, np.load(replay / path.relative_to(output), allow_pickle=False) as right:
                if set(left.files) != set(right.files):
                    raise ValueError('MD3 fit output keys differ')
                for key in left.files:
                    if not np.array_equal(left[key], right[key], equal_nan=True):
                        raise ValueError('MD3 complete numerical fit differs')


def verify(output, inputs, config):
    output = Path(output)
    value = execute(output / 'independent-replay', inputs, config)
    if value.get('status') == 'yielded':
        return value | dict(verified=False)
    compare_complete(output)
    return dict(verified=True, all_draws_nulls_and_full_fits_replayed=True)
