"""Constructed bindings for Round 32. No participant data or trait source."""
import numpy as np
import pandas as pd
import pytest

from runners.drive.cards import week6_nt1_stage1_v1 as nt


def row(who, hour, ctx="1", level="1", date="2026-01-01", day="1"):
    clock=f"{date}T{hour}:00:00Z"
    return dict(id=who, day=day, created_esm=clock, ended_esm=clock, interaction=ctx,
                **{"status_"+name: level for name in nt.EVENTS})


def select(rows):
    return nt.select_lags(pd.DataFrame(rows, columns=nt.EXPOSURE_COLUMNS), {"NA"}, lambda: None)


def test_lag_and_support_ignore_outcomes_and_source_order():
    target=select([row("a","13","2"), row("b","12"), row("a","09",level="3"),
                   row("a","14"), row("b","17",level="2"), row("a","13",date="2026-01-02",day="2")])
    assert target.people==2
    assert target.current.tolist()==[0]
    assert target.events[0].tolist()==[0.]*6+[2.]*6
    assert target.hours.tolist()==[4.]
    assert target.counts["prior_criticised_prompts"]==target.counts["prior_criticised_people"]==1
    assert target.counts["over_four_hours"]==1 and target.counts["cross_day_pairs"]==1


def test_intervening_unknown_context_and_incomplete_prior_are_not_skipped():
    bad=row("b","09",level="2")
    bad["status_ignored"]="NA"
    target=select([row("a","09",level="2"),row("a","10",ctx="NA"),row("a","11"),
                   bad,row("b","10")])
    assert len(target.units)==0 and target.people==2
    assert target.counts["incomplete_event_pairs"]==1


def test_tied_or_unplaceable_clock_holds_person_and_preserves_roster():
    bad=row("b","12")
    bad["ended_esm"]="NA"
    target=select([row("a","09"),row("a","09"),row("b","09"),bad,row("c","08"),row("c","09")])
    assert target.people==3 and target.units.tolist()==[2]
    assert target.counts["ambiguous_clock_or_study_day_people"]==target.counts["unplaceable_clock_people"]==1


def test_support_reader_rejects_outcome_or_trait_columns():
    frame=pd.DataFrame([row("a","10")])
    with pytest.raises(ValueError,match="exposure-only"):
        nt.select_lags(frame.assign(int_angry="1"),{"NA"},lambda:None)


def test_support_counts_people_with_exposure_and_checks_both_floors():
    rows=[]
    for i in range(150):
        rows.extend(row(str(i),hour,level="3") for hour in ("08","09","10"))
    target=select(rows)
    assert target.summary()["supported"]
    assert not select(rows[:-1]).summary()["supported"]
    assert not select(rows[:-3]+[row("0","11",level="3"),row("0","12",level="3")]).summary()["supported"]


def test_occurrence_uses_current_context_and_preserves_unknown_negatives():
    x=select([row("a","08"),row("a","09"),row("a","10","2"),row("b","08"),row("b","09")])
    f=pd.DataFrame("1",index=range(5),columns=nt.FEELING_COLUMNS)
    f.loc[1,["int_angry","int_sad"]]=["3","NA"]
    f.loc[2,"int_sad"]="6"
    f.loc[4,"int_anxious"]="NA"
    y=nt.occurrence(f,x,{"NA"})
    np.testing.assert_equal(y,[1.,0.,np.nan])


def test_registered_gate_is_distinct_from_practical_size():
    assert nt.stage_two_gate(.2,.06,[.001,.16])
    assert not nt.stage_two_gate(.5,.14,[.02,.30])
    assert not nt.stage_two_gate(.2,.15,[0.,.25])
    assert not nt.stage_two_gate(0.,.15,[.01,.25])
    assert not nt.stage_two_gate(None,.15,None)


def test_coefficients_agree_for_independent_whole_person_fits_and_gap_thirds():
    rng=np.random.default_rng(20261120)
    units=np.repeat(np.arange(50),12)
    n=len(units)
    events=rng.normal(size=(n,12))
    gap=rng.uniform(.1,4,n)
    context=rng.integers(1,3,n)
    x=nt.Selection(50,np.arange(n),units,context,gap,events,
                   dict(prior_criticised_prompts=n,prior_criticised_people=50))
    y=(rng.logistic(size=n)<(.3*events[:,0]+.22*events[:,6])).astype(float)
    weights=rng.integers(0,3,50)
    mask=np.ones(n,dtype=bool)
    estimate=nt.coefficients(x,y,mask,weights)
    replay=nt.coefficients(x,y,mask,weights,verify=True)
    assert all(value is not None for value in estimate)
    np.testing.assert_allclose(estimate,replay,rtol=1e-7,atol=1e-8)
    assert len(nt.gap_description(x,y)["thirds"])==3
    assert nt.coefficients(x,np.zeros(n),mask,weights)==(None,None)


def test_empty_or_ineligible_source_stops_before_feelings_and_replays_support(tmp_path, monkeypatch):
    import hashlib
    import json
    from runners.drive.cards import week6_diary_rows_v2 as entry
    def save(name, value):
        path=tmp_path/name
        path.write_text(json.dumps(value),encoding="utf8")
        return {"path":str(path),"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
    table=tmp_path/"source.tsv"
    source_frame=pd.DataFrame([row("a","09"),row("a","10",level="4")])
    for col in nt.FEELING_COLUMNS:
        source_frame[col]="invalid_outcome_if_read"
    source_frame.to_csv(table,sep="\t",index=False)
    pin={"sha256":hashlib.sha256(table.read_bytes()).hexdigest(),"bytes":table.stat().st_size}
    names=nt.EXPOSURE_COLUMNS+nt.FEELING_COLUMNS
    book=save("book.json",{"dataset_id":"0057","features":[{"name":x} for x in names]})
    monkeypatch.setitem(nt.common.CODEBOOK_HASHES,"0057",book["sha256"])
    registration=save("rows.json",{"member":"0057","operator":"NT1-stage-1",
        "rows":[{"id":"NT1.d","metric":"B2","bar":.1,"draws":2000},
                {"id":"NT1.e","metric":"B2_by_gap_third","draws":0}],
        "support":{"prior_criticised_prompts":300,"prior_criticised_people":150}})
    panel=dict(card="NT1.d",member="0057",source_pin=pin,missing_tokens=["NA"],
               draws=2000,source_seed=entry.draws.SOURCE_SEEDS["0057"])
    review=save("admit.json",dict(schema="NT1_STAGE_ONE_SOURCE_V1",owner_reviewed=True,
        panel_config=panel,source_path=str(table),source_layout=save("schema.json",{"files":[dict(pin,columns=[{"name":x} for x in names])]}),
        rights="constructed",authority=save("authority.json",{"fixture":True}),codebook=book,rows_table=registration))
    inputs=dict(source_path=str(table),source_admission_path=review["path"],source_admission_sha256=review["sha256"])
    config=dict(panel_config=panel,max_new_draws=100,max_wall_seconds=50)
    output=tmp_path/"output"
    assert entry.execute(output,inputs,config)["draw_count"]==0
    assert entry.verify(output,inputs,config)["verified"]
    assert not (output/"NT1_E_DESCRIPTION.json").exists()
    receipts=list(output.glob("*.receipt.json"))
    assert len(receipts)==1
    receipts[0].write_text('{"sha256":"wrong"}',encoding="utf8")
    with pytest.raises(ValueError,match="digest"):
        entry.verify(output,inputs,config)
