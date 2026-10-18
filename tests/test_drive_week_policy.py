import pytest
from runners.drive.cards import week_policy as p


def plan():
    return dict(original_wall_ceiling_seconds=100, max_wall_seconds=100, forecast_cpu_seconds=50, pins={})


@pytest.mark.parametrize('when,allowed',[
    ('2026-10-21T05:59:59-07:00',True),('2026-10-21T06:00:00-07:00',False),
    ('2026-10-21T12:00:00-07:00',False),('2026-10-22T06:59:59-07:00',False),
    ('2026-10-22T07:00:00-07:00',True),('2026-10-25T19:59:59-07:00',True),
    ('2026-10-25T20:00:00-07:00',False),('2026-10-25T22:00:00-07:00',False)])
def test_exact_start_boundaries(when,allowed):
    if allowed:assert p.window(p.instant(when))[0] in ('pre-talk','post-talk')
    else:
        with pytest.raises(RuntimeError):p.window(p.instant(when))


def test_original_ceiling_doubles_once_and_prior_replay_counts():
    assert p.cost(plan()|dict(max_wall_seconds=200)) == (100,0,200)
    with pytest.raises(ValueError):p.cost(plan()|dict(max_wall_seconds=201))
    with pytest.raises(ValueError):p.cost(plan()|dict(max_wall_seconds=200,prior_wall_seconds_charged=1))
    assert p.cost(plan()|dict(max_wall_seconds=150,prior_wall_seconds_charged=50)) == (100,50,150)


def test_demo_unknown_peak_floor_and_expiry():
    snapshot=dict(ram_available_GiB=11.99,commit_headroom_GiB=20,disk_free_GiB=50)
    before=p.instant('2026-10-20T19:59:59-07:00');after=p.instant('2026-10-20T20:00:00-07:00')
    with pytest.raises(RuntimeError,match='Demo'):p.admission(plan(),before,snapshot)
    value=p.admission(plan(),before,snapshot|dict(ram_available_GiB=12))
    assert value['reserved_demo_slot'] and value['slots']==p.slot_count()-1
    assert not p.admission(plan(),after,snapshot)['reserved_demo_slot']


def test_windows_pilots_and_completion_proof(tmp_path):
    snapshot=dict(ram_available_GiB=20,commit_headroom_GiB=20,disk_free_GiB=50)
    at=p.instant('2026-10-18T15:00:00-07:00')
    with pytest.raises(RuntimeError,match='pilot'):p.admission(plan()|dict(forecast_cpu_seconds=7200),at,snapshot)
    with pytest.raises(RuntimeError,match='window'):p.admission(plan()|dict(week_window='post-talk'),at,snapshot)
    with pytest.raises(RuntimeError,match='earliest'):p.admission(plan()|dict(earliest_start_utc='2026-10-19T07:00:00-07:00'),at,snapshot)
    receipt=tmp_path/'complete.json';receipt.write_text('{"availableModulesComplete":true}')
    with pytest.raises(ValueError,match='pinned'):p.demo_reserved(plan()|dict(demo_completion_receipt=str(receipt)),at)
    assert not p.demo_reserved(plan()|dict(demo_completion_receipt=str(receipt),pins={str(receipt):p.filehash(receipt)}),at)
