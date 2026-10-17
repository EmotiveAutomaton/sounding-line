import json

import numpy as np
import pytest

from runners.drive.cards import timing_checkpoint as checkpoint
from runners.drive.cards.timing_stats import regression


def observations():
    rng = np.random.default_rng(35)
    x, y, writers = [], [], []
    for w in range(8):
        for i in range(12):
            nuisance = rng.normal()
            x.append([i % 2, nuisance])
            y.append(10 * w + 2 * (i % 2) - nuisance + rng.normal(0, .1))
            writers.append(str(w))
    return x, y, writers


def test_saved_boundary_resume_is_exact_and_does_not_repeat_saved_fits(tmp_path, monkeypatch):
    args = observations()
    expected = regression(*args, within=True, draws=100)
    first = checkpoint.regression(*args, within=True, draws=100, checkpoint=tmp_path,
                                  yield_requested=lambda: True)
    assert first == dict(status="yielded", completed_draws=10, total_draws=100)
    real_fit, calls = checkpoint.fit, []
    def counted(*a, **k):
        calls.append(1)
        return real_fit(*a, **k)
    monkeypatch.setattr(checkpoint, "fit", counted)
    resumed = checkpoint.regression(*args, within=True, draws=100, checkpoint=tmp_path)
    assert resumed == expected
    assert len(calls) == 91  # point estimate plus only the remaining 90 draws
    assert 1.9 < resumed["effect"] < 2.1


def test_changed_input_and_corrupt_checkpoint_refuse_resume(tmp_path):
    x, y, writers = observations()
    checkpoint.regression(x, y, writers, within=True, draws=100, checkpoint=tmp_path,
                          yield_requested=lambda: True)
    changed = list(y); changed[0] += 1
    with pytest.raises(ValueError, match="binding changed"):
        checkpoint.regression(x, changed, writers, within=True, draws=100, checkpoint=tmp_path)
    p = tmp_path / "block-00000.json"
    record = json.loads(p.read_text()); record["samples"][0] += 1
    p.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="hash changed"):
        checkpoint.regression(x, y, writers, within=True, draws=100, checkpoint=tmp_path)


def test_null_and_negative_direction_remain_distinct():
    x, y, writers = observations()
    negative = checkpoint.regression(x, [-v for v in y], writers, within=True, draws=100)
    assert negative["state"] == "negative"
    assert checkpoint.regression(x, y, ["one"] * len(y), within=True)["state"] == "invalid"
