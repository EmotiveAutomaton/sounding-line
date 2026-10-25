import json
from pathlib import Path
import subprocess
import sys

import pytest

from runners.drive.cards import week3_pieces_input as original
from runners.drive.cards import week3_pieces_input_recovery as recovery
from runners.drive.cards.timing_census import read,write,filehash
from runners.drive.timeline import rebuild
from tests.test_week3_pieces_input import fixture_events,fixture_inputs


def test_epoch_clock_reproduces_p2_exactly_without_relaxing_tolerance():
    events,menus,_=fixture_events()
    epoch=1615189114123
    for event in events:
        event["eventTimestamp"]+=epoch
    # Exact corpus failure shape: this subtraction loses >1e-7 seconds when
    # its two epoch operands have already been divided by 1000.
    events[2]["eventTimestamp"]=epoch+28906
    # Keep the isolated known clock case separate from the chronological fixture.
    sample=[events[0],events[2]]
    assert abs(original.checked_clock(sample)[1]-28.906)>1e-7
    assert recovery.checked_clock(sample)[1]==28.906
    events,menus,_=fixture_events()
    for event in events:
        event["eventTimestamp"]+=epoch
    timeline=rebuild(events,menus)
    with recovery.canonical_clock():
        result=original.extract_session(events,timeline)
    assert result["raw_deltas"]==len(timeline["deltas"])
    timeline["deltas"][0]["seconds"]+=.001
    with recovery.canonical_clock(),pytest.raises(ValueError,match="clock disagreement"):
        original.extract_session(events,timeline)


def test_wrapper_restores_original_even_after_failure(tmp_path):
    previous=original.checked_clock
    with pytest.raises(ValueError):
        recovery.execute(tmp_path,{}, {})
    assert original.checked_clock is previous


def test_actual_serialized_epoch_handler_fresh_process(tmp_path):
    inputs=fixture_inputs(tmp_path/"source")
    root=Path(inputs["repo_root"])
    roster=read(inputs["raw_roster"])
    index=read(inputs["session_index"])
    for meta,item in zip(roster,index):
        path=root/meta["path"]
        events=[json.loads(l) for l in path.read_text().splitlines()]
        for event in events:
            event["eventTimestamp"]+=1615189114123
        path.write_text("".join(json.dumps(e)+"\n" for e in events),encoding="utf-8")
        meta["source_sha256"]=filehash(path)
        p2=Path(inputs["session_index"]).parent/item["file"]
        timeline=read(p2)
        timeline["source_sha256"]=filehash(path)
        p2.write_text(json.dumps(timeline),encoding="utf-8")
        item["sha256"]=filehash(p2)
    Path(inputs["raw_roster"]).write_text(json.dumps(roster),encoding="utf-8")
    Path(inputs["session_index"]).write_text(json.dumps(index),encoding="utf-8")
    plan=read(inputs["foundation_plan"])
    plan["pins"]["ROSTER.json"]=filehash(inputs["raw_roster"])
    Path(inputs["foundation_plan"]).write_text(json.dumps(plan),encoding="utf-8")
    terminal=read(inputs["foundation_complete"])
    terminal["plan_sha256"]=filehash(inputs["foundation_plan"])
    terminal["outputs"]["SESSION_INDEX.json"]=filehash(inputs["session_index"])
    Path(inputs["foundation_complete"]).write_text(json.dumps(terminal),encoding="utf-8")
    config=dict(mode="constructed",expected_sessions=8,seed=20261026)
    output=tmp_path/"run"
    assert recovery.execute(output,inputs,config)["sessions"]==8
    assert recovery.verify(output,inputs,config)["verified"]
    manifest=tmp_path/"manifest.json"
    write(manifest,dict(output=str(output),inputs=inputs,config=config))
    script="import json,sys;from pathlib import Path;from runners.drive.cards.week3_pieces_input_recovery import verify;x=json.load(open(sys.argv[1]));assert verify(Path(x['output']),x['inputs'],x['config'])['verified']"
    subprocess.run([sys.executable,"-X","utf8","-B","-c",script,str(manifest)],check=True,timeout=60)
