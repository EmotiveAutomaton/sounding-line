"""Stage 7 closure engine (brief §10 B, §12.5, B01-B06): at most three frozen claims run on
untouched confirmation lineages (selected at the freeze by the scheduler and written to
CONFIRMATION_REGISTRY), the Ghost V15 status/hash bridge, the ledger reconciliation, and
the closure analysis the final packet reads. A failed confirmation is never replaced by
the next-ranked result.

DESIGN CHECK (2026-09-02)
lessons read: LESSONS §3 (confirmation access only after the freeze; the oracle is a
  ceiling, never the comparator; a failed confirmation stays in the packet; the frozen
  estimand cannot be substituted), §5.
gates: B01-B03 use the exhaustive bands on the frozen estimand at the frozen floor on
  untouched lineages (NULL: the interval covers zero or sits under the floor; ALTERNATIVE:
  above; failure direction DOWN and final); B04-B06 are ledgers (INFRASTRUCTURE /
  DESCRIPTIVE / VOID). bands: exhaustive.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from runners.stage7 import cards as C                                              # noqa: E402
from runners.stage7.cardrun import CardRun7                                        # noqa: E402
from soundingline.stage7 import (GHOST_V15, S7, ghost_receipt, ghost_status, now_iso,  # noqa: E402
                                 read_json, read_registry, sha256_file, write_registry, update_registry)


def _confirm(run: CardRun7, slot: int) -> int:
    reg = read_registry("CONFIRMATION_REGISTRY") or {}
    sel = reg.get("selected") or []
    if len(sel) < slot:
        run.finish({"registry": reg}, {"exec": "COMPLETE", "outcome": "NOT_RUN", "primary": C.ALL[run.card]["primary"],
                                       "reason": "no frozen claim in this slot (fewer eligible discoveries at the freeze)"})
        return 0
    claim = sel[slot - 1]
    src = claim["card"]
    os.environ["S7_SPLIT"] = "confirmation"
    try:
        from runners.stage7 import engines as E                                   # noqa: PLC0415
        rc = E.run_card(src)
    finally:
        os.environ.pop("S7_SPLIT", None)
    cv = read_json(S7 / f"{src}/confirmation" / "verdict.json") if (S7 / f"{src}/confirmation" / "verdict.json").exists() else {}
    run.finish({"claim": claim, "confirmation_verdict": cv, "rc": rc},
               {"exec": "COMPLETE", "outcome": cv.get("outcome", "INSTRUMENT_FAILED"),
                "primary": f"the frozen claim ({src}: {claim.get('what', '')}) on untouched confirmation lineages",
                "reason": cv.get("reason", "confirmation run missing"), "point": cv.get("point"), "ci": cv.get("ci"), "n_units": cv.get("n_units"),
                "conditional_cells": cv.get("conditional_cells")})
    return 0


def run_B04(run: CardRun7) -> int:
    rec = ghost_receipt()
    st = ghost_status()
    files = {}
    for name in ("RUNNER_STATUS.json", "COMPLETION.json", "COVERAGE.json"):
        p = GHOST_V15 / name
        if p.exists():
            files[name] = sha256_file(p)[:16]
    ledger = {"written_at": now_iso(), "head": rec.get("head"), "reviewed_head": "ce4c06b", "v15_complete": rec.get("v15_complete"),
              "status": {k: st.get(k) for k in ("live", "stage", "age_min", "program")}, "files": files,
              "imported": [], "rule": "status/hash bridge only; partial V15 outcomes are never imported; no V16 is opened by any Stage 7 result"}
    write_registry("GHOST_BRIDGE", ledger)
    run.finish({"ledger": ledger}, {"exec": "COMPLETE", "outcome": "INFRASTRUCTURE" if rec.get("exists") else "VOID",
                                    "primary": C.ALL["B04"]["primary"],
                                    "reason": f"V15 head {rec.get('head')} (reviewed ce4c06b); complete {rec.get('v15_complete')}; live {st.get('live')}; nothing imported"})
    return 0


def run_B05(run: CardRun7) -> int:
    """Ledger agreement: coverage, sources, access, compute, dependency, conformance,
    gates, and claims reconcile with the verdicts on disk."""
    from runners.stage7.validate import validate                                  # noqa: PLC0415
    cov = validate(write=True)
    checks = {"coverage_ok": cov.get("ok"), "source_manifest": bool(read_registry("SOURCE_MANIFEST")),
              "access_receipt": bool((read_registry("ACCESS_RECEIPT") or {}).get("all_raised")),
              "compute_ledger": bool(read_registry("COMPUTE_LEDGER")), "dependency_audit": bool(read_registry("STAGE6_DEPENDENCY_AUDIT")),
              "conformance": bool(read_registry("CONFORMANCE")), "gates": bool(read_registry("GATES")),
              "confirmation_registry": bool(read_registry("CONFIRMATION_REGISTRY")), "split_receipt": bool((read_registry("SPLIT_RECEIPT") or {}).get("clean"))}
    verdicts = {}
    for c in list(C.QUESTIONS) + list(C.ATTACKS):
        p = S7 / c / "verdict.json"
        if p.exists():
            verdicts[c] = read_json(p).get("outcome")
    pursuit = {c: v for c, v in verdicts.items() if v == "SUPPORT_CANDIDATE"}
    conf = read_registry("CONFIRMATION_REGISTRY") or {}
    warrant = {s["card"]: (read_json(S7 / f"B0{i + 1}" / "verdict.json").get("outcome") if (S7 / f"B0{i + 1}" / "verdict.json").exists() else None)
               for i, s in enumerate(conf.get("selected") or [])}
    update_registry("COMPLETION", lambda _r: {**_r, "pursuit": pursuit, "warrant": warrant, "checks": checks, "at": now_iso()})
    ok = all(v for k, v in checks.items() if k not in ("confirmation_registry",))
    run.finish({"checks": checks, "pursuit": pursuit, "warrant": warrant, "n_verdicts": len(verdicts)},
               {"exec": "COMPLETE", "outcome": "INFRASTRUCTURE" if ok else "INSTRUMENT_FAILED", "primary": C.ALL["B05"]["primary"],
                "reason": json.dumps(checks)})
    return 0


def run_B06(run: CardRun7) -> int:
    """The closure analysis the packet reads: what moved, by the §12.2 branching table."""
    def oc(c):
        p = S7 / c / "verdict.json"
        return read_json(p).get("outcome") if p.exists() else None
    routing = []
    g = read_registry("GATES") or {}
    if not (g.get("construction") or {}).get("passed"):
        routing.append({"shape": "K01 has no oracle gap on a target", "action": "that target INSTRUMENT_FAILED; no reader tested on it"})
    if (g.get("supplied_state") or {}).get("passed"):
        routing.append({"shape": "K04 passes: a reader can use a complete supplied executable state", "action": "factor-inference rungs interpretable"})
    else:
        routing.append({"shape": "K04 fails with executable true state", "action": "K16 diagnoses; factor-inference comparisons close for that target; a state-use/interface boundary"})
    if oc("K04") == "SUPPORT_CANDIDATE" and oc("K05") not in ("SUPPORT_CANDIDATE", None):
        routing.append({"shape": "K04 passes but K05 fails", "action": "an interface loss in the language rendering; not general incapacity"})
    if (g.get("learn_law") or {}).get("passed") is False and oc("K14") in ("SUPPORT_CANDIDATE",):
        routing.append({"shape": "KL works but R09 fails", "action": "known-law system identification retained; law-learning language closed"})
    for f in ("proximal_goal", "belief_state", "expertise_law", "subjective_action_space", "maker_context"):
        if (g.get(f"recall_{f}") or {}).get("passed") is False:
            routing.append({"shape": f"candidate recall fails for {f}", "action": "selection comparisons cannot rescue absent candidates"})
    conf = read_registry("CONFORMANCE") or {}
    for fam, rec in conf.items():
        if not rec.get("pass"):
            routing.append({"shape": f"external conformance fails: {fam}", "action": f"the mechanism runs under its local name {rec.get('admitted_name')}"})
    if oc("R13") in ("SUPPORT_CANDIDATE",):
        routing.append({"shape": "SL-J beats DOM (R13)", "action": "a maker-specific reconstruction candidate; confirmation decides"})
    if (g.get("discontinuity") or {}).get("passed") and (g.get("style_crossover") or {}).get("passed") and oc("B03") == "SUPPORT_CANDIDATE":
        routing.append({"shape": "P11/P12 pass and B03 confirms", "action": "promote a bounded mixed-process detector to a separate confirmation program; never a universal detector"})
    if (g.get("dated_history") or {}).get("passed") or oc("V06") == "SUPPORT_CANDIDATE":
        routing.append({"shape": "V05/V06 pass", "action": "carry the longitudinal ruler into a future value-shadow design; no value or alignment claim"})
    short = read_registry("SHORT_RUN")
    if short:
        routing.append({"shape": "the locked useful work exhausted early", "action": "honest short-run receipt; no filler"})
    counts: dict = {}
    for c in list(C.QUESTIONS) + list(C.ATTACKS):
        counts[oc(c)] = counts.get(oc(c), 0) + 1
    run.finish({"routing": routing, "outcome_counts": counts, "gates": {k: v.get("passed") for k, v in g.items() if isinstance(v, dict) and "passed" in v},
                "stage8": {"ruling_needed": True, "machine_view": "opened only by the curator after Pass A; no result opens it automatically (§19)"}},
               {"exec": "COMPLETE", "outcome": "DESCRIPTIVE", "primary": C.ALL["B06"]["primary"], "reason": json.dumps(counts)})
    return 0


def run_card(run: CardRun7) -> int:
    if run.card == "B01":
        return _confirm(run, 1)
    if run.card == "B02":
        return _confirm(run, 2)
    if run.card == "B03":
        return _confirm(run, 3)
    if run.card == "B04":
        return run_B04(run)
    if run.card == "B05":
        return run_B05(run)
    if run.card == "B06":
        return run_B06(run)
    raise ValueError(run.card)
