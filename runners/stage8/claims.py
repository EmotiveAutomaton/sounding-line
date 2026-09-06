"""Explicit confirmation identities, shared by selection, execution and reconciliation.

DESIGN CHECK (2026-09-06)
lessons read: LESSONS sections 3 and 5 (a failed confirmation and its estimand stay).
gates: Under the NULL, another reader, diagnosis, or an unmapped result cannot confirm;
failure direction is DOWN. Under the ALTERNATIVE, an admitted, frozen reader/estimand
has its own declared result path. Bands are exhaustive: EXECUTABLE, UNIMPLEMENTED,
INVALID; B03 is always reconciliation only.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from runners.stage8.admission import gate_identity

SLOT_CARDS = {1: "B01", 2: "B02"}


def eligible_support_readers(verdict: dict, admission: dict) -> list[str]:
    if verdict.get("diagnosis_only"):
        return []
    cells = verdict.get("conditional_cells") or {}
    return [reader for reader, record in admission.items() if record.get("admitted")
            and any((cells.get(key) or {}).get("outcome") == "SUPPORT_CANDIDATE"
                    for key in (reader, f"whole|{reader}", f"tail|{reader}"))]


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mapping_errors(claim: dict) -> list[str]:
    slot, card = claim.get("slot"), claim.get("card")
    errors = []
    if slot not in (1, 2, 3) or not isinstance(card, str) or "/" in card or card.startswith("B"):
        errors.append("invalid confirmation slot or source card")
    if not claim.get("claim_id") or not claim.get("reader") or not claim.get("source_sha256"):
        errors.append("missing frozen claim/reader/source identity")
    if (claim.get("slice") not in ("whole", "tail") or not claim.get("estimand")
            or not claim.get("admission_identity") or not claim.get("source_metrics_sha256")
            or not claim.get("source_cases_sha256")):
        errors.append("missing frozen slice, estimand or admission identity")
    if claim.get("source_path") != f"{card}/verdict.json":
        errors.append("source path does not match source card")
    result = SLOT_CARDS.get(slot)
    if result is None:
        if claim.get("status") != "UNIMPLEMENTED" or claim.get("result_path") is not None or not claim.get("reason"):
            errors.append("slot three must remain explicitly unrun; B03 is reconciliation")
    elif (claim.get("result_card") != result or claim.get("result_path") != f"{result}/verdict.json"
          or claim.get("confirmation_source_path") != f"{card}/confirmation/verdict.json"):
        errors.append("confirmation result mapping does not match executable slot")
    return errors


def measured_identity(root: Path, cell: str, reader: str, arm: str) -> dict:
    path = root / cell / "cases.jsonl"
    if not path.is_file():
        return {"error": "measured source rows absent"}
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if any(row.get("cell_id") != cell for row in rows):
        return {"error": "measured source cell mismatch"}
    return gate_identity(rows, reader, arm)


def select_claims(root: Path, admission: dict) -> dict:
    candidates, declined = [], []
    for card in ("G02", "G03", "E08", "E06", "A01", "A03", "A05"):
        vp, mp = root / card / "verdict.json", root / card / "metrics.json"
        if not vp.exists() or not mp.exists():
            continue
        v, m = json.loads(vp.read_text(encoding="utf-8")), json.loads(mp.read_text(encoding="utf-8"))
        if v.get("diagnosis_only") or v.get("exec") != "COMPLETE":
            continue
        for reader, adm in admission.items():
            if not adm.get("admitted"):
                continue
            for scope in ("whole", "tail"):
                x = (m.get(scope) or {}).get(reader) or {}
                if x.get("outcome") != "SUPPORT_CANDIDATE":
                    continue
                if not x.get("ci") or any(x.get(k) is None for k in ("arm", "rival", "threshold", "point")):
                    declined.append({"card": card, "reader": reader, "slice": scope,
                                     "reason": "per-reader frozen estimand is incomplete"})
                    continue
                if measured_identity(root, card, reader, x["arm"]) != adm["prediction_identity"]:
                    declined.append({"card": card, "reader": reader, "slice": scope,
                                     "reason": "measured discovery rows do not match admitted identity"})
                    continue
                candidates.append({"card": card, "reader": reader, "slice": scope,
                                   "point": x["point"], "ci": x["ci"],
                                   "estimand": {k: x[k] for k in ("arm", "rival", "threshold")},
                                   "source_path": f"{card}/verdict.json", "source_sha256": file_hash(vp),
                                   "source_metrics_sha256": file_hash(mp),
                                   "source_cases_sha256": file_hash(root / card / "cases.jsonl"),
                                   "admission_identity": adm["prediction_identity"]})
    selected = []
    groups = ((1, {"G02", "A03", "E08", "E06"}, "whole"),
              (2, {"G02", "G03", "A01", "A03", "A05"}, "whole"),
              (3, {"G02", "G03", "E08", "A03", "A05", "E06"}, "tail"))
    for slot, allowed, scope in groups:
        eligible = [x for x in candidates if x["card"] in allowed and x["slice"] == scope
                    and x["card"] not in {s["card"] for s in selected}
                    and (slot != 1 or x["estimand"]["rival"] == "DOM")
                    and (slot != 3 or not any(y["card"] == x["card"] and y["reader"] == x["reader"]
                                             and y["slice"] == "whole" for y in candidates))]
        if not eligible:
            continue
        claim = dict(max(eligible, key=lambda x: (x["ci"][0], x["card"], x["reader"])))
        result = SLOT_CARDS.get(slot)
        claim.update(slot=slot, result_card=result, result_path=f"{result}/verdict.json" if result else None,
                     confirmation_source_path=f"{claim['card']}/confirmation/verdict.json" if result else None,
                     status="EXECUTABLE" if result else "UNIMPLEMENTED",
                     reason="frozen per-reader claim" if result else "third executable confirmation path is not implemented; no work launched",
                     tail_only=scope == "tail", what=f"{scope} {claim['card']} effect for {claim['reader']}")
        claim["claim_id"] = hashlib.sha256(json.dumps(claim, sort_keys=True).encode()).hexdigest()[:16]
        selected.append(claim)
    return {"selected": selected, "declined": declined, "mapping_version": 1}


def confirmation_warrant(root: Path, registry: dict, admission: dict) -> dict:
    """Never substitute enumeration, another reader, or a later source verdict."""
    out = {}
    for i, claim in enumerate(registry.get("selected") or []):
        errors = mapping_errors(claim)
        hashes = {}
        adm = admission.get(claim.get("reader")) or {}
        if not adm.get("admitted") or adm.get("prediction_identity") != claim.get("admission_identity"):
            errors.append("frozen reader is not currently eligible under the same identity")
        status, outcome = "INVALID", None
        if claim.get("slot") == 3 and not claim.get("result_path"):
            status = "UNRUN"
            errors.append("third executable path is unimplemented; frozen claim retained without confirmation evidence")
        if not errors:
            if claim.get("status") == "UNIMPLEMENTED":
                status = "UNRUN"
            else:
                p = root / claim["result_path"]
                if not p.exists():
                    status = "MISSING"
                else:
                    v = json.loads(p.read_text(encoding="utf-8"))
                    if (v.get("card") != claim["result_card"] or v.get("claim_id") != claim["claim_id"]
                            or v.get("reader") != claim["reader"] or v.get("exec") != "COMPLETE"):
                        errors.append("result identity does not match frozen claim")
                    else:
                        try:
                            # The frozen discovery and the actual confirmation both
                            # belong to this reader/estimand; no later verdict substitution.
                            for name, field in (("verdict.json", "source_sha256"),
                                                ("metrics.json", "source_metrics_sha256"),
                                                ("cases.jsonl", "source_cases_sha256")):
                                rel = f"{claim['card']}/{name}"
                                hashes[rel] = file_hash(root / rel)
                                if hashes[rel] != claim[field]:
                                    raise ValueError("frozen discovery evidence changed")
                            cvp = root / claim["confirmation_source_path"]
                            for name in ("verdict.json", "metrics.json", "cases.jsonl"):
                                rel = f"{claim['card']}/confirmation/{name}"
                                hashes[rel] = file_hash(root / rel)
                                if (v.get("confirmation_hashes") or {}).get(name) != hashes[rel]:
                                    raise ValueError("confirmation evidence changed or unreceipted")
                            cv = json.loads(cvp.read_text(encoding="utf-8"))
                            cm = json.loads(cvp.with_name("metrics.json").read_text(encoding="utf-8"))
                            measured = (cm.get(claim["slice"]) or {}).get(claim["reader"]) or {}
                            if (cv.get("card") != claim["card"] or cv.get("cell_id") != f"{claim['card']}/confirmation"
                                    or cv.get("exec") != "COMPLETE" or cv.get("lane") != "confirmation"
                                    or cm.get("card") != claim["card"] or cm.get("lane") != "confirmation"):
                                raise ValueError("confirmation source card/cell/lane mismatch")
                            failed_measurement = (v.get("outcome") == "INSTRUMENT_FAILED"
                                                  and v.get("confirmation_compatible") is False)
                            if not failed_measurement and (cv.get("diagnosis_only")
                                    or measured.get("outcome") != v.get("outcome")
                                    or any(measured.get(k) != val for k, val in claim["estimand"].items())):
                                raise ValueError("confirmation source does not match frozen estimand and result")
                            if not failed_measurement and measured_identity(root, f"{claim['card']}/confirmation", claim["reader"], claim["estimand"]["arm"]) != claim["admission_identity"]:
                                raise ValueError("confirmation measured identity differs from admission")
                            status, outcome = "RESOLVED", v.get("outcome")
                        except (OSError, ValueError, KeyError, TypeError) as exc:
                            errors.append(str(exc))
        out[claim.get("claim_id") or f"unmapped:{i}"] = {"card": claim.get("card"), "reader": claim.get("reader"),
                    "result_path": claim.get("result_path"), "status": status, "outcome": outcome,
                    "evidence_hashes": hashes,
                    "reasons": errors or ([claim["reason"]] if status == "UNRUN" else [])}
    return out
