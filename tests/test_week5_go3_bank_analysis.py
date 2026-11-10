"""Unexecuted full-grid mathematical fixtures and immutable-state refusals."""
import numpy as np
import pytest
from runners.drive.cards import week5_go3_bank_analysis as a
from runners.drive.cards import week5_go3_bank_analysis_fixture as f


@pytest.mark.parametrize('signal', [False, True])
@pytest.mark.parametrize('specification', a.original.grid(), ids=lambda item: item['cell'])
def test_every_declared_cell_and_full_reference_parity(tmp_path, signal, specification):
    pauses = 0
    while True:
        try:
            result = f.mathematical_parity(tmp_path / 'actual', signal, specification)
            break
        except a.Paused:
            pauses += 1
            assert pauses <= 2
    assert result['draws'] == specification['draws']
    assert pauses == (2 if specification['cell'] == 'GO3' else 1)


def test_changed_fold_and_reference_refused(tmp_path):
    frame = f.world(True)
    config = a.cell_config('GO3')
    with pytest.raises(a.Paused):
        a.run_frame(tmp_path, frame, config, 'fixed', lambda: False)
    part = next((tmp_path / 'classifier/folds').glob('*.npz'))
    part.write_bytes(part.read_bytes() + b'changed')
    with pytest.raises(ValueError, match='fold changed'):
        a.run_frame(tmp_path, frame, config, 'fixed', lambda: False)


def test_changed_semantic_binding_refused(tmp_path):
    frame = f.world(False)
    config = a.cell_config('GO3')
    with pytest.raises(a.Paused):
        a.run_frame(tmp_path, frame, config, 'fixed', lambda: False)
    with pytest.raises(ValueError, match='binding differs'):
        a.run_frame(tmp_path, frame, config, 'changed', lambda: False)


def test_sparse_route_equals_original_without_heldout_claim(tmp_path):
    frame = f.world(False)
    keep = sorted(frame.editor.unique())[:12]
    frame = frame.loc[frame.editor.isin(keep)]
    config = a.cell_config('GO3.self')
    result = a.run_frame(tmp_path, frame, config, 'sparse', lambda: False)
    expected = a.original.classify(frame, config)
    assert result['outcome'] == 'below floor, descriptive'
    assert all(result[key] == value for key, value in expected.items())


def test_resource_yield_precedes_fit(tmp_path):
    with pytest.raises(a.Paused):
        a.run_frame(tmp_path, f.world(True), a.cell_config('GO3'), 'paused', lambda: True)
    assert not list(tmp_path.rglob('*.npz'))


def test_full_habit_scope_contains_nonprimary_rows():
    frame = f.world(False)
    primary = frame.type.isin([5, 24]) & frame.reason.isin(a.SOURCE.PRIMARY)
    assert len(frame) == 3600 and primary.sum() == 2250
    profiles = a.original.habit_profiles(frame.assign(row=np.arange(len(frame))).to_dict('records'))
    assert sum(len(half) for halves in profiles.values() for half in halves) == len(frame)
