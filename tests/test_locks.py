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
    path = REPO_ROOT / "soundingline" / "family" / "family_v2.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_family_has_the_v2_dimensions():
    """SPEC §4's table plus the two dimensions calibration added.

    Still not a superset test by accident: an extra dimension beyond these is an unrecorded
    change to the instrument. The two additions are recorded in CALIBRATION_02 §5 and in the
    family file's own `provenance_of_changes`.
    """
    assert set(_family()["dimensions"]) == {
        "purpose", "audience", "depth", "cost_borne",
        "artifact_effort", "demonstrated_work", "trade_offs",
    }


def test_effort_is_two_dimensions_not_one():
    """The curator split effort before it was built; it must not be re-collapsed.

    Collapsing these loses the postmortem case -- a cheap document about an expensive thing --
    which is where the depth construct attaches for reportage.
    """
    dims = _family()["dimensions"]
    assert "artifact_effort" in dims and "demonstrated_work" in dims
    assert "effort" not in dims, "effort must not exist as a single collapsed dimension"


def test_artifact_effort_records_its_own_recovery_ceiling():
    """CALIBRATION_02 §7: partially recoverable by construction, because the missing
    information is how the artifact was made -- which the instrument refuses to claim."""
    assert "limit" in _family()["dimensions"]["artifact_effort"]


def test_family_records_its_known_limits():
    """A family that cannot say what it cannot express invites the overclaim."""
    limits = {l["id"] for l in _family()["known_limits"]}
    assert {"L-1", "L-2", "L-3", "L-4"} <= limits


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
        "audience", "depth", "demonstrated_work", "trade_offs"
    }


def test_family_states_what_it_may_not_claim():
    """SPEC §1. The instrument never makes a claim about authorship, and the file that defines
    the instrument has to say so."""
    claims = _family()["may_not_claim"]
    assert any("machine wrote this" in c for c in claims)
    assert any("tuple" in c for c in claims)
