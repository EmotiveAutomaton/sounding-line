"""Collector-bound, complete-row GO3 diff and released-intent feature bank.

DESIGN CHECK: LESSONS 2-5. Authenticate the complete five-site source collector
before reading text. Retain all source rows for the original habit companion;
comment labels never enter features. Exact original feature/model parity and
complete fresh replay are required. This stage computes no Stack outcome fit.
"""
from pathlib import Path
from collections import Counter
import hashlib
import json
import math
import time
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import sklearn
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from . import week5_go3_collection as collection
from . import week5_go3_analysis as analysis
from .week5_la2_ic import requested

core = collection.core
BATCH = 512
COLLECTOR_MODULE = 'runners.drive.cards.week5_go3_collection'


class Paused(Exception):
    pass


def read(path):
    return json.loads(Path(path).read_text('utf8'))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def safe_child(root, name):
    path = Path(root) / name
    if path.is_symlink():
        raise ValueError('Linked feature dependency refused')
    path.resolve().relative_to(Path(root).resolve())
    return path


def authenticate_collection(root, stop, expected_module=COLLECTOR_MODULE):
    root = Path(root).resolve()
    terminal = read(root / 'COMPLETE.json')
    if terminal.get('status') != 'COMPLETE' or terminal.get('fresh_process_verified') is not True:
        raise ValueError('Complete independently replayed GO3 collection required')
    if any((root / name).exists() for name in ('PAUSED.json', 'FAILED.json')):
        raise ValueError('Ambiguous collection terminal')
    required = ('PLAN.json', 'VERIFIED.json', 'output/COLLECTION.json', 'output/SUPPORT.json',
                'output/COLLECTION_BINDING.json', 'output/SNAPSHOT.json', 'output/projection.sqlite')
    if any(name not in terminal['outputs'] for name in required):
        raise ValueError('Incomplete collection output manifest')
    for name, expected in sorted(terminal['outputs'].items()):
        if stop():
            raise Paused('complete collector authentication boundary')
        if core.sha(safe_child(root, name)) != expected:
            raise ValueError('Completed collection output changed')
    plan, verified = read(root / 'PLAN.json'), read(root / 'VERIFIED.json')
    if plan['module'] != expected_module:
        raise ValueError('Unreviewed source collector module')
    if verified.get('verified') is not True or verified.get('complete_source_collection_replayed') is not True:
        raise ValueError('Full independent collection replay is absent')
    support, data = read(root / 'output/SUPPORT.json'), read(root / 'output/COLLECTION.json')
    if (support.get('complete_collection') is not True or support.get('source_only') is not True
            or support.get('no_fitting_performed') is not True or support.get('scientific_admission') is not False
            or support.get('sites') != list(collection.SITES)):
        raise ValueError('Exact source-only five-site collection required')
    binding = data['binding']
    expected = dict(collector_sha256=core.sha(collection.__file__),
                    producer_sha256=core.sha(collection.producer.__file__),
                    source_sha256=core.sha(collection.source.__file__))
    if any(binding.get(key) != value for key, value in expected.items()):
        raise ValueError('Collection source code changed')
    if read(root / 'output/COLLECTION_BINDING.json') != binding:
        raise ValueError('Collection binding sidecar differs')
    snapshot = read(root / 'output/SNAPSHOT.json')
    if snapshot['binding'] != binding or snapshot['sha256'] != terminal['outputs']['output/projection.sqlite']:
        raise ValueError('Collection snapshot seal differs')
    if [item['site'] for item in data['sources']] != list(collection.SITES):
        raise ValueError('Collection source order or membership changed')
    current = []
    for item in data['sources']:
        if stop():
            raise Paused('source provenance authentication boundary')
        entry = dict(root=item['root'], complete_sha256=item['complete_sha256'])
        if core.sha(Path(item['root']) / 'COMPLETE.json') != entry['complete_sha256']:
            raise ValueError('Upstream source completion changed')
        try:
            now = collection.authenticate(item['site'], entry, stop)
        except collection.Paused as exc:
            raise Paused(str(exc)) from exc
        if now != item:
            raise ValueError('Complete source provenance differs from collector')
        current.append(now)
    if len({item['salt_sha256'] for item in current}) != 1 or sum(item['rows'] for item in current) != support['rows']:
        raise ValueError('Collection source salt or full row census differs')
    if data['sites'] != [str(Path(item['root']) / 'output') for item in current]:
        raise ValueError('Collection path roster differs')
    return dict(root=str(root), complete_sha256=core.sha(root / 'COMPLETE.json'),
                support_sha256=core.sha(root / 'output/SUPPORT.json'),
                collection_sha256=core.sha(root / 'output/COLLECTION.json'),
                expected_module=expected_module, sources=current, rows=support['rows'])


def training_rows(path):
    if core.sha(path) != analysis.ITERATER_SHA:
        raise ValueError('Published IteraTeR training partition pin differs')
    with Path(path).open(encoding='utf8') as stream:
        rows = [json.loads(line) for line in stream if line.strip()]
    if not rows or any(not all(isinstance(row.get(key), str) for key in ('before_sent', 'after_sent', 'labels')) for row in rows):
        raise ValueError('Invalid published intent training row')
    return rows


def array_digest(arrays):
    value = hashlib.sha256()
    for key in sorted(arrays):
        item = np.ascontiguousarray(arrays[key])
        value.update(json.dumps([key, item.dtype.str, item.shape]).encode())
        value.update(item.tobytes())
    return value.hexdigest()


def table_digest(table):
    table = table.combine_chunks().replace_schema_metadata(None)
    sink = pa.BufferOutputStream()
    with pa.ipc.new_stream(sink, table.schema) as writer:
        writer.write_table(table)
    return hashlib.sha256(sink.getvalue()).hexdigest()


def load_arrays(path):
    with np.load(path, allow_pickle=False) as data:
        return {key: data[key].copy() for key in data.files}


def model_arrays(model):
    scale, fit = model.steps[0][1], model.steps[1][1]
    return dict(mean=scale.mean_, scale=scale.scale_, var=scale.var_, samples=np.asarray(scale.n_samples_seen_),
                coef=fit.coef_, intercept=fit.intercept_, classes=fit.classes_, iterations=fit.n_iter_)


def restore_model(arrays):
    model = make_pipeline(StandardScaler(), LogisticRegression(C=1., max_iter=1000, random_state=core.SEED))
    scale, fit = model.steps[0][1], model.steps[1][1]
    scale.mean_, scale.scale_, scale.var_ = (arrays[key] for key in ('mean', 'scale', 'var'))
    scale.n_samples_seen_ = arrays['samples'][()]
    scale.n_features_in_ = len(scale.mean_)
    fit.coef_, fit.intercept_, fit.classes_, fit.n_iter_ = (arrays[key] for key in ('coef', 'intercept', 'classes', 'iterations'))
    fit.n_features_in_ = len(scale.mean_)
    return model


def checkpoint(output, state):
    core.write(output / 'STATE.json', state)
    core.write(output / 'STATE.seal.json', dict(sha256=core.sha(output / 'STATE.json')))


def open_state(output, binding):
    path = output / 'STATE.json'
    if not path.exists():
        if any((output / name).exists() for name in ('training', 'blocks', 'model.npz')):
            raise ValueError('Unsealed feature output is not resumable')
        state = dict(binding=binding, training=[], blocks=[], model=None, pilot_done=False, completed_units=0)
        checkpoint(output, state)
    else:
        if read(output / 'STATE.seal.json')['sha256'] != core.sha(path):
            raise ValueError('Feature checkpoint state changed')
        state = read(path)
        if state['binding'] != binding:
            raise ValueError('Feature checkpoint source/model/code binding changed')
    listed = state['training'] + state['blocks'] + ([state['model']] if state['model'] else [])
    expected = {row['path'] for row in listed}
    actual = {path.relative_to(output).as_posix() for folder in ('training', 'blocks')
              for path in (output / folder).glob('*') if path.is_file()}
    if (output / 'model.npz').exists():
        actual.add('model.npz')
    if expected != actual or len(expected) != len(listed):
        raise ValueError('Feature checkpoint contains unsealed or duplicate parts')
    for item in listed:
        if core.sha(safe_child(output, item['path'])) != item['sha256']:
            raise ValueError('Feature checkpoint part changed')
    if state['completed_units'] != len(listed):
        raise ValueError('Feature checkpoint work accounting differs')
    return state


def save_arrays(output, relative, arrays):
    path = output / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise ValueError('Refusing to overwrite unsealed numerical part')
    np.savez(path, **arrays)
    return dict(path=relative, sha256=core.sha(path), content_sha256=array_digest(arrays))


def complete_unit(output, state, pilot):
    state['completed_units'] += 1
    trigger = not state['pilot_done'] and state['completed_units'] >= pilot
    if trigger:
        state['pilot_done'] = True
    checkpoint(output, state)
    core.write(output / 'PROGRESS.json', dict(phase='complete_feature_units', completed=state['completed_units']))
    if trigger:
        raise Paused('first five percent of declared training and source feature units')


def run_features(output, inputs, config, expected_module=COLLECTOR_MODULE):
    if set(inputs) != {'collection_run', 'iterater_train'} or set(config) - {'phase', 'max_wall_seconds'}:
        raise ValueError('Exact collector-bound feature contract required')
    if config.get('phase') != 'features':
        raise ValueError('Feature-only stage required')
    maximum = float(config.get('max_wall_seconds', 900))
    if not math.isfinite(maximum) or maximum <= 0:
        raise ValueError('Positive finite feature wall quantum required')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    began = time.monotonic()
    stop = lambda: requested(output) or time.monotonic() - began >= maximum
    early = dict(collection_root=str(Path(inputs['collection_run']).resolve()),
                 collection_complete_sha256=core.sha(Path(inputs['collection_run']) / 'COMPLETE.json'),
                 training_sha256=core.sha(inputs['iterater_train']), feature_code_sha256=core.sha(__file__),
                 collector_module=expected_module)
    if (output / 'FEATURE_BINDING.json').exists() and read(output / 'FEATURE_BINDING.json') != early:
        raise ValueError('Feature dependency binding changed')
    core.write(output / 'FEATURE_BINDING.json', early)
    state = None
    planned = 0
    try:
        provenance = authenticate_collection(inputs['collection_run'], stop, expected_module)
        rows = training_rows(inputs['iterater_train'])
        planned = math.ceil(len(rows) / BATCH) + 1 + sum(math.ceil(info['rows'] / BATCH) for info in provenance['sources'])
        pilot = max(1, math.ceil(.05 * planned))
        binding = dict(provenance=provenance, training_sha256=analysis.ITERATER_SHA, batch_size=BATCH,
                       feature_code_sha256=core.sha(__file__), analysis_sha256=core.sha(analysis.__file__),
                       core_sha256=core.sha(core.__file__), collection_sha256=core.sha(collection.__file__),
                       libraries=dict(numpy=np.__version__, pyarrow=pa.__version__, sklearn=sklearn.__version__))
        state = open_state(output, binding)
        for start in range(0, len(rows), BATCH):
            number = start // BATCH
            if number < len(state['training']):
                continue
            if stop():
                raise Paused('before complete external training feature block')
            block = rows[start:start + BATCH]
            x = np.asarray([analysis.features(row['before_sent'], row['after_sent']) for row in block], float)
            y = np.asarray([row['labels'] for row in block], dtype=str)
            saved = save_arrays(output, f'training/{number:07d}.npz', dict(x=x, y=y))
            state['training'].append(saved | dict(first_row=start, rows=len(block)))
            complete_unit(output, state, pilot)
        if state['model'] is None:
            if stop():
                raise Paused('before fixed external intent model fit')
            bank = [load_arrays(output / item['path']) for item in state['training']]
            x = np.concatenate([item['x'] for item in bank])
            y = np.concatenate([item['y'] for item in bank])
            model = make_pipeline(StandardScaler(), LogisticRegression(C=1., max_iter=1000, random_state=core.SEED))
            model.fit(x, y)
            state['model'] = save_arrays(output, 'model.npz', model_arrays(model))
            complete_unit(output, state, pilot)
        model = restore_model(load_arrays(output / state['model']['path']))
        index = 0
        for info in provenance['sources']:
            first = 0
            for batch in pq.ParquetFile(info['projection']).iter_batches(batch_size=BATCH):
                if index < len(state['blocks']):
                    saved = state['blocks'][index]
                    if (saved['site'], saved['first_row'], saved['rows']) != (info['site'], first, batch.num_rows):
                        raise ValueError('Retained source block cursor differs')
                else:
                    if stop():
                        raise Paused('before complete Stack feature block')
                    frame = batch.to_pandas()
                    x = np.asarray([analysis.features(a, b) for a, b in zip(frame.before, frame.after)], float)
                    probability = model.predict_proba(x)
                    if x.shape != (len(frame), 14) or not np.isfinite(x).all() or not np.isfinite(probability).all():
                        raise ValueError('Incomplete or nonfinite diff/intent features')
                    if not np.allclose(probability.sum(axis=1), 1., atol=1e-12, rtol=0):
                        raise ValueError('External intent probabilities are not normalized')
                    saved_frame = frame.drop(columns=['before', 'after']).copy()
                    for column in range(x.shape[1]):
                        saved_frame[f'diff_{column}'] = x[:, column]
                    for column, label in enumerate(model.classes_):
                        saved_frame['intent_' + label] = probability[:, column]
                    table = pa.Table.from_pandas(saved_frame, preserve_index=False).replace_schema_metadata(None)
                    relative = f'blocks/{index:07d}.parquet'
                    path = output / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    if path.exists():
                        raise ValueError('Refusing to overwrite unsealed feature block')
                    pq.write_table(table, path, compression='zstd')
                    state['blocks'].append(dict(path=relative, sha256=core.sha(path), content_sha256=table_digest(table),
                                                site=info['site'], first_row=first, rows=len(frame)))
                    complete_unit(output, state, pilot)
                index += 1
                first += batch.num_rows
            if first != info['rows']:
                raise ValueError('Complete source row count changed')
        if len(state['blocks']) != index or sum(part['rows'] for part in state['blocks']) != provenance['rows'] or state['completed_units'] != planned:
            raise ValueError('Complete feature bank accounting differs')
        result = dict(feature_only=True, scientific_admission=False, complete_features=True, all_source_rows_retained=True,
                      rows_projected=provenance['rows'], declared_work_units=planned, first_pilot_units=pilot,
                      binding=binding, training=dict(published_split='train only', rows=len(rows),
                      labels=dict(Counter(row['labels'] for row in rows)), source_sha256=analysis.ITERATER_SHA,
                      label_scope='released annotator revision-intent categories, not writers own goal survey'),
                      model=state['model'], training_blocks=state['training'], blocks=state['blocks'],
                      required_next='separately admitted collection-bound complete classifier and all-row habit consumer')
        core.write(output / 'FEATURES.json', result)
        return result
    except Paused as pause:
        return dict(status='yielded', phase='feature_preparation', reason=str(pause),
                    completed=state['completed_units'] if state else 0, total=planned,
                    feature_only=True, complete_features=False)


def execute(output, inputs, config):
    return run_features(output, inputs, config)


def verify_features(output, inputs, config, expected_module=COLLECTOR_MODULE):
    output = Path(output)
    actual = run_features(output / 'independent-replay', inputs, config, expected_module)
    if actual.get('status') == 'yielded':
        return actual | dict(verified=False)
    expected = read(output / 'FEATURES.json')
    for field in ('model', 'training_blocks', 'blocks'):
        left = [expected[field]] if field == 'model' else expected[field]
        right = [actual[field]] if field == 'model' else actual[field]
        if len(left) != len(right):
            raise ValueError('Incomplete independent feature bank replay')
        for saved, replayed in zip(left, right):
            if {k: v for k, v in saved.items() if k != 'sha256'} != {k: v for k, v in replayed.items() if k != 'sha256'}:
                raise ValueError('Independent feature logical content differs')
            a, b = output / saved['path'], output / 'independent-replay' / replayed['path']
            if core.sha(a) != saved['sha256'] or core.sha(b) != replayed['sha256']:
                raise ValueError('Saved/replayed feature storage changed')
            if field == 'blocks':
                if not pq.read_table(a).equals(pq.read_table(b), check_metadata=True):
                    raise ValueError('Every feature and metadata row must replay exactly')
            else:
                x, y = load_arrays(a), load_arrays(b)
                if set(x) != set(y) or any(not np.array_equal(x[k], y[k]) for k in x):
                    raise ValueError('Complete original intent training and model must replay')
    if {k: v for k, v in expected.items() if k not in ('model', 'training_blocks', 'blocks')} != {k: v for k, v in actual.items() if k not in ('model', 'training_blocks', 'blocks')}:
        raise ValueError('Complete feature contract or counts differ')
    return dict(verified=True, all_feature_rows_replayed=True, all_external_training_rows_and_model_replayed=True,
                all_source_rows_retained=True, no_stack_scientific_fit=True)


def verify(output, inputs, config):
    return verify_features(output, inputs, config)
