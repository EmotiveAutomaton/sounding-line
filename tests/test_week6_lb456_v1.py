"""Known answers and support checks for the four original-format diary cohorts."""
import numpy as np
import pandas as pd
import pytest

from runners.drive.cards import week6_lb456_source_v1 as source
from runners.drive.cards import week6_lb456_panel_v1 as panel
from runners.drive.cards import week6_lb456_run_v1 as runner


def frame(member):
    spec = source.MEMBERS[member]
    rng = np.random.default_rng(7063)
    n = 24 * 12
    fields = {"id": np.repeat(np.arange(24),12).astype(str)}
    for name in spec.ratings:
        low, high = (0,4) if name=="interaction_frequency" else (spec.low,spec.high)
        fields[name] = rng.integers(low, high+1, n).astype(str)
    return pd.DataFrame(fields)


def make(member, df):
    return panel.build(member, source.project(member, df, ["","NA"]))


def calc(sample, weight=None, verify=False):
    return panel.evaluate(sample, weight, lambda: None, verify=verify)


@pytest.mark.parametrize("member",sorted(source.MEMBERS))
def test_weighted_independent_replay(member):
    data = make(member, frame(member))
    mass = np.resize([0,2,1], data.people)
    first, second = calc(data,mass), calc(data,mass,True)
    assert all(v is not None and abs(v-second[k])<1e-9 for k,v in first.items())


def test_expectedness_signed():
    f=frame("0070")
    f["silly"]=(100-f.expected.astype(int)).astype(str)
    assert calc(make("0070",f))["row/26"]==pytest.approx(-1)


def test_work_known_answer():
    f=frame("0063")
    f["inspired"]=f.good_at_this
    r=calc(make("0063",f))
    assert r["row/32"]==pytest.approx(1) and abs(r["row/33"])<1e-10


def test_stress_known_answer():
    f=frame("0076")
    f["interaction_playful"]=(6-f.stressed.astype(int)).astype(str)
    assert calc(make("0076",f))["row/29"]==pytest.approx(-1)


def test_equal_fear_and_anger():
    f=frame("0064")
    for name in (*source.FEAR,*source.ANGER):
        f[name]=f["afraid"]
    assert calc(make("0064",f))["row/30"]==pytest.approx(1)


def test_scorn_difference_exact_null():
    f=frame("0064")
    for left,right in zip(source.SCORN,source.ANGER):
        f[left]=f[right]
    assert abs(calc(make("0064",f))["row/31"])<1e-10


def test_category_table_uses_distinct_report_denominators():
    f=frame("0076")
    f["interaction_frequency"]="0"
    f.loc[0,"interaction_meaningful"]="NA"
    data=make("0076",f)
    values=calc(data)
    assert data.specs["frequency/0/interaction_meaningful"]["rows"]==len(f)-1
    assert values["frequency/0/interaction_playful"]==pytest.approx(f.interaction_playful.astype(float).mean())
    assert values["frequency/4/interaction_playful"] is None


def test_complete_case_support_preserves_source_roster():
    f=frame("0063")
    f.loc[f.id=="1","appreciated"]="NA"
    data=make("0063",f)
    assert data.people==24 and data.metadata["matched"]=={"rows":276,"people":23}


def test_constant_predictor_refuses_fit():
    f=frame("0070")
    f["expected"]="44"
    data=make("0070",f)
    assert calc(data)["row/26"] is None and calc(data,verify=True)["row/28"] is None


def test_missing_fear_item_cannot_shorten_scale():
    f=frame("0064")
    f.loc[0,"jittery"]="NA"
    assert make("0064",f).metadata["matched"]["rows"]==len(f)-1


def test_changed_pin_and_outside_scale():
    from pathlib import Path
    with pytest.raises(ValueError):
        source.load("0064",Path("absent.tsv"),{},["","NA"],lambda:None)
    f=frame("0063")
    f.loc[0,"doubt"]="8"
    with pytest.raises(ValueError):
        make("0063",f)


def test_runtime_rejects_cross_card():
    cfg=dict(card="LB5",member="0063",draws=2000,missing_tokens=["","NA"],
             source_seed=source.MEMBERS["0063"].seed,source_pin=source.MEMBERS["0063"].pin)
    with pytest.raises(ValueError):
        runner.validate(dict(source_path="",source_admission_path="",source_admission_sha256=""),
                        dict(panel_config=cfg,max_new_draws=100,max_wall_seconds=600))
