"""Read-only Stage 4 validator (brief §9.3): expected cells against realized, scored
units against floors, completion markers against the data, duplicate lineages, split
integrity, and the run label against the contract. Writes nothing unless --write is
given (then COVERAGE.json). Exit 0 when nothing is missing, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from runners import s4_cards                                                      # noqa: E402
from runners.s4_scheduler import validate                                         # noqa: E402
from soundingline.s4 import S4, Lineages, RunContract, check_marker, read_json     # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    cov = validate(write=a.write)
    problems = []
    for card in s4_cards.CARDS:
        vp = S4 / card / "verdict.json"
        if vp.exists():
            bad = check_marker(read_json(vp))
            if bad:
                problems.append(f"{card}: marker {bad[:3]}")
    L = Lineages()
    for lid, r in L.rows.items():
        if r.get("parent") and r["split"] != L.rows.get(r["parent"], {}).get("split", r["split"]):
            problems.append(f"{lid}: split differs from parent")
        if r["split"] == "confirmation" and r.get("inspected") and not r.get("confirmation_access"):
            problems.append(f"{lid}: confirmation lineage inspected without recorded access")
    c = RunContract.load()
    if c and c.data.get("run_label") == "COMPLETE_24H" and not c.deadline_passed():
        problems.append("run labeled COMPLETE_24H before its deadline")
    print(json.dumps({"expected": cov.get("expected"), "complete": cov.get("complete"),
                      "missing": len(cov.get("missing", [])), "under_floor": len(cov.get("under_floor", [])),
                      "duplicate_lineages": cov.get("duplicate_lineages"), "cells": cov.get("cells"),
                      "outcomes": cov.get("outcomes"), "problems": problems}, indent=1))
    return 1 if (problems or cov.get("missing") or cov.get("under_floor")) else 0


if __name__ == "__main__":
    sys.exit(main())
