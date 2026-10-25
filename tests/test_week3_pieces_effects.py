import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from runners.drive.cards import week3_pieces_effects as w
from runners.drive.cards import week3_pieces_input as prep
from runners.drive.cards.timing_census import read,write,filehash
from runners.drive.cards.timing_p6 import gzread
from runners.drive.timeline import rebuild
from tests.test_week3_pieces_input import fixture_events
from tests.test_week3_pieces_coverage import prepared


def test_future_windows_full_censored_and_absent_acceptance():
    events,menus,_=fixture_events()
    timeline=rebuild(events,menus)
    clocks=w.checked_clock(events)
    occurrences=[dict(source_ordinal=i,seconds=clocks[i],session="s",writer="w",side="test",symbols=["a","b","c"],start=0,stop=3) for i in (1,len(events)-1)]
    rows=w.effect_windows(events,timeline,occurrences)
    assert rows[0]["full_followup"] and rows[0]["net_characters"]>0
    assert rows[0]["sentence_completed"]==1
    assert rows[0]["accepted_original_utf16"]==3
    assert rows[0]["accepted_surviving_utf16"]==1
    assert rows[0]["accepted_retained_share"]==pytest.approx(1/3)
    assert not rows[1]["full_followup"] and rows[1]["net_characters"] is None
    assert rows[1]["accepted_retained_share"] is None


def effect_records():
    records=[]
    for side in ("discovery","test"):
        for writer in range(6):
            for occurrence in range(20):
                label=occurrence%2
                row=dict(side=side,writer=f"{side}-{writer}",session=str(writer),source_ordinal=occurrence,symbols=["a","b",str(label)])
                row.update({k:float(label) for k in w.EFFECTS})
                records.append(row)
    return records


def test_effect_consistency_label_null_and_constant_effect():
    rows=effect_records()
    result=w.consistency(rows)
    assert result["net_characters"]["variance_explained"]==1
    assert result["net_characters"]["permutation_p"]<.05
    for row in rows:
        row["net_characters"]=7.
    constant=w.consistency(rows)
    assert constant["net_characters"]["variance_explained"]==0
    assert constant["net_characters"]["permutation_p"]==1


def test_classes_use_only_discovery_and_report_missing_effects():
    rows=effect_records()
    result=w.classes(rows)
    assert result["state"]=="fitted" and len(result["assignments"])==2
    for row in rows:
        if row["side"]=="test":
            row.update({k:123456. for k in w.EFFECTS})
    assert w.classes(rows)==result
    for row in rows:
        row["accepted_retained_share"]=None
    assert w.classes(rows)["state"]=="unsupported"


def effect_inputs(tmp_path):
    inputs=prepared(tmp_path)
    split=read(inputs["writer_split"])["writers"]
    edges=read(inputs["bin_edges"])
    index_path=Path(inputs["preparation_index"])
    occurrences=[]
    for item in read(index_path):
        row=gzread(index_path.parent/item["file"])
        action=row["actions"][2]
        occurrences.append(dict(session=row["session"],writer=row["writer"],side=split[row["writer"]],
            start=0,stop=3,symbols=prep.symbols(row["actions"],edges)[:3],
            source_ordinal=action["source_ordinals"][-1],seconds=action["seconds"]))
    cov=tmp_path/"coverage"
    write(cov/"PLAN.json",dict(inputs=inputs))
    write(cov/"output/WB1_COVERAGE_RESULT.json",dict(status="component_complete",full_card_complete=False,card="WB1-coverage",
        whole=dict(occurrences=occurrences),route=dict(coverage_gate_passed=False,next="WB1b")))
    write(cov/"COMPLETE.json",dict(status="COMPLETE",fresh_process_verified=True,outputs={p.relative_to(cov).as_posix():filehash(p) for p in cov.rglob("*") if p.is_file()}))
    root=tmp_path/"source"
    source_inputs=dict(repo_root=str(root.resolve()),foundation_complete=str((root/"foundation/COMPLETE.json").resolve()),
        foundation_plan=str((root/"foundation/PLAN.json").resolve()),session_index=str((root/"foundation/SESSION_INDEX.json").resolve()),
        raw_roster=str((root/"ROSTER.json").resolve()),prepared_sessions=str((root/"SESSIONS.json").resolve()))
    write(tmp_path/"source_inputs.json",source_inputs)
    write(tmp_path/"fake_model.json",dict(constructed=True))
    write(tmp_path/"fake_model_complete.json",dict(constructed=True))
    return dict(coverage_complete=str(cov/"COMPLETE.json"),coverage_result=str(cov/"output/WB1_COVERAGE_RESULT.json"),
        source_inputs=str(tmp_path/"source_inputs.json"),content_model=str(tmp_path/"fake_model.json"),content_complete=str(tmp_path/"fake_model_complete.json"))


def test_serialized_effects_fresh_source_replay_and_mutation(tmp_path):
    inputs=effect_inputs(tmp_path)
    config=dict(mode="constructed",permutation_draws=10,seed=20261026)
    output=tmp_path/"effects"
    result=w.execute(output,inputs,config)
    assert result["full_card_complete"] and not result["scientific_admission"]
    assert result["occurrences"]==8
    assert w.verify(output,inputs,config)["verified"]
    manifest=tmp_path/"verify.json"
    write(manifest,dict(output=str(output),inputs=inputs,config=config))
    script="import json,sys;from pathlib import Path;from runners.drive.cards.week3_pieces_effects import verify;x=json.load(open(sys.argv[1]));assert verify(Path(x['output']),x['inputs'],x['config'])['verified']"
    subprocess.run([sys.executable,"-X","utf8","-B","-c",script,str(manifest)],check=True,timeout=60,env=dict(os.environ,PYTHONHASHSEED="94",OMP_NUM_THREADS="2",OPENBLAS_NUM_THREADS="2",MKL_NUM_THREADS="2"))
    rows=read(output/"WB1_EFFECT_ROWS.json")
    rows[0]["net_characters"]=-999
    (output/"WB1_EFFECT_ROWS.json").write_text(json.dumps(rows),encoding="utf-8")
    with pytest.raises(ValueError,match="full source replay"):
        w.verify(output,inputs,config)
