"""Frozen metadata chains cannot authenticate fabricated occurrence content."""
import gzip
import json
from pathlib import Path

import pytest

from runners.drive.cards import timing_revision_source as source
from runners.drive.cards.timing_census import filehash, read
from runners.drive.cards.timing_p6 import gzread
from runners.drive.cards.timing_text import replay_words


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    if path.suffix == ".gz":
        with gzip.open(path, "wt", encoding="utf8") as f:
            f.write(text)
    else:
        path.write_text(text, encoding="utf8")


def seal(inputs):
    root = Path(inputs["repo_root"])
    save(inputs["foundation_plan"], dict(pins={Path(inputs[k]).relative_to(root).as_posix(): filehash(inputs[k])
        for k in ("prepared_sessions", "raw_roster", "source_pins")}))
    base = Path(inputs["foundation_complete"]).parent
    save(inputs["foundation_complete"], dict(status="COMPLETE", plan_sha256=filehash(inputs["foundation_plan"]),
        outputs={Path(inputs["session_index"]).relative_to(base).as_posix(): filehash(inputs["session_index"])}))
    binding = Path(inputs["p6_index"]).parent / "P6_BINDINGS.json"
    save(binding, dict(config={}, repo_root=str(root.resolve()), index_sha256=filehash(inputs["p6_index"]),
        inputs={k: filehash(inputs[k]) for k in ("foundation_complete", "prepared_sessions", "raw_roster", "session_index")}))
    base = Path(inputs["p6_completion"]).parent
    save(inputs["p6_completion"], dict(status="COMPLETE", fresh_process_verified=True,
        outputs={p.relative_to(base).as_posix(): filehash(p) for p in (Path(inputs["p6_index"]), binding)}))


def fixture(root):
    root = Path(root).resolve()
    root.mkdir(parents=True)
    events = [dict(eventName="system-initialize", eventTimestamp=0, currentDoc=""),
        dict(eventName="text-insert", eventTimestamp=100, eventSource="user", textDelta=dict(ops=[dict(insert="cat ")])),
        dict(eventName="text-delete", eventTimestamp=200, eventSource="user", textDelta=dict(ops=[dict(delete=3), dict(insert="dog")]))]
    raw = root / "raw/s.jsonl"
    raw.parent.mkdir()
    raw.write_text("\n".join(json.dumps(e) for e in events), encoding="utf8")
    original = replay_words(events)
    timeline = dict(session="s", writer="w", prompt="p", final_document=original["final_document"], source_sha256=filehash(raw))
    timeline_path = root / "foundation/s.json"
    save(timeline_path, timeline)
    score = dict(session="s", writer="w", prompt="p", timestamp=0, end_at=1,
        words=[dict(w, population_probability=.5, population_surprisal=.693147, population_log_frequency=-1.) for w in original["words"]])
    score_path = root / "p6/output/s.json.gz"
    save(score_path, score)
    inputs = dict(repo_root=str(root), foundation_complete=str(root / "foundation/COMPLETE.json"),
        foundation_plan=str(root / "foundation/PLAN.json"), session_index=str(root / "foundation/SESSION_INDEX.json"),
        prepared_sessions=str(root / "SESSIONS.json"), raw_roster=str(root / "ROSTER.json"),
        source_pins=str(root / "SOURCE_PINS.json"), p6_index=str(root / "p6/output/P6_INDEX.json"),
        p6_completion=str(root / "p6/COMPLETE.json"))
    save(inputs["session_index"], [dict(session="s", writer="w", file="s.json", sha256=filehash(timeline_path))])
    save(inputs["p6_index"], [dict(session="s", writer="w", file="s.json.gz", sha256=filehash(score_path))])
    save(inputs["prepared_sessions"], [dict(session="s", writer="w", prompt="p", timestamp=0, end_at=1)])
    save(inputs["raw_roster"], [dict(session="s", path="raw/s.jsonl", source_sha256=filehash(raw)),
        dict(session="upstream-only", path="unused.jsonl", source_sha256="0" * 64)])
    save(inputs["source_pins"], {"raw/s.jsonl": filehash(raw)})
    seal(inputs)
    return inputs


def test_authenticated_source_preserves_upstream_superset_and_original_occurrences(tmp_path):
    inputs = fixture(tmp_path / "source")
    sources = source.Sources(inputs)
    assert sources.population["primary_session_ids"] == ["s"]
    assert sources.population["upstream_only_session_ids"] == ["upstream-only"]
    result = sources.session("s")
    assert result["occurrence_count"] == 2
    assert result["revision_events"][0]["changes"][0]["ordinal"] == 2
    assert result["revision_events"][1]["changes"] == []


def test_raw_hash_change_refused(tmp_path):
    inputs = fixture(tmp_path / "source")
    path = Path(inputs["repo_root"]) / "raw/s.jsonl"
    path.write_text(path.read_text(encoding="utf8").replace("cat", "rat"), encoding="utf8")
    with pytest.raises(ValueError, match="raw revision source differs"):
        source.Sources(inputs).session("s")


def test_forged_saved_occurrence_refused_despite_resealed_index(tmp_path):
    inputs = fixture(tmp_path / "source")
    score_path = Path(inputs["p6_index"]).parent / "s.json.gz"
    score = gzread(score_path)
    score["words"][0]["revised"] = False
    save(score_path, score)
    index = read(inputs["p6_index"])
    index[0]["sha256"] = filehash(score_path)
    save(inputs["p6_index"], index)
    seal(inputs)
    with pytest.raises(ValueError, match="exact P6 occurrences"):
        source.Sources(inputs).session("s")


def test_changed_population_and_identity_refuse_after_metadata_reseal(tmp_path):
    inputs = fixture(tmp_path / "source")
    rows = read(inputs["prepared_sessions"])
    save(inputs["prepared_sessions"], rows * 2)
    seal(inputs)
    with pytest.raises(ValueError, match="duplicate session"):
        source.Sources(inputs)
    rows[0]["writer"] = "different"
    save(inputs["prepared_sessions"], rows)
    seal(inputs)
    with pytest.raises(ValueError, match="identity differs"):
        source.Sources(inputs).session("s")
