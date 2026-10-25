"""Known-null, severity/topic separation, fixed-grid and full replay controls."""
import json
from pathlib import Path

import numpy as np
import pytest

from runners.drive.cards import week3_dices as base
from runners.drive.cards import week3_dices_followup as shared
from runners.drive.cards import week3_dices_specification as specification
from runners.drive.cards import week3_dices_mechanism as mechanism
from runners.drive.cards.menus_io import input_hashes, read, sha256, write
from tests.test_week3_dices import fixture as source_fixture, planted


def fixture(root):
    root = Path(root)
    inputs = source_fixture(root)
    # Constructed admission receipt only; production admission binds real hashes.
    parent = root / "parent-summary.json"
    write(parent, {"card": "CA5", "input_hashes": input_hashes(inputs),
                   "primary_all_released_raters": {"state": "positive"}})
    complete = root / "parent-complete.json"
    write(complete, {"status": "COMPLETE", "fresh_process_verified": True,
                     "outputs": {"output/SUMMARY.json": sha256(parent)}})
    return {**inputs, "parent_summary": str(parent), "parent_complete": str(complete)}


def test_fixed_halves_use_metadata_and_exact_partition():
    items = [1, 2, 3, 7, 10, 12]
    np.testing.assert_array_equal(shared.split_labels(items, "odd_even"), [1, 0, 1, 1, 0, 0])
    np.testing.assert_array_equal(shared.split_labels(items, "first_last"), [0, 0, 0, 1, 1, 1])
    with pytest.raises(ValueError, match="unique ascending"):
        shared.split_labels(items[::-1], "first_last")
    with pytest.raises(ValueError, match="frozen"):
        shared.split_labels(items, "random")


def test_unsure_recoding_retains_every_entry_and_endpoint():
    values = np.array([[0., .5, 1.], [1., .5, 0.]])
    for value in shared.UNSURE:
        changed = shared.recode(values, value)
        assert changed.shape == values.shape
        np.testing.assert_array_equal(changed[:, [0, 2]], values[:, [0, 2]])
        assert np.all(changed[:, 1] == value)
    with pytest.raises(ValueError, match="outside"):
        shared.recode(values, .25)


def test_odd_even_features_equal_original_frozen_method():
    values, groups, items, topics = planted()
    expected, supported, retained, missing = base.adjusted_profiles(values, groups, items, topics)
    actual, _, counts = shared.features(values, groups, items, topics, "odd_even")
    np.testing.assert_array_equal(actual, expected)
    assert np.all(supported) and counts["topics_in_both_halves"] == len(retained)
    assert counts["topics_missing_from_one_half"] == missing


def test_stable_severity_only_cannot_create_topic_recurrence():
    _, groups, items, topics = planted()
    values = np.array([[.01 * w + .005 * j + .02 * (w // 6) * (j % 3) for j in range(64)] for w in range(12)])
    for split in shared.SPLITS:
        profiles, severity, _ = shared.features(values, groups, items, topics, split)
        np.testing.assert_array_equal(profiles, 0.)
        assert mechanism.correlation(severity) == pytest.approx(1.)
        assert np.all(base.profile_correlations(profiles)[0] == 0.)


def test_stable_and_reversed_topics_without_severity():
    for reverse, expected in ((False, 1.), (True, -1.)):
        profiles, severity, _ = shared.features(*planted(reverse), "odd_even")
        np.testing.assert_allclose(base.profile_correlations(profiles)[0], expected, atol=1e-12)
        np.testing.assert_array_equal(severity, 0.)
        assert mechanism.correlation(severity) == 0.


def test_severity_reversal_is_negative_and_constants_are_zero():
    x = np.arange(12, dtype=float)
    assert mechanism.correlation(np.column_stack([x, -x])) == pytest.approx(-1.)
    assert mechanism.correlation(np.column_stack([x, np.ones(12)])) == 0.
    assert mechanism.correlation(np.ones((12, 2))) == 0.


def test_both_mechanisms_can_coexist():
    values, groups, items, topics = planted()
    values += np.tile(np.linspace(-.1, .1, 6), 2)[:, None]
    profiles, severity, _ = shared.features(values, groups, items, topics, "odd_even")
    np.testing.assert_allclose(base.profile_correlations(profiles)[0], 1., atol=1e-12)
    assert mechanism.correlation(severity) == pytest.approx(1.)


def test_singleton_or_missing_topic_does_not_drop_population():
    values, groups, items, topics = planted()
    groups[0] = ("singleton", "group")
    profiles, severity, counts = shared.features(values, groups, items, topics, "odd_even")
    assert profiles is severity is None and counts["raters"] == 12 and counts["singleton_group_raters"] == 1
    _, groups, _, _ = planted()
    profiles, _, counts = shared.features(values, groups, items, ["only"] * 64, "odd_even")
    assert profiles is None and counts["raters"] == 12


def test_exact_group_item_null_is_null_in_both_endpoints():
    _, groups, items, topics = planted()
    values = np.array([[.1 * (j % 5) + .2 * (w // 6) for j in range(64)] for w in range(12)])
    profiles, severity, _ = shared.features(values, groups, items, topics, "odd_even")
    real = base.profile_correlations(profiles)[0]
    null_topics, null_severity = [], []
    for j in range(9):
        fp, fs, _ = shared.features(base.permutation(values, groups, shared.SEED + j), groups, items, topics, "odd_even")
        null_topics.append(base.profile_correlations(fp)[0]); null_severity.append(fs)
    for result in (shared.topic_report(real, np.asarray(null_topics), 20),
                   mechanism.severity_report(severity, np.asarray(null_severity), 20)):
        assert result["state"] == "null" and result["real_minus_permutation_mean"] == 0.
        assert result["paired_rater_95_interval"] == [0., 0.] and result["permutation_p_one_sided"] == 1.


def test_severity_bootstrap_is_paired_full_null_recomputation():
    rng = np.random.default_rng(42)
    real, null = rng.normal(size=(9, 2)), rng.normal(size=(7, 9, 2))
    result = mechanism.severity_report(real, null, 23)
    ix = np.random.default_rng(shared.SEED + 10001).integers(0, 9, size=(23, 9))
    expected = [float(mechanism.correlation(real[i])) - np.mean([mechanism.correlation(n[i]) for n in null]) for i in ix]
    np.testing.assert_allclose(result["paired_rater_95_interval"], np.quantile(expected, [.025, .975]), atol=1e-14)


def test_planted_severity_survives_the_actual_assignment_reference():
    _, groups, items, topics = planted()
    values = np.tile(np.linspace(0., 1., 6), 2)[:, None] + np.zeros((12, 64))
    _, real, _ = shared.features(values, groups, items, topics, "odd_even")
    bank = [shared.features(base.permutation(values, groups, shared.SEED + j), groups, items, topics, "odd_even")[1] for j in range(99)]
    result = mechanism.severity_report(real, np.asarray(bank), 200)
    assert result["state"] == "positive" and result["paired_rater_95_interval"][0] > 0


def test_holm_includes_all_cells_and_is_order_preserving():
    np.testing.assert_allclose(shared.holm([.04, .001, .02, 1.]), [.08, .004, .06, 1.])


@pytest.mark.parametrize("module", [specification, mechanism])
def test_execute_and_fresh_replay_preserve_denominators_and_refuse_mutation(tmp_path, module):
    inputs = fixture(tmp_path / "inputs")
    output = tmp_path / "output"
    config = {"fixture": True, "permutation_draws": 9, "bootstrap_draws": 20}
    result = module.execute(output, inputs, config)
    cells = result.get("cells", result.get("populations"))
    assert len(cells) == (12 if module is specification else 2)
    assert set(c["raters"] for c in cells) == {12, 10}
    assert all(c["items"] == 64 for c in cells)
    assert result["followups_allowed"] is False
    assert module.verify(output, inputs, config)["verified"]
    saved = read(output / "SUMMARY.json"); saved["followup_generation"] = 2
    (output / "SUMMARY.json").write_text(json.dumps(saved), encoding="utf8")
    with pytest.raises(ValueError, match="recomputation"):
        module.verify(output, inputs, config)


def test_production_bank_source_and_parent_gates(tmp_path):
    inputs = fixture(tmp_path)
    with pytest.raises(ValueError, match="exactly 1000"):
        shared.admit(inputs, {"permutation_draws": 999})
    with pytest.raises(ValueError, match="unfrozen"):
        shared.admit(inputs, {"fixture": True, "best_split": True})
    with pytest.raises(ValueError, match="pinned DICES"):
        shared.admit(inputs, {})
    path = Path(inputs["parent_summary"])
    value = read(path); value["primary_all_released_raters"]["state"] = "null"
    path.write_text(json.dumps(value), encoding="utf8")
    with pytest.raises(ValueError, match="not authenticated"):
        shared.admit(inputs, {"fixture": True})
    complete = read(inputs["parent_complete"]); complete["outputs"]["output/SUMMARY.json"] = sha256(path)
    Path(inputs["parent_complete"]).write_text(json.dumps(complete), encoding="utf8")
    with pytest.raises(ValueError, match="positive CA5"):
        shared.admit(inputs, {"fixture": True})
