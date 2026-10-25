"""Known sensitivity/criterion separation and no circular reference fits."""
import copy
import json
from pathlib import Path

import numpy as np
import pytest
from scipy.special import ndtr

from runners.drive.cards import week3_sdt as card
from runners.drive.cards.menus_io import write


def fixture(root, writers=6):
    rng = np.random.default_rng(34); sessions = []; records = []; vectors = []
    for wi in range(writers):
        writer = f"w{wi}"
        for si in range(4):
            sid = f"w{wi}s{si}"; start = si * 10000; rows = []
            for di in range(8):
                key = sid + "-" + str(di); quality = (di - 3.5) / 3
                handling = "accept" if rng.random() < ndtr(-.2 + (wi + 1) / 5 * quality) else "dismiss"
                rows.append(dict(key=key, writer=writer, session=sid, prompt="p" + str(si % 2),
                    session_time=start, open_at=start + di * 100 + 1, resolved_at=start + di * 100 + 50,
                    handling=handling, document="context", menu=["alpha", "beta"], decision_index=di))
                offset = len(vectors); vectors.extend([[quality, 0., 1.], [quality, .1, 0.], [quality, .2, 1.]])
                records.append(dict(key=key, writer=writer, session=sid, context=offset,
                    options=[offset + 1, offset + 2], cosine=[.2, .3], scalars=[[quality, 0, 1, 1], [quality, 1, 0, 1]]))
            sessions.append(dict(writer=writer, session=sid, prompt="p" + str(si % 2), timestamp=start,
                                 end_at=start + 900, rows=rows))
    root = Path(root); root.mkdir(parents=True, exist_ok=True)
    write(root / "sessions.json", sessions); write(root / "records.json", records)
    np.save(root / "vectors.npy", np.array(vectors))
    return {"sessions": str(root / "sessions.json"), "records": str(root / "records.json"),
            "vectors": str(root / "vectors.npy")}


def test_known_answer_criterion_and_sensitivity_separate():
    score = np.repeat(np.linspace(-3, 3, 61), 200)
    unit = np.tile((np.arange(200) + .5) / 200, 61)
    for intercept, sensitivity in ((0., .8), (-.7, .8), (0., 1.6), (0., 0.)):
        truth = (unit < ndtr(intercept + sensitivity * score)).astype(float)
        fitted = card.probit_fit(score, truth)
        assert fitted["criterion"] == pytest.approx(-intercept, abs=.025)
        assert fitted["sensitivity"] == pytest.approx(sensitivity, abs=.025)


def test_population_features_ignore_own_choice_history(tmp_path):
    inputs = fixture(tmp_path); sessions = json.loads(Path(inputs["sessions"]).read_text())
    records = json.loads(Path(inputs["records"]).read_text()); vectors = np.load(inputs["vectors"])
    original = card.population_features(sessions, records, vectors)
    changed = copy.deepcopy(sessions)
    for session in changed:
        for row in session["rows"]:
            row["handling"] = "ignore" if row["handling"] == "accept" else "edit"
    other = card.population_features(changed, records, vectors)
    np.testing.assert_array_equal(original[2], other[2])
    np.testing.assert_array_equal(original[3], other[3])


def test_held_writer_outcome_changes_cannot_change_own_reference(tmp_path):
    inputs = fixture(tmp_path); sessions = json.loads(Path(inputs["sessions"]).read_text())
    records = json.loads(Path(inputs["records"]).read_text()); vectors = np.load(inputs["vectors"])
    sessions, rows, scalars, embeddings = card.population_features(sessions, records, vectors)
    before, _, proof = card.reference_scores(sessions, rows, scalars, embeddings, {}, dimensions=2)
    changed = copy.deepcopy(rows)
    for row in changed:
        if row["writer"] == "w0": row["handling"] = "edit" if row["handling"] == "dismiss" else "ignore"
    after, _, _ = card.reference_scores(sessions, changed, scalars, embeddings, {}, dimensions=2)
    mask = np.array([r["writer"] == "w0" for r in rows])
    np.testing.assert_array_equal(before[mask], after[mask])
    assert proof["w0"]["own_decisions_in_fit"] == 0


def test_permutation_preserves_prompt_specific_writer_counts(tmp_path):
    from collections import Counter
    inputs = fixture(tmp_path); sessions = json.loads(Path(inputs["sessions"]).read_text())
    assignment = card.permute_sessions(sessions, 9)
    assert Counter((r["prompt"], r["writer"]) for r in sessions) == Counter((r["prompt"], assignment[r["session"]]) for r in sessions)
    assert assignment == card.permute_sessions(list(reversed(sessions)), 9)
    assert any(assignment[r["session"]] != r["writer"] for r in sessions)


def test_constant_reliability_is_not_positive():
    assert card.correlation(np.ones((12, 2))) is None
    assert card.correlation(np.c_[np.arange(12), np.arange(12)]) == pytest.approx(1.)


def test_full_mode_cannot_silently_reduce_reference_bank(tmp_path):
    with pytest.raises(ValueError, match="1000"):
        card.execute(tmp_path, {}, {"permutation_draws": 2})


def test_actual_handler_and_fresh_replay(tmp_path):
    inputs = fixture(tmp_path / "input"); config = dict(mode="fixture", permutation_draws=2, bootstrap_draws=4, pca_dimensions=2)
    output = tmp_path / "out"
    result = card.execute(output, inputs, config)
    assert result["future_own_history_used"] is False
    assert card.verify(output, inputs, config)["verified"]
    before = (output / "permutations/0000.json").read_bytes()
    assert card.execute(output, inputs, config) == result
    assert (output / "permutations/0000.json").read_bytes() == before
    value = json.loads((output / "REAL.json").read_text())
    value["profiles"]["w0"]["halves"][0]["sensitivity"] += .1
    (output / "REAL.json").write_text(json.dumps(value))
    with pytest.raises(ValueError, match="recomputation"):
        card.verify(output, inputs, config)


def test_saved_checkpoint_yield_and_resume(tmp_path):
    inputs = fixture(tmp_path / "input"); config = dict(mode="fixture", permutation_draws=2, bootstrap_draws=4, pca_dimensions=2)
    output = tmp_path / "out"; output.mkdir()
    write(output / "YIELD_REQUEST.json", {"reason": "test"})
    assert card.execute(output, inputs, config)["status"] == "yielded"
    assert not (output / "SUMMARY.json").exists()
    (output / "YIELD_REQUEST.json").unlink()
    card.execute(output, inputs, config)
    assert card.verify(output, inputs, config)["verified"]
