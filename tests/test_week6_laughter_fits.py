"""Constructed checks for the registered strict-window meeting comparisons."""
from copy import deepcopy

import numpy as np
import pytest

from runners.drive.cards import week6_laughter_followup_fit_v1 as fit


def block(meeting, length_pairs=2, signal=False):
    pairs = [["C1", "N"], ["C2", "N"]]
    data = {}
    for key in ("C1", "C2", "N"):
        data[key] = {"act_type": "fixed", "numeric": [4, int(signal and key.startswith("C")), *([0] * 7)]}

    def variant(n):
        return {"pairs": pairs[:n], "audit": {"cases": 2, "matched": n, "unsupported": [{}] * (2-n),
                                               "unique_controls": int(n > 0), "reused_control_copies": max(0, n-1)}}

    return {"meeting": meeting, "source_utterances": 12, "features": data,
            "windows": {str(w): {"strict": variant(2), "length_held": variant(length_pairs),
                                 "excluded_preexisting": 3} for w in (1, 2)}}


def test_folds_are_identical_to_parent_when_all_meetings_are_retained():
    blocks = [block(str(n), signal=True) for n in range(10)]
    rows = fit.samples(blocks, "LA6.s")[0]["2s_strict"]
    expected = fit.parent.point(rows)
    actual = fit.point(rows, fit.fixed_folds(r["meeting"] for r in rows))
    fit.compare.compare_record(actual, expected)
    for arm in ("True", "False"):
        assert actual[arm]["auc"] == 1


def test_lost_meeting_cannot_move_other_meetings_to_different_folds():
    names = list("abcdefghij")
    folds = fit.fixed_folds(names)
    rows = fit.samples([block(n) for n in names if n != "b"], "LA6.s")[0]["1s_strict"]
    area, predictions, audit = fit.held_out(rows, folds, True)
    assert area == .5 and np.all(predictions == 0)
    for row in audit:
        assert all(folds[name] == row["fold"] for name in row["test_meetings"])
        assert set(row["test_meetings"]).isdisjoint(row["training_meetings"])
    assert {r["fold"] for r in audit} == set(range(5))


def test_length_route_uses_the_total_and_keeps_both_windows():
    half = [block("a", 0), block("b", 2)]
    samples, audit = fit.samples(half, "LA6.sl")
    assert set(samples) == {"1s_length_held", "2s_length_held"}
    assert all(row["length_route"] == "matched" for row in audit.values())
    assert audit["1"]["strict_unmatched"] == 0 and audit["1"]["length_held_unmatched"] == 2
    assert audit["1"]["strict_reused_control_copies"] == 2 and audit["1"]["excluded_preexisting"] == 6
    below = [block("a", 0), block("b", 1)]
    samples, audit = fit.samples(below, "LA6.sl")
    for w in (1, 2):
        included = samples[f"{w}s_strict"]
        omitted = samples[f"{w}s_strict_without_length"]
        assert len(included) == len(omitted) == 8
        assert all(x["numeric"][0] == 4 and y["numeric"][0] == 0 for x, y in zip(included, omitted))
        assert all(x["numeric"][1:] == y["numeric"][1:] for x, y in zip(included, omitted))
        assert audit[str(w)]["length_route"] == "covariate"


def test_mismatched_pair_accounting_fails_before_a_fit():
    bad = deepcopy(block("broken"))
    bad["windows"]["2"]["strict"]["audit"]["cases"] += 2
    with pytest.raises(ValueError, match="dispositions"):
        fit.samples([bad], "LA6.s")


def test_first_draws_checkpoint_and_detect_changed_draw(tmp_path, monkeypatch):
    blocks = [block(n, signal=True) for n in "abcdefg"]
    folds = fit.fixed_folds(r["meeting"] for r in blocks)
    monkeypatch.setattr(fit, "load", lambda _: (blocks, folds, {"source": "fixture"}))
    config = {"phase": "LA6.s", "draws": 2000, "max_new_draws": 2}
    assert fit.execute(tmp_path, {}, config)["completed"] == 2
    assert fit.execute(tmp_path, {}, config)["completed"] == 4
    assert fit.verify(tmp_path, {}, config)["completed"] == 2
    for i in range(2):
        name = f"draws/{i:04}.json"
        actual = fit.stored(tmp_path / name)
        fit.compare.compare_record(actual, fit.stored(tmp_path / "independent-replay" / name))
        assert actual["series"]["1s_strict"]["True"]["auc"] == 1
    changed = tmp_path / "draws/0000.json"
    changed.write_bytes(changed.read_bytes() + b" ")
    with pytest.raises(ValueError, match="checkpoint bytes"):
        fit.execute(tmp_path, {}, config)


def test_one_parent_fold_and_no_pairs_are_both_descriptive(tmp_path, monkeypatch):
    blocks = [block("a"), block("f")]
    monkeypatch.setattr(fit, "load", lambda _: (blocks, fit.fixed_folds("abcdefg"), {"source": "fixture"}))
    config = {"phase": "LA6.s", "draws": 2000}
    result = fit.execute(tmp_path, {}, config)
    assert result["draws"] == 0 and result["series"]["2s_strict"]["meetings"] == 2
    assert fit.verify(tmp_path, {}, config)["all_draws_replayed"]
    for item in blocks:
        for window in item["windows"].values():
            for mode in ("strict", "length_held"):
                variant = window[mode]
                variant.update(pairs=[], audit=dict(cases=0, matched=0, unsupported=[],
                                                   unique_controls=0, reused_control_copies=0))
    result = fit.execute(tmp_path / "empty", {}, config)
    assert result["series"]["1s_strict"]["pooled_descriptive"] == {}


def test_draw_count_and_membership_cannot_be_changed(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="2,000"):
        fit.execute(tmp_path, {}, {"phase": "LA6.s", "draws": 20})
    monkeypatch.setattr(fit, "load", lambda _: ([block("outside")], {"inside": 0}, {"source": "fixture"}))
    with pytest.raises(ValueError, match="outside"):
        fit.execute(tmp_path, {}, {"phase": "LA6.sl", "draws": 2000})
