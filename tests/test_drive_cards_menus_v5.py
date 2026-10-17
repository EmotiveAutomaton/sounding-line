import numpy as np
import pytest

from runners.drive.cards import menus_v5 as v5
from runners.drive.cards.menus_io import write


def metadata(personal=True):
    return [dict(key=f"{w}-{s}-{d}", writer=str(w), session=f"{w}-{s}", prompt="p",
                 outcome=w if personal else d)
            for w in range(4) for s in range(3) for d in range(2)]


def all_pairs(rows):
    x = np.ones((len(rows), 1))
    return v5.match_pairs(rows, x, x, 3)


def test_exact_agreement_floors_known_personal_answer():
    rows = metadata(); pairs = all_pairs(rows)
    writers, wi, si, sw, truth = v5.encode_metadata(rows)
    left, right = pairs["left"], pairs["right"]
    stats = v5.agreement_summary(left, right, (truth[left] == truth[right]).astype(float), wi, si)
    assert stats["A_w"] == 1
    assert stats["A_b"] == 0
    assert stats["personal_floor"] == 0
    assert stats["pooled_floor"] == .5
    assert stats["H"] == .5
    report = v5.summarize(rows, pairs, dict(bootstrap_draws=300))
    assert report["primary"]["estimate"] == .5
    assert abs(report["curves"][2]["writer_shuffle"]["mean"]) < .05


def test_null_has_zero_headroom_despite_multiple_decisions_per_session():
    rows = metadata(False); pairs = all_pairs(rows)
    report = v5.summarize(rows, pairs, dict(bootstrap_draws=300))
    assert report["primary"]["estimate"] == 0
    assert report["primary"]["interval95"] == [0, 0]
    assert report["route"] == "near_zero"


def test_prompt_and_dual_cosine_boundaries():
    rows = [dict(prompt="p"), dict(prompt="p"), dict(prompt="q"), dict(prompt="p")]
    ctx = np.array([[1., 0], [.8, .6], [1, 0], [1, 0]])
    menu = np.array([[1., 0], [1, 0], [1, 0], [.5, np.sqrt(.75)]])
    pairs = v5.match_pairs(rows, ctx, menu, 1)
    found = {(int(a), int(b)): c for a, b, c in zip(pairs["left"], pairs["right"], pairs["similarity"])}
    assert found[(0, 1)] == .8
    assert (0, 2) not in found and (0, 3) not in found
    assert len(found) == 1


def test_no_pairs_is_invalid_and_negative_denominators_undefined():
    rows = metadata()
    pairs = {"left": np.array([], int), "right": np.array([], int), "similarity": np.array([])}
    assert v5.summarize(rows, pairs, dict(bootstrap_draws=100))["state"] == "invalid"
    ratios = v5.gain_shares(.01, .2, .3, -.01, .05)
    assert ratios["share_of_population_to_personal_floor"] is None
    assert ratios["share_of_personal_headroom"] is None
    assert ratios["share_using_headroom_upper"] == pytest.approx(.2)


def test_execute_and_saved_primary_recompute(tmp_path):
    rows = metadata(False); sessions = []
    for session_id in sorted({row["session"] for row in rows}):
        subset = [row for row in rows if row["session"] == session_id]
        sessions.append(dict(session=session_id, writer=subset[0]["writer"], prompt="p",
                             rows=[dict(key=row["key"], menu=["a"], handling=v5.ACTIONS[row["outcome"]]) for row in subset]))
    records = [dict(key=row["key"], session=row["session"], writer=row["writer"], context=0, options=[0]) for row in rows]
    write(tmp_path / "sessions.json", sessions); write(tmp_path / "records.json", records)
    np.save(tmp_path / "vectors.npy", np.array([[1., 0]]), allow_pickle=False)
    inputs = {key: str(tmp_path / name) for key, name in (("sessions", "sessions.json"), ("records", "records.json"), ("vectors", "vectors.npy"))}
    config = dict(bootstrap_draws=100, block_size=2)
    v5.execute(tmp_path / "output", inputs, config)
    assert v5.verify(tmp_path / "output", inputs, config)["verified"]
