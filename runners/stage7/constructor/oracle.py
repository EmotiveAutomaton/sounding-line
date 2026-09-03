"""The oracle bundle store (brief §6.1, §14): OracleBundleV1 objects live under the stage
root's oracle/ directory, outside every capsule, readable by constructors and scorers
only; the scorer receives PredictionV1 after the reader process exits and looks the
truth up here. The store also keeps every visible evidence's hash beside its bundle so
I12 can prove paired arms saw identical bytes.

DESIGN CHECK (2026-09-02)
lessons read: LESSONS §5 (a filename two code paths share is built by ONE helper: the
  bundle path is built here and nowhere else), §3.
gates: none here. bands: none.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from soundingline.stage7 import S7, evidence_sha, read_json, write_json           # noqa: E402

ORACLE_DIR = S7 / "oracle"


def bundle_path(cell: str, unit_ref: str) -> Path:
    return ORACLE_DIR / cell.replace("/", "_") / f"{unit_ref}.json"


def save(cell: str, unit_ref: str, bundle: dict, evidence: dict | None = None) -> Path:
    p = bundle_path(cell, unit_ref)
    p.parent.mkdir(parents=True, exist_ok=True)
    b = dict(bundle)
    if evidence is not None:
        b["evidence_sha"] = evidence_sha(evidence)
    write_json(p, b)
    return p


def load(cell: str, unit_ref: str) -> dict | None:
    p = bundle_path(cell, unit_ref)
    return read_json(p) if p.exists() else None
