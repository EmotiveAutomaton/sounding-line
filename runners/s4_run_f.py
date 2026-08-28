"""Stage 4 confirmation card F01 (brief §7 F01, §8.1): fresh confirmation of at most
two findings under frozen definitions, on lineages reserved before discovery and never
inspected.

DESIGN CHECK (2026-08-27)
lessons read: LESSONS §3 (power before verdicts: the precision of the reserved sample is
  computed from the discovery spread before the reserve is opened; frozen is frozen;
  "gate met" only under the card's own terms; the reserve is a confirmation set only
  when its lineages were never inspected or fit on), CONTROLS §6.
gates and bands:
  - eligibility, in code, from each discovery verdict and its cases: (1) outcome
    SUPPORT_CANDIDATE with no failed required control (the runners fold control
    failures into the outcome); (2) point at or above the frozen threshold in the
    predicted direction, interval reported; (3) direction not carried by one domain:
    the per-domain primary contrasts agree in sign where a paired contrast is defined;
    (4) the information-matched cheap alternative is insufficient (the card's control
    arm) or the finding is an explicit boundary; (5) the reserved sample's expected
    half-width (1.96 x discovery unit SD / sqrt(n)) is at or below the threshold.
    Candidates order by the theory bridge (BRIDGE_ORDER); at most two enter. A useful
    boundary result (VALID_NULL with instruments intact) may take the second slot.
  - the confirmation estimate is the frozen contrast on the fresh split with the interval
    at alpha 0.05 divided by the number of confirmed claims (Bonferroni); NULL: the
    corrected interval covers 0; ALTERNATIVE: it excludes 0 with the point at or above
    the threshold; bands via classify_outcome. A model-specific calibration that fails on
    the fresh split is reported as such, never as a two-model replication.
  - no eligible discovery: record 'no confirmation justified'; the allowance goes to the
    predeclared expansion ladder, never to a search of the reserve.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from runners import s4_cards, s4_lib                                              # noqa: E402
from runners.s4_run_common import select_rows                                     # noqa: E402
from soundingline.s4 import (S4, ClaimLedger, Lineages, RunContract,               # noqa: E402
                             classify_outcome, completion_marker, now_iso, read_json,
                             read_jsonl, write_json)

PY = str(REPO / ".venv" / "Scripts" / "python.exe")
RUNNER_OF = {"C": "s4_run_c.py", "A": "s4_run_a.py", "T": "s4_run_t.py", "H": "s4_run_h.py",
             "P": "s4_run_p.py"}

# how to recompute each card's primary from its rows: (filter_a, filter_b, value) with
# None meaning the primary is a level or lives outside a paired row contrast
PRIMARY_DEF = {
    "C01": ({"question": "choice", "condition": "bundle"}, {"question": "choice", "condition": "facts"}, "primary_score"),
    "C02": ({"prior": "misleading", "records": 6, "route": "direct"}, {"prior": "misleading", "records": 0, "route": "direct"}, "primary_score"),
    "C03": ({"treatment": "select"}, None, "primary_score"),
    "A01": ({"source": "ruler"}, None, "a01_pair"),                 # special-cased below
    "A02": ({"intervention": "pos", "dose": "high", "evidence": "high"}, None, "extra.aligned_benefit"),
    "A03": ({"phase": "context"}, {"phase": "answer"}, "extra.aligned_benefit"),
    "T01": ({"outcome": "application", "support": "supported", "aligned": True}, {"outcome": "application", "support": "bare", "aligned": True}, "extra.correct"),
    "T02": ({"route": "reconstruct2"}, {"route": "summary2"}, "primary_score"),
    "T03": (None, None, None),
    "H01": (None, None, None),
    "H02": (None, None, None),
    "P01": (None, None, None), "H03": (None, None, None),
    "P02": ({"access": "unordered_strokes"}, None, "p02_contrast"),   # special-cased below
}


def _special_unit_values(card: str, rows) -> dict | None:
    """Per-unit values for the level estimands whose precision the eligibility rule must
    still compute (brief F01: H and P keep their natural unit and declare their precision).
    A01: per world, the mean correctness on the valuation and audience questions of the
    ruler source minus the 0.25 floor. P02: per drawing, the learned first-stroke hit minus
    the frozen geometry heuristic's hit (rows landed before the field existed fall back to
    the per-drawing best of the two heuristics, the severe form)."""
    if card == "A01":
        acc: dict = {}
        for r in rows:
            f = r["factors"]
            if f.get("source") == "ruler" and f.get("question") in ("valuation", "audience") and r.get("valid"):
                acc.setdefault(r["unit_id"], []).append(float(bool(r["extra"].get("correct"))))
        return {u: sum(v) / len(v) - 0.25 for u, v in acc.items()}
    if card == "P02":
        out = {}
        for r in rows:
            if r["factors"].get("access") == "unordered_strokes" and r.get("primary_score") is not None:
                h = r["extra"].get("best_heuristic_hit", r["extra"].get("heuristic_hit"))
                if h is not None:
                    out[r["unit_id"]] = float(r["primary_score"]) - float(h)
        return out
    return None


def _value(r: dict, key: str):
    if key == "primary_score":
        return r.get("primary_score")
    if key.startswith("extra."):
        v = r.get("extra", {}).get(key[6:])
        return float(v) if v is not None else None
    return None


def _unit_values(rows, fa, fb, key):
    """Per-unit contrast values (mean over readers within unit), recomputed from the
    rows exactly as the discovery runner computes its primary; the aligned-benefit
    estimands (A02, A03) are balanced over the appraisal-sign strata as there."""
    if fa is None:
        return {}
    if key in ("a01_pair", "p02_contrast"):
        return _special_unit_values("A01" if key == "a01_pair" else "P02", rows) or {}

    def pick(flt):
        if key == "primary_score":
            return select_rows(rows, **flt)
        return [r for r in rows if all(r["factors"].get(k, r.get(k)) == v for k, v in flt.items())]

    def per_unit(sub):
        acc: dict = {}
        for r in sub:
            v = _value(r, key)
            if v is not None:
                acc.setdefault(r["unit_id"], []).append(v)
        return {u: sum(v) / len(v) for u, v in acc.items()}

    va = per_unit(pick(fa))
    if fb is None:
        out = va
    else:
        vb = per_unit(pick(fb))
        out = {u: va[u] - vb[u] for u in va if u in vb}
    if key == "extra.aligned_benefit":
        strat = {}
        for r in rows:
            if "target_negative" in r["factors"]:
                strat[r["unit_id"]] = bool(r["factors"]["target_negative"])
            elif r.get("extra", {}).get("sign_val") is not None:
                strat[r["unit_id"]] = r["extra"]["sign_val"] < 0
        out = s4_lib.stratum_balanced(out, strat)
    return out


def _sd(values):
    if len(values) < 2:
        return None
    m = sum(values) / len(values)
    return (sum((v - m) ** 2 for v in values) / (len(values) - 1)) ** 0.5


def eligibility(card: str, verdict: dict, rows: list[dict], threshold: float, n_conf: int) -> dict:
    rep = {"card": card, "outcome": verdict.get("outcome"), "checks": {}}
    c = rep["checks"]
    c["1_support_with_controls"] = verdict.get("outcome") == "SUPPORT_CANDIDATE"
    c["2_point_at_threshold"] = (verdict.get("point") is not None and verdict["point"] >= threshold)
    fa, fb, key = PRIMARY_DEF.get(card, (None, None, None))
    per_dom = {}
    if fa is not None:
        for dom in s4_cards.CARDS[card]["domains"]:
            sub = [r for r in rows if r["factors"].get("domain") == dom]
            vals = _unit_values(sub, fa, fb, key)
            if vals:
                per_dom[dom] = sum(vals.values()) / len(vals)
        c["3_domains_agree"] = (len(per_dom) >= 2 and all(v > 0 for v in per_dom.values())) if per_dom else None
    else:
        c["3_domains_agree"] = "not_applicable_level_estimand"
    rep["per_domain_primary"] = per_dom
    c["4_cheap_alternative_insufficient"] = "carried by the card's own control arm; see metrics"
    vals = _unit_values(rows, fa, fb, key) if fa is not None else {}
    sd = _sd(list(vals.values())) if vals else None
    half = (1.96 * sd / (n_conf ** 0.5)) if sd is not None else None
    c["5_precision_ok"] = (half is not None and half <= threshold)
    rep["discovery_unit_sd"] = sd
    rep["expected_half_width"] = half
    rep["eligible"] = all(v is True for k, v in c.items() if k in ("1_support_with_controls", "2_point_at_threshold", "5_precision_ok")) \
        and c["3_domains_agree"] in (True, "not_applicable_level_estimand")
    rep["boundary_candidate"] = verdict.get("outcome") == "VALID_NULL"
    return rep


def arm_f01() -> int:
    t0 = time.time()
    out = s4_lib.card_dir("F01")
    contract = RunContract.load()
    design = contract.frozen("design") or {}
    L = Lineages()
    candidates = []
    for card in s4_cards.BRIDGE_ORDER:
        vp = S4 / card / "verdict.json"
        if not vp.exists() or card in design.get("deferred", []):
            continue
        v = read_json(vp)
        rows = read_jsonl(S4 / card / "cases.jsonl")
        thr = (design.get("thresholds") or {}).get(card) or s4_cards.CARDS[card]["threshold"] or 0.05
        n_conf = s4_cards.CONFIRMATION_UNITS.get(s4_cards.CARDS[card]["unit"], 128) * max(1, len(s4_cards.CARDS[card]["domains"]))
        rep = eligibility(card, v, rows, thr, n_conf)
        rep["threshold"] = thr
        rep["n_confirmation_units"] = n_conf
        candidates.append(rep)
    eligible = [c for c in candidates if c["eligible"]]
    selected = eligible[:2]
    if len(selected) < 2:
        boundary = [c for c in candidates if c["boundary_candidate"] and c["card"] not in {s["card"] for s in selected}]
        if boundary and len(selected) == 1:
            selected.append(boundary[0])
    write_json(out / "candidates.json", {"written_at": now_iso(), "candidates": candidates,
                                         "selected": [s["card"] for s in selected]})
    if not selected:
        write_json(out / "verdict.json", {"card": "F01", "exec": "COMPLETE", "outcome": "NOT_RUN",
                                          "reason": "no discovery met the frozen eligibility rule; no confirmation justified; "
                                                    "the allowance goes to the predeclared expansion ladder",
                                          "candidates": candidates,
                                          "marker": completion_marker({}, {}, contract)})
        print("F01: no confirmation justified")
        return 0
    # freeze the confirmation definitions before any fresh lineage is opened
    spec = {s["card"]: {"primary": s4_cards.CARDS[s["card"]]["primary"], "threshold": s["threshold"],
                        "n_units": s["n_confirmation_units"], "readers": design.get("readers"),
                        "parser": design.get("parser_version"), "readout": design.get("readout_version"),
                        "stopping_rule": "fixed n, no interim look", "alpha": 0.05 / len(selected)}
            for s in selected}
    contract.freeze("confirmations", spec)
    results = {}
    ledger = ClaimLedger()
    for s in selected:
        card = s["card"]
        dom_ids = []
        for dom in s4_cards.CARDS[card]["domains"]:
            dom_ids += [lid for lid, r in L.rows.items() if r["card"] == card and r["domain"] == dom and r["split"] == "confirmation"]
        try:
            L.open_confirmation(dom_ids, "F01")
        except Exception as e:                                                   # noqa: BLE001
            results[card] = {"outcome": "VOID", "reason": f"freshness violation: {e}"}
            continue
        env = dict(os.environ, S4_SPLIT="confirmation")
        cmd = [PY, str(REPO / "runners" / RUNNER_OF[card[0]]), "--card", card]
        rc = subprocess.call(cmd, env=env, cwd=str(REPO))
        cv = S4 / card / "confirmation" / "verdict.json"
        if rc != 0 or not cv.exists():
            results[card] = {"outcome": "VOID", "reason": f"confirmation run exited {rc}"}
            continue
        v = read_json(cv)
        rows = read_jsonl(S4 / card / "confirmation" / "cases.jsonl")
        fa, fb, key = PRIMARY_DEF[card]
        vals = _unit_values(rows, fa, fb, key) if fa is not None else {}
        alpha = 0.05 / len(selected)
        if vals:
            ci = s4_lib.cluster_bootstrap_ci(vals, 51000, alpha=alpha)
            oc, why = classify_outcome(ci["point"], ci["lo"], ci["hi"], s["threshold"])
        else:
            ci = {"point": v.get("point"), "lo": (v.get("ci") or [None, None])[0], "hi": (v.get("ci") or [None, None])[1], "n_units": v.get("n_units")}
            oc, why = (v.get("outcome"), "runner classification at uncorrected alpha (level estimand)")
        results[card] = {"outcome": oc, "reason": why, "corrected_alpha": alpha, "estimate": ci,
                         "runner_verdict": {k: v.get(k) for k in ("outcome", "point", "ci", "n_units", "reason")},
                         "controls_in_confirmation": s4_cards.CARDS[card]["controls"]}
        ledger.add(card, s4_cards.CARDS[card]["primary"], oc,
                   strongest_rival=", ".join(s4_cards.CARDS[card]["controls"]) or "none named",
                   scope="model readers on fictional constructed worlds; not a human mechanism",
                   pursuit="PROMOTE" if oc == "SUPPORT_CANDIDATE" else "STALLED",
                   warrant="CONFIRMED_MODEL_BOUNDED" if oc == "SUPPORT_CANDIDATE" else "BOUNDED_MODEL_EFFECT",
                   public_wording=f"{card}: {oc} on fresh lineages (corrected alpha {alpha:.3f})",
                   detail={"estimate": ci})
    write_json(out / "verdict.json", {"card": "F01", "exec": "COMPLETE",
                                      "outcome": "SUPPORT_CANDIDATE" if any(r.get("outcome") == "SUPPORT_CANDIDATE" for r in results.values()) else "VALID_NULL",
                                      "selected": [s["card"] for s in selected], "results": results,
                                      "minutes": round((time.time() - t0) / 60, 2),
                                      "marker": completion_marker({"candidates": str(out / "candidates.json")}, {}, contract)})
    print(f"F01: {json.dumps({k: v.get('outcome') for k, v in results.items()})}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--card", default="F01")
    ap.parse_args()
    return arm_f01()


if __name__ == "__main__":
    sys.exit(main())
