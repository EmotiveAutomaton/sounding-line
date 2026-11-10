"""Component tests only; actual counted original-model fixture is separate."""
from pathlib import Path
import json
import numpy as np
import pytest
from runners.drive.cards import week5_go3_collection_fixture as source_fixture
from runners.drive.cards import week5_go3_collection as collector
from runners.drive.cards import week5_go3_features_collected as feature
from runners.drive.cards import week5_go3_features_collected_fixture as fixture


def completed_collection(tmp_path):
    sources = tmp_path / 'sources'
    source_fixture.prepare(sources)
    root = tmp_path / 'collection'
    root.mkdir()
    inputs = dict(roster=str(sources / 'supported-roster.json'))
    config = dict(phase='collect', max_wall_seconds=300)
    output = root / 'output'
    assert collector.execute(output, inputs, config)['status'] == 'yielded'
    assert collector.execute(output, inputs, config)['complete_collection']
    assert collector.verify(output, inputs, config)['status'] == 'yielded'
    verified = collector.verify(output, inputs, config)
    collector.core.write(root / 'VERIFIED.json', verified)
    collector.core.write(root / 'PLAN.json', dict(module=feature.COLLECTOR_MODULE, inputs=inputs, config=config))
    seal(root)
    return root


def seal(root):
    collector.core.write(root / 'COMPLETE.json', dict(status='COMPLETE', fresh_process_verified=True,
        constructed_component_only=True,
        outputs={path.relative_to(root).as_posix(): collector.core.sha(path)
                 for path in root.rglob('*') if path.is_file() and path.name != 'COMPLETE.json'}))


def constructed_training(tmp_path, monkeypatch):
    rows = [dict(before_sent='old ' + 'word ' * (label + 1),
                 after_sent='New ' + 'word ' * (label + 1) + '.' * (repeat + 1),
                 labels='class_' + str(label)) for label in range(6) for repeat in range(4)]
    path = tmp_path / 'training.jsonl'
    path.write_text(''.join(json.dumps(row) + '\n' for row in rows), encoding='utf8')
    monkeypatch.setattr(feature.analysis, 'ITERATER_SHA', collector.core.sha(path))
    return path


def test_literal_known_answers():
    fixture.known_features()


def test_actual_collection_authentication(tmp_path):
    root = completed_collection(tmp_path)
    actual = feature.authenticate_collection(root, lambda: False)
    assert actual['rows'] == 2250
    assert [row['site'] for row in actual['sources']] == list(collector.SITES)


@pytest.mark.parametrize('damage', ['module', 'replay', 'scope', 'site_order'])
def test_resealed_bad_collection_contract_refused(tmp_path, damage):
    root = completed_collection(tmp_path)
    if damage == 'module':
        path = root / 'PLAN.json'; item = feature.read(path); item['module'] = 'other'
    elif damage == 'replay':
        path = root / 'VERIFIED.json'; item = feature.read(path); item['complete_source_collection_replayed'] = False
    elif damage == 'scope':
        path = root / 'output/SUPPORT.json'; item = feature.read(path); item['scientific_admission'] = True
    else:
        path = root / 'output/COLLECTION.json'; item = feature.read(path); item['sources'].reverse()
    collector.core.write(path, item)
    seal(root)
    with pytest.raises(ValueError):
        feature.authenticate_collection(root, lambda: False)


def test_checkpointed_model_and_full_feature_rows_replay(tmp_path, monkeypatch):
    root = completed_collection(tmp_path)
    train = constructed_training(tmp_path, monkeypatch)
    inputs = dict(collection_run=str(root), iterater_train=str(train))
    config = dict(phase='features', max_wall_seconds=300)
    output = tmp_path / 'features'
    first = feature.execute(output, inputs, config)
    assert first['status'] == 'yielded' and first['completed'] == 1
    saved = {p.relative_to(output): collector.core.sha(p) for p in (output / 'training').glob('*')}
    result = feature.execute(output, inputs, config)
    assert result['all_source_rows_retained'] and result['rows_projected'] == 2250
    assert all(collector.core.sha(output / p) == digest for p, digest in saved.items())
    fixture.original_parity(output, inputs, dict(rows=2250))
    assert feature.verify(output, inputs, config)['verified'] is False
    verified = feature.verify(output, inputs, config)
    assert verified['verified'] and verified['all_feature_rows_replayed']


def test_changed_training_and_checkpoint_parts_refused(tmp_path, monkeypatch):
    root = completed_collection(tmp_path)
    train = constructed_training(tmp_path, monkeypatch)
    inputs = dict(collection_run=str(root), iterater_train=str(train))
    config = dict(phase='features', max_wall_seconds=300)
    output = tmp_path / 'features'
    feature.execute(output, inputs, config)
    part = next((output / 'training').glob('*.npz'))
    part.write_bytes(part.read_bytes() + b'changed')
    with pytest.raises(ValueError, match='part changed'):
        feature.execute(output, inputs, config)
    train.write_text(train.read_text('utf8') + '\n', encoding='utf8')
    with pytest.raises(ValueError, match='dependency binding changed'):
        feature.execute(output, inputs, config)


def test_unsealed_parts_refuse_resume(tmp_path):
    folder = tmp_path / 'blocks'
    folder.mkdir()
    (folder / '0000000.parquet').write_bytes(b'unsealed')
    with pytest.raises(ValueError, match='Unsealed'):
        feature.open_state(tmp_path, {'binding': 'constructed'})


def test_model_roundtrip_exact():
    x = np.arange(120, dtype=float).reshape(12, 10)
    y = np.asarray(['one', 'two', 'three'] * 4)
    model = feature.make_pipeline(feature.StandardScaler(), feature.LogisticRegression(C=1., max_iter=1000, random_state=feature.core.SEED))
    model.fit(x, y)
    restored = feature.restore_model(feature.model_arrays(model))
    assert np.array_equal(model.predict_proba(x), restored.predict_proba(x))


def test_resource_pause_before_authentication_keeps_binding(tmp_path, monkeypatch):
    root = completed_collection(tmp_path)
    train = constructed_training(tmp_path, monkeypatch)
    monkeypatch.setattr(feature, 'requested', lambda output: True)
    output = tmp_path / 'features'
    result = feature.execute(output, dict(collection_run=str(root), iterater_train=str(train)), dict(phase='features'))
    assert result['status'] == 'yielded' and (output / 'FEATURE_BINDING.json').is_file()
    assert not (output / 'STATE.json').exists()
