"""Joined MIDUS integration. All tables are created under the test temporary root."""
import importlib.util
from pathlib import Path
import sys

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "runners/drive/sealed/week6-sm-science"
PRESERVED = ROOT / ".agent-state/drive-20261115/full-week-extension/mi"
LIBRARIES = [FOLDER, ROOT / "runners/drive/cards", PRESERVED,
             PRESERVED / "sealed-wrapper-mi4-nullfix-v4", PRESERVED / "mi4-v1",
             PRESERVED / "statcore-v2"]
for path in reversed(LIBRARIES):
    sys.path.insert(0, str(path))

import aggregate_register_v1 as register
import analysis_v1 as analysis
import engine
import joined_fixture
import joined_source
from panels import plan
import science_entry
from week6_sealed_support_v1 import SealedFailure


def editions():
    import json
    return json.loads((FOLDER / "source_map.json").read_text("utf8"))


def tables_for(root, mapping, wave):
    from mi_source_contract_v1 import fields
    from sealed_io_v1 import selected_columns

    roles = mapping[wave]
    files = {role: root / entry["filename"] for role, entry in roles.items()}
    cols = {"diary": selected_columns(wave + "_P2", fields),
            "survey": selected_columns(wave + "_P1", fields)}
    return joined_source.read_roles(files, cols)


def test_reviewed_cores_and_standalone_package(tmp_path):
    spec = importlib.util.spec_from_file_location("sm_build", FOLDER / "build.py")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    a = builder.build(tmp_path / "one")
    b = builder.build(tmp_path / "two")
    assert a == b
    assert a["science_draws"] == 2000
    assert set(a["jobs"]) == {"midus-m2-joined", "midus-m2m3-joined", "rehearsal", "scratch-rehearsal"}


def test_source_pair_hash_and_bound(tmp_path):
    root = tmp_path / "joined"
    entries, _ = joined_fixture.construct(root, editions())
    mapping = {"M2": entries}
    private = tmp_path / "private"
    private.mkdir()
    size = sum(d["bytes"] for d in entries.values())
    assert joined_source.take_snapshot(root, private, mapping, size)[0] == "M2"
    with (root / entries["diary"]["filename"]).open("ab") as f:
        f.write(b"x")
    other = tmp_path / "other"
    other.mkdir()
    with pytest.raises(SealedFailure):
        joined_source.take_snapshot(root, other, mapping, size)


def test_repeat_population_uses_each_primary_eligibility_roster(tmp_path):
    ed = editions()
    m2, _ = joined_fixture.construct(tmp_path / "m2", ed, "M2")
    m3, _ = joined_fixture.construct(tmp_path / "m3", ed, "M3", extra_profile=True)
    mapping = {"M2": m2, "M3": m3}
    source = {wave: tables_for(tmp_path / wave.lower(), mapping, wave) for wave in mapping}
    original = {wave + compound: rows[role] for wave, rows in source.items()
                for role, compound in (("survey", "_P1"), ("diary", "_P2"))}
    familiar, counts = analysis.plan_panels(original, analysis.decode_all(original))
    for wave in mapping:
        panels, groups = plan(source, wave, False)
        independent, checked = plan(source, wave, True)
        assert groups == checked == {k: v for (w, k), v in counts.items() if w == wave}
        for name in register.BRANCHES:
            actual = [p["id"] for p in panels[name]]
            assert actual == [p["id"] for p in independent[name]]
            assert actual == [p["id"] for p in familiar[wave, name]]
    with pytest.raises(SealedFailure):
        science_entry.run_joined({"M3": tmp_path / "m3"}, "M3", mapping, tmp_path)


def test_small_complement_is_never_emitted(tmp_path):
    root = tmp_path / "wave"
    m2, _ = joined_fixture.construct(root, editions())
    data = tables_for(root, {"M2": m2}, "M2")
    survey = dict(data["survey"][0])
    survey["M2ID"] += 100000
    data["survey"].append(survey)
    with pytest.raises(SealedFailure) as raised:
        engine.study({"M2": data}, {"M2": data}, "M2")
    assert raised.value.code == 12


def test_point_and_first_draw_all_branches_replay(tmp_path):
    root = tmp_path / "wave"
    m2, _ = joined_fixture.construct(root, editions())
    data = tables_for(root, {"M2": m2}, "M2")
    panels, _ = plan({"M2": data}, "M2", False)
    reference, _ = plan({"M2": data}, "M2", True)
    for branch in register.BRANCHES:
        a, b = panels[branch], reference[branch]
        pa, pb = analysis.prepare(a, branch), analysis.prepare(b, branch, True)
        point = analysis.private_point(a, pa, branch)
        assert engine.equal_values(point, analysis.private_point(b, pb, branch, True))
        if point is None:
            continue
        seed = register.SEEDS[branch]
        analysis.same_record(analysis.draw_record(a, pa, branch, seed, 0),
                             analysis.draw_record(b, pb, branch, seed, 0, True))
    mi4 = panels["MI4"]
    point = analysis.private_point(mi4, analysis.prepare(mi4, "MI4"), "MI4")
    np.testing.assert_allclose(point, [1., 1., 0.], rtol=0, atol=1e-10)


def test_end_to_end_production_draw_bank(tmp_path):
    ed = editions()
    m2, n = joined_fixture.construct(tmp_path / "wave", ed)
    out = tmp_path / "aggregates"
    out.mkdir()
    got = science_entry.run_joined({"M2": tmp_path / "wave"}, "M2", {"M2": m2}, out)
    joined_fixture.check_known(got)
    assert all(11 <= row["n"] <= n for rows in got.values() for row in rows)
    assert all(set(row).issubset({"n","branch","parameter","estimate","lower","upper",
                                  "standard_error","draws","invalid_draws","descriptive","count_group",
                                  "table_role","loaded","fields_required","fields_present","resampling","family_field_present",
                                  "wave","fields_supported"})
               for rows in got.values() for row in rows)
    assert {file.stem for file in out.iterdir()} == set(got)


def test_partial_source_status_counts_only_real_fixture_people(tmp_path, monkeypatch):
    # This checks dispatch and a fresh point/draw replay for every surviving
    # branch. The full-draw test separately exercises the 2,000-draw contract.
    monkeypatch.setattr(engine, "DRAW_COUNT", 1)
    from table_support import TABLE_IDS
    from hashlib import sha256
    import pyreadstat
    root = tmp_path / "joined"
    m2, n = joined_fixture.construct(root, editions())
    file = root / m2["diary"]["filename"]
    frame, _ = pyreadstat.read_sav(str(file))
    frame = frame.drop(columns=["B2DC17"])
    pyreadstat.write_sav(frame, str(file))
    data = file.read_bytes()
    m2["diary"].update(bytes=len(data), sha256=sha256(data).hexdigest())
    out = tmp_path / "out"
    out.mkdir()
    tables = science_entry.run_joined({"M2": root}, "M2", {"M2": m2}, out)
    roles = {row["table_role"]: row for row in tables["status"]}
    assert roles[1]["n"] == roles[2]["n"] == n
    assert roles[2]["fields_required"] > roles[2]["fields_present"]
    rows = {row["branch"]: row for row in tables["table_status"] if row["table_role"] == 2}
    assert set(rows) == set(TABLE_IDS.values())
    assert all(row["n"] == n for row in rows.values())
    assert rows[TABLE_IDS["MI1"]]["fields_supported"] == 0
    assert rows[TABLE_IDS["MI3"]]["fields_supported"] == 0
    assert rows[TABLE_IDS["MI2"]]["fields_supported"] == 1
    assert rows[TABLE_IDS["MI4"]]["fields_supported"] == 1
    assert rows[TABLE_IDS["NT1.s"]]["fields_supported"] == 0
    identified = {r["branch"] for r in tables["interval_unavailable"]}
    assert TABLE_IDS["MI4"] in identified and TABLE_IDS["MI1"] not in identified


def test_equal_length_byte_change_refuses_before_decode(tmp_path):
    root = tmp_path / "wave"
    m2, _ = joined_fixture.construct(root, editions())
    file = root / m2["diary"]["filename"]
    with file.open("r+b") as raw:
        value = raw.read(1)
        raw.seek(0)
        raw.write(bytes([value[0] ^ 1]))
    out = tmp_path / "out"
    out.mkdir()
    with pytest.raises(SealedFailure) as raised:
        science_entry.run_joined({"M2": root}, "M2", {"M2": m2}, out)
    assert raised.value.code == 11 and not list(out.iterdir())


def test_nonmatching_independent_draw_never_releases(tmp_path, monkeypatch):
    root = tmp_path / "wave"
    m2, _ = joined_fixture.construct(root, editions())
    original = analysis.draw_record

    def mismatch(people, stats, branch, seed, index, reference=False):
        value = original(people, stats, branch, seed, index, reference)
        if reference:
            value = dict(value, status="UNREVIEWED")
        return value

    monkeypatch.setattr(analysis, "draw_record", mismatch)
    out = tmp_path / "out"
    out.mkdir()
    with pytest.raises(ValueError, match="independent draw status"):
        science_entry.run_joined({"M2": root}, "M2", {"M2": m2}, out)
    assert not list(out.iterdir())


def test_family_draws_move_relatives_together_and_match_person_draws_for_singletons():
    import family_draws

    people = [{"id": value} for value in (11, 15, 56, 70, 81)]
    linked = {11: 400, 15: 12, 56: 400, 70: 12, 81: 19}
    clusters = family_draws.roster(people, linked)
    independent = family_draws.roster(people, linked, reference=True)
    np.testing.assert_array_equal(clusters, [0, 1, 0, 1, 2])
    for index in range(20):
        weights = family_draws.multiplicities(clusters, 20261120, index)
        np.testing.assert_array_equal(weights, family_draws.multiplicities(independent, 20261120, index, True))
        assert weights[0] == weights[2] and weights[1] == weights[3]
        assert sum(weights[[0, 1, 4]]) == 3
        singletons = family_draws.roster(people, {p["id"]: 1000 - p["id"] for p in people})
        rng = np.random.default_rng(np.random.SeedSequence([20261120, index]))
        expected = np.bincount(rng.integers(len(people), size=len(people)), minlength=len(people))
        np.testing.assert_array_equal(family_draws.multiplicities(singletons, 20261120, index), expected)
    assert family_draws.roster(people, {11: 400}) is None


def test_family_linkage_preserves_absent_fields_and_declared_spss_missing_values(tmp_path):
    import family_draws
    import pandas as pd
    import pyreadstat

    missing = tmp_path / "no-family-field.sav"
    pyreadstat.write_sav(pd.DataFrame({"M2ID": [1., 2., 3.]}), missing)
    assert family_draws.family_index(missing) is None
    present = tmp_path / "with-family-field.sav"
    frame = pd.DataFrame({"M2ID": [1., 2., 3.], "M2FAMNUM": [7., 7., 999.]})
    pyreadstat.write_sav(frame, present, missing_ranges={"M2FAMNUM": [999.]})
    assert family_draws.family_index(present) == {1: 7, 2: 7, 3: None}
    duplicate = tmp_path / "ambiguous.sav"
    frame.loc[2, "M2ID"] = 2.
    pyreadstat.write_sav(frame, duplicate)
    with pytest.raises(SealedFailure):
        family_draws.family_index(duplicate)


def test_both_wave_snapshots_require_the_registered_four_files(tmp_path):
    from shutil import copyfile

    ed = editions()
    joined = tmp_path / "combined"
    joined.mkdir()
    mapping = {}
    for wave in ("M2", "M3"):
        single = tmp_path / wave
        pair, _ = joined_fixture.construct(single, ed, wave)
        mapping[wave] = pair
        for record in pair.values():
            copyfile(single / record["filename"], joined / record["filename"])
    for wave in mapping:
        target = tmp_path / ("private-" + wave)
        target.mkdir()
        size = sum(r["bytes"] for r in mapping[wave].values())
        actual, files = joined_source.take_snapshot(joined, target, mapping, size, combined_wave=wave)
        assert actual == wave and set(files) == {"survey", "diary"}
    partial = tmp_path / "incomplete"
    partial.mkdir()
    for record in mapping["M2"].values():
        copyfile(joined / record["filename"], partial / record["filename"])
    inner = tmp_path / "unused"
    inner.mkdir()
    with pytest.raises(SealedFailure):
        joined_source.take_snapshot(partial, inner, mapping, 100000000, combined_wave="M2")
    assert not list(inner.iterdir())


def test_independent_column_dependencies_for_wave_two_and_repeat():
    from table_support import EXTRAS, required_columns, supported_columns, table_names

    def all_columns(wave, names):
        return {role: set().union(*(required_columns(wave, name)[role] for name in names))
                for role in ("diary", "survey")}

    wave_two = all_columns("M2", table_names("M2"))
    wave_three = all_columns("M3", table_names("M3"))
    assert set(supported_columns({"M2": wave_two}, "M2")) == set(register.BRANCHES) | set(EXTRAS)
    wave_two["diary"].remove("B2DF1WC6")
    available = supported_columns({"M2": wave_two}, "M2")
    assert set(available) == (set(register.BRANCHES) | {"NT1.s"})
    wave_two["survey"].remove("B1SNEURO")
    available = supported_columns({"M2": wave_two}, "M2")
    assert "MI2-traits" not in available and "NT1.s" not in available
    assert {"MI1", "MI2", "MI3", "MI4"} <= set(available)
    wave_three["diary"].remove("C2DC17")
    repeat = supported_columns({"M2": wave_two, "M3": wave_three}, "M3")
    assert not ({"MI1", "MI3", "MI2-traits", *EXTRAS} & set(repeat))
    assert {"MI2", "MI2-reliability", "MI4"}.issubset(repeat)
