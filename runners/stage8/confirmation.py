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

    from runners.stage8.admission import admitted_readers
    from runners.stage8.claims import select_claims
    reg = {"written_at": now_iso(), **select_claims(S8, admitted_readers()),
           "rule": "per-reader freeze rule, explicit slots; failed confirmation never replaced"}
    write_registry("CONFIRMATION_REGISTRY", reg)
    return reg


def _confirm(run: CardRun8, slot: int) -> int:
    reg = read_registry("CONFIRMATION_REGISTRY") or {}
    from runners.stage8.admission import admitted_readers
    from runners.stage8.claims import mapping_errors, file_hash, measured_identity
    selected = [x for x in reg.get("selected", []) if x.get("slot") == slot]
    if not selected:
        run.finish({"registry": reg}, {"exec": "COMPLETE", "outcome": "NOT_RUN",
                   "primary": C.ALL[run.card]["primary"], "reason": "no frozen claim in this explicit slot"})
        return 0
    if len(selected) != 1:
        raise ValueError("duplicate frozen slot")
    claim = selected[0]
    errors = mapping_errors(claim)
    adm = admitted_readers().get(claim.get("reader")) or {}
    if not adm.get("admitted") or adm.get("prediction_identity") != claim.get("admission_identity"):
        errors.append("frozen reader is not admitted under the same identity")
    if errors:
        raise ValueError("; ".join(errors))
    existing = S8 / claim["result_path"]
    if existing.exists():
        v = read_json(existing)
        if v.get("claim_id") != claim["claim_id"] or v.get("reader") != claim["reader"]:
            raise ValueError("existing confirmation belongs to another claim; preserve it")
        return 0  # including failed confirmation; never replace it
    src = claim["card"]
    if file_hash(S8 / claim["source_path"]) != claim["source_sha256"]:
        raise ValueError("frozen discovery source changed")
    if file_hash(S8 / src / "metrics.json") != claim["source_metrics_sha256"]:
        raise ValueError("frozen discovery estimand source changed")
    if (file_hash(S8 / src / "cases.jsonl") != claim["source_cases_sha256"]
            or measured_identity(S8, src, claim["reader"], claim["estimand"]["arm"]) != claim["admission_identity"]):
        raise ValueError("frozen discovery measured lineage changed")
    # A failed or malformed existing attempt is evidence, never permission to replace it.
    p = S8 / claim["confirmation_source_path"]
    if p.exists():
        rc = None
    else:
        prior_split = os.environ.get("S7_SPLIT")
        os.environ["S7_SPLIT"] = "confirmation"
        try:
            from runners.stage8 import engines as E
            rc = E.run_card(src)
        finally:
            if prior_split is None:
                os.environ.pop("S7_SPLIT", None)
            else:
                os.environ["S7_SPLIT"] = prior_split
    cv = read_json(p) if p.exists() else {}
    mp = p.with_name("metrics.json")
    metrics = read_json(mp) if mp.exists() else {}
    measured = (metrics.get(claim["slice"]) or {}).get(claim["reader"]) or {}
    same = (cv.get("card") == src and cv.get("cell_id") == f"{src}/confirmation"
            and cv.get("lane") == "confirmation" and not cv.get("diagnosis_only")
            and cv.get("exec") == "COMPLETE" and measured.get("outcome") is not None
            and metrics.get("card") == src and metrics.get("lane") == "confirmation"
            and measured_identity(S8, f"{src}/confirmation", claim["reader"], claim["estimand"]["arm"]) == claim["admission_identity"]
            and all(measured.get(k) == v for k, v in claim["estimand"].items()))
    run.finish({"claim": claim, "confirmation_verdict": cv, "rc": rc},
               {"exec": "COMPLETE", "outcome": measured.get("outcome") if same else "INSTRUMENT_FAILED",
                "claim_id": claim["claim_id"], "reader": claim["reader"],
                "confirmation_compatible": same,
                "confirmation_hashes": {name: file_hash(p.with_name(name)) for name in
                                        ("verdict.json", "metrics.json", "cases.jsonl") if p.with_name(name).is_file()},
                "primary": f"frozen {claim['what']} on untouched confirmation lineages",
                "reason": measured.get("reason", "missing or incompatible confirmation evidence"),
                "point": measured.get("point") if same else None, "ci": measured.get("ci") if same else None,
                "n_units": measured.get("n_units") if same else None})
    return 0


def run_B04(run: CardRun8) -> int:
    def oc(c):
        p = S8 / c / "verdict.json"
        return read_json(p).get("outcome") if p.exists() else None
    g = read_registry("GATES") or {}
    from runners.stage8.admission import admitted_readers
    eg = admitted_readers()
    routing = []
    adm = [k for k, x in eg.items() if x.get("passed")]
    if not adm:
        routing.append({"shape": "no trained reader passes both prediction and generation with matching identity", "action": "the stage's reader claims close; E08 and D01 ran as diagnosis; the testbed and construction facts stand; theory-change interrupt"})
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
        from runners.stage8.claims import eligible_support_readers
        path = S8 / c / "verdict.json"
        if path.exists() and eligible_support_readers(read_json(path), eg):
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
    cov = validate(write=True, exclude_pending={"B03"})
    missing_due = [c for c in (cov.get("missing_mandatory") or []) if c != "B03"]
    fr = read_registry("FRONTIER_LEDGER") or {}
    checks = {"coverage_ok": cov["ok"], "missing_due": missing_due,
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
    from runners.stage8.admission import admitted_readers
    from runners.stage8.claims import confirmation_warrant
    warrant = confirmation_warrant(S8, conf, admitted_readers())
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
