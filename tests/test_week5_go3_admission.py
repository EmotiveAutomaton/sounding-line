"""Metadata-only scaffold refusals; no source, model or native execution."""
import json
from pathlib import Path
import pytest
from runners.drive.cards import week5_go3_admission as admission


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding='utf8')
    return path


def test_nonlaunchable_template_refuses():
    with pytest.raises(ValueError, match='owner-reviewed'):
        admission.build_plan({'owner_reviewed': False})


def test_missing_native_evidence_is_not_a_pass():
    with pytest.raises(ValueError, match='completion reference'):
        admission.completed(None, admission.FEATURE, [], {})


def test_scope_contains_all_scientific_and_runtime_bindings():
    assert 'runners/drive/cards/week5_go3_analysis.py' in admission.REQUIRED_SCOPE
    assert 'runners/drive/cards/week5_go.py' in admission.REQUIRED_SCOPE
    assert 'runners/drive/cards/week5_output_size.py' in admission.REQUIRED_SCOPE
    assert 'docs/design/stage-15/week5/GO3-analysis.md' in admission.REQUIRED_SCOPE


def test_conflicting_original_pin_refuses(tmp_path):
    path = str((tmp_path / 'x').resolve())
    with pytest.raises(ValueError, match='Conflicting'):
        admission.merge({path: 'a'}, {path: 'b'})


def test_source_path_cannot_escape(tmp_path):
    with pytest.raises(ValueError):
        admission.child(tmp_path, '../escape')


def test_changed_small_receipt_refuses(tmp_path):
    path = write(tmp_path / 'proof.json', {'verified': True})
    reference = dict(path=str(path), sha256=admission.sha(path))
    write(path, {'verified': False})
    with pytest.raises(ValueError, match='changed'):
        admission.file_proof(reference, {})


def test_measurement_boolean_without_counted_attempt_refuses(tmp_path):
    path = write(tmp_path / 'measurement.json', dict(measured=True, constructed_or_counted_native=True))
    with pytest.raises(ValueError, match='exact counted native attempt'):
        admission.measured_native(dict(path=str(path), sha256=admission.sha(path)), {})


def test_cost_census_keeps_failed_paused_and_live_reservations(tmp_path):
    for name, state, cpu in [('GO3-failed', 'FAILED.json', 7), ('GO3-paused', 'PAUSED.json', 11), ('GO2-live', None, 90)]:
        root = tmp_path / name
        write(root / 'PLAN.json', dict(campaign='S15-WEEK5', family='GO', max_cpu_seconds=cpu))
        (root / 'ATTEMPT.claim').write_text('claimed')
        if state:
            write(root / state, dict(cpu_seconds=cpu))
    result = admission.cost_census(tmp_path)
    assert result['known_GO3_cpu_seconds'] == 78
    assert result['known_GO_cpu_seconds'] == 198


def test_ambiguous_cost_terminal_refuses(tmp_path):
    root = tmp_path / 'GO3-ambiguous'
    write(root / 'PLAN.json', dict(campaign='S15-WEEK5', family='GO', max_cpu_seconds=10))
    write(root / 'PAUSED.json', dict(cpu_seconds=2))
    write(root / 'COMPLETE.json', dict(cpu_seconds=3))
    with pytest.raises(ValueError, match='Ambiguous'):
        admission.cost_census(tmp_path)


@pytest.mark.parametrize('count,expected', [(99, False), (100, True), (2000, True)])
def test_actual_primary_pilot_threshold(tmp_path, count, expected):
    path = write(tmp_path / 'output/classifier/bootstrap.json', dict(pilot_done=True, draws=[0] * count))
    paused = dict(paused_operation='execute', checkpoint_outputs={'classifier/bootstrap.json': admission.sha(path)})
    assert admission.observed_pilot((tmp_path, paused), 'analysis', 'GO3') is expected


def test_feature_pilot_requires_saved_complete_unit_state(tmp_path):
    path = write(tmp_path / 'output/independent-replay/STATE.json', dict(pilot_done=False, completed_units=3))
    paused = dict(paused_operation='verify', checkpoint_outputs={'independent-replay/STATE.json': admission.sha(path)})
    assert admission.observed_pilot((tmp_path, paused), 'features', None) is False


def test_changed_pilot_checkpoint_refuses(tmp_path):
    path = write(tmp_path / 'output/STATE.json', dict(pilot_done=True, completed_units=8))
    paused = dict(paused_operation='execute', checkpoint_outputs={'STATE.json': admission.sha(path)})
    write(path, dict(pilot_done=True, completed_units=9))
    with pytest.raises(ValueError, match='binding changed'):
        admission.observed_pilot((tmp_path, paused), 'features', None)
