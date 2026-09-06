"""The pre-registration is checkable, or it is decoration.

These tests are the whole reason the hash-locking is worth anything: they let someone who does
not trust the author confirm that the spec, the gate verdict, the hypothesis family and the
pre-registered criteria are the ones that were written down before the runs.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

from soundingline.hashlock import LockViolation, hash_file, hash_obj
from soundingline.locks import LOCKS, REPO_ROOT

# The lock KEYS are the paths the artifacts had when they were locked, and two documentation
# reorganisations have moved six of them since (docs/gateN -> docs/gates/gateN on 2026-08-08;
# the spec off the top level on 2026-08-21). Both are recorded in docs/method/DEVIATIONS.md,
# and `tools/verify_locks.py` is the canonical verifier that carries the mapping -- the mapping
# lives THERE rather than in soundingline/locks.py precisely because locks.py is itself
# hash-protected and must not be edited (CLAUDE.md, hard rules).
#
# This module used to call `soundingline.locks.verify_all()`, which resolves keys literally and
# so raised FileNotFoundError on the first moved artifact. Eight tests here failed on that --
# NOT because a lock was broken (all 21 verify byte for byte through the canonical path) but
# because the test was reading the pre-move layout. Routed through `current_path` it agrees
# with `tools/verify_locks.py`, which is the point: the two must not be able to disagree.
sys.path.insert(0, str(REPO_ROOT / "tools"))
from verify_locks import current_path                                            # noqa: E402


def _verify_all_at_current_paths() -> None:
    for key, expected in LOCKS.items():
        got = hash_file(current_path(key))
        if got != expected:
            raise LockViolation(f"{key}: {got} != {expected}")


def test_all_locks_hold():
    """Every locked artifact still hashes to its recorded value."""
    _verify_all_at_current_paths()


@pytest.mark.parametrize("rel", sorted(LOCKS))
def test_locked_file_exists(rel):
    assert current_path(rel).is_file(), f"locked artifact missing: {rel}"


def test_the_canonical_verifier_and_this_module_agree():
    """A control on the control's address. If `tools/verify_locks.py` passes while this module
    fails, one of them is reading a layout the other does not, and the pre-registration is only
    as checkable as whichever one someone happens to run."""
    import subprocess
    r = subprocess.run([sys.executable, str(REPO_ROOT / "tools" / "verify_locks.py")],
                       capture_output=True, text=True, timeout=120)
    _verify_all_at_current_paths()
    assert r.returncode == 0, f"canonical verifier disagrees with this module: {r.stdout}"


def test_lock_actually_fires(tmp_path, monkeypatch):
    """A control on the control.

    The simulation found four separate criteria unable to do their own job. The failure mode was
    always the same -- nobody checked that the check could fire. So: perturb a byte, confirm the
    verifier raises.
    """
    key = "soundingline/family/family_v1.yaml"
    original_path = current_path(key)
    path = tmp_path / "family_v1.yaml"
    path.write_bytes(original_path.read_bytes())
    resolve = current_path
    monkeypatch.setattr(sys.modules[__name__], "current_path",
                        lambda name: path if name == key else resolve(name))
    _verify_all_at_current_paths()
    path.write_bytes(path.read_bytes() + b"\n# perturbation\n")
    with pytest.raises(LockViolation):
        _verify_all_at_current_paths()
    assert hash_file(original_path) == LOCKS[key]


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
