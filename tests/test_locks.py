"""The pre-registration is checkable, or it is decoration.

These tests are the whole reason the hash-locking is worth anything: they let someone who does
not trust the author confirm that the spec, the gate verdict, the hypothesis family and the
pre-registered criteria are the ones that were written down before the runs.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from soundingline.hashlock import LockViolation, hash_file, hash_obj
from soundingline.locks import LOCKS, REPO_ROOT, verify_all


def test_all_locks_hold():
    """Every locked artifact still hashes to its recorded value."""
    verify_all()


@pytest.mark.parametrize("rel", sorted(LOCKS))
def test_locked_file_exists(rel):
    assert (REPO_ROOT / rel).is_file(), f"locked artifact missing: {rel}"


def test_lock_actually_fires():
    """A control on the control.

    The simulation found four separate criteria unable to do their own job. The failure mode was
    always the same -- nobody checked that the check could fire. So: perturb a byte, confirm the
    verifier raises.
    """
    path = REPO_ROOT / "soundingline" / "family" / "family_v1.yaml"
    original = path.read_bytes()
    try:
        path.write_bytes(original + b"\n# perturbation\n")
        with pytest.raises(LockViolation):
            verify_all()
    finally:
        path.write_bytes(original)
    verify_all()  # and it is clean again afterwards


def test_hash_obj_is_order_stable():
    """Dict construction order must not move the hash, or the card lock is worthless."""
    assert hash_obj({"a": 1, "b": 2}) == hash_obj({"b": 2, "a": 1})


def test_hash_file_is_byte_exact():
    """Line endings are content. On Windows this is not hypothetical."""
    a = REPO_ROOT / "soundingline" / "family" / "family_v1.yaml"
    assert hash_file(a) == hash_file(Path(a))


# ---------------------------------------------------------------------------------------------
# The family is data, so it gets the checks data gets.

def _family() -> dict:
    path = REPO_ROOT / "soundingline" / "family" / "family_v1.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_family_has_the_five_spec_dimensions():
    """SPEC §4's table, exactly. Not a superset -- an extra dimension is an unrecorded change
    to the instrument."""
    assert set(_family()["dimensions"]) == {
        "purpose", "audience", "depth", "cost_borne", "trade_offs"
    }


def test_audience_carries_the_two_distinct_empty_cases():
    """`machine` and `nobody_in_particular` must both exist and must not be merged.

    This is the load-bearing distinction of SPEC §4: `machine` is the presence of a non-human
    audience model, `nobody_in_particular` is the absence of any audience model. Collapsing them
    destroys the audience posterior, which is the output that says the socially useful thing
    without making an accusation.
    """
    ids = {v["id"] for v in _family()["dimensions"]["audience"]["values"]}
    assert {"machine", "nobody_in_particular"} <= ids


def test_load_bearing_dimensions_are_marked():
    """Audience, depth and trade-offs are the three the spec calls load-bearing."""
    dims = _family()["dimensions"]
    assert {d for d, v in dims.items() if v["load_bearing"]} == {
        "audience", "depth", "trade_offs"
    }


def test_family_states_what_it_may_not_claim():
    """SPEC §1. The instrument never makes a claim about authorship, and the file that defines
    the instrument has to say so."""
    claims = _family()["may_not_claim"]
    assert any("machine wrote this" in c for c in claims)
    assert any("tuple" in c for c in claims)
