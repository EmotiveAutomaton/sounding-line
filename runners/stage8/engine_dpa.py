"""Stage 8 difference, purpose, and accumulation trunks (brief §7 D, G, A) and the frontier
cells (E07, D05, G08). Every prospective contrast is reported whole and tail; every
per-event card reports its surprise alignment per reader, family, shape, and N before any
pooling; the admitted readers come from the expertise gate's registry (a reader that failed
is not tested past E, except where the branching table names a diagnosis).

DESIGN CHECK (2026-09-04)
lessons read: LESSONS §3 (the primary is the paired difference on the estimand's own
  per-unit quantity: per-world AUROC differences, not pooled-event AUROCs alone; a
  falsifier's baseline arm is a known-answer gate: DOM's own AUROC sits beside every
  reader's; a one-number contrast over a heterogeneous set reports its matrix: shapes,
  N, reveal; a conditional first, pooled after; a paired contrast under the same option
  order), §4, §5.
gates and bands:
  - D01 (non-inferiority): NULL of a worse localizer is a per-world reader-minus-DOM AUROC
    difference with point under -0.02 (fails DOWN: the difference mechanism claim narrows
    to "with the purpose known" and D04 diagnoses); ALTERNATIVE: point at or above -0.02
    with the interval reported. Per reader and shape before pooling.
  - G01 (recall gate): NULL is recall under 0.5 (fails DOWN: the one repair on the proposal
    readout, then the selection cards read as bounded diagnosis); ALTERNATIVE: at or above.
  - G02, G03, A03, A05: the Stage 5 exhaustive bands, whole and tail, the floor a fifth of
    the relevant gap.
  - G04: NULL is coverage under a half on equivalence worlds or false abstention over a half
    (fails DOWN); ALTERNATIVE: both held.
  - A01: NULL is no monotone rise of alignment with N (the N3 minus N0 interval covering
    zero or below); ALTERNATIVE: the interval above zero with the per-N cells rising.
  - E07, D05, G08: the same bands as the local cells; a cap stop lands INSTRUMENT_FAILED.
  bands: exhaustive.
"""

from __future__ import annotations

import copy
import json
import math
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from runners import s5_lib                                                         # noqa: E402
from runners.stage7.constructor import oracle as ORC                               # noqa: E402
from runners.stage7.constructor import worlds as W                                 # noqa: E402
from runners.stage7.reader import baselines as B                                   # noqa: E402
from runners.stage7.reader import law as LAW                                       # noqa: E402
from runners.stage7.scoring import prospective as PS                               # noqa: E402
from runners.stage8 import cards as C                                              # noqa: E402
from runners.stage8 import engines as E                                            # noqa: E402
from runners.stage8 import frontier as FR                                          # noqa: E402
from runners.stage8.cardrun import SMOKE, CardRun8                                 # noqa: E402
from runners.stage8.constructor import gradient as G                               # noqa: E402
from runners.stage8.constructor import purpose as PU                               # noqa: E402
from runners.stage8.reader import logfmt as LF                                     # noqa: E402
from soundingline.stage5 import calibration_slope, ece                             # noqa: E402
from soundingline.stage8 import (S8, SHAPES, FrontierCap, evidence_sha, now_iso,     # noqa: E402
                                 read_json, read_registry, record_interrupt, set_gate,
                                 update_registry, write_registry)

SEED = 82000
NONINF = -0.02


def _ci(values: dict, seed: int = SEED) -> dict:
    if not values:
        return {"point": None, "lo": None, "hi": None, "n_units": 0}
    c = s5_lib.cluster_bootstrap_ci(values, seed)
    c["n_units"] = len(values)
    return c


def _n(run: CardRun8) -> int:
    return E.n_units(run.card)


def _readers(run: CardRun8, diagnosis: bool = False) -> list[str]:
    """The admitted readers; when none is admitted and the gate has been read, the trained
    readers run as DIAGNOSIS (his ruling 2026-09-04: every test runs; the brief's closure of
    the reader claims is kept by labeling every such verdict and barring it from confirmation)."""
    adm = E.admitted(run)
    if adm:
        return adm
    gate = read_registry("EXPERTISE_GATE") or {}
    if gate.get("readers"):
        run.diagnosis_only = True
        return E.reader_set(run)
    if diagnosis:
        return E.reader_set(run)
    return []


def _not_run(run: CardRun8, why: str) -> int:
    run.finish({"why": why}, {"exec": "COMPLETE", "outcome": "NOT_RUN", "primary": C.ALL[run.card]["primary"], "reason": why})
    return 0


# ── D: surprise localization ─────────────────────────────────────────────────────────

def _auroc_cells(run: CardRun8, rows: list[dict], arm: str, key_r: str = "auroc_reader", key_d: str = "auroc_dom", group=None) -> dict:
    """Per reader (and per group): the per-world paired AUROC difference with its cluster
    interval, the mean reader and DOM AUROCs, and the pooled-event AUROC beside."""
    out = {}
    readers = sorted({r["model_id"] for r in rows if r["arm"] == arm and r["model_id"] != "-"})
    groups = sorted({group(r) for r in rows if r["arm"] == arm}) if group else [None]
    for rd in readers:
        for g in groups:
            rs = [r for r in rows if r["arm"] == arm and r["model_id"] == rd and r.get("valid") and (group is None or group(r) == g)]
            diffs = {r["unit_id"]: float(r["scores"][key_r]) - float(r["scores"][key_d]) for r in rs if (r.get("scores") or {}).get(key_r) is not None and r["scores"].get(key_d) is not None}
            c = _ci(diffs)
            mr = [float(r["scores"][key_r]) for r in rs if (r.get("scores") or {}).get(key_r) is not None]
            md = [float(r["scores"][key_d]) for r in rs if (r.get("scores") or {}).get(key_d) is not None]
            cell = {**c, "mean_reader": (sum(mr) / len(mr)) if mr else None, "mean_dom": (sum(md) / len(md)) if md else None,
                    "n_worlds": len(rs), "n_scored": len(diffs)}
            cell["outcome"] = "VOID" if c["point"] is None else ("NON_INFERIOR" if c["point"] >= NONINF else "INFERIOR")
            out[f"{rd}|{g}" if g is not None else rd] = cell
    return out


def run_D01(run: CardRun8) -> int:
    readers = _readers(run, diagnosis=True)
    n = _n(run)
    spec = C.ALL["D01"]
    E.batch(run, ["FM"], readers, spec["condition"], n, family="AG", per_event=True, targets=["surprise"])
    rows = run.rows()
    cells = _auroc_cells(run, rows, "FM")
    by_shape = _auroc_cells(run, rows, "FM", group=lambda r: (r.get("factors") or {}).get("shape"))
    adm = E.admitted(run)
    ok_any = any(v["outcome"] == "NON_INFERIOR" for k, v in cells.items() if k in adm) if adm else False
    if adm and not ok_any:
        record_interrupt("surprise_not_localized", "an admitted reader's surprise does not land on the maker's events as well as the standard process's; the difference claim narrows to 'with the purpose known'; D04 diagnoses before G",
                         blocks=[], detail={k: {"point": v["point"], "ci": [v["lo"], v["hi"]]} for k, v in cells.items()})
    set_gate("difference", ok_any, {"card": "D01", "cells": {k: v["outcome"] for k, v in cells.items()}})
    best = max((v for k, v in cells.items() if v["point"] is not None), key=lambda v: v["lo"], default={"point": None})
    oc = "VOID" if best.get("point") is None else ("SUPPORT_CANDIDATE" if best["lo"] is not None and best["lo"] > 0 else ("INCONCLUSIVE" if best["point"] >= NONINF else "COUNTEREVIDENCE"))
    return E.finish_desc(run, {"cells": cells, "by_shape": by_shape, "tau": read_registry("TAIL_THRESHOLDS"), "admitted": adm, "degenerate": run._degenerate},
                         "; ".join(f"{k}: {v['outcome']} diff {v['point']!s:.6} reader {v['mean_reader']!s:.5} dom {v['mean_dom']!s:.5}" for k, v in cells.items()),
                         outcome=oc, point=best.get("point"), ci=[best.get("lo"), best.get("hi")], n_units=best.get("n_units"),
                         conditional_cells={k: {"outcome": v["outcome"], "point": v["point"]} for k, v in {**cells, **by_shape}.items()})


def run_D02(run: CardRun8) -> int:
    rows = run.rows_of("D01")
    cells = _auroc_cells(run, rows, "FM", group=lambda r: (r.get("factors") or {}).get("shape"))
    facts = (read_registry("CONSTRUCTION_FACTS") or {}).get("shapes") or {}
    order = ["free", "essay", "structured"]
    mono = {}
    for rd in sorted({k.split("|")[0] for k in cells}):
        vals = [cells.get(f"{rd}|{s}", {}).get("mean_reader") for s in order]
        mono[rd] = all(a is not None and b is not None and b >= a for a, b in zip(vals, vals[1:]))
    return E.finish_desc(run, {"by_shape": cells, "construction_tail_gap_by_shape": facts, "monotone_free_to_structured": mono},
                         f"alignment by shape {json.dumps({k: v.get('mean_reader') for k, v in cells.items()})}; monotone {mono}",
                         conditional_cells={k: {"outcome": v["outcome"], "point": v["point"]} for k, v in cells.items()})


def run_D03(run: CardRun8) -> int:
    rows = [r for r in run.rows_of("D01") if r["arm"] == "FM" and r.get("valid")]
    per = {}
    for rd in sorted({r["model_id"] for r in rows}):
        rs = [r for r in rows if r["model_id"] == rd]
        hit = [1.0 if r["scores"].get("hit_reader") else 0.0 for r in rs if r["scores"].get("hit_reader") is not None]
        w1 = [1.0 if r["scores"].get("within1_reader") else 0.0 for r in rs if r["scores"].get("within1_reader") is not None]
        hd = [1.0 if r["scores"].get("hit_dom") else 0.0 for r in rs if r["scores"].get("hit_dom") is not None]
        per[rd] = {"hit_rate": sum(hit) / len(hit) if hit else None, "within1_rate": sum(w1) / len(w1) if w1 else None,
                   "dom_hit_rate": sum(hd) / len(hd) if hd else None, "n": len(rs),
                   "chance": sum(1.0 / max(1, r["scores"].get("n_events") or 1) for r in rs) / len(rs) if rs else None}
    return E.finish_desc(run, {"per_reader": per}, f"first-explanation hit rates {json.dumps(per)}")


def run_D04(run: CardRun8) -> int:
    readers = _readers(run, diagnosis=True)
    n = _n(run)
    spec = C.ALL["D04"]
    ws = E.worlds_for(run, "D04", n, family="PU")
    E.batch(run, ["FM"], readers, dict(spec["condition"], purpose="withheld"), n, worlds=ws, per_event=True, targets=["surprise"], unit_suffix="~w")
    E.batch(run, ["FMPT"], readers, dict(spec["condition"], purpose="withheld"), n, worlds=ws, per_event=True, targets=["surprise"], unit_suffix="~p",
            task_extra=lambda w: {"goal_line": w["purpose"]})
    rows = run.rows()
    fm = [dict(r, unit_id=r["unit_id"][:-2]) for r in rows if r["arm"] == "FM"]
    fp = [dict(r, unit_id=r["unit_id"][:-2]) for r in rows if r["arm"] == "FMPT"]
    out = {}
    for rd in readers:
        a = {r["unit_id"]: r["scores"] for r in fp if r["model_id"] == rd and r.get("valid")}
        b = {r["unit_id"]: r["scores"] for r in fm if r["model_id"] == rd and r.get("valid")}
        common = [u for u in a if u in b]
        d_tail = {u: float(a[u]["auroc_reader"]) - float(b[u]["auroc_reader"]) for u in common if a[u].get("auroc_reader") is not None and b[u].get("auroc_reader") is not None}
        d_res = {u: float(a[u]["auroc_residue_reader"]) - float(b[u]["auroc_residue_reader"]) for u in common if a[u].get("auroc_residue_reader") is not None and b[u].get("auroc_residue_reader") is not None}
        out[rd] = {"tail_alignment_gain": _ci(d_tail), "residue_alignment_gain": _ci(d_res),
                   "mean_residue_auroc_with_purpose": (sum(float(a[u]["auroc_residue_reader"]) for u in d_res) / len(d_res)) if d_res else None,
                   "mean_residue_auroc_without": (sum(float(b[u]["auroc_residue_reader"]) for u in d_res) / len(d_res)) if d_res else None}
    best = max((v["residue_alignment_gain"] for v in out.values() if v["residue_alignment_gain"]["point"] is not None), key=lambda c: c["lo"], default={"point": None})
    oc = "VOID" if best.get("point") is None else ("SUPPORT_CANDIDATE" if best["lo"] > 0 else ("COUNTEREVIDENCE" if best["hi"] < 0 else "INCONCLUSIVE"))
    return E.finish_desc(run, {"per_reader": out, "degenerate": run._degenerate}, json.dumps({k: v["residue_alignment_gain"].get("point") for k, v in out.items()}),
                         outcome=oc, point=best.get("point"), ci=[best.get("lo"), best.get("hi")], n_units=best.get("n_units"),
                         conditional_cells={f"{k}|residue": {"outcome": oc, "point": v["residue_alignment_gain"].get("point")} for k, v in out.items()})


def run_D06(run: CardRun8) -> int:
    table = {}
    signs = []
    for card in ("G02", "G03", "E08", "A03", "E06", "A05"):
        p = S8 / card / "verdict.json"
        if not p.exists():
            continue
        v = read_json(p)
        table[card] = {"whole": {"outcome": v.get("outcome"), "point": v.get("point"), "ci": v.get("ci")},
                       "tail": {"outcome": v.get("tail_outcome"), "point": v.get("tail_point"), "ci": v.get("tail_ci")}}
        pw, pt = v.get("point"), v.get("tail_point")
        if pw is not None and pt is not None and (pw > 0) != (pt > 0):
            signs.append(card)
    return E.finish_desc(run, {"table": table, "sign_differences": signs}, f"{len(table)} prospective cards; sign differences on {signs or 'none'}",
                         conditional_cells={f"{c}|{k}": {"outcome": x["outcome"], "point": x["point"]} for c, t in table.items() for k, x in t.items()})


# ── G: goal as purpose ───────────────────────────────────────────────────────────────

def _purpose_hits(rows: list[dict], arm: str = "PUR") -> dict:
    """Recall by reader: the reader's class (within band) contains the truth or, on an
    equivalence world, its partner; top-1 and calibration beside."""
    out = {}
    for rd in sorted({r["model_id"] for r in rows if r["arm"] == arm and r["model_id"] != "-"}):
        rs = [r for r in rows if r["arm"] == arm and r["model_id"] == rd and r.get("valid")]
        hits = top1 = tot = 0
        confs, corr = [], []
        for r in rs:
            b = ORC.load(r["cell_id"], r["unit_id"].replace("|", "-")) or ORC.load(r["cell_id"], r["unit_id"].split("~")[0].replace("|", "-"))
            if not b or not b.get("purpose"):
                continue
            truth = b["purpose"]
            cls = set(b.get("purpose_class") or [truth])
            reader_cls = set((r.get("extra") or {}).get("equivalence_class") or [])
            dist = ((r.get("extra") or {}).get("targets_extra") or {}).get("purpose") or {}
            top = max(dist, key=dist.get) if dist else None
            tot += 1
            hits += int(bool(reader_cls & cls) or (top in cls if top else False))
            top1 += int(top == truth)
            if dist:
                confs.append(float(dist.get(top, 0.0)))
                corr.append(1.0 if top in cls else 0.0)
        out[rd] = {"recall": hits / tot if tot else None, "top1": top1 / tot if tot else None, "n": tot,
                   "ece": ece(list(zip(confs, [bool(x) for x in corr]))) if confs else None, "mean_conf": (sum(confs) / len(confs)) if confs else None}
    return out


def run_G01(run: CardRun8) -> int:
    readers = _readers(run)
    if not readers:
        return _not_run(run, "no reader passed the expertise gate (E03/E04); the purpose trunk is not tested")
    n = _n(run)
    spec = C.ALL["G01"]
    ws = E.worlds_for(run, "G01", n, family="PU")
    E.batch(run, ["PUR"], readers, spec["condition"], n, worlds=ws, targets=["purpose"])
    rows = run.rows()
    rec = _purpose_hits([r for r in rows if not r["unit_id"].endswith("~repair")])
    repaired = {}
    if not any((v.get("recall") or 0) >= 0.5 for v in rec.values()):
        E.batch(run, ["PUR"], readers, spec["condition"], n, worlds=ws, targets=["purpose"], unit_suffix="~repair", arm_tasks={"PUR": {"proposal_weights": "base"}})
        rows = run.rows()
        repaired = _purpose_hits([r for r in rows if r["unit_id"].endswith("~repair")])
        update_registry("REPAIRS", lambda r: {**r, "G01": "one repair: the proposal readout through the base weights (the adapted readout missed the 0.5 bar)"})
    final = {k: (repaired[k] if repaired and (repaired[k].get("recall") or 0) > (v.get("recall") or 0) else v) for k, v in rec.items()}
    passed = any((v.get("recall") or 0) >= 0.5 for v in final.values())
    set_gate("purpose_recall", passed, {"card": "G01", "recall": {k: v.get("recall") for k, v in final.items()}, "repaired": bool(repaired)})
    return E.finish_desc(run, {"adapted": rec, "repaired": repaired, "final": final, "degenerate": run._degenerate},
                         "; ".join(f"{k}: recall {v.get('recall')!s:.5} top1 {v.get('top1')!s:.5} n {v.get('n')}" for k, v in final.items()) + (" (repaired readout)" if repaired else ""),
                         outcome="INFRASTRUCTURE" if passed else "COUNTEREVIDENCE",
                         point=max((v.get("recall") or 0) for v in final.values()) if final else None,
                         conditional_cells={k: {"outcome": "PASS" if (v.get("recall") or 0) >= 0.5 else "FAIL", "point": v.get("recall")} for k, v in final.items()})


def _proposal_weights() -> str:
    g = read_registry("GATES") or {}
    return "base" if (g.get("purpose_recall") or {}).get("detail", {}).get("repaired") else "adapted"


def run_G02(run: CardRun8) -> int:
    readers = _readers(run)
    if not readers:
        return _not_run(run, "no reader passed the expertise gate")
    n = _n(run)
    spec = C.ALL["G02"]
    ws = E.worlds_for(run, "G02", n, family="PU")
    E.batch(run, ["FMP", "FMPT", "FM", "DOM", "U", "PERS"], readers, spec["condition"], n, worlds=ws,
            arm_tasks={"FMP": {"propose": True, "proposal_weights": _proposal_weights()}},
            task_extra=lambda w: {"goal_line_true": w["purpose"]})
    rows = run.rows()
    # FMPT needs the true purpose in its goal line: the task carried goal_line_true; the arm map sets it
    wt = E.whole_and_tail(run, rows, "FMP", "DOM")
    vs_fm = E.whole_and_tail(run, rows, "FMP", "FM")
    truep = E.whole_and_tail(run, rows, "FMPT", "DOM")
    fm_dom = E.whole_and_tail(run, rows, "FM", "DOM")
    return E.finish_contrast(run, wt, {"fmp_vs_fm": vs_fm, "true_purpose_vs_dom": truep, "fm_vs_dom": fm_dom},
                             gate="purpose_execution", extra_reason=f"vs FM {E.best_cell(vs_fm['whole']).get('point')}; true purpose vs DOM {E.best_cell(truep['whole']).get('point')}; FM vs DOM {E.best_cell(fm_dom['whole']).get('point')}")


def run_G03(run: CardRun8) -> int:
    rows = run.rows_of("G02")
    if not rows:
        return _not_run(run, "G02 did not run")
    # the copied-brief rival: FMP's plain next action scored on the changed-context truth
    keyed = []
    for r in rows:
        if not r.get("valid") or r["arm"] not in ("FMP", "DOM", "FM", "FMPT"):
            continue
        sc = r.get("scores") or {}
        if sc.get("changed_context_ls") is None:
            continue
        keyed.append(dict(r, primary_score=float(sc["changed_context_ls"])))
        if r["arm"] == "FMP" and r.get("pred_ref") and Path(r["pred_ref"]).exists():
            pred = read_json(Path(r["pred_ref"]))
            b = ORC.load(r["cell_id"], r["unit_id"].replace("|", "-"))
            choice = ((b or {}).get("hidden") or {}).get("changed_context", {}).get("choice") if b else None
            if choice:
                p = float((pred["targets"].get("next_action") or {}).get(choice, 0.0))
                keyed.append(dict(r, arm="COPIED", primary_score=math.log(max(p, 1e-9))))
    wt = E.whole_and_tail(run, keyed, "FMP", "DOM")
    vs_copied = E.whole_and_tail(run, keyed, "FMP", "COPIED")
    return E.finish_contrast(run, wt, {"fmp_vs_copied_brief": vs_copied, "note": "the changed-context log score; the copied-brief rival predicts the unchanged choice"},
                             extra_reason=f"vs copied brief {E.best_cell(vs_copied['whole']).get('point')}")


def run_G04(run: CardRun8) -> int:
    rows = [r for r in run.rows_of("G01") if r["arm"] == "PUR" and r.get("valid") and not r["unit_id"].endswith("~repair")]
    if not rows:
        return _not_run(run, "G01 did not run")
    per = {}
    for rd in sorted({r["model_id"] for r in rows}):
        eq_cov = eq_abst = eq_n = single_abst = single_n = 0
        for r in [x for x in rows if x["model_id"] == rd]:
            b = ORC.load(r["cell_id"], r["unit_id"].replace("|", "-"))
            if not b:
                continue
            cls = set(b.get("purpose_class") or [b.get("purpose")])
            rc = set((r.get("extra") or {}).get("equivalence_class") or [])
            abst = bool((r.get("extra") or {}).get("abstain"))
            if len(cls) >= 2:
                eq_n += 1
                eq_cov += int(cls <= rc)
                eq_abst += int(abst)
            else:
                single_n += 1
                single_abst += int(abst)
        per[rd] = {"equivalence_worlds": eq_n, "class_coverage": eq_cov / eq_n if eq_n else None, "abstain_on_equivalence": eq_abst / eq_n if eq_n else None,
                   "singleton_worlds": single_n, "false_abstain": single_abst / single_n if single_n else None}
        per[rd]["passed"] = bool(eq_n) and (per[rd]["abstain_on_equivalence"] or 0) >= 0.5 and (per[rd]["false_abstain"] or 0) <= 0.5
    ok = any(v["passed"] for v in per.values())
    set_gate("equivalence", ok, {"card": "G04"})
    return E.finish_desc(run, {"per_reader": per}, json.dumps(per), outcome="INFRASTRUCTURE" if ok else ("VOID" if not any(v["equivalence_worlds"] for v in per.values()) else "COUNTEREVIDENCE"),
                         conditional_cells={k: {"outcome": "PASS" if v["passed"] else "FAIL", "point": v["class_coverage"]} for k, v in per.items()})


def _pull_candidates(w: dict) -> tuple[dict, str]:
    law = w["state"]["expertise_law"]
    cands = {}
    truth_key = None
    for p in PU.PURPOSES:
        order = G.pull_ordering(PU.PURPOSE_UTILITY[p], law)
        key = f"{order[0]}>{order[1]}"
        cands[key] = f"first {order[0]}, then {order[1]}"
        if p == w["purpose"]:
            truth_key = key
    return cands, truth_key


def run_G05(run: CardRun8) -> int:
    readers = _readers(run)
    if not readers:
        return _not_run(run, "no reader passed the expertise gate")
    n = _n(run)
    spec = C.ALL["G05"]
    ws = E.worlds_for(run, "G05", n, family="PU")
    E.batch(run, ["PULL"], readers, spec["condition"], n, worlds=ws, targets=["pull"],
            task_extra=lambda w: {"question": "Which two kinds of move is the maker pulled toward most, in order?", "candidates": _pull_candidates(w)[0], "proposal_weights": _proposal_weights()})
    rows = run.rows()
    wmap = {w["lid"]: w for w in ws}
    per = {}
    for rd in readers:
        hits = tot = 0
        for r in [x for x in rows if x["arm"] == "PULL" and x["model_id"] == rd and x.get("valid")]:
            w = wmap.get(r["unit_id"])
            if not w:
                continue
            _c, truth = _pull_candidates(w)
            dist = ((r.get("extra") or {}).get("targets_extra") or {}).get("pull") or {}
            if not dist:
                continue
            top = max(dist.values())
            cls = {k for k, v in dist.items() if top - v <= 0.15}
            tot += 1
            hits += int(truth in cls)
        g01 = (read_json(S8 / "G01" / "metrics.json") if (S8 / "G01" / "metrics.json").exists() else {}).get("final", {}).get(rd, {})
        per[rd] = {"pull_recall": hits / tot if tot else None, "n": tot, "purpose_recall": g01.get("recall"),
                   "difference_purpose_minus_pull": ((g01.get("recall") or 0) - (hits / tot)) if tot and g01.get("recall") is not None else None}
    return E.finish_desc(run, {"per_reader": per, "degenerate": run._degenerate}, json.dumps(per),
                         conditional_cells={k: {"outcome": "purpose_easier" if (v["difference_purpose_minus_pull"] or 0) > 0 else "pull_easier", "point": v["difference_purpose_minus_pull"]} for k, v in per.items()})


def _paraphrase(ev: dict) -> dict:
    ev = copy.deepcopy(ev)
    secs = [s["name"] for s in ev["artifact_state"]["sections"]]
    smap = {s: f"part{chr(97 + i)}" for i, s in enumerate(secs)}
    def slot(x):
        return x.replace("s", "u").replace(".", "-") if x[:1] == "s" and any(ch.isdigit() for ch in x) else x
    for s in ev["artifact_state"]["sections"]:
        s["slots"] = [slot(x) for x in s["slots"]]
        s["filled"] = [f"{f.split('@')[0]}@{slot(f.split('@')[1])}" for f in s.get("filled", [])]
        s["name"] = smap[s["name"]]
    for e in ev["process_prefix"]:
        e["section"] = smap.get(e["section"], e["section"])
        e["slot"] = slot(e["slot"])
    q = ev["query"]
    q["next_action_options"] = [f"{t}:{smap.get(s, s)}:{slot(sl)}" for t, s, sl in (o.split(":") for o in q["next_action_options"])]
    q["sections"] = [smap[s] for s in q["sections"]]
    oo = ev.get("objective_options") or {}
    for key in ("initial", "at_cut"):
        for a in oo.get(key, []):
            a["section"] = smap.get(a["section"], a["section"])
            a["slot"] = slot(a["slot"])
    if ev.get("brief"):
        ev["brief"]["required_sections"] = [smap.get(s, s) for s in ev["brief"]["required_sections"]]
    ev["artifact_state"]["prefix_text"] = W.render_prefix_text(ev["process_prefix"], "log", ev["artifact_state"].get("topic", ""))
    return ev


SWAP = {"write": "check", "check": "write", "cite": "consult", "consult": "cite", "revise": "fix", "fix": "revise", "restructure": "probe", "probe": "restructure"}


def _meaning_change(ev: dict) -> dict:
    ev = copy.deepcopy(ev)
    for e in ev["process_prefix"]:
        e["type"] = SWAP.get(e["type"], e["type"])
    for s in ev["artifact_state"]["sections"]:
        s["filled"] = [f"{SWAP.get(f.split('@')[0], f.split('@')[0])}@{f.split('@')[1]}" for f in s.get("filled", [])]
    ev["artifact_state"]["prefix_text"] = W.render_prefix_text(ev["process_prefix"], "log", ev["artifact_state"].get("topic", ""))
    return ev


def run_G06(run: CardRun8) -> int:
    readers = _readers(run)
    if not readers:
        return _not_run(run, "no reader passed the expertise gate")
    n = _n(run)
    spec = C.ALL["G06"]
    ws = E.worlds_for(run, "G06", n, family="PU", )
    E.batch(run, ["PUR"], readers, spec["condition"], n, worlds=ws, targets=["purpose"], unit_suffix="~base", arm_tasks={"PUR": {"proposal_weights": _proposal_weights()}})
    E.batch(run, ["PUR"], readers, spec["condition"], n, worlds=ws, targets=["purpose"], unit_suffix="~para", evidence_hook=lambda w, ev: _paraphrase(ev), arm_tasks={"PUR": {"proposal_weights": _proposal_weights()}})
    E.batch(run, ["PUR"], readers, spec["condition"], n, worlds=ws, targets=["purpose"], unit_suffix="~mean", evidence_hook=lambda w, ev: _meaning_change(ev), arm_tasks={"PUR": {"proposal_weights": _proposal_weights()}})
    rows = run.rows()
    per = {}
    for rd in readers:
        rec = {}
        for tag in ("base", "para", "mean"):
            rs = [r for r in rows if r["model_id"] == rd and r["unit_id"].endswith(f"~{tag}")]
            h = _purpose_hits(rs).get(rd) or {}
            rec[tag] = h.get("recall")
        rec["paraphrase_survives"] = rec["base"] is not None and rec["para"] is not None and rec["para"] >= rec["base"] - 0.1
        rec["meaning_falls"] = rec["base"] is not None and rec["mean"] is not None and rec["mean"] <= rec["base"] - 0.2
        rec["crossover"] = rec["paraphrase_survives"] and rec["meaning_falls"]
        per[rd] = rec
    ok = any(v["crossover"] for v in per.values())
    return E.finish_desc(run, {"per_reader": per, "degenerate": run._degenerate}, json.dumps(per), outcome="INFRASTRUCTURE" if ok else "COUNTEREVIDENCE",
                         conditional_cells={k: {"outcome": "PASS" if v["crossover"] else "FAIL", "point": v.get("base")} for k, v in per.items()})


def run_G07(run: CardRun8) -> int:
    rows = [r for r in run.rows_of("G01") if r["arm"] == "PUR" and r.get("valid") and not r["unit_id"].endswith("~repair")]
    if not rows:
        return _not_run(run, "G01 did not run")
    per = {}
    for rd in sorted({r["model_id"] for r in rows}):
        buckets = {"short": ([], []), "mid": ([], []), "long": ([], [])}
        confs, corr, doses = [], [], []
        for r in [x for x in rows if x["model_id"] == rd]:
            b = ORC.load(r["cell_id"], r["unit_id"].replace("|", "-"))
            dist = ((r.get("extra") or {}).get("targets_extra") or {}).get("purpose") or {}
            if not b or not dist:
                continue
            top = max(dist, key=dist.get)
            cls = set(b.get("purpose_class") or [b.get("purpose")])
            c, y = float(dist[top]), 1.0 if top in cls else 0.0
            L = int((r.get("factors") or {}).get("prefix_len") or 0)
            k = "short" if L <= 4 else ("mid" if L <= 7 else "long")
            buckets[k][0].append(c)
            buckets[k][1].append(y)
            confs.append(c)
            corr.append(y)
            doses.append(L)
        rec = {k: {"n": len(v[0]), "mean_conf": (sum(v[0]) / len(v[0])) if v[0] else None, "accuracy": (sum(v[1]) / len(v[1])) if v[1] else None,
                   "ece": ece(list(zip(v[0], [bool(x) for x in v[1]]))) if v[0] else None} for k, v in buckets.items()}
        slope = calibration_slope(list(zip(confs, [bool(x) for x in corr]))) if len(confs) >= 8 else None
        # confidence against dose: the rank correlation
        rc = None
        if len(doses) >= 8:
            rk = lambda xs: [sorted(xs).index(x) for x in xs]  # noqa: E731
            a, bq = rk(doses), rk(confs)
            ma, mb = sum(a) / len(a), sum(bq) / len(bq)
            num = sum((x - ma) * (y - mb) for x, y in zip(a, bq))
            den = math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in bq)) or 1.0
            rc = num / den
        per[rd] = {"by_dose": rec, "slope": slope, "ece_all": ece(list(zip(confs, [bool(x) for x in corr]))) if confs else None, "conf_dose_rank_corr": rc, "n": len(confs)}
    return E.finish_desc(run, {"per_reader": per}, json.dumps({k: {"slope": v["slope"], "ece": v["ece_all"], "rho": v["conf_dose_rank_corr"]} for k, v in per.items()}),
                         outcome="VALID_NULL" if all((v["conf_dose_rank_corr"] or 0) <= 0.1 for v in per.values()) else "DESCRIPTIVE")


# ── A: accumulation ─────────────────────────────────────────────────────────────────

def run_A01(run: CardRun8) -> int:
    readers = _readers(run)
    if not readers:
        return _not_run(run, "no reader passed the expertise gate")
    n = _n(run)
    spec = C.ALL["A01"]
    ws = E.worlds_for(run, "A01", n, family="MS")
    for N in (0, 1, 2, 3):
        E.batch(run, ["FMN"], readers, dict(spec["condition"], n_earlier=N), n, worlds=ws, per_event=True, targets=["surprise"], unit_suffix=f"~n{N}",
                factors_of=lambda w, N=N: {"n_earlier": N, "reveal": w.get("reveal"), "maker": w.get("maker")})
    rows = run.rows()
    by_n = E.contrast_by_reader  # noqa: F841  (the helper is reused below through _auroc_cells)
    cells = _auroc_cells(run, rows, "FMN", group=lambda r: (r.get("factors") or {}).get("n_earlier"))
    per = {}
    for rd in readers:
        a3 = {r["unit_id"][:-3]: float(r["scores"]["auroc_reader"]) for r in rows if r["arm"] == "FMN" and r["model_id"] == rd and r.get("valid") and r["unit_id"].endswith("~n3") and (r.get("scores") or {}).get("auroc_reader") is not None}
        a0 = {r["unit_id"][:-3]: float(r["scores"]["auroc_reader"]) for r in rows if r["arm"] == "FMN" and r["model_id"] == rd and r.get("valid") and r["unit_id"].endswith("~n0") and (r.get("scores") or {}).get("auroc_reader") is not None}
        d = {u: a3[u] - a0[u] for u in a3 if u in a0}
        means = [cells.get(f"{rd}|{N}", {}).get("mean_reader") for N in (0, 1, 2, 3)]
        per[rd] = {"n3_minus_n0": _ci(d), "means_by_n": means, "monotone": all(x is not None and y is not None and y >= x for x, y in zip(means, means[1:]))}
    best = max((v["n3_minus_n0"] for v in per.values() if v["n3_minus_n0"]["point"] is not None), key=lambda c: c["lo"], default={"point": None})
    oc = "VOID" if best.get("point") is None else ("SUPPORT_CANDIDATE" if best["lo"] > 0 else ("COUNTEREVIDENCE" if best["hi"] < 0 else ("VALID_NULL" if best["hi"] < 0.05 else "INCONCLUSIVE")))
    set_gate("accumulation", oc == "SUPPORT_CANDIDATE", {"card": "A01"})
    return E.finish_desc(run, {"cells": cells, "per_reader": per, "degenerate": run._degenerate},
                         "; ".join(f"{k}: means by N {[(round(m, 3) if m is not None else None) for m in v['means_by_n']]}; N3-N0 {v['n3_minus_n0'].get('point')!s:.6} monotone {v['monotone']}" for k, v in per.items()),
                         outcome=oc, point=best.get("point"), ci=[best.get("lo"), best.get("hi")], n_units=best.get("n_units"),
                         conditional_cells={k: {"outcome": v["outcome"], "point": v["mean_reader"]} for k, v in cells.items()})


def _law_candidates() -> dict:
    return {ln: W.factor_language("expertise_law", {"expertise_law": W.LAWS[ln]}) for ln in W.LAW_NAMES}


def _residue_candidates(w: dict) -> dict:
    out = {}
    for name in W.RESIDUES:
        h = W._residue(name, w["inventory"], cue_step=5)
        out[name] = W.factor_language("history_residue", {"history_residue": h})
    return out


def run_A02(run: CardRun8) -> int:
    readers = _readers(run)
    if not readers:
        return _not_run(run, "no reader passed the expertise gate")
    n = _n(run)
    spec = C.ALL["A02"]
    ws = E.worlds_for(run, "A02", n, family="MS")
    for N in (0, 1, 2, 3):
        E.batch(run, ["LAWR", "RESR"], readers, dict(spec["condition"], n_earlier=N), n, worlds=ws, unit_suffix=f"~n{N}",
                factors_of=lambda w, N=N: {"n_earlier": N, "reveal": w.get("reveal")},
                arm_tasks={"LAWR": {"question": "Which description fits how this maker works?", "candidates": _law_candidates(), "proposal_weights": _proposal_weights()},
                           "RESR": {"question": "Which standing habit or held intention does this maker carry?", "proposal_weights": _proposal_weights()}},
                task_extra=lambda w: {"candidates_resr": _residue_candidates(w)})
    rows = run.rows()
    wmap = {w["lid"]: w for w in ws}
    per = {}
    for rd in readers:
        rec = {}
        for arm, key, truth_of in (("LAWR", "lawr", lambda w: w["state"]["names"]["law"]), ("RESR", "resr", lambda w: w["state"]["names"]["residue"])):
            byn = {}
            for N in (0, 1, 2, 3):
                hits = tot = 0
                for r in [x for x in rows if x["arm"] == arm and x["model_id"] == rd and x.get("valid") and x["unit_id"].endswith(f"~n{N}")]:
                    w = wmap.get(r["unit_id"][:-3])
                    dist = ((r.get("extra") or {}).get("targets_extra") or {}).get(key) or {}
                    if not w or not dist:
                        continue
                    tot += 1
                    hits += int(max(dist, key=dist.get) == truth_of(w))
                byn[N] = hits / tot if tot else None
            rec[arm] = {"recall_by_n": byn, "chance": 1.0 / len(W.LAW_NAMES) if arm == "LAWR" else 1.0 / len(W.RESIDUES),
                        "rises": all(byn[a] is not None and byn[b] is not None and byn[b] >= byn[a] for a, b in ((0, 1), (1, 2), (2, 3)))}
        per[rd] = rec
    s7 = {"law_recall_stage7_cold": 0.33, "residue_recall_stage7": 0.56, "source": "L344, L354"}
    return E.finish_desc(run, {"per_reader": per, "stage7_comparator": s7, "degenerate": run._degenerate}, json.dumps(per),
                         conditional_cells={f"{k}|{arm}|n{N}": {"outcome": "rises" if v[arm]["rises"] else "flat", "point": v[arm]["recall_by_n"][N]} for k, v in per.items() for arm in ("LAWR", "RESR") for N in (0, 1, 2, 3)})


def run_A03(run: CardRun8) -> int:
    readers = _readers(run)
    if not readers:
        return _not_run(run, "no reader passed the expertise gate")
    n = _n(run)
    spec = C.ALL["A03"]
    ws = E.worlds_for(run, "A03", n, family="MS")
    E.batch(run, ["FMN", "DOM", "U", "PERS"], readers, dict(spec["condition"], n_earlier=3), n, worlds=ws)
    E.batch(run, ["FM"], readers, dict(spec["condition"], n_earlier=0), n, worlds=ws)
    if os.environ.get("S8_STUDENT"):
        from runners.stage8 import student as ST                                  # noqa: PLC0415
        ST.run_student(run, ws, readers)
    rows = run.rows()
    wt = E.whole_and_tail(run, rows, "FMN", "DOM")
    vs0 = E.whole_and_tail(run, rows, "FMN", "FM")
    extra = {"fmn3_vs_fm0": vs0}
    if os.environ.get("S8_STUDENT"):
        extra["student_vs_fmn3"] = E.whole_and_tail(run, rows, "STU", "FMN")
        extra["student_vs_dom"] = E.whole_and_tail(run, rows, "STU", "DOM")
    return E.finish_contrast(run, wt, extra, extra_reason=f"vs FM+0 {E.best_cell(vs0['whole']).get('point')}")


def run_A04(run: CardRun8) -> int:
    a1 = [r for r in run.rows_of("A01") if r["arm"] == "FMN" and r.get("valid")]
    a2 = [r for r in run.rows_of("A02") if r.get("valid")]
    if not a1 and not a2:
        return _not_run(run, "A01 and A02 did not run")
    per = {}
    for rd in sorted(({r["model_id"] for r in a1} | {r["model_id"] for r in a2}) - {"-"}):
        rec = {}
        for rv in ("low", "high"):
            rs = [r for r in a1 if r["model_id"] == rd and (r.get("factors") or {}).get("reveal") == rv and r["unit_id"].endswith("~n3") and (r.get("scores") or {}).get("auroc_reader") is not None]
            rec[f"alignment_n3_{rv}"] = (sum(float(r["scores"]["auroc_reader"]) for r in rs) / len(rs)) if rs else None
            rec[f"n_{rv}"] = len(rs)
        per[rd] = rec
    return E.finish_desc(run, {"per_reader": per}, json.dumps(per))


def run_A05(run: CardRun8) -> int:
    readers = _readers(run)
    if not readers:
        return _not_run(run, "no reader passed the expertise gate")
    n = _n(run)
    spec = C.ALL["A05"]
    ws = E.worlds_for(run, "A05", n, family="MS")
    for which in ("none", "law", "residue", "purpose"):
        E.batch(run, ["FMN"] + (["DOM", "U"] if which == "none" else []), readers, dict(spec["condition"], n_earlier=3), n, worlds=ws, unit_suffix=f"~{which}",
                factors_of=lambda w, which=which: {"supplied": which},
                task_extra=lambda w, which=which: {"state_lines": E.factor_line(w, which)} if which != "none" else {})
    rows = run.rows()
    base = [dict(r, unit_id=r["unit_id"].split("~")[0]) for r in rows if r["unit_id"].endswith("~none")]
    wt = E.whole_and_tail(run, base, "FMN", "DOM")
    removed = {}
    for which in ("law", "residue", "purpose"):
        rs = base + [dict(r, arm="FMNX", unit_id=r["unit_id"].split("~")[0]) for r in rows if r["unit_id"].endswith(f"~{which}") and r["arm"] == "FMN"]
        removed[which] = E.whole_and_tail(run, rs, "FMNX", "FMN")
    return E.finish_contrast(run, wt, {"gain_change_when_supplied": removed, "note": "a factor whose supply ADDS nothing to FM+3 is one the earlier artifacts already carried; a factor that adds is one they did not"},
                             extra_reason="; ".join(f"+{k}: {E.best_cell(v['whole']).get('point')}" for k, v in removed.items()))


# ── the frontier cells ───────────────────────────────────────────────────────────────

def _fr_rows(run: CardRun8, ws: list[dict], cond_spec: dict, mode: str, purpose_line=None) -> None:
    m = FR.chosen()
    if not m:
        raise RuntimeError("no frontier model chosen")
    model = m["model"]
    dp = E.dom_params()
    for w in ws:
        run.check_deadline()
        uid = w["lid"] + (f"~{mode}" if mode != "next" else "")
        if run.is_done(model, uid, "FR"):
            continue
        cond = E.build_condition(cond_spec, E._opaque(w["lid"]), run.card)
        if mode == "per_event":
            cond["per_event"] = True
        ev = E.evidence_for(w, cond)
        b = E.bundle_for(w, cond, ev)
        try:
            if mode == "purpose":
                r = FR.fr_purpose(run.cell_id, ev, PU.purpose_candidates())
                dist = r["dist"] or {}
                named = {k: v for k, v in dist.items() if k != "unknown"}
                z = sum(named.values()) or 1.0
                named = {k: v / z for k, v in named.items()}
                top = max(named, key=named.get) if named else None
                cls = sorted(k for k, v in named.items() if named and max(named.values()) - v <= 0.15)
                sc = {"primary": None, "purpose_top": top, "in_class": bool(top and top in set(b.get("purpose_class") or [b.get("purpose")]))}
                extra = {"targets_extra": {"purpose": named}, "equivalence_class": cls, "abstain": len(cls) >= 2 or (dist.get("unknown", 0) >= max(named.values(), default=0)),
                         "confidence": max(named.values()) if named else None, "usd": r["usd"], "raw": r["raw"][:400]}
            elif mode == "per_event":
                per = FR.fr_per_event(run.cell_id, ev)
                pred = {"notes": {"per_event": [{"next_action": p["dist"] or {}} for p in per]}}
                events = b.get("events") or []
                idx = {p["i"]: p for p in per}
                b2 = dict(b, events=[e for e in events if e["i"] in idx])
                pred["notes"]["per_event"] = [None] * (max(idx) + 1 if idx else 0)
                for p in per:
                    pred["notes"]["per_event"][p["i"]] = {"next_action": p["dist"] or {}}
                for i in range(len(pred["notes"]["per_event"])):
                    if pred["notes"]["per_event"][i] is None:
                        pred["notes"]["per_event"][i] = {"next_action": {}}
                sc = E.score_per_event(pred, b2)
                extra = {"usd": sum(p["usd"] for p in per), "n_calls": len(per)}
            else:
                r = FR.fr_next_action(run.cell_id, ev, purpose_line=purpose_line(w) if purpose_line else None)
                dist = r["dist"]
                pred = {"targets": {"next_action": dist or {k: 1.0 / len(ev["query"]["next_action_options"]) for k in ev["query"]["next_action_options"]}, "stop": 0.5}, "abstain": False, "confidence": max(dist.values()) if dist else 0.0}
                sc = PS.score(pred, b)
                extra = {"usd": r["usd"], "raw": r["raw"][:400], "parsed": dist is not None}
        except FrontierCap as e:
            run.row(uid, reader=model, arm="FR", valid=False, validity_reason=f"cap: {e}")
            run.unit_complete(model, uid, "FR")
            raise
        ORC.save(run.cell_id, uid.replace("|", "-"), b, ev)
        run.row(uid, reader=model, arm="FR", factors={"domain": w["domain"], "tail": bool(b.get("tail")), "shape": b.get("shape"), "purpose": b.get("purpose")},
                truth=b["hidden"].get("next_action"), truth_ref=str(ORC.bundle_path(run.cell_id, uid.replace("|", "-"))), scores=sc,
                primary_score=sc.get("primary"), evidence_sha=evidence_sha(ev), extra=extra)
        run.unit_complete(model, uid, "FR")
        if mode in ("next",) and dp:
            d = B.dom(ev, dp)
            if d and not run.is_done("-", uid, "DOM"):
                predd = {"targets": {"next_action": d["next_action"], "stop": d["p_stop"]}, "abstain": False, "confidence": 0.5}
                scd = PS.score(predd, b)
                run.row(uid, arm="DOM", factors={"domain": w["domain"], "tail": bool(b.get("tail"))}, truth=b["hidden"].get("next_action"), scores=scd, primary_score=scd.get("primary"))
                run.unit_complete("-", uid, "DOM")
    if mode == "next":
        E.oracle_rows(run, ws, E.build_condition(cond_spec, "u", run.card))


def _fr_cell(run: CardRun8, family: str, mode: str, n: int, worlds=None, purpose_line=None, **kw) -> tuple[dict, str, bool]:
    if not FR.chosen():
        return {}, "no frontier model passed the calibration fixture; INSTRUMENT_FAILED at zero dollars", False
    ws = worlds if worlds is not None else E.worlds_for(run, run.card, n, family=family, **kw)
    capped = False
    try:
        _fr_rows(run, ws, C.ALL[run.card]["condition"], mode, purpose_line=purpose_line)
    except FrontierCap as e:
        capped = True
        update_registry("FRONTIER_LEDGER", lambda led: {**led, "cap_hit": {"cell": run.cell_id, "at": now_iso(), "why": str(e)}})
    return {"n_worlds": len(ws), "capped": capped, "usd_total": (read_registry("FRONTIER_LEDGER") or {}).get("total_usd")}, "", capped


def run_E07(run: CardRun8) -> int:
    n = _n(run)
    ws = E._gate_worlds(run, "E07", n)
    meta, why, capped = _fr_cell(run, "POPPU", "next", n, worlds=ws)
    if why:
        return E.finish_infra(run, {"why": why}, False, why)
    rows = run.rows()
    c = E.contrast_by_reader(run, rows, "FR", "DOM")
    cell = next((v for k, v in c.items() if k != "pooled"), {})
    passed = cell.get("point") is not None and cell["point"] >= -0.05
    parsed = sum(1 for r in rows if r["arm"] == "FR" and r.get("valid") and (r.get("extra") or {}).get("parsed")) / max(1, sum(1 for r in rows if r["arm"] == "FR"))
    return E.finish_desc(run, {**meta, "contrast": c, "parse_rate": parsed}, f"FR vs DOM {cell.get('point')} {cell.get('ci')}; {'PASS' if passed else 'FAIL'} the expertise band; parse {parsed:.2f}; capped {capped}",
                         outcome="INSTRUMENT_FAILED" if capped and cell.get("point") is None else ("SUPPORT_CANDIDATE" if passed and (cell.get("ci") or [-1])[0] > 0 else ("INCONCLUSIVE" if passed else "COUNTEREVIDENCE")),
                         point=cell.get("point"), ci=cell.get("ci"), n_units=cell.get("n_units"))


def run_D05(run: CardRun8) -> int:
    n = _n(run)
    meta, why, capped = _fr_cell(run, "AG", "per_event", n)
    if why:
        return E.finish_infra(run, {"why": why}, False, why)
    rows = run.rows()
    cells = _auroc_cells(run, rows, "FR")
    best = next(iter(cells.values()), {"point": None})
    return E.finish_desc(run, {**meta, "cells": cells}, json.dumps({k: {"diff": v["point"], "reader": v["mean_reader"], "dom": v["mean_dom"]} for k, v in cells.items()}) + f"; capped {capped}",
                         outcome="INSTRUMENT_FAILED" if capped and best.get("point") is None else ("SUPPORT_CANDIDATE" if best.get("lo") is not None and best["lo"] > 0 else ("INCONCLUSIVE" if best.get("point") is not None and best["point"] >= NONINF else ("COUNTEREVIDENCE" if best.get("point") is not None else "VOID"))),
                         point=best.get("point"), ci=[best.get("lo"), best.get("hi")], n_units=best.get("n_units"))


def run_G08(run: CardRun8) -> int:
    n = _n(run)
    ws = E.worlds_for(run, "G08", n, family="PU")
    meta, why, capped = _fr_cell(run, "PU", "purpose", n, worlds=ws)
    if why:
        return E.finish_infra(run, {"why": why}, False, why)
    rows = run.rows()
    fr_p = [r for r in rows if r["arm"] == "FR" and r["unit_id"].endswith("~purpose") and r.get("valid")]
    recall = (sum(1 for r in fr_p if (r.get("scores") or {}).get("in_class")) / len(fr_p)) if fr_p else None
    gain = None
    if not capped:
        top_of = {r["unit_id"][:-8]: (r.get("scores") or {}).get("purpose_top") for r in fr_p}
        meta2, why2, capped = _fr_cell(run, "PU", "next", n, worlds=ws, purpose_line=lambda w: (PU.PURPOSE_LANGUAGE.get(top_of.get(w["lid"]) or "", None)))
        rows = run.rows()
        c = E.contrast_by_reader(run, rows, "FR", "DOM")
        gain = next((v for k, v in c.items() if k != "pooled"), {})
    return E.finish_desc(run, {**meta, "purpose_recall": recall, "n_purpose": len(fr_p), "gain_with_own_purpose_vs_dom": gain, "capped": capped},
                         f"FR purpose recall {recall}; gain with its own purpose vs DOM {(gain or {}).get('point')} {(gain or {}).get('ci')}; capped {capped}",
                         outcome="INSTRUMENT_FAILED" if capped and recall is None else ("SUPPORT_CANDIDATE" if gain and (gain.get("ci") or [-1])[0] > 0 else ("DESCRIPTIVE" if gain else "VOID")),
                         point=(gain or {}).get("point"), ci=(gain or {}).get("ci"), n_units=(gain or {}).get("n_units"))


DISPATCH = {"D01": run_D01, "D02": run_D02, "D03": run_D03, "D04": run_D04, "D05": run_D05, "D06": run_D06,
            "G01": run_G01, "G02": run_G02, "G03": run_G03, "G04": run_G04, "G05": run_G05, "G06": run_G06, "G07": run_G07, "G08": run_G08,
            "A01": run_A01, "A02": run_A02, "A03": run_A03, "A04": run_A04, "A05": run_A05, "E07": run_E07}


def run_card(run: CardRun8) -> int:
    return DISPATCH[run.card](run)
