"""Constructed qualification of the original parent-diary reader and registered fits."""
import hashlib

import numpy as np
import pandas as pd
import pytest

from runners.drive.cards import week6_lb3_panel_v1 as panel
from runners.drive.cards import week6_lb3_source_v1 as source
from runners.drive.cards import week6_lb3_run_v1 as native
from runners.drive.cards import week6_lb_bank_v1 as bank
from runners.drive.cards.week6_ld_draws_v1 import RequestedYield, load_blocks


def world():
    rng = np.random.default_rng(7821)
    people, days = 34, 18
    n = people * days
    data = {"id":np.repeat(np.arange(people),days), "day":np.tile(np.arange(1,days+1),people)}
    for item in source.STRESSORS:
        data[item] = rng.binomial(1,.23,n)
    for item in source.RATINGS:
        data[item] = rng.integers(1,8,n)
    data["time_with_child_hours"] = rng.integers(0,10,n)
    data["time_with_child_minutes"] = rng.choice([0,15,30,45],n)
    blocked = .5*(data["told_what_to_do"]+data["against_own_will"])-4.
    threat = np.maximum(data["stressor_health"],data["stressor_financial"])
    distressed = np.mean([data[k] for k in source.CHILD_DISTRESS],axis=0)-4.
    def rating(value):
        return np.clip(np.rint(value+rng.normal(0,.48,n)),1,7).astype(int)
    data["parent_angry"] = rating(4+.9*blocked)
    data["parent_afraid"] = rating(3+2.1*threat)
    data["parent_worried"] = rating(3+1.5*threat+.9*distressed)
    data["parent_sad"] = rating(4+.8*(data["excluded_ostracized"]-4))
    data["parenting_fun"] = rating(4-.8*(data["parent_afraid"]-4)+.18*(data["parent_sad"]-4))
    return pd.DataFrame(data).astype(str)


def prepared(frame=None):
    return panel.build(source.prepare_frame(world() if frame is None else frame, ["","NA"]))


def evaluate(data):
    return panel.evaluate(data,None,lambda: None)


def test_roster_exclusions_and_duplicate_days():
    frame = world()
    frame.loc[0,"day"] = "NA"
    frame.loc[1,"id"] = ""
    frame.loc[2,"day"] = frame.loc[3,"day"]
    data = source.prepare_frame(frame,["","NA"])
    assert data.people==34
    assert data.counts["missing_identity"]==1 and data.counts["missing_day"]==1
    assert data.counts["duplicate_parent_day_rows"]==2
    assert data.counts["eligible_parent_days"]==len(frame)-4


def test_composite_missingness_and_time():
    frame = world()
    frame.loc[0,["stressor_health","stressor_financial"]]=["1","NA"]
    frame.loc[1,["stressor_health","stressor_financial"]]=["0","NA"]
    frame.loc[2,"child_worried"]=""
    frame.loc[3,["time_with_child_hours","time_with_child_minutes"]]=["1.5","15"]
    frame.loc[4,"time_with_child_minutes"]=""
    frame.loc[5,"time_with_child_hours"]="25"
    data=source.prepare_frame(frame,["","NA"])
    assert data.values["health_or_financial"][0]==1 and np.isnan(data.values["health_or_financial"][1])
    assert np.isnan(data.values["child_distress"][2])
    assert data.values["time_minutes"][3]==105
    assert np.isnan(data.values["time_minutes"][4:6]).all()
    assert (data.counts["incomplete_time_components"],data.counts["invalid_time_duration"])==(1,1)


def test_undocumented_coding_refused():
    frame=world()
    frame.loc[0,"parent_afraid"]="8"
    with pytest.raises(ValueError):
        source.prepare_frame(frame,["NA"])
    frame.loc[0,"parent_afraid"]="4"
    frame.loc[0,"stressor_health"]="2"
    with pytest.raises(ValueError):
        source.prepare_frame(frame,["NA"])


def test_tables_and_registry_cover_original_design():
    p=prepared()
    assert list(panel.COMPARE)==["21","22","23","24","25"]
    assert len([k for k in p.specs if k.startswith("events_")])==4*16
    assert len([k for k in p.specs if k.startswith("care_")])==11*2
    assert p.specs["row/25"]["direction"]=="negative"
    assert all(p.specs["row/"+s]["bar"]==.05 for s in panel.COMPARE)


def test_planted_positive_contrasts_and_negative_brake():
    values=evaluate(prepared())
    assert all(values["row/"+key]>.1 for key in ("21","22","23","24"))
    assert values["row/25"]<-.1


def test_identical_feelings_cancel_and_collinear_brake_is_unsupported():
    frame=world()
    frame["parent_sad"]=frame["parent_afraid"]
    frame["parent_angry"]=frame["parent_afraid"]
    result=evaluate(prepared(frame))
    assert result["row/21"]==0 and result["row/23"]==0
    assert result["row/25"] is None


def test_each_contrast_keeps_its_paired_rows():
    frame=world()
    frame.loc[0,"parent_angry"]="NA"
    frame.loc[1,"child_sad"]="NA"
    p=prepared(frame)
    assert p.specs["row/24"]["rows"]==len(frame)-2
    assert p.specs["row/21"]["rows"]==len(frame)-1
    assert p.specs["row/25"]["rows"]==len(frame)-1
    assert p.specs["care_parent_worried/parent_worried/child_distress"]["rows"]==len(frame)-1


def test_source_hash_and_original_format(tmp_path):
    frame=world()
    f=tmp_path/"diary.tsv"
    frame.to_csv(f,index=False,sep="\t")
    pin={"sha256":hashlib.sha256(f.read_bytes()).hexdigest(),"bytes":f.stat().st_size}
    data=source.load(f,pin,["","NA"],lambda: None)
    assert data.people==34 and data.counts["source_rows"]==len(frame)
    with f.open("ab") as stream:
        stream.write(b"\n")
    with pytest.raises(ValueError,match="source pin"):
        source.load(f,pin,["","NA"],lambda: None)


def test_independent_replay_of_nonuniform_person_weights():
    p=prepared()
    w=np.ones(p.people,dtype=int)
    w[0],w[1]=2,0
    fit=panel.evaluate(p,w,lambda: None)
    other=panel.evaluate(p,w,lambda: None,verify=True)
    assert list(fit)==list(other)
    for key,val in fit.items():
        if val is None: assert other[key] is None
        else: assert val==pytest.approx(other[key],abs=1e-8,rel=0)
    with pytest.raises(ValueError,match="lost a parent"):
        panel.evaluate(p,np.full(p.people,2),lambda: None)


def test_missing_support_is_not_a_zero_effect():
    frame=world()
    frame["stressor_financial"]="0"
    p=prepared(frame)
    values=evaluate(p)
    assert values["row/21"] is None and values["row/23"] is None
    assert values["row/22"] is not None and values["row/24"] is not None
    assert "row/21" in p.metadata["point_dispositions"]


def test_counted_draw_block_resumes_without_replacement(tmp_path):
    p=prepared()
    opts=dict(member="0072",source_digest="1"*64,seed=source.SOURCE_SEED,guard=lambda: None,
              verify=False,execute_dir=tmp_path,progress=lambda count,elapsed: None)
    for _ in range(2):
        with pytest.raises(RequestedYield,match="draw quantum"):
            bank.run(tmp_path,panel,p,limit=2,**opts)
    keys=sorted(p.specs)
    assert len(load_blocks(tmp_path,keys))==4


def test_wrong_source_member_or_native_draw_contract_is_refused():
    with pytest.raises(ValueError,match="Unregistered parent-diary"):
        panel.prepare("0060","unused",{},["NA"],lambda: None)
    with pytest.raises(ValueError):
        native.validate({},{"panel_config":{"member":"0060","card":"LB3","draws":2000},
                             "max_new_draws":100,"max_wall_seconds":600})
