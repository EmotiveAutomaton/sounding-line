"""Prospective scoring (brief §8, §16.1): one PredictionV1 against one OracleBundleV1.
Held-out proper log score at the independent unit is the primary (the exact next
feasible action); Brier, correctness, the mass placed on subjectively unavailable
options, the type and section marginals, the changed-context choice, the invalidation
response, the boundary type, the discrete-time stop hazard, and class coverage ride
along. Nothing here reads a world object: the bundle carries the truths.

DESIGN CHECK (2026-09-02)
lessons read: LESSONS §3 (every statistic a verdict rests on is written to the row; the
  primary is the paired log-score difference on the estimand's own per-unit quantity,
  never raw correctness; blind floors follow the truth marginal, so U's score is written
  beside every arm's), §5 (aggregation clusters at the world).
gates: none here; the engines own the bands. bands: none.
"""

from __future__ import annotations

import math

FLOOR = 1e-9


def _ls(dist: dict | None, truth) -> float | None:
    if not dist or truth is None:
        return None
    return math.log(max(float(dist.get(truth, 0.0)), FLOOR))


def _brier(dist: dict, truth) -> float:
    keys = set(dist) | {truth}
    return sum((float(dist.get(k, 0.0)) - (1.0 if k == truth else 0.0)) ** 2 for k in keys)


def score(pred: dict, bundle: dict) -> dict:
    """Every endpoint of one prediction against the bundle's hidden targets."""
    h = bundle["hidden"]
    t = pred["targets"]
    out: dict = {}
    na = t.get("next_action") or {}
    has_next = h.get("next_action") is not None
    out["next_action_ls"] = _ls(na, h["next_action"]) if has_next else None
    out["next_action_brier"] = _brier(na, h["next_action"]) if (na and has_next) else None
    out["next_action_correct"] = (max(na, key=na.get) == h["next_action"]) if (na and has_next) else None
    out["mass_on_unavailable"] = sum(float(na.get(k, 0.0)) for k in h.get("unavailable_ids", [])) if na else None
    out["next_type_ls"] = _ls(t.get("next_type"), h["next_type"])
    out["next_section_ls"] = _ls(t.get("next_section"), h["next_section"])
    p_stop = t.get("stop")
    if isinstance(p_stop, (int, float)):
        p = min(max(float(p_stop), FLOOR), 1 - FLOOR)
        out["stop_ls"] = math.log(p) if h["stop_next"] else math.log(1 - p)
        out["stop_brier"] = (p - (1.0 if h["stop_next"] else 0.0)) ** 2
        out["stop_conf"] = p
    else:
        out["stop_ls"] = out["stop_brier"] = out["stop_conf"] = None
    out["stop_truth"] = bool(h.get("stop_next"))
    # the cut design oversamples terminal boundaries; this weight (q(c)/Q_TERMINAL on stop
    # rows, 1 elsewhere) restores the natural-boundary expectation in every stop contrast
    out["stop_weight"] = float(h.get("stop_weight", 1.0) or 1.0)
    cc = h.get("changed_context") or {}
    out["changed_context_ls"] = _ls(t.get("changed_context"), cc.get("choice")) if cc else None
    inv = h.get("invalidation") or {}
    out["invalidation_ls"] = _ls(t.get("invalidation"), inv.get("choice")) if inv else None
    if h.get("stop_next") and h.get("boundary_type") not in (None, "none"):
        out["boundary_type_ls"] = _ls(t.get("boundary_type"), h["boundary_type"])
    else:
        out["boundary_type_ls"] = None
    truth_class_size = len(h.get("equivalence_class") or [])
    out["truth_class_size"] = truth_class_size
    out["abstained"] = bool(pred.get("abstain"))
    out["class_coverage_correct"] = (out["abstained"] == (truth_class_size > 1))
    out["confidence"] = float(pred.get("confidence", 0.5))
    out["primary"] = out["next_action_ls"]
    out["combined"] = (out["next_action_ls"] + out["stop_ls"]) if (out["next_action_ls"] is not None and out["stop_ls"] is not None) else None
    return out


def oracle_scores(bundle: dict) -> dict:
    """The exact oracle's own scores on the same targets (the ceiling)."""
    o = bundle["oracle"]
    h = bundle["hidden"]
    fake = {"targets": {"next_action": o["next_action"], "next_type": o["next_type"], "next_section": o["next_section"],
                        "stop": o["p_stop"], "changed_context": (h.get("changed_context") or {}).get("dist"),
                        "invalidation": (h.get("invalidation") or {}).get("dist"),
                        "boundary_type": {o["boundary_type"]: 1.0} if o.get("boundary_type") else None},
            "abstain": len(h.get("equivalence_class") or []) > 1, "confidence": max(o["next_action"].values()) if o["next_action"] else 0.0}
    return score(fake, bundle)


def tail_scores(pred_tail: list[dict], bundle: dict) -> dict:
    """P09: the whole withheld tail: per-event log scores summed over the events the
    prediction covers (a sequence of next-action distributions), with the localization
    audit (which positions carry the gain)."""
    tail = bundle["hidden"].get("tail") or []
    per = []
    for i, (d, ev) in enumerate(zip(pred_tail, tail)):
        truth = f"{ev['type']}:{ev['section']}:{ev['slot']}"
        per.append({"i": i, "ls": _ls(d, truth)})
    return {"n_events": len(per), "sum_ls": sum(x["ls"] for x in per if x["ls"] is not None), "per_event": per}
