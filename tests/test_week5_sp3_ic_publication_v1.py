import json
from pathlib import Path
import numpy as np
import pytest
from runners.drive.cards import week5_sp3_ic_publication_v1 as adapter
from runners.drive.cards import week5_sp3_ic_publication_fixture_v1 as fixture


def test_writer_scope_restored_on_failure(monkeypatch, tmp_path):
    writer = adapter.original.parent.write
    def fail(*args):
        assert adapter.original.parent.write is adapter.publication.write_json
        raise RuntimeError('deliberate producer failure')
    monkeypatch.setattr(adapter.original, 'execute', fail)
    with pytest.raises(RuntimeError, match='deliberate'):
        adapter.execute(tmp_path, {'data': 'unused'}, {'phase': 'SP3.ic'})
    assert adapter.original.parent.write is writer


@pytest.mark.parametrize('config', [dict(phase='SP3'), dict(phase='SP3.ic', draws=1999),
                                   dict(phase='SP3.ic', worlds=99), dict(phase='SP3.ic', extra=True)])
def test_changed_grid_refused_before_source_access(tmp_path, config):
    with pytest.raises(ValueError):
        adapter.execute(tmp_path, {'data': 'does-not-exist'}, config)


def test_extra_input_refused(tmp_path):
    with pytest.raises(ValueError, match='data input'):
        adapter.execute(tmp_path, {'data': 'unused', 'extra': 'unused'}, {'phase': 'SP3.ic'})


def test_orphan_checkpoint_refused_before_producer(monkeypatch, tmp_path):
    (tmp_path / 'worlds').mkdir()
    (tmp_path / 'worlds/-2-000.sha256.json').write_text('{}')
    monkeypatch.setattr(adapter.original, 'execute', lambda *args: pytest.fail('producer must not run'))
    with pytest.raises(ValueError, match='orphaned'):
        adapter.execute(tmp_path, {'data': 'unused'}, {'phase': 'SP3.ic'})


def test_actual_verifier_restores_writer_and_retains_pilot(monkeypatch, tmp_path):
    (tmp_path / 'RESULT.json').write_text(json.dumps({'status': 'below floor, descriptive'}))
    writer = adapter.original.parent.write
    def verify(*args):
        assert adapter.original.parent.write is adapter.publication.write_json
        return {'status': 'yielded', 'verified': False}
    monkeypatch.setattr(adapter.original, 'verify', verify)
    assert adapter.verify(tmp_path, {'data': 'unused'}, {'phase': 'SP3.ic'})['verified'] is False
    assert adapter.original.parent.write is writer


def test_parity_refuses_changed_sealed_array(tmp_path):
    for side, value in [('left', 0.), ('right', 1.)]:
        root = tmp_path / side / 'worlds'
        root.mkdir(parents=True)
        path = root / '-2-000.npz'
        np.savez_compressed(path, values=np.full(2000, value), point=value)
        adapter.publication.write_json(path.with_suffix('.sha256.json'), {'sha256': adapter.publication.sha(path)})
    with pytest.raises(ValueError, match='numerical array'):
        fixture.compare(tmp_path / 'left', tmp_path / 'right')


def test_hash_tamper_refused(tmp_path):
    root = tmp_path / 'worlds'
    root.mkdir()
    path = root / '-2-000.npz'
    np.savez_compressed(path, values=np.zeros(2000), point=0.)
    adapter.publication.write_json(path.with_suffix('.sha256.json'), {'sha256': '0' * 64})
    with pytest.raises(ValueError, match='checkpoint changed'):
        adapter.execute(tmp_path, {'data': 'unused'}, {'phase': 'SP3.ic'})
