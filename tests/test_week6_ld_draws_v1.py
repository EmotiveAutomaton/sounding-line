"""Manufactured draw, interruption and replay checks for the diary launcher."""
from types import SimpleNamespace

import numpy as np
import pytest

from runners.drive.cards import week6_ld_draws_v1 as engine
from runners.drive.cards import week6_ld_runtime_v1 as runtime
from runners.drive.cards.batch_runtime import freeze


class Producer:
    @staticmethod
    def evaluate(prepared, w, guard, *, verify=False):
        guard()
        w = np.ones(4, dtype=int) if w is None else w
        return {"a": float(w @ np.arange(4)) / 4, "b": None if w[1] == 0 else float(w[1])}


def panel():
    return SimpleNamespace(people=4, metadata={"rows": 16}, specs={
        "a": dict(role="primary", bar=.1), "b": dict(role="diagnostic")})


def test_paused_prefix_full_replay_and_invalid_draws(tmp_path):
    original = tmp_path / "execution"
    with pytest.raises(engine.RequestedYield):
        engine.run_draws(original, Producer, panel(), "0056", lambda: None, max_new_draws=37)
    assert len(engine.load_blocks(original, ["a", "b"])) == 37
    answer = engine.run_draws(original, Producer, panel(), "0056", lambda: None)
    assert answer["metrics"]["a"]["interval"] is not None
    assert answer["metrics"]["b"]["interval"] is None
    assert 0 < answer["metrics"]["b"]["invalid_draws"] < engine.DRAWS
    replay = engine.run_draws(tmp_path / "verify", Producer, panel(), "0056",
                              lambda: None, verify=True, original=original)
    assert replay["verified"] and replay["metrics"] == answer["metrics"]


def test_different_source_seed_and_resumed_schema_are_rejected(tmp_path):
    with pytest.raises(engine.RequestedYield):
        engine.run_draws(tmp_path, Producer, panel(), "0056", lambda: None, max_new_draws=2)
    with pytest.raises(ValueError, match="Checkpoint source"):
        engine.run_draws(tmp_path, Producer, panel(), "0057", lambda: None)


def test_gapped_block_cannot_skip_work(tmp_path):
    freeze(tmp_path / "draws-0001.json", {"start": 1, "values": [[.4]]})
    with pytest.raises(ValueError, match="Noncontiguous"):
        engine.load_blocks(tmp_path, ["a"])


def test_replay_disagreement_and_missing_rows_are_rejected():
    with pytest.raises(ValueError, match="identification"):
        engine.compare([None], [0.])
    with pytest.raises(ValueError, match="numerically"):
        engine.compare([.1], [.1001])
    with pytest.raises(ValueError, match="2,000"):
        engine.summarize(["a"], {"a": {}}, [1.], [[1.]])


def test_source_review_and_control_precede_human_reads(tmp_path):
    with pytest.raises(ValueError, match="inputs"):
        runtime.operate("LD3", Producer, tmp_path, {"source_path": "not-a-source"},
                        {}, verify=False)
