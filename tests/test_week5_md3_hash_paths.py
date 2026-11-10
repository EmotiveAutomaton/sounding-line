import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from runners.drive.cards import week5_md3_followup as study
from runners.drive.cards import week5_md3_followup_fixture as fixture
from runners.drive.cards import week5_md3_followup_fixture_v3 as first
from runners.drive.cards import week5_md3_followup_fixture_v4 as repaired


@pytest.fixture
def real_boundary(tmp_path, monkeypatch):
    task = tmp_path / 'task with spaces.npz'
    np.savez(task, first=np.zeros((96, 30, 15)))
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps(dict(constructed_only=True, card='MD3.s', case='positive',
        participants=96, parent_primary={'gamma': .65, 'standing_sd': 1},
        source_sha256=hashlib.sha256(task.read_bytes()).hexdigest())), encoding='utf8')
    monkeypatch.setattr(fixture, 'arithmetic', lambda: {'component_stub': True})
    def before_fit(*args, **kwargs):
        raise study.YieldRequested({'status': 'yielded', 'component_pre_fit_boundary': True})
    monkeypatch.setattr(study, 'cell_setup', before_fit)
    return {'task': str(task), 'manifest': str(manifest)}


def test_first_repair_fails_inside_actual_handler(tmp_path, real_boundary):
    with pytest.raises(AttributeError, match='open'):
        first.execute(tmp_path / 'old', real_boundary, {'phase': 'MD3.s', 'case': 'positive', 'draws': 2000})


@pytest.mark.parametrize('operation', ['execute', 'verify'])
def test_actual_handler_reaches_controlled_prefit_yield(tmp_path, real_boundary, operation):
    prior = study.core.sha
    result = getattr(repaired, operation)(tmp_path / operation, real_boundary,
        {'phase': 'MD3.s', 'case': 'positive', 'draws': 2000})
    assert result['component_pre_fit_boundary'] and study.core.sha is prior
    assert all(isinstance(value, str) for value in real_boundary.values())


def test_all_dependency_hashes_equal_independent_bytes():
    with repaired.path_hashing():
        actual = study.dependencies()
    modules = (study.core, study.original, study.conditional, study)
    assert actual == {Path(module.__file__).name: hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest() for module in modules}


def test_exception_restores_reader_and_changed_source_still_fails(tmp_path, real_boundary):
    prior = study.core.sha
    Path(real_boundary['task']).write_bytes(b'changed')
    with pytest.raises(ValueError, match='task changed'):
        repaired.execute(tmp_path / 'bad', real_boundary, {'phase': 'MD3.s', 'case': 'positive', 'draws': 2000})
    assert study.core.sha is prior
