"""Manufactured, independent checks for the LD3 full table and both contrasts."""
import numpy as np
import pytest
import csv
import hashlib

from runners.drive.cards import week6_ld3_v1 as ld3
from runners.drive.cards.week6_lattice_bindings_v1 import ld3 as reference_table


def make_people(member="0057"):
    rng = np.random.default_rng(67)
    people = []
    for i in range(24):
        size = 13 + i % 7
        x = rng.normal(size=(size, 8))
        ratings = {k: x[:, j] for j, k in enumerate(ld3.ACTIVITY)}
        for key in ld3.feeling_names(member):
            ratings[key] = i + rng.normal(size=size)
        ratings["enthusiastic"] = i + x[:, 3] + .25 * rng.normal(size=size)
        ratings["anxious"] = i + x[:, 4] + .25 * rng.normal(size=size)
        people.append({"ratings": ratings, "source_ordinals": list(range(size))})
    return people


@pytest.mark.parametrize("member", ["0056", "0057"])
def test_full_table_matches_literal_cluster_replication(member):
    people = make_people(member)
    prepared = ld3.prepare_from_people(member, people, {}, lambda: None)
    w = np.tile([0, 1, 2], 8)
    rows = [p for p, count in zip(people, w) for _ in range(count)]
    units = np.concatenate([np.full(len(p["source_ordinals"]), i) for i, p in enumerate(rows)])
    def columns(keys):
        return {k: np.concatenate([p["ratings"][k] for p in rows]) for k in keys}
    expected = reference_table(units, columns(ld3.ACTIVITY), columns(ld3.feeling_names(member)))
    a = ld3.evaluate(prepared, w, lambda: None)
    b = ld3.evaluate(prepared, w, lambda: None, verify=True)
    assert set(a) == set(b) == set(prepared.specs)
    for feeling, vector in expected["table"].items():
        for name, value in zip(ld3.ACTIVITY, vector):
            key = f"table/{feeling}/{name}"
            assert a[key] == pytest.approx(value, abs=1e-10)
            assert b[key] == pytest.approx(value, abs=1e-10)
    assert a["contrast/intellectual_enthusiastic_minus_relaxed"] == pytest.approx(expected["intellectual"])
    assert a["contrast/overwhelmed_anxious_minus_angry"] == pytest.approx(expected["overwhelmed"])
    assert expected["intellectual"] > .65 and expected["overwhelmed"] > .65


def test_unrelated_missing_outcome_preserves_both_primary_samples():
    people = make_people()
    before = ld3.prepare_from_people("0057", people, {}, lambda: None)
    for person in people:
        person["ratings"]["lonely"][:] = np.nan
    after = ld3.prepare_from_people("0057", people, {}, lambda: None)
    a = ld3.evaluate(before, None, lambda: None)
    b = ld3.evaluate(after, None, lambda: None)
    assert all(b[k] == a[k] for k in a if k.startswith("contrast/"))
    assert all(b[k] is None for k in b if k.startswith("table/lonely/"))
    assert after.metadata["coverage"]["lonely"]["retained_people"] == 0


def test_two_outcomes_in_a_contrast_share_the_same_rows():
    people = make_people()
    for person in people[:10]:
        person["ratings"]["relaxed"][::2] = np.nan
    prepared = ld3.prepare_from_people("0057", people, {}, lambda: None)
    key = "intellectual_enthusiastic_minus_relaxed"
    coverage = prepared.metadata["coverage"]
    assert coverage[key]["retained_rows"] == coverage["relaxed"]["retained_rows"]
    assert coverage[key]["retained_rows"] < coverage["enthusiastic"]["retained_rows"]
    assert coverage[key]["missing_rows"] > 0
    observed = ld3.evaluate(prepared, None, lambda: None)
    replay = ld3.evaluate(prepared, None, lambda: None, verify=True)
    assert observed[f"contrast/{key}"] == pytest.approx(replay[f"contrast/{key}"])


def test_lost_rank_is_explicit_across_independent_replay():
    people = make_people()
    for p in people:
        p["ratings"]["fun"] = p["ratings"]["pleasant"]
    prepared = ld3.prepare_from_people("0057", people, {}, lambda: None)
    for ref in (False, True):
        values = ld3.evaluate(prepared, None, lambda: None, verify=ref)
        assert values and all(v is None for v in values.values())


@pytest.mark.parametrize("weights", [[1], [1.] * 24, [-1, 25] + [0] * 22, [0] * 24])
def test_invalid_cluster_multiplicities_refuse(weights):
    prepared = ld3.prepare_from_people("0057", make_people(), {}, lambda: None)
    with pytest.raises(ValueError):
        ld3.evaluate(prepared, weights, lambda: None)


def test_literal_public_layout_includes_interaction_only_people(tmp_path):
    fields = ["id", "day", "created_esm", "ended_esm", "interaction", "communication",
              "type_interaction", *ld3.ACTIVITY, *["occup_" + n for n in ld3.feeling_names("0057")]]
    path = tmp_path / "diary.tsv"
    with path.open("w", encoding="utf8", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for who in range(5):
            for j in range(10):
                context = "1" if who == 0 or j % 2 else "2"
                stamp = f"2020-01-04T{8+j:02d}:00:00Z"
                data = dict.fromkeys(fields, "3")
                data.update(id=str(who), day="1", created_esm=stamp, ended_esm=stamp,
                            interaction=context, communication="2", type_interaction="1")
                writer.writerow(data)
    payload = path.read_bytes()
    pin = dict(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
    result = ld3.prepare("0057", path, pin, ["", "NA"], lambda: None)
    assert result.people == 5
    assert result.metadata["coverage"]["angry"]["retained_people"] == 4
    after = result.metadata["next_answered_prompt"]
    assert after["by_boredom"]["3"] == {"anchors": 20, "next_interaction": 20}
    assert after["next_interaction_type_codes"]["3"] == {"1": 20}
