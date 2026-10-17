import copy
import numpy as np
import pytest

from runners.drive.cards import menus_p4 as p4
from runners.drive.cards.menus_io import write


def minimal_sessions():
    sessions = []
    for writer in ("a", "b", "c"):
        for session in range(5):
            start = session * 10000
            name = f"{writer}{session}"
            rows = []
            for decision in range(8):
                rows.append(dict(key=f"{name}-{decision}", writer=writer, session=name, prompt="p", session_time=start,
                    open_at=start + decision * 100 + 1, resolved_at=start + decision * 100 + 50,
                    handling=p4.ACTIONS[decision % 4], document="some context", menu=["suggestion"], decision_index=decision,
                    session_end=start + 900))
            sessions.append(dict(writer=writer, session=name, timestamp=start, end_at=start + 900, prompt="p", rows=rows))
    return sessions


def test_recipient_cuts_donor_future_before_any_label_access():
    sessions = minimal_sessions()
    for session in sessions:
        if session["writer"] == "b":
            session["timestamp"] += 100000
            session["end_at"] += 100000
    splits, _ = p4.chronological_partitions(sessions)
    selected = p4.recipient_split("a", splits)
    assert all(session["writer"] != "b" for session in selected["train"])
    assert selected["excluded_future_training"] == ["b0", "b1", "b2"]
    assert selected["reason"] is None


def test_overlap_and_empty_partitions_are_explicit():
    sessions = minimal_sessions()
    next(session for session in sessions if session["session"] == "a3")["end_at"] = 50000
    splits, _ = p4.chronological_partitions(sessions)
    selected = p4.recipient_split("a", splits)
    assert selected["excluded_overlapping_calibration"] == ["a3"]
    assert selected["reason"] == "chronology leaves fewer than 3/1/1 sessions"


def test_scoring_is_half_brier_and_equal_session_weight():
    assert p4.brier([[1, 0, 0, 0], [.25] * 4], [0, 0]).tolist() == [0, .375]
    assert p4.session_mean([0, 1, 1], [dict(session="a"), dict(session="b"), dict(session="b")]) == .5
    predictions = []
    for writer in ("a", "b", "c"):
        predictions.append(dict(writer=writer, session=writer, truth="accept", probabilities={
            "backbone": [.25] * 4, "content": [1, 0, 0, 0], "content_writer": [1, 0, 0, 0]}))
    report = p4.summarize(predictions, dict(bootstrap_draws=100))
    assert report["primary"]["estimate"] == .375
    assert report["extension"]["estimate"] == 0
    assert report["state"] == "positive"


def inputs_for(tmp_path):
    sessions = minimal_sessions(); records = []
    for session in sessions:
        for row in session["rows"]:
            feature = row["decision_index"] % 4
            records.append(dict(key=row["key"], writer=row["writer"], session=row["session"],
                context=feature, options=[feature], cosine=[1.], scalars=[[10., 1., 1., 0.]]))
    write(tmp_path / "sessions.json", sessions); write(tmp_path / "records.json", records)
    np.save(tmp_path / "vectors.npy", np.eye(4), allow_pickle=False)
    return {key: str(tmp_path / name) for key, name in (("sessions", "sessions.json"), ("records", "records.json"), ("vectors", "vectors.npy"))}


def test_end_to_end_fitted_constructed_signal_and_recompute(tmp_path):
    inputs = inputs_for(tmp_path)
    config = dict(seed=20261017, bootstrap_draws=100, pca_dimensions=3)
    report = p4.execute(tmp_path / "out", inputs, config)
    assert report["primary"]["estimate"] > 0
    assert report["shuffle_control"]["state"] != "positive"
    assert p4.verify(tmp_path / "out", inputs, config)["verified"]


def test_future_outcomes_do_not_enter_first_test_features(tmp_path):
    inputs = inputs_for(tmp_path)
    sessions = p4.read(inputs["sessions"]); records = p4.read(inputs["records"]); vectors = np.load(inputs["vectors"])
    rows, base, scalar, embedding = p4.prefix_features(sessions, records, vectors)
    changed = copy.deepcopy(sessions)
    for session in changed:
        if session["session"].endswith("4"):
            for row in session["rows"]:
                row["handling"] = "ignore"
    rows2, base2, scalar2, embedding2 = p4.prefix_features(changed, records, vectors)
    first = [i for i, row in enumerate(rows) if row["session"].endswith("4") and row["decision_index"] == 0]
    assert np.array_equal(base[first], base2[first])
    assert np.array_equal(scalar[first], scalar2[first])
    assert np.array_equal(embedding, embedding2)


def test_pilot_uses_first_eligible_writer_and_is_execution_only(tmp_path):
    inputs = inputs_for(tmp_path)
    config = dict(mode="pilot", seed=20261017, bootstrap_draws=100, pca_dimensions=3)
    report = p4.execute(tmp_path / "pilot", inputs, config)
    assert report["computed_recipients"] == 1
    assert report["eligible_recipients"] == 3
    assert report["execution_only"]
    assert report["projected_full_seconds"] == 3 * report["wall_seconds"]
    assert p4.read(tmp_path / "pilot/ELIGIBILITY.json")["selected_writers"] == ["a"]
    assert p4.verify(tmp_path / "pilot", inputs, config)["verified"]
