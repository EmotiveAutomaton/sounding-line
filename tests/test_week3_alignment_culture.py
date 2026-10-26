"""CA2 fitted-half parity, known recurrence, nulls, references and source replay."""
import copy
import json
from pathlib import Path

import numpy as np
import pytest

from runners.drive.cards import week3_alignment_culture as card
from runners.drive.cards import week3_alignment_stats as stats
from runners.drive.cards.menus_io import read, write, sha256
from tests.test_week3_alignment_stats import world, fixture as feature_fixture


def fixture(root):
    root = Path(root); inputs = feature_fixture(root/"features")
    parent = root/"parent"; config = {"mode":"fixture", "permutation_draws":2, "bootstrap_draws":20}
    stats.execute(parent/"output", inputs, config)
    assert stats.verify(parent/"output", inputs, config)["verified"]
    write(parent/"COMPLETE.json", {"status":"COMPLETE", "fresh_process_verified":True,
          "outputs":{p.relative_to(parent).as_posix():sha256(p) for p in sorted((parent/"output").rglob("*")) if p.is_file()}})
    return inputs|{"ca1_summary":str(parent/"output/SUMMARY.json"), "ca1_complete":str(parent/"COMPLETE.json")}


def test_opposite_half_fit_matches_original_frozen_reader_exactly():
    rows, x, _ = world(writers=4, conversations=8); people = sorted({r["writer"] for r in rows})
    expected = stats.evaluate(rows, x, {}, people, half=1)
    actual = card.fit_half(rows, x, {}, people)
    assert actual["population"] == expected["population"] and actual["country"] == expected["country"]
    for person in people:
        for key in ("individual", "country", "support", "train_comparisons"):
            assert actual["profiles"][person][key] == expected["profiles"][person][key]


def test_common_country_cancels_and_personal_directions_are_rotation_invariant():
    rng = np.random.default_rng(1); directions = rng.normal(size=(8, 4))
    paired = np.stack([directions, directions], axis=1)
    np.testing.assert_allclose(card.cosines(paired)[0], 1., atol=1e-12)
    rotation = np.linalg.qr(rng.normal(size=(4, 4)))[0]
    np.testing.assert_allclose(card.cosines(paired@rotation)[0], card.cosines(paired)[0], atol=1e-12)
    np.testing.assert_allclose(card.cosines(paired*np.array([1., -1.])[None, :, None])[0], -1., atol=1e-12)
    values, zero = card.cosines(np.zeros((8, 2, 4)))
    np.testing.assert_array_equal(values, 0.); assert zero.all()


def test_fitted_planted_personal_directions_beat_rebuilt_assignments():
    rows, x, clusters = world(); people = sorted({r["writer"] for r in rows})
    first = stats.evaluate(rows, x, {}, people)
    actual, _, _ = card.paired(first, card.fit_half(rows, x, {}, people), people)
    real, _ = card.cosines(actual); null = []
    for j in range(24):
        assigned = stats.assignment(rows, clusters, "country_50_clusters", card.SEED+j)
        a = stats.evaluate(rows, x, assigned, people)
        b = card.fit_half(rows, x, assigned, people)
        null.append(card.cosines(card.paired(a, b, people)[0])[0])
    result = card.summarize(real, null, 300)
    assert result["state"] == "positive" and result["paired_annotator_95_interval"][0] > 0


def test_exact_indifference_remains_exact_null_through_fits():
    rows, x, clusters = world(writers=4, conversations=8); x[:] = 0.
    people = sorted({r["writer"] for r in rows}); null = []
    a = stats.evaluate(rows, x, {}, people); b = card.fit_half(rows, x, {}, people)
    real = card.cosines(card.paired(a, b, people)[0])[0]
    for j in range(3):
        assigned = stats.assignment(rows, clusters, "country_50_clusters", card.SEED+j)
        null.append(card.cosines(card.paired(stats.evaluate(rows, x, assigned, people), card.fit_half(rows, x, assigned, people), people)[0])[0])
    result = card.summarize(real, null, 20)
    assert result["state"] == "null" and result["real_minus_permutation_mean"] == 0.
    assert result["paired_annotator_95_interval"] == [0., 0.] and result["permutation_p_one_sided"] == 1.


def test_identical_country_preferences_cannot_pass_as_personal_recurrence():
    rows, x, clusters = world(writers=4, conversations=8)
    # All people face the same menu and make the same choice; shared shrinkage
    # can leave aligned individual-minus-country vectors, but null subtraction
    # must refuse that apparent personal recurrence.
    x[:] = np.eye(4)[None, :, :]-0.25
    for row in rows: row["choice"] = 0
    people = sorted({r["writer"] for r in rows})
    a, b = stats.evaluate(rows, x, {}, people), card.fit_half(rows, x, {}, people)
    real = card.cosines(card.paired(a, b, people)[0])[0]; null = []
    for j in range(3):
        assigned = stats.assignment(rows, clusters, "country_50_clusters", card.SEED+j)
        null.append(card.cosines(card.paired(stats.evaluate(rows, x, assigned, people), card.fit_half(rows, x, assigned, people), people)[0])[0])
    result = card.summarize(real, null, 20)
    assert result["state"] == "null" and result["real_minus_permutation_mean"] == 0.
    assert result["paired_annotator_95_interval"] == [0., 0.] and result["permutation_p_one_sided"] == 1.


def test_paired_decomposition_closes_with_exact_known_components():
    rng = np.random.default_rng(8); people = rng.normal(size=(8, 3))
    halves = np.stack([people-.2, people+.2], axis=1)
    result = card.decompose(halves, ["a"]*4+["b"]*4)
    assert sum(result["sum_squares"].values()) == pytest.approx(result["total_sum_squares"])
    assert result["sum_squares"]["half_within_annotator_disagreement"] == pytest.approx(8*2*3*.2**2)
    assert sum(result["shares"].values()) == pytest.approx(1.)


def test_half_zero_choices_cannot_change_opposite_half_readers():
    rows, x, _ = world(writers=4, conversations=8); people = sorted({r["writer"] for r in rows})
    halves, _, _ = stats.fixed_halves(rows, {}, people); altered = copy.deepcopy(rows)
    for i, row in enumerate(altered):
        if halves[i] == 0: row["choice"] = (row["choice"]+1)%4
    assert card.fit_half(rows, x, {}, people) == card.fit_half(altered, x, {}, people)


def test_different_halves_or_people_cannot_be_paired():
    rows, x, _ = world(writers=4, conversations=8); people = sorted({r["writer"] for r in rows})
    a = stats.evaluate(rows, x, {}, people); b = card.fit_half(rows, x, {}, people)
    b["profiles"][people[0]]["support"]["prompts"] += 1
    with pytest.raises(ValueError, match="split differs"): card.paired(a, b, people)
    b = card.fit_half(rows, x, {}, people); b["train_half"] = 0
    with pytest.raises(ValueError, match="opposite"): card.paired(a, b, people)
    with pytest.raises(ValueError, match="population"): card.paired(a, b, people[:-1])


def test_native_handler_replays_and_authenticates_every_parent_reference(tmp_path):
    inputs = fixture(tmp_path/"inputs"); output = tmp_path/"output"
    config = {"fixture":True, "permutation_draws":2, "bootstrap_draws":20}
    result = card.execute(output, inputs, config)
    assert result["primary"]["annotators"] == 5 and result["primary"]["permutation_draws"] == 2
    assert card.verify(output, inputs, config)["verified"]
    assert card.execute(output, inputs, config) == result
    path = Path(inputs["ca1_summary"]).parent/"permutations/0001.json"
    changed = read(path); changed["train_half"] = 1; path.write_text(json.dumps(changed), encoding="utf8")
    with pytest.raises(ValueError, match="authenticated completion"):
        card.verify(output, inputs, config)


def test_bank_and_full_source_requirements_refuse_smaller_inference(tmp_path):
    inputs = fixture(tmp_path/"inputs")
    with pytest.raises(ValueError, match="exactly 1000"):
        card.execute(tmp_path/"short", inputs, {"permutation_draws":999})
    with pytest.raises(ValueError, match="complete full CA1"):
        card.execute(tmp_path/"full", inputs, {})
    with pytest.raises(ValueError, match="bank differs"):
        card.execute(tmp_path/"different-bank", inputs, {"fixture":True, "permutation_draws":3})


def test_saved_second_half_corruption_is_not_a_valid_resume(tmp_path):
    inputs = fixture(tmp_path/"inputs"); output = tmp_path/"output"
    config = {"fixture":True, "permutation_draws":2, "bootstrap_draws":20}
    card.execute(output, inputs, config)
    path = output/"private_second_half_references/0000.json"
    value = read(path); value["population"][0] += .1; path.write_text(json.dumps(value), encoding="utf8")
    with pytest.raises(ValueError, match="changed CA2 checkpoint"):
        card.execute(output, inputs, config)
    with pytest.raises(ValueError, match="recomputation"):
        card.verify(output, inputs, config)
