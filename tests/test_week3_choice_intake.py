"""CA0 counts without exposing choices, text, or annotator identifiers."""
import csv
import json
from pathlib import Path

import pytest

from runners.drive.cards import week3_choice_intake as card


def source(tmp_path, rows):
    path = tmp_path / "source.csv"
    with path.open("w", encoding="utf8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader(); writer.writerows(rows)
    return path


def row(i=0, w="writer-private", prompt="a prompt"):
    value = dict(conversation_id=str(i), annotator_id=w, annotator_country="us",
                 assigned_lang="en", wave="1")
    for turn in card.TURNS:
        for suffix in ("prompt", "preferred_response", "feedback", *card.OPTIONS):
            value[f"{turn}_turn_{suffix}"] = ""
    value.update(first_turn_prompt=prompt, first_turn_preferred_response="response_c",
                 first_turn_feedback="private reason")
    for option in card.OPTIONS:
        value["first_turn_" + option] = "private text " + option
    return value


def test_counts_turns_separately_and_privacy(tmp_path):
    r = row()
    for suffix in ("prompt", "preferred_response", "feedback", *card.OPTIONS):
        r["second_turn_" + suffix] = r["first_turn_" + suffix]
    result = card.census(source(tmp_path, [r]))
    assert result["conversation_rows"] == 1
    assert result["turn_counts"]["valid_comparisons"] == 2
    serialized = json.dumps(result)
    assert "writer-private" not in serialized and "private text" not in serialized
    assert "response_c" not in serialized


def test_missing_candidate_and_unrecognized_choice_excluded(tmp_path):
    a, b = row(), row(1)
    a["first_turn_response_d"] = ""
    b["first_turn_preferred_response"] = "E"
    result = card.census(source(tmp_path, [a, b]))
    assert result["turn_counts"].get("valid_comparisons", 0) == 0
    assert result["turn_counts"]["excluded_turns"] == 2


def test_missing_prior_turn_excludes_later_context(tmp_path):
    r = row()
    for suffix in ("prompt", "preferred_response", "feedback", *card.OPTIONS):
        r["third_turn_" + suffix] = r["first_turn_" + suffix]
    result = card.census(source(tmp_path, [r]))
    assert result["turn_counts"]["valid_comparisons"] == 1
    assert result["exclusion_reasons_nonexclusive"]["incomplete_prior_turn"] == 1


def test_eligibility_and_shared_prompt_rule(tmp_path):
    rows = [row(w * 20 + j, "w" + str(w), "prompt " + str(j % 10))
            for w in range(5) for j in range(20)]
    result = card.census(source(tmp_path, rows))
    assert result["eligible_annotators"] == 5 and result["eligible_comparisons"] == 100
    assert result["comparisons_on_prompts_shared_by_five_eligible_annotators"] == 100
    assert result["permutation_route"] == "within_prompt"


def test_duplicate_identity_refused(tmp_path):
    with pytest.raises(ValueError, match="duplicate"):
        card.census(source(tmp_path, [row(), row()]))


def test_hash_pin_and_fresh_replay(tmp_path):
    path = source(tmp_path, [row()]); inputs = {"source": str(path)}
    with pytest.raises(ValueError, match="source changed"):
        card.execute(tmp_path / "bad", inputs, {"source_sha256": "0" * 64})
    root = tmp_path / "out"
    card.execute(root, inputs, {})
    assert card.verify(root, inputs, {})["verified"]
    value = json.loads((root / "SUMMARY.json").read_text())
    value["counts"]["conversation_rows"] += 1
    (root / "SUMMARY.json").write_text(json.dumps(value))
    with pytest.raises(ValueError, match="recomputation"):
        card.verify(root, inputs, {})
