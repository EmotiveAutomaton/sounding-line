"""Canonical provenance recovery only; complete synthetic serialized runs."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from runners.drive.cards import timing_events as original
from runners.drive.cards import timing_events_recovery as event_card
from runners.drive.cards import timing_d3_content as content_original
from runners.drive.cards import timing_d3_content_recovery as content_card
from runners.drive.cards.timing_census import read, write, filehash
from runners.drive.timeline import rebuild
from runners.stage9.coauthor import replay, units
from tests.test_drive_cards_timing_d3_content import fixture_inputs
from tests.test_drive_cards_timing_events import accepted_events


def repeated_append(document="\n", timestamp=0):
    options = [dict(index=0, original="first ", trimmed="first ")]
    events = [
        dict(eventName="suggestion-open", eventSource="user", currentSuggestions=options),
        dict(eventName="suggestion-select", eventSource="user", currentSuggestionIndex=0),
        dict(eventName="text-insert", eventSource="api", textDelta=dict(ops=[dict(retain=len(units(document))-1), dict(insert="first ")])),
        dict(eventName="text-delete", eventSource="user", textDelta=dict(ops=[dict(retain=len(units(document))-1), dict(delete=1)])),
        dict(eventName="suggestion-reopen", eventSource="user", currentSuggestions=options),
        dict(eventName="suggestion-select", eventSource="user", currentSuggestionIndex=0),
        dict(eventName="text-insert", eventSource="api", textDelta=dict(ops=[dict(retain=len(units(document))+4), dict(insert="second ")])),
    ]
    return [dict(e, eventTimestamp=timestamp+(i+1)*1000) for i,e in enumerate(events)]


def test_repeated_excluded_menu_requires_exact_canonical_proof():
    events = [dict(eventName="system-initialize",eventSource="api",eventTimestamp=0,currentDoc="\n")] + repeated_append()
    timeline = rebuild(events, [])
    canonical = replay(events)
    assert canonical["reconstructed"] and canonical["errors"] == {}
    assert canonical["final_document"] == timeline["final_document"]
    assert canonical["events"][0]["verified_insertion"]
    assert canonical["events"][0]["exclusion"] == "selection has no active undecided set"
    with pytest.raises(ValueError,match="empty/repeated"):
        original.accepted_lifetimes(events)
    spans, exclusions = event_card.accepted_lifetimes(events,timeline)
    assert spans == {}
    assert [(r["menu_ordinal"],r["insertion_ordinal"],r["inserted_utf16"]) for r in exclusions] == [(1,3,6),(1,7,7)]
    # A canonical valid acceptance omitted from the P2 index is not excluded.
    valid = events[:4]
    assert replay(valid)["events"][0]["usable"]
    with pytest.raises(ValueError,match="lacks canonical exclusion"):
        event_card.accepted_lifetimes(valid,rebuild(valid,[]))
    # Duplicate accepted identity cannot be rescued by its canonical exclusion.
    with pytest.raises(ValueError,match="repeated eligible"):
        event_card.accepted_lifetimes(events,dict(timeline,decisions=[dict(ordinal=1,handling="accept")]))


def test_utf16_survival_internal_insertion_and_canonical_append_unchanged():
    events = accepted_events()
    events[3]["textDelta"] = dict(ops=[dict(insert="😀abcd")])
    events += [dict(eventName="text-edit",eventSource="user",textDelta=dict(ops=[dict(retain=3),dict(insert="😀")])),
               dict(eventName="text-edit",eventSource="user",textDelta=dict(ops=[dict(retain=5),dict(insert="x")])),
               dict(eventName="text-edit",eventSource="user",textDelta=dict(ops=[dict(delete=2)]))]
    expected = original.accepted_lifetimes(events)
    final = replay(events)["final_document"]
    timeline = dict(decisions=[dict(ordinal=1,handling="edit")],final_document=final)
    assert event_card.accepted_lifetimes(events,timeline) == (expected,[])
    assert expected[1]["original_utf16"] == 6
    assert expected[1]["inserted_inside_utf16"] == 3
    assert expected[1]["deleted_original_utf16"] == 2 and expected[1]["reversed"]
    events[0]["currentDoc"] = "prefix\n"
    with pytest.raises(ValueError,match="canonical append"):
        event_card.accepted_lifetimes(events,timeline)


@pytest.mark.parametrize("defect",["wrong_reason","unverified","canonical_errors"])
def test_recovery_refuses_any_other_canonical_condition(monkeypatch,defect):
    events = [dict(eventName="system-initialize",eventSource="api",eventTimestamp=0,currentDoc="\n")] + repeated_append()
    timeline = rebuild(events,[])
    canonical = replay(events)
    if defect=="wrong_reason":canonical["events"][0]["exclusion"]="selected API insertion does not match an offered full-document transform"
    elif defect=="unverified":canonical["events"][0]["verified_insertion"]=False
    else:canonical["errors"]={"unresolved delta":1}
    monkeypatch.setattr(event_card,"canonical_replay",lambda events:canonical)
    with pytest.raises(ValueError,match="canonical"):
        event_card.accepted_lifetimes(events,timeline)


def failed_fixture(root, kind, direction):
    root = Path(root)
    inputs = fixture_inputs(root / "source",direction)
    source_root = Path(inputs["repo_root"])
    index, roster = read(inputs["session_index"]), read(inputs["raw_roster"])
    target = index[1]
    meta = next(r for r in roster if r["session"] == target["session"])
    raw = source_root / meta["path"]
    events = [json.loads(line) for line in raw.read_text(encoding="utf-8").splitlines()]
    timeline_path = Path(inputs["session_index"]).parent / target["file"]
    timeline = read(timeline_path)
    boundary = len(events)
    events.extend(repeated_append(timeline["final_document"],events[-1]["eventTimestamp"]))
    menus = [dict(key=d["key"],ordinal=d["ordinal"],end_ordinal=timeline["decisions"][i+1]["ordinal"] if i+1<len(timeline["decisions"]) else boundary,
                  handling=d["handling"],menu=["abcd "]) for i,d in enumerate(timeline["decisions"])]
    raw.write_text(''.join(json.dumps(e)+'\n' for e in events),encoding="utf-8",newline="\n")
    fresh = rebuild(events,menus)
    fresh.update({k:timeline[k] for k in ("session","writer","prompt")},source_sha256=filehash(raw))
    timeline_path.write_text(json.dumps(fresh),encoding="utf-8")
    target["sha256"],meta["source_sha256"] = filehash(timeline_path),filehash(raw)
    Path(inputs["session_index"]).write_text(json.dumps(index),encoding="utf-8")
    Path(inputs["raw_roster"]).write_text(json.dumps(roster),encoding="utf-8")
    plan = read(inputs["foundation_plan"])
    plan["pins"][Path(inputs["raw_roster"]).relative_to(source_root).as_posix()] = filehash(inputs["raw_roster"])
    Path(inputs["foundation_plan"]).write_text(json.dumps(plan),encoding="utf-8")
    complete = read(inputs["foundation_complete"])
    complete["plan_sha256"] = filehash(inputs["foundation_plan"])
    complete["outputs"]["SESSION_INDEX.json"] = filehash(inputs["session_index"])
    Path(inputs["foundation_complete"]).write_text(json.dumps(complete),encoding="utf-8")
    legacy, config = (original,dict(card="D3",extension=False,bootstrap_draws=2000,seed=20261017)) if kind=="EVENT" else (content_original,dict(content_original.CONFIG))
    if kind=="EVENT":inputs = {k:v for k,v in inputs.items() if k not in {"prepared_sessions","content_complete"}}
    attempt = root / "failed"
    with pytest.raises(ValueError,match="empty/repeated"):
        legacy.execute(attempt/"output",inputs,config)
    write(attempt/"PLAN.json",dict(module=legacy.__name__,config=config,inputs=inputs,
          at="2026-10-18T01:00:00+00:00",pins={str(Path(m.__file__).resolve()):filehash(m.__file__) for m in {legacy,original}}))
    write(attempt/"FAILED.json",dict(status="FAILED",engineering_retry_available=True,at="2026-10-18T01:00:10+00:00"))
    return dict(inputs,failed_plan=str(attempt/"PLAN.json"),failed_record=str(attempt/"FAILED.json")),config


@pytest.mark.parametrize("kind",["EVENT","CONTENT"])
@pytest.mark.parametrize("direction,state",[(1,"positive"),(0,"null"),(-1,"negative")])
def test_serialized_recovery_known_answers_preserved_bytes_and_fresh_process(tmp_path,kind,direction,state):
    inputs,config = failed_fixture(tmp_path,kind,direction)
    card = event_card if kind=="EVENT" else content_card
    output = tmp_path/"recovered"
    result = card.execute(output,inputs,config)
    assert result["state"] == state
    identity = read(output/"RECOVERY_SOURCE.json")
    assert identity["charged_prior_seconds"] == 10
    assert len(identity["retained_files"]) == (2 if kind=="EVENT" else 0)
    assert all(filehash(output/name)==digest for name,digest in identity["retained_files"].items())
    assert len(read(output/"SOURCE_EXCLUSIONS.json")) == 2
    assert read(output/"FIRST_TENTH.json")["charged_prior_seconds"] == 10
    if kind=="EVENT":assert result["effect"] == direction
    else:
        assert result["observations"] == 200
        assert "<polyline" in (output/"LATENCY_CURVE.svg").read_text()
    manifest = tmp_path/"verification.json"
    write(manifest,dict(output=str(output),inputs=inputs,config=config))
    code = "import json,sys; from pathlib import Path; from " + card.__name__ + " import verify; x=json.load(open(sys.argv[1])); print(json.dumps(verify(Path(x['output']),x['inputs'],x['config'])))"
    child = subprocess.run([sys.executable,"-c",code,str(manifest)],text=True,capture_output=True,timeout=60,
        env=dict(os.environ,PYTHONHASHSEED="431"),creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS if os.name=="nt" else 0)
    assert child.returncode == 0,child.stderr
    assert json.loads(child.stdout)["primary"] == result
    assert card.execute(output,inputs,config) == result


@pytest.mark.parametrize("kind",["EVENT","CONTENT"])
def test_yield_resume_caps_exact_config_and_source_or_forged_output_refusal(tmp_path,kind):
    inputs,config = failed_fixture(tmp_path,kind,1)
    card = event_card if kind=="EVENT" else content_card
    legacy = original if kind=="EVENT" else content_original
    output = tmp_path/"recovered"
    write(output/"YIELD_REQUEST.json",{})
    assert card.execute(output,inputs,config)["status"] == "yielded"
    saved = {p.name:p.read_bytes() for p in (output/"sessions").glob("*.json")}
    (output/"YIELD_REQUEST.json").unlink()
    assert card.execute(output,inputs,config)["state"] == "positive"
    assert all((output/"sessions"/name).read_bytes()==data for name,data in saved.items())
    with pytest.raises(ValueError,match="config"):
        card.execute(tmp_path/"wrong",inputs,dict(config,extra=True))
    rows_path = output/f"{kind}_ROWS.json"
    rows = read(rows_path)
    (rows if kind=="EVENT" else rows["rows"])[0]["latency"] += 5
    rows_path.write_text(json.dumps(rows),encoding="utf-8")
    binding = read(output/"TIMING_BINDINGS.json")
    binding["outputs"][rows_path.name] = filehash(rows_path)
    (output/"TIMING_BINDINGS.json").write_text(json.dumps(binding),encoding="utf-8")
    with pytest.raises(ValueError,match="does not reconstruct"):
        card.verify(output,inputs,config)
    failure = read(inputs["failed_record"])
    failure["at"] = "2026-10-18T01:30:00+00:00"
    Path(inputs["failed_record"]).write_text(json.dumps(failure),encoding="utf-8")
    with pytest.raises(ValueError,match="allowance unavailable"):
        event_card.failure_identity(inputs,config,legacy,kind)
    failure["at"] = "2026-10-18T01:00:10+00:00"
    Path(inputs["failed_record"]).write_text(json.dumps(failure),encoding="utf-8")
    raw = Path(inputs["repo_root"])/read(inputs["raw_roster"])[0]["path"]
    raw.write_text(raw.read_text()+" ",encoding="utf-8")
    with pytest.raises(ValueError,match="raw source changed"):
        card.execute(tmp_path/"changed",inputs,config)
