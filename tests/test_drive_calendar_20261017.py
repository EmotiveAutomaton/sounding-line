from datetime import datetime
import pytest
from runners.drive.calendar_20261017 import due_names, tick
from runners.stage14.common import atomic, read


def test_due_boundary_and_no_repeat(tmp_path):
    config = tmp_path / 'watch.json'
    atomic(config, {'transition_only': False, 'paths': ['keep'], 'health_interval_seconds': 21600})
    assert due_names(datetime.fromisoformat('2026-10-18T02:59:59+00:00'), set()) == []
    instant = datetime.fromisoformat('2026-10-18T03:00:00+00:00')
    assert tick(tmp_path, config, instant) == ['DIGEST_20261017']
    assert tick(tmp_path, config, instant) == []
    assert read(config)['transition_only'] is False
    with pytest.raises(ValueError):
        due_names(datetime(2026, 10, 18), set())


def test_freeze_restores_only_switch_and_catches_up(tmp_path):
    config = tmp_path / 'watch.json'
    original = {'transition_only': False, 'paths': ['keep'], 'health_interval_seconds': 21600, 'owner': 'unchanged'}
    atomic(config, original)
    emitted = tick(tmp_path, config, datetime.fromisoformat('2026-10-21T13:00:00+00:00'))
    assert 'FREEZE' in emitted and 'DRAIN_REVIEW' not in emitted
    assert read(config) == dict(original, transition_only=True)
    assert read(tmp_path / 'FREEZE.json')['publication_performed'] is False
    assert tick(tmp_path, config, datetime.fromisoformat('2026-10-21T19:00:00+00:00')) == ['DRAIN_REVIEW']
