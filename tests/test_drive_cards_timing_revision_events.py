"""Known raw edit histories; no D30 burst boundary or scientific fit."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from runners.drive.cards.timing_text import replay_words
from runners.drive.cards.timing_revision_events import replay_revision_events


def event(ms, ops=None, source="user", doc=None):
    result = dict(eventName="system-initialize" if doc is not None else "text-insert",
                  eventTimestamp=ms, eventSource=source)
    if doc is not None:
        result["currentDoc"] = doc
    if ops is not None:
        result["textDelta"] = dict(ops=ops)
    return result


def checked(events):
    result = replay_revision_events(events)
    assert result["replay"] == replay_words(events)
    assert len(result["revision_events"]) == len(result["replay"]["words"])
    return result


def test_deleted_occurrence_stays_with_exact_source_event():
    rows = [event(0, doc=""), event(100, [{"insert": "cat "}]),
            event(200, [{"delete": 3}, {"insert": "dog"}])]
    result = checked(rows)
    assert [w["token"] for w in result["replay"]["words"]] == ["cat", "dog"]
    audit = result["revision_events"][0]
    assert audit["production_ordinals"] == [1]
    assert audit["changes"] == [dict(ordinal=2, seconds=.2, kind="delete", event_source="user", affected_character_ids=[0, 1, 2])]


def test_insertion_only_and_two_distinct_later_changes_retained():
    rows = [event(0, doc=""), event(100, [{"insert": "cat "}]),
            event(200, [{"retain": 1}, {"insert": "h"}]),
            event(5000, [{"delete": 1}])]
    result = checked(rows)
    changes = result["revision_events"][0]["changes"]
    assert [(c["kind"], c["ordinal"], c["seconds"]) for c in changes] == [("insert", 2, .2), ("delete", 3, 5.)]
    assert changes[0]["affected_character_ids"] == []
    assert "threshold" not in result and "immediate" not in result


def test_multiple_delete_ops_same_event_merge_character_identity():
    rows = [event(0, doc=""), event(100, [{"insert": "cat "}]),
            event(200, [{"delete": 1}, {"retain": 1}, {"delete": 1}])]
    result = checked(rows)
    assert result["revision_events"][0]["changes"] == [dict(ordinal=2, seconds=.2, kind="delete", event_source="user", affected_character_ids=[0, 2])]
    assert result["delta_clock"][-1]["deleted_utf16"] == 2


def test_api_deletion_not_silently_relabelled_human():
    rows = [event(0, doc=""), event(100, [{"insert": "cat "}]),
            event(2200, [{"delete": 3}], source="api")]
    result = checked(rows)
    assert result["replay"]["words"][0]["revised"] is True
    assert result["revision_events"][0]["changes"][0]["event_source"] == "api"
    assert result["delta_clock"][-1]["event_source"] == "api"


def test_utf16_identity_and_source_delta_clocks_preserved():
    rows = [event(0, doc=""), event(100, [{"insert": "😀 cat "}]),
            event(2100, [{"delete": 2}]), event(2100, [{"retain": 1}, {"insert": "x "}])]
    result = checked(rows)
    assert result["delta_clock"][0]["inserted_codepoints"] == 6
    assert result["delta_clock"][0]["inserted_utf16"] == 7
    assert result["revision_events"][0]["changes"][0]["affected_character_ids"] == [0]
    assert result["delta_clock"][-1]["seconds"] == result["delta_clock"][-2]["seconds"]


def test_in_composition_correction_does_not_invent_completed_occurrence():
    rows = [event(0, doc=""), event(100, [{"insert": "ca"}]),
            event(200, [{"retain": 1}, {"delete": 1}, {"insert": "t "}])]
    result = checked(rows)
    assert [w["token"] for w in result["replay"]["words"]] == ["ct"]
    assert result["revision_events"][0]["changes"] == []
    assert result["revision_events"][0]["production_ordinals"] == [1, 2]


def test_bad_chronology_and_split_surrogate_refuse():
    with pytest.raises(ValueError, match="chronology"):
        checked([event(0, doc=""), event(100, [{"insert": "cat "}]), event(90, [{"delete": 1}])])
    with pytest.raises((ValueError, UnicodeDecodeError)):
        checked([event(0, doc=""), event(100, [{"insert": "😀 "}]), event(200, [{"delete": 1}])])


def test_serialized_fresh_process_same_source_result(tmp_path):
    rows = [event(0, doc=""), event(100, [{"insert": "cat "}]),
            event(200, [{"retain": 1}, {"insert": "h"}]), event(5000, [{"delete": 1}])]
    expected = checked(rows)
    src, dst = tmp_path / "events.json", tmp_path / "replay.json"
    src.write_text(json.dumps(rows), encoding="utf8")
    code = "import json,sys;from runners.drive.cards.timing_revision_events import replay_revision_events as f;v=json.load(open(sys.argv[1],encoding='utf8'));json.dump(f(v),open(sys.argv[2],'x',encoding='utf8'))"
    child = subprocess.run([sys.executable, "-c", code, str(src), str(dst)], cwd=Path(__file__).resolve().parents[1],
        capture_output=True, text=True, timeout=30,
        creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS if os.name == "nt" else 0)
    assert child.returncode == 0, child.stderr
    assert json.loads(dst.read_text(encoding="utf8")) == expected
