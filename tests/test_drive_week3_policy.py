"""Admission tests use clocks/resources, not research outcomes."""
from datetime import timedelta
import json
import pytest
from runners.drive.cards import week3_policy as p
from runners.drive import calendar_20261025_week3 as c

AT = p.OPEN + timedelta(hours=1)


def plan():
    return dict(original_cpu_ceiling_seconds=3600, prior_cpu_seconds_charged=0,
                max_cpu_seconds=3600, max_wall_seconds=7200,
                forecast_cpu_seconds=600, projected_peak_ram_GiB=3)


def resource():
    return dict(ram_available_GiB=16, commit_headroom_GiB=24, disk_free_GiB=100)


def test_absent_shared_lock(tmp_path):
    result = p.admission(plan(), AT, resource(), tmp_path/'lock', 12)
    assert result['slots'] == 4 and not result['shared_reservation']['active']


def test_live_and_expired_shared_lock(tmp_path):
    lock = tmp_path/'lock'
    lock.write_text(json.dumps(dict(created_at=p.OPEN.isoformat(), expires_at=(p.OPEN+timedelta(days=2)).isoformat())))
    assert p.admission(plan(), AT, resource(), lock, 12)['slots'] == 3
    old = p.admission(plan(), p.OPEN+timedelta(hours=7), resource(), lock, 12)
    assert old['slots'] == 4 and old['shared_reservation']['log_required']


def test_missing_expiry_is_ignored_and_logged(tmp_path):
    lock = tmp_path/'lock'
    lock.write_text('{}')
    assert p.shared_reservation(lock, AT) == dict(active=False, reason='missing_expiry', log_required=True)


def test_reserved_memory_after_peak(tmp_path):
    lock = tmp_path/'lock'
    lock.write_text(json.dumps(dict(created_at=p.OPEN.isoformat(), expires_at=(p.OPEN+timedelta(hours=2)).isoformat())))
    with pytest.raises(RuntimeError, match='eight GiB'):
        p.admission(plan(), AT, dict(resource(), ram_available_GiB=10), lock, 12)


def test_dst_cutoffs_and_no_recursive_doubling(tmp_path):
    assert p.admission(plan(), p.FREEZE-timedelta(seconds=1), resource(), tmp_path/'lock', 8)['slots'] == 3
    with pytest.raises(RuntimeError, match='no-new-start'):
        p.admission(plan(), p.FREEZE, resource(), tmp_path/'lock', 12)
    bad = dict(plan(), prior_cpu_seconds_charged=4000)
    with pytest.raises(ValueError, match='cumulative'):
        p.costs(bad)
    with pytest.raises(RuntimeError, match='pilot'):
        p.admission(dict(plan(), forecast_cpu_seconds=7200), AT, resource(), tmp_path/'lock', 12)


def test_calendar_final_drain_preserves_health_config(tmp_path):
    config = tmp_path/'watch.json'
    config.write_text(json.dumps(dict(transition_only=False, health_interval_seconds=21600, paths=['existing'])))
    c.tick(tmp_path, config, p.DRAIN)
    value = json.loads(config.read_text())
    assert value['transition_only'] is True and value['paths'] == ['existing']
    assert value['health_interval_seconds'] == 21600
    assert not (tmp_path/'DRAIN_ADDENDUM_DUE.json').exists()
    assert c.tick(tmp_path, config, p.DRAIN) == []


def test_october25_old_close_no_longer_freezes_new_window(tmp_path):
    at = p.instant('2026-10-26T05:00:00+00:00')
    assert p.admission(plan(), at, resource(), tmp_path/'lock', 12)['slots'] == 4
    assert c.due_names(at, set()) == ['DIGEST_20261025']
