import json
from pathlib import Path

import pytest

from runners.drive.cards import timing_census as tc


@pytest.mark.parametrize("single,total,resolution,expected", [
    (8, 10, 100, "per_character"), (799, 1000, 100, "first_character_delta"),
    (5, 10, 100, "first_character_delta"), (499, 1000, 1, "invalid"),
    (10, 10, 100.001, "invalid"), (10, 10, None, "invalid"),
    (0, 0, 1, "invalid"), (10, 10, 0, "invalid"),
])
def test_exhaustive_bands(single, total, resolution, expected):
    assert tc.band(single, total, resolution) == expected


def session(times=(0, .1, .1, .2)):
    return {"session": "s", "writer": "w", "deltas": [
        dict(seconds=t, ordinal=i, source=source, inserted_codepoints=n)
        for i, (t, source, n) in enumerate(zip(times, ["user", "api", "user", "user"], [1, 100, 3, 1]))]}


def test_character_weighting_suggestions_zeros_and_clock():
    result = tc.primary([tc.summarize_session(session())])
    assert result["single_character_share"] == .4
    assert result["counts"]["typed_characters"] == 5
    assert result["counts"]["multi_characters"] == 3
    assert result["counts"]["nonuser_characters"] == 100
    assert result["zero_interval_share"] == 1 / 3
    assert result["resolution_ms"] == 100
    assert result["timing_mode"] == "invalid"


def test_no_positive_intervals_is_explicitly_invalid():
    result = tc.primary([tc.summarize_session(session((0, 0, 0, 0)))])
    assert result["resolution_ms"] is None
    assert result["zero_interval_share"] == 1
    assert not result["pause_valid"]


def test_nonfinite_and_reversed_chronology_refused():
    for times in [(0, .2, .1, .3), (0, float("nan"), .1, .3)]:
        with pytest.raises(ValueError):
            tc.summarize_session(session(times))


def test_real_handler_recomputation_and_mutation_refusal(tmp_path):
    root = tmp_path / "input"
    tc.write(root / "sessions/s.json", session())
    tc.write(root / "SESSION_INDEX.json", [dict(session="s", writer="w", file="sessions/s.json", sha256=tc.filehash(root / "sessions/s.json"))])
    tc.write(root / "COMPLETE.json", dict(status="COMPLETE", outputs={"SESSION_INDEX.json": tc.filehash(root / "SESSION_INDEX.json")}))
    inputs = dict(session_index=str(root / "SESSION_INDEX.json"), foundation_complete=str(root / "COMPLETE.json"))
    output = tmp_path / "output"
    result = tc.execute(output, inputs, {})
    assert tc.verify(output, inputs, {})["primary"] == result
    (output / "TC_PRIMARY.json").write_text("{}")
    with pytest.raises(ValueError, match="recompute"):
        tc.verify(output, inputs, {})
    (root / "sessions/s.json").write_text("{}")
    with pytest.raises(ValueError, match="hash changed"):
        tc.execute(tmp_path / "other", inputs, {})
