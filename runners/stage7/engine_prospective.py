"""Stage 7 prospective, ecological, and bounded-history trunks (brief §10 P and V, §16.1,
§16.4, §16.5). P01-P08 and P10 are analyses over the R13 (cold) and K15 rows; P09 runs
the tail; P11/P12 the controlled histories; P13 CoAuthor after the loader repair; P14
ScholaWrite switches; V01-V06 the bounded attention/history constructions.

DESIGN CHECK (2026-09-02)
lessons read: LESSONS §3 (a paired contrast on the estimand's own per-item quantity;
  stopping gains read against matched progress and length; a change-point claim needs
  the style-switch crossover and its baseline arm caught at its known answer; a
  representation-space claim needs the cheap scalars in its surface control; a filter
  that keeps a minority is reported as a kept fraction), §5 (the independent unit is the
  world, history, or session).
gates and bands:
  - P01-P08: the Stage-5 exhaustive bands on the paired arm-minus-DOM contrast at the
    §12.4 floor; NULL: interval covering zero or under the floor; ALTERNATIVE: above.
  - P11/P12 (discontinuity): NULL of a surface reader is a process-switch change-point
    gain over the stacked surface rival with the interval covering zero, OR any gain on
    the style-shift no-switch adversary (fails DOWN: renamed a style detector);
    ALTERNATIVE: gain on both the plain and the style-matched switch and none on the
    style shift.
  - P13/P14: bands on the choice or switch-conditioned gain over the position or
    persistence rival; the state-reconstruction gate (D07/D08) is read first.
  bands: exhaustive as in the Stage-5 set.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from runners import s5_lib                                                         # noqa: E402
from runners.stage7 import cards as C                                              # noqa: E402
from runners.stage7 import engine_supplied as ES                                   # noqa: E402
from runners.stage7 import engines as E                                            # noqa: E402
from runners.stage7 import runtime as RT                                           # noqa: E402
from runners.stage7.cardrun import SMOKE, CardRun7                                 # noqa: E402
from runners.stage7.constructor import histories as H                              # noqa: E402
from runners.stage7.constructor import oracle as ORC                               # noqa: E402
from runners.stage7.constructor import worlds as W                                 # noqa: E402
from runners.stage7.records import coauthor as CA                                  # noqa: E402
from runners.stage7.records import mixed_control as MC                             # noqa: E402
from runners.stage7.records import scholawrite as SW                               # noqa: E402
from runners.stage7.scoring import calibration as CAL                              # noqa: E402
from runners.stage7.scoring import change_point as CP                              # noqa: E402
from runners.stage7.scoring import prospective as PS                               # noqa: E402
from soundingline.stage7 import (EVIDENCE_VERSION, evidence_sha, gate_state,        # noqa: E402
                                 prediction_sha, read_json, read_registry, set_gate,
                                 validate_prediction, write_registry, update_registry)

SEED = 73000


# ── P01-P08, P10: analyses over the cold rows ────────────────────────────────────────

P_KEY = {"P01": ("primary_score", None), "P02": ("next_type_ls", None), "P03": ("next_section_ls", None),
         "P04": ("pairwise_ls", "rejected"), "P05": ("stop_ls", None), "P06": ("boundary_type_ls", None),
         "P07": ("changed_context_ls", None), "P08": ("invalidation_ls", None)}


def _pairwise_rows(rows: list[dict], cell: str) -> list[dict]:
    """P04: the pairwise choice score between the taken action and the rejected
    alternative from each prediction's next-action distribution."""
    out = []
    for r in rows:
        if not r.get("valid") or not r.get("pred_ref"):
            continue
        b = ORC.load(cell, r["unit_id"].replace("|", "-"))
        if not b or not b["hidden"].get("rejected_alternative"):
            continue
        d = read_json(Path(r["pred_ref"]))["targets"]["next_action"]
        t, a = b["hidden"]["next_action"], b["hidden"]["rejected_alternative"]
        pt, pa = float(d.get(t, 0.0)), float(d.get(a, 0.0))
        z = pt + pa
        out.append(dict(r, primary_score=math.log(max(pt / z if z > 0 else 0.5, 1e-9))))
    return out


def run_P_analysis(run: CardRun7) -> int:
    card = run.card
    key, special = P_KEY[card]
    src_rows = [r for r in run.rows_of("R13")] if (E.S7 / "R13" / "cases.jsonl").exists() else []
    if card == "P05" and (E.S7 / "K15" / "cases.jsonl").exists():
        k15 = run.rows_of("K15")
    else:
        k15 = []
    if special == "rejected":
        rows = _pairwise_rows(src_rows, "R13")
        orr = []
    else:
        rows = ES._score_key(src_rows, key) if key != "primary_score" else [r for r in src_rows if r.get("valid") and r.get("primary_score") is not None]
        orr = [r for r in rows if r["arm"] == "OR"]
    if not rows:
        return E._finish_desc(run, {"source": "R13", "n": 0}, "no R13 rows landed", outcome="VOID")
    floor, g = ES._gate_floor(rows) if orr else (0.03, {"gap": None})
    cells = {}
    for arm in ("SLJ", "DIR"):
        for k, v in ES._contrast_by_reader(run, rows, arm, "DOM", threshold=floor).items():
            cells[f"{arm}|{k}"] = v
    metrics = {"source": "R13", "key": key, "oracle_gap": g, "floor": floor,
               "vs_pers": {a: {k: v.get("point") for k, v in ES._contrast_by_reader(run, rows, a, "PERS", threshold=floor).items()} for a in ("SLJ", "DIR")} if any(r["arm"] == "PERS" for r in rows) else None}
    if card == "P05" and k15:
        k15s = ES._score_key(k15, "stop_ls")
        metrics["k15_supplied_state"] = {k: v.get("point") for k, v in ES._contrast_by_reader(run, k15s, "DIR", "DOM", threshold=floor).items()}
    if card == "P06":
        eq_rows = [r for r in src_rows if r.get("valid") and r["arm"] in ("SLJ", "DIR")]
        metrics["equivalent_boundary_abstention"] = "the 'equivalent' option carries the credit where two stop terms tie (scored inside boundary_type_ls)"
        metrics["resumption_counterfactual"] = {a: E.mean_score(ES._score_key([r for r in src_rows if r["arm"] == a and r.get("valid")], "changed_context_ls")) for a in ("SLJ", "DIR", "DOM")}
    if card == "P03":
        metrics["note"] = "section-level hierarchical score; slot within section is carried by the exact next-action score (P01)"
    return ES._finish_contrast(run, cells, metrics)


def run_P09(run: CardRun7) -> int:
    """The whole withheld tail: sequential predictions with teacher forcing, per event."""
    spec = C.ALL["P09"]
    n = E.n_units("P09")
    arms = spec["arms"]
    with E.ModelServer("s7_p09", run.readers) as server:
        skipped_terminal = 0
        for w in E.worlds_for(run, "P09", n, family="worlds_P", offset=200):
            run.check_deadline()
            tail = w["hidden"]["tail"][:4]
            if not tail:
                skipped_terminal += 1               # a terminal cut has no withheld tail
                continue
            for arm in arms:
                for reader in (run.readers if arm in E.MODEL_ARMS else [None]):
                    if run.is_done(reader, w["lid"], arm):
                        continue
                    per = []
                    budget = {}
                    for k in range(len(tail)):
                        w_k = dict(w, cut=w["cut"] + k)
                        w_k["state_at_cut"] = W._state_at(w["state"], w["trajectory"], w["cut"] + k, w["inventory"])
                        if w["cut"] + k >= len(w["trajectory"]["steps"]):
                            break
                        sections = [s["name"] for s in w["doc"]["sections"]]
                        n_done = sum(1 for s in w["trajectory"]["steps"][:w["cut"] + k] if s["outcome"] == "done")
                        w_k["oracle"] = W._predictive(w_k["state_at_cut"], w_k["state_at_cut"]["pending"], sections, w["trajectory"]["steps"][w["cut"] + k - 1]["type"], w["cut"] + k, n_done, len(w["inventory"]))
                        nxt = w["trajectory"]["steps"][w["cut"] + k]
                        w_k["hidden"] = dict(w["hidden"], next_action=f"{nxt['type']}:{nxt['section']}:{nxt['slot']}", next_type=nxt["type"], next_section=nxt["section"],
                                             unavailable_ids=[a for a in (W.action_id(x) for x in w_k["state_at_cut"]["pending"]) if a not in w_k["state_at_cut"]["subjective_action_space"]],
                                             stop_next=w["trajectory"]["stopped_at"] == w["cut"] + k)
                        cond = E.build_condition(spec["condition"], ES._opaque(w["lid"]) + str(k), "P09")
                        ev = W.visible_evidence(w_k, cond)
                        b = W.oracle_bundle(w_k, cond)
                        task = {"arm": arm, "model": reader or "", "seed": SEED + k, "withheld": list(C.ALL7), "targets": ["next_action"]}
                        cap = RT.materialize(run.cell_id, f"{w['lid'].replace('|', '-')}__{arm}__{(reader or 'x').split('/')[-1]}__{k}", ev, task, E.dom_params())
                        res = RT.run_capsule(cap, server.endpoint, server.token, reader or "", timeout_s=900)
                        pred = res.get("prediction")
                        sc = PS.score(pred, b)["next_action_ls"] if pred and not validate_prediction(pred) else None
                        per.append({"k": k, "ls": sc})
                        for kk, v in ((pred or {}).get("compute") or {}).items():
                            budget[kk] = (budget.get(kk) or 0) + (v or 0)
                        RT.cleanup_unit(cap)
                    vals = [p["ls"] for p in per if p["ls"] is not None]
                    total = sum(vals) if vals else None
                    run.row(w["lid"], reader=reader, arm=arm, factors={"domain": w["domain"], "n_events": len(vals)},
                            scores={"tail_sum_ls": total, "per_event": per, "n_events": len(vals)}, primary_score=total,
                            valid=total is not None, validity_reason="ok" if total is not None else "no scored events", budget=budget)
                    run.unit_complete(reader, w["lid"], arm)
    rows = run.rows()
    cells = {}
    for arm in ("SLJ", "DIR"):
        for k, v in ES._contrast_by_reader(run, rows, arm, "DOM", threshold=0.05).items():
            cells[f"{arm}|{k}"] = v
    loc = {}
    for arm in arms:
        rr = E.rows_valid(rows, arm=arm)
        by_k: dict = {}
        for r in rr:
            for p in r["scores"]["per_event"]:
                if p["ls"] is not None:
                    by_k.setdefault(p["k"], []).append(p["ls"])
        loc[arm] = {k: sum(v) / len(v) for k, v in sorted(by_k.items())}
    return ES._finish_contrast(run, cells, {"localization_by_event": loc, "skipped_terminal_cuts": skipped_terminal,
                                            "note": "teacher-forced sequential scoring over up to four tail events"})


def run_P10(run: CardRun7) -> int:
    rows = [r for r in run.rows_of("R13") if r.get("valid")] if (E.S7 / "R13" / "cases.jsonl").exists() else []
    r16 = [r for r in run.rows_of("R16") if r.get("valid")] if (E.S7 / "R16" / "cases.jsonl").exists() else []
    out = {}
    for arm in ("SLJ", "DIR", "DOM"):
        rr = [r for r in rows if r["arm"] == arm]
        out[arm] = {"reliability": {k: v for k, v in CAL.reliability(rr).items() if k != "bins"}, "risk_coverage": CAL.risk_coverage(rr),
                    "by_dose": CAL.by_dose(rr), "class_coverage": CAL.class_coverage(rr + [r for r in r16 if r["arm"] == arm])}
    return E._finish_desc(run, {"by_arm": out}, json.dumps({a: v["reliability"].get("ece") for a, v in out.items()}), outcome="DESCRIPTIVE" if rows else "VOID")


# ── P11/P12/B03: histories ────────────────────────────────────────────────────────────

def history_batch(run: CardRun7, kinds: list[str], interfaces: list[str], arms: list[str], n: int, offset: int = 0,
                  stack_weights: dict | None = None) -> None:
    with E.ModelServer(f"s7_{run.card.lower()}", run.readers if "HDIR" in arms else []) as server:
        for kind in kinds:
            for hid in MC.history_ids(run.card, kind, n, split=run.split, offset=offset):
                run.check_deadline()
                h = MC.unit(hid, kind)
                run.register_world(hid, {"hid": hid, "kind": kind, "n": h["n"]})
                for iface in interfaces:
                    ev = MC.visible_evidence(h, iface, unit_ref=ES._opaque(hid), condition_ref=run.card)
                    b = MC.oracle_bundle(h, iface)
                    uid = hid if iface == "process" else f"{hid}|final"
                    for arm in arms:
                        for reader in (run.readers if arm == "HDIR" else [None]):
                            if run.is_done(reader, uid, arm):
                                continue
                            task = {"arm": arm, "model": reader or "", "seed": SEED, "stack_weights": stack_weights or {"style": 0.5, "pers": 0.5}}
                            cap = RT.materialize(run.cell_id, f"{hid.replace('|', '-')}__{iface}__{arm}__{(reader or 'x').split('/')[-1]}", ev, task, None)
                            res = RT.run_capsule(cap, server.endpoint, server.token, reader or "", timeout_s=900)
                            pred = res.get("prediction")
                            valid = pred is not None and not validate_prediction(pred)
                            sc = {}
                            if valid:
                                post = pred["targets"]["change_point"]
                                truth = h["truth"]["change_point"]
                                sc = {"cp_ls": CP.changepoint_ls(post, truth), "abs_error": CP.expected_abs_error(post, truth, h["n"]),
                                      "tol2": CP.tolerance_hit(post, truth, 2), "type_ls": math.log(max(float(pred["targets"]["change_type"].get(h["truth"]["type"], 0.0)), 1e-9)),
                                      "oracle_cp_ls": CP.changepoint_ls(b["oracle_posterior"], truth), "none_mass": float(post.get("none", 0.0))}
                            pref = run.save_prediction(uid, arm, reader, pred) if pred else None
                            ORC.save(run.cell_id, uid.replace("|", "-"), b, ev)
                            run.row(uid, reader=reader, arm=arm, factors={"kind": kind, "interface": iface, "n_events": h["n"]},
                                    truth=str(h["truth"]["change_point"]), scores=sc, primary_score=sc.get("cp_ls"), valid=valid,
                                    validity_reason="ok" if valid else f"no prediction: {(res.get('error') or {}).get('error', '')[:120]}",
                                    budget=(pred or {}).get("compute"), evidence_sha=evidence_sha(ev), pred_ref=pref,
                                    extra={"canonical_sha": prediction_sha(pred) if pred else None})
                            run.unit_complete(reader, uid, arm)
                            RT.cleanup_unit(cap)
    update_registry("COMPUTE_LEDGER", lambda led: {**led, run.cell_id.replace("/", "_"): {"ledger": server.ledger, "gpu_held_s": server.held_s, "at": E.now_iso()}})


def _stack_weights(rows: list[dict]) -> dict:
    """The strongest stacked surface baseline frozen in discovery: the style/persistence
    mix with the best mean change-point score on the discovery rows."""
    best, bw = -1e9, {"style": 0.5, "pers": 0.5}
    for ws in (0.0, 0.25, 0.5, 0.75, 1.0):
        s = E.mean_score([r for r in rows if r["arm"] == "HSTYLE" and r.get("valid")]) or -1e9
        p = E.mean_score([r for r in rows if r["arm"] == "HPERS" and r.get("valid")]) or -1e9
        v = ws * s + (1 - ws) * p
        if v > best:
            best, bw = v, {"style": ws, "pers": 1 - ws}
    return bw


def run_P11(run: CardRun7) -> int:
    spec = C.ALL["P11"]
    n = E.n_units("P11") // len(spec["factors"]["kind"]) or 1
    history_batch(run, spec["factors"]["kind"], ["process"], [a for a in spec["arms"] if a != "HSTACK"], n)
    rows = run.rows()
    frozen = update_registry("DOM_FROZEN", lambda f: f if "history_stack" in f else {**f, "history_stack": _stack_weights(rows)})
    history_batch(run, spec["factors"]["kind"], ["process"], ["HSTACK"], n, stack_weights=frozen["history_stack"])
    rows = run.rows()
    switch_rows = [r for r in rows if r["factors"].get("kind") in ("human_then_model", "model_then_human", "alternating_normalized")]
    cells = {}
    for arm in ("HPROC", "HDIR"):
        for k, v in ES._contrast_by_reader(run, switch_rows, arm, "HSTACK", threshold=0.1).items():
            cells[f"{arm}|{k}"] = v
    by_kind = {}
    for kind in spec["factors"]["kind"]:
        sub = [r for r in rows if r["factors"].get("kind") == kind]
        by_kind[kind] = {a: {"cp_ls": E.mean_score(E.rows_valid(sub, arm=a)), "abs_error": E.mean_score(ES._score_key(E.rows_valid(sub, arm=a), "abs_error")),
                             "tol2": E.mean_score([dict(r, primary_score=1.0 if r["scores"].get("tol2") else 0.0) for r in E.rows_valid(sub, arm=a)]),
                             "none_mass": E.mean_score(ES._score_key(E.rows_valid(sub, arm=a), "none_mass"))} for a in spec["arms"]}
    return ES._finish_contrast(run, cells, {"by_kind": by_kind, "stack_weights": frozen["history_stack"], "oracle_cp_ls": E.mean_score(ES._score_key(switch_rows, "oracle_cp_ls"))}, gate="discontinuity")


def run_P12(run: CardRun7) -> int:
    spec = C.ALL["P12"]
    n = E.n_units("P12") // 2 or 1
    frozen = read_registry("DOM_FROZEN") or {}
    history_batch(run, spec["factors"]["kind"], spec["factors"]["interface"], spec["arms"], n, offset=500, stack_weights=frozen.get("history_stack"))
    rows = run.rows()
    matched = [r for r in rows if r["factors"].get("kind") == "style_matched_switch" and r["factors"].get("interface") == "process"]
    shift = [r for r in rows if r["factors"].get("kind") == "style_shift_no_switch" and r["factors"].get("interface") == "process"]
    cells = {}
    for arm in ("HPROC", "HDIR"):
        for k, v in ES._contrast_by_reader(run, matched, arm, "HSTACK", threshold=0.1).items():
            cells[f"matched|{arm}|{k}"] = v
    shift_gain = {a: {k: v.get("point") for k, v in ES._contrast_by_reader(run, shift, a, "HU", threshold=0.1).items()} for a in ("HPROC", "HDIR", "HSTYLE")}
    style_catches_shift = E.mean_score([dict(r, primary_score=1.0 if r["scores"].get("none_mass", 1.0) < 0.5 else 0.0) for r in E.rows_valid(shift, arm="HSTYLE")])
    process_ignores_shift = E.mean_score(ES._score_key(E.rows_valid(shift, arm="HPROC"), "none_mass"))
    final_only = {a: E.mean_score(E.rows_valid([r for r in rows if r["factors"].get("interface") == "final_only"], arm=a)) for a in spec["arms"]}
    crossover = {"matched_switch_gain": {k: v.get("point") for k, v in cells.items()}, "style_shift_no_switch_gain_over_uniform": shift_gain,
                 "stylometry_fires_on_style_shift": style_catches_shift, "process_none_mass_on_style_shift": process_ignores_shift}
    return ES._finish_contrast(run, cells, {"crossover": crossover, "final_only_interface": final_only, "n_matched": len(matched), "n_shift": len(shift)},
                               gate="style_crossover", extra_reason=f"stylometry fires on the style shift {style_catches_shift}; the process reader's none-mass there {process_ignores_shift}")


# ── P13: CoAuthor after the loader repair ────────────────────────────────────────────

def _coauthor_items(session: dict) -> list[dict]:
    items = []
    prior = []
    for e in session["events"]:
        if e.get("decided") not in CA.DECISIONS:
            continue
        items.append({"doc_tail": e["doc_tail"], "doc_len": e["doc_len"], "suggestion": e["suggestions"], "prior_decisions": list(prior[-8:]), "truth": e["decided"]})
        prior.append(e["decided"])
    return items


def run_P13(run: CardRun7) -> int:
    spec = C.ALL["P13"]
    if not (gate_state("coauthor_loader") or {}).get("passed"):
        return E._finish_desc(run, {"gate": gate_state("coauthor_loader")}, "the loader gate (D07) is not passed; no scoring", outcome="NOT_RUN")
    n = E.n_units("P13")
    sessions = CA.coauthor_sessions(max_sessions=None, lane=run.split if run.split != "pilot" else "discovery")
    sessions = sessions[:n]
    disc = CA.coauthor_sessions(max_sessions=200, lane="discovery")
    table: dict = {}
    for s in disc:
        for it in _coauthor_items(s):
            b = "short" if it["doc_len"] < 800 else ("mid" if it["doc_len"] < 2000 else "long")
            table.setdefault(b, {d: 1 for d in CA.DECISIONS})
            table[b][it["truth"]] += 1
    table = {b: {d: v / sum(c.values()) for d, v in c.items()} for b, c in table.items()}
    table["all"] = {d: sum(c[d] for c in table.values()) / len(table) for d in CA.DECISIONS}
    with E.ModelServer("s7_p13", run.readers) as server:
        for s in sessions:
            run.check_deadline()
            items = _coauthor_items(s)[:12]
            run.register_world(s["session_id"], {"session": s["session_id"], "n_items": len(items)})
            for arm in spec["arms"]:
                for reader in (run.readers if arm == "CDIR" else [None]):
                    if run.is_done(reader, s["session_id"], arm):
                        continue
                    ls = []
                    correct = 0
                    budget: dict = {}
                    for j, it in enumerate(items):
                        ev = {"version": EVIDENCE_VERSION, "unit_ref": ES._opaque(s["session_id"]) + str(j), "condition_ref": "P13", "domain": "coauthor",
                              "regime": "cold", "render": "log",
                              "history": {"interface": "coauthor", "doc_tail": it["doc_tail"], "doc_len": it["doc_len"], "suggestion": it["suggestion"], "prior_decisions": it["prior_decisions"]},
                              "query": {"decision_options": list(CA.DECISIONS)}}
                        task = {"arm": arm, "model": reader or "", "seed": SEED + j, "position_table": table}
                        cap = RT.materialize(run.cell_id, f"{ES._opaque(s['session_id'])}__{arm}__{(reader or 'x').split('/')[-1]}__{j}", ev, task, None)
                        res = RT.run_capsule(cap, server.endpoint, server.token, reader or "", timeout_s=600)
                        pred = res.get("prediction")
                        if pred and not validate_prediction(pred):
                            d = pred["targets"]["decision"]
                            ls.append(math.log(max(float(d.get(it["truth"], 0.0)), 1e-9)))
                            correct += int(max(d, key=d.get) == it["truth"])
                            for kk, v in (pred.get("compute") or {}).items():
                                budget[kk] = (budget.get(kk) or 0) + (v or 0)
                        RT.cleanup_unit(cap)
                    run.row(s["session_id"], reader=reader, arm=arm, factors={"n_items": len(items), "lane": s["lane"]},
                            scores={"mean_ls": sum(ls) / len(ls) if ls else None, "accuracy": correct / len(ls) if ls else None, "n": len(ls)},
                            primary_score=sum(ls) / len(ls) if ls else None, valid=bool(ls), budget=budget)
                    run.unit_complete(reader, s["session_id"], arm)
    rows = run.rows()
    cells = {}
    for rival in ("CPOS", "CPRIOR"):
        for k, v in ES._contrast_by_reader(run, rows, "CDIR", rival, threshold=0.03).items():
            cells[f"vs{rival}|{k}"] = v
    marg = {d: 0 for d in CA.DECISIONS}
    for s in sessions:
        for it in _coauthor_items(s)[:12]:
            marg[it["truth"]] += 1
    return ES._finish_contrast(run, cells, {"position_table": table, "decision_marginal": marg, "n_sessions": len(sessions), "means": {a: E.mean_score(E.rows_valid(rows, arm=a)) for a in spec["arms"]}})


# ── P14: ScholaWrite switches ────────────────────────────────────────────────────────

def run_P14(run: CardRun7) -> int:
    spec = C.ALL["P14"]
    n = E.n_units("P14") // 2 or 1
    with E.ModelServer("s7_p14", run.readers) as server:
        for protocol in spec["factors"]["protocol"]:
            sessions = SW.sessions(protocol=protocol, lane=run.split if run.split != "pilot" else "discovery")[:n]
            disc = SW.sessions(protocol=protocol, lane="discovery")
            rate = sum(1 - s["switch_rate"] for s in disc) / max(1, len(disc)) if disc else 0.8
            for s in sessions:
                run.check_deadline()
                items = SW.switch_items(s)[:10]
                if not items:
                    continue
                run.register_world(s["session_id"], {"session": s["session_id"], "protocol": protocol, "n_items": len(items)})
                for arm in spec["arms"]:
                    for reader in (run.readers if arm == "SDIR" else [None]):
                        uid = f"{s['session_id']}|{protocol}"
                        if run.is_done(reader, uid, arm):
                            continue
                        ls_all, ls_switch = [], []
                        budget: dict = {}
                        for j, it in enumerate(items):
                            ev = {"version": EVIDENCE_VERSION, "unit_ref": ES._opaque(uid) + str(j), "condition_ref": "P14", "domain": "scholawrite",
                                  "regime": "cold", "render": "log",
                                  "history": {"interface": "scholawrite", "window": it["context"], "current_category": it["current"]},
                                  "query": {"category_options": list(SW.CATEGORIES)}}
                            task = {"arm": arm, "model": reader or "", "seed": SEED + j, "persistence_rate": rate}
                            cap = RT.materialize(run.cell_id, f"{ES._opaque(uid)}__{arm}__{(reader or 'x').split('/')[-1]}__{j}", ev, task, None)
                            res = RT.run_capsule(cap, server.endpoint, server.token, reader or "", timeout_s=600)
                            pred = res.get("prediction")
                            if pred and not validate_prediction(pred):
                                d = pred["targets"]["next_category"]
                                v = math.log(max(float(d.get(it["next"], 0.0)), 1e-9))
                                ls_all.append(v)
                                if it["switch"]:
                                    ls_switch.append(v)
                                for kk, x in (pred.get("compute") or {}).items():
                                    budget[kk] = (budget.get(kk) or 0) + (x or 0)
                            RT.cleanup_unit(cap)
                        run.row(uid, reader=reader, arm=arm, factors={"protocol": protocol, "n_items": len(ls_all), "n_switch": len(ls_switch)},
                                scores={"mean_ls": sum(ls_all) / len(ls_all) if ls_all else None, "switch_ls": sum(ls_switch) / len(ls_switch) if ls_switch else None},
                                primary_score=sum(ls_switch) / len(ls_switch) if ls_switch else None, valid=bool(ls_switch),
                                validity_reason="ok" if ls_switch else "no switch positions", budget=budget)
                        run.unit_complete(reader, uid, arm)
    rows = run.rows()
    cells = {}
    for protocol in spec["factors"]["protocol"]:
        sub = [r for r in rows if r["factors"].get("protocol") == protocol]
        for k, v in ES._contrast_by_reader(run, sub, "SDIR", "SPERS", threshold=0.03).items():
            cells[f"{protocol}|{k}"] = v
    overall = {a: E.mean_score(ES._score_key(E.rows_valid(rows, arm=a), "mean_ls")) for a in spec["arms"]}
    return ES._finish_contrast(run, cells, {"switch_conditioned": True, "overall_means": overall, "kept_fraction": sum(1 for r in rows if r.get("valid")) / max(1, len(rows))})


# ── V: bounded attention/history ─────────────────────────────────────────────────────

def run_V01(run: CardRun7) -> int:
    spec = C.ALL["V01"]
    for residue in spec["factors"]["residue"]:
        for opposes in spec["factors"]["goal_opposes"]:
            goal = ("audit" if residue == "habit_write" else "produce") if opposes == "yes" else ("produce" if residue == "habit_write" else "audit")
            ES.batch(run, spec["arms"], run.readers, spec["condition"], max(4, E.n_units("V01") // 4), "worlds_V", targets=spec["targets"],
                     forced={"residue": residue, "goal": goal}, offset=100 * (spec["factors"]["residue"].index(residue) * 2 + spec["factors"]["goal_opposes"].index(opposes)),
                     factors_of=lambda w, r_=residue, o_=opposes: {"residue": r_, "goal_opposes": o_})
    rows = run.rows()
    floor, g = ES._gate_floor(rows)
    cells = {}
    for opposes in spec["factors"]["goal_opposes"]:
        sub = [r for r in rows if r["arm"] in ("DOM", "OR") or r["factors"].get("goal_opposes") == opposes]
        for k, v in ES._contrast_by_reader(run, sub, "SLJ", "DOM", threshold=floor).items():
            cells[f"opposes={opposes}|{k}"] = v
    return ES._finish_contrast(run, cells, {"oracle_gap": g, "floor": floor, "recall_goal": ES._recall(run, "proximal_goal"), "recall_residue": ES._recall(run, "history_residue"),
                                            "note": "present choice (next action) and compiled residue (the residue marginal) scored apart"})


def run_V02(run: CardRun7) -> int:
    spec = C.ALL["V02"]
    ES.batch(run, spec["arms"] + ["DOM"], run.readers, spec["condition"], E.n_units("V02"), "worlds_V", targets=spec["targets"], offset=500)
    rows = run.rows()
    floor, g = ES._gate_floor(rows)
    cells = ES._contrast_by_reader(run, rows, "SLJ", "GBLIND", threshold=floor)
    return ES._finish_contrast(run, cells, {"oracle_gap": g, "floor": floor, "gblind_mean": E.mean_score(E.rows_valid(rows, arm="GBLIND")), "vs_dom": ES._contrast_by_reader(run, rows, "SLJ", "DOM", threshold=floor)})


def run_V03(run: CardRun7) -> int:
    spec = C.ALL["V03"]
    for conflict in spec["factors"]["conflict"]:
        forced = {"law_name": "specialist", "goal": "produce"} if conflict == "opposed" else {"law_name": "specialist", "goal": "attribute"}
        ES.batch(run, spec["arms"], run.readers, spec["condition"], max(4, E.n_units("V03") // 2), "worlds_V", targets=spec["targets"], forced=forced,
                 offset=800 + 100 * spec["factors"]["conflict"].index(conflict), factors_of=lambda w, c_=conflict: {"conflict": c_})
    rows = run.rows()
    floor, g = ES._gate_floor(rows)
    cells = {}
    for conflict in spec["factors"]["conflict"]:
        sub = [r for r in rows if r["arm"] in ("DOM", "OR") or r["factors"].get("conflict") == conflict]
        for k, v in ES._contrast_by_reader(run, sub, "SLJ", "DOM", threshold=floor).items():
            cells[f"{conflict}|{k}"] = v
    return ES._finish_contrast(run, cells, {"oracle_gap": g, "floor": floor, "recall_goal": ES._recall(run, "proximal_goal"), "recall_law": ES._recall(run, "expertise_law")})


def _dated_hook(w: dict, ev: dict) -> dict:
    """V04-V06: the demonstrations become a DATED series under a drifting law: the two
    oldest under a different law, the newest under the present law, with ages."""
    demos = ev.get("demonstrations") or []
    names = w["state"]["names"]
    other = W.LAW_NAMES[(W.LAW_NAMES.index(names["law"]) + 1) % len(W.LAW_NAMES)]
    out = []
    n = len(demos)
    for i, d in enumerate(demos):
        lid = f"{w['lid']}|dated{i}"
        doc = W._doc_plan(lid, w["domain"])
        inv = W._inventory(lid, doc)
        law = other if i < n // 2 else names["law"]
        st = W.make_state(lid, doc, inv, W.GOALS[(i + 1) % 4], law, "accurate", "none", names["tendency"])
        traj = W.simulate(lid, doc, inv, st, salt="dated")
        pre = [{"step": s["i"], "type": s["type"], "section": s["section"], "slot": s["slot"], "outcome": s["outcome"]} for s in traj["steps"]]
        out.append({"episode_ref": f"dated-{i + 1}", "topic": doc["topic"], "sections": [s["name"] for s in doc["sections"]], "events": pre,
                    "text": W.render_prefix_text(pre, "log", doc["topic"]), "age_days": float(30 * (n - i)), "date_rank": i})
    ev2 = dict(ev)
    ev2["demonstrations"] = out
    return ev2


def run_V04(run: CardRun7) -> int:
    spec = C.ALL["V04"]
    ES.batch(run, spec["arms"], [], spec["condition"], E.n_units("V04"), "worlds_V", targets=spec["targets"], offset=1200, evidence_hook=_dated_hook)
    rows = run.rows()
    # the mixture's weight on the present-law demos versus the point's single demo
    mix_scores = []
    for r in E.rows_valid(rows, arm="MIX"):
        m = ((r.get("extra") or {}).get("notes") or {}).get("mixture") or {}
        n = len(m)
        present = sum(v for k, v in m.items() if int(k.split("-")[-1]) > n // 2)
        mix_scores.append(present)
    cells = ES._contrast_by_reader(run, rows, "MIX", "POINT", threshold=0.03)
    return ES._finish_contrast(run, cells, {"mixture_mass_on_present_law_demos": sum(mix_scores) / len(mix_scores) if mix_scores else None,
                                            "note": "forced point dating is the rival; the mixture is scored on the present episode"})


def run_V05_V06(run: CardRun7) -> int:
    spec = C.ALL[run.card]
    ES.batch(run, spec["arms"] + ["DOM"], [], spec["condition"], E.n_units(run.card), "worlds_V", targets=spec["targets"],
             offset=1600 if run.card == "V05" else 2000, evidence_hook=_dated_hook)
    rows = run.rows() if run.card == "V05" else ES._score_key(run.rows(), "changed_context_ls")
    floor, g = ES._gate_floor(rows)
    cells = ES._contrast_by_reader(run, rows, "DATED", "AGG", threshold=floor)
    extra = {"oracle_gap": g, "floor": floor}
    if run.card == "V05":
        extra["ordered_vs_agg"] = ES._contrast_by_reader(run, rows, "ORDERED", "AGG", threshold=floor)
        extra["dated_vs_ordered"] = ES._contrast_by_reader(run, rows, "DATED", "ORDERED", threshold=floor)
    else:
        extra["dated_vs_sol_ceiling"] = ES._contrast_by_reader(run, rows, "DATED", "SOL", threshold=0.03)
        extra["dated_vs_dom"] = ES._contrast_by_reader(run, rows, "DATED", "DOM", threshold=floor)
    return ES._finish_contrast(run, cells, extra, gate="dated_history" if run.card == "V05" else None)


def run_card(run: CardRun7) -> int:
    card = run.card
    if card in P_KEY:
        return run_P_analysis(run)
    if card == "P09":
        return run_P09(run)
    if card == "P10":
        return run_P10(run)
    if card == "P11":
        return run_P11(run)
    if card == "P12":
        return run_P12(run)
    if card == "P13":
        return run_P13(run)
    if card == "P14":
        return run_P14(run)
    if card == "V01":
        return run_V01(run)
    if card == "V02":
        return run_V02(run)
    if card == "V03":
        return run_V03(run)
    if card == "V04":
        return run_V04(run)
    if card in ("V05", "V06"):
        return run_V05_V06(run)
    raise ValueError(card)
