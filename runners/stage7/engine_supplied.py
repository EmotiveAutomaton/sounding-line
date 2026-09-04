"""Stage 7 supplied-state, reconstruction, and architecture trunks (brief §4, §8, §10 K/R/A,
§12.2, §16.2). Every question runs the shared batch: constructed worlds on its lineage
family, one visible evidence per unit under the question's condition, every arm in its
own capsule, the oracle bundle outside, scores at the unit, and the verdict on a paired
contrast at the world with the cluster interval, reader by reader BEFORE any pooling
(X21). The capability ratios (U_state, R_j) are void under the minimum oracle gap.

DESIGN CHECK (2026-09-02)
lessons read: LESSONS §3 (blind floors follow the truth marginal: U, PERS, DOM rows sit
  beside every arm; the paired contrast is on the estimand's own per-unit quantity; the
  per-item best of comparators is never the comparator; candidate generation is scored
  apart from selection; the matched comparator and the plain route both reported; every
  statistic a verdict rests on is written), §4 (instruct readers only), §5 (one GPU
  session per invocation).
gates and bands:
  - K01 (construction): NULL of a dead ruler is a mean oracle-minus-DOM gap under
    MIN_GAP_NATS on next action or on stopping (fails DOWN to INSTRUMENT_FAILED, the
    ladder closes for that target); ALTERNATIVE: both at or above the floor.
  - K04 (supplied state): NULL of an unusable interface is a paired DIR-minus-DOM gain
    whose interval covers zero or sits under the 20-percent-of-gap floor (VALID_NULL or
    INCONCLUSIVE by the exhaustive Stage-5 bands); ALTERNATIVE: the interval above the
    floor (SUPPORT_CANDIDATE); failure direction: DOWN; the gate opens on any reader.
  - K11-K14 (inference rungs): the same bands on SLJ-minus-DOM with the factor posterior
    on truth reported beside, never substituted.
  - R01-R05 (recall): NULL of absent candidates is recall under 0.5 (fails DOWN: the
    selection questions that depend on it are bounded); ALTERNATIVE: at or above 0.5.
  bands: the Stage-5 exhaustive outcome bands (SUPPORT_CANDIDATE / COUNTEREVIDENCE /
  VALID_NULL / INCONCLUSIVE / INSTRUMENT_FAILED / VOID / DESCRIPTIVE / INFRASTRUCTURE).
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from runners import s5_lib                                                         # noqa: E402
from runners.stage7 import cards as C                                              # noqa: E402
from runners.stage7 import engines as E                                            # noqa: E402
from runners.stage7.cardrun import SMOKE, CardRun7                                 # noqa: E402
from runners.stage7.constructor import worlds as W                                 # noqa: E402
from runners.stage7.reader import law as LAW                                       # noqa: E402
from runners.stage7.scoring import calibration as CAL                              # noqa: E402
from soundingline.stage7 import (DEFAULT_GAIN_FLOOR, MIN_GAP_NATS, gate_state,      # noqa: E402
                                 read_registry, set_gate, u_state, r_ratio, write_registry, update_registry)

SEED = 72000


def _opaque(lid: str) -> str:
    return "u" + hashlib.sha256(lid.encode()).hexdigest()[:10]


def _alt(names: dict, factor: str) -> str:
    grid = {"goal": list(LAW.GOALS), "belief": list(W.BELIEFS), "law": list(W.LAW_NAMES), "residue": list(W.RESIDUES)}[factor]
    cur = names[factor]
    return grid[(grid.index(cur) + 1) % len(grid)]


def batch(run: CardRun7, arms: list[str], readers: list[str], cond_spec: dict, n: int, family: str,
          targets: list | None = None, forced: dict | None = None, twin: str | None = None,
          offset: int = 0, regime: str | None = None, task_extra: dict | None = None,
          evidence_hook=None, factors_of=None, worlds: list[dict] | None = None,
          unit_suffix: str | None = None) -> list[dict]:
    """The shared batch. Returns the worlds used. `twin` runs every arm on the world's
    factor twin as well (unit_id = the twin's lid, pair = 'twin'). `evidence_hook(w, ev)`
    may alter the evidence per unit (a condition variant). `factors_of(w)` adds factors.
    `unit_suffix` is appended to every unit id (every arm, the twins, the oracle rows) when
    the same worlds are crossed with a condition such as a regime: without it the done-check
    treats the second crossing as already run (R14's first landing)."""
    model_readers = readers if any(a in E.MODEL_ARMS for a in arms) else []
    used = []
    with E.ModelServer(f"s7_{run.card.lower()}", model_readers) as server:
        ws = worlds if worlds is not None else E.worlds_for(run, run.card, n, family=family, offset=offset, **(forced or {}))
        for w in ws:
            run.check_deadline()
            cond = E.build_condition(cond_spec, _opaque(w["lid"]), run.card, regime=regime)
            ev = W.visible_evidence(w, cond)
            if evidence_hook:
                ev = evidence_hook(w, ev)
            b = W.oracle_bundle(w, cond)
            facs = {"domain": w["domain"], "pair": "original", "class_size": len(w["hidden"]["equivalence_class"])}
            if factors_of:
                facs.update(factors_of(w))
            for arm in arms:
                for reader in (readers if arm in E.MODEL_ARMS else [None]):
                    E.run_unit(run, server, w, ev, b, arm, reader, task_extra=task_extra, factors=facs, targets=targets,
                               unit_id=(w["lid"] + unit_suffix) if unit_suffix else None)
            used.append(w)
            if twin:
                t = W.factor_twin(w, twin, _alt(w["state"]["names"], twin))
                if t is None:
                    continue
                cond_t = E.build_condition(cond_spec, _opaque(t["lid"]), run.card, regime=regime)
                evt = W.visible_evidence(t, cond_t)
                if evidence_hook:
                    evt = evidence_hook(t, evt)
                bt = W.oracle_bundle(t, cond_t)
                ft = dict(facs, pair="twin", collides=bool(t.get("prefix_collides")))
                for arm in arms:
                    for reader in (readers if arm in E.MODEL_ARMS else [None]):
                        E.run_unit(run, server, t, evt, bt, arm, reader, task_extra=task_extra, factors=ft, targets=targets,
                                   unit_id=t["lid"] + (unit_suffix or ""))
                used.append(t)
        E.oracle_rows(run, used, E.build_condition(cond_spec, "u", run.card, regime=regime), unit_suffix=unit_suffix)
    update_registry("COMPUTE_LEDGER", lambda led: {**led, run.cell_id.replace("/", "_"): {"ledger": server.ledger, "gpu_held_s": server.held_s, "at": E.now_iso()}})
    return used


def _gap(rows: list[dict], key: str = "primary_score") -> dict:
    """Mean oracle-minus-DOM per unit on a key."""
    orr = {r["unit_id"]: float(r[key]) for r in rows if r["arm"] == "OR" and r.get(key) is not None}
    dom = {r["unit_id"]: float(r[key]) for r in rows if r["arm"] == "DOM" and r.get("valid") and r.get(key) is not None}
    common = [u for u in orr if u in dom]
    if not common:
        return {"gap": None, "n": 0}
    g = [orr[u] - dom[u] for u in common]
    return {"gap": sum(g) / len(g), "n": len(g), "oracle_mean": sum(orr[u] for u in common) / len(common), "dom_mean": sum(dom[u] for u in common) / len(common)}


def _score_key(rows: list[dict], score_name: str) -> list[dict]:
    """Rows re-keyed on one score name (stop_ls, changed_context_ls, ...) as primary. The
    stop score carries the cut design's weight (constructor CUT_DESIGN): terminal
    boundaries are oversampled at construction and weighted back here, so a stop contrast
    estimates the natural-boundary expectation with the oracle as its exact ceiling."""
    out = []
    if score_name == "stop_ls":
        # self-normalized importance weights: a weighted mean divides by the weight sum, so the
        # per-row weight is scaled by the mean weight over these rows (K01 on the relaunched run
        # was read with unnormalized weights, a factor 0.85 low; the verdict did not change)
        ws = [float((r.get("scores") or {}).get("stop_weight", 1.0) or 1.0) for r in rows if (r.get("scores") or {}).get("stop_ls") is not None]
        mean_w = (sum(ws) / len(ws)) if ws else 1.0
    for r in rows:
        sc = r.get("scores") or {}
        v = sc.get(score_name)
        if v is None:
            continue
        v = float(v)
        if score_name == "stop_ls":
            v *= float(sc.get("stop_weight", 1.0) or 1.0) / mean_w
        out.append(dict(r, primary_score=v))
    return out


def _contrast_by_reader(run: CardRun7, rows: list[dict], arm: str, rival: str, key: str = "primary_score",
                        threshold: float = 0.03) -> dict:
    """Reader-conditional contrasts first, the pooled contrast after (X21)."""
    out = {}
    readers = sorted({r["model_id"] for r in rows if r["arm"] == arm and r["model_id"] != "-"}) or [None]
    model_rival = rival in E.MODEL_ARMS
    for rd in readers:
        ra = [r for r in rows if r["arm"] == arm and r.get("valid") and r.get(key) is not None and (rd is None or r["model_id"] == rd)]
        # a model rival is paired within the SAME reader (a rival read by another model is a
        # different comparison); a solver or baseline rival has one row per unit
        rb = [r for r in rows if r["arm"] == rival and r.get("valid") and r.get(key) is not None
              and (not model_rival or rd is None or r["model_id"] == rd)]
        c = s5_lib.paired_contrast(ra, rb, "unit_id", key, SEED + (hash(rd) % 1000 if rd else 0))
        out[rd or "-"] = {**run.classify(c, threshold), "arm": arm, "rival": rival}
    if len(readers) > 1:
        ra = [r for r in rows if r["arm"] == arm and r.get("valid") and r.get(key) is not None]
        rb = [r for r in rows if r["arm"] == rival and r.get("valid") and r.get(key) is not None]
        if model_rival:
            ra = [dict(r, unit_id=f"{r['model_id']}::{r['unit_id']}") for r in ra]
            rb = [dict(r, unit_id=f"{r['model_id']}::{r['unit_id']}") for r in rb]
        c = s5_lib.paired_contrast(ra, rb, "unit_id", key, SEED)
        out["pooled"] = {**run.classify(c, threshold), "arm": arm, "rival": rival, "note": "pooled after the conditional cells"}
    return out


def _best(cells: dict) -> dict:
    """The reader cell with the strongest lower interval bound (the verdict's headline);
    the pooled cell never overrides a conditional reversal."""
    cand = [(k, v) for k, v in cells.items() if k != "pooled" and v.get("point") is not None]
    if not cand:
        return {"outcome": "VOID", "reason": "no units"}
    k, v = max(cand, key=lambda kv: kv[1]["ci"][0] if kv[1].get("ci") else -1e9)
    return dict(v, reader=k)


def _truth_signature(bundle: dict, factor: str) -> tuple:
    st = bundle["state_at_cut"]
    if factor == "proximal_goal":
        g0 = bundle["state_names"]["goal"]
        order = sorted(LAW.GOAL_UTILITY[g0].items(), key=lambda kv: -kv[1])
        return (order[0][0], order[1][0])
    if factor == "belief_state":
        b = st["belief_state"]
        return ("yes" if b["believed_tools"]["library"] else "no", "yes" if b["believed_tools"]["source_access"] else "no",
                b["believed_deadline"], (b["believed_checked"] or ["none"])[0])
    if factor == "expertise_law":
        L = st["expertise_law"]
        strong = [t for t, _ in sorted(L["skill"].items(), key=lambda kv: -kv[1])[:2]]
        weak = [t for t, _ in sorted(L["skill"].items(), key=lambda kv: kv[1])[:2]]
        return (strong[0], strong[1], weak[0], weak[1], "steady" if L["fluency"] < 1.2 else "erratic")
    if factor == "subjective_action_space":
        return tuple(sorted(st["subjective_action_space"]))
    if factor == "maker_context":
        c = st["maker_context"]
        return ("usable" if c["perceived_tools"]["library"] else "not", c["perceived_deadline"],
                "high" if c["audience_weight"] > 0.5 else ("low" if c["audience_weight"] > 0 else "none"))
    if factor == "history_residue":
        h = st["history_residue"]
        hab = next(iter(h.get("habit") or {}), "none")
        return (hab, (h.get("maintained") or {}).get("option", "none"))
    raise KeyError(factor)


def _sig_match(factor: str, prop_sig: list, truth: tuple) -> bool:
    ps = tuple(prop_sig)
    if factor == "proximal_goal":
        return set(ps) == set(truth[:2]) or ps[0] == truth[0]
    if factor == "expertise_law":
        return set(ps[:2]) == set(truth[:2]) or (ps[0] in truth[:2] and ps[4] == truth[4])
    if factor == "subjective_action_space":
        a, b = set(ps), set(truth)
        return len(a & b) / max(1, len(a | b)) >= 0.75
    if factor == "history_residue":
        return ps[0] == truth[0]
    return ps == truth


def _recall(run: CardRun7, factor: str) -> dict:
    """R01-R05: candidate recall and redundancy from the SLJ rows' proposal lists against
    the bundle's truth signature; the posterior's mass on matching candidates beside."""
    from runners.stage7.constructor import oracle as ORC                          # noqa: PLC0415
    hits = tot = 0
    red = []
    mass = []
    per_reader: dict = {}
    for r in run.rows():
        if r["arm"] != "SLJ" or not r.get("valid"):
            continue
        b = ORC.load(run.cell_id, r["unit_id"].replace("|", "-"))
        if not b:
            continue
        truth = _truth_signature(b, factor)
        props = ((r.get("extra") or {}).get("notes") or {}).get("proposals") or {}
        plist = props.get(factor) or []
        tot += 1
        hit = any(_sig_match(factor, p["signature"], truth) for p in plist)
        hits += int(hit)
        sigs = [tuple(p["signature"]) for p in plist]
        red.append(1 - len(set(sigs)) / max(1, len(sigs)))
        marg = (((r.get("extra") or {}).get("notes") or {}).get("factor_marginals") or {}).get(factor) or {}
        m = sum(v for p in plist for k, v in marg.items() if k == p["ref"] and _sig_match(factor, p["signature"], truth))
        mass.append(m)
        pr = per_reader.setdefault(r["model_id"], [0, 0])
        pr[0] += int(hit)
        pr[1] += 1
    return {"recall": hits / tot if tot else None, "n": tot, "redundancy": sum(red) / len(red) if red else None,
            "posterior_mass_on_truth": sum(mass) / len(mass) if mass else None,
            "by_reader": {k: v[0] / v[1] for k, v in per_reader.items() if v[1]}}


def _finish_contrast(run: CardRun7, cells: dict, metrics: dict, gate: str | None = None, extra_reason: str = "") -> int:
    best = _best(cells)
    oc = best.get("outcome", "VOID")
    if gate:
        set_gate(gate, oc == "SUPPORT_CANDIDATE", {"card": run.card, "cells": {k: v.get("outcome") for k, v in cells.items()}})
    run.finish({**metrics, "cells": cells, "degenerate_worlds": getattr(run, "_degenerate", 0)},
               {"exec": "COMPLETE", "outcome": oc, "primary": C.ALL[run.card]["primary"],
                "reason": f"{best.get('reason', '')}; reader {best.get('reader')}; {extra_reason}".strip("; "),
                "point": best.get("point"), "ci": best.get("ci"), "n_units": best.get("n_units"),
                "conditional_cells": {k: {"outcome": v.get("outcome"), "point": v.get("point")} for k, v in cells.items()}},
               rival=C.ALL[run.card]["discriminator"])
    return 0


def _gate_floor(rows: list[dict], key: str = "primary_score") -> tuple[float, dict]:
    """The §12.4 floor: 20 percent of the oracle-minus-DOM gap on these rows (the world-
    specific construction may justify another before reader outcomes; none did)."""
    g = _gap(rows, key)
    if g["gap"] is None or g["gap"] < MIN_GAP_NATS:
        return 0.03, g
    return max(0.03, DEFAULT_GAIN_FLOOR * g["gap"]), g


# ── K: the supplied-state ladder ─────────────────────────────────────────────────────

def run_K01(run: CardRun7) -> int:
    spec = C.ALL["K01"]
    batch(run, spec["arms"], [], spec["condition"], E.n_units("K01"), "worlds_K", targets=spec["targets"])
    rows = run.rows()
    gaps = {"next_action": _gap(rows, "primary_score"),
            "stop": _gap(_score_key(rows, "stop_ls"), "primary_score"),
            "changed_context": _gap(_score_key(rows, "changed_context_ls"), "primary_score"),
            "next_type": _gap(_score_key(rows, "next_type_ls"), "primary_score"),
            "invalidation": _gap(_score_key(rows, "invalidation_ls"), "primary_score")}
    live = {k: (v["gap"] is not None and v["gap"] >= MIN_GAP_NATS) for k, v in gaps.items()}
    stop_truths = [r for r in rows if r["arm"] == "OR" and (r.get("scores") or {}).get("stop_truth")]
    live["stop_truth_present"] = len(stop_truths) >= 3
    # the smoke flag rehearses code paths at a handful of worlds, where a stop truth may not
    # occur at all; the stop conditions bind the real run only
    ok = live["next_action"] and live["changed_context"] and (SMOKE or (live["stop"] and live["stop_truth_present"]))
    set_gate("construction", ok, {"gaps": {k: v["gap"] for k, v in gaps.items()}})
    update_registry("GATES", lambda _r: {**_r, "oracle_gaps": {k: v["gap"] for k, v in gaps.items()}})
    oc = "INFRASTRUCTURE" if ok else "INSTRUMENT_FAILED"
    run.finish({"gaps": gaps, "live": live, "degenerate_worlds": getattr(run, "_degenerate", 0), "floor": MIN_GAP_NATS,
                "stop_truth_worlds": len(stop_truths), "kept_fraction": getattr(run, "_kept_fraction", None)},
               {"exec": "COMPLETE", "outcome": oc, "primary": spec["primary"],
                "reason": "; ".join(f"{k} gap {v['gap']:+.3f} (n {v['n']})" if v["gap"] is not None else f"{k}: no rows" for k, v in gaps.items())
                + f"; stop truths {len(stop_truths)}"},
               rival=spec["discriminator"])
    return 0


def run_K02_K03(run: CardRun7) -> int:
    spec = C.ALL[run.card]
    batch(run, spec["arms"], [], spec["condition"], E.n_units(run.card), "worlds_K", targets=spec["targets"])
    rows = run.rows()
    table = {}
    for arm in spec["arms"] + ["OR"]:
        # valid rows, not primary-bearing rows: a terminal cut has no next action but a stop
        rr = [r for r in rows if r["arm"] == arm and (arm == "OR" or r.get("valid"))]
        table[arm] = {k: E.mean_score(_score_key(rr, k), "primary_score") for k in ("next_action_ls", "stop_ls", "next_type_ls", "next_section_ls", "changed_context_ls", "invalidation_ls")}
        table[arm]["n"] = len(rr)
    cal = CAL.reliability(E.rows_valid(rows, arm="DOM")) if run.card == "K03" else None
    return E._finish_desc(run, {"table": table, "calibration_dom": cal, "dom_params_fitted_on": (E.dom_params() or {}).get("fitted_on")},
                          json.dumps({a: round(v["next_action_ls"], 3) if v.get("next_action_ls") is not None else None for a, v in table.items()}))


def run_K_gain(run: CardRun7) -> int:
    """K04-K08, K11-K13: the arm-minus-DOM contrast per reader at the §12.4 floor, with
    U_state (K04-K10) or the factor posterior on truth (K11-K13) beside."""
    card = run.card
    spec = C.ALL[card]
    twin = spec["condition"].get("twin")
    # K13 asks for the subjective action set with the maker context derived through the law
    propose = {"K13": {"propose": ["subjective_action_space"]}}.get(card)
    batch(run, spec["arms"], run.readers, spec["condition"], E.n_units(card), "worlds_K", targets=spec["targets"], twin=twin, task_extra=propose)
    rows = run.rows()
    floor, g = _gate_floor(rows)
    main_arm = "SLJ" if "SLJ" in spec["arms"] else "DIR"
    cells = _contrast_by_reader(run, rows, main_arm, "DOM", threshold=floor)
    metrics: dict = {"oracle_gap": g, "floor": floor}
    if "SOL" in spec["arms"]:
        # a terminal cut carries no next action (primary None on both sides): compare the pairs that have one
        sol = [r for r in rows if r["arm"] == "SOL" and r.get("valid") and r.get("primary_score") is not None]
        orr = {r["unit_id"]: r["primary_score"] for r in rows if r["arm"] == "OR" and r.get("primary_score") is not None}
        metrics["sol_reproduces_oracle"] = all(abs(float(r["primary_score"]) - float(orr.get(r["unit_id"], 1e9))) < 1e-6 for r in sol if r["unit_id"] in orr) if sol else None
        metrics["sol_mean"] = E.mean_score(sol)
    u = {}
    for rd, c in cells.items():
        dm = E.mean_score(E.rows_valid(rows, arm="DOM"))
        am = E.mean_score([r for r in E.rows_valid(rows, arm=main_arm) if rd in ("pooled", "-") or r["model_id"] == rd])
        om = g.get("oracle_mean")
        if None not in (dm, am, om):
            u[rd] = u_state(am, dm, om)
    metrics["u_state_by_reader"] = u
    if "DIR" in spec["arms"] and main_arm == "SLJ":
        metrics["slj_vs_dir"] = _contrast_by_reader(run, rows, "SLJ", "DIR", threshold=0.03)
    if twin:
        metrics["twin"] = _twin_reversal(rows, main_arm)
    for f in ("proximal_goal", "belief_state", "subjective_action_space"):
        if f not in (spec["condition"].get("supplied") or []) and main_arm == "SLJ":
            metrics[f"recall_{f}"] = _recall(run, f)
    if card == "K13":
        metrics["unavailable_mass"] = {a: E.mean_score(_score_key(E.rows_valid(rows, arm=a), "mass_on_unavailable")) for a in spec["arms"]}
    if card == "K07":
        metrics["unavailable_mass"] = {a: E.mean_score(_score_key(E.rows_valid(rows, arm=a), "mass_on_unavailable")) for a in spec["arms"]}
    if card == "K05":
        k04 = [r for r in run.rows_of("K04") if r.get("valid")] if (E.S7 / "K04" / "cases.jsonl").exists() else []
        if k04:
            metrics["executable_vs_language"] = {rd: {"language_gain": cells[rd].get("point"), "executable_gain": _contrast_by_reader(run, k04, "DIR", "DOM", threshold=floor).get(rd, {}).get("point")} for rd in cells}
    gate = {"K04": "supplied_state", "K11": "infer_goal", "K12": "infer_belief", "K13": "infer_action_space"}.get(card)
    return _finish_contrast(run, cells, metrics, gate=gate, extra_reason=f"floor {floor:.3f} nats (20 percent of gap {g.get('gap')})")


def _twin_reversal(rows: list[dict], arm: str) -> dict:
    """For twin pairs: the oracle's argmax differs between the pair in `oracle_changes`
    cases; the reader's argmax follows in `follows` of them (K09/K10/K12's reversal)."""
    from runners.stage7.constructor import oracle as ORC                          # noqa: PLC0415
    from soundingline.stage7 import read_json as rj                               # noqa: PLC0415
    preds = {}
    for r in rows:
        if r["arm"] == arm and r.get("valid") and r.get("pred_ref"):
            preds[(r["model_id"], r["unit_id"])] = rj(Path(r["pred_ref"]))["targets"]["next_action"]
    changes = follows = pairs = 0
    for (rd, uid), d in preds.items():
        if "|twin-" in uid:
            continue
        tw = next((k for k in preds if k[0] == rd and k[1].startswith(uid + "|twin-")), None)
        if not tw:
            continue
        b1 = ORC.load(rows[0]["cell_id"], uid.replace("|", "-"))
        b2 = ORC.load(rows[0]["cell_id"], tw[1].replace("|", "-"))
        if not b1 or not b2:
            continue
        pairs += 1
        o1, o2 = max(b1["oracle"]["next_action"], key=b1["oracle"]["next_action"].get), max(b2["oracle"]["next_action"], key=b2["oracle"]["next_action"].get)
        if o1 != o2:
            changes += 1
            r1, r2 = max(d, key=d.get), max(preds[tw], key=preds[tw].get)
            follows += int(r1 != r2 and r2 == o2)
    return {"pairs": pairs, "oracle_changes": changes, "reader_follows": follows, "follow_rate": follows / changes if changes else None}


def run_K14(run: CardRun7) -> int:
    spec = C.ALL["K14"]
    batch(run, spec["arms"], run.readers, spec["condition"], E.n_units("K14"), "worlds_K", targets=spec["targets"])
    rows = run.rows()
    floor, g = _gate_floor(rows)
    cells = {}
    for arm in ("LEARN", "SLJ", "KL", "DIR"):
        cells.update({f"{arm}|{k}": v for k, v in _contrast_by_reader(run, rows, arm, "DOM", threshold=floor).items()})
    from runners.stage7.constructor import oracle as ORC                          # noqa: PLC0415
    kl_truth = []
    for r in rows:
        if r["arm"] == "KL" and r.get("valid"):
            b = ORC.load(run.cell_id, r["unit_id"].replace("|", "-"))
            post = ((r.get("extra") or {}).get("notes") or {}).get("posterior") or {}
            if b and post:
                w = W.make_world(r["unit_id"], b["condition"].get("domain", r["factors"].get("domain", "essay")))
                truth_ref = W.candidate_law_truth(w) if not w["degenerate"] else None
                if truth_ref:
                    kl_truth.append(post.get(truth_ref, 0.0))
    learned_vs_selected = _contrast_by_reader(run, rows, "LEARN", "KL", threshold=0.03)
    metrics = {"oracle_gap": g, "floor": floor, "kl_mass_on_true_law": sum(kl_truth) / len(kl_truth) if kl_truth else None,
               "learned_minus_selected": learned_vs_selected, "recall_law": _recall(run, "expertise_law")}
    best_cells = {k: v for k, v in cells.items() if k.startswith(("LEARN", "SLJ"))}
    return _finish_contrast(run, best_cells or cells, {**metrics, "all_cells": cells}, gate="infer_law", extra_reason="learned (LEARN, SLJ) versus selected (KL) scored apart")


def run_K15(run: CardRun7) -> int:
    spec = C.ALL["K15"]
    batch(run, spec["arms"], run.readers, spec["condition"], E.n_units("K15"), "worlds_K", targets=spec["targets"])
    rows = _score_key(run.rows(), "stop_ls")
    floor, g = _gate_floor(rows)
    cells = _contrast_by_reader(run, rows, "DIR", "DOM", threshold=floor)
    cells.update({f"vsPERS|{k}": v for k, v in _contrast_by_reader(run, rows, "DIR", "PERS", threshold=floor).items()})
    sol = _contrast_by_reader(run, rows, "SOL", "DOM", threshold=floor)
    metrics = {"stop_gap": g, "floor": floor, "sol_hazard_gain": sol,
               "stop_truth_rate": E.mean_score([dict(r, primary_score=1.0 if (r.get("scores") or {}).get("stop_truth") else 0.0) for r in rows if r["arm"] == "OR"]) if rows else None}
    return _finish_contrast(run, {k: v for k, v in cells.items() if not k.startswith("vsPERS")}, {**metrics, "vs_persistence": {k: v for k, v in cells.items() if k.startswith("vsPERS")}}, gate="stop_state")


def run_K16(run: CardRun7) -> int:
    spec = C.ALL["K16"]
    g4 = gate_state("supplied_state") or {}
    readers = [C.SIZE_LADDER[k] for k in spec["factors"]["size"]]
    cond = spec["condition"]
    with E.ModelServer("s7_k16", readers) as server:
        ws = E.worlds_for(run, "K16", E.n_units("K16"), family="worlds_K")
        for w in ws:
            run.check_deadline()
            c = E.build_condition(cond, _opaque(w["lid"]), "K16")
            ev = W.visible_evidence(w, c)
            b = W.oracle_bundle(w, c)
            for size, reader in zip(spec["factors"]["size"], readers):
                for compute in spec["factors"]["compute"]:
                    arm = "DIR" if compute == "small" else "DIRS"
                    tg = ["next_action", "stop"] if compute == "small" else None
                    E.run_unit(run, server, w, ev, b, arm, reader, factors={"domain": w["domain"], "size": size, "compute": compute}, targets=tg)
            E.run_unit(run, server, w, ev, b, "DOM", None, factors={"domain": w["domain"]})
        E.oracle_rows(run, ws, E.build_condition(cond, "u", "K16"))
    rows = run.rows()
    floor, g = _gate_floor(rows)
    cells = {}
    for size in spec["factors"]["size"]:
        for compute in spec["factors"]["compute"]:
            sub = [r for r in rows if r["arm"] == "DOM" or (r.get("factors", {}).get("size") == size and r.get("factors", {}).get("compute") == compute)]
            arm = "DIR" if compute == "small" else "DIRS"
            c = _contrast_by_reader(run, sub, arm, "DOM", threshold=floor)
            for k, v in c.items():
                cells[f"{size}|{compute}"] = v
    interaction = None
    try:
        pts = {k: v.get("point") for k, v in cells.items()}
        interaction = {"size_effect_small": pts.get("qwen3|small", 0) - pts.get("qwen05|small", 0),
                       "structure_effect_1.5B": pts.get("qwen15|expanded", 0) - pts.get("qwen15|small", 0)}
    except Exception:                                                             # noqa: BLE001
        pass
    reason = "diagnosis under a failed K04 gate" if not g4.get("passed") else "conditional on the passed K04 gate"
    return _finish_contrast(run, cells, {"oracle_gap": g, "floor": floor, "interaction": interaction, "k04_gate": g4.get("passed"),
                                         "caveats": "Qwen3.5 9B via Ollama: different family, Q4_K_M quantization, top-20 log-probability interface"}, extra_reason=reason)


# ── R: the reconstruction ladder ─────────────────────────────────────────────────────

RECALL_FACTOR = {"R01": "proximal_goal", "R02": "belief_state", "R03": "expertise_law", "R04": "subjective_action_space", "R05": "maker_context"}


def run_R_recall(run: CardRun7) -> int:
    spec = C.ALL[run.card]
    factor = RECALL_FACTOR[run.card]
    twin = "belief" if run.card == "R02" else None
    # one factor per recall rung: the other derivable one derives through the law
    propose = {"R04": {"propose": ["subjective_action_space"]}, "R05": {"propose": ["maker_context"]}}.get(run.card)
    batch(run, spec["arms"], run.readers, spec["condition"], E.n_units(run.card), "worlds_R", targets=spec["targets"], twin=twin, task_extra=propose)
    rec = _recall(run, factor)
    ok = rec["recall"] is not None and rec["recall"] >= 0.5
    set_gate(f"recall_{factor}", ok, rec)
    if run.card == "R04":
        rows = run.rows()
        rec["unavailable_mass_slj"] = E.mean_score(_score_key(E.rows_valid(rows, arm="SLJ"), "mass_on_unavailable"))
    run.finish({"recall": rec, "band": "recall at or above 0.5 opens the selection questions"},
               {"exec": "COMPLETE", "outcome": "DESCRIPTIVE", "primary": spec["primary"], "point": rec["recall"],
                "reason": f"recall {rec['recall']}; redundancy {rec['redundancy']}; posterior mass on truth {rec['posterior_mass_on_truth']}; gate {'open' if ok else 'closed'}"},
               rival=spec["discriminator"])
    return 0


def run_R_ratio(run: CardRun7) -> int:
    """R06-R08: R_j from the K-rung SLJ rows against the K04 supplied ceiling and DOM."""
    src = {"R06": "K11", "R07": "K12", "R08": "K13"}[run.card]
    krows = [r for r in run.rows_of(src) if r.get("valid")] if (E.S7 / src / "cases.jsonl").exists() else []
    k04 = [r for r in run.rows_of("K04") if r.get("valid")] if (E.S7 / "K04" / "cases.jsonl").exists() else []
    out = {}
    for rd in sorted({r["model_id"] for r in krows if r["arm"] == "SLJ"}):
        dom = E.mean_score([r for r in krows if r["arm"] == "DOM"])
        slj = E.mean_score([r for r in krows if r["arm"] == "SLJ" and r["model_id"] == rd])
        sup = E.mean_score([r for r in k04 if r["arm"] == "DIR" and r["model_id"] == rd])
        orr = E.mean_score([r for r in krows if r["arm"] == "OR"])
        out[rd] = {"dom": dom, "slj": slj, "supplied_ceiling": sup, "oracle": orr,
                   "r_ratio": r_ratio(slj, dom, sup) if None not in (slj, dom, sup) else None,
                   "u_state_slj": u_state(slj, dom, orr) if None not in (slj, dom, orr) else None}
    if run.card == "R07":
        cc = {}
        for rd in out:
            dom = E.mean_score(_score_key([r for r in krows if r["arm"] == "DOM"], "changed_context_ls"))
            slj = E.mean_score(_score_key([r for r in krows if r["arm"] == "SLJ" and r["model_id"] == rd], "changed_context_ls"))
            cc[rd] = {"dom": dom, "slj": slj}
        out["changed_context"] = cc
    if run.card == "R08":
        out["unavailable_mass"] = E.mean_score(_score_key([r for r in krows if r["arm"] == "SLJ"], "mass_on_unavailable"))
    valid = [v for k, v in out.items() if isinstance(v, dict) and v.get("r_ratio") is not None]
    oc = "DESCRIPTIVE" if valid else "VOID"
    return E._finish_desc(run, {"ratios": out, "source": src}, json.dumps({k: (round(v["r_ratio"], 3) if isinstance(v, dict) and v.get("r_ratio") is not None else None) for k, v in out.items()}), outcome=oc)


def run_R09(run: CardRun7) -> int:
    spec = C.ALL["R09"]
    batch(run, spec["arms"], run.readers, spec["condition"], E.n_units("R09"), "worlds_R", targets=spec["targets"], offset=700)
    rows = run.rows()
    floor, g = _gate_floor(rows)
    cells = {f"LEARN|{k}": v for k, v in _contrast_by_reader(run, rows, "LEARN", "DOM", threshold=floor).items()}
    slj = _contrast_by_reader(run, rows, "SLJ", "DOM", threshold=floor)
    k14 = [r for r in run.rows_of("K14") if r.get("valid") and r["arm"] == "KL"] if (E.S7 / "K14" / "cases.jsonl").exists() else []
    metrics = {"oracle_gap": g, "floor": floor, "slj_cells": slj, "kl_on_K14_mean": E.mean_score(k14),
               "learn_mean": E.mean_score(E.rows_valid(rows, arm="LEARN")), "note": "no candidate law supplied on these untouched episodes"}
    return _finish_contrast(run, cells, metrics, gate="learn_law")


def run_R10(run: CardRun7) -> int:
    spec = C.ALL["R10"]

    def copied(w, ev):
        # the copied-context rival: C_m taken verbatim from C_ext with accurate beliefs (SOL runs it)
        ev2 = dict(ev)
        sf = dict(ev["supplied_factors"])
        facs = dict(sf["factors"])
        c = w["state_at_cut"]["external_context"]
        acc = {"believed_tools": dict(c["tools"]), "believed_deadline": c["deadline"], "believed_checked": []}
        facs["maker_context"] = LAW.maker_context(W.factor_executable("external_context", w["state_at_cut"]), acc, facs["expertise_law"])
        ev2["supplied_factors"] = {"form": "executable", "factors": facs}
        return ev2
    batch(run, ["DOM", "DIR", "SLJ"], run.readers, spec["condition"], E.n_units("R10"), "worlds_R", targets=spec["targets"],
          task_extra={"propose": ["maker_context"]})            # the context is the reconstruction; the action set derives
    batch(run, ["SOL"], [], spec["condition"], E.n_units("R10"), "worlds_R", targets=spec["targets"], evidence_hook=copied,
          task_extra={"variant": "copied_context"})
    rows = run.rows()
    cc = _score_key(rows, "changed_context_ls")
    floor, g = _gate_floor(cc)
    cells = _contrast_by_reader(run, cc, "SLJ", "DOM", threshold=floor)
    vs_copy = _contrast_by_reader(run, cc, "SLJ", "SOL", threshold=0.03)
    return _finish_contrast(run, cells, {"gap": g, "floor": floor, "slj_vs_copied_context": vs_copy, "recall_context": _recall(run, "maker_context")}, gate="infer_context")


def run_R_joint(run: CardRun7) -> int:
    """R11 (goal x belief crossed), R12 (law swaps with the action space derived), R13
    (everything withheld, cold)."""
    card = run.card
    spec = C.ALL[card]
    forced = {}
    twin = None
    if card == "R11":
        pass
    if card == "R12":
        twin = "law"
    used = batch(run, spec["arms"], run.readers, spec["condition"], E.n_units(card), "worlds_R", targets=spec["targets"], forced=forced, twin=twin,
                 factors_of=(lambda w: {"goal_x_belief": f"{w['state']['names']['goal']}|{w['state']['names']['belief']}"}) if card == "R11" else None)
    rows = run.rows()
    floor, g = _gate_floor(rows)
    cells = _contrast_by_reader(run, rows, "SLJ", "DOM", threshold=floor)
    metrics = {"oracle_gap": g, "floor": floor, "slj_vs_dir": _contrast_by_reader(run, rows, "SLJ", "DIR", threshold=0.03), "n_worlds": len(used)}
    for f in (spec["identity"]["withheld_target"].split("_next_action")[0].split("_") if card != "R13" else []):
        pass
    withheld = [f for f in C.ALL7 if f not in (spec["condition"].get("supplied") or [])]
    for f in withheld:
        if f in ("proximal_goal", "belief_state", "expertise_law", "subjective_action_space", "maker_context", "history_residue"):
            metrics[f"recall_{f}"] = _recall(run, f)
    if card == "R11":
        metrics["component_posteriors"] = {f: metrics.get(f"recall_{f}", {}).get("posterior_mass_on_truth") for f in ("proximal_goal", "belief_state")}
        metrics["by_cross"] = {}
        for key in sorted({r["factors"].get("goal_x_belief") for r in rows if r.get("factors", {}).get("goal_x_belief")}):
            sub = [r for r in rows if r["arm"] == "DOM" or r["factors"].get("goal_x_belief") == key]
            metrics["by_cross"][key] = {k: v.get("point") for k, v in _contrast_by_reader(run, sub, "SLJ", "DOM", threshold=floor).items()}
    if card == "R12":
        metrics["twin"] = _twin_reversal(rows, "SLJ")
        metrics["unavailable_mass_slj"] = E.mean_score(_score_key(E.rows_valid(rows, arm="SLJ"), "mass_on_unavailable"))
    if card == "R13":
        for t in ("stop_ls", "next_type_ls", "next_section_ls", "changed_context_ls", "invalidation_ls"):
            metrics[f"cells_{t}"] = {a: {k: v.get("point") for k, v in _contrast_by_reader(run, _score_key(rows, t), a, "DOM", threshold=0.03).items()} for a in ("SLJ", "DIR")}
        metrics["class_coverage"] = {a: CAL.class_coverage(E.rows_valid(rows, arm=a)) for a in ("SLJ", "DIR")}
    gate = {"R11": "joint_goal_belief", "R12": "joint_law_space", "R13": "joint_all"}[card]
    return _finish_contrast(run, cells, metrics, gate=gate)


def run_R14(run: CardRun7) -> int:
    spec = C.ALL["R14"]
    for regime in spec["factors"]["regime"]:
        batch(run, spec["arms"], run.readers, spec["condition"], E.n_units("R14"), "worlds_R", targets=spec["targets"], regime=regime,
              factors_of=lambda w, rg=regime: {"regime": rg}, task_extra={"regime": regime}, unit_suffix=f"~{regime}")
    rows = run.rows()
    floor, g = _gate_floor(rows)
    cells = {}
    for regime in spec["factors"]["regime"]:
        sub = [r for r in rows if r["arm"] in ("DOM", "OR") or r.get("factors", {}).get("regime") == regime]
        for arm in ("SLJ", "DIR"):
            for k, v in _contrast_by_reader(run, sub, arm, "DOM", threshold=floor).items():
                cells[f"{regime}|{arm}|{k}"] = v
    return _finish_contrast(run, cells, {"oracle_gap": g, "floor": floor, "note": "regime cells before any pooling (X21)"}, gate="regimes")


def run_R15(run: CardRun7) -> int:
    rows = [r for r in run.rows_of("R14") if r.get("valid")] if (E.S7 / "R14" / "cases.jsonl").exists() else []
    out = {}
    for regime in ("cold", "domain_expert", "maker_familiar"):
        sub = [r for r in rows if r["arm"] == "SLJ" and r.get("factors", {}).get("regime") == regime]
        ents = []
        for r in sub:
            marg = ((r.get("extra") or {}).get("notes") or {}).get("factor_marginals") or {}
            if marg:
                ents.append(sum(CAL.entropy(m) for m in marg.values()) / len(marg))
        out[regime] = {"n": len(sub), "mean_primary": E.mean_score(sub), "mean_factor_entropy": sum(ents) / len(ents) if ents else None,
                       "calibration": {k: v for k, v in CAL.reliability(sub).items() if k != "bins"}}
    return E._finish_desc(run, {"by_regime": out}, json.dumps({k: (round(v["mean_primary"], 3) if v["mean_primary"] is not None else None, v["mean_factor_entropy"]) for k, v in out.items()}),
                          outcome="DESCRIPTIVE" if rows else "VOID")


def run_R16(run: CardRun7) -> int:
    spec = C.ALL["R16"]
    batch(run, spec["arms"], run.readers, spec["condition"], E.n_units("R16"), "worlds_R", targets=spec["targets"], offset=900)
    rows = run.rows()
    from runners.stage7.constructor import oracle as ORC                          # noqa: PLC0415
    cov = CAL.class_coverage(E.rows_valid(rows, arm="SLJ"))
    eig_ratios = []
    for r in E.rows_valid(rows, arm="SLJ"):
        notes = (r.get("extra") or {}).get("notes") or {}
        post = notes.get("posterior") or {}
        cp = notes.get("candidate_preds") or {}
        b = ORC.load(run.cell_id, r["unit_id"].replace("|", "-"))
        if not post or not cp or not b:
            continue
        # expected information about the candidate set from observing whether the maker takes option a
        opts = set()
        for d in cp.values():
            opts |= set(d)
        h0 = CAL.entropy(post)

        def eig(a, post_, preds_):
            p_take = sum(post_[k] * preds_[k].get(a, 0.0) for k in post_)
            if p_take <= 1e-9 or p_take >= 1 - 1e-9:
                return 0.0
            post_take = {k: post_[k] * preds_[k].get(a, 0.0) / p_take for k in post_}
            post_not = {k: post_[k] * (1 - preds_[k].get(a, 0.0)) / (1 - p_take) for k in post_}
            return h0 - (p_take * CAL.entropy(post_take) + (1 - p_take) * CAL.entropy(post_not))
        reader_eig = {a: eig(a, post, cp) for a in opts}
        if not reader_eig:
            continue
        chosen = max(reader_eig, key=reader_eig.get)
        best = max(reader_eig.values())
        eig_ratios.append(reader_eig[chosen] / best if best > 0 else None)
    ratios = [x for x in eig_ratios if x is not None]
    metrics = {"class_coverage": cov, "eig_ratio_mean": sum(ratios) / len(ratios) if ratios else None, "n_eig": len(ratios),
               "note": "the discriminator is the option whose observation most reduces the reader's own candidate entropy; the ratio is against the reader's best option (1.0 by construction when chosen greedily), reported with the class coverage as the R16 receipt"}
    ok = cov.get("coverage_correct_equivalence") is not None
    return E._finish_desc(run, metrics, f"abstain on equivalence {cov.get('abstain_rate_on_equivalence')}; false abstain {cov.get('false_abstain_rate')}", outcome="DESCRIPTIVE" if ok else "VOID")


# ── A: architecture conformance and compute ──────────────────────────────────────────

def run_A_fixture(run: CardRun7) -> int:
    from runners.stage7.conformance import fixtures as F                          # noqa: PLC0415
    from runners.stage7.conformance import sources as SRC                         # noqa: PLC0415
    card = run.card
    if card == "A01":
        m = SRC.write_manifest()
        return E._finish_infra(run, {"manifest": {k: v.get("status") for k, v in m["sources"].items()}, "all_pinned": m["all_pinned"]}, m["all_pinned"],
                               f"{sum(1 for v in m['sources'].values() if v.get('clone_receipt', {}).get('present'))} clones pinned; every entry pinned {m['all_pinned']}")
    if card == "A02":
        s = SRC.sealed()
        return E._finish_infra(run, s, s["sealed"], f"sealed {s['sealed']}: inside repo {s['inside_repo']}, on path {s['on_sys_path']}")
    fam = {"A03": "laip", "A04": "thought_tracing", "A05": "thought_tracing", "A06": "thought_tracing", "A07": "autotom",
           "A09": "autotom", "A10": "liras", "A12": "inverse_planning", "A13": "labtom"}[card]
    res = F.FIXTURES[fam]()
    update_registry("CONFORMANCE", lambda conf: {**conf, fam: {"pass": res.get("pass"), "ops": res.get("ops"), "admitted_name": res.get("admitted_name") or (C.ALL and __import__("soundingline.stage7", fromlist=["EXTERNAL_FAMILIES"]).EXTERNAL_FAMILIES[fam]["published"] if res.get("pass") else __import__("soundingline.stage7", fromlist=["EXTERNAL_FAMILIES"]).EXTERNAL_FAMILIES[fam]["local"]), "card": card, "at": E.now_iso()}})
    set_gate(f"conformance_{fam}", bool(res.get("pass")), {"ops": res.get("ops")})
    return E._finish_infra(run, {"fixture": res}, bool(res.get("pass")), f"{fam}: {'PASS' if res.get('pass') else 'FAIL'} {res.get('ops')} {res.get('error', '')}")


def run_A08(run: CardRun7) -> int:
    spec = C.ALL["A08"]
    for comp in spec["factors"]["world_completeness"]:
        forced = {"belief": "accurate", "residue": "none"} if comp == "complete" else {"belief": "false_library", "residue": "habit_check"}
        batch(run, spec["arms"], run.readers, spec["condition"], E.n_units("A08"), "worlds_A", targets=spec["targets"], forced=forced,
              offset=0 if comp == "complete" else 300, factors_of=lambda w, c=comp: {"world_completeness": c})
    rows = run.rows()
    added = {}
    for r in E.rows_valid(rows, arm="adaptive_factor_expansion"):
        rec = ((r.get("extra") or {}).get("notes") or {}).get("receipt") or {}
        key = r["factors"].get("world_completeness")
        added.setdefault(key, []).append(len(rec.get("added") or []))
    floor, g = _gate_floor(rows) if any(r["arm"] == "DOM" for r in rows) else (0.03, {"gap": None})
    cells = {}
    for comp in spec["factors"]["world_completeness"]:
        sub = [r for r in rows if r["arm"] == "OR" or r["factors"].get("world_completeness") == comp]
        for k, v in _contrast_by_reader(run, sub, "adaptive_factor_expansion", "SLJ", threshold=0.03).items():
            cells[f"{comp}|{k}"] = v
    metrics = {"mean_factors_added": {k: sum(v) / len(v) for k, v in added.items() if v}, "interaction": "missing-variable gain versus complete-world cost, cells above"}
    return _finish_contrast(run, cells, metrics)


def run_A11(run: CardRun7) -> int:
    spec = C.ALL["A11"]
    batch(run, spec["arms"] + ["DOM"], run.readers, spec["condition"], E.n_units("A11"), "worlds_A", targets=spec["targets"], offset=600)
    rows = run.rows()
    floor, g = _gate_floor(rows)
    cells = _contrast_by_reader(run, rows, "synthesized_agent_model", "DIR", threshold=0.03)
    val = [((r.get("extra") or {}).get("notes") or {}).get("receipt") or {} for r in E.rows_valid(rows, arm="synthesized_agent_model")]
    return _finish_contrast(run, cells, {"validated_rate": sum(1 for v in val if v.get("semantics")) / len(val) if val else None,
                                         "vs_dom": _contrast_by_reader(run, rows, "synthesized_agent_model", "DOM", threshold=floor), "oracle_gap": g})


def run_A14(run: CardRun7) -> int:
    spec = C.ALL["A14"]
    batch(run, spec["arms"], run.readers, spec["condition"], E.n_units("A14"), "worlds_A", targets=spec["targets"], offset=900)
    rows = run.rows()
    updates = []
    for r in E.rows_valid(rows, arm="sequential_hypothesis_particles"):
        rec = ((r.get("extra") or {}).get("notes") or {}).get("receipt") or {}
        updates.append({"ess": rec.get("ess"), "resampled": rec.get("resampled"), "rejuvenated": rec.get("rejuvenated"), "weighted": rec.get("weighted")})
    marg_moves = 0
    for r in E.rows_valid(rows, arm="SLJ"):
        m = ((r.get("extra") or {}).get("notes") or {}).get("factor_marginals") or {}
        if m and any(len(v) > 1 for v in m.values()):
            marg_moves += 1
    cells = _contrast_by_reader(run, rows, "SLJ", "sequential_hypothesis_particles", threshold=0.03)
    return _finish_contrast(run, cells, {"revision_receipts": updates[:40], "slj_rows_with_live_factor_posteriors": marg_moves,
                                         "note": "predictions are emitted at every revision through the solver; a longer rationale never enters"})


def run_A15(run: CardRun7) -> int:
    spec = C.ALL["A15"]
    batch(run, spec["arms"] + ["DOM"], run.readers, spec["condition"], E.n_units("A15"), "worlds_A", targets=spec["targets"], offset=1200)
    rows = run.rows()
    floor, g = _gate_floor(rows)
    cells = {}
    compute = {}
    for arm in spec["arms"]:
        for k, v in _contrast_by_reader(run, rows, arm, "DIR", threshold=0.03).items():
            cells[f"{arm}|{k}"] = v
        rr = E.rows_valid(rows, arm=arm)
        b = [r.get("budget") or {} for r in rr]
        compute[arm] = {k: (sum(float(x.get(k, 0) or 0) for x in b) / len(b) if b else None) for k in ("model_calls", "tokens_in", "tokens_out", "solver_operations", "wall_s", "retries", "cache_hits")}
        compute[arm]["n"] = len(rr)
        compute[arm]["vs_dom_point"] = _contrast_by_reader(run, rows, arm, "DOM", threshold=floor).get("pooled", {}).get("point") or next(iter(_contrast_by_reader(run, rows, arm, "DOM", threshold=floor).values()), {}).get("point")
    gain_per = {a: ((c["vs_dom_point"] or 0.0) / max(1.0, (c["model_calls"] or 0) + 0.01 * (c["solver_operations"] or 0))) for a, c in compute.items()}
    conf = read_registry("CONFORMANCE") or {}
    names = {a: a for a in spec["arms"]}
    for fam, rec in conf.items():
        local = __import__("soundingline.stage7", fromlist=["EXTERNAL_FAMILIES"]).EXTERNAL_FAMILIES[fam]["local"]
        if local in names and rec.get("pass"):
            names[local] = rec.get("admitted_name") or local
    update_registry("COMPUTE_LEDGER", lambda _r: {**_r, "A15_priced": compute})
    return _finish_contrast(run, {k: v for k, v in cells.items() if k.startswith("SLJ")} or cells,
                            {"all_cells": cells, "compute_by_arm": compute, "gain_per_unit_compute": gain_per, "names_after_conformance": names, "oracle_gap": g})


def run_A16(run: CardRun7) -> int:
    spec = C.ALL["A16"]
    g4 = gate_state("supplied_state") or {}
    readers = [C.SIZE_LADDER[k] for k in spec["factors"]["size"]]
    with E.ModelServer("s7_a16", readers) as server:
        ws = E.worlds_for(run, "A16", E.n_units("A16"), family="worlds_A", offset=1500)
        c_full = C.ALL["K04"]["condition"]
        c_goal = C.ALL["K11"]["condition"]
        for w in ws:
            run.check_deadline()
            cf = E.build_condition(c_full, _opaque(w["lid"]), "A16")
            cg = E.build_condition(c_goal, _opaque(w["lid"]) + "g", "A16g")
            evf, evg = W.visible_evidence(w, cf), W.visible_evidence(w, cg)
            bf, bg = W.oracle_bundle(w, cf), W.oracle_bundle(w, cg)
            for size, reader in zip(spec["factors"]["size"], readers):
                E.run_unit(run, server, w, evf, bf, "DIR", reader, factors={"domain": w["domain"], "size": size, "cond": "full"})
                E.run_unit(run, server, w, evg, bg, "SLJ", reader, factors={"domain": w["domain"], "size": size, "cond": "goal_withheld"}, unit_id=w["lid"] + "|g")
            E.run_unit(run, server, w, evf, bf, "DOM", None, factors={"domain": w["domain"], "cond": "full"})
        E.oracle_rows(run, ws, E.build_condition(c_full, "u", "A16"))
    rows = run.rows()
    floor, g = _gate_floor([r for r in rows if r["factors"].get("cond") == "full" or r["arm"] == "OR"])
    cells = {}
    recall = {}
    for size, reader in zip(spec["factors"]["size"], readers):
        sub = [r for r in rows if r["arm"] == "DOM" or (r["factors"].get("size") == size and r["factors"].get("cond") == "full")]
        for k, v in _contrast_by_reader(run, sub, "DIR", "DOM", threshold=floor).items():
            cells[f"{size}"] = v
        gr = [r for r in rows if r["arm"] == "SLJ" and r["factors"].get("size") == size and r.get("valid")]
        hits = tot = 0
        from runners.stage7.constructor import oracle as ORC                      # noqa: PLC0415
        for r in gr:
            b = ORC.load(run.cell_id, r["unit_id"].replace("|", "-"))
            if not b:
                continue
            truth = _truth_signature(b, "proximal_goal")
            plist = (((r.get("extra") or {}).get("notes") or {}).get("proposals") or {}).get("proximal_goal") or []
            tot += 1
            hits += int(any(_sig_match("proximal_goal", p["signature"], truth) for p in plist))
        recall[size] = hits / tot if tot else None
    reason = "diagnosis under a failed K04 gate" if not g4.get("passed") else "conditional on the passed K04 gate"
    return _finish_contrast(run, cells, {"oracle_gap": g, "floor": floor, "goal_recall_by_size": recall, "k04_gate": g4.get("passed"),
                                         "caveats": "0.5B/1.5B/3B share the Qwen2.5 family and the HF letter readout; the 9B is Qwen3.5 through Ollama (Q4_K_M, top-20 log probabilities)"},
                            extra_reason=reason)


# ── dispatch ─────────────────────────────────────────────────────────────────────────

def run_card(run: CardRun7) -> int:
    card = run.card
    if card == "K01":
        return run_K01(run)
    if card in ("K02", "K03"):
        return run_K02_K03(run)
    if card in ("K04", "K05", "K06", "K07", "K08", "K09", "K10", "K11", "K12", "K13"):
        return run_K_gain(run)
    if card == "K14":
        return run_K14(run)
    if card == "K15":
        return run_K15(run)
    if card == "K16":
        return run_K16(run)
    if card in RECALL_FACTOR:
        return run_R_recall(run)
    if card in ("R06", "R07", "R08"):
        return run_R_ratio(run)
    if card == "R09":
        return run_R09(run)
    if card == "R10":
        return run_R10(run)
    if card in ("R11", "R12", "R13"):
        return run_R_joint(run)
    if card == "R14":
        return run_R14(run)
    if card == "R15":
        return run_R15(run)
    if card == "R16":
        return run_R16(run)
    if card in ("A01", "A02", "A03", "A04", "A05", "A06", "A07", "A09", "A10", "A12", "A13"):
        return run_A_fixture(run)
    if card == "A08":
        return run_A08(run)
    if card == "A11":
        return run_A11(run)
    if card == "A14":
        return run_A14(run)
    if card == "A15":
        return run_A15(run)
    if card == "A16":
        return run_A16(run)
    raise ValueError(card)
