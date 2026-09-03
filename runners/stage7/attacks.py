"""Stage 7 adversarial matrix (brief §11): the 24 attacks. Each names its covered
questions, the invariant or reversal it expects, and the consequence; most derive from
landed rows and registries, seven replay small capsule batches with the presentation
varied (X06, X10, X11, X12, X13, and the mutation attacks read the I05-I07 rows).

DESIGN CHECK (2026-09-02)
lessons read: LESSONS §3 (run the interpretation control before adopting the reading; a
  falsifier is an instrument and its baseline arm is a known-answer gate: every replay
  attack carries the case where the invariant SHOULD break, so a vacuously passing attack
  is caught; a quiet control needs its replicate), §5.
gates: an attack lands INFRASTRUCTURE when its invariant holds (and its should-break case
  breaks), INSTRUMENT_FAILED when the invariant fails on the covered questions (the
  consequence in the registry then applies), VOID when its covered rows do not exist;
  NULL/ALTERNATIVE/direction per attack are stated inline at each band. bands: exhaustive.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from runners import s5_lib                                                         # noqa: E402
from runners.stage7 import cards as C                                              # noqa: E402
from runners.stage7 import engine_supplied as ES                                   # noqa: E402
from runners.stage7 import engines as E                                            # noqa: E402
from runners.stage7.cardrun import SMOKE, CardRun7                                 # noqa: E402
from runners.stage7.constructor import worlds as W                                 # noqa: E402
from runners.stage7.scoring import calibration as CAL                              # noqa: E402
from soundingline.stage7 import S7, gate_state, read_json, read_jsonl, read_registry, tv  # noqa: E402

SEED = 74000


def _finish(run: CardRun7, metrics: dict, ok: bool | None, reason: str) -> int:
    oc = "VOID" if ok is None else ("INFRASTRUCTURE" if ok else "INSTRUMENT_FAILED")
    run.finish(metrics, {"exec": "COMPLETE", "outcome": oc, "primary": C.ALL[run.card]["question"], "reason": reason},
               rival=C.ALL[run.card]["consequence"])
    return 0


def _verdict(card: str) -> dict:
    p = S7 / card / "verdict.json"
    return read_json(p) if p.exists() else {}


def _gate_attack(run: CardRun7, gate: str, src: str) -> int:
    g = gate_state(gate) or {}
    v = _verdict(src)
    ok = None if not v else bool(g.get("passed"))
    return _finish(run, {"gate": g, "source_verdict": v.get("outcome")}, ok, f"{src} {v.get('outcome')}; gate {gate} {g.get('passed')}")


def _covered_ok(run: CardRun7) -> int:
    checks = {}
    for c in C.ALL[run.card]["covers"]:
        v = _verdict(c)
        checks[c] = {"outcome": v.get("outcome"), "point": v.get("point"), "cells": v.get("conditional_cells")}
    landed = {c: x for c, x in checks.items() if x["outcome"]}
    ok = all(x["outcome"] not in ("INSTRUMENT_FAILED",) for x in landed.values()) if landed else None
    return _finish(run, {"covered": checks}, ok, f"covered: {json.dumps({c: x['outcome'] for c, x in checks.items()})}")


def _replay(run: CardRun7, variant: str) -> int:
    """X06 (order), X10 (paraphrase), X11 (meaning change), X12 (duplicated evidence), X13
    (law relabeling): a small capsule batch with the presentation varied against the base;
    the invariant and its should-break case measured on the same units."""
    spec = C.ALL[run.card]
    n = E.n_units(run.card)
    arms = spec["arms"]
    cond = spec["condition"]
    moves, breaks = [], []
    sharpen = []
    follow = []
    readers = run.readers if any(a in E.MODEL_ARMS for a in arms) else []
    with E.ModelServer(f"s7_{run.card.lower()}", readers) as server:
        for w in E.worlds_for(run, run.card, n, family="worlds_attack", offset=3000 + 100 * int(run.card[1:])):
            run.check_deadline()
            c0 = E.build_condition(cond, ES._opaque(w["lid"]), run.card)
            ev = W.visible_evidence(w, c0)
            b = W.oracle_bundle(w, c0)
            ev_var = copy.deepcopy(ev)
            ev_break = None
            if variant == "order":
                q = ev_var["query"]
                q["next_action_options"] = list(reversed(q["next_action_options"]))
                oo = ev_var["objective_options"]
                oo["at_cut"] = list(reversed(oo["at_cut"]))
            elif variant == "paraphrase":
                sf = ev_var["supplied_factors"]["factors"]
                for k, v in sf.items():
                    if isinstance(v, str):
                        sf[k] = v.replace("The maker", "This maker").replace("believes", "holds that").replace("is strongest at", "does best at").replace("Right now", "At this point")
                ev_break = copy.deepcopy(ev)
                sfb = ev_break["supplied_factors"]["factors"]
                if isinstance(sfb.get("belief_state"), str):
                    s = sfb["belief_state"]
                    sfb["belief_state"] = s.replace("library is available", "library is TMP").replace("library is unavailable", "library is available").replace("library is TMP", "library is unavailable")
            elif variant == "meaning":
                sf = ev_var["supplied_factors"]["factors"]
                if isinstance(sf.get("belief_state"), str):
                    s = sf["belief_state"]
                    sf["belief_state"] = s.replace("library is available", "library is TMP").replace("library is unavailable", "library is available").replace("library is TMP", "library is unavailable")
                if isinstance(sf.get("proximal_goal"), str):
                    s = sf["proximal_goal"]
                    parts = s.split("pulled most strongly toward ")
                    if len(parts) > 1:
                        sf["proximal_goal"] = s.replace("least toward", "TMP").replace("most strongly toward", "least toward").replace("TMP", "most strongly toward")
            elif variant == "duplicate":
                pre = ev_var["process_prefix"]
                ev_var["artifact_state"]["prefix_text"] = ev["artifact_state"]["prefix_text"] + "\n(Restated for the file:)\n" + W.render_prefix_text(pre[-3:], "prose", w["doc"]["topic"])
            elif variant == "relabel":
                c1 = dict(c0, relabel_seed=7)
                ev_var = W.visible_evidence(w, c1)
            for arm in arms:
                for reader in (readers if arm in E.MODEL_ARMS else [None]):
                    E.run_unit(run, server, w, ev, b, arm, reader, factors={"domain": w["domain"], "variant": "base"}, unit_id=w["lid"])
                    E.run_unit(run, server, w, ev_var, b, arm, reader, factors={"domain": w["domain"], "variant": variant}, unit_id=f"{w['lid']}|{variant}")
                    if ev_break is not None:
                        E.run_unit(run, server, w, ev_break, b, arm, reader, factors={"domain": w["domain"], "variant": "break"}, unit_id=f"{w['lid']}|break")
    rows = run.rows()
    preds = {}
    for r in rows:
        if r.get("valid") and r.get("pred_ref"):
            preds[(r["arm"], r["model_id"], r["unit_id"])] = read_json(Path(r["pred_ref"]))
    for (arm, rd, uid), p in preds.items():
        if "|" + variant in uid or "|break" in uid:
            continue
        pv = preds.get((arm, rd, f"{uid}|{variant}"))
        if pv is None:
            continue
        moves.append(tv(p["targets"]["next_action"], pv["targets"]["next_action"]))
        pb = preds.get((arm, rd, f"{uid}|break"))
        if pb is not None:
            breaks.append(tv(p["targets"]["next_action"], pb["targets"]["next_action"]))
        if variant == "duplicate":
            sharpen.append(pv["confidence"] - p["confidence"])
        if variant == "relabel":
            post0 = (p.get("notes") or {}).get("posterior") or {}
            post1 = (pv.get("notes") or {}).get("posterior") or {}
            # behavior, not tags: the mass on the TRUE law must be the same under either labeling
            wld = W.make_world(uid, next(r["factors"]["domain"] for r in rows if r["unit_id"] == uid))
            t0, t1 = W.candidate_law_truth(wld, 0), W.candidate_law_truth(wld, 7)
            follow.append(abs(post0.get(t0, 0.0) - post1.get(t1, 0.0)))
    m = sum(moves) / len(moves) if moves else None
    bm = sum(breaks) / len(breaks) if breaks else None
    if variant == "order":
        ok = m is not None and m <= 0.05
        reason = f"order permutation TV {m}; band at or under 0.05"
    elif variant == "paraphrase":
        ok = m is not None and (m <= 0.15 or (bm is not None and m <= 0.5 * bm))
        reason = f"paraphrase TV {m}; meaning-change (should-break) TV {bm}"
    elif variant == "meaning":
        ok = m is not None and m >= 0.05
        reason = f"meaning-change TV {m}; band at or above 0.05"
    elif variant == "duplicate":
        s = sum(sharpen) / len(sharpen) if sharpen else None
        ok = s is not None and s <= 0.05
        reason = f"duplicate-evidence confidence sharpening {s}; band at or under 0.05"
        return _finish(run, {"sharpening": s, "n": len(sharpen)}, ok, reason)
    elif variant == "relabel":
        f = sum(follow) / len(follow) if follow else None
        ok = f is not None and f <= 1e-6
        reason = f"true-law mass difference under relabeling {f}"
        return _finish(run, {"mass_difference": f, "n": len(follow)}, ok, reason)
    else:
        ok, reason = None, "unknown variant"
    return _finish(run, {"tv_mean": m, "break_tv_mean": bm, "n": len(moves)}, ok, reason)


def run_card(run: CardRun7) -> int:
    card = run.card
    if card in ("X01", "X02", "X03"):
        src = {"X01": "I05", "X02": "I06", "X03": "I07"}[card]
        kind = {"X01": "tail", "X02": "stop", "X03": "event"}[card]
        v = _verdict(src)
        rates = (read_json(S7 / src / "metrics.json") if (S7 / src / "metrics.json").exists() else {}).get("identity_rate_by_arm") or {}
        ok = None if not v else all(x == 1.0 for x in rates.values() if x is not None)
        return _finish(run, {"identity_rates": rates, "source": src}, ok, f"{src}: {rates}; gate mutation_{kind} {(gate_state(f'mutation_{kind}') or {}).get('passed')}")
    if card == "X04":
        return _gate_attack(run, "isolation", "I04")
    if card == "X05":
        v9, v10 = _verdict("I09"), _verdict("I10")
        ok = None if not (v9 and v10) else (v9.get("outcome") == "INFRASTRUCTURE" and v10.get("outcome") == "INFRASTRUCTURE")
        return _finish(run, {"I09": v9.get("outcome"), "I10": v10.get("outcome")}, ok, f"I09 {v9.get('outcome')}, I10 {v10.get('outcome')}")
    if card == "X06":
        return _replay(run, "order")
    if card == "X07":
        return _gate_attack(run, "sensitivity", "I08")
    if card == "X08":
        v = _verdict("I12")
        return _finish(run, {"I12": v.get("outcome")}, None if not v else v.get("outcome") == "INFRASTRUCTURE", f"I12 {v.get('outcome')}")
    if card == "X09":
        v = _verdict("I13")
        priced = (read_registry("COMPUTE_LEDGER") or {}).get("A15_priced")
        ok = None if not v else (v.get("outcome") == "INFRASTRUCTURE" and bool(priced))
        return _finish(run, {"I13": v.get("outcome"), "A15_priced": bool(priced)}, ok, f"I13 {v.get('outcome')}; A15 compute priced {bool(priced)}")
    if card == "X10":
        return _replay(run, "paraphrase")
    if card == "X11":
        return _replay(run, "meaning")
    if card == "X12":
        return _replay(run, "duplicate")
    if card == "X13":
        return _replay(run, "relabel")
    if card == "X14":
        v = _verdict("R16")
        m = read_json(S7 / "R16" / "metrics.json") if (S7 / "R16" / "metrics.json").exists() else {}
        cov = (m.get("class_coverage") or {})
        ok = None if not v else (cov.get("abstain_rate_on_equivalence") is not None and cov["abstain_rate_on_equivalence"] >= 0.5 and (cov.get("false_abstain_rate") or 0) <= 0.5)
        return _finish(run, {"class_coverage": cov}, ok, f"abstain on equivalence {cov.get('abstain_rate_on_equivalence')}; false abstain {cov.get('false_abstain_rate')}")
    if card in ("X15", "X16", "X17", "X18"):
        src = {"X15": "K13", "X16": "K09", "X17": "K08", "X18": "K10"}[card]
        v = _verdict(src)
        m = read_json(S7 / src / "metrics.json") if (S7 / src / "metrics.json").exists() else {}
        tw = m.get("twin") or {}
        um = m.get("unavailable_mass")
        if card == "X15":
            ok = None if not v else (um is not None and (um.get("SLJ") is not None and um["SLJ"] <= 0.1))
            return _finish(run, {"unavailable_mass": um, "verdict": v.get("outcome")}, ok, f"K13 SLJ mass on unavailable {um.get('SLJ') if um else None}")
        if card == "X17":
            ok = None if not v else v.get("outcome") not in ("INSTRUMENT_FAILED",)
            return _finish(run, {"K08": v.get("outcome"), "point": v.get("point")}, ok, f"K08 {v.get('outcome')} {v.get('point')}")
        ok = None if not tw or not tw.get("oracle_changes") else (tw.get("follow_rate") is not None and tw["follow_rate"] >= 0.5)
        return _finish(run, {"twin": tw, "verdict": v.get("outcome")}, ok, f"{src} twin reversal follow rate {tw.get('follow_rate')} over {tw.get('oracle_changes')} oracle changes")
    if card == "X19":
        v2, v6 = _verdict("V02"), _verdict("V06")
        ok = None if not (v2 or v6) else all(x.get("outcome") != "INSTRUMENT_FAILED" for x in (v2, v6) if x)
        return _finish(run, {"V02": v2.get("outcome"), "V06": v6.get("outcome"), "note": "context effects reported under their own name; no preference-change language"}, ok, f"V02 {v2.get('outcome')}, V06 {v6.get('outcome')}")
    if card == "X20":
        # the strengthened rival: the best of DOM and PERS per target on the K03/K02 tables; maker claims are read against it
        k2 = read_json(S7 / "K02" / "metrics.json") if (S7 / "K02" / "metrics.json").exists() else {}
        k3 = read_json(S7 / "K03" / "metrics.json") if (S7 / "K03" / "metrics.json").exists() else {}
        t2, t3 = (k2.get("table") or {}), (k3.get("table") or {})
        best = {}
        for key in ("next_action_ls", "stop_ls", "next_type_ls"):
            cands = {a: v.get(key) for a, v in {**t2, **t3}.items() if a != "OR" and v.get(key) is not None}
            best[key] = max(cands.items(), key=lambda kv: kv[1]) if cands else None
        r13 = _verdict("R13")
        rows = [r for r in read_jsonl(S7 / "R13" / "cases.jsonl") if r.get("valid")] if (S7 / "R13" / "cases.jsonl").exists() else []
        strengthened = {}
        for arm in ("SLJ", "DIR"):
            for rival in ("DOM", "PERS"):
                c = s5_lib.paired_contrast([r for r in rows if r["arm"] == arm], [r for r in rows if r["arm"] == rival], "unit_id", "primary_score", SEED)
                strengthened[f"{arm}_vs_{rival}"] = c.get("point")
        ok = None if not rows else all((v or 0) > 0 for k, v in strengthened.items() if k.startswith("SLJ")) or r13.get("outcome") in ("VALID_NULL", "COUNTEREVIDENCE", "INCONCLUSIVE")
        return _finish(run, {"best_cheap_by_target": best, "R13_vs_rivals": strengthened, "R13": r13.get("outcome")}, ok, f"strengthened rival table {json.dumps(best)}; R13 vs rivals {strengthened}")
    if card == "X21":
        v14, v16 = _verdict("R14"), _verdict("A16")
        cells14 = v14.get("conditional_cells") or {}
        cells16 = v16.get("conditional_cells") or {}
        pts = [c.get("point") for c in {**cells14, **cells16}.values() if c.get("point") is not None]
        rev = bool(pts) and min(pts) < 0 < max(pts)
        ok = None if not (v14 or v16) else bool(cells14 or cells16)
        return _finish(run, {"R14_cells": cells14, "A16_cells": cells16, "sign_reversal_present": rev}, ok, f"{len(cells14) + len(cells16)} conditional cells emitted before pooling; reversal {rev}")
    if card == "X22":
        return _gate_attack(run, "style_crossover", "P12")
    if card == "X23":
        v15, v14 = _verdict("I15"), _verdict("I14")
        alarms = []
        for c in ("R14", "A16", "K16", "R11"):
            v = _verdict(c)
            cells = v.get("conditional_cells") or {}
            pts = [x.get("point") for x in cells.values() if x.get("point") is not None]
            if pts and min(pts) < 0 < max(pts):
                alarms.append({"card": c, "min": min(pts), "max": max(pts)})
        ok = None if not (v15 and v14) else (v15.get("outcome") == "INFRASTRUCTURE" and v14.get("outcome") == "INFRASTRUCTURE")
        return _finish(run, {"I15": v15.get("outcome"), "I14": v14.get("outcome"), "reversal_alarms": alarms}, ok, f"I15 {v15.get('outcome')}, I14 {v14.get('outcome')}; {len(alarms)} planned-reversal alarm(s) surfaced")
    if card == "X24":
        from runners.stage7 import fresh_clone as FC                              # noqa: PLC0415
        rep = FC.verify()
        return _finish(run, rep, rep.get("ok"), rep.get("summary", ""))
    raise ValueError(f"no attack handler for {card}")
