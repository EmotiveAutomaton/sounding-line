"""Stage 6 world-track engines (brief §8 C, A, V, F): the construction audits, the exact
CPU statistics on the controller, history, value, and foraging worlds, and the GPU reader
cards that ask a reader the track's discriminating question. One module because the four
tracks share the chassis; the per-card discriminators are the spec table below.

The brief's layout named control/history/value/foraging_models.py; they are merged here
with the card registry as the single home of per-card logic (recorded as a deviation in
the registry entry: one interpreter beats four near-copies).

DESIGN CHECK (2026-08-30)
lessons read: LESSONS §3 (a manipulation check needs dynamic range: every audit card
  measures its planted difference's size before any reader touches the worlds; blind
  floors follow the truth's label marginal; denominators are declared opportunities), §5.
gates and bands:
  - audit cards (C01, C02, A01, V01, F01, F07): INFRASTRUCTURE when the construction's
    planted property holds (liveness, endpoint match, collision, floor), INSTRUMENT_FAILED
    otherwise; the alternative is a construction defect, never a reader result.
  - exact statistic cards (CPU): the discriminator's contrast over worlds with the
    exhaustive verdict bands at the card's threshold; these validate that the WORLDS carry
    the distinction (the same role Ghost V14 plays for its ontology), and their claims are
    construction-side only.
  - reader cards (GPU): the reader's held-out prediction of the discriminating event
    against the track baseline, bands as everywhere; capability scoping as in engines.py.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from runners import s5_lib                                                         # noqa: E402
from runners.stage6 import architectures as A                                      # noqa: E402
from runners.stage6 import cards as CARDS_MOD                                      # noqa: E402
from runners.stage6 import prediction as P                                         # noqa: E402
from runners.stage6 import worlds as W                                             # noqa: E402
from runners.stage6.cardrun import SMOKE, CardRun6, bench_lineages                 # noqa: E402
from runners.stage6.engines import capability_note                                 # noqa: E402

SEED = 66700


def _worlds_for(run: CardRun6, card: str, n: int, **forced) -> list[dict]:
    track = card[0]
    out = []
    for dom in CARDS_MOD.DOMAINS:
        for lid in bench_lineages(card, dom, n, split=run.split):
            w = W.make_process_world(lid, dom, track=track, **forced)
            run.register_world(lid, w)
            out.append(w)
    return out


def _ci(run: CardRun6, vals: dict, seed: int) -> dict:
    return s5_lib.cluster_bootstrap_ci(vals, seed)


def _traj_stats(w: dict) -> dict:
    """The exact per-world statistics the CPU cards contrast."""
    steps = w["trajectory"]["steps"]
    sec_idx = {s["name"]: i for i, s in enumerate(w["doc"]["sections"])}
    jumps = [abs(sec_idx[a["action"]["section"]] - sec_idx[b["action"]["section"]])
             for a, b in zip(steps, steps[1:])]
    runs = 1 + sum(1 for a, b in zip(steps, steps[1:]) if a["goal_active"] != b["goal_active"])
    itr = w["events"].get("interrupt_step")
    post_interrupt = next((s["action"]["type"] for s in steps if s["i"] > itr), None) if itr is not None else None
    urgent_at = next((k for k, s in enumerate(steps) if s["action"]["slot"] == "urgent"), None)
    hanging = 0
    for i, s in enumerate(steps[:-1]):
        sec = s["action"]["section"]
        later = [t for t in steps[i + 1:] if t["action"]["section"] == sec]
        if s["action"]["type"] == "write" and later and steps[i + 1]["action"]["section"] != sec:
            hanging += 1
    probes = [k for k, s in enumerate(steps) if s["action"]["type"] == "probe"]
    fixes = [k for k, s in enumerate(steps) if s["action"]["type"] == "fix" and s["action"]["slot"] != "urgent"]
    probe_to_fix = (min(fixes) - min(probes)) if probes and fixes and min(fixes) > min(probes) else None
    # the OUTCOME READ: a check on the technique's own slot after the probe (the ordinary
    # per-section checks are not outcome reads and would alias the count across generators)
    checks_after_probe = sum(1 for k, s in enumerate(steps)
                             if s["action"]["type"] == "check" and s["action"]["slot"].startswith("tech")
                             and probes and k > min(probes))
    return {"mean_section_jump": sum(jumps) / max(1, len(jumps)), "goal_runs": runs,
            "n_steps": len(steps), "post_interrupt_type": post_interrupt,
            "urgent_latency": (urgent_at - itr) if (urgent_at is not None and itr is not None) else None,
            "hanging_dependencies": hanging, "probe_to_fix_gap": probe_to_fix,
            "checks_after_probe": checks_after_probe,
            "cc_choice": w["hidden"]["changed_context"]["choice"],
            "stopped": w["trajectory"]["stopped_at"] is not None}


# ── audits ────────────────────────────────────────────────────────────────────────────

def _audit_liveness(run: CardRun6, card: str, kinds: list[str], forced_key: str) -> int:
    """C01/A01/V01/F01: the generators are independently live (oracle separates each from
    the full order at better than the marginal) and surface matched (the cheap 1-nn on
    render statistics sits at the floor)."""
    n = 3 if SMOKE else 16
    hits, total = 0, 0
    surf_rows = []
    for kind in kinds:
        for dom in CARDS_MOD.DOMAINS:
            for i, lid in enumerate(bench_lineages(card, dom, n, split=run.split)):
                w = W.make_process_world(f"{lid}|{kind}", dom, track=card[0], **{forced_key: kind} if forced_key else {})
                post = W.oracle_posterior(w, upto=len(w["trajectory"]["steps"]))
                truth_tag = next((t for t in post if t.endswith(kind) or t == kind), None)
                hits += int(truth_tag is not None and max(post, key=post.get) == truth_tag)
                total += 1
                text = W.render_artifact(w)
                surf_rows.append(((len(text), text.count("present"), text.count("reworked")), kind))
    live = hits / max(1, total)
    marg = 1.0 / len(kinds)
    s_hits = 0
    for i, (f, y) in enumerate(surf_rows):
        best, by = None, None
        for j, (g, y2) in enumerate(surf_rows):
            if i == j:
                continue
            dd = sum((a - b) ** 2 for a, b in zip(f, g))
            if best is None or dd < best:
                best, by = dd, y2
        s_hits += int(by == y)
    floor = s_hits / max(1, len(surf_rows))
    ok = live >= min(0.55, marg + 0.2) and floor <= marg + 0.2
    run.finish({"oracle_recovery": live, "surface_1nn": floor, "truth_marginal": marg, "n": total},
               {"exec": "COMPLETE", "outcome": "INFRASTRUCTURE" if ok else "INSTRUMENT_FAILED",
                "primary": CARDS_MOD.ALL[card]["primary"],
                "reason": f"oracle {live:.2f} vs marginal {marg:.2f}; artifact-surface 1nn {floor:.2f}"})
    return 0


def _audit_c02(run: CardRun6) -> int:
    n = 3 if SMOKE else 24
    mismatches = 0
    total = 0
    for dom in CARDS_MOD.DOMAINS:
        for lid in bench_lineages("C02", dom, n, split=run.split):
            w0 = W.make_process_world(lid, dom, track="C")
            w = dict(w0, stop_shift=-99.0)                 # the no-stop replica: endpoint match
            base = None                                    # is an order-policy property
            for c in W.CONTROLLERS:
                t = W.simulate(w, W.controller_cfg(w, c, tag=c))
                if t["stopped_at"] is not None:
                    continue
                done = tuple(sorted(a for a in t["final_done"] if "urgent" not in a))
                gc = tuple(sorted({g: sum(1 for s in t["steps"] if s["action"]["goal"] == g and s["action"]["slot"] != "urgent") for g in W.GOALS}.items()))
                if base is None:
                    base = (done, gc)
                else:
                    total += 1
                    mismatches += int((done, gc) != base)
    ok = total > 0 and mismatches == 0
    run.finish({"comparisons": total, "mismatches": mismatches},
               {"exec": "COMPLETE", "outcome": "INFRASTRUCTURE" if ok else "INSTRUMENT_FAILED",
                "primary": CARDS_MOD.ALL["C02"]["primary"],
                "reason": f"{mismatches} of {total} full runs mismatched"})
    return 0


def _audit_f07(run: CardRun6) -> int:
    n = 3 if SMOKE else 16
    rows = []
    for kind in W.FORAGE:
        for dom in CARDS_MOD.DOMAINS:
            for lid in bench_lineages("F07", dom, n, split=run.split):
                w = W.make_process_world(f"{lid}|{kind}", dom, track="F", forage=kind)
                st = _traj_stats(w)
                rows.append(((st["n_steps"], st["mean_section_jump"], int(st["stopped"])), kind))
    marg = 1.0 / len(W.FORAGE)
    hits = 0
    for i, (f, y) in enumerate(rows):
        best, by = None, None
        for j, (g, y2) in enumerate(rows):
            if i == j:
                continue
            dd = sum((a - b) ** 2 for a, b in zip(f, g))
            if best is None or dd < best:
                best, by = dd, y2
        hits += int(by == y)
    floor = hits / max(1, len(rows))
    ok = floor <= marg + 0.2
    run.finish({"blind_surface_rate": floor, "truth_marginal": marg, "n": len(rows)},
               {"exec": "COMPLETE", "outcome": "INFRASTRUCTURE" if ok else "INSTRUMENT_FAILED",
                "primary": CARDS_MOD.ALL["F07"]["primary"],
                "reason": f"blind classifier {floor:.2f} vs marginal {marg:.2f} on oddness/effort statistics"})
    return 0


# ── the exact CPU statistic cards: spec-driven ───────────────────────────────────────
# each entry: (factor kind, levels, statistic key or callable, contrast description)

def _stat_card(run: CardRun6, card: str) -> int:
    n = 4 if SMOKE else max(8, CARDS_MOD.units_for(card) // (2 * 2))
    spec = SPECS[card]
    levels = spec["levels"]
    vals: dict = {lv: {} for lv in levels}
    extras: dict = {lv: [] for lv in levels}
    for lv in levels:
        for dom in CARDS_MOD.DOMAINS:
            for lid in bench_lineages(card, dom, n, split=run.split):
                w = spec["world"](lid + "|" + lv, dom, lv)
                run.register_world(lid + "|" + lv, w)
                st = _traj_stats(w)
                v = spec["stat"](w, st)
                if v is not None:
                    vals[lv][f"{dom}|{lid}"] = float(v)
                    extras[lv].append(st)
                run.row(lid + "|" + lv, arm="exact", factors={"domain": dom, spec["factor"]: lv},
                        truth=str(w["truth"]), scores={"stat": v}, primary_score=float(v) if v is not None else None)
    a, b = levels[0], levels[-1]
    diffs = {u: vals[a][u] - vals[b][u] for u in vals[a] if u in vals[b]}
    ci = _ci(run, diffs, SEED + hash(card) % 1000)
    means = {lv: (sum(v.values()) / len(v)) if v else None for lv, v in vals.items()}
    verdict = run.classify(ci, run.threshold(spec.get("threshold", 0.03)))
    run.finish({"means_by_level": means, "contrast": ci, "levels": levels, "n_per_level": {lv: len(v) for lv, v in vals.items()}},
               {"exec": "COMPLETE", **verdict, "primary": CARDS_MOD.ALL[card]["primary"]},
               rival=CARDS_MOD.ALL[card]["discriminator"])
    return 0


def _w_ctrl(lid, dom, lv):
    return W.make_process_world(lid, dom, track="C", controller=lv)


def _w_value(lid, dom, lv):
    return W.make_process_world(lid, dom, track="V", value=lv)


def _w_forage(lid, dom, lv):
    return W.make_process_world(lid, dom, track="F", forage=lv)


def _w_hist(lid, dom, lv):
    presets = {
        "exposure": dict(attended=False), "attended": dict(attended=True),
        "practiced": dict(practiced=True, feedback=0.8),
        "reward": dict(practiced=True, feedback=1.0), "error": dict(practiced=True, feedback=-0.6),
        "none": dict(practiced=True, feedback=0.0),
        "pressure": dict(constraint=1.0), "free": dict(constraint=0.0),
        "narrow": dict(opportunity=0.0), "wide": dict(opportunity=1.0),
        "yes": dict(practiced=True, feedback=0.8, constraint=1.0), "no": dict(practiced=True, feedback=0.8),
        "pre": dict(practiced=True, feedback=1.0), "post_reversal": dict(practiced=True, feedback=1.0),
        "dated": dict(practiced=True, feedback=0.8), "ordered": dict(practiced=True, feedback=0.8),
        "shuffled": dict(practiced=True, feedback=0.8), "aggregate": dict(practiced=True, feedback=0.8),
        "current_goal": dict(), "selection_history": dict(attended=True),
        "skill": dict(practiced=True, feedback=1.0), "constraint_history": dict(constraint=1.0),
    }
    h = W.make_history(lid, tag=lv, **presets.get(lv, {}))
    return W.make_process_world(lid, dom, track="A", history=h)


def _habit_gap(w, st):
    """The compiled habit's behavioral trace: the revise-rate in the episode."""
    steps = w["trajectory"]["steps"]
    return sum(1 for s in steps if s["action"]["type"] == "revise") / max(1, len(steps))


def _cc_recheck(w, st):
    return 1.0 if st["cc_choice"] == "recheck_sources" else 0.0


def _cc_polish(w, st):
    return 1.0 if st["cc_choice"] == "polish_wording" else 0.0


SPECS = {
    # C track (exact)
    "C04": {"factor": "controller", "levels": ["strict_switch", "concurrent"], "world": _w_ctrl,
            "stat": lambda w, st: st["mean_section_jump"], "threshold": 0.03},
    "C06": {"factor": "controller", "levels": ["concurrent", "strict_switch"], "world": _w_ctrl,
            "stat": lambda w, st: st["hanging_dependencies"], "threshold": 0.05},
    "C08": {"factor": "controller", "levels": ["maintained", "strict_switch"], "world": _w_ctrl,
            "stat": lambda w, st: st["goal_runs"], "threshold": 0.05},
    "C10": {"factor": "controller", "levels": ["focal_habit", "strict_switch"], "world": _w_ctrl,
            "stat": _habit_gap, "threshold": 0.03},
    # A track (exact; the history laws' behavioral separations)
    "A02": {"factor": "history", "levels": ["attended", "exposure"], "world": _w_hist, "stat": _habit_gap},
    "A03": {"factor": "history", "levels": ["practiced", "attended"], "world": _w_hist, "stat": _habit_gap},
    "A04": {"factor": "feedback", "levels": ["reward", "error"], "world": _w_hist, "stat": _habit_gap},
    "A05": {"factor": "imposed", "levels": ["yes", "no"], "world": _w_hist, "stat": _cc_polish},
    "A06": {"factor": "constraint", "levels": ["pressure", "free"], "world": _w_hist, "stat": _habit_gap},
    "A07": {"factor": "toolset", "levels": ["wide", "narrow"], "world": _w_hist, "stat": _habit_gap},
    "A08": {"factor": "phase", "levels": ["post_reversal", "pre"], "world": _w_hist, "stat": _habit_gap},
    "A09": {"factor": "phase", "levels": ["post_reversal", "pre"], "world": _w_hist, "stat": _cc_recheck},
    "A13": {"factor": "history_view", "levels": ["dated", "shuffled"], "world": _w_hist,
            "stat": lambda w, st: st["goal_runs"]},
    "A14": {"factor": "object", "levels": ["skill", "current_goal"], "world": _w_hist, "stat": _cc_recheck},
    # V track (exact; post-diagnostic separations, private cost, visibility)
    "V02": {"factor": "value", "levels": ["accuracy", "prestige"], "world": _w_value, "stat": _cc_recheck},
    "V03": {"factor": "value", "levels": ["accuracy", "prestige"], "world": _w_value, "stat": _cc_recheck},
    "V04": {"factor": "value", "levels": ["prestige", "accuracy"], "world": _w_value, "stat": _cc_polish},
    "V05": {"factor": "value", "levels": ["prestige", "accuracy"], "world": _w_value, "stat": _cc_polish},
    "V07": {"factor": "value", "levels": ["accuracy", "prestige"], "world": _w_value, "stat": _habit_gap},
    "V08": {"factor": "change", "levels": ["genuine", "concealment"], "world": lambda lid, dom, lv: _w_value(lid, dom, "accuracy" if lv == "genuine" else "prestige"), "stat": _cc_recheck},
    "V09": {"factor": "change", "levels": ["value", "context"], "world": lambda lid, dom, lv: _w_value(lid, dom, "prestige" if lv == "value" else "accuracy"), "stat": _cc_polish},
    "V10": {"factor": "change", "levels": ["value", "competence"], "world": lambda lid, dom, lv: _w_value(lid, dom, "prestige" if lv == "value" else "accuracy"), "stat": _cc_polish},
    "V13": {"factor": "model", "levels": ["time_aware", "time_blind"], "world": lambda lid, dom, lv: _w_value(lid, dom, None), "stat": _cc_recheck},
    # F track (exact)
    "F02": {"factor": "forage", "levels": ["explore", "error"], "world": _w_forage,
            "stat": lambda w, st: st["checks_after_probe"], "threshold": 0.05},
    "F03": {"factor": "forage", "levels": ["explore", "habit_misuse"], "world": _w_forage,
            "stat": lambda w, st: st["checks_after_probe"]},
    "F04": {"factor": "forage", "levels": ["error", "explore"], "world": _w_forage,
            "stat": lambda w, st: -(st["probe_to_fix_gap"] if st["probe_to_fix_gap"] is not None else 10)},
    "F05": {"factor": "forage", "levels": ["habit_misuse", "error"], "world": _w_forage,
            "stat": lambda w, st: st["probe_to_fix_gap"] if st["probe_to_fix_gap"] is not None else 10},
    "F06": {"factor": "forage", "levels": ["hidden_goal", "explore"], "world": _w_forage,
            "stat": lambda w, st: sum(1 for s in w["trajectory"]["steps"] if s["action"]["slot"] == "s-link")},
    "F08": {"factor": "forage", "levels": ["explore", "error"], "world": _w_forage,
            "stat": lambda w, st: 1.0 if st["cc_choice"] == "expand_scope" else 0.0},
    "F09": {"factor": "forage", "levels": ["explore", "habit_misuse"], "world": _w_forage,
            "stat": lambda w, st: st["checks_after_probe"]},
    "F10": {"factor": "pattern", "levels": ["structured", "noise"], "world": lambda lid, dom, lv: _w_forage(lid + ("|nz" if lv == "noise" else ""), dom, "explore"),
            "stat": lambda w, st: st["checks_after_probe"]},
}


# ── GPU reader cards ─────────────────────────────────────────────────────────────────
# each asks the reader the track's discriminating question via the shared machinery and
# scores the held-out event against the world's cheap baseline

READER_SPECS = {
    "C03": {"world": _w_ctrl, "levels": W.CONTROLLERS, "endpoint": "next_edit_type_ls"},
    "C05": {"world": _w_ctrl, "levels": ["focal_habit", "strict_switch"], "endpoint": "next_edit_type_ls"},
    "C07": {"world": _w_ctrl, "levels": ["maintained", "strict_switch"], "endpoint": "next_edit_type_ls"},
    "C09": {"world": _w_ctrl, "levels": ["strict_switch"], "endpoint": "next_edit_type_ls"},
    "C11": {"world": _w_ctrl, "levels": W.CONTROLLERS, "endpoint": None},
    "A10": {"world": _w_hist, "levels": ["skill", "current_goal"], "endpoint": "next_edit_type_ls"},
    "A11": {"world": _w_ctrl, "levels": ["focal_habit"], "endpoint": "next_edit_type_ls"},
    "A12": {"world": _w_hist, "levels": ["skill", "current_goal"], "endpoint": "changed_context_ls"},
    "V06": {"world": _w_value, "levels": W.VALUES, "endpoint": None},
    "V11": {"world": _w_value, "levels": W.VALUES, "endpoint": None},
    "V12": {"world": _w_value, "levels": W.VALUES, "endpoint": "changed_context_ls"},
    "V14": {"world": _w_value, "levels": W.VALUES, "endpoint": "changed_context_ls"},
    "F11": {"world": _w_forage, "levels": W.FORAGE, "endpoint": None},
}


SPEC_MODES = {"V06": "breadth_pre", "V11": "breadth_staircase",
              "V12": "probe_choice", "V14": "cc_rich"}


def _consult_idx(w: dict):
    for i, s in enumerate(w["trajectory"]["steps"]):
        if s["action"]["type"] == "consult":
            return i
    return None


def _recut(w: dict, cut: int) -> dict:
    w2 = dict(w)
    w2["cut"] = max(3, min(int(cut), len(w["trajectory"]["steps"]) - 1))
    return w2


def _p_true(res: dict, w: dict):
    post = res.get("posterior") or {}
    if not post:
        return None
    tag = f"value:{w['truth']['value']}" if "value" in w["truth"] else None
    if tag is None:
        return None
    z = sum(post.values()) or 1.0
    return post.get(tag, 0.0) / z, 1.0 / max(1, len(post))


def _small_band(ci: dict, band: float = 0.10, collapse: float = 0.25) -> dict:
    if ci.get("point") is None:
        return {"outcome": "VOID", "reason": "no units"}
    lo, hi = ci["lo"], ci["hi"]
    if hi <= band:
        oc, why = "SUPPORT_CANDIDATE", f"pre-event deviation stays under {band}: the posterior holds its breadth"
    elif lo >= collapse:
        oc, why = "COUNTEREVIDENCE", f"pre-event deviation at or above {collapse}: the posterior collapses before the evidence"
    else:
        oc, why = "INCONCLUSIVE", "the interval spans the breadth band"
    return {"outcome": oc, "reason": why, "point": ci["point"], "ci": [lo, hi],
            "n_units": ci.get("n_units"), "threshold": band}


def _value_reader_card(run: CardRun6, card: str) -> int:
    """V06/V11/V12/V14 on their DECLARED discriminators (the 2026-08-30 reader-spec
    family repair; the first attempt collapsed all four onto two generic statistics).
    V06: posterior deviation from even at one pre-consult cut (support = breadth held).
    V11: the same deviation held across a pre-consult staircase, post-consult descriptive.
    V12: predictive mass the reader puts on the diagnostic consult at the pre-event cut,
         against the prefix baseline's mass; post-resolution probe mass descriptive.
    V14: changed-context log score against the BEST of uniform, leave-one-out domain
         marginal, modal-goal utility, and last-goal utility baselines."""
    mode = SPEC_MODES[card]
    spec = READER_SPECS[card]
    n = 2 if SMOKE else max(6, CARDS_MOD.units_for(card) // (len(spec["levels"]) * 2))
    note = capability_note(run)
    with s5_lib.GpuSession(f"s6_{card.lower()}") as gs:
        for reader in run.readers:
            model, tok, _ = s5_lib.load_model(reader)
            try:
                for lv in spec["levels"]:
                    for dom in CARDS_MOD.DOMAINS:
                        for lid in bench_lineages(card, dom, n, split=run.split):
                            ulid = f"{lid}|{lv}"
                            if run.is_done(reader, ulid, "CR"):
                                continue
                            run.check_deadline()
                            w = spec["world"](ulid, dom, lv)
                            ci_ = _consult_idx(w)
                            if ci_ is None:
                                run.row(ulid, reader=reader, arm="CR", valid=False,
                                        validity_reason="no_consult", factors={"domain": dom, "level": lv})
                                run.unit_complete(reader, ulid, "CR")
                                continue
                            run.register_world(ulid, w)
                            variants = []
                            if mode == "breadth_pre":
                                variants = [("pre", _recut(w, ci_))]
                            elif mode == "breadth_staircase":
                                variants = [("pre40", _recut(w, ci_ * 0.4)), ("pre90", _recut(w, ci_ * 0.9))]
                                if w["cut"] > ci_ + 1:
                                    variants.append(("post", w))
                            elif mode == "probe_choice":
                                variants = [("probe", _recut(w, ci_))]
                                if w["cut"] > ci_ + 1:
                                    variants.append(("probefp", w))
                            elif mode == "cc_rich":
                                variants = [("cc", w)]
                            bad = False
                            rows_out = []
                            for vtag, wv in variants:
                                res = A.run_arm("CR", model, tok, wv, A.BUDGET_SMALL)
                                if res["predictions"] is None:
                                    bad = True
                                    break
                                prim = None
                                sc = {}
                                if mode in ("breadth_pre", "breadth_staircase"):
                                    pt = _p_true(res, wv)
                                    prim = abs(pt[0] - pt[1]) if pt else None
                                elif mode == "probe_choice":
                                    ptype = (res["predictions"].get("next_edit_type") or {}).get("consult", 0.0)
                                    btype = W.cheap_baselines(wv)["next_edit_type"].get("consult", 0.0)
                                    prim = ptype - btype
                                elif mode == "cc_rich":
                                    sc = P.score_predictions(wv, res["predictions"])
                                    prim = sc.get("changed_context_ls")
                                rows_out.append((vtag, prim, sc, res))
                            if bad:
                                run.row(ulid, reader=reader, arm="CR", valid=False, validity_reason="unrealized",
                                        factors={"domain": dom, "level": lv})
                                run.unit_complete(reader, ulid, "CR")
                                continue
                            for vtag, prim, sc, res in rows_out:
                                run.row(f"{ulid}|{vtag}", reader=reader, arm="CR", truth=str(w["truth"]),
                                        factors={"domain": dom, "level": lv, "variant": vtag},
                                        scores=sc, primary_score=prim, budget=res["budget"],
                                        extra={"posterior": res["posterior"],
                                               "abstain": res["predictions"]["abstain"]})
                            run.unit_complete(reader, ulid, "CR")
            finally:
                s5_lib.free_model(model)
    gpu = gs.held_s
    rows = [r for r in run.rows() if r["valid"] and r["primary_score"] is not None]

    def vals_of(*vtags):
        return {f"{r['model_id']}|{r['unit_id']}": r["primary_score"] for r in rows
                if r["factors"].get("variant") in vtags}

    metrics: dict = {"n": len(rows), "mode": mode}
    if mode == "breadth_pre":
        ci = _ci(run, vals_of("pre"), SEED + 81)
        metrics["pre_event_deviation"] = ci
        verdict = {"exec": "COMPLETE", **_small_band(ci),
                   "primary": "posterior deviation from even at the pre-consult cut (support = breadth held, band 0.10)"}
    elif mode == "breadth_staircase":
        ci = _ci(run, vals_of("pre40", "pre90"), SEED + 82)
        post = _ci(run, vals_of("post"), SEED + 83)
        metrics["pre_staircase_deviation"] = ci
        metrics["post_event_deviation"] = post
        verdict = {"exec": "COMPLETE", **_small_band(ci),
                   "primary": "posterior deviation from even across the pre-consult staircase (support = class preserved, band 0.10); post-event deviation reported"}
    elif mode == "probe_choice":
        ci = _ci(run, vals_of("probe"), SEED + 84)
        fp = _ci(run, vals_of("probefp"), SEED + 85)
        metrics["diagnostic_probe_elevation"] = ci
        metrics["post_resolution_probe_mass"] = fp
        verdict = {"exec": "COMPLETE", **run.classify(ci, run.threshold()),
                   "primary": "predictive mass on the diagnostic consult at the pre-event cut minus the prefix baseline's mass"}
    else:  # cc_rich
        by_dom: dict = {}
        for r in rows:
            wv = spec["world"](r["unit_id"].rsplit("|", 1)[0], r["factors"]["domain"], r["factors"]["level"])
            ch = wv["hidden"]["changed_context"]["choice"]
            by_dom.setdefault(r["factors"]["domain"], []).append(ch)
        diffs = {}
        for r in rows:
            base_ulid = r["unit_id"].rsplit("|", 1)[0]
            wv = spec["world"](base_ulid, r["factors"]["domain"], r["factors"]["level"])
            truth_choice = wv["hidden"]["changed_context"]["choice"]
            steps = wv["trajectory"]["steps"][:wv["cut"]]
            goals = [s["action"].get("goal") for s in steps if s["action"].get("goal")]
            cands = [math.log(1.0 / len(W.CC_OPTIONS))]
            for g in ({max(set(goals), key=goals.count)} if goals else set()) | ({goals[-1]} if goals else set()):
                if g in W.CC_UTIL:
                    ex = {k: math.exp(W.CC_UTIL[g][k]) for k in W.CC_OPTIONS}
                    z = sum(ex.values())
                    cands.append(math.log(max(1e-9, ex[truth_choice] / z)))
            pool = by_dom.get(r["factors"]["domain"], [])
            n_others = len(pool) - 1
            if n_others > 0:
                c_others = sum(1 for x in pool if x == truth_choice) - 1
                cands.append(math.log((c_others + 1) / (n_others + len(W.CC_OPTIONS))))
            diffs[f"{r['model_id']}|{r['unit_id']}"] = r["primary_score"] - max(cands)
        ci = _ci(run, diffs, SEED + 86)
        metrics["cc_vs_best_rich_baseline"] = ci
        verdict = {"exec": "COMPLETE", **run.classify(ci, run.threshold()),
                   "primary": "changed-context log score against the best of uniform, LOO domain-marginal, modal-goal, and last-goal baselines"}
    if note:
        verdict["capability_note"] = note
    run.finish(metrics, verdict, gpu, rival=CARDS_MOD.ALL[card]["discriminator"])
    return 0


def _reader_card(run: CardRun6, card: str) -> int:
    if card in SPEC_MODES:
        return _value_reader_card(run, card)
    spec = READER_SPECS[card]
    n = 2 if SMOKE else max(6, CARDS_MOD.units_for(card) // (len(spec["levels"]) * 2))
    note = capability_note(run)
    with s5_lib.GpuSession(f"s6_{card.lower()}") as gs:
        for reader in run.readers:
            model, tok, _ = s5_lib.load_model(reader)
            try:
                for lv in spec["levels"]:
                    for dom in CARDS_MOD.DOMAINS:
                        for lid in bench_lineages(card, dom, n, split=run.split):
                            ulid = f"{lid}|{lv}"
                            if run.is_done(reader, ulid, "CR"):
                                continue
                            run.check_deadline()
                            w = spec["world"](ulid, dom, lv)
                            run.register_world(ulid, w)
                            res = A.run_arm("CR", model, tok, w, A.BUDGET_SMALL)
                            if res["predictions"] is None:
                                run.row(ulid, reader=reader, arm="CR", valid=False, validity_reason="unrealized",
                                        factors={"domain": dom, spec.get("factor", "level"): lv})
                                run.unit_complete(reader, ulid, "CR")
                                continue
                            sc = P.score_predictions(w, res["predictions"])
                            sb = P.score_baselines(w)
                            key = spec["endpoint"]
                            prim = None
                            if key and sc.get(key) is not None and sb.get(key) is not None:
                                prim = sc[key] - sb[key]
                            elif key is None:
                                prim = sc.get("posterior_on_truth")
                            run.row(ulid, reader=reader, arm="CR", truth=str(w["truth"]),
                                    factors={"domain": dom, "level": lv}, scores=sc,
                                    primary_score=prim, budget=res["budget"],
                                    extra={"posterior": res["posterior"], "abstain": res["predictions"]["abstain"]})
                            run.unit_complete(reader, ulid, "CR")
            finally:
                s5_lib.free_model(model)
    gpu = gs.held_s
    rows = [r for r in run.rows() if r["valid"] and r["primary_score"] is not None]
    vals = {f"{r['model_id']}|{r['unit_id']}": r["primary_score"] for r in rows}
    ci = _ci(run, vals, SEED + 77)
    by_level = {}
    for lv in spec["levels"]:
        sub = {f"{r['model_id']}|{r['unit_id']}": r["primary_score"] for r in rows if r["factors"].get("level") == lv}
        by_level[str(lv)] = _ci(run, sub, SEED + 78)
    if spec["endpoint"] is None:
        marg = 1.0 / len(spec["levels"]) if len(spec["levels"]) > 1 else 0.5
        shifted = {k: v - marg for k, v in vals.items()}
        ci = _ci(run, shifted, SEED + 79)
        primary_desc = f"posterior mass on the true latent minus the {marg:.2f} marginal"
    else:
        primary_desc = f"reader {spec['endpoint']} minus the cheap baseline on the discriminating event"
    verdict = {"exec": "COMPLETE", **run.classify(ci, run.threshold()), "primary": primary_desc}
    if note:
        verdict["capability_note"] = note
    abst = [bool(r["extra"].get("abstain")) for r in rows]
    run.finish({"primary": ci, "by_level": by_level, "abstain_rate": (sum(abst) / len(abst)) if abst else None,
                "n": len(rows)}, verdict, gpu, rival=CARDS_MOD.ALL[card]["discriminator"])
    return 0


def run_card(run: CardRun6) -> int:
    card = run.card
    if card in ("C01", "A01", "V01", "F01"):
        kinds = {"C01": list(W.CONTROLLERS), "A01": ["rich", "attention_only"],
                 "V01": list(W.VALUES), "F01": list(W.FORAGE)}[card]
        forced = {"C01": "controller", "V01": "value", "F01": "forage"}.get(card, "")
        if card == "A01":
            n = 3 if SMOKE else 16
            hits = total = 0
            for law in kinds:
                for dom in CARDS_MOD.DOMAINS:
                    for lid in bench_lineages(card, dom, n, split=run.split):
                        h = W.make_history(lid, practiced=(law == "rich"), feedback=0.8 if law == "rich" else 0.0, tag=law)
                        w = W.make_process_world(f"{lid}|{law}", dom, track="A", history=h)
                        post = W.oracle_posterior(w, upto=len(w["trajectory"]["steps"]))
                        best = max(post, key=post.get)
                        hits += int(best.split(":")[1] == law)
                        total += 1
            live = hits / max(1, total)
            ok = live >= 0.6
            run.finish({"oracle_recovery": live, "n": total},
                       {"exec": "COMPLETE", "outcome": "INFRASTRUCTURE" if ok else "INSTRUMENT_FAILED",
                        "primary": CARDS_MOD.ALL[card]["primary"], "reason": f"law recovery {live:.2f}"})
            return 0
        return _audit_liveness(run, card, kinds, forced)
    if card == "C02":
        return _audit_c02(run)
    if card == "F07":
        return _audit_f07(run)
    if card in SPECS:
        return _stat_card(run, card)
    if card in READER_SPECS:
        return _reader_card(run, card)
    raise ValueError(f"no world-track handler for {card}")
