"""Constructed checks for pre-outcome support, joint privacy and complete draw banks."""
from pathlib import Path
import sys

import numpy as np
import pytest

HERE = Path(__file__).resolve().parents[1]
for path in (HERE / "runners/drive/sealed/week6-sm-science", HERE / "runners/drive/cards",
             HERE / ".agent-state/drive-20261115/full-week-extension/mi",
             HERE / ".agent-state/drive-20261115/full-week-extension/mi/sealed-wrapper-mi4-nullfix-v4"):
    sys.path.insert(0, str(path))
import aggregate_register_v1 as register
import daily_bank as bank
from week6_sealed_support_v1 import SealedFailure


def synthetic(n):
    fields = bank.contract.fields("M2")
    tables = {"survey": [], "diary": []}
    for person in range(1, n+1):
        tables["survey"].append({"M2ID": person, "B1SNEURO": 1.25 + .5*(person % 5)})
        for day in range(1, 9):
            row = {"M2ID": person, fields["study_day"]: day, fields["weekday"]: ((day-1) % 7) + 1}
            row.update({item["occurrence"]: 2 for item in fields["stressors"]})
            row["B2DF1"] = 1 if (person + day) % 3 else 2
            row.update({f: (person*day + day % 2) % 3 for f in fields["negative"]})
            tables["diary"].append(row)
    return tables


def tracked_reader(monkeypatch, tables):
    calls = []
    def read(paths, columns):
        assert set(paths) == set(columns)
        calls.append({k: set(v) for k, v in columns.items()})
        return {role: [{name: row[name] for name in columns[role]} for row in tables[role]] for role in paths}
    monkeypatch.setattr(bank, "read_roles", read)
    return calls


def test_under_floor_never_requests_a_feeling_column(monkeypatch):
    calls = tracked_reader(monkeypatch, synthetic(149))
    state = bank.plan({"diary": "fixture", "survey": "fixture"})
    assert len(calls) == 2 and state["pairs"] >= 300 and not state["support"]
    assert all(not (c["diary"] & set(bank.contract.fields("M2")["negative"])) for c in calls)
    assert bank.run(state, None, None) == {"daily_exposure": [
        {"n": 149, "previous_stressor_pairs": state["pairs"], "support_met": 0}]}


def test_exact_support_boundary_and_protected_memberships(monkeypatch):
    calls = tracked_reader(monkeypatch, synthetic(150))
    state = bank.plan({"diary": "fixture", "survey": "fixture"})
    assert len(calls) == 4 and state["support"] and len(state["exposed"]) == 150
    for index, selection in enumerate(calls):
        assert bool(selection["diary"] & set(bank.contract.fields("M2")["negative"])) == (index >= 2)
    groups = bank.released_sets(state)
    assert groups == [set(range(1,151))]*2
    assert register.exact_counts_safe(groups)
    assert not register.exact_counts_safe([*groups, set(range(1,146))])


def minimal():
    return {"support": True, "exposed": set(range(1,151)), "pairs": 450,
            "panel": {"ids": np.arange(1,151)}, "replay": {"ids": np.arange(1,151)}}


def test_missing_family_link_uses_only_point_and_preserves_real_n(monkeypatch):
    monkeypatch.setattr(bank.daily, "score", lambda p, w, replay=False: [1.]*7)
    families = {i: i//2 for i in range(1,150)}
    result = bank.run(minimal(), families, families)
    assert len(result["daily_point_only"]) == 7 and "daily_estimates" not in result
    assert all(r["n"] == 150 and r["resampling"] == 3 and r["draws"] == 0 for r in result["daily_point_only"])


def test_all_2000_cluster_draws_and_parameter_specific_missingness(monkeypatch):
    calls = [0, 0]
    def score(p, w, replay=False):
        position = calls[replay]
        calls[replay] += 1
        assert np.array_equal(w[::2], w[1::2])
        v = float(w[0])
        return [1.+v, 1., 1., 1., 1., 0., None if position == 31 else v]
    monkeypatch.setattr(bank.daily, "score", score)
    families = {i: (i-1)//2 + 1 for i in range(1,151)}
    result = bank.run(minimal(), families, families)
    assert calls == [2001,2001]
    assert {r["parameter"] for r in result["daily_estimates"]} == set(range(1,7))
    row, = result["daily_point_only"]
    assert row["parameter"] == 7 and row["valid_draws"] == 1999 and row["n"] == 150
    assert all(r["resampling"] == 2 for r in result["daily_estimates"])
    assert result["daily_reading"][0]["decision"] == 7


def test_independent_solver_disagreement_is_a_failed_check():
    with pytest.raises(SealedFailure):
        bank.checked_values([1.]*7, [1.]*6+[None])
    with pytest.raises(SealedFailure):
        bank.checked_values([1.]*7, [1.]*6+[1.1])
