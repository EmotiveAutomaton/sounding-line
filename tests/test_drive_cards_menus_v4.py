import copy
import numpy as np
import pytest
from scipy.special import expit

from runners.drive.cards import menus_v4 as v4
from runners.drive.cards.menus_v4_stats import conditional_mode, variance_reader, predict, taste_directions
from runners.drive.cards.menus_io import write


def fixture():
    rng = np.random.default_rng(9); sessions = []; keys = []
    for writer in ("a", "b", "c"):
        for session in range(5):
            name = f"{writer}{session}"; rows = []
            for decision in range(4):
                key = name + "-" + str(decision); keys.append(key)
                rows.append(dict(key=key, writer=writer, session=name, prompt="p", session_time=session * 1000,
                    open_at=session * 1000 + decision * 100, resolved_at=session * 1000 + decision * 100 + 1,
                    handling="ignore", decision_index=decision, document="context", menu=["one", "two"]))
            sessions.append(dict(writer=writer, session=name, prompt="p", timestamp=session * 1000, end_at=session * 1000 + 500, rows=rows))
    keys.sort(); lexical = rng.normal(size=(len(keys) * 2, 16)); mini = rng.normal(size=lexical.shape)
    basis, _ = np.linalg.qr(rng.normal(size=(16, 4)))
    geometry = dict(keys=keys, slices=np.array([(2 * i, 2 * i + 2) for i in range(len(keys))]),
        lexical=lexical, mini=mini, basis=basis, menu_lexical=lexical.reshape(-1, 2, 16).mean(1),
        menu_mini=mini.reshape(-1, 2, 16).mean(1))
    base = {key: [.25] * 4 for key in keys}
    return sessions, base, geometry


def test_null_preserves_generating_probabilities_and_ignores_original_outcomes():
    sessions, base, geometry = fixture()
    generated, trace, _ = v4.construct(sessions, base, geometry, "habit", 0., 123)
    assert all(row["probabilities"] == [.25] * 4 for row in trace)
    changed = copy.deepcopy(sessions)
    for session in changed:
        for row in session["rows"]:
            row["handling"] = "accept"
    assert trace == v4.construct(changed, base, geometry, "habit", 0., 123)[1]
    assert all(row["previous_key"] is None or row["previous_key"] != row["key"] for row in trace)


def test_taste_menu_aggregation_and_oracle_exact_rank():
    sessions, base, geometry = fixture()
    _, trace, oracle = v4.construct(sessions, base, geometry, "taste_matched", .4, 123)
    for row in trace:
        assert row["scalar"] == pytest.approx(np.mean(row["option_projections"]))
        assert row["shift"] == pytest.approx(.4 * row["scalar"])
        assert len(oracle[row["key"]]) == 4
    for writer in ("a", "b", "c"):
        values = [row["scalar"] for row in trace if row["writer"] == writer]
        assert np.mean(values) == pytest.approx(0, abs=1e-14)
        assert np.std(values) == pytest.approx(1)


def test_habit_kernel_is_recursive_from_simulated_resolved_choices():
    sessions, base, geometry = fixture()
    generated, trace, _ = v4.construct(sessions, base, geometry, "habit", .4, 123)
    rows = sorted([row for session in generated for row in session["rows"]], key=lambda row: row["key"])
    kernels = v4.kernel_features(rows, base, .7)[:, 0]
    bykey = {row["key"]: row["kernel"] for row in trace}
    assert np.allclose(kernels, [bykey[row["key"]] for row in rows])
    assert all(row["kernel"] == 0 for row in trace if row["previous_key"] is None)


def test_balanced_null_marginal_likelihood_cannot_become_signal():
    x = np.tile(np.array([-1., -1., 1., 1.]), 20)[:, None]
    y = np.tile([0., 1., 0., 1.], 20)
    writers = np.repeat(np.arange(5), 16)
    fit = variance_reader(x, y, np.full(len(y), .5), writers)
    assert fit["likelihood_ratio"] < 1e-7
    assert fit["variance"][0] < 1e-7
    assert not fit["detected"]


def test_planted_random_slope_is_detected_and_improves_predictions():
    rng = np.random.default_rng(16); writers = np.repeat(np.arange(12), 80)
    x = rng.normal(size=(len(writers), 1)); signs = np.where(np.arange(12) % 2, -1., 1.)
    y = rng.binomial(1, expit(1.5 * signs[writers] * x[:, 0])).astype(float)
    fit = variance_reader(x, y, np.full(len(y), .5), writers)
    assert fit["detected"]
    p = predict(fit, x, np.tile([.5, 1/6, 1/6, 1/6], (len(y), 1)), writers)
    assert np.allclose(p.sum(1), 1)
    assert np.mean((p[:, 0] - y) ** 2) < np.mean((.5 - y) ** 2)


def test_directions_cannot_read_scored_tail_labels():
    rng = np.random.default_rng(8); x = rng.normal(size=(100, 16)); y = rng.binomial(1, .4, size=100)
    writers = np.repeat(np.arange(5), 20); train = np.arange(100) % 20 < 12
    first = taste_directions(x, y, np.full(100, .4), writers, train, 4)
    y[~train] = 1 - y[~train]
    second = taste_directions(x, y, np.full(100, .4), writers, train, 4)
    assert np.array_equal(first, second)


def test_pilot_actual_entrypoint_and_fresh_primary_recompute(tmp_path):
    sessions, base, _ = fixture(); rng = np.random.default_rng(12)
    records = []; vectors = []
    for session in sessions:
        for row in session["rows"]:
            option_ids = []
            row["menu"] = ["".join(rng.choice(list("abcdefghijklmnopqrstuvw"), size=40)) for _ in range(2)]
            for option in row["menu"]:
                option_ids.append(len(vectors)); value = rng.normal(size=32); vectors.append(value / np.linalg.norm(value))
            records.append(dict(key=row["key"], writer=row["writer"], session=row["session"], options=option_ids))
    write(tmp_path / "sessions.json", sessions); write(tmp_path / "records.json", records)
    write(tmp_path / "predictions.json", [dict(key=key, probabilities={"B-pop": value}) for key, value in base.items()])
    np.save(tmp_path / "vectors.npy", vectors, allow_pickle=False)
    inputs = {key: str(tmp_path / (key + (".npy" if key == "vectors" else ".json")))
              for key in ("sessions", "records", "predictions", "vectors")}
    report = v4.execute(tmp_path / "pilot", inputs, dict(mode="pilot", seed=20261017))
    assert report["execution_only"] and report["worlds"] == 3
    assert v4.verify(tmp_path / "pilot", inputs, dict(mode="pilot", seed=20261017))["verified"]


@pytest.mark.parametrize("zero,medium,large,size,label", [
    (.1, .8, .8, True, "sees"), (.1, .7, .8, True, "sees large only"),
    (.2, 1., 1., True, "blind"), (0., 1., 1., False, "blind"),
    (0., .7, .7, True, "blind")])
def test_exhaustive_instrument_labels(zero, medium, large, size, label):
    assert v4.instrument_label(zero, medium, large, size) == label
