"""Content-hash locking, carried over from the simulation's habit rather than its code.

The rule the Ghost Scale Simulation held for ten versions and this project inherits:

    Every criterion is written down before its run, as executable code, content-hash locked.
    Where one is changed afterwards it is logged, the original is retained and still computed,
    and it is reported as failing if it fails.

That habit is the single most credible thing about the existing repository (SPEC §9), and the
spec's instruction is not to drop it on the way into a new one. This module is the mechanism.

Three things get locked here, and they are locked for different reasons:

* **Pre-registration cards** — so a criterion cannot be quietly rewritten after seeing a result.
* **The hypothesis family** — so two readings taken under different families are not silently
  compared. Changing `family_v1.yaml` changes the instrument (SPEC §4).
* **Prompt templates** — because in an LLM-based instrument the prompt IS the measurement
  apparatus. The simulation had no analogue of this and it is the most likely place for
  undocumented drift to enter this project.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def hash_obj(obj: Any) -> str:
    """Stable content hash of a JSON-serialisable object.

    `sort_keys` is what makes this stable across dict construction order; without it the same
    card hashes differently between runs and the lock is worthless.
    """
    payload = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def hash_file(path: str | Path) -> str:
    """Content hash of a file, read as bytes.

    Bytes rather than text: a line-ending change is a change. On Windows this matters, and
    silently normalising it would let a file drift without the hash moving.
    """
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class LockViolation(RuntimeError):
    """A locked artifact no longer matches the hash recorded for it.

    This is deliberately an error and not a warning. A run that proceeds against a changed
    criterion produces a number that looks pre-registered and is not, which is worse than no
    number at all.
    """


def verify(path: str | Path, expected: str) -> None:
    """Raise unless `path` still hashes to `expected`.

    Called at the top of every experiment, before any model is touched.
    """
    actual = hash_file(path)
    if actual != expected:
        raise LockViolation(
            f"{path} has changed since it was locked.\n"
            f"  expected: {expected}\n"
            f"  actual:   {actual}\n"
            f"If the change is intended, record it as a deviation in docs/DEVIATIONS.md, "
            f"retain the original, and keep computing it. Do not simply update the hash."
        )
