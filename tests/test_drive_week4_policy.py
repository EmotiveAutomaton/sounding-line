"""Week 4 boundaries preserve the old freeze, accounting and shared leases."""
from datetime import timedelta
import json
import pytest
from runners.drive.cards import week3_policy as old, week4_policy as p
from runners.drive import calendar_20261102_week4 as c, budget_week4 as b

def plan():
    return dict(campaign='S15-WEEK4', original_cpu_ceiling_seconds=3600,
        prior_cpu_seconds_charged=120,max_cpu_seconds=3600,max_wall_seconds=7200,
        forecast_cpu_seconds=600,projected_peak_ram_GiB=3,
        premortem=dict(case_and_check='Known-answer source replay.',smaller_route='Whole-unit sample; no partial result.'))

def resources():
    return dict(ram_available_GiB=16,commit_headroom_GiB=24,disk_free_GiB=100)

def test_new_handoff_and_old_attempts_remain_frozen(tmp_path):
    at=p.OPEN+timedelta(seconds=1)
    assert p.admission(plan(),at,resources(),tmp_path/'absent',24)['slots']==4
    with pytest.raises(RuntimeError,match='no-new-start'): old.admission(plan(),at,resources(),tmp_path/'absent',24)
    for at in (p.OPEN-timedelta(microseconds=1),p.FREEZE,p.DRAIN):
        with pytest.raises(RuntimeError,match='no-new-start'): p.admission(plan(),at,resources(),tmp_path/'absent',24)

def test_premortem_cost_and_resources_refuse(tmp_path):
    at=p.OPEN+timedelta(seconds=1)
    for change in (dict(premortem={}),dict(campaign='S15-WEEK3'),dict(prior_cpu_seconds_charged=4000)):
        with pytest.raises(ValueError): p.admission(dict(plan(),**change),at,resources(),tmp_path/'absent',24)
    with pytest.raises(RuntimeError,match='resource'): p.admission(plan(),at,dict(resources(),disk_free_GiB=19),tmp_path/'absent',24)

def test_shared_reservation_counts_and_expires(tmp_path):
    lock=tmp_path/'lock'
    lock.write_text(json.dumps(dict(created_at=p.OPEN.isoformat(),expires_at=(p.OPEN+timedelta(days=2)).isoformat())))
    assert p.admission(plan(),p.OPEN+timedelta(hours=1),resources(),lock,24)['slots']==3
    assert p.admission(plan(),p.OPEN+timedelta(hours=7),resources(),lock,24)['slots']==4

def test_calendar_and_paid_pacific_boundaries(tmp_path):
    config=tmp_path/'watch.json';config.write_text(json.dumps(dict(transition_only=False,health_interval_seconds=21600)))
    assert 'FINAL_DIGEST_AND_START_FREEZE' not in c.due_names(p.FREEZE-timedelta(microseconds=1),set())
    c.tick(tmp_path,config,p.DRAIN)
    assert json.loads(config.read_text())==dict(transition_only=True,health_interval_seconds=21600)
    assert not (tmp_path/'DRAIN_ADDENDUM_DUE.json').exists()
    assert b.CUTOFF==p.PAID_CUTOFF.timestamp()
    assert sum(b.CAPS.values())==900

def approval():
    return dict(campaign=b.CAMPAIGN,first_paid_cents=1000,nodes=list(b.CAPS),
        statement_verbatim='Explicit approval',packet_sha256='a'*64)

def test_each_node_cap_unknown_duplicate_and_cutoff():
    for node,cap in b.CAPS.items():
        b.guard([],node,'new',cap,approval(),b.CUTOFF-1)
        with pytest.raises(ValueError,match='Node cap'): b.guard([],node,'new',cap+1,approval(),b.CUTOFF-1)
    oldrow=dict(campaign_id=b.CAMPAIGN,invocation='old',node='PROC',booked_cents=200,reserved_cents=200,status='UNKNOWN')
    with pytest.raises(ValueError,match='Reconcile'): b.guard([oldrow],'PLAN','new',1,approval(),b.CUTOFF-1)
    settled=b.reconcile_row(oldrow,3,'f'*64)
    b.guard([settled],'PLAN','new',150,approval(),b.CUTOFF-1)
    with pytest.raises(ValueError,match='Duplicate'): b.guard([settled],'PROC','old',1,approval(),b.CUTOFF-1)
    with pytest.raises(ValueError,match='cutoff'): b.guard([],'PROC','new',1,approval(),b.CUTOFF)
    with pytest.raises(ValueError,match='approval'): b.guard([],'PROC','new',1,{},b.CUTOFF-1)
