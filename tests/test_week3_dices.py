"""CA5 exact nuisance cancellation, stable/reversed profiles and source gates."""
import csv
import json
from pathlib import Path

import numpy as np
import pytest

from runners.drive.cards import week3_dices as card


def planted(reverse=False):
    items = list(range(1, 65)); topics = ["t" + str((i // 2) % 4) for i in range(64)]
    groups = [("g" + str(w // 6), "race") for w in range(12)]
    preferences = np.array([[1., -.5, .5, -1.], [-1., 1., -.5, .5], [.5, -1., 1., -.5],
                            [-.5, .5, -1., 1.], [1., 0., -1., 0.], [-1., 0., 1., 0.]] * 2)
    values = np.array([[.5 + .2 * preferences[w, int(topic[1])] * (-1 if reverse and item % 2 == 0 else 1)
                        for item, topic in zip(items, topics)] for w in range(12)])
    return values, groups, items, topics


def fixture(root):
    root = Path(root); root.mkdir(parents=True, exist_ok=True)
    values, groups, items, topics = planted(); rows = []
    for w in range(len(values)):
        for j, item in enumerate(items):
            score = values[w, j]
            response = "Yes" if score > .55 else "No" if score < .45 else "Unsure"
            rows.append(dict(rater_id="w" + str(w), item_id=item, rater_gender=groups[w][0],
                             rater_race=groups[w][1], harm_type=topics[j], Q_overall=response))
    path = root / "source.csv"
    with path.open("w", encoding="utf8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    (root / "codebook.md").write_text("removed_raters_350 = ['w5', 'w11']\n", encoding="utf8")
    return {"source": str(path), "codebook": str(root / "codebook.md")}


def test_group_item_and_leniency_cancel_exactly():
    _, groups, items, topics = planted()
    values = np.array([[w * .01 + j * .005 + (w // 6) * (j % 3) * .1 for j in range(64)] for w in range(12)])
    profiles, mask, _, _ = card.adjusted_profiles(values, groups, items, topics)
    np.testing.assert_array_equal(profiles, 0.)
    assert np.all(mask)
    result = card.profile_correlations(profiles)
    assert np.all(result[0] == 0.) and np.all(result[1])


def test_known_stable_and_reversed_directions():
    for reverse, expected in ((False, 1.), (True, -1.)):
        profiles, _, _, _ = card.adjusted_profiles(*planted(reverse))
        np.testing.assert_allclose(card.profile_correlations(profiles)[0], expected, atol=1e-12)


def test_balanced_decomposition_closes():
    values, groups, _, _ = planted()
    report = card.decomposition(values, groups)
    assert sum(report["sum_squares"].values()) == pytest.approx(report["total_sum_squares"])
    assert "cannot be separated" in report["limitation"]


def test_permutation_preserves_every_group_item_distribution():
    values, groups, _, _ = planted(); changed = card.permutation(values, groups, 13)
    for ids in (slice(0, 6), slice(6, 12)):
        np.testing.assert_array_equal(np.sort(values[ids], axis=0), np.sort(changed[ids], axis=0))
    assert not np.array_equal(values, changed)


def test_planted_primary_beats_rebuilt_null():
    values, groups, items, topics = planted()
    result = card.compute(values, groups, items, topics, dict(permutation_draws=99, bootstrap_draws=200))
    assert result["state"] == "positive" and result["paired_rater_95_interval"][0] > 0


def test_quality_subset_and_crossing_refusal(tmp_path):
    inputs = fixture(tmp_path)
    values, _, _, _, quality = card.load(inputs, {"fixture": True})
    assert values.shape == (12, 64) and quality.sum() == 10
    path = Path(inputs["source"])
    lines = path.read_text().splitlines(); path.write_text("\n".join(lines[:-1]) + "\n")
    with pytest.raises(ValueError, match="fully crossed"):
        card.load(inputs, {"fixture": True})


def test_native_handler_replays_both_denominators(tmp_path):
    inputs = fixture(tmp_path / "input"); root = tmp_path / "output"
    config = {"fixture": True, "permutation_draws": 8, "bootstrap_draws": 20}
    result = card.execute(root, inputs, config)
    assert result["primary_all_released_raters"]["raters"] == 12
    assert result["sensitivity_published_quality_subset"]["raters"] == 10
    assert card.verify(root, inputs, config)["verified"]
    path = root / "SUMMARY.json"; value = json.loads(path.read_text())
    value["primary_all_released_raters"]["real_minus_permutation_mean"] += .1
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="recomputation"):
        card.verify(root, inputs, config)


def test_no_unfrozen_source_or_small_null_bank(tmp_path):
    inputs = fixture(tmp_path)
    with pytest.raises(ValueError, match="pinned DICES"):
        card.load(inputs, {})
    with pytest.raises(ValueError, match="1000"):
        card.execute(tmp_path / "out", inputs, {"permutation_draws": 20})
