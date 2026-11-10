import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from runners.drive.cards import week5_md3_followup_fixture_v3 as repaired
from runners.drive.cards import week5_qualification_driver_v2 as driver2
from runners.drive.cards import week5_qualification_driver_v3 as driver3


@pytest.fixture
def serialized(tmp_path, monkeypatch):
    task = tmp_path / 'task with spaces.npz'
    np.savez(task, first=np.zeros((1, 2, 8)))
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps(dict(constructed_only=True, card='MD3.s',
        case='positive', participants=96, parent_primary={'gamma': .65},
        source_sha256=hashlib.sha256(task.read_bytes()).hexdigest())), encoding='utf8')
    base = repaired.original.original
    monkeypatch.setattr(base, 'arithmetic', lambda: {'verified': True, 'component_stub': True})
    monkeypatch.setattr(base.study, 'perform', lambda *a, **kw: {'status': 'yielded'})
    return json.loads(json.dumps({'task': str(task), 'manifest': str(manifest)}))


def test_original_real_entry_reproduces_json_path_failure(tmp_path, serialized):
    with pytest.raises(AttributeError, match='open'):
        repaired.original.execute(tmp_path / 'old', serialized, {'phase': 'MD3.s', 'case': 'positive', 'draws': 2000})


def test_repaired_real_entry_reaches_unchanged_handler(tmp_path, serialized):
    before = dict(serialized)
    assert repaired.execute(tmp_path / 'new', serialized,
        {'phase': 'MD3.s', 'case': 'positive', 'draws': 2000}) == {'status': 'yielded'}
    assert serialized == before and all(isinstance(value, str) for value in serialized.values())


def test_repaired_real_entry_keeps_changed_source_refusal(tmp_path, serialized):
    Path(serialized['task']).write_bytes(b'changed')
    with pytest.raises(ValueError, match='task changed'):
        repaired.execute(tmp_path / 'bad', serialized, {'phase': 'MD3.s', 'case': 'positive', 'draws': 2000})


def test_independent_verifier_normalizes_without_changing_config(tmp_path, serialized, monkeypatch):
    config = {'phase': 'MD3.s', 'case': 'positive', 'draws': 2000}
    def observe(output, inputs, received):
        assert received is config and all(isinstance(value, Path) for value in inputs.values())
        assert {key: str(value) for key, value in inputs.items()} == serialized
        return {'verified': False, 'component_only': True}
    monkeypatch.setattr(repaired.original, 'verify', observe)
    assert repaired.verify(tmp_path, serialized, config)['component_only']


def test_driver_registry_preserves_non_md_contracts():
    for card, spec in driver2.SPECS.items():
        new = driver3.SPECS[card]
        assert new[:3] == spec[:3]
        assert new[3] == ('runners.drive.cards.week5_md3_followup_fixture_v3' if card.startswith('MD') else spec[3])
    assert Path(driver3.__file__).resolve() != Path(driver2.__file__).resolve()
