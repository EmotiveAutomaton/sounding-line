"""Stage 3 completion validator (brief section 6.5). Fails loudly on every contract
violation; PROGRAM-EXHAUSTED may be declared only when this passes with every mandatory
cell resolved. Also writes COVERAGE.json.

Checks: mandatory cells present; floors unreduced (estimates may be re-measured, floors
may not shrink); produces uniqueness; landed cells carry outputs and actual runtimes;
closures carry reasons; statuses legal; remaining-work rule (if projected remaining work
is under 24 hours while eligible frozen expansions remain uninstantiated, FAIL).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from soundingline.s3 import (COVERAGE_PATH, STATUSES, TOTAL_ATTEMPT_FLOOR,       # noqa: E402
                             TRUNK_FLOORS, load_manifest)
from soundingline import completion                                              # noqa: E402

MANDATORY_PREFIXES = [
    "E24-S3-S01", "E24-S3-S02", "E24-S3-S03", "E24-S3-S04", "E24-S3-S05", "E24-S3-S06",
    "E24-S3-L01", "E24-S3-L02", "E24-S3-L03", "E24-S3-L04", "E24-S3-L05",
    "E24-S3-D01", "E24-S3-D02", "E24-S3-D03", "E24-S3-D04", "E24-S3-D05", "E24-S3-D06",
    "E24-S3-E01", "E24-S3-E02", "E24-S3-E03", "E24-S3-E04", "E24-S3-E05", "E24-S3-E06",
    "E24-S3-A01", "E24-S3-A02", "E24-S3-A03", "E24-S3-A04", "E24-S3-A05", "E24-S3-A06",
    "E24-S3-A07",
    "E24-S3-M01", "E24-S3-M02", "E24-S3-M03", "E24-S3-M04",
    "E24-S3-H01", "E24-S3-H02", "E24-S3-H03", "E24-S3-H04", "E24-S3-H05", "E24-S3-H06",
    "E24-S3-H07",
    "E24-S3-C01", "E24-S3-C02", "E24-S3-C03", "E24-S3-C04", "E24-S3-C05", "E24-S3-C06",
    "E24-S3-V01", "E24-S3-V02", "E24-S3-V03", "E24-S3-V04", "E24-S3-V05", "E24-S3-V06",
]
RESOLVED = ("LANDED", "INSTRUMENT_FAILED", "SCIENTIFIC_CLOSED", "RESOURCE_BLOCKED")
VALID_ATTEMPT = ("LANDED", "INSTRUMENT_FAILED", "SCIENTIFIC_CLOSED")


def main() -> int:
    cells = load_manifest()
    errors, warnings = [], []
    ids = [c["cell_id"] for c in cells]

    for p in MANDATORY_PREFIXES:
        if not any(i == p or i.startswith(p + "/") for i in ids):
            errors.append(f"mandatory card absent: {p}")

    prods = [c["produces"] for c in cells]
    if len(prods) != len(set(prods)):
        dupes = {p for p in prods if prods.count(p) > 1}
        errors.append(f"produces collision: {dupes}")

    for c in cells:
        if c["status"] not in STATUSES:
            errors.append(f"{c['cell_id']}: illegal status {c['status']}")
        if c["status"] == "LANDED":
            # H4 (2026-08-28): this was `exists()`. A truncated JSON left by a killed writer,
            # a zero-byte file, and a result carrying another cell's id all passed it, so
            # PROGRAM-EXHAUSTED could be declared over a hole while the status counts and the
            # attempt floors both looked complete. The shared validator reads the artifact.
            chk = completion.inspect(REPO / c["produces"],
                                     expect={"cell_id": c["cell_id"], "lane": c.get("lane")})
            if chk["status"] in completion.BAD:
                errors.append(f"{c['cell_id']}: LANDED with a {chk['status']} produce "
                              f"({chk['reason']})")
            elif chk["status"] == completion.UNVERIFIABLE:
                # legacy artifact predating the identity stamp: reported, never fabricated,
                # and never silently relabelled invalid
                warnings.append(f"{c['cell_id']}: produce carries no identity to verify "
                                f"({chk['reason']})")
            if c.get("actual_gpu_minutes") is None:
                errors.append(f"{c['cell_id']}: LANDED without actual runtime")
        if c["status"] in ("SCIENTIFIC_CLOSED", "INSTRUMENT_FAILED",
                          "RESOURCE_BLOCKED") and not c.get("closure_reason"):
            errors.append(f"{c['cell_id']}: closure without recorded reason")

    per_trunk_valid = {t: 0 for t in TRUNK_FLOORS}
    for c in cells:
        if c["status"] in VALID_ATTEMPT and c["trunk"] in per_trunk_valid:
            per_trunk_valid[c["trunk"]] += 1
    total_valid = sum(per_trunk_valid.values())

    remaining = sum(c["estimated_gpu_minutes"] for c in cells
                    if c["status"] in ("PLANNED", "BUILT", "VALIDATED", "RUNNING"))
    all_resolved = all(c["status"] in RESOLVED for c in cells)

    if remaining / 60 < 24 and not all_resolved:
        planned_left = [c["cell_id"] for c in cells if c["status"] == "PLANNED"]
        if not planned_left:
            errors.append("projected remaining work under 24h with unresolved cells and "
                          "no PLANNED expansion instantiated (ladder rungs 5-8 owed)")

    exhausted = (all_resolved and total_valid >= TOTAL_ATTEMPT_FLOOR
                 and all(per_trunk_valid[t] >= f for t, f in TRUNK_FLOORS.items()))

    COVERAGE_PATH.write_text(json.dumps({
        "n_cells": len(cells),
        "per_status": {s: sum(1 for c in cells if c["status"] == s) for s in STATUSES},
        "valid_attempts_per_trunk": per_trunk_valid,
        "total_valid_attempts": total_valid,
        "attempt_floor": TOTAL_ATTEMPT_FLOOR, "trunk_floors": TRUNK_FLOORS,
        "estimated_remaining_gpu_hours": remaining / 60,
        "program_exhausted_eligible": exhausted,
        "produce_inventory": completion.inventory(
            [(str(REPO / c["produces"]),
              {"cell_id": c["cell_id"], "lane": c.get("lane")}) for c in cells])["counts"],
        "errors": errors, "warnings": warnings}, indent=1),
        encoding="utf-8", newline="\n")

    print(f"{len(cells)} cells; valid attempts {total_valid}/{TOTAL_ATTEMPT_FLOOR}; "
          f"remaining {remaining / 60:.1f} GPU-h; "
          f"exhausted-eligible: {exhausted}")
    for e in errors:
        print(f"  ERROR: {e}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
