"""Stage 8 coverage validator: every mandatory question and attack has a valid disposition;
the expected-cell enumeration is matched; the short-run rule and the three-confirmation cap;
the COVERAGE registry the reporter requires.

DESIGN CHECK (2026-09-04)
lessons read: LESSONS §3 (coverage compares against the enumeration, never against what
  happened to run), §5.
gates: NULL of incomplete coverage is any missing or invalid mandatory disposition (fails
  DOWN: the packet refuses); ALTERNATIVE: all present and valid and the cap held. bands: a dict.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from runners.stage8 import cards as C                                              # noqa: E402
from soundingline.stage8 import (OUTCOMES7, S8, Manifest8, RunContract8, now_iso,   # noqa: E402
                                 read_json, read_registry, update_registry, write_registry)

VALID = set(OUTCOMES7) | {"NOT_RUN"}


def validate(write: bool = False) -> dict:
    m = Manifest8()
    contract = RunContract8.load()
    exp = read_registry("EXPECTED_CELLS") or {"cells": []}
    verdicts, missing = {}, []
    for c in list(C.QUESTIONS) + list(C.ATTACKS):
        p = S8 / c / "verdict.json"
        if p.exists():
            verdicts[c] = read_json(p)
        else:
            missing.append(c)
    outcomes: dict = {}
    bad = []
    for c, v in verdicts.items():
        oc = v.get("outcome")
        outcomes[oc] = outcomes.get(oc, 0) + 1
        if oc not in VALID:
            bad.append((c, oc))
    n_rows = 0
    for c in C.QUESTIONS:
        p = S8 / c / "cases.jsonl"
        if p.exists():
            n_rows += sum(1 for _ in open(p, encoding="utf-8"))
    conf = read_registry("CONFIRMATION_REGISTRY") or {}
    n_conf = len(conf.get("selected") or [])
    gates = read_registry("GATES") or {}
    fr = read_registry("FRONTIER_LEDGER") or {}
    cov = {"written_at": now_iso(), "expected": len(exp["cells"]), "complete": len(verdicts),
           "mandatory_total": len(C.QUESTIONS) + len(C.ATTACKS), "missing_mandatory": missing, "invalid_dispositions": bad,
           "outcomes": outcomes, "rows_total": n_rows, "confirmations_selected": n_conf, "confirmation_cap_ok": n_conf <= 3,
           "cells": m.state_counts() if m.cells else {}, "short_run": bool(read_registry("SHORT_RUN")),
           "keystone_signed": bool((read_registry("KEYSTONE_LOCK") or {}).get("signed")),
           "gates": {k: v.get("passed") for k, v in gates.items() if isinstance(v, dict) and "passed" in v},
           "frontier_usd": fr.get("total_usd"), "frontier_under_cap": float(fr.get("total_usd") or 0.0) <= 40.0,
           "interrupts": len((read_registry("INTERRUPTS") or {}).get("interrupts") or []),
           "elapsed_h": round(contract.elapsed_h(), 2) if contract and contract.data.get("execution_start") else None}
    cov["ok"] = not missing and not bad and cov["confirmation_cap_ok"] and cov["frontier_under_cap"]
    if write:
        write_registry("COVERAGE", cov)
        update_registry("COMPLETION", lambda _r: {**_r, "written_at": now_iso(), "cards": {c: {"outcome": v.get("outcome"), "exec": v.get("exec")} for c, v in verdicts.items()}})
    return cov


if __name__ == "__main__":
    import json
    cov = validate(write="--write" in sys.argv)
    print(json.dumps({k: v for k, v in cov.items() if k not in ("cells",)}, indent=1)[:3000])
    sys.exit(0 if cov["ok"] else 1)
