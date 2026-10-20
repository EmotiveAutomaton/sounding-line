import numpy as np
import pytest
from runners.drive.cards.week_reading_order import metadata_matrix, make_order, variance_gain


def records():
    return [dict(session=str(i), writer="a", prompt=str(i % 3),
                 timestamp=10-i, typed_words=10+2*i) for i in range(12)]


def test_gain_matches_full_matrix_inverse_and_is_nonnegative():
    covariance = np.array([[2., .3], [.3, .8]])
    target = np.array([1., -.2])
    candidate = np.array([.5, 3.])
    updated = np.linalg.inv(np.linalg.inv(covariance) + np.outer(candidate, candidate))
    expected = target @ (covariance-updated) @ target
    assert variance_gain(covariance, target, candidate) == pytest.approx(expected, abs=1e-14)
    assert expected >= 0


@pytest.mark.parametrize("policy", ["chronological", "random", "directed", "directed_random20"])
def test_full_permutation_probability_ledger_and_reproducibility(policy):
    result = make_order(records(), policy, 45)
    assert result == make_order(list(reversed(records())), policy, 45)
    assert len({s["session"] for s in result["steps"]}) == 12
    for step in result["steps"]:
        p = step["candidate_probabilities"]
        assert sum(p.values()) == pytest.approx(1)
        assert p[step["session"]] == step["conditional_pick_probability"]
        assert step["expected_reference_variance_drop"] >= 0
        if policy in {"random", "directed_random20"}:
            assert all(value > 0 for value in p.values())
        else:
            assert sum(value > 0 for value in p.values()) == 1
    assert result["population_weights_available"] is False


def test_chronology_and_variance_monotonicity():
    result = make_order(records(), "chronological", 99)
    assert [r["session"] for r in result["steps"]] == [str(i) for i in reversed(range(12))]
    before = [r["predictive_variance_before"] for r in result["steps"]]
    assert all(a >= b for a, b in zip(before, before[1:]))


def test_hidden_profiles_are_rejected_not_silently_used():
    data = records()
    data[0]["style_profile"] = [99]
    with pytest.raises(ValueError, match="pre-read"):
        make_order(data, "directed", 1)


def test_constant_metadata_finite_and_exact_ties_stable():
    data = [dict(session=str(i), writer="a", prompt="same", timestamp=0, typed_words=0) for i in range(3)]
    _, matrix = metadata_matrix(data)
    assert np.isfinite(matrix).all()
    assert [s["session"] for s in make_order(data, "directed", 2)["steps"]] == ["0", "1", "2"]


@pytest.mark.parametrize("field,value", [("typed_words", -1), ("timestamp", float("nan")), ("writer", "b"), ("session", "1")])
def test_invalid_identity_and_measurement_refuse(field, value):
    data = records(); data[0][field] = value
    with pytest.raises(ValueError):
        make_order(data, "directed", 0)
