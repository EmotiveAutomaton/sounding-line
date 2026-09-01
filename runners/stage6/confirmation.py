"""Stage 6 closure engine (brief §8 B track, §10.3): the two untouched confirmations of
the frozen claims, the Ghost V14 bridge ledger, and the closure analysis the final packet
reads. The confirmation freeze (at most two claims, selected at hour 144 by the scheduler
and written to CONFIRMATION_REGISTRY) happens before these cards run; B01/B02 execute the
frozen estimand on confirmation-lane worlds and cannot substitute endpoints.

DESIGN CHECK (2026-08-30)
lessons read: LESSONS §3 (confirmation access only after the freeze; the oracle is a
  ceiling, never the comparator; a failed confirmation stays in the packet), §5.
bands: B01/B02 use the exhaustive bands on the frozen estimand at the frozen threshold;
  B03 and B04 are ledgers (INFRASTRUCTURE / DESCRIPTIVE).
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from runners.stage6 import cards as CARDS_MOD                                      # noqa: E402
from runners.stage6.cardrun import CardRun6                                        # noqa: E402
from soundingline.stage6 import (S6, GHOST_V14, ghost_coverage, now_iso,           # noqa: E402
                                 read_json, read_registry, write_registry)

SEED = 67100


def _confirm(run: CardRun6, slot: int) -> int:
    reg = read_registry("CONFIRMATION_REGISTRY") or {}
    sel = (reg.get("selected") or [])
    if len(sel) < slot:
        run.finish({"registry": reg},
                   {"exec": "COMPLETE", "outcome": "NOT_RUN",
                    "primary": CARDS_MOD.ALL[run.card]["primary"],
                    "reason": "no frozen claim in this slot (fewer than two eligible discoveries at the freeze)"})
        return 0
    claim = sel[slot - 1]
    src_card = claim["card"]
    import os                                                                     # noqa: PLC0415
    os.environ["S6_SPLIT"] = "confirmation"
    try:
        from runners.stage6 import engines as E                                   # noqa: PLC0415
        rival = E.RIVAL_OF.get(src_card)
        if rival:
            rc_rival = E.run_card(rival)  # the comparator arm on the SAME confirmation lineages
            if rc_rival != 0:
                raise RuntimeError(f"confirmation rival {rival} failed rc={rc_rival}")
        rc = E.run_card(src_card)
    finally:
        os.environ.pop("S6_SPLIT", None)
    cv = read_json(S6 / f"{src_card}/confirmation" / "verdict.json") if (S6 / f"{src_card}/confirmation" / "verdict.json").exists() else {}
    run.finish({"claim": claim, "confirmation_verdict": cv, "rc": rc},
               {"exec": "COMPLETE", "outcome": cv.get("outcome", "INSTRUMENT_FAILED"),
                "primary": f"the frozen claim ({src_card}: {claim.get('what', '')}) on untouched confirmation lineages",
                "reason": cv.get("reason", "confirmation run missing"), "point": cv.get("point"),
                "ci": cv.get("ci"), "n_units": cv.get("n_units")})
    return 0


def run_b03(run: CardRun6) -> int:
    """The Ghost bridge ledger: which LANDED V14 rulers could transfer (receipt-by-receipt
    with source hashes), and which Stage 6 results feed back as context only. Nothing is
    imported into a Stage-6 estimand mid-run; the ledger names what a future contract MAY
    import, per the reservation rule (§11.5)."""
    cov = ghost_coverage() or {}
    rows = []
    v14_dir = GHOST_V14
    for name in ("COVERAGE.json", "CLAIM_LEDGER.json", "CONSTRUCTION_IDENTITIES.json"):
        p = v14_dir / name
        if p.exists():
            rows.append({"file": name, "sha": hashlib.sha256(p.read_bytes()).hexdigest()[:16],
                         "read_only": True})
    resolved = cov.get("mandatory_resolved")
    ledger = {"written_at": now_iso(), "v14_coverage": {"resolved": resolved, "total": cov.get("mandatory_total")},
              "receipts": rows,
              "transferable_when_landed": [
                  {"ruler": "V14 joint-reconstruction exact posteriors", "condition": "landed receipt + final verdict + source hash", "status": "candidate"},
                  {"ruler": "V14 route-reliability constructions", "condition": "same", "status": "candidate"},
                  {"ruler": "V14 foraging generators", "condition": "same", "status": "candidate"}],
              "feedback_to_ghost": "context only; no V15 is opened by any Stage-6 result (§18.30)"}
    write_registry("GHOST_BRIDGE", ledger)
    ok = bool(rows)
    run.finish({"ledger": ledger},
               {"exec": "COMPLETE", "outcome": "INFRASTRUCTURE" if ok else "VOID",
                "primary": CARDS_MOD.ALL["B03"]["primary"],
                "reason": f"V14 at {resolved}/{cov.get('mandatory_total')} resolved; {len(rows)} receipts hashed; imports deferred to a future contract"})
    return 0


def run_b04(run: CardRun6) -> int:
    """Closure analysis: pursuit and warrant per §15's routing table, from landed verdicts;
    the packet itself is written by the scheduler's reporter after hour 168."""
    verdicts = {}
    for c in CARDS_MOD.CARDS:
        p = S6 / c / "verdict.json"
        if p.exists():
            verdicts[c] = read_json(p)
    def oc(c):
        return (verdicts.get(c) or {}).get("outcome")
    crit = read_json(S6 / "P12" / "metrics.json") if (S6 / "P12" / "metrics.json").exists() else {}
    m08 = oc("M08")
    routing = []
    if crit.get("met_by"):
        routing.append({"shape": "contextual realization improves next edit, stopping, and transfer", "pursuit": "PROMOTE",
                        "warrant": "MECHANISM CANDIDATE (model-reader only)"})
    elif m08 in ("VALID_NULL", "COUNTEREVIDENCE", "INCONCLUSIVE"):
        best = [c for c in ("M02", "M03", "M04", "M05", "M06", "M07") if oc(c) == "SUPPORT_CANDIDATE"]
        routing.append({"shape": f"a published scaffold wins or nothing does (CR {m08}; supports: {best})",
                        "pursuit": "PROMISING engineering route" if best else "revise the distinctive mechanism",
                        "warrant": "evidence for that implementation, not the umbrella theory"})
    i05 = read_json(S6 / "I05" / "metrics.json") if (S6 / "I05" / "metrics.json").exists() else {}
    passed = [r for r, v in (i05.get("readers") or {}).items() if v.get("passed")]
    if not passed:
        routing.append({"shape": "all readers fail supplied-true-state prediction", "pursuit": "interface/capability only; inference comparisons close",
                        "warrant": "reader boundary, not evidence that maker states are absent"})
    for shape, card, good in (("focal-plus-habit control", "C11", "SUPPORT_CANDIDATE"),
                              ("dated histories separate value change", "V14", "SUPPORT_CANDIDATE"),
                              ("exploration tetrad prospectively separable", "F11", "SUPPORT_CANDIDATE")):
        if oc(card) == good:
            routing.append({"shape": shape, "pursuit": "promote per §15", "warrant": "constructed/model evidence only"})
    counts: dict = {}
    for c, v in verdicts.items():
        counts[v.get("outcome")] = counts.get(v.get("outcome"), 0) + 1
    stage7 = {"ruling_needed": True, "machine_view": "opened only by the curator; no result opens it automatically (§18.30)"}
    run.finish({"routing": routing, "outcome_counts": counts, "stage7": stage7, "n_verdicts": len(verdicts)},
               {"exec": "COMPLETE", "outcome": "DESCRIPTIVE",
                "primary": CARDS_MOD.ALL["B04"]["primary"],
                "reason": json.dumps(counts)})
    return 0


def run_card(run: CardRun6) -> int:
    if run.card == "B01":
        return _confirm(run, 1)
    if run.card == "B02":
        return _confirm(run, 2)
    if run.card == "B03":
        return run_b03(run)
    if run.card == "B04":
        return run_b04(run)
    raise ValueError(run.card)
