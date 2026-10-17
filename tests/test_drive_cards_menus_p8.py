import json
from pathlib import Path

import pytest

from runners.drive.cards import menus_p8 as p8
from runners.drive.cards.menus_io import sha256, write


def fixture():
    session = dict(session="session", writer="writer", rows=[dict(ordinal=1, key="decision", menu=["one", "two"])])
    event = dict(eventName="suggestion-open", currentSuggestions=[
        dict(index=3, original="one", trimmed="different display", probability=.25),
        dict(index=7, original="two", trimmed="two", probability=0)],
        currentN="2", currentMaxToken="40", currentTemperature="0.75", currentTopP="1",
        currentPresencePenalty="0", currentFrequencyPenalty="1")
    return session, event


def test_logged_values_positions_zero_and_settings_preserved():
    session, event = fixture()
    rows = list(p8.extract_session([{}, event], session, "hash"))
    assert [row["suggestion_index"] for row in rows] == [3, 7]
    assert rows[0]["log_positive_score"] == pytest.approx(-1.3862943611198906)
    assert rows[1]["log_positive_score"] is None
    assert rows[1]["score_status"] == "zero"
    assert rows[0]["decoding_logged"]["currentTemperature"] == "0.75"
    assert rows[0]["decoding_numeric"]["currentTemperature"] == .75


def test_menu_mismatch_and_nonfinite_score_refuse():
    session, event = fixture()
    event["currentSuggestions"][0]["probability"] = float("nan")
    with pytest.raises(ValueError, match="nonfinite"):
        list(p8.extract_session([{}, event], session, "hash"))


def test_outside_probability_range_is_retained_without_semantic_conversion():
    session, event = fixture()
    event["currentSuggestions"][0]["probability"] = 77.54296235638745
    event["currentSuggestions"][1]["probability"] = -2.5
    rows = list(p8.extract_session([{}, event], session, "hash"))
    assert rows[0]["logged_score"] == 77.54296235638745
    assert rows[0]["score_status"] == "above_one"
    assert rows[1]["probability_logged"] == -2.5
    assert rows[1]["logged_score"] == -2.5
    assert rows[1]["log_positive_score"] is None
    assert rows[1]["score_status"] == "negative"
    event["currentSuggestions"][0]["probability"] = .25
    event["currentSuggestions"].reverse()
    with pytest.raises(ValueError, match="ordering"):
        list(p8.extract_session([{}, event], session, "hash"))


def test_entrypoint_replay_and_mutation(tmp_path):
    session, event = fixture()
    raw = tmp_path / "raw.jsonl"
    raw.write_text(json.dumps({}) + "\n" + json.dumps(event) + "\n", encoding="utf8")
    write(tmp_path / "sessions.json", [session])
    write(tmp_path / "roster.json", [dict(session="session", path="raw.jsonl", source_sha256=sha256(raw))])
    inputs = dict(source_root=str(tmp_path), sessions=str(tmp_path / "sessions.json"), roster=str(tmp_path / "roster.json"))
    output = tmp_path / "out"
    report = p8.execute(output, inputs, {})
    assert report["summary"]["suggestions"] == 2
    assert p8.verify(output, inputs, {})["verified"]
    raw.write_text(raw.read_text(encoding="utf8") + "{}\n", encoding="utf8")
    with pytest.raises(ValueError, match="hash changed"):
        p8.verify(output, inputs, {})
