"""CA1 source authentication, exact CA0 parity and history-safe partitions."""
import copy
import gzip
import json
from pathlib import Path

import pytest

from runners.drive.cards import week3_alignment_inputs as card, week3_choice_intake as intake
from runners.drive.cards.menus_io import write, sha256
from tests.test_week3_choice_intake import row, source


def fixture(root):
    root = Path(root); root.mkdir(parents=True, exist_ok=True)
    rows = [row(w * 20 + j, "w" + str(w), "prompt " + str(j % 10)) for w in range(5) for j in range(20)]
    csv = source(root, rows); prior = root / "ca0"; output = prior / "output"
    intake.execute(output, {"source": str(csv)}, {})
    write(prior / "COMPLETE.json", {"status": "COMPLETE", "fresh_process_verified": True,
          "outputs": {"output/SUMMARY.json": sha256(output / "SUMMARY.json")}})
    return {"source": str(csv), "ca0_summary": str(output / "SUMMARY.json"), "ca0_complete": str(prior / "COMPLETE.json")}


def test_splits_never_cross_prompts_or_conversations():
    rows = [dict(writer="w", conversation="c" + str(i // 2), prompt="p" + str(i % 10)) for i in range(20)]
    split, exclusions, details = card.partitions(rows)
    assert not exclusions and len(details) == 1
    prompt_halves = {}
    for r in rows:
        h = split[(r["writer"], r["conversation"])]
        prompt_halves.setdefault(r["prompt"], set()).add(h)
    assert all(len(h) == 1 for h in prompt_halves.values())
    assert card.partitions(list(reversed(rows))) == (split, exclusions, details)


def test_connected_component_cannot_be_faked_independent():
    rows = [dict(writer="w", conversation="all", prompt="p" + str(i % 10)) for i in range(20)]
    split, exclusions, details = card.partitions(rows)
    assert not split and not details
    assert exclusions["single_connected_prompt_conversation_component"] == 1


def test_partition_ignores_choices():
    rows = [dict(writer="w", conversation="c" + str(i), prompt="p" + str(i % 10), choice=0) for i in range(20)]
    before = card.partitions(rows)
    for r in rows: r["choice"] = 3
    assert card.partitions(rows) == before


def test_complete_handler_private_table_and_fresh_replay(tmp_path):
    inputs = fixture(tmp_path / "input"); output = tmp_path / "out"
    report = card.execute(output, inputs, {"fixture": True})
    assert report["split_supported_annotators"] == 5
    assert report["comparisons"]["records"] == 100
    assert card.verify(output, inputs, {"fixture": True})["verified"]
    with gzip.open(output / "COMPARISONS.jsonl.gz", "rt", encoding="utf8") as stream:
        rows = [json.loads(x) for x in stream]
    assert len(rows[0]["candidates"]) == 4
    assert len(rows[0]["writer"]) == 64
    assert "private text" not in json.dumps(report)
    assert "private reason" not in json.dumps(report)


def test_source_and_completion_refusal(tmp_path):
    inputs = fixture(tmp_path / "input")
    completion = Path(inputs["ca0_complete"]); value = json.loads(completion.read_text())
    value["fresh_process_verified"] = False; completion.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="fresh complete"):
        card.execute(tmp_path / "out", inputs, {"fixture": True})


def test_changed_private_output_is_refused(tmp_path):
    inputs = fixture(tmp_path / "input"); output = tmp_path / "out"
    card.execute(output, inputs, {"fixture": True})
    with (output / "TEXTS.jsonl.gz").open("ab") as stream: stream.write(b"changed")
    with pytest.raises(ValueError, match="recomputation"):
        card.verify(output, inputs, {"fixture": True})
