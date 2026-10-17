import numpy as np
import pytest

from runners.drive.cards import menus_p4 as pilot
from runners.drive.cards import menus_p4_primary as primary
from runners.drive.cards import menus_p4_extension as extension
from runners.drive.cards.menus_io import read, write


def inputs_for(tmp_path):
    sessions, records = [], []
    for writer in "abc":
        for number in range(5):
            start = number * 10000; name = f"{writer}{number}"; rows = []
            for decision in range(8):
                key = f"{name}-{decision}"; feature = decision % 4
                rows.append(dict(key=key, writer=writer, session=name, prompt="p", session_time=start,
                    open_at=start + decision * 100 + 1, resolved_at=start + decision * 100 + 50,
                    handling=pilot.ACTIONS[feature], document="some context", menu=["suggestion"],
                    decision_index=decision, session_end=start + 900))
                records.append(dict(key=key, writer=writer, session=name, context=feature, options=[feature],
                                    cosine=[1.], scalars=[[10., 1., 1., 0.]]))
            sessions.append(dict(writer=writer, session=name, timestamp=start, end_at=start+900, prompt="p", rows=rows))
    write(tmp_path / "sessions.json", sessions); write(tmp_path / "records.json", records)
    np.save(tmp_path / "vectors.npy", np.eye(4), allow_pickle=False)
    return {key: str(tmp_path / name) for key, name in (("sessions", "sessions.json"), ("records", "records.json"), ("vectors", "vectors.npy"))}


def prepared(tmp_path):
    inputs = inputs_for(tmp_path)
    config = dict(seed=20261017, bootstrap_draws=100, pca_dimensions=3)
    pilot.execute(tmp_path / "pilot", inputs, dict(config, mode="pilot"))
    write(tmp_path / "pilot_plan.json", dict(config=dict(config, mode="pilot"), inputs=inputs))
    return dict(inputs, pilot_summary=str(tmp_path / "pilot/SUMMARY.json"), pilot_plan=str(tmp_path / "pilot_plan.json")), config


def test_primary_matches_pilot_without_computing_extension_and_conditional_reuse(tmp_path, monkeypatch):
    inputs, config = prepared(tmp_path); calls = []
    original = pilot.select_offset
    def counted(*args, **kwargs):
        calls.append(True)
        return original(*args, **kwargs)
    monkeypatch.setattr(pilot, "select_offset", counted)
    report = primary.execute(tmp_path / "full", inputs, config)
    assert len(calls) == 6  # One backbone offset for each of three writers in each arm.
    assert report["state"] == "positive" and report["primary"]["estimate"] > 0
    assert report["shuffle_control"]["state"] != "positive"
    assert report["extension_computed"] is False
    assert report["primary"]["standard_error"] >= 0
    assert "p_value_approx" in report["primary"]
    assert primary.verify(tmp_path / "full", inputs, config)["verified"]
    first = {row["key"]: row for row in read(tmp_path / "pilot/PREDICTIONS.json")}
    for row in read(tmp_path / "full/PREDICTIONS.json"):
        assert set(row["probabilities"]) == {"backbone", "content"}
        if row["key"] in first:
            for arm in ("backbone", "content"):
                np.testing.assert_array_equal(row["probabilities"][arm], first[row["key"]]["probabilities"][arm])
    plan = tmp_path / "primary_plan.json"
    write(plan, dict(module="runners.drive.cards.menus_p4_primary", config=config, inputs=inputs))
    extension_inputs = {key: inputs[key] for key in ("sessions", "records", "vectors")}
    extension_inputs.update(primary_summary=str(tmp_path / "full/SUMMARY.json"), primary_plan=str(plan))
    extended = extension.execute(tmp_path / "extension", extension_inputs, config)
    assert len(calls) == 12
    assert extended["conditional_extension"]
    assert extension.verify(tmp_path / "extension", extension_inputs, config)["verified"]
    for row in read(tmp_path / "extension/PREDICTIONS.json"):
        if row["key"] in first:
            np.testing.assert_array_equal(row["probabilities"]["content_writer"], first[row["key"]]["probabilities"]["content_writer"])


def test_yield_retains_completed_units_and_resume_skips_them(tmp_path, monkeypatch):
    inputs, config = prepared(tmp_path); output = tmp_path / "full"; calls = []
    original = primary.fit_recipient
    def controlled(*args, **kwargs):
        result = original(*args, **kwargs); calls.append(args[0]["writer"])
        if len(calls) == 2:
            write(output / "YIELD_REQUEST.json", {"reason": "synthetic boundary test"})
        return result
    monkeypatch.setattr(primary, "fit_recipient", controlled)
    report = primary.execute(output, inputs, config)
    assert report == dict(status="yielded", card="P4", completed_recipients=1)
    assert not (output / "SUMMARY.json").exists()
    assert not (output / "PREDICTIONS.json").exists()
    assert (output / "FIRST_TENTH.json").exists()
    (output / "YIELD_REQUEST.json").unlink()  # Test-owned synthetic request; production owner alone clears it.
    report = primary.execute(output, inputs, config)
    assert calls == ["a", "a", "b", "b", "c", "c"]
    assert primary.verify(output, inputs, config)["verified"]
    with (output / "FEATURES.npz").open("ab") as stream:
        stream.write(b"mutation")
    with pytest.raises(ValueError, match="feature checkpoint changed"):
        primary.execute(output, inputs, config)


def test_extension_refuses_null_before_loading_models(tmp_path):
    write(tmp_path / "SUMMARY.json", {"state": "null"})
    with pytest.raises(ValueError, match="positive or marginal"):
        extension.execute(tmp_path / "extension", {"primary_summary": str(tmp_path / "SUMMARY.json")}, {})


def test_exact_zero_and_writer_cluster_uncertainty():
    predictions = [dict(writer=writer, session=writer, truth="accept", probabilities={"backbone": [.25]*4, "content": [.25]*4}) for writer in "abc"]
    report = primary.summarize(predictions, dict(bootstrap_draws=100))
    assert report["state"] == "null"
    assert report["primary"]["estimate"] == report["primary"]["standard_error"] == 0
    assert report["primary"]["p_value_approx"] == 1
