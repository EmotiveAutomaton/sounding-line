"""Stage 7 immutable contracts (brief §6.1, §14): the minimal module a reader capsule
receives. STDLIB ONLY, NO REPOSITORY IMPORTS: this file is copied into every capsule, so
anything it imported would ride along. It knows the three artifact schemas by name, how to
canonicalize a prediction, how to hash evidence, and nothing about worlds, oracles, or
scores. The scorer-side copy of the same rules lives in soundingline/stage7.py and the
guard suite asserts the two agree on fixtures (test 4, test 6).

DESIGN CHECK (2026-09-02)
lessons read: LESSONS §3 (a filename two code paths share is built by ONE helper: the
  canonical serialization here and in soundingline/stage7.py are asserted equal on
  fixtures rather than trusted), §5 (no gate here; a contract module carries none).
gates: none here (the validators return problem lists; the engines turn them into
  verdicts with the null, alternative, and direction stated there). bands: none.
"""

from __future__ import annotations

import hashlib
import json

EVIDENCE_VERSION = "VisibleEvidenceV1"
PREDICTION_VERSION = "PredictionV1"
EVIDENCE_FIELDS = ("version", "unit_ref", "condition_ref", "domain", "brief", "artifact_state",
                   "process_prefix", "objective_options", "demonstrations", "supplied_factors",
                   "candidate_laws", "query", "history", "regime", "render")


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def evidence_sha(ev: dict) -> str:
    return hashlib.sha256(canonical(ev).encode("utf-8")).hexdigest()[:16]


def _round(obj, nd: int = 6):
    if isinstance(obj, float):
        return round(obj, nd)
    if isinstance(obj, dict):
        return {k: _round(v, nd) for k, v in sorted(obj.items())}
    if isinstance(obj, (list, tuple)):
        return [_round(v, nd) for v in obj]
    return obj


def canonical_prediction(pred: dict) -> bytes:
    core = {k: v for k, v in pred.items() if k not in ("compute", "at", "wall_s")}
    return json.dumps(_round(core), sort_keys=True, separators=(",", ":")).encode("utf-8")


def normalize(dist: dict, floor: float = 0.0) -> dict:
    d = {k: max(float(v), floor) for k, v in dist.items()}
    z = sum(d.values())
    if z <= 0:
        n = len(d) or 1
        return {k: 1.0 / n for k in d}
    return {k: v / z for k, v in d.items()}


def prediction(evidence: dict, targets: dict, equivalence_class: list | None = None,
               abstain: bool = False, confidence: float = 0.5, arm: str = "", notes: dict | None = None,
               compute: dict | None = None) -> dict:
    """Build one PredictionV1: every distribution normalized here, hazards clipped."""
    out_t = {}
    for name, dist in targets.items():
        if isinstance(dist, dict):
            out_t[name] = normalize(dist)
        else:
            out_t[name] = min(max(float(dist), 0.0), 1.0)
    return {"version": PREDICTION_VERSION, "evidence_sha": evidence_sha(evidence),
            "arm": arm, "targets": out_t, "equivalence_class": list(equivalence_class or []),
            "abstain": bool(abstain), "confidence": float(min(max(confidence, 0.0), 1.0)),
            "notes": dict(notes or {}), "compute": dict(compute or {})}


def evidence_problems(ev: dict) -> list[str]:
    """The capsule-side allowlist check (a reader refuses malformed evidence rather than
    guessing): only declared fields, JSON values only."""
    problems = []
    if not isinstance(ev, dict) or ev.get("version") != EVIDENCE_VERSION:
        return ["not a VisibleEvidenceV1 object"]
    for k in ev:
        if k not in EVIDENCE_FIELDS:
            problems.append(f"undeclared field {k}")
    try:
        json.dumps(ev)
    except (TypeError, ValueError) as e:
        problems.append(f"non-JSON content: {e}")
    return problems
