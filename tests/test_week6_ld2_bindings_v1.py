"""End-to-end LD1 and LD2 sources use only generated prompts and people."""
import hashlib

import numpy as np
import pandas as pd
import pytest

from runners.drive.cards import week6_ld12_common_v1 as core
from runners.drive.cards import week6_ld1_v1 as ld1
from runners.drive.cards import week6_ld2_v1 as ld2
from runners.drive.cards import week6_lattice_bindings_v1 as binding
from runners.drive.cards import week6_lattice_diagnostics_v1 as diagnostics
from runners.drive.cards import week6_lattice_source_v1 as source


MISSING = ("", "NA")


def guard():
    return None


def pin(path):
    blob = path.read_bytes()
    return dict(bytes=len(blob), sha256=hashlib.sha256(blob).hexdigest())


def constructed_source(path, member, *, people=60, prompts=30):
    """Literal TSV with independently varied contexts, ranks and missingness."""
    rng = np.random.default_rng(396)
    columns = {"communication", "no_interactionpartner", "created_esm", "ended_esm"}
    for route in ("LD1", "LD2-support", "LD2-product"):
        columns.update(source.columns(member, route))
    rows = []
    for i in range(people + 1):
        for j in range(prompts):
            company = (j % 5 != 0) and i < people
            role = (1, 2, 3)[j % 3]
            date = pd.Timestamp("2026-01-01", tz="UTC") + pd.Timedelta(days=j // 3, hours=j % 3)
            values = {k: str(int(rng.integers(1, 7))) for k in sorted(columns)}
            values.update(id=f"p{i:04d}", day=str(j // 3 + 1),
                          interaction="1" if company else "2",
                          no_interactionpartner="2" if j % 11 == 0 else "1",
                          interaction_partner1=str(role), communication=str(j % 2 + 1),
                          created_esm=date.isoformat(), ended_esm=(date + pd.Timedelta(minutes=3)).isoformat(),
                          beh_leadership=str(int(rng.integers(1, 4)) + (2 if role == 2 else 0)))
            for feeling in source.feeling_names(member):
                for prefix in ("int_", "occup_"):
                    rating = 1 if rng.random() < .45 else int(rng.integers(2, 7))
                    values[prefix + feeling] = str(rating) if (prefix == "int_") == company else ""
            rows.append(values)
    frame = pd.DataFrame.from_records(rows)
    frame.to_csv(path, sep="\t", index=False, lineterminator="\n")
    return frame


def assert_equivalent(left, right):
    assert set(left) == set(right)
    assert {k for k, v in left.items() if v is None} == {k for k, v in right.items() if v is None}
    keys = sorted(k for k, v in left.items() if v is not None)
    np.testing.assert_allclose([left[k] for k in keys], [right[k] for k in keys], atol=2e-7, rtol=1e-7)


def test_ld1_source_primary_draws_missingness_and_suppression(tmp_path):
    path = tmp_path / "constructed.tsv"
    frame = constructed_source(path, "0057", people=16)
    p = ld1.prepare("0057", path, pin(path), MISSING, guard)
    assert p.people == 17
    key = "company.O.ashamed_minus_sad"
    assert p.specs[key]["role"] == "primary" and p.specs[key]["bar"] == .1
    observed = ld1.evaluate(p, None, guard)
    assert set(observed) == set(p.specs)
    assert observed[key] is not None
    assert observed["company.O.success.delta"] is None
    assert p.metadata["point_dispositions"]["company.O.success.delta"] == "perfect_separation_by_construction"
    np.testing.assert_allclose(observed["company.L.success.reference"], -1., atol=1e-10)
    weights = np.random.default_rng(91).multinomial(p.people, np.full(p.people, 1 / p.people))
    assert_equivalent(ld1.evaluate(p, weights, guard), ld1.evaluate(p, weights, guard, verify=True))
    frame["int_lonely"] = ""
    frame["occup_lonely"] = ""
    frame.to_csv(path, sep="\t", index=False, lineterminator="\n")
    q = ld1.prepare("0057", path, pin(path), MISSING, guard)
    r = ld1.evaluate(q, None, guard)
    assert q.specs[key]["rows"] == p.specs[key]["rows"]
    assert r[key] == pytest.approx(observed[key])
    assert r["company.O.lonely_minus_sad"] is None


def test_ld2_roles_products_and_agreement(tmp_path):
    path = tmp_path / "constructed.tsv"
    constructed_source(path, "0057")
    p = ld2.prepare("0057", path, pin(path), MISSING, guard)
    assert p.people == 61
    assert p.metadata["panels"]["role"]["disposition"] == "eligible"
    assert p.specs["role.O.below_minus_above"]["bar"] == .4
    assert p.specs["superior.O.anger_minus_fear"]["bar"] == .05
    observed = ld2.evaluate(p, None, guard)
    assert set(observed) == set(p.specs)
    assert all(observed[k] is not None for k in ("role.O.below_minus_above", "role.L.below_minus_above",
                                                  "leadership.O.anger_minus_fear", "selfesteem.L.anger_minus_fear"))
    panel = p.panels["role"]
    events = {k: panel["events"][:, j] for j, k in enumerate(ld2.EVENTS)}
    official = diagnostics.role_fit(panel["units"], panel["role"], events, panel["outcomes"])
    assert observed["role.O.below_minus_above"] == pytest.approx(official["primary"])
    for feeling, table in official["table"].items():
        for group, slopes in table.items():
            for event, value in slopes.items():
                assert observed[f"role.O.{group}.{feeling}.{event}"] == pytest.approx(value)
    panel = p.panels["leadership"]
    events = {k: panel["events"][:, j] for j, k in enumerate(ld2.EVENTS)}
    official = binding.ld2_product(panel["units"], events, panel["moderator"], panel["outcomes"])
    assert observed["leadership.O.anger_minus_fear"] == pytest.approx(official["primary"])
    assert observed["leadership.L.anger_minus_fear"] == pytest.approx(official["form_l"])
    weights = np.random.default_rng(131).multinomial(p.people, np.full(p.people, 1 / p.people))
    assert_equivalent(ld2.evaluate(p, weights, guard), ld2.evaluate(p, weights, guard, verify=True))


def test_unsupported_role_does_not_block_products(tmp_path):
    path = tmp_path / "constructed.tsv"
    constructed_source(path, "0056", people=18)
    p = ld2.prepare("0056", path, pin(path), MISSING, guard)
    assert p.metadata["panels"]["role"]["disposition"] == "unsupported_before_outcomes"
    values = ld2.evaluate(p, None, guard)
    assert values["role.O.below_minus_above"] is None
    assert values["leadership.O.anger_minus_fear"] is not None
    assert p.specs["superior.O.anger_minus_fear"]["role"] == "diagnostic"
    q = ld1.prepare("0056", path, pin(path), MISSING, guard)
    assert "company.O.lonely_minus_sad" not in q.specs


def test_source_identity_changed_refuses_both_projections(tmp_path):
    path = tmp_path / "changed.tsv"
    constructed_source(path, "0057", people=1, prompts=4)
    previous = pin(path)
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="[Pp]in"):
        ld1.prepare("0057", path, previous, MISSING, guard)
    with pytest.raises(ValueError, match="[Pp]in"):
        list(core.next_prompt_frames("0057", path, previous, MISSING, guard))


def test_identical_feelings_null_and_secondary_code_isolation(tmp_path):
    path = tmp_path / "constructed.tsv"
    frame = constructed_source(path, "0057", people=16)
    for prefix in ("int_", "occup_"):
        frame[prefix + "ashamed"] = frame[prefix + "sad"]
    frame.loc[frame["interaction"].eq("1").idxmax(), "communication"] = "no such code"
    frame.to_csv(path, sep="\t", index=False)
    p = ld1.prepare("0057", path, pin(path), MISSING, guard)
    estimates = ld1.evaluate(p, None, guard)
    assert estimates["company.O.ashamed_minus_sad"] == 0.
    assert estimates["one_partner.O.ashamed_minus_sad"] == 0.
    assert estimates["in_person.O.ashamed_minus_sad"] is None
    assert p.metadata["contexts"]["in_person"]["disposition"] == "values_outside_frozen_codebook"
    assert p.metadata["source_counts"]["invalid_optional_codes"]["communication"] == 1
