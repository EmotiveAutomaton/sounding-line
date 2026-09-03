"""Calibration and coverage (brief §8, §16.1, P10): reliability bins, expected
calibration error, calibration slope and intercept, Brier decomposition, selective
risk-coverage by confidence, and class coverage for equivalence cases, all from landed
rows at the independent unit.

DESIGN CHECK (2026-09-02)
lessons read: LESSONS §3 (a verdict band on a small-probe gate needs its sampling width
  derived; reliability is reported per reader and per evidence dose before pooling;
  a mean cannot exceed both its parts: pooled numbers are checked against their parts).
gates: none here. bands: none.
"""

from __future__ import annotations

import math


def reliability(rows: list[dict], conf_key: str = "confidence", correct_key: str = "next_action_correct", bins: int = 5) -> dict:
    pts = [(float(r["scores"][conf_key]), 1.0 if r["scores"].get(correct_key) else 0.0)
           for r in rows if r.get("scores", {}).get(conf_key) is not None and r["scores"].get(correct_key) is not None]
    if not pts:
        return {"n": 0, "ece": None, "bins": []}
    out_bins = []
    ece = 0.0
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        sel = [(c, y) for c, y in pts if lo <= c < hi or (b == bins - 1 and c == 1.0)]
        if not sel:
            out_bins.append({"lo": lo, "hi": hi, "n": 0})
            continue
        mc = sum(c for c, _ in sel) / len(sel)
        acc = sum(y for _, y in sel) / len(sel)
        ece += len(sel) / len(pts) * abs(mc - acc)
        out_bins.append({"lo": lo, "hi": hi, "n": len(sel), "mean_conf": round(mc, 4), "accuracy": round(acc, 4)})
    xs = [c for c, _ in pts]
    ys = [y for _, y in pts]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    vx = sum((x - mx) ** 2 for x in xs)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / vx if vx > 0 else None
    intercept = (my - slope * mx) if slope is not None else None
    brier = sum((c - y) ** 2 for c, y in pts) / len(pts)
    return {"n": len(pts), "ece": round(ece, 4), "slope": None if slope is None else round(slope, 4),
            "intercept": None if intercept is None else round(intercept, 4), "brier_conf": round(brier, 4), "bins": out_bins}


def risk_coverage(rows: list[dict], conf_key: str = "confidence", loss_key: str = "next_action_ls", steps: int = 10) -> list[dict]:
    """Selective risk: mean negative log score over the units whose confidence is at or
    above each coverage threshold."""
    pts = sorted(((float(r["scores"][conf_key]), -float(r["scores"][loss_key])) for r in rows
                  if r.get("scores", {}).get(conf_key) is not None and r["scores"].get(loss_key) is not None),
                 key=lambda t: -t[0])
    out = []
    n = len(pts)
    for k in range(1, steps + 1):
        m = max(1, int(round(n * k / steps)))
        sel = pts[:m]
        out.append({"coverage": round(m / max(1, n), 3), "risk": round(sum(l for _, l in sel) / len(sel), 4) if sel else None})
    return out


def class_coverage(rows: list[dict]) -> dict:
    """Equivalence cases: the fraction of units whose abstention matched whether the truth
    class was a singleton, split by class size."""
    eq = [r for r in rows if r.get("scores", {}).get("truth_class_size", 0) > 1]
    single = [r for r in rows if r.get("scores", {}).get("truth_class_size", 0) == 1]
    def rate(rs):
        return round(sum(1 for r in rs if r["scores"].get("class_coverage_correct")) / len(rs), 4) if rs else None
    return {"n_equivalence": len(eq), "abstain_rate_on_equivalence": round(sum(1 for r in eq if r["scores"].get("abstained")) / len(eq), 4) if eq else None,
            "n_singleton": len(single), "false_abstain_rate": round(sum(1 for r in single if r["scores"].get("abstained")) / len(single), 4) if single else None,
            "coverage_correct_equivalence": rate(eq), "coverage_correct_singleton": rate(single)}


def by_dose(rows: list[dict], dose_key: str = "prefix_len") -> dict:
    """Calibration by evidence dose (prefix length tercile)."""
    vals = sorted(float(r.get("factors", {}).get(dose_key, 0)) for r in rows)
    if not vals:
        return {}
    t1, t2 = vals[len(vals) // 3], vals[2 * len(vals) // 3]
    out = {}
    for name, sel in (("low", [r for r in rows if float(r.get("factors", {}).get(dose_key, 0)) <= t1]),
                      ("mid", [r for r in rows if t1 < float(r.get("factors", {}).get(dose_key, 0)) <= t2]),
                      ("high", [r for r in rows if float(r.get("factors", {}).get(dose_key, 0)) > t2])):
        out[name] = {k: v for k, v in reliability(sel).items() if k != "bins"}
    return out


def entropy(dist: dict) -> float:
    return -sum(float(p) * math.log(max(float(p), 1e-12)) for p in dist.values())
