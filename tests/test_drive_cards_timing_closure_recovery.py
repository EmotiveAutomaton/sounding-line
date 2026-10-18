"""D24 source-schema recovery controls; no native model or corpus execution."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from runners.drive.cards import timing_closure as original
from runners.drive.cards import timing_closure_measure as measure
from runners.drive.cards import timing_closure_recovery as card
from runners.drive.cards.timing_census import read, write, filehash
from runners.drive.timeline import rebuild
from tests.test_drive_cards_timing_closure import FixtureEncoder, admitted_inputs


def excluded_events():
    return [
        dict(eventName="system-initialize", eventSource="api", eventTimestamp=0, currentDoc="\n"),
        dict(eventName="suggestion-open", eventSource="user", eventTimestamp=500000,
             currentSuggestions=[dict(index=0, original="Unfinished", trimmed="Unfinished")]),
        dict(eventName="suggestion-close", eventSource="user", eventTimestamp=501000),
        dict(eventName="suggestion-select", eventSource="user", eventTimestamp=502000, currentSuggestionIndex=0),
        dict(eventName="text-insert", eventSource="api", eventTimestamp=503000,
             textDelta=dict(ops=[dict(insert="Unfinished")])),
        dict(eventName="text-insert", eventSource="user", eventTimestamp=504000,
             textDelta=dict(ops=[dict(retain=10), dict(insert=" tale.")])),
        dict(eventName="system-finish", eventSource="user", eventTimestamp=900000),
    ]


def test_excluded_api_text_remains_non_typed_and_not_an_acceptance():
    events = excluded_events()
    timeline = rebuild(events, [])
    with pytest.raises(ValueError, match="canonical P2"):
        measure.replay(events, timeline)
    result = card.replay(events, timeline)
    assert result["entries"] == []  # typed ending cannot promote its API prefix
    assert result["excluded_api_insertions"] == [dict(menu_ordinal=1, insertion_ordinal=4,
        reason="selection has no active undecided set", inserted_utf16=10)]
    assert result["duration_seconds"] == 900
    events.pop(2)  # ordinary valid acceptance omitted from P2 must still refuse
    with pytest.raises(ValueError, match="no authenticated canonical exclusion"):
        card.replay(events, rebuild(events, []))


def failed_fixture(tmp_path, monkeypatch, direction):
    inputs = admitted_inputs(tmp_path, monkeypatch, direction)
    root = Path(inputs["repo_root"])
    index = read(inputs["session_index"])
    roster = read(inputs["raw_roster"])
    target = index[1]
    meta = next(r for r in roster if r["session"] == target["session"])
    raw = root / meta["path"]
    events = [json.loads(line) for line in raw.read_text().splitlines()]
    timeline_path = Path(inputs["session_index"]).parent / target["file"]
    timeline = read(timeline_path)
    previous = events.pop()
    at = len(events)
    events.extend([
        dict(eventName="suggestion-open", eventSource="user", eventTimestamp=750000,
             currentSuggestions=[dict(index=0, original="Excluded API.", trimmed="Excluded API.")]),
        dict(eventName="suggestion-close", eventSource="user", eventTimestamp=751000),
        dict(eventName="suggestion-select", eventSource="user", eventTimestamp=752000, currentSuggestionIndex=0),
        dict(eventName="text-insert", eventSource="api", eventTimestamp=753000,
             textDelta=dict(ops=[dict(retain=len(timeline["final_document"])-1), dict(insert="Excluded API.")])),
        previous,
    ])
    rows = [dict(key=d["key"], ordinal=d["ordinal"], end_ordinal=timeline["decisions"][i+1]["ordinal"] if i+1 < len(timeline["decisions"]) else at,
                 handling=d["handling"], menu=["unused"]) for i, d in enumerate(timeline["decisions"])]
    raw.write_text(''.join(json.dumps(e)+'\n' for e in events), encoding="utf-8", newline="\n")
    fresh = rebuild(events, rows)
    fresh.update({k: timeline[k] for k in ("session", "writer", "prompt")}, source_sha256=filehash(raw))
    timeline_path.write_text(json.dumps(fresh), encoding="utf-8")
    target["sha256"] = filehash(timeline_path)
    meta["source_sha256"] = filehash(raw)
    Path(inputs["session_index"]).write_text(json.dumps(index), encoding="utf-8")
    Path(inputs["raw_roster"]).write_text(json.dumps(roster), encoding="utf-8")
    foundation_plan = read(inputs["foundation_plan"])
    foundation_plan["pins"][Path(inputs["raw_roster"]).relative_to(root).as_posix()] = filehash(inputs["raw_roster"])
    Path(inputs["foundation_plan"]).write_text(json.dumps(foundation_plan), encoding="utf-8")
    complete = read(inputs["foundation_complete"])
    complete["plan_sha256"] = filehash(inputs["foundation_plan"])
    complete["outputs"]["SESSION_INDEX.json"] = filehash(inputs["session_index"])
    Path(inputs["foundation_complete"]).write_text(json.dumps(complete), encoding="utf-8")
    attempt = tmp_path / "failed"
    config = original.config_for("primary")
    with pytest.raises(ValueError, match="canonical P2"):
        original.execute(attempt / "output", inputs, config)
    write(attempt / "PLAN.json", dict(module="runners.drive.cards.timing_closure", config=config, inputs=inputs,
          at="2026-10-18T01:00:00+00:00", pins={str(Path(original.__file__).resolve()): filehash(original.__file__),
          str(Path(measure.__file__).resolve()): filehash(measure.__file__)}))
    write(attempt / "FAILED.json", dict(status="FAILED", engineering_retry_available=True, at="2026-10-18T01:00:10+00:00"))
    return dict(inputs, failed_plan=str(attempt / "PLAN.json"), failed_record=str(attempt / "FAILED.json"))


@pytest.mark.parametrize("direction,state", [(1, "positive"), (0, "null"), (-1, "negative")])
def test_serialized_recovery_preserves_checkpoints_and_fresh_verifies(tmp_path, monkeypatch, direction, state):
    inputs = failed_fixture(tmp_path, monkeypatch, direction)
    output = tmp_path / "recovered"
    config = original.config_for("primary")
    result = card.execute(output, inputs, config)
    assert result["state"] == state
    assert result["effect"] == pytest.approx(.75*direction, abs=1e-10)
    identity = read(output / "RECOVERY_SOURCE.json")
    assert identity["charged_prior_seconds"] == 10
    assert len(identity["retained_files"]) == 2
    assert all(filehash(output / name) == digest for name, digest in identity["retained_files"].items())
    assert len(read(output / "CLOSURE_SOURCE_EXCLUSIONS.json")) == 1
    manifest = tmp_path / "verify.json"
    write(manifest, dict(output=str(output), inputs=inputs, config=config))
    code = "import json,sys; from pathlib import Path; from tests.test_drive_cards_timing_closure import FixtureEncoder; from runners.drive.cards import timing_closure_recovery as c; c.measure.Encoder=FixtureEncoder; x=json.load(open(sys.argv[1])); print(json.dumps(c.verify(Path(x['output']),x['inputs'],x['config'])))"
    child = subprocess.run([sys.executable, "-c", code, str(manifest)], capture_output=True, text=True, timeout=120,
        env=dict(os.environ, PYTHONHASHSEED="431"), creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS if os.name == "nt" else 0)
    assert child.returncode == 0, child.stderr
    assert json.loads(child.stdout)["primary"] == result


def test_recovery_yield_resume_source_mutation_and_cumulative_cap(tmp_path, monkeypatch):
    inputs = failed_fixture(tmp_path, monkeypatch, 1)
    output = tmp_path / "recovered"
    config = original.config_for("primary")
    write(output / "YIELD_REQUEST.json", {})
    assert card.execute(output, inputs, config)["status"] == "yielded"
    (output / "YIELD_REQUEST.json").unlink()
    assert card.execute(output, inputs, config)["state"] == "positive"
    progress = Path(inputs["failed_plan"]).parent / "output/CLOSURE_PROGRESS.json"
    old = read(progress); old["active_seconds"] = 2700
    progress.write_text(json.dumps(old), encoding="utf-8")
    with pytest.raises(ValueError, match="allowance unavailable"):
        card.failure_identity(inputs, config)
    old["active_seconds"] = .1
    progress.write_text(json.dumps(old), encoding="utf-8")
    checkpoint = next(p for p in (progress.parent / "sessions").glob("*.json") if not p.name.endswith(".receipt.json"))
    checkpoint.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="checkpoint changed"):
        card.failure_identity(inputs, config)


def test_schema_repair_preserves_unaffected_replay_exactly(tmp_path):
    from tests.test_drive_cards_timing_closure import fixture_inputs
    inputs = fixture_inputs(tmp_path)
    meta = read(inputs["raw_roster"])[0]
    events = [json.loads(line) for line in (Path(inputs["repo_root"]) / meta["path"]).read_text().splitlines()]
    row = read(inputs["session_index"])[0]
    timeline = read(Path(inputs["session_index"]).parent / row["file"])
    result = card.replay(events, timeline)
    assert result.pop("excluded_api_insertions") == []
    assert result == measure.replay(events, timeline)
