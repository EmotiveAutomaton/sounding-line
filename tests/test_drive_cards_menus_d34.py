import numpy as np
import pytest

from runners.drive.cards import menus_d34 as d34
from runners.drive.cards import menus_d34_stats as stats
from runners.drive.cards.menus_io import read, write, sha256


def test_centering_before_product_retains_known_slope_and_transfer():
    z = np.tile(np.arange(-5, 6, dtype=float), 3)[:, None]
    y = (z[:, 0] > 0).astype(float); r = y - .5
    sessions = np.repeat(["a", "b", "c"], 11)
    result = stats.writer_statistic(r, np.full(len(r), .5), sessions, np.repeat([0, 1, 2], 11),
        {"content": z}, permutations=100, seed=7)
    assert result["arms"]["content"]["observed"] == pytest.approx(1.)
    assert result["arms"]["content"]["last_session"]["balanced_accuracy"] > .9
    assert abs(np.mean(result["arms"]["content"]["null"])) < .2
    # Centering the product, the rejected ambiguous implementation, is identically zero.
    product = r[:11, None] * z[:11]
    assert np.allclose((product - product.mean(0)).mean(0), 0)


def test_zero_direction_and_singleton_permutations_are_invalid():
    result = stats.writer_statistic([1., -1., 1., -1.], [.5]*4, ["a", "a", "b", "b"], [0, 0, 1, 1],
                                    {"content": np.zeros((4, 2))}, 20)
    assert stats.summarize({"x": result, "y": result}, {})["state"] == "invalid"
    result = stats.writer_statistic([.1, -.1], [.1, .9], ["a", "b"], [0, 1], {"content": np.eye(2)}, 20)
    assert result["movable_residuals"] == 0


def test_verdicts_are_exhaustive_and_power_cannot_rescue_a_variant():
    summary = dict(state="positive", content_minus_variants={"state": {"state": "positive"}, "reader": {"state": "positive"}},
                   variants={"content": {"state": "positive"}, "state": {"state": "null"}, "reader": {"state": "null"}},
                   last_session_transfer={"state": "positive"})
    assert stats.verdict(summary, 0) == "HIDDEN GOAL"
    summary["last_session_transfer"]["state"] = "null"
    assert stats.verdict(summary, 5) == "UNDETERMINED"
    summary["state"] = "null"
    assert stats.verdict(summary, 4) == "NOISE AT THIS POWER"
    assert stats.verdict(summary, 3) == "UNDETERMINED"
    summary["variants"]["state"]["state"] = "positive"
    assert stats.verdict(summary, 5) == "STATE OR MISFIT"


def inputs_for(tmp_path):
    sessions, records, predictions, vectors = [], [], [], []; rng = np.random.default_rng(22)
    for writer in "abc":
        for number in range(3):
            rows = []; session = writer + str(number); start = number * 10000
            for i in range(8):
                key = session + str(i); truth = "accept" if i % 2 else "dismiss"; option = rng.normal(scale=.02, size=20)
                option[0] = 1 if truth == "accept" else -1
                ids = [len(vectors), len(vectors) + 1]; vectors.extend([option, option.copy()])
                rows.append(dict(key=key, writer=writer, session=session, session_time=start, open_at=start + i*10,
                    resolved_at=start+i*10+1, handling=truth, menu=["a", "b"], document="context", decision_index=i))
                records.append(dict(key=key, writer=writer, session=session, options=ids))
                predictions.append(dict(key=key, writer=writer, truth=truth, probabilities={"B-mixlogit": [.5, .1, .3, .1]}))
            sessions.append(dict(writer=writer, session=session, timestamp=start, end_at=start+100, rows=rows))
    write(tmp_path / "sessions.json", sessions); write(tmp_path / "records.json", records)
    write(tmp_path / "PREDICTIONS.json", predictions); np.save(tmp_path / "vectors.npy", vectors)
    write(tmp_path / "COMPLETE.json", dict(status="COMPLETE", outputs={"PREDICTIONS.json": sha256(tmp_path / "PREDICTIONS.json")}))
    controls = []
    for i in range(5):
        folder = tmp_path / f"control{i}"; write(folder / "PREDICTIONS.json", predictions)
        write(folder / "RESULT.json", dict(cell=dict(effect="content", delta=.4, replicate=i)))
        write(folder / "COMPLETE.json", dict(status="COMPLETE", outputs={name: sha256(folder / name) for name in ("PREDICTIONS.json", "RESULT.json")}))
        item = dict(replicate=i, predictions=str(folder / "PREDICTIONS.json"), result=str(folder / "RESULT.json"), completion=str(folder / "COMPLETE.json"))
        item["sha256"] = {key: sha256(item[key]) for key in ("predictions", "result", "completion")}; controls.append(item)
    write(tmp_path / "controls.json", controls)
    return {"sessions": str(tmp_path / "sessions.json"), "records": str(tmp_path / "records.json"), "vectors": str(tmp_path / "vectors.npy"),
            "predictions": str(tmp_path / "PREDICTIONS.json"), "prediction_completion": str(tmp_path / "COMPLETE.json"), "positive_controls": str(tmp_path / "controls.json")}


def test_entrypoint_primary_saved_recompute_and_other_writer_pca(tmp_path):
    inputs = inputs_for(tmp_path); config = dict(seed=20261017, permutations=1000, dimensions=16, bootstrap=100)
    report = d34.execute(tmp_path / "out", inputs, config)
    assert report["state"] == "positive" and report["positive_control_detections"] == 5
    assert d34.verify(tmp_path / "out", inputs, config)["verified"]
    pca = read(tmp_path / "out/PCA.json")
    assert all(value["training_options"] == 96 for value in pca.values())
    sessions = read(inputs["sessions"]); records = read(inputs["records"]); vectors = np.load(inputs["vectors"])
    own_options = [i for row in records if row["writer"] == "a" for i in row["options"]]
    vectors[own_options] += 10
    _, _, changed = d34.representations(sessions, records, vectors)
    np.testing.assert_array_equal(changed["a"]["components"], pca["a"]["components"])
    assert d34.stats.states.__name__.endswith("states_v2")
