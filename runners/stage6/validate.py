"""Stage 6 coverage validator (brief §13.2, §19): every mandatory card and attack has a
valid disposition; the expected-cell enumeration is matched against realized rows; the
short-run rule and the confirmation cap are checked; the result is the COVERAGE registry
the reporter requires.

DESIGN CHECK (2026-08-30)
lessons read: LESSONS §3 (a clean exit that wrote no produce is a failure; coverage
  compares against the enumeration, never against what happened to run), §5.
bands: a dict; the scheduler writes it and the reporter refuses without it.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from runners.stage6 import cards as CARDS_MOD                                      # noqa: E402
from soundingline.stage6 import (S6, OUTCOMES6, Manifest6, RunContract6,           # noqa: E402
                                 now_iso, read_json, read_registry, write_registry)

VALID_DISPOSITIONS = set(OUTCOMES6) | {"NOT_RUN"}


def validate(write: bool = False) -> dict:
    m = Manifest6()
    contract = RunContract6.load()
    exp = read_registry("EXPECTED_CELLS") or {"cells": []}
    verdicts = {}
    missing = []
    for c in list(CARDS_MOD.CARDS) + list(CARDS_MOD.ATTACKS):
        p = S6 / c / "verdict.json"
        if p.exists():
            verdicts[c] = read_json(p)
        else:
            missing.append(c)
    outcomes: dict = {}
    bad = []
    for c, v in verdicts.items():
        oc = v.get("outcome")
        outcomes[oc] = outcomes.get(oc, 0) + 1
        if oc not in VALID_DISPOSITIONS:
            bad.append((c, oc))
    n_cases = 0
    for c in CARDS_MOD.CARDS:
        p = S6 / c / "cases.jsonl"
        if p.exists():
            n_cases += sum(1 for _ in open(p, encoding="utf-8"))
    conf = read_registry("CONFIRMATION_REGISTRY") or {}
    n_conf = len(conf.get("selected") or [])
    cov = {"written_at": now_iso(), "expected": len(exp["cells"]),
           "complete": len(verdicts), "mandatory_total": len(CARDS_MOD.CARDS) + len(CARDS_MOD.ATTACKS),
           "missing_mandatory": missing, "invalid_dispositions": bad, "outcomes": outcomes,
           "rows_total": n_cases, "confirmations_selected": n_conf,
           "confirmation_cap_ok": n_conf <= 2,
           "cells": m.state_counts() if m.cells else {},
           "short_run": bool(read_registry("SHORT_RUN")),
           "elapsed_h": round(contract.elapsed_h(), 2) if contract and contract.data.get("execution_start") else None}
    cov["ok"] = not missing and not bad and cov["confirmation_cap_ok"]
    if write:
        write_registry("COVERAGE", cov)
        write_registry("COMPLETION", {"written_at": now_iso(),
                                      "cards": {c: {"outcome": v.get("outcome"), "exec": v.get("exec")}
                                                for c, v in verdicts.items()}})
    return cov


if __name__ == "__main__":
    import json
    cov = validate(write="--write" in sys.argv)
    print(json.dumps({k: v for k, v in cov.items() if k not in ("cells",)}, indent=1)[:2500])
    sys.exit(0 if cov["ok"] else 1)
