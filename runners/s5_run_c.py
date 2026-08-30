"""Stage 5 confirmation and closure cards (brief §6 C01-C02, §7.4): at most two frozen
candidates, chosen by the brief's order from the cards that passed their gates, re-run
on untouched confirmation lineages under the frozen estimand at a corrected alpha.

DESIGN CHECK (2026-08-29)
lessons read: LESSONS §3 (gate met only under the card's own terms; a reserve opened
  after inspection is not confirmation; the analysis by side; power before verdicts,
  so the precision rule uses the discovery unit spread), §5 (the gate dependency is the
  verdict, not the file).
gates and bands:
  - eligibility (§7.4): a candidate must be SUPPORT_CANDIDATE with its controls quiet,
    have its point at or above its threshold, agree in sign across its domains, and
    have a discovery unit spread giving an expected confirmation half-width at or under
    the threshold; C01 takes the first eligible bridge in the brief's order, C02 the
    next eligible card or, failing that, the strongest boundary (a VALID_NULL with a
    prospective endpoint); at most two.
  - confirmation: the frozen contrast on the fresh lane at alpha 0.05 divided by the
    number of confirmations; NULL: the interval includes zero; ALTERNATIVE: the
    SUPPORT_CANDIDATE band at the corrected alpha; no substituted endpoint; a freshness
    violation voids the confirmation rather than repairing it.
  under the null the confirmation estimate on untouched lineages sits at zero and the
  interval at the corrected alpha includes it; under the alternative the point reaches
  the frozen threshold with the interval excluding zero; the failure direction guarded
  is regression to the null from a discovery estimate selected on its own extreme, which
  is why the estimand, the threshold, and the unit count are frozen before the run and
  no candidate is opened after inspection.
verdict bands per card, exhaustive (no silent interval), from the shared classifier on
  the primary's point and its cluster-bootstrap interval against the frozen threshold:
  COUNTEREVIDENCE when the whole interval sits below zero; SUPPORT_CANDIDATE when the
  interval excludes zero and the point reaches the threshold; INCONCLUSIVE when the
  interval excludes zero but the point falls short, or includes zero without excluding
  the threshold; VALID_NULL when the interval includes zero and excludes the threshold;
  every real interval lands in exactly one. Before any interval exists the cell carries
  VOID (no units, or every reader excluded by the gate), INSTRUMENT_FAILED (a validity
  or manipulation gate failed, named in the reason), or NOT_RUN (a dependency died);
  those three are states of the instrument, never evidence about the hypothesis.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from runners import s5_cards, s5_lib                                              # noqa: E402
from runners.s5_run_common import cluster_by_construction, select_rows            # noqa: E402
from soundingline.stage5 import (S5, ClaimLedger5, Lineages5, RunContract5,        # noqa: E402
                                 classify_outcome, completion_marker, now_iso, read_json,
                                 read_jsonl, write_json, write_registry)

PY = str(REPO / ".venv" / "Scripts" / "python.exe")
RUNNER_OF = {"B": "s5_run_b.py", "J": "s5_run_j.py", "A": "s5_run_a.py", "R": "s5_run_r.py",
             "P": "s5_run_p.py", "F": "s5_run_f.py"}


def unit_values(card: str, rows: list[dict], verdict: dict) -> dict:
    """Per-unit values of each card's frozen primary, recomputed from its rows the way
    the discovery runner computed them (clustered on the construction)."""
    rows = [r for r in rows if r.get("valid") and r.get("primary_score") is not None]
    rows = cluster_by_construction(rows)

    def pu(sub):
        return s5_lib.per_unit_means(sub, "unit_id", "primary_score")

    def diff(a, b):
        va, vb = pu(a), pu(b)
        return {u: va[u] - vb[u] for u in va if u in vb}
    if card in ("B01", "B02"):
        ck = {"B01": "qwen3b", "B02": "anchor"}[card]
        return diff(select_rows(rows, checkpoint=ck, steer="congruent"), select_rows(rows, checkpoint=ck, steer="zero"))
    if card == "J02":
        best = verdict.get("best_comparator") or "factored"
        return diff(select_rows(rows, reader="recurrent"), select_rows(rows, reader=best))
    if card == "J05":
        best = verdict.get("best_baseline") or "habit"
        return diff(select_rows(rows, predictor="inferred_preference"), select_rows(rows, predictor=best))
    if card == "A02":
        return pu(select_rows(rows, behavior="selection", twin="original"))
    if card == "A03":
        a = pu(select_rows(rows, maker="audience_modeling", reader_model="audience"))
        o = pu(select_rows(rows, maker="audience_modeling", reader_model="ordinary"))
        pa = pu(select_rows(rows, maker="plain", reader_model="audience"))
        po = pu(select_rows(rows, maker="plain", reader_model="ordinary"))
        plain_gain = (sum(pa[u] - po[u] for u in pa if u in po) / max(1, len([u for u in pa if u in po]))) if pa else 0.0
        return {u: (a[u] - o[u]) - plain_gain for u in a if u in o}
    if card == "R02":
        hi = pu(select_rows(rows, information="high", ease="plain"))
        lo = pu(select_rows(rows, information="low", ease="plain"))
        st = pu(select_rows(rows, ease="stilted", information="high"))
        return {u: (hi[u] - lo[u]) - (hi[u] - st[u]) for u in hi if u in lo and u in st}
    if card == "P01":
        best = verdict.get("best_access_level") or "true_prefix"
        return pu(select_rows(rows, access=best))
    if card == "P02":
        return pu(rows)
    if card == "F02":
        best = verdict.get("best_raw_baseline") or "random"
        return diff(select_rows(rows, policy="model"), select_rows(rows, policy=best))
    return {}


def _sd(values):
    if len(values) < 2:
        return None
    m = sum(values) / len(values)
    return (sum((v - m) ** 2 for v in values) / (len(values) - 1)) ** 0.5


def eligibility(card: str, verdict: dict, rows: list[dict], threshold: float, n_conf: int) -> dict:
    vals = unit_values(card, rows, verdict)
    per_dom = {}
    for dom in (s5_cards.CARDS[card]["domains"] or ["all"]):
        sub = unit_values(card, [r for r in rows if r["factors"].get("domain") == dom], verdict)
        if sub:
            per_dom[dom] = sum(sub.values()) / len(sub)
    sd = _sd(list(vals.values())) if vals else None
    half = (1.96 * sd / (n_conf ** 0.5)) if sd is not None else None
    checks = {"1_support_with_controls": verdict.get("outcome") == "SUPPORT_CANDIDATE" and not verdict.get("decode_void"),
              "2_point_at_threshold": verdict.get("point") is not None and threshold is not None and verdict["point"] >= threshold,
              "3_domains_agree": (all(v > 0 for v in per_dom.values()) if len(per_dom) >= 2 else "single_domain"),
              "4_precision_ok": half is not None and threshold is not None and half <= threshold}
    return {"card": card, "outcome": verdict.get("outcome"), "checks": checks, "per_domain": per_dom, "unit_sd": sd,
            "expected_half_width": half, "n_confirmation_units": n_conf, "threshold": threshold,
            "eligible": checks["1_support_with_controls"] and checks["2_point_at_threshold"] and checks["4_precision_ok"] and checks["3_domains_agree"] in (True, "single_domain"),
            "boundary_candidate": verdict.get("outcome") == "VALID_NULL" and card in ("R02", "P01", "P02", "F02")}


def select_candidates() -> list[dict]:
    contract = RunContract5.load()
    design = contract.frozen("design") or {}
    cands = []
    for card in s5_cards.BRIDGE_ORDER:
        cdir = S5 / card
        # a repaired cell (card/v2) supersedes the withdrawn readout's verdict
        for sub in sorted(cdir.glob("v*/verdict.json"), reverse=True) if cdir.exists() else []:
            cdir = sub.parent
            break
        vp = cdir / "verdict.json"
        if not vp.exists():
            continue
        v = read_json(vp)
        rows = read_jsonl(cdir / "cases.jsonl")
        thr = (design.get("thresholds") or {}).get(card) or s5_cards.CARDS[card]["threshold"]
        unit = s5_cards.CARDS[card]["unit"]
        n_conf = s5_cards.CONFIRMATION_UNITS.get(unit, 128) * max(1, len(s5_cards.CARDS[card]["domains"]))
        cands.append(eligibility(card, v, rows, thr, n_conf))
    return cands


def run_confirmation(cell: str) -> int:
    """C01 = the first eligible candidate in the brief's order; C02 = the next eligible,
    else the strongest boundary. Both freeze their definitions before opening a lane."""
    t0 = time.time()
    out = s5_lib.card_dir(cell)
    contract = RunContract5.load()
    design = contract.frozen("design") or {}
    L = Lineages5()
    cands = select_candidates()
    reg = read_json(S5 / "CONFIRMATION_REGISTRY.json") if (S5 / "CONFIRMATION_REGISTRY.json").exists() else {"selected": {}, "candidates": []}
    taken = set(reg["selected"].values())
    eligible = [c for c in cands if c["eligible"] and c["card"] not in taken]
    pick = eligible[0] if eligible else None
    if pick is None and cell == "C02":
        bnd = [c for c in cands if c["boundary_candidate"] and c["card"] not in taken]
        pick = bnd[0] if bnd else None
    reg["candidates"] = cands
    reg["selected"][cell] = pick["card"] if pick else None
    reg["written_at"] = now_iso()
    write_registry("CONFIRMATION_REGISTRY", reg)
    if pick is None:
        write_json(out / "verdict.json", {"card": cell, "exec": "COMPLETE", "outcome": "NOT_RUN",
                                          "reason": "no discovery met the frozen eligibility rule; no confirmation justified",
                                          "candidates": cands, "marker": completion_marker({}, {}, contract)})
        print(f"{cell}: no confirmation justified")
        return 0
    card = pick["card"]
    n_sel = len([v for v in reg["selected"].values() if v])
    alpha = 0.05 / max(1, n_sel)
    spec = {card: {"primary": s5_cards.CARDS[card]["primary"], "threshold": pick["threshold"], "n_units": pick["n_confirmation_units"],
                   "readers": design.get("readers"), "readout": design.get("readout_version"), "stopping_rule": "fixed n, no interim look",
                   "alpha": alpha, "selected_by": cell}}
    contract.freeze(f"confirmation_{cell}", spec)
    ledger = ClaimLedger5()
    parent = s5_cards.DERIVED.get(card, card)
    lids = [lid for lid, r in L.rows.items() if r["card"] == card and r["split"] == "confirmation"]
    if not lids and parent != card:
        lids = [lid for lid, r in L.rows.items() if r["card"] == card and r["split"] == "confirmation"]
    result = {}
    try:
        roots = [lid for lid in lids if L.rows[lid].get("parent") is None] or [L.rows[lid]["parent"] for lid in lids]
        L.open_confirmation(sorted(set(roots)), cell)
    except Exception as e:                                                           # noqa: BLE001
        result = {"outcome": "VOID", "reason": f"freshness violation: {e}"}
    if not result:
        env = dict(os.environ, S5_SPLIT="confirmation")
        cmd = [PY, str(REPO / "runners" / RUNNER_OF[card[0]]), "--card", card]
        rc = subprocess.call(cmd, env=env, cwd=str(REPO))
        cv = S5 / card / "confirmation" / "verdict.json"
        if rc != 0 or not cv.exists():
            result = {"outcome": "VOID", "reason": f"confirmation run exited {rc}"}
        else:
            v = read_json(cv)
            rows = read_jsonl(S5 / card / "confirmation" / "cases.jsonl")
            vals = unit_values(card, rows, v)
            if vals:
                ci = s5_lib.cluster_bootstrap_ci(vals, 51000, alpha=alpha)
                oc, why = classify_outcome(ci["point"], ci["lo"], ci["hi"], pick["threshold"] or 0.03)
            else:
                ci = {"point": v.get("point"), "lo": (v.get("ci") or [None, None])[0], "hi": (v.get("ci") or [None, None])[1], "n_units": v.get("n_units")}
                oc, why = v.get("outcome", "VOID"), "runner classification (no per-unit recomputation available)"
            result = {"outcome": oc, "reason": why, "corrected_alpha": alpha, "estimate": ci,
                      "runner_verdict": {k: v.get(k) for k in ("outcome", "point", "ci", "n_units", "reason")},
                      "strongest_rival": v.get("strongest_surviving_rival")}
            ledger.add(card, s5_cards.CARDS[card]["primary"], oc, strongest_rival=v.get("strongest_surviving_rival") or "none named",
                       scope="model readers on controlled constructions; bounded model-reader claim only",
                       pursuit="PROMOTE" if oc == "SUPPORT_CANDIDATE" else "STALLED",
                       warrant="CONFIRMED_MODEL_BOUNDED" if oc == "SUPPORT_CANDIDATE" else "BOUNDED_MODEL_EFFECT",
                       public_wording=f"{card}: {oc} on fresh lineages (corrected alpha {alpha:.3f})", detail={"estimate": ci})
    write_json(out / "verdict.json", {"card": cell, "exec": "COMPLETE", "outcome": result.get("outcome", "VOID"),
                                      "confirmed_card": card, "result": result, "minutes": round((time.time() - t0) / 60, 2),
                                      "marker": completion_marker({}, {}, contract)})
    print(f"{cell}: {card} -> {result.get('outcome')}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--card", required=True, choices=["C01", "C02"])
    a = ap.parse_args()
    return run_confirmation(a.card)


if __name__ == "__main__":
    sys.exit(main())
