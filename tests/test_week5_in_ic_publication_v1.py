import json
import numpy as np
import pytest
from runners.drive.cards import week5_in_ic_publication_v1 as adapter
from runners.drive.cards import week5_in_ic_publication_fixture_v1 as fixture


def save(root, name='-2-000.json', status='ok', draws=2000, value=0):
    path = root / 'worlds' / name
    record = dict(binding='a' * 64, fit=dict(status=status, draws=draws, estimate=[value], interval=[[value, value]]))
    adapter.publication.write_json(path, record)
    adapter.publication.write_json(path.with_suffix('.seal.json'), dict(sha256=adapter.publication.sha(path)))
    return path


@pytest.mark.parametrize('config', [dict(phase='IN1.w'), dict(phase='IN3.ic', draws=1999),
    dict(phase='IN3.ic', worlds=99), dict(phase='IN3.ic', max_new_worlds=1)])
def test_contract_refuses_before_source_access(tmp_path, config):
    with pytest.raises(ValueError):
        adapter.execute(tmp_path, {'generation': 'absent'}, config)


@pytest.mark.parametrize('inputs', [{'generation': 'absent', 'validation': 'extra'}, {}])
def test_exact_source_roster(tmp_path, inputs):
    with pytest.raises(ValueError, match='inputs'):
        adapter.execute(tmp_path, inputs, dict(phase='IN3.ic'))


def test_writer_restored_on_producer_exception(tmp_path, monkeypatch):
    writer = adapter.original.core.write_json
    def fail(*args):
        assert adapter.original.core.write_json is adapter.publication.write_json
        raise RuntimeError('producer failure')
    monkeypatch.setattr(adapter.original, 'calibrate', fail)
    with pytest.raises(RuntimeError, match='producer failure'):
        adapter.calibrate(None, None, None, None, .1, {}, tmp_path)
    assert adapter.original.core.write_json is writer


@pytest.mark.parametrize('fault', ['orphan', 'gap', 'changed', 'short-draws', 'after-failure', 'extra'])
def test_checkpoint_refusals(tmp_path, fault):
    path = save(tmp_path)
    if fault == 'orphan':
        path.unlink()
    elif fault == 'gap':
        save(tmp_path, '-2-002.json')
    elif fault == 'changed':
        path.write_text('{}')
    elif fault == 'short-draws':
        save(tmp_path, draws=1999)
    elif fault == 'after-failure':
        save(tmp_path, status='rank deficient')
        save(tmp_path, '-2-001.json')
    else:
        (path.parent / 'unexpected.txt').write_text('extra')
    with pytest.raises(ValueError):
        adapter.world_bank(tmp_path)


def test_failed_fit_retained_but_never_success(tmp_path):
    save(tmp_path, status='rank deficient')
    assert len(adapter.world_bank(tmp_path)) == 1
    with pytest.raises(ValueError):
        adapter.world_bank(tmp_path, complete=True)


def test_operational_quantum_preserves_full_grid(tmp_path):
    assert adapter.numerical_config(tmp_path, {}) == dict(worlds=100, draws=2000, max_new_worlds=25)
    for i in range(25):
        save(tmp_path, f'-2-{i:03d}.json')
    assert adapter.numerical_config(tmp_path, {}) == dict(worlds=100, draws=2000, max_new_worlds=500)


@pytest.mark.parametrize('rank_deficient', [False, True])
def test_actual_in4_entry_preserves_support_disposition(tmp_path, monkeypatch, rank_deficient):
    monkeypatch.setattr(adapter.original.pd, 'read_parquet', lambda _: None)
    x = np.ones((12, 2 if rank_deficient else 1))
    monkeypatch.setattr(adapter.original, 'matrix', lambda *args: (x, np.ones(12), np.arange(12), np.ones(x.shape[1]), .1))
    result = adapter.execute(tmp_path, {'generation': 'fake', 'validation': 'fake'}, dict(phase='IN4.ic'))
    assert result['status'] == ('design cannot test' if rank_deficient else 'below floor, descriptive')
    assert adapter.verify(tmp_path, {'generation': 'fake', 'validation': 'fake'}, dict(phase='IN4.ic'))['verified']
    assert not (tmp_path / 'worlds').exists()


def test_individual_world_parity_not_just_summary(tmp_path):
    save(tmp_path / 'left', value=0)
    save(tmp_path / 'right', value=1)
    with pytest.raises(ValueError, match='individual world'):
        fixture.compare(tmp_path / 'left', tmp_path / 'right')


def test_verify_keeps_pilot_incomplete(tmp_path, monkeypatch):
    adapter.publication.write_json(tmp_path / 'RESULT.json', {'status': 'below floor, descriptive'})
    monkeypatch.setattr(adapter, 'execute', lambda *args: dict(status='yielded', complete_card=False))
    assert adapter.verify(tmp_path, {'generation': 'fake'}, dict(phase='IN3.ic'))['verified'] is False


def test_verifier_refuses_sealed_world_change_with_equal_summary(tmp_path, monkeypatch):
    saved = dict(status='invalid sensitivity', card='IN3.ic')
    adapter.publication.write_json(tmp_path / 'RESULT.json', saved)
    save(tmp_path, status='rank deficient', value=0)
    save(tmp_path / 'independent-replay', status='rank deficient', value=1)
    monkeypatch.setattr(adapter, 'execute', lambda *args: saved)
    with pytest.raises(ValueError, match='individual world replay'):
        adapter.verify(tmp_path, {'generation': 'fake'}, dict(phase='IN3.ic'))
