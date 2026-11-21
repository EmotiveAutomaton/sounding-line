"""Constructed cases only for the three-cohort interaction-diary runner."""
import json

import numpy as np
import pandas as pd
import pytest
from scipy.special import expit

from runners.drive.cards import week6_lb2_panel_v1 as panel
from runners.drive.cards import week6_lb2_run_v1 as runner
from runners.drive.cards import week6_lb2_source_v1 as source
from runners.drive.cards import week6_lb_bank_v1 as bank
from runners.drive.cards.week6_ld_draws_v1 import RequestedYield, compare, load_blocks


MISSING = ["", "NA"]


def guard():
    pass


def fixture(member="0042", people=42):
    rng = np.random.default_rng(37)
    count = people * 20
    ids = np.repeat(np.arange(people), 20)
    unpleasant = rng.integers(10, 86, count)
    dominant = rng.integers(-34, 35, count)
    product = (unpleasant - 48) / 22 * dominant / 20
    angry = np.where(rng.random(count) < expit(-.4 + .9 * product), 60, 5)
    nervous = np.where(rng.random(count) < .45, 60, 5)
    happy_key, angry_key, nervous_key = source.MEMBERS[member].ratings
    return pd.DataFrame({"id": ids, "interaction": 1, "dom_sub_you": dominant,
                         happy_key: 100 - unpleasant, angry_key: angry,
                         nervous_key: nervous}).astype(str)


def prepared(frame, member="0042"):
    return panel.build(member, source.prepare_frame(member, frame, MISSING))


def test_member_bindings():
    for member, spec in source.MEMBERS.items():
        data = prepared(fixture(member), member)
        assert data.metadata["row"] == str(int(member) - 24)
        assert data.metadata["source"]["rating_fields"] == list(spec.ratings)
        assert spec.seed == 202611190000 + int(member)
        assert len(spec.digest) == len(spec.codebook) == 64
    assert len({v.digest for v in source.MEMBERS.values()}) == 3


def test_during_and_momentary_items_cannot_substitute():
    rows = fixture("0044")
    with pytest.raises(ValueError, match="missing cohort fields"):
        source.prepare_frame("0043", rows, MISSING)
    for col in ("happy_interaction", "angry_interaction", "nervous_interaction"):
        rows[col] = "invalid distractor"
    assert prepared(rows, "0044").metadata["source"]["rows"] == len(rows)


def test_matched_support_and_untouched_roster():
    rows = fixture()
    rows.loc[rows.id == "0", "interaction"] = "0"
    rows.loc[20, "nervous_interaction"] = "NA"
    rows.loc[21, "interaction"] = ""
    rows.loc[22, "id"] = "NA"
    data = prepared(rows)
    counts = data.metadata["source"]
    assert data.people == 42
    assert counts["people"] == counts["people_reporting_interaction"] == 41
    assert counts["missing_identity"] == counts["missing_interaction"] == 1
    assert counts["no_interaction"] == 20 and counts["incomplete_interactions"] == 1
    assert counts["rows"] == len(rows) - 23
    assert {v["rows"] for v in data.specs.values()} == {counts["rows"]}


def test_bipolar_direction_and_unpleasantness():
    rows = fixture()
    rows.loc[0, ["dom_sub_you", "happy_interaction"]] = ["-50", "100"]
    rows.loc[1, ["dom_sub_you", "happy_interaction"]] = ["50", "0"]
    data = source.prepare_frame("0042", rows, MISSING)
    assert data.x[:2].tolist() == [[0, -50], [100, 50]]
    rows.loc[0, "dom_sub_you"] = "51"
    with pytest.raises(ValueError, match="dom_sub_you"):
        source.prepare_frame("0042", rows, MISSING)


def test_registered_slider_boundary():
    rows = fixture()
    rows["angry_interaction"] = np.resize(["0", "1", "5", "6", "100"], len(rows))
    data = prepared(rows)
    assert data.metadata["above_floor"]["angry"] == 2 * len(rows) // 5
    changed = rows.copy()
    changed["angry_interaction"] = changed["angry_interaction"].replace({"0": "5", "1": "5"})
    before = panel.evaluate(data, None, guard)
    after = panel.evaluate(prepared(changed), None, guard)
    assert before["row/18"] == pytest.approx(after["row/18"])


def test_null_and_planted_product():
    rows = fixture()
    original = panel.evaluate(prepared(rows), None, guard)
    assert original["row/18"] > .35
    assert original["linear_sensitivity/18"] > 0
    rows["angry_interaction"] = rows["nervous_interaction"]
    null = panel.evaluate(prepared(rows), None, guard)
    assert null["row/18"] == pytest.approx(0, abs=1e-10)
    assert null["linear_sensitivity/18"] == pytest.approx(0, abs=1e-10)


def test_scale_origin_is_immaterial():
    rows = fixture()
    before = panel.evaluate(prepared(rows), None, guard)
    rows["dom_sub_you"] = (rows.dom_sub_you.astype(int) + 8).astype(str)
    after = panel.evaluate(prepared(rows), None, guard)
    assert before["row/18"] == pytest.approx(after["row/18"], abs=1e-8)
    assert before["linear_sensitivity/18"] == pytest.approx(after["linear_sensitivity/18"])


def test_fresh_weighted_solver_agrees_for_both_cohorts_of_ratings():
    for member in ("0042", "0044"):
        data = prepared(fixture(member), member)
        w = np.arange(data.people) % 3
        assert w.sum() == data.people
        left = panel.evaluate(data, w, guard)
        right = panel.evaluate(data, w, guard, verify=True)
        compare([left[k] for k in sorted(left)], [right[k] for k in sorted(right)])
        assert left["row/" + source.MEMBERS[member].row] is not None


def test_separated_or_constant_cells_stay_missing():
    rows = fixture()
    rows["angry_interaction"] = "5"
    data = prepared(rows)
    result = panel.evaluate(data, None, guard)
    assert result["row/18"] is None and result["linear_sensitivity/18"] is None
    assert result["O/nervous/unpleasantness_by_own_dominance"] is not None
    assert "row/18" in data.metadata["point_dispositions"]


def test_small_cohort_retains_description():
    data = prepared(fixture(people=18))
    results = panel.evaluate(data, None, guard)
    assert results["row/18"] is None
    assert results["occurrence_description/18"] is not None
    assert data.specs["row/18"]["disposition"] == "below_support_floor"


def test_resampling_rejects_prompt_weights_and_lost_people():
    data = prepared(fixture())
    for weights in (np.ones(data.metadata["source"]["rows"]), np.zeros(data.people),
                    np.full(data.people, 2), np.full(data.people, 1.5)):
        with pytest.raises(ValueError):
            panel.evaluate(data, weights, guard)


def test_invalid_slider_and_missing_tokens_do_not_mask_errors():
    rows = fixture()
    for value in ("inf", "NA?", "1.5", "-1", "101"):
        rows.loc[0, "happy_interaction"] = value
        with pytest.raises(ValueError, match="happy_interaction"):
            source.prepare_frame("0042", rows, MISSING)


def test_wrong_source_or_native_configuration_fails_before_read(tmp_path):
    spec = source.MEMBERS["0043"]
    path = tmp_path / "fake.tsv"
    path.write_text("constructed", encoding="utf8")
    with pytest.raises(ValueError, match="source has changed"):
        source.load("0043", path, spec.pin, MISSING, guard)
    cfg = dict(card="LB2", member="0043", source_pin=spec.pin, draws=2000,
               source_seed=source.MEMBERS["0042"].seed, missing_tokens=MISSING)
    with pytest.raises(ValueError, match="Unregistered"):
        runner.validate(dict(source_path=str(path), source_admission_path=str(path),
                             source_admission_sha256="a"*64),
                        dict(panel_config=cfg, max_new_draws=100, max_wall_seconds=600))


def test_partial_blocks_resume_and_wrong_member_replay_is_refused(tmp_path):
    data = prepared(fixture())
    directory = tmp_path / "execute"
    spec = source.MEMBERS["0042"]
    args = dict(member="0042", source_digest=spec.digest, seed=spec.seed, guard=guard,
                verify=False, execute_dir=directory, progress=lambda n, t: None)
    for limit in (2, 1):
        with pytest.raises(RequestedYield, match="draw quantum"):
            bank.run(directory, panel, data, limit=limit, **args)
    assert len(load_blocks(directory, sorted(data.specs))) == 3
    schema = json.loads((directory / "SCHEMA.json").read_text("utf8"))
    assert schema["member"] == "0042"
    args.update(member="0043", verify=True, source_digest=source.MEMBERS["0043"].digest)
    with pytest.raises(ValueError, match="support differ"):
        bank.run(tmp_path/"verify", panel, data, limit=1, **args)
