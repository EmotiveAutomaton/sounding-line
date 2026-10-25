import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from runners.drive.cards import week3_pieces_input as w
from runners.drive.cards.timing_census import write, filehash, read
from runners.drive.cards.timing_p6 import gzread, gzwrite
from runners.drive.timeline import rebuild


def fixture_events():
    events = [dict(eventName="system-initialize", eventSource="api", eventTimestamp=0, currentDoc="\n")]
    now = 0
    text = ""
    def add(name="text-insert", source="user", delay=.1, **kwargs):
        nonlocal now
        now += delay
        events.append(dict(eventName=name, eventSource=source, eventTimestamp=round(now*1000, 8), **kwargs))
    for char in "One. Two\nThree ":
        add(delay=3 if char == "T" else .1, textDelta={"ops": [{"retain":len(text)}, {"insert":char}]})
        text += char
    add("suggestion-get")
    add("suggestion-open", delay=3)
    menu = len(events)-1
    add("suggestion-select")
    selected = len(events)-1
    add(source="api", textDelta={"ops": [{"retain":len(text)}, {"insert":"xyz"}]})
    add("text-delete", delay=59.8, textDelta={"ops":[{"retain":len(text)}, {"delete":1}]})
    # The deletion is within exactly sixty seconds of selection.
    add("text-delete", textDelta={"ops":[{"retain":len(text)}, {"delete":1}]})
    return events, [dict(key="k", ordinal=menu, end_ordinal=len(events), handling="edit", menu=["xyz"])], selected


def fixture_inputs(root):
    root = Path(root).resolve()
    foundation = root / "foundation"
    roster, metadata, index = [], [], []
    for writer in range(4):
        for session in range(2):
            sid = f"w{writer}s{session}"
            events, menus, _ = fixture_events()
            raw = root / "raw" / (sid + ".jsonl")
            raw.parent.mkdir(parents=True, exist_ok=True)
            raw.write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")
            timeline = rebuild(events, menus)
            timeline.update(session=sid, writer=str(writer), prompt="prompt", source_sha256=filehash(raw))
            path = foundation / "sessions" / (sid + ".json")
            write(path, timeline)
            index.append(dict(session=sid, writer=str(writer), file=path.relative_to(foundation).as_posix(), sha256=filehash(path)))
            roster.append(dict(session=sid, writer=str(writer), path=raw.relative_to(root).as_posix(), source_sha256=filehash(raw)))
            metadata.append(dict(session=sid, writer=str(writer), prompt="prompt", timestamp=session, genre="argumentative"))
    write(root / "ROSTER.json", roster)
    write(root / "SESSIONS.json", metadata)
    write(foundation / "SESSION_INDEX.json", index)
    write(foundation / "PLAN.json", dict(pins={name: filehash(root/name) for name in ("ROSTER.json", "SESSIONS.json")}))
    write(foundation / "COMPLETE.json", dict(status="COMPLETE", plan_sha256=filehash(foundation/"PLAN.json"), outputs={"SESSION_INDEX.json":filehash(foundation/"SESSION_INDEX.json")}))
    return dict(repo_root=str(root), foundation_complete=str(foundation/"COMPLETE.json"), foundation_plan=str(foundation/"PLAN.json"),
                session_index=str(foundation/"SESSION_INDEX.json"), raw_roster=str(root/"ROSTER.json"), prepared_sessions=str(root/"SESSIONS.json"))


def test_event_provenance_boundaries_and_future_symbol():
    events, menus, _ = fixture_events()
    result = w.extract_session(events, rebuild(events, menus))
    kinds = [a["kind"] for a in result["actions"]]
    assert {"burst", "pause", "request", "accept", "delete", "revision", "edit_accepted"} <= set(kinds)
    assert result["actions"][0]["length"] == len("One. ")
    assert any(r["location"] == "before_sentence" for r in result["intervals"])
    assert any(r["location"] == "before_paragraph" for r in result["intervals"])
    assert any(r["location"] == "separator" for r in result["intervals"])
    assert sum(a["kind"] == "edit_accepted" for a in result["actions"]) == 2
    assert result["interval_exclusions"]["endpoint_not_single_user_insert"] >= 1


def test_exact_two_second_gap_and_tied_bin_partition():
    actions = [dict(kind="insert", length=1, seconds=s, source_ordinals=[i]) for i,s in enumerate((0,1.999,3.999))]
    result = w.collapse_actions(actions)
    assert [(r["kind"],r["length"]) for r in result] == [("burst",2),("pause",2),("burst",1)]
    edges = w.bin_edges([dict(actions=result)])
    assert len(w.symbols(result, edges)) == 3
    assert w.symbols([dict(kind="delete",length=1)], {"delete":dict(terciles=[1,1])}) == ["delete0"]


def test_interval_rejects_previous_multicharacter_and_suggestion_touch():
    events = [dict(eventName="system-initialize",currentDoc="",eventTimestamp=0),
        dict(eventName="text-insert",eventSource="user",eventTimestamp=100,textDelta={"ops":[{"insert":"ab"}]}),
        dict(eventName="text-insert",eventSource="user",eventTimestamp=200,textDelta={"ops":[{"retain":2},{"insert":"c"}]}),
        dict(eventName="suggestion-hover",eventTimestamp=250),
        dict(eventName="text-insert",eventSource="user",eventTimestamp=300,textDelta={"ops":[{"retain":3},{"insert":"d"}]}),
        dict(eventName="text-insert",eventSource="user",eventTimestamp=400,textDelta={"ops":[{"retain":4},{"insert":"e"}]})]
    result = w.extract_session(events, rebuild(events, []))
    assert [r["ordinal"] for r in result["intervals"]] == [5]
    assert result["interval_exclusions"] == {"endpoint_not_single_user_insert":1,"suggestion":1}


def test_unicode_counts_are_codepoints_and_utf16_positions():
    events = [dict(eventName="system-initialize",currentDoc="\n",eventTimestamp=0),
        dict(eventName="text-insert",eventSource="user",eventTimestamp=100,textDelta={"ops":[{"insert":"\U0001f600a"}]}),
        dict(eventName="text-delete",eventSource="user",eventTimestamp=200,textDelta={"ops":[{"delete":2}]})]
    result = w.extract_session(events, rebuild(events, []))
    assert next(a for a in result["actions"] if a["kind"]=="burst")["length"] == 2
    assert next(a for a in result["actions"] if a["kind"]=="delete")["length"] == 1


def test_writer_split_disjoint_stable_and_count_balanced():
    counts = {str(i): i//2+1 for i in range(20)}
    a = w.stratified_split(counts)
    assert a == w.stratified_split(dict(reversed(list(counts.items()))))
    assert list(a.values()).count("discovery") == 10
    assert sum(counts[k] for k,v in a.items() if v=="discovery") == sum(counts[k] for k,v in a.items() if v=="test")


def test_full_serialized_handler_fresh_process_and_mutation(tmp_path):
    inputs = fixture_inputs(tmp_path/"source")
    config = dict(mode="constructed",expected_sessions=8,seed=w.SEED)
    output = tmp_path/"run"
    result = w.execute(output,inputs,config)
    assert result["sessions"]==8 and result["scientific_result"] is False
    assert w.verify(output,inputs,config)["verified"]
    manifest = tmp_path/"verify.json"
    write(manifest, dict(output=str(output),inputs=inputs,config=config))
    script = "import json,sys;from pathlib import Path;from runners.drive.cards.week3_pieces_input import verify;x=json.load(open(sys.argv[1]));assert verify(Path(x['output']),x['inputs'],x['config'])['verified']"
    env = dict(os.environ, PYTHONHASHSEED="71")
    subprocess.run([sys.executable,"-X","utf8","-B","-c",script,str(manifest)],check=True,env=env,timeout=60)
    index = read(output/"WB1_INPUT_INDEX.json")
    path = output/index[0]["file"]
    record = gzread(path)
    record["actions"][0]["length"]+=1
    path.unlink()
    gzwrite(path,record)
    with pytest.raises(ValueError,match="reproduce original source"):
        w.verify(output,inputs,config)


def test_changed_source_and_bad_census_refused(tmp_path):
    inputs=fixture_inputs(tmp_path/"source")
    config=dict(mode="constructed",expected_sessions=8,seed=w.SEED)
    path=Path(inputs["raw_roster"])
    path.write_text(path.read_text()+" ")
    with pytest.raises(ValueError,match="metadata source changed"):
        w.execute(tmp_path/"run",inputs,config)
    with pytest.raises(ValueError,match="full canonical P2"):
        w.validate_config(dict(mode="corpus",expected_sessions=10,seed=w.SEED))
