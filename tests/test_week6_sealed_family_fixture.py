"""Regression checks on the expanded, entirely invented two-table MIDUS mount."""
from pathlib import Path
import json
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "runners/drive/sealed/week6-sm-science"
PRESERVED = ROOT / ".agent-state/drive-20261115/full-week-extension/mi"
for path in reversed((FOLDER, ROOT/"runners/drive/cards", PRESERVED,
                      PRESERVED/"sealed-wrapper-mi4-nullfix-v4", PRESERVED/"mi4-v1", PRESERVED/"statcore-v2")):
    sys.path.insert(0, str(path))

import daily_bank
import daily_fixture as fixture
import family_draws
import nt1_daily as daily


def test_population_source_and_known_points(tmp_path):
    source = json.loads((FOLDER/"source_map.json").read_text("utf8"))
    mapping = fixture.construct(tmp_path/"made-up", source)["M2"]
    paths = {role: tmp_path/"made-up"/record["filename"] for role, record in mapping.items()}
    design = daily_bank.plan(paths)
    assert design["support"] and len(design["exposed"]) == len(fixture.HISTORIES)*4*fixture.COPIES
    assert design["pairs"] == 4*fixture.COPIES*sum(h[:-1].count("1") for h in fixture.HISTORIES)
    panel = design["panel"]
    weights = np.ones(len(panel["ids"]))
    actual = daily.score(panel, weights)
    independent = daily.score(design["replay"], weights, replay=True)
    np.testing.assert_allclose(actual, fixture.known_daily_point(), rtol=1e-7, atol=1e-8)
    np.testing.assert_allclose(independent, actual, rtol=1e-7, atol=1e-8)
    groups = family_draws.roster([{"id": int(v)} for v in panel["ids"]], family_draws.family_index(paths["survey"]))
    assert np.all(groups[::2] == groups[1::2])
    assert len(set(groups)) * 2 == len(groups)
    for draw in (0, 17, 1999):
        w = family_draws.multiplicities(groups, daily.SEED, draw)
        assert np.array_equal(w, family_draws.multiplicities(groups, daily.SEED, draw, independent=True))
        assert all(value is not None for value in daily_bank.checked_values(
            daily.score(panel, w), daily.score(design["replay"], w, True)))


def test_conditional_resolution_and_cluster_sizes():
    rows = fixture.records()
    assert all(row["B2DF1WC6"] in (1, 2) if row["B2DF1"] == 1 else row["B2DF1WC6"] == 9
               for row in rows["diary"])
    statuses = {row["B2DF1WC6"] for row in rows["diary"]}
    assert statuses == {1, 2, 9}
    assert len(rows["diary"]) == len(rows["survey"])*8
    # Every distinct response pattern has twelve copies before any split.
    for start in range(0, len(rows["survey"]), fixture.COPIES):
        patterns = [{k: v for k, v in row.items() if k not in ("M2ID", "M2FAMNUM")}
                    for row in rows["survey"][start:start+fixture.COPIES]]
        assert all(row == patterns[0] for row in patterns)
