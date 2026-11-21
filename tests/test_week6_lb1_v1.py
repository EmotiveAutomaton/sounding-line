"""Constructed original-format source, registered contrasts and indexed-bank checks."""
import numpy as np
import pandas as pd
import pytest
from hashlib import sha256

from runners.drive.cards import week6_lb1_source_v1 as src
from runners.drive.cards import week6_lb1_panel_v1 as panel
from runners.drive.cards import week6_lb1_run_v1 as runtime
from runners.drive.cards import week6_lb_bank_v1 as bank
from runners.drive.cards.week6_lattice_diary_v1 import person_draw
from runners.drive.cards.week6_ld_draws_v1 import RequestedYield, load_blocks
from runners.drive.cards.batch_runtime import read

MISSING = ["","NA","NaN","nan"]


def frame(people=26, visits=21):
    rng=np.random.default_rng(118811)
    n=people*visits
    v=np.tile(np.arange(visits),people)
    d={"id":np.repeat(["p"+str(i).zfill(3) for i in range(people)],visits),
       "day":v//3+1,"hour":8+4*(v%3),"minute":np.zeros(n,dtype=int)}
    for fields,lo,hi in ((src.FIVE_POINT,1,6),(src.THREE_POINT,1,4),(src.BINARY,0,2)):
        for k in fields:
            d[k]=rng.integers(lo,hi,n)
    # The two planted comparisons use independent control feelings.
    d["curious"]=np.clip(2*d["intellect"]-1+rng.integers(-1,2,n),1,5)
    arg=np.maximum(d["argument_family"],d["argument_friend"])
    d["angry"]=np.clip(1+2*arg+rng.integers(-1,3,n),1,5)
    # Positive argument cases need some floor responses for a finite logit.
    d["angry"][rng.random(n)<.10]=1
    return pd.DataFrame(d).astype(str)


def nop():
    return None


def test_full_earlier_roster_and_two_planted_contrasts():
    data=src.prepare_frame(frame(),MISSING)
    assert data.people==26 and len(data.earlier)==26*14
    built=panel.build(data)
    results=panel.evaluate(built,None,nop)
    assert results["row/11"]>.60 and results["row/16"]>.45
    assert {k for k in results if k.startswith("row/")}=={"row/"+str(i) for i in range(11,18)}
    assert all(results["row/"+str(i)] is not None for i in range(11,18))


def test_same_outcomes_give_exact_null_on_common_rows():
    f=frame()
    f["content"]=f["curious"]
    f["excited"]=f["curious"]
    f["afraid"]=f["angry"]
    result=panel.evaluate(panel.build(src.prepare_frame(f,MISSING)),None,nop)
    assert [result["row/"+r] for r in ("11","15","16","17")]==[0.,0.,0.,0.]


def test_ambiguous_clocks_preserve_valid_neighbours_without_bridging():
    units=np.array([0]*5+[1]*2+[2]*2)
    days=np.array([1.]*7+[1.,np.nan])
    hours=np.array([10.,8.,8.,9.,11.,10.,np.nan,10.,13.])
    early,late,counts=src.ordered_pairs(units,days,hours,np.zeros(9))
    assert list(zip(early,late))==[(3,0),(0,4)]
    assert counts["people_excluded_unknown_day"]==1 and counts["days_with_missing_clock"]==1
    assert counts["transitions_touching_ties"]==2 and counts["adjacent_same_day_pairs"]==2


def test_missing_prior_rating_does_not_create_a_new_pair():
    f=frame()
    baseline=panel.build(src.prepare_frame(f,MISSING))
    f.loc[1,"proud"]="NA"
    modified=panel.build(src.prepare_frame(f,MISSING))
    assert modified.metadata["panels"]["opportunity_lag"]["rows"]==baseline.metadata["panels"]["opportunity_lag"]["rows"]-1
    assert modified.metadata["panels"]["thinking"]==baseline.metadata["panels"]["thinking"]


def test_argument_three_valued_or_and_row_specific_missingness():
    f=frame()
    f.loc[:3,"argument_family"]=["1","0","NA","0"]
    f.loc[:3,"argument_friend"]=["NA","NA","0","0"]
    f.loc[8,"content"]="NA"
    data=src.prepare_frame(f,MISSING)
    np.testing.assert_equal(data.values["argument"][:4],[1.,np.nan,np.nan,0.])
    built=panel.build(data)
    assert built.panels["argument"].units.size==len(f)-2
    assert built.panels["thinking"].units.size==len(f)-1
    assert built.panels["competence"].units.size==len(f)


def test_checked_scales_and_source_bytes(tmp_path):
    f=frame()
    path=tmp_path/"fixture.tsv"
    f.to_csv(path,sep="\t",index=False)
    pin={"bytes":path.stat().st_size,"sha256":sha256(path.read_bytes()).hexdigest()}
    assert src.load(path,pin,MISSING,nop).people==26
    with pytest.raises(ValueError,match="pin"):
        src.load(path,dict(pin,sha256="0"*64),MISSING,nop)
    for field,coded in [("mating","4"),("bored_schoolwork","2"),("angry","2.5"),("minute","60")]:
        bad=f.copy()
        bad.loc[0,field]=coded
        with pytest.raises(ValueError,match=field):
            src.prepare_frame(bad,MISSING)


def test_reference_solver_agrees_on_each_registered_and_diagnostic_cell():
    data=panel.build(src.prepare_frame(frame(),MISSING))
    weights=person_draw(np.arange(data.people),source_seed=src.SOURCE_SEED,draw=19)
    left=panel.evaluate(data,weights,nop)
    right=panel.evaluate(data,weights,nop,verify=True)
    assert all(v is not None for v in left.values())
    np.testing.assert_allclose(list(left.values()),[right[k] for k in left],atol=1.e-7,rtol=1.e-7)


def test_whole_person_replication_and_draw_conservation():
    f=frame()
    base=panel.build(src.prepare_frame(f,MISSING))
    masses=np.ones(base.people,dtype=int)
    masses[0],masses[1]=2,0
    copy=f.loc[f.id=="p000"].copy()
    copy["id"]="copy"
    literal=panel.build(src.prepare_frame(pd.concat([f.loc[f.id!="p001"],copy],ignore_index=True),MISSING))
    weighted=panel.evaluate(base,masses,nop)
    repeated=panel.evaluate(literal,None,nop)
    np.testing.assert_allclose(list(weighted.values()),[repeated[k] for k in weighted],atol=1.e-7,rtol=1.e-7)
    with pytest.raises(ValueError,match="roster"):
        panel.evaluate(base,masses+1,nop)


def test_shifted_floor_same_binary_occurrence():
    f=frame()
    other=f.copy()
    nonfloor=other.angry!="1"
    other.loc[nonfloor,"angry"]="5"
    a=panel.evaluate(panel.build(src.prepare_frame(f,MISSING)),None,nop)
    b=panel.evaluate(panel.build(src.prepare_frame(other,MISSING)),None,nop)
    assert abs(a["row/17"]-b["row/17"])<1.e-10
    assert abs(a["argument/L/angry/argument"]-b["argument/L/angry/argument"])>.01


def test_separation_and_constant_predictors_stay_unidentified():
    f=frame()
    f["sociality"]="2"
    f["afraid"]="1"
    pred=panel.evaluate(panel.build(src.prepare_frame(f,MISSING)),None,nop)
    assert all(pred["row/"+s] is None for s in ["12","13","14","15","16","17"])
    assert pred["row/11"] is not None

    separated=frame()
    argument=(separated.argument_family=="1") | (separated.argument_friend=="1")
    separated["angry"]=np.where(argument,"5","1")
    assert panel.evaluate(panel.build(src.prepare_frame(separated,MISSING)),None,nop)["row/17"] is None


def test_two_point_monotone_purpose_reversal():
    data=src.prepare_frame(frame(),MISSING)
    np.testing.assert_equal(data.values["low_purpose"]+data.values["purposeful"],6.)
    built=panel.build(data)
    assert built.panels["opportunity_lag"].predictors==("prior_proud","prior_bored_schoolwork","prior_low_purpose","prior_mating","sociality")


def test_partial_bank_appends_and_preserves_member_identity(tmp_path):
    data=panel.build(src.prepare_frame(frame(16,15),MISSING))
    params=dict(member="0060",source_digest="a"*64,seed=src.SOURCE_SEED,guard=nop,verify=False,
                execute_dir=tmp_path,limit=2,progress=lambda n,t: None)
    with pytest.raises(RequestedYield,match="draw quantum"):
        bank.run(tmp_path,panel,data,**params)
    keys=sorted(data.specs)
    first=load_blocks(tmp_path,keys)
    with pytest.raises(RequestedYield,match="draw quantum"):
        bank.run(tmp_path,panel,data,**params)
    second=load_blocks(tmp_path,keys)
    assert len(first)==2 and second[:2]==first and len(second)==4
    assert read(tmp_path/"SCHEMA.json")["people"]==16
    with pytest.raises(ValueError,match="schema"):
        bank.run(tmp_path,panel,data,**dict(params,source_digest="b"*64))


def test_phase_refuses_unreviewed_source_inputs():
    inputs={"source_path":"fixture","source_admission_path":"missing","source_admission_sha256":"0"*64}
    cfg={"card":"LB1","member":"0060","source_pin":{"bytes":2473213,"sha256":src.SOURCE_SHA256},
         "source_seed":src.SOURCE_SEED,"draws":2000,"missing_tokens":MISSING}
    deadline={"panel_config":dict(cfg,member="0057"),"max_new_draws":100,"max_wall_seconds":600}
    with pytest.raises(ValueError,match="Unregistered"):
        runtime.validate(inputs,deadline)
