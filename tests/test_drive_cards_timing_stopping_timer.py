from pathlib import Path

import pytest

from runners.drive.cards import timing_stopping as primary
from runners.drive.cards import timing_stopping_timer as timer
from runners.drive.cards.timing_census import read, write, filehash
from tests.test_drive_cards_timing_stopping import stopping_inputs, fresh_verify


def completed_primary(tmp_path, durations):
    inputs = stopping_inputs(tmp_path / "source", durations=durations)
    output = tmp_path / "primary" / "output"
    assert primary.execute(output, inputs, primary.CONFIG)["state"] == "positive"
    complete = output.parent / "COMPLETE.json"
    write(complete, dict(status="COMPLETE", fresh_process_verified=True,
                        outputs={"output/" + p.name: filehash(p) for p in output.glob("*.json")}))
    return dict(inputs, primary_complete=str(complete))


@pytest.mark.parametrize("direction,state", [(1, "positive"), (0, "null"), (-1, "negative")])
def test_timer_serialized_sign_and_fresh_replay(tmp_path, direction, state):
    durations = [615, 645] * (3 if direction == 1 else 1 if direction == 0 else 0) + list(range(675, 900, 30))
    inputs = completed_primary(tmp_path, durations)
    output = tmp_path / "timer"
    result = timer.execute(output, inputs, timer.CONFIG)
    assert result["state"] == state
    expected = 4 / 14 if direction == 1 else 0 if direction == 0 else -2 / 8
    assert result["effect"] == pytest.approx(expected)
    assert timer.verify(output, inputs, timer.CONFIG)["verified"]
    fresh_verify(tmp_path, "runners.drive.cards.timing_stopping_timer", output, inputs, timer.CONFIG, result)


def test_negative_counterfactual_and_support_refused():
    records = [dict(writer=str(w), sessions=20, counts=[2, 2, 0, 0, 0, 0, 0, 0, 0, 16]) for w in range(10)]
    result = timer.infer(records, timer.CONFIG)
    assert result["state"] == "invalid"
    assert "negative" in result["reason"]
    for row in records:
        row["counts"] = [2, 2] + [0] * 8
    assert "no right-side" in timer.infer(records, timer.CONFIG)["reason"]


def test_linear_right_side_counterfactual_and_gate(tmp_path):
    records = [dict(writer=str(w), sessions=110, counts=list(range(2, 22, 2))) for w in range(10)]
    result = timer.infer(records, timer.CONFIG)
    assert result["effect"] == 0
    assert result["predicted_first_two_bin_masses"] == pytest.approx([2 / 110, 4 / 110])
    inputs = completed_primary(tmp_path, list(range(615, 900, 30)))
    complete = Path(inputs["primary_complete"])
    value = read(complete)
    value["fresh_process_verified"] = False
    complete.write_text(__import__('json').dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match="fresh-verified"):
        timer.execute(tmp_path / "refused", inputs, timer.CONFIG)
    with pytest.raises(ValueError, match="configuration"):
        timer.execute(tmp_path / "wrong", inputs, dict(timer.CONFIG, extension=1))
