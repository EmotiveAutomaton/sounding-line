from datetime import timedelta
from pathlib import Path
import json
import pytest
from runners.drive.cards import week5_policy as p
from runners.drive import calendar_20261107_week5 as calendar

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value),encoding='utf-8')

def plan():
    return dict(campaign='S15-WEEK5',family='CH',numerical_threads=2,paid=False,gpu=False,ollama=False,
                premortem=dict(case_and_check='known answer',smaller_route='whole clusters'),max_cpu_seconds=100,
                max_wall_seconds=200,forecast_cpu_seconds=100,projected_peak_ram_GiB=2,
                fixture_passed=True,reviewed_design_commit='fixture')

def admit(tmp,**kw):
    params=dict(at=p.FREEZE-timedelta(days=1),resources=dict(ram_available_GiB=24,commit_headroom_GiB=32,disk_free_GiB=99),
                budget_root=tmp,lock_path=tmp/'shared.lock',occupied=[],logical=24)
    params.update(kw);return p.admission(plan(),**params)

def test_new_clock_does_not_inherit_old_freeze(tmp_path):
    assert admit(tmp_path)['slots']==8
    with pytest.raises(RuntimeError,match='boundary'):admit(tmp_path,at=p.FREEZE)

def test_unstarted_reservations_do_not_consume_capacity(tmp_path):
    write(tmp_path/'a/PLAN.json',plan()|{'max_cpu_seconds':3e6})
    assert p.charges(tmp_path)['CH']==0
    assert admit(tmp_path)['remaining_cpu_seconds']>0

def test_failures_count_and_ambiguous_terminal_refuses(tmp_path):
    write(tmp_path/'a/PLAN.json',plan());(tmp_path/'a/ATTEMPT.claim').touch()
    write(tmp_path/'a/FAILED.json',{'cpu_seconds':17})
    assert p.charges(tmp_path)['CH']==47
    write(tmp_path/'a/COMPLETE.json',{'cpu_seconds':17})
    with pytest.raises(ValueError,match='Ambiguous'):p.charges(tmp_path)

def test_unknown_attempt_retains_charge(tmp_path):
    write(tmp_path/'a/PLAN.json',plan());(tmp_path/'a/ATTEMPT.claim').touch()
    assert p.charges(tmp_path)['CH']==130

def test_joint_memory_and_slot_banks(tmp_path):
    old,new=tmp_path/'old',tmp_path/'new'
    for i in range(8):write((old if i<4 else new)/f'slot-{i}.json',{'native':{'pid':999999},'projected_peak_ram_GiB':2})
    paths=p.lease_paths(old,new);assert len(paths)==8
    with pytest.raises(RuntimeError,match='occupied'):admit(tmp_path,occupied=paths)
    with pytest.raises(RuntimeError,match='eight GiB'):admit(tmp_path,occupied=paths[:7],resources=dict(ram_available_GiB=23,commit_headroom_GiB=32,disk_free_GiB=99))

def test_small_host_and_resource_floor_refuse(tmp_path):
    with pytest.raises(RuntimeError,match='host'):admit(tmp_path,logical=12)
    with pytest.raises(RuntimeError,match='floor'):admit(tmp_path,resources=dict(ram_available_GiB=5,commit_headroom_GiB=32,disk_free_GiB=99))

def test_calendar_restores_after_both_older_drains_and_closes_once(tmp_path):
    root=tmp_path/'calendar';cfg=tmp_path/'watch.json'
    for at in ('2026-11-08T15:01:00+00:00','2026-11-09T06:01:00+00:00'):
        write(cfg,{'transition_only':True,'unrelated':'retained'})
        calendar.tick(root,cfg,p.instant(at))
        assert json.loads(cfg.read_text())==dict(transition_only=False,unrelated='retained')
    calendar.tick(root,cfg,p.DRAIN)
    assert json.loads(cfg.read_text())['transition_only'] is True
    calendar.tick(root,cfg,p.ADDENDUM)
    before={x.name:x.read_bytes() for x in root.glob('*.json')}
    assert calendar.tick(root,cfg,p.ADDENDUM+timedelta(hours=2))==[]
    assert before=={x.name:x.read_bytes() for x in root.glob('*.json')}
