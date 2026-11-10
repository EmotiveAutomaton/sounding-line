"""Authenticated GO3 feature-bank consumer with preserved folds and references.

DESIGN CHECK: complete bank and all-row habit scope are mandatory. Exact frozen
five-fold predictions, stochastic-prior baseline, whole-user bootstrap, roles,
fixed galleries and every conditional reassignment are retained. This module
changes checkpoint/storage boundaries, not the original scientific comparison.
"""
from collections import defaultdict
from pathlib import Path
import json
import math
import time
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from . import week5_go3_features_collected as features
from . import week5_go3_analysis as original
from .week5_la2_ic import requested

core = features.core
SOURCE = original.source
BANK_MODULE = 'runners.drive.cards.week5_go3_features_collected'


class Paused(Exception):
    pass


def checked_write(path, value):
    core.write(path, value)
    core.write(path.with_suffix(path.suffix + '.seal.json'), dict(sha256=core.sha(path)))


def checked_read(path, binding):
    if core.sha(path) != features.read(path.with_suffix(path.suffix + '.seal.json'))['sha256']:
        raise ValueError('Saved GO3 analysis checkpoint changed')
    value = features.read(path)
    if value['binding'] != binding:
        raise ValueError('Saved GO3 analysis binding differs')
    return value


def authenticate_bank(root, stop, expected_module=BANK_MODULE):
    root = Path(root).resolve()
    terminal = features.read(root / 'COMPLETE.json')
    if terminal.get('status') != 'COMPLETE' or terminal.get('fresh_process_verified') is not True:
        raise ValueError('Complete independently verified feature bank required')
    if any((root / name).exists() for name in ('FAILED.json', 'PAUSED.json')):
        raise ValueError('Ambiguous feature terminal')
    required = ('PLAN.json', 'VERIFIED.json', 'output/FEATURES.json', 'output/FEATURE_BINDING.json', 'output/STATE.json', 'output/STATE.seal.json')
    if any(name not in terminal['outputs'] for name in required):
        raise ValueError('Incomplete feature terminal manifest')
    for name, expected in sorted(terminal['outputs'].items()):
        if stop():
            raise Paused('complete feature-bank authentication boundary')
        if core.sha(features.safe_child(root, name)) != expected:
            raise ValueError('Complete feature-bank output changed')
    plan, verified = features.read(root / 'PLAN.json'), features.read(root / 'VERIFIED.json')
    if plan['module'] != expected_module:
        raise ValueError('Unreviewed feature-bank producer')
    if any(verified.get(key) is not True for key in ('verified', 'all_feature_rows_replayed',
                                                   'all_external_training_rows_and_model_replayed', 'all_source_rows_retained', 'no_stack_scientific_fit')):
        raise ValueError('Complete external model and feature replay required')
    bank = features.read(root / 'output/FEATURES.json')
    if any(bank.get(key) is not True for key in ('complete_features', 'all_source_rows_retained', 'feature_only')) or bank.get('scientific_admission') is not False:
        raise ValueError('Complete feature-only source scope required')
    binding = bank['binding']
    if (binding['feature_code_sha256'] != core.sha(features.__file__)
            or binding['analysis_sha256'] != core.sha(original.__file__)
            or binding['training_sha256'] != original.ITERATER_SHA
            or binding['batch_size'] != features.BATCH):
        raise ValueError('Frozen source feature or external training binding changed')
    if [info['site'] for info in binding['provenance']['sources']] != list(features.collection.SITES):
        raise ValueError('Feature bank site roster differs')
    if bank['rows_projected'] != sum(info['rows'] for info in binding['provenance']['sources']):
        raise ValueError('Feature bank full row accounting differs')
    state = features.open_state(root / 'output', binding)
    if state['blocks'] != bank['blocks'] or state['model'] != bank['model'] or state['training'] != bank['training_blocks']:
        raise ValueError('Feature final report and sealed bank disagree')
    index = 0
    raw_bytes = 0
    for info in binding['provenance']['sources']:
        first = 0
        while first < info['rows']:
            if index >= len(bank['blocks']):
                raise ValueError('Feature bank lacks source rows')
            block = bank['blocks'][index]
            size = min(features.BATCH, info['rows'] - first)
            if (block['site'], block['first_row'], block['rows'], block['path']) != (info['site'], first, size, f'blocks/{index:07d}.parquet'):
                raise ValueError('Whole feature-bank row order differs')
            name = 'output/' + block['path']
            if terminal['outputs'].get(name) != block['sha256']:
                raise ValueError('Feature block is absent from complete terminal')
            table = pq.ParquetFile(root / name)
            if table.metadata.num_rows != size:
                raise ValueError('Feature block row count differs')
            raw_bytes += sum(table.metadata.row_group(i).total_byte_size for i in range(table.metadata.num_row_groups))
            first += size
            index += 1
    if index != len(bank['blocks']) or not index:
        raise ValueError('Feature bank contains extra or no rows')
    return root, bank, raw_bytes


def load_frame(root, bank, stop):
    tables = []
    for block in bank['blocks']:
        if stop():
            raise Paused('whole-frame load boundary; reload complete frame on resume')
        table = pq.read_table(root / 'output' / block['path'])
        if features.table_digest(table) != block['content_sha256']:
            raise ValueError('Feature values differ from logical seal')
        tables.append(table)
    frame = pa.concat_tables(tables).to_pandas()
    if len(frame) != bank['rows_projected']:
        raise ValueError('Whole feature-bank population was not loaded')
    return frame


def cell_config(cell):
    matches = [row for row in original.grid() if row['cell'] == cell]
    if len(matches) != 1:
        raise ValueError('Cell is outside the declared GO3 grid')
    return matches[0]


def classify(output, frame, config, binding, stop):
    data = frame.loc[frame.type.isin([5, 24]) & frame.reason.isin(SOURCE.PRIMARY)].copy()
    if config.get('self_only'):
        data = data.loc[data.self_edit & data.owner_known]
    if config.get('site'):
        data = data.loc[data.site.eq(config['site'])]
    columns = [c for c in data if c.startswith('diff_') or (c.startswith('intent_') and not config.get('without_iterater'))]
    x, labels, users = data[columns].to_numpy(float), data.reason.to_numpy(), data.editor.to_numpy()
    if not np.isfinite(x).all():
        raise ValueError('Nonfinite classifier feature')
    keys, codes = np.unique(users, return_inverse=True)
    encoded = np.asarray([SOURCE.PRIMARY.index(value) for value in labels])
    assignment = {key: i % 5 for i, key in enumerate(np.random.default_rng(core.SEED).permutation(keys))}
    fold = np.asarray([assignment[value] for value in users])
    supported = len(keys) >= 20 and all(len(np.unique(encoded[fold != value])) == 5 for value in range(5))
    if not supported:
        path = output / 'fallback.json'
        if path.exists():
            return checked_read(path, binding)['result']
        if stop():
            raise Paused('before exact pooled descriptive fallback')
        result = original.classify(frame, config)
        checked_write(path, dict(binding=binding, result=result))
        return result
    model_counts = np.zeros((len(keys), 5, 5))
    prior_counts = np.zeros_like(model_counts)
    predicted = np.full(len(data), -1, int)
    priors = np.zeros((len(data), 5))
    for value in range(5):
        path = output / 'folds' / f'{value}.npz'
        seal = path.with_suffix('.seal.json')
        train, test = fold != value, fold == value
        indices = np.flatnonzero(test)
        if path.exists():
            meta = checked_read(seal, binding)
            if core.sha(path) != meta['sha256']:
                raise ValueError('Saved GO3 fold changed')
            saved = features.load_arrays(path)
            if not np.array_equal(saved['indices'], indices):
                raise ValueError('Saved GO3 held-out fold allocation differs')
        else:
            if stop():
                raise Paused('before complete editor-disjoint fold')
            model = original.make_pipeline(original.StandardScaler(), original.LogisticRegression(C=1., max_iter=1000, solver='lbfgs', random_state=core.SEED))
            model.fit(x[train], encoded[train])
            saved = dict(indices=indices, prediction=model.predict(x[test]),
                         prior=np.bincount(encoded[train], minlength=5) / train.sum(), **features.model_arrays(model))
            path.parent.mkdir(parents=True, exist_ok=True)
            np.savez(path, **saved)
            checked_write(seal, dict(binding=binding, sha256=core.sha(path)))
        predicted[test] = saved['prediction']
        priors[test] = saved['prior']
    for i in range(len(data)):
        model_counts[codes[i], encoded[i], predicted[i]] += 1
        prior_counts[codes[i], encoded[i]] += priors[i]
    path = output / 'bootstrap.json'
    saved = checked_read(path, binding) if path.exists() else dict(binding=binding, draws=[], pilot_done=False)
    values = saved['draws']
    count, draws = len(keys), config['draws']
    if len(values) > draws:
        raise ValueError('Extra saved classifier draws')
    rng = np.random.default_rng(core.SEED)
    for draw in range(draws):
        weights = np.bincount(rng.integers(0, count, count), minlength=count)
        if draw < len(values):
            continue
        if stop():
            checked_write(path, saved)
            raise Paused('complete classifier draw boundary')
        values.append(SOURCE.macro_f1(np.einsum('n,nij->ij', weights, model_counts)) - SOURCE.macro_f1(np.einsum('n,nij->ij', weights, prior_counts)))
        pilot = not saved['pilot_done'] and len(values) >= math.ceil(.05 * draws)
        if pilot:
            saved['pilot_done'] = True
        if len(values) % 20 == 0 or len(values) == draws or pilot:
            checked_write(path, saved)
            core.write(output / 'PROGRESS.json', dict(phase='classifier_bootstrap', completed=len(values), total=draws))
        if pilot and len(values) < draws:
            raise Paused('first five percent of complete classifier resamples')
    observed = SOURCE.macro_f1(model_counts.sum(axis=0)) - SOURCE.macro_f1(prior_counts.sum(axis=0))
    interval = np.quantile(values, [.025, .975]).tolist()
    lo, hi = interval
    return dict(users=count, edits=len(encoded), macro_f1=SOURCE.macro_f1(model_counts.sum(axis=0)),
                prior_only_expected_macro_f1=SOURCE.macro_f1(prior_counts.sum(axis=0)), gain=observed, interval=interval,
                draws=draws, outcome='supports' if lo > .05 else 'against' if hi < 0 or (lo >= -.05 and hi <= .05) else 'inconclusive',
                baseline='expected confusion of stochastic training-prior predictions, not majority class',
                status='ok', feature_columns=columns, folds=5)


def habits(output, frame, binding, stop):
    data = frame[['editor', 'post', 'site', 'stamp', 'reason']].copy()
    data['row'] = np.arange(len(data))
    rows = data.to_dict('records')
    profiles = original.habit_profiles(rows)
    eligible = sorted(profiles)
    folds = {str(w): i % 3 for i, w in enumerate(np.random.default_rng(core.SEED).permutation(eligible))}
    rows = [row for row in rows if row['editor'] in folds]
    rosters = {}
    rng = np.random.default_rng(core.SEED + 1)
    for role in range(3):
        gallery = [w for w in eligible if folds[w] != role]
        probes = [w for w in eligible if folds[w] == (role + 1) % 3]
        if len(gallery) < 30:
            return dict(status='unsupported', reason='fewer than thirty fixed non-donor gallery users', eligible_users=len(eligible))
        rosters[role] = {w: [w] + rng.choice([g for g in gallery if g != w], 29, replace=False).tolist() for w in probes}
    result = original.habit_accuracy(rows, folds, rosters)
    if result is None:
        return dict(status='unsupported', reason='fixed galleries lack independent same-post donor support', eligible_users=len(eligible))
    real, context = result
    keys = sorted(real)
    a, b = np.asarray([real[key] for key in keys]), np.asarray([context[key] for key in keys])
    groups = defaultdict(list)
    for row in rows:
        groups[(row['site'], row['post'], folds[row['editor']])].append(row)
    path = output / 'permutations.json'
    state = checked_read(path, binding) if path.exists() else dict(binding=binding, null=[], pilot_done=False)
    if 'failure' in state:
        return state['failure']
    values = state['null']
    if len(values) > 1000:
        raise ValueError('Extra saved conditional reference draws')
    for index in range(len(values), 1000):
        if stop():
            checked_write(path, state)
            raise Paused('complete fixed-gallery reassignment boundary')
        rng = np.random.default_rng(np.random.SeedSequence([core.SEED, index, 91]))
        assignment = {}
        for group in groups.values():
            for row, user in zip(group, rng.permutation([r['editor'] for r in group])):
                assignment[row['row']] = user
        value = original.habit_accuracy(rows, folds, rosters, assignment)
        if value is None:
            state['failure'] = dict(status='unsupported', reason='fixed gallery support lost under conditional reassignment', draw=index, eligible_users=len(eligible))
            checked_write(path, state)
            return state['failure']
        values.append(float(np.mean(list(value[0].values()))))
        pilot = not state['pilot_done'] and len(values) >= 50
        if pilot:
            state['pilot_done'] = True
        if len(values) % 10 == 0 or len(values) == 1000 or pilot:
            checked_write(path, state)
            core.write(output / 'PROGRESS.json', dict(phase='habit_conditional_reference', completed=len(values), total=1000))
        if pilot:
            raise Paused('first five percent of fixed-gallery conditional references')
    path = output / 'bootstrap.json'
    state = checked_read(path, binding) if path.exists() else dict(binding=binding, draws=[])
    boot = state['draws']
    if len(boot) > 2000:
        raise ValueError('Extra saved paired habit resamples')
    rng = np.random.default_rng(core.SEED + 2)
    for draw in range(2000):
        indices = rng.integers(0, len(a), len(a))
        if draw < len(boot):
            continue
        if stop():
            checked_write(path, state)
            raise Paused('whole-user paired habit resample boundary')
        boot.append(float(np.mean((a - b)[indices])))
        if len(boot) % 100 == 0 or len(boot) == 2000:
            checked_write(path, state)
    ci = np.quantile(boot, [.025, .975]).tolist()
    p = float((1 + sum(value >= a.mean() - 1e-12 for value in values)) / 1001)
    return dict(status='ok', users=len(keys), gallery=30, real_accuracy=float(a.mean()), context_accuracy=float(b.mean()),
                difference_interval=ci, conditional_reassignments=1000, one_sided_p=p, paired_draws=2000,
                passes=bool(p < .05 and ci[0] > 0), context='same-post independent donors; all fixed gallery support required')


def run_frame(output, frame, config, binding, stop):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    result = classify(output / 'classifier', frame, config, binding, stop)
    if config['cell'] == 'GO3':
        result['habit_companion'] = habits(output / 'habits', frame, binding, stop)
    result.update(card='GO3', scope='comment-stated editing reason categories; retrospective and descriptive')
    core.write(output / 'RESULT.json', result)
    return result


def progress_counts(output, specification):
    completed = len(list((output / 'classifier/folds').glob('*.npz')))
    for path, key in ((output / 'classifier/bootstrap.json', 'draws'),
                      (output / 'habits/permutations.json', 'null'),
                      (output / 'habits/bootstrap.json', 'draws')):
        if path.exists():
            completed += len(features.read(path)[key])
    total = 5 + specification['draws'] + (3000 if specification['cell'] == 'GO3' else 0)
    return completed, total


def run(output, inputs, config, expected_module=BANK_MODULE):
    if set(inputs) != {'feature_run'} or set(config) - {'phase', 'cell', 'max_wall_seconds', 'max_frame_GiB'}:
        raise ValueError('Exact complete-bank scientific contract required')
    if config.get('phase') != 'GO3':
        raise ValueError('Declared GO3 phase required')
    specification = cell_config(config['cell'])
    maximum = float(config.get('max_wall_seconds', 900))
    memory = float(config.get('max_frame_GiB', 3))
    if any(not math.isfinite(value) or value <= 0 for value in (maximum, memory)):
        raise ValueError('Positive finite wall and frame envelopes required')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    began = time.monotonic()
    stop = lambda: requested(output) or time.monotonic() - began >= maximum
    early = dict(feature_root=str(Path(inputs['feature_run']).resolve()),
                 feature_complete_sha256=core.sha(Path(inputs['feature_run']) / 'COMPLETE.json'),
                 consumer_sha256=core.sha(__file__), specification=specification, max_frame_GiB=memory)
    if (output / 'ANALYSIS_BINDING.json').exists() and features.read(output / 'ANALYSIS_BINDING.json') != early:
        raise ValueError('GO3 scientific binding changed')
    core.write(output / 'ANALYSIS_BINDING.json', early)
    try:
        root, bank, raw_bytes = authenticate_bank(inputs['feature_run'], stop, expected_module)
        # This is a conservative planning check, not a measured peak-RAM claim.
        estimate = 4 * raw_bytes
        core.write(output / 'FRAME_COST.json', dict(parquet_uncompressed_bytes=raw_bytes,
                   projected_frame_bytes=estimate, multiplier=4, measured_peak=False, rows=bank['rows_projected']))
        if estimate > memory * 1024 ** 3:
            return dict(status='yielded', phase='frame_memory_scope_gate', completed=0, total=bank['rows_projected'],
                        reason='full-frame estimate exceeds frozen envelope; owner must freeze an adequate envelope or whole-editor sample before a new semantic plan',
                        no_scientific_fit=True)
        frame = load_frame(root, bank, stop)
        binding = features.digest(early | dict(feature_report_sha256=core.sha(root / 'output/FEATURES.json'),
                                               original_analysis_sha256=core.sha(original.__file__),
                                               source_analysis_sha256=core.sha(SOURCE.__file__)))
        return run_frame(output, frame, specification, binding, stop)
    except Paused as pause:
        completed, total = progress_counts(output, specification)
        return dict(status='yielded', phase='complete_bank_analysis', reason=str(pause), complete_card=False,
                    completed=completed, total=total)


def execute(output, inputs, config):
    return run(output, inputs, config)


def verify_run(output, inputs, config, expected_module=BANK_MODULE):
    output = Path(output)
    actual = run(output / 'independent-replay', inputs, config, expected_module)
    if actual.get('status') == 'yielded':
        return actual | dict(verified=False)
    if actual != features.read(output / 'RESULT.json'):
        raise ValueError('Complete GO3 primary/grid/reference result differs')
    # Summary parity is insufficient: compare every saved model, allocation and draw.
    for area in ('classifier', 'habits'):
        left, right = output / area, output / 'independent-replay' / area
        names = sorted(path.relative_to(left).as_posix() for path in left.rglob('*') if path.is_file() and not path.name.endswith('.seal.json') and path.name != 'PROGRESS.json')
        other = sorted(path.relative_to(right).as_posix() for path in right.rglob('*') if path.is_file() and not path.name.endswith('.seal.json') and path.name != 'PROGRESS.json')
        if names != other:
            raise ValueError('Incomplete GO3 saved reference/fold replay')
        for name in names:
            if name.endswith('.npz'):
                a, b = features.load_arrays(left / name), features.load_arrays(right / name)
                if set(a) != set(b) or any(not np.array_equal(a[key], b[key]) for key in a):
                    raise ValueError('Every fitted model and held-out prediction must replay')
            elif features.read(left / name) != features.read(right / name):
                raise ValueError('Every complete null and user-resample draw must replay')
    return dict(verified=True, complete_replay=True, complete_models_predictions_and_reference_banks_replayed=True,
                complete_feature_bank_authenticated=True, all_row_habit_scope_preserved=True)


def verify(output, inputs, config):
    return verify_run(output, inputs, config)
