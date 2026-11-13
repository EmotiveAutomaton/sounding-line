from pathlib import Path
import pytest
from runners.drive.cards import week5_md3_s_production as adapter
from runners.drive.cards import week5_md3_s_adapter_fixture as fixture


def test_actual_production_boundary_and_independent_replay(tmp_path):
    assert fixture.execute(tmp_path / 'proof', {}, {})['actual_production_execute_verify']
    assert fixture.verify(tmp_path / 'proof', {}, {})['verified']


@pytest.mark.parametrize('phase', ['MD3.m', 'MD3.p', None])
def test_only_r3_specification_released(tmp_path, phase):
    with pytest.raises(ValueError, match='MD3.s only'):
        adapter.execute(tmp_path, {'task': 'unused', 'parent_run': 'unused'}, {'phase': phase})


def test_changed_source_bytes_still_refuse(tmp_path):
    args = fixture.prepare(tmp_path / 'fixture')
    Path(args['task']).write_bytes(b'changed')
    with pytest.raises(ValueError, match='source mismatch'):
        adapter.execute(tmp_path / 'out', args, {'phase': 'MD3.s', 'draws': 2000})


def test_changed_parent_bytes_still_refuse(tmp_path):
    args = fixture.prepare(tmp_path / 'fixture')
    (Path(args['parent_run']) / 'output/RESULT.json').write_bytes(b'changed')
    with pytest.raises(ValueError, match='dependency output changed'):
        adapter.execute(tmp_path / 'out', args, {'phase': 'MD3.s', 'draws': 2000})


def test_callable_restoration_on_error():
    old = (adapter.study.core.sha, adapter.study.core.save_json, adapter.study.save_fit)
    with pytest.raises(RuntimeError):
        with adapter.compatibility():
            raise RuntimeError('fixture')
    assert old == (adapter.study.core.sha, adapter.study.core.save_json, adapter.study.save_fit)
