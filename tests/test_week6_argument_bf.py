"""Constructed coverage for the within-person sealed argument replication."""
from pathlib import Path
import json
import sys

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCIENCE = ROOT/"runners/drive/sealed/week6-sm-science"
MI = ROOT/".agent-state/drive-20261115/full-week-extension/mi"
for path in reversed((SCIENCE, ROOT/"runners/drive/cards", MI, MI/"sealed-wrapper-mi4-nullfix-v4",
                      MI/"mi4-v1", MI/"statcore-v1", MI/"statcore-v2")):
    sys.path.insert(0, str(path))

import argument_bank as bank
import argument_panel as panel
import mi_source_contract_v1 as contract
from week6_sealed_support_v1 import SealedFailure, write_tables


def invented_day(person, day, resolution=None, feeling=1, argument=False):
    spec = contract.fields("M2")
    row = {"M2ID":person, spec["study_day"]:day, spec["weekday"]:1+(day-1)%7}
    row.update({x["occurrence"]:2 for x in spec["stressors"]})
    row.update({col:feeling for col in spec["negative"]})
    row.update(B2DF1=1 if argument else 2, B2DF1WC6=9 if resolution is None else resolution)
    return row


def test_exposure_only_and_adjacent_days():
    spec = contract.fields("M2")
    rows = [invented_day(1,1,1,argument=True), invented_day(1,2,2), invented_day(1,3,2,argument=True),
            invented_day(1,5,2,argument=True), invented_day(1,6), invented_day(1,7,7,argument=True),
            invented_day(1,8)]
    rows[4][spec["stressors"][2]["occurrence"]] = 8
    without = [{k:v for k,v in row.items() if k not in spec["negative"]} for row in rows]
    plan = panel.exposure(without)
    assert plan==panel.exposure(reversed(without))
    assert plan[1]=={(1,1):1,(1,5):2}
    assert plan[0][1]==(2,8)
    _, status = panel.support_summary(plan)
    assert status[0]==dict(group=1,n=1,resolved_days=1,unresolved_days=1,primary_support_met=0)
    with pytest.raises(SealedFailure):
        panel.exposure(without+[without[0]])


def test_person_baseline_and_same_day_rosters():
    spec = contract.fields("M2")
    rows = [invented_day(1,1,feeling=1), invented_day(1,2,1,1,True), invented_day(1,3,feeling=2),
            invented_day(1,4,2,3,True), invented_day(1,5,feeling=4)]
    # Only day one is stressor-free. The two next-day reports have other stressors.
    rows[2][spec["stressors"][1]["occurrence"]]=1
    rows[4][spec["stressors"][1]["occurrence"]]=1
    exposure = panel.exposure(rows)
    scores = panel.daily_scores(rows)
    assert panel.person_totals(exposure,scores)[1]==(1,1,3,1,0,1,2,1)
    rows[3][spec["negative"][3]]=8
    records=panel.person_totals(exposure,panel.daily_scores(rows))
    assert bank.contributors(records)[0][bank.WITHIN]=={1}
    assert not bank.contributors(records)[0][bank.SAME_DAY]
    rows[0][spec["negative"][1]]=9
    assert panel.person_totals(exposure,panel.daily_scores(rows))=={}


def invented_counts(n, disagree=False):
    arguments, stats = {}, {}
    for p in range(1,n+1):
        arguments[p,2]=1
        arguments[p,4]=2
        low = p<=n//2
        a,b = ((1,8) if low else (8,1)) if disagree else (1,1)
        resolved = 0 if low else 3
        stats[p]=(a*resolved,a,b*(resolved+1),b, .5,1, 1.,1)
    return ({},arguments),stats


def test_whole_family_draws_and_sign_disagreement():
    exp, stats=invented_counts(120,disagree=True)
    families={p:(p+1)//2 for p in stats}
    t=bank.run(exp,stats,dict(reversed(list(stats.items()))),families,dict(families))
    rows={r["comparison"]:r for r in t["argument_estimates"]}
    assert [(rows[i]["n"],rows[i]["resampling"],rows[i]["valid_draws"]) for i in (1,2,3)]==[(120,2,2000)]*3
    assert rows[1]["estimate"]==pytest.approx(1) and rows[1]["lower"]==pytest.approx(1)
    assert rows[2]["estimate"]<0 and rows[3]["estimate"]==pytest.approx(.5)
    assert t["argument_reading"]==[dict(n=120,support_met=1,sign_disagreement=1,decision=4)]


def test_support_floor_keeps_point_without_verdict(monkeypatch):
    monkeypatch.setattr(bank,"DRAWS",24)
    for n, met, decision in ((99,0,3),(100,1,1)):
        exposure,data=invented_counts(n)
        tables=bank.run(exposure,data,data,None,None)
        assert tables["argument_reading"]==[dict(n=n,support_met=met,sign_disagreement=0,decision=decision)]
        assert tables["argument_estimates"][0]["estimate"]==pytest.approx(1)
        assert tables["argument_estimates"][0]["resampling"]==1


def test_incomplete_family_link_and_small_rosters(tmp_path):
    exposure,data=invented_counts(40)
    families={p:(None if p==2 else p) for p in data}
    tables=bank.run(exposure,data,data,families,families)
    assert "argument_estimates" not in tables
    assert all(row["resampling"]==3 for row in tables["argument_point_only"])
    small, records=invented_counts(10)
    target=tmp_path/"out"
    target.mkdir()
    result=write_tables(target,dict(status=[dict(n=20)],**bank.run(small,records,records,None,None)))
    assert set(result["written"])=={"status.csv"}
    assert bank.released_sets(small,records)==[]


def test_one_sided_people_only_enter_description(monkeypatch):
    monkeypatch.setattr(bank,"DRAWS",24)
    exposure, data=invented_counts(110)
    for p in range(111,123):
        exposure[1][p,4]=2
        data[p]=(0,0,3,1,0,0,2,1)
    tables=bank.run(exposure,data,data,None,None)
    rows={r["comparison"]:r for r in tables["argument_estimates"]}
    assert rows[1]["n"]==rows[3]["n"]==110 and rows[2]["n"]==122
    assert tables["argument_report_people"]==[dict(n=110,resolution=1),dict(n=122,resolution=2)]

def test_main_sealed_entry_preserves_independent_returns(tmp_path, monkeypatch):
    import daily_fixture
    import json
    import science_entry
    from unittest.mock import Mock
    editions=json.loads((SCIENCE/"source_map.json").read_text("utf8"))
    directory=tmp_path/"artificial"
    registry=daily_fixture.construct(directory,editions)
    sibling=Mock(return_value={"sibling":[{"n":576,"qualified":1}]})
    monkeypatch.setattr(science_entry,"study",sibling)
    monkeypatch.setattr(science_entry.daily_bank,"run",lambda *args:{})
    monkeypatch.setattr(bank,"DRAWS",12)
    out=tmp_path/"ordinary"
    out.mkdir()
    tables=science_entry.run_joined({"M2":directory},"M2",registry,out)
    assert tables["sibling"][0]["n"]==576 and "argument_reading" in tables
    assert "M2ID" not in (out/"argument_support.csv").read_text("utf8")
    original=bank.released_sets
    def complementary_trap(exposure,data):
        return original(exposure,data)+[set(range(1,576))]
    monkeypatch.setattr(bank,"released_sets",complementary_trap)
    out=tmp_path/"suppressed"
    out.mkdir()
    tables=science_entry.run_joined({"M2":directory},"M2",registry,out)
    assert tables["sibling"][0]["n"]==576 and not any(k.startswith("argument_") for k in tables)
