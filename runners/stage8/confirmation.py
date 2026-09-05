"""Stage 8 closure engine (brief §7 B, §9): at most three frozen claims run on untouched
confirmation lineages (chosen by rule at the freeze: the strongest gate-passing reader
effect against DOM; the strongest purpose or accumulation effect; a tail-only effect if one
cleared its floor), the world-model routing cell (B04), and the ledger reconciliation
(B03), which runs LAST (the Stage 7 B05 lesson: the ledger cell runs after what it counts).

DESIGN CHECK (2026-09-04)
lessons read: LESSONS §3 (confirmation only after the freeze; the oracle is a ceiling; a
  failed confirmation stays; the frozen estimand is never substituted), §5 (order the
  closure by what each cell reads).
gates: B01/B02: the exhaustive bands on the frozen estimand at the frozen floor on
  untouched lineages (NULL: the interval covers zero or sits under the floor; ALTERNATIVE:
  above; DOWN and final). B03: NULL is any ledger disagreeing (fails DOWN); ALTERNATIVE:
  all agree. B04: descriptive routing. bands: exhaustive.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from runners.stage8 import cards as C                                              # noqa: E402
from runners.stage8.cardrun import CardRun8                                        # noqa: E402
from soundingline.stage8 import (S8, interrupts, now_iso, read_json, read_registry,  # noqa: E402
                                 update_registry, write_registry)


def freeze_confirmations() -> dict:
    """The freeze rule (§9): slot 1 the strongest gate-passing reader effect against DOM;
    slot 2 the strongest purpose or accumulation effect; slot 3 a tail-only effect."""
    if read_registry("CONFIRMATION_REGISTRY"):
        return read_registry("CONFIRMATION_REGISTRY")

    def v(c):
        p = S8 / c / "verdict.json"
        x = read_json(p) if p.exists() else {}
        return {} if x.get("diagnosis_only") else x        # a diagnosis cell is never a confirmation claim

    def lower(x):
        return (x.get("ci") or [-1e9])[0] if x.get("ci") else -1e9
    sel = []
    adm = {k for k, x in ((read_registry("EXPERTISE_GATE") or {}).get("readers") or {}).items() if x.get("passed")}
    c1 = [(c, v(c)) for c in ("G02", "A03", "E08", "E06") if v(c).get("outcome") == "SUPPORT_CANDIDATE" and adm]
    if c1:
        c, x = max(c1, key=lambda kv: lower(kv[1]))
        sel.append({"card": c, "what": f"the strongest gate-passing reader effect against DOM ({x.get('primary', '')[:100]})", "point": x.get("point"), "slot": 1})
    c2 = [(c, v(c)) for c in ("G02", "G03", "A01", "A03", "A05") if v(c).get("outcome") == "SUPPORT_CANDIDATE" and c not in {s["card"] for s in sel}]
    if c2:
        c, x = max(c2, key=lambda kv: lower(kv[1]))
        sel.append({"card": c, "what": f"the strongest purpose or accumulation effect ({x.get('primary', '')[:100]})", "point": x.get("point"), "slot": 2})
    c3 = [(c, v(c)) for c in ("G02", "G03", "E08", "A03", "A05", "E06") if v(c).get("tail_outcome") == "SUPPORT_CANDIDATE" and v(c).get("outcome") != "SUPPORT_CANDIDATE" and c not in {s["card"] for s in sel}]
    if c3:
        c, x = max(c3, key=lambda kv: (kv[1].get("tail_ci") or [-1e9])[0])
        sel.append({"card": c, "what": f"a tail-only effect that cleared its floor ({x.get('primary', '')[:100]})", "point": x.get("tail_point"), "slot": 3, "tail_only": True})
    reg = {"written_at": now_iso(), "selected": sel[:3],
           "rule": "the strongest gate-passing reader effect against DOM; the strongest purpose or accumulation effect; a tail-only effect if one cleared its floor (§9); untouched lineages; a failed confirmation is never replaced"}
    write_registry("CONFIRMATION_REGISTRY", reg)
    return reg


def _confirm(run: CardRun8, slot: int) -> int:
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
        from runners.stage8 import engines as E                                   # noqa: PLC0415
        rc = E.run_card(src)
    finally:
        os.environ.pop("S7_SPLIT", None)
    p = S8 / f"{src}/confirmation" / "verdict.json"
    cv = read_json(p) if p.exists() else {}
    oc = cv.get("tail_outcome") if claim.get("tail_only") else cv.get("outcome")
    run.finish({"claim": claim, "confirmation_verdict": cv, "rc": rc},
               {"exec": "COMPLETE", "outcome": oc or "INSTRUMENT_FAILED",
                "primary": f"the frozen claim ({src}: {claim.get('what', '')}) on untouched confirmation lineages",
                "reason": cv.get("reason", "confirmation run missing"), "point": cv.get("tail_point") if claim.get("tail_only") else cv.get("point"),
                "ci": cv.get("tail_ci") if claim.get("tail_only") else cv.get("ci"), "n_units": cv.get("n_units"), "conditional_cells": cv.get("conditional_cells")})
    return 0


def run_B04(run: CardRun8) -> int:
    def oc(c):
        p = S8 / c / "verdict.json"
        return read_json(p).get("outcome") if p.exists() else None
    g = read_registry("GATES") or {}
    eg = (read_registry("EXPERTISE_GATE") or {}).get("readers") or {}
    routing = []
    adm = [k for k, x in eg.items() if x.get("passed")]
    if not adm:
        routing.append({"shape": "E03 fails on every trained reader", "action": "the stage's reader claims close; E08 and D01 ran as diagnosis; the testbed and construction facts stand; theory-change interrupt"})
    else:
        routing.append({"shape": f"the expertise gate admits {adm}", "action": "the difference, purpose, and accumulation trunks are interpretable on those readers"})
    if oc("E05") == "SUPPORT_CANDIDATE":
        routing.append({"shape": "an untrained reader passes the gate", "action": "the Stage 7 boundary reading is wrong; theory-change interrupt"})
    if (g.get("difference") or {}).get("passed") is False and adm:
        routing.append({"shape": "D01 fails on an admitted reader", "action": "the difference mechanism claim narrows to 'with the purpose known' (D04)"})
    if (g.get("purpose_recall") or {}).get("passed") is False:
        routing.append({"shape": "G01 recall under 0.5 after the repair", "action": "the selection cards read as bounded diagnosis"})
    g05 = read_json(S8 / "G05" / "metrics.json") if (S8 / "G05" / "metrics.json").exists() else {}
    for rd, rec in (g05.get("per_reader") or {}).items():
        d = rec.get("difference_purpose_minus_pull")
        if d is not None and abs(d) >= 0.2:
            routing.append({"shape": f"G05: {'the purpose' if d > 0 else 'the pull ordering'} is easier for {rd} by {abs(d):.2f}", "action": "theory movement in the packet; no interrupt"})
    for c in ("E07", "G08"):
        if oc(c) == "SUPPORT_CANDIDATE":
            routing.append({"shape": f"{c} passes on FR", "action": "reported; FR never becomes a reader arm this stage"})
    for c in ("G02", "A03", "E08"):
        if oc(c) == "SUPPORT_CANDIDATE":
            routing.append({"shape": f"an FM arm beats DOM on the whole artifact ({c})", "action": "freeze candidate; never pooled across readers before the per-reader cells are read"})
    if read_registry("SHORT_RUN"):
        routing.append({"shape": "the locked useful work exhausted early", "action": "the re-sized ladder was admitted; the short-run receipt stands"})
    counts: dict = {}
    for c in list(C.QUESTIONS) + list(C.ATTACKS):
        counts[oc(c)] = counts.get(oc(c), 0) + 1
    tb = read_registry("TESTBED") or {}
    run.finish({"routing": routing, "outcome_counts": counts, "interrupts": interrupts(), "gates": {k: v.get("passed") for k, v in g.items() if isinstance(v, dict) and "passed" in v},
                "testbed": {"clones": len(tb.get("clones") or {}), "corpora": len(tb.get("corpora") or {})},
                "stage9": {"ruling_needed": True, "machine_view": "opened only by the curator after Pass A; no result opens it automatically (§16)"}},
               {"exec": "COMPLETE", "outcome": "DESCRIPTIVE", "primary": C.ALL["B04"]["primary"], "reason": json.dumps(counts)})
    return 0


def run_B03(run: CardRun8) -> int:
    from runners.stage8.validate import validate                                  # noqa: PLC0415
    cov = validate(write=True)
    missing_due = [c for c in (cov.get("missing_mandatory") or []) if c != "B03"]
    fr = read_registry("FRONTIER_LEDGER") or {}
    checks = {"coverage_ok": not missing_due and not cov.get("invalid_dispositions"), "missing_due": missing_due,
              "source_manifest": bool(read_registry("TESTBED_SOURCES")), "corpus_manifests": bool(read_registry("CORPUS_MANIFESTS")),
              "access_receipt": bool((read_registry("ACCESS_RECEIPT") or {}).get("all_raised")),
              "compute_ledger": bool(read_registry("COMPUTE_LEDGER")), "dollar_ledger_under_cap": float(fr.get("total_usd") or 0.0) <= 40.0,
              "adapters": bool(read_registry("ADAPTERS")), "gates": bool(read_registry("GATES")),
              "confirmation_registry": bool(read_registry("CONFIRMATION_REGISTRY")), "split_receipt": bool((read_registry("SPLIT_RECEIPT") or {}).get("clean")),
              "fresh_clone": (read_json(S8 / "X12" / "verdict.json").get("outcome") == "INFRASTRUCTURE") if (S8 / "X12" / "verdict.json").exists() else False}
    verdicts = {}
    for c in list(C.QUESTIONS) + list(C.ATTACKS):
        p = S8 / c / "verdict.json"
        if p.exists():
            verdicts[c] = read_json(p).get("outcome")
    pursuit = {c: v for c, v in verdicts.items() if v == "SUPPORT_CANDIDATE"}
    conf = read_registry("CONFIRMATION_REGISTRY") or {}
    warrant = {s["card"]: (read_json(S8 / f"B0{i + 1}" / "verdict.json").get("outcome") if (S8 / f"B0{i + 1}" / "verdict.json").exists() else None)
               for i, s in enumerate(conf.get("selected") or [])}
    update_registry("COMPLETION", lambda _r: {**_r, "pursuit": pursuit, "warrant": warrant, "checks": checks, "at": now_iso()})
    ok = all(v for k, v in checks.items() if k not in ("confirmation_registry", "missing_due"))
    run.finish({"checks": checks, "pursuit": pursuit, "warrant": warrant, "n_verdicts": len(verdicts), "frontier_usd": fr.get("total_usd")},
               {"exec": "COMPLETE", "outcome": "INFRASTRUCTURE" if ok else "INSTRUMENT_FAILED", "primary": C.ALL["B03"]["primary"], "reason": json.dumps(checks)})
    return 0


def run_card(run: CardRun8) -> int:
    if run.card == "B01":
        return _confirm(run, 1)
    if run.card == "B02":
        return _confirm(run, 2)
    if run.card == "B03":
        return run_B03(run)
    if run.card == "B04":
        return run_B04(run)
    raise ValueError(run.card)
