"""The opposite-half cost pilot cannot emit a smaller-cohort finding."""
import json
from pathlib import Path

import pytest

from runners.drive.cards import week3_alignment_culture_timing as card
from runners.drive.cards.menus_io import read
from tests.test_week3_alignment_stats import fixture


def test_cost_handler_replays_without_hypothesis_readout(tmp_path, monkeypatch):
    inputs = fixture(tmp_path/"inputs"); output = tmp_path/"output"
    def forbidden(*args, **kwargs): raise AssertionError("timing cannot score scientific outcomes")
    monkeypatch.setattr(card.stats, "losses", forbidden)
    monkeypatch.setattr(card.stats, "evaluate", forbidden)
    monkeypatch.setattr(card.stats, "summarize", forbidden)
    result = card.execute(output, inputs, {"fixture":True})
    assert result["scientific_inference"] is False and result["train_half"] == 1
    assert result["fixed_annotators_full"] == result["sampled_annotators_with_training"] == 5
    assert card.verify(output, inputs, {"fixture":True})["verified"]
    timing = read(output/"TIMING.json")
    assert timing["all_1000_references_real_and_fresh_replay_projection_cpu_seconds"] == timing["one_opposite_half_full_fit_projection_cpu_seconds"]*2002


def test_pilot_requires_exact_feature_scope(tmp_path):
    inputs = fixture(tmp_path/"inputs")
    with pytest.raises(ValueError, match="ten-percent"):
        card.execute(tmp_path/"output", inputs, {})


def test_changed_timing_summary_refused(tmp_path):
    inputs = fixture(tmp_path/"inputs"); output = tmp_path/"output"
    card.execute(output, inputs, {"fixture":True})
    path = output/"SUMMARY.json"; value = read(path); value["train_half"] = 0
    path.write_text(json.dumps(value), encoding="utf8")
    with pytest.raises(ValueError, match="recomputation"):
        card.verify(output, inputs, {"fixture":True})
