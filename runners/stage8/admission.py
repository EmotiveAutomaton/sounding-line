"""Read-only Stage 8 admission: prediction AND generation for the same reader lineage.

DESIGN CHECK (2026-09-06)
lessons read: LESSONS sections 3 and 5 (a verdict, not a file, licenses a claim).
gates: Under the NULL, absent, failed, or mismatched evidence cannot admit a reader;
failure direction is DOWN. Under the ALTERNATIVE, both gates pass with one complete
matching identity. Bands are exhaustive: ADMITTED, NOT_ADMITTED, PENDING.
Historical registries are never rewritten by this consumer.
"""
from __future__ import annotations

import json
from pathlib import Path

IDENTITY_FIELDS = ("reader", "model_revision", "adapter_sha", "construction", "scoring", "contract", "capsule_sources")


def gate_identity(rows: list[dict], reader: str, arm: str) -> dict:
    """Identity from the rows actually measured, never today's adapter configuration.

    Legacy row code_hash covers construction and scoring together; retaining that
    conservative closure can refuse a match but cannot invent compatibility.
    """
    identities = []
    for row in rows:
        if row.get("model_id") != reader or row.get("arm") != arm or not row.get("valid"):
            continue
        notes = (row.get("extra") or {}).get("notes") or {}
        stamp = notes.get("generated", {}) if arm == "GEN" else notes
        identities.append({"reader": reader, "model_revision": stamp.get("revision"),
                           "adapter_sha": stamp.get("adapter_sha"),
                           "construction": row.get("code_hash"), "scoring": row.get("code_hash"),
                           "contract": row.get("contract_hash"),
                           "capsule_sources": (row.get("extra") or {}).get("capsule_source_sha256")})
    if not identities or any(not x.get(k) for x in identities for k in IDENTITY_FIELDS):
        return {"error": "missing identity in measured rows"}
    if any(x != identities[0] for x in identities[1:]):
        return {"error": "mixed identities in measured rows"}
    return identities[0]


def eligibility(prediction: dict, generation: dict, gates: dict | None = None) -> dict:
    """Pure per-reader decisions; `passed` is a compatibility alias for admission only."""
    predictions = prediction.get("readers") or {}
    generations = (generation.get("fm") or {}).get("readers") or {}
    summary = (gates or {}).get("generation") or {}
    flags = (summary.get("detail") or {}).get("readers") or {}
    result = {}
    for reader in sorted(set(predictions) | set(generations) | set(flags)):
        pred, gen = predictions.get(reader) or {}, generations.get(reader) or {}
        # Old `passed` was sometimes overwritten by E04. A recorded failure still
        # refuses admission; new E03 writes an unambiguous prediction_passed field.
        p = pred.get("prediction_passed", pred.get("passed"))
        g = gen.get("generation_passed", gen.get("passed", flags.get(reader)))
        reasons = []
        if p is False:
            reasons.append("prediction failed")
        if g is False or summary.get("passed") is False:
            reasons.append("generation failed")
        failed = bool(reasons)
        if type(p) is not bool:
            reasons.append("prediction evidence missing or invalid")
        if type(g) is not bool:
            reasons.append("per-reader generation evidence missing or invalid")
        pi, gi = pred.get("identity") or {}, gen.get("identity") or {}
        if not all(pi.get(k) and gi.get(k) for k in IDENTITY_FIELDS):
            reasons.append("model/adapter/construction/scoring/copied-source identity incomplete")
        elif pi != gi or pi["reader"] != reader:
            reasons.append("prediction and generation identities differ")
        if reader in flags and flags[reader] != g:
            reasons.append("generation registry and gate summary disagree")
        state = "NOT_ADMITTED" if failed else ("PENDING" if reasons else "ADMITTED")
        result[reader] = {**pred, "prediction_passed": p, "generation_passed": g,
                          "admission": state, "admitted": state == "ADMITTED",
                          "passed": state == "ADMITTED", "reasons": reasons,
                          "prediction_identity": pi, "generation_identity": gi}
    return result


def admitted_readers(root: Path | None = None) -> dict:
    if root is None:
        from soundingline.stage8 import S8
        root = S8
    def read(name):
        path = Path(root) / f"{name}.json"
        value = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        if not isinstance(value, dict):
            raise ValueError(f"{name}: expected object")
        return value
    return eligibility(read("EXPERTISE_GATE"), read("GENERATION_GATE"), read("GATES"))
