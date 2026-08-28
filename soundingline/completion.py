"""Is this artifact a real completion, or just a file that exists? (H4, 2026-08-28)

Both places that asked "is this stage done?" answered with `Path.exists()`:

  * `runners/run_queue.py` skipped any stage whose `produces` path existed, and
  * `runners/validate_stage3_program.py` passed a LANDED cell whose produce existed.

A zero-byte file, a truncated JSON left by a killed writer, and a result belonging to a
different card all satisfy `exists()`. The second one is the dangerous case: a stage that
died mid-write is skipped forever by the scheduler AND counted as landed by the program
validator, so PROGRAM-EXHAUSTED can be declared over a hole. `exit code 0` does not mean
usable output either -- a process can exit clean having written nothing readable.

This module is the one shared check. It is deliberately STRUCTURAL: it decides whether a
measurement can be READ, never whether the science is good. Four meanings stay separate and
this file only speaks to the first two:

  execution resolved   the attempt reached a declared closure state       (manifest's job)
  instrument valid     the artifact is present, parseable, and identified (HERE)
  scientific result    positive / negative / inconclusive / counterevidence   (verdict's job)
  report delivered     documentation and curator review                      (FINDINGS' job)

A valid NEGATIVE result completes. `usable()` returning True is not a claim that the result
supports anything; a broken instrument returning False is not a theory-negative. Callers keep
that distinction -- this file cannot make it for them.

LEGACY: `usable()` takes `expect` only when the caller actually knows what to expect. An
artifact written before a field existed is reported UNVERIFIABLE, never relabelled invalid and
never given fabricated provenance. Missing historical execution identity stays unknown.
"""

from __future__ import annotations

import json
from pathlib import Path

# Status vocabulary for the read-only inventory.
OK = "ok"                       # present, parses, identity matches (or nothing to check)
MISSING = "missing"             # no file
EMPTY = "empty"                 # zero bytes, or a container with no content
MALFORMED = "malformed"         # present but unparseable for its declared type
MISIDENTIFIED = "misidentified"  # parses, but belongs to a different card/stage/lane
UNVERIFIABLE = "unverifiable"   # parses, but carries no identity to check against `expect`

BAD = (MISSING, EMPTY, MALFORMED, MISIDENTIFIED)

# Identity keys an artifact may carry. Absent keys are unknown, never assumed to match.
IDENTITY_KEYS = ("cell_id", "card", "stage", "lane", "split", "lineage_id", "arm")


def _check_json(p: Path, expect: dict | None) -> tuple[str, str]:
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
    except ValueError as e:
        return MALFORMED, f"not valid JSON: {e}"
    except OSError as e:
        return MALFORMED, f"unreadable: {e}"
    if obj is None or (isinstance(obj, (list, dict, str)) and len(obj) == 0):
        return EMPTY, "parses but carries no content"
    if not expect:
        return OK, ""
    if not isinstance(obj, dict):
        return UNVERIFIABLE, f"{type(obj).__name__} carries no identity fields to check"
    checked = 0
    for k, want in expect.items():
        if k not in obj:
            continue                       # legacy artifact: unknown, not wrong
        checked += 1
        if obj[k] != want:
            return MISIDENTIFIED, f"{k} is {obj[k]!r}, expected {want!r}"
    if checked == 0:
        return UNVERIFIABLE, f"carries none of {sorted(expect)}; identity unknown"
    return OK, ""


def _check_jsonl(p: Path, expect: dict | None) -> tuple[str, str]:
    try:
        lines = [ln for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
    except OSError as e:
        return MALFORMED, f"unreadable: {e}"
    if not lines:
        return EMPTY, "no rows"
    for i, ln in enumerate(lines, 1):
        try:
            row = json.loads(ln)
        except ValueError as e:
            # a killed writer truncates the LAST line; that is still a malformed artifact
            return MALFORMED, f"row {i} of {len(lines)} is not valid JSON: {e}"
        if expect and isinstance(row, dict):
            for k, want in expect.items():
                if k in row and row[k] != want:
                    return MISIDENTIFIED, f"row {i}: {k} is {row[k]!r}, expected {want!r}"
    return OK, ""


def _check_opaque(p: Path, expect: dict | None) -> tuple[str, str]:
    """Not every declared artifact is JSON (.pt checkpoints, .csv, .md, .npz). We check
    presence and non-emptiness only, and say so rather than implying more."""
    return (OK, "") if p.stat().st_size > 0 else (EMPTY, "zero bytes")


_CHECKERS = {".json": _check_json, ".jsonl": _check_jsonl}


def inspect(path: Path | str, expect: dict | None = None) -> dict:
    """Read-only. Returns {status, reason, path, bytes}. Never writes, never repairs."""
    p = Path(path)
    if not p.exists():
        return {"path": str(p), "status": MISSING, "reason": "no such file", "bytes": None}
    try:
        size = p.stat().st_size
    except OSError as e:
        return {"path": str(p), "status": MALFORMED, "reason": f"unstattable: {e}",
                "bytes": None}
    if size == 0:
        return {"path": str(p), "status": EMPTY, "reason": "zero bytes", "bytes": 0}
    checker = _CHECKERS.get(p.suffix.lower(), _check_opaque)
    status, reason = checker(p, expect)
    return {"path": str(p), "status": status, "reason": reason, "bytes": size}


def usable(path: Path | str, expect: dict | None = None,
           allow_unverifiable: bool = True) -> bool:
    """The scheduling/validation predicate: may this artifact be treated as a completion?

    `allow_unverifiable` is True by default so that legacy artifacts predating an identity
    field are not mass-relabelled invalid (H4's compatibility rule). Set it False for NEW
    work, where the writer is expected to stamp identity.
    """
    st = inspect(path, expect)["status"]
    if st == UNVERIFIABLE:
        return allow_unverifiable
    return st == OK


def inventory(items: list[tuple[str, dict | None]]) -> dict:
    """Read-only inventory of (path, expect) pairs, grouped by status. For the legacy audit:
    it reports what cannot be verified, and preserves every original untouched."""
    rows = [inspect(p, e) for p, e in items]
    by: dict[str, list[dict]] = {}
    for r in rows:
        by.setdefault(r["status"], []).append(r)
    return {"n": len(rows), "counts": {k: len(v) for k, v in sorted(by.items())}, "by_status": by}
