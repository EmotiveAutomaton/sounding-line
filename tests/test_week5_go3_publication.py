"""Focused publication/identity checks; full numerical qualification is separate."""
from pathlib import Path
import types
import pytest
from runners.drive.cards import week5_go3_publication as p
from runners.drive.cards import week5_go3_publication_io_fixture as native
from runners.drive.cards import week5_go3_features_publication as feature
from runners.drive.cards import week5_go3_features_publication_fixture as feature_fixture
from runners.drive.cards import week5_go3_bank_publication as bank
from runners.drive.cards import week5_go3_bank_publication_fixture as bank_fixture
from runners.drive.cards import week5_go3_math_publication_fixture as math_fixture


def test_real_writer_matches_unchanged_monitor_during_replace(tmp_path):
    assert all(native.race_case(tmp_path / 'race').values())


def test_real_monitor_still_refuses_missing_data_and_permission(tmp_path):
    result = native.refusal_case(tmp_path / 'strict')
    assert result['observed'] == ['FileNotFoundError', 'PermissionError']


def test_actual_windows_sharing_denial_and_recovery(tmp_path):
    assert all(native.sharing_case(tmp_path / 'sharing').values())


def test_writer_and_producer_alias_restore_on_exception():
    original = lambda *args: None
    module = types.SimpleNamespace(write=original, expected='original')
    with pytest.raises(RuntimeError):
        with p.alias(module, 'expected', 'successor'):
            with p.io.publication([(module, 'write')]):
                assert module.expected == 'successor' and module.write is p.io.write_json
                raise RuntimeError('retained failure')
    assert module.expected == 'original' and module.write is original


@pytest.mark.parametrize('adapter', [feature, feature_fixture, bank, bank_fixture, math_fixture])
def test_execute_delegates_without_changing_scientific_result(tmp_path, monkeypatch, adapter):
    core = feature.original.core
    original_writer = core.write
    result = {'unchanged_scientific_value': [1, 0, -2.5]}
    calls = []
    def delegated(output, inputs, config, *identity):
        assert core.write is p.io.write_json
        calls.append((inputs, config, identity))
        core.write(output / 'DELEGATE.json', result)
        return result
    monkeypatch.setattr(p, 'require_complete_identity', lambda *args, **kwargs: None)
    monkeypatch.setattr(adapter.original, 'run' if adapter is bank else 'execute', delegated)
    inputs, config = {'feature_run': 'unread-stub'}, {'phase': 'stub', 'max_wall_seconds': 900}
    assert adapter.execute(tmp_path / 'actual', inputs, config) == result
    assert calls[0][:2] == (inputs, config)
    assert core.write is original_writer
    if adapter is bank:
        assert calls[0][2] == (feature.MODULE,)
    assert p.read(tmp_path / 'actual/DELEGATE.json') == result


@pytest.mark.parametrize('adapter', [feature, feature_fixture, bank, bank_fixture, math_fixture])
def test_independent_verifier_adds_identity_only(tmp_path, monkeypatch, adapter):
    original = {'verified': True, 'original_numeric_parity': True}
    def delegated(output, inputs, config, *identity):
        assert feature.original.core.write is p.io.write_json
        return original
    monkeypatch.setattr(p, 'require_complete_identity', lambda *args, **kwargs: None)
    monkeypatch.setattr(adapter.original, 'verify_run' if adapter is bank else 'verify', delegated)
    result = adapter.verify(tmp_path / 'actual', {'feature_run': 'unread-stub'}, {'phase': 'stub'})
    assert {k: result[k] for k in original} == original
    assert set(result) - set(original) == {'publication_identity_replayed', 'publication_spec'}
    assert p.read(tmp_path / 'actual' / p.IDENTITY) == p.read(tmp_path / 'actual/independent-replay' / p.IDENTITY)


def test_wall_quantum_can_change_but_cell_cannot(tmp_path):
    p.bind(tmp_path, 'declared', [], {}, {'cell': 'fixed', 'max_wall_seconds': 30})
    p.bind(tmp_path, 'declared', [], {}, {'cell': 'fixed', 'max_wall_seconds': 90})
    with pytest.raises(ValueError, match='identity changed'):
        p.bind(tmp_path, 'declared', [], {}, {'cell': 'other', 'max_wall_seconds': 90})


def test_changed_adapter_source_is_refused(tmp_path):
    source = tmp_path / 'source.py'; source.write_text('first')
    output = tmp_path / 'output'
    p.bind(output, 'declared', [source], {}, {})
    source.write_text('second')
    with pytest.raises(ValueError, match='identity changed'):
        p.bind(output, 'declared', [source], {}, {})


def test_legacy_unbound_output_cannot_be_migrated(tmp_path):
    (tmp_path / 'STATE.json').write_text('{}')
    with pytest.raises(ValueError, match='Unbound predecessor'):
        p.bind(tmp_path, 'declared', [], {}, {})


def test_incomplete_verifier_is_not_promoted(tmp_path):
    core = types.SimpleNamespace(write=lambda *args: None)
    with pytest.raises(ValueError, match='incomplete verification'):
        p.invoke(lambda *args: {'verified': False}, tmp_path, {}, {}, module='declared', sources=[], core=core, verify=True)


def test_changed_case_checkpoint_refuses(tmp_path):
    p.bind(tmp_path, native.MODULE, native.SOURCES, {}, {'phase': 'publication-qualification'})
    p.io.write_json(tmp_path / 'CASES.json', [])
    p.io.write_json(tmp_path / 'CASES.seal.json', {'sha256': 'changed'})
    with pytest.raises(ValueError, match='unsealed or changed'):
        native.execute(tmp_path, {}, {'phase': 'publication-qualification'})


def artificial_identity_envelope(root):
    """Component-only metadata: never a native fixture or scientific admission."""
    plan = dict(module=feature.MODULE, inputs={'constructed': 'unread'}, config={'phase': 'features'})
    p.io.write_json(root / 'PLAN.json', plan)
    p.io.write_json(root / 'VERIFIED.json', dict(publication_identity_replayed=True, publication_spec='GO3-UUID-1'))
    for directory in ('output', 'output/independent-replay'):
        p.bind(root / directory, feature.MODULE, feature.SOURCES, plan['inputs'], plan['config'])
    names = ['PLAN.json', 'VERIFIED.json'] + [directory + '/' + name for directory in ('output', 'output/independent-replay') for name in (p.IDENTITY, p.SEAL)]
    p.io.write_json(root / 'COMPLETE.json', dict(status='COMPLETE', fresh_process_verified=True,
                                               outputs={name: p.io.sha(root / name) for name in names}))


def test_added_identity_envelope_authenticates_exact_producer(tmp_path):
    artificial_identity_envelope(tmp_path)
    value = p.require_complete_identity(tmp_path, module=feature.MODULE, sources=feature.SOURCES)
    assert value['module'] == feature.MODULE
    with pytest.raises(ValueError, match='producer identity'):
        p.require_complete_identity(tmp_path, module=feature_fixture.MODULE, sources=feature_fixture.SOURCES)


@pytest.mark.parametrize('damage', ['missing_replay', 'changed_identity', 'ambiguous_terminal'])
def test_added_identity_envelope_refuses_incomplete_or_changed_metadata(tmp_path, damage):
    artificial_identity_envelope(tmp_path)
    if damage == 'missing_replay':
        done = p.read(tmp_path / 'COMPLETE.json')
        del done['outputs']['output/independent-replay/' + p.IDENTITY]
        p.io.write_json(tmp_path / 'COMPLETE.json', done)
    elif damage == 'changed_identity':
        p.io.write_json(tmp_path / 'output' / p.IDENTITY, {'changed': True})
    else:
        p.io.write_json(tmp_path / 'PAUSED.json', {'status': 'PAUSED'})
    with pytest.raises(ValueError):
        p.require_complete_identity(tmp_path, module=feature.MODULE, sources=feature.SOURCES)
