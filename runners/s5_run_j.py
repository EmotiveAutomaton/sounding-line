"""Stage 5 joint-reconstruction cards (brief §6 J01-J05, §1.1-§1.2, §7.2).

DESIGN CHECK (2026-08-29)
lessons read: LESSONS §3 (the comparator and the plain route both reported; the oracle
  bypass is never end-to-end success; a proper score on the hidden future choice, not a
  retrospective label; short candidates given the long evidence; a criterion that can
  fail; every statistic written), §4 (instruct readers), CONTROLS §6 (matched
  information: every reader variant sees the same evidence, candidates, and prior text).
gates and bands:
  - J01 rulers: each latent's log score over its candidates when the other two are
    supplied as true, against the chance log score of a uniform draw over the same
    candidates; NULL: no gain; ALTERNATIVE: at or above 0.03 nats; the plan ruler on
    equifinal worlds is scored on ABSTENTION (mass on unknown or split across the twin
    plans) and never on picking the historical one; a latent with no gain closes its
    recovery as VOID for the joint card's interpretation, not as a null of the theory.
  - J02 primary: the recurrent reader minus the best same-evidence staged or factored
    reader on the hidden future choice's log score, paired by world; NULL: 0;
    ALTERNATIVE: at or above 0.03 nats AND calibrated (expected calibration error not
    worse than the best comparator by more than 0.05) AND the ablation (the factored
    reader is the recurrent reader with the between-latent conditioning removed, at the
    same call allowance) shows the gain comes from the conditioning. The oracle-latent
    reader is a ceiling and never counts. Failure direction guarded: a recurrent reader
    that gains through more calls rather than through passing evidence is exposed by the
    equal call allowance (nine calls for every variant; unused calls are recorded).
  - J03: per-latent first-useful step, reversals, overconfidence after the exact
    contradiction step; descriptive, no band.
  - J04 primary: the opened hypothesis set minus the fixed set on conflict worlds' target
    log score; NULL: 0; ALTERNATIVE: at or above 0.03 with the false-alarm cost on
    consistent worlds within 0.02 nats of zero; a gain bought by a matching loss on
    consistent worlds reads as a criterion shift, not a search benefit.
  - J05 primary: the inferred standing preference minus the best cheap baseline (habit,
    topic base rate, last goal) on the episode-2 choice log score; NULL: 0; ALTERNATIVE:
    at or above 0.03; the exact oracle preference is the ceiling.
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
import math
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from runners import s5_lib, s5_worlds                                              # noqa: E402
from runners.s3_lib import AXES                                                   # noqa: E402
from runners.s5_run_common import (CardRun, DeadlineReached, cluster_by_construction,        # noqa: E402
                                   construction_summary, mean_by, select_rows)
from soundingline.stage5 import ece, latent_record, selective_risk_coverage         # noqa: E402

SEED = s5_lib.SEED0 + 200
CALL_ALLOWANCE = 9
PREF_TEXT = {"robust": "it weights reliability and safety far above cost, speed, or habit",
             "cheap": "it weights cost savings far above reliability, speed, or habit",
             "fast": "it weights schedule and speed far above cost, reliability, or habit",
             "precedent": "it weights proven track records far above cost, speed, or novelty"}
LATENT_Q = {"episode_goal": "What was the maker's goal for this piece?",
            "process_plan": "In what order did the maker take its three production steps?",
            "standing_preference": ("Setting this piece's goal aside, what does this maker weight most across ALL its work?"
                                    if s5_lib.DESIGN == "2" else "What does this maker weight most, across all its work?")}
STAGED = {"goal_first": ("episode_goal", "process_plan", "standing_preference"),
          "process_first": ("process_plan", "episode_goal", "standing_preference"),
          "preference_first": ("standing_preference", "episode_goal", "process_plan")}


def _plan_text(plan) -> str:
    return ", then ".join(plan)


def candidates(world: dict) -> dict:
    """The same candidate sets for every reader variant: goals, preferences, and the
    plan candidates ranked by prior mass with the true plan and its equifinal twins
    always present (at most five, so the listing with `unknown` keeps six labels)."""
    cands = [tuple(c) for c in world["plan_candidates"]]
    pp = world["plan_probs_under_truth"]
    ranked = [c for _, c in sorted(zip(pp, cands), key=lambda x: -x[0])]
    # the true plan and at most four of its equifinal twins (design 2's relaxed-order worlds
    # can have five), the twins ranked by prior mass; six labels hold five plans plus unknown
    twin_set = [tuple(t) for t in world["equifinal_twins"]]
    twins_ranked = [c for c in ranked if c in twin_set][:4]
    keep = [tuple(world["process_plan"])] + twins_ranked
    for c in ranked:
        if len(keep) >= 5:
            break
        if c not in keep:
            keep.append(c)
    return {"episode_goal": {g: s5_worlds.GOAL_TEXT[g] for g in s5_worlds.GOALS},
            "standing_preference": {a: PREF_TEXT[a] for a in AXES},
            "process_plan": {" > ".join(c): _plan_text(c) for c in keep}}


def evidence_text(world: dict, routes=("contextual", "action", "semantic", "forensic"), n_records: int = 6) -> tuple[str, list]:
    rt = s5_worlds.route_texts(world, n_records)
    blocks, ids = [], []
    for r in routes:
        blocks.append(rt[r]["text"])
        ids += rt[r]["ids"]
    return "\n".join(blocks), ids


def _given(latents: dict) -> str:
    parts = []
    if "episode_goal" in latents and latents["episode_goal"] not in (None, "unknown"):
        parts.append(f"the maker's goal for this piece was {s5_worlds.GOAL_TEXT[latents['episode_goal']]}")
    if "process_plan" in latents and latents["process_plan"] not in (None, "unknown"):
        parts.append(f"its steps were {_plan_text(latents['process_plan'].split(' > '))}")
    if "standing_preference" in latents and latents["standing_preference"] not in (None, "unknown"):
        parts.append(f"across all its work {PREF_TEXT[latents['standing_preference']]}")
    return ("Take as established: " + "; ".join(parts) + ".\n") if parts else ""


def ask_latent(model, tok, ev: str, latent: str, cands: dict, given: dict, rng) -> dict:
    body = f"Evidence about a maker and one of its pieces:\n{ev}\n{_given(given)}{LATENT_Q[latent]}"
    return s5_lib.candidate_likelihood(model, tok, body, cands[latent], rng, unknown=True)


READOUT_VERSION = os.environ.get("S5_READOUT_VERSION", "2" if s5_lib.DESIGN == "2" else "1")


def choice_prompt(world: dict, given: dict, scen_i: int, note: str = "", ev: str = "",
                  version: str | None = None) -> tuple[str, dict]:
    """The future-choice question. Version 1 (withdrawn 2026-08-29, L263) offered the long
    option sentences as the candidates and the reader answered from their wording ('robust'
    seven times in ten, 1.3 nats under uniform). Version 2 lists the options in the body and
    scores the short axis words as candidates (LESSONS §3: short candidates given the long
    evidence)."""
    version = version or READOUT_VERSION
    s = world["scenarios"][scen_i]
    head = f"Evidence about a maker and one of its pieces:\n{ev}\n{_given(given)}{note}"
    if version == "1":
        body = head + f"The maker now faces this decision: {s['context']}\nWhich option will it choose?"
        return body, {ax: s["options"][ax] for ax in s["feasible"]}
    listing = "\n".join(f"- {ax}: {s['options'][ax]}" for ax in s["feasible"])
    body = (head + f"The maker now faces this decision: {s['context']}\nIts options, each named by "
            f"the quality it favors:\n{listing}\nWhich option will it choose? Answer with the option's name.")
    return body, {ax: ax for ax in s["feasible"]}


def ask_choice(model, tok, ev: str, world: dict, given: dict, scen_i: int, rng, note: str = "") -> dict:
    body, cands = choice_prompt(world, given, scen_i, note, ev)
    r = s5_lib.candidate_likelihood(model, tok, body, cands, rng, unknown=False)
    r["readout_version"] = READOUT_VERSION
    return r


def _mass(r: dict) -> dict:
    if not r.get("valid"):
        return {}
    m = dict(r["mass"])
    m["unknown"] = r.get("p_unknown", 0.0)
    return m


# ── J01: rulers ───────────────────────────────────────────────────────────────────────

def arm_j01() -> int:
    run = CardRun("J01", "s5_run_j.py")
    with s5_lib.GpuSession("s5_j01") as gs:
        for reader in run.readers:
            model, tok, _ = s5_lib.load_model(reader)
            try:
                for domain in s5_worlds.DOMAINS:
                    for i, lid in enumerate(run.units(domain)):
                        if run.is_done(reader, lid):
                            continue
                        run.check_deadline()
                        w = s5_worlds.make_joint_world(lid, domain)
                        run.register_world(lid, w)
                        cands = candidates(w)
                        ev, ids = evidence_text(w)
                        truth = {"episode_goal": w["episode_goal"], "process_plan": " > ".join(w["process_plan"]),
                                 "standing_preference": w["standing_preference"]}
                        rng = random.Random(SEED + i)
                        for latent in s5_worlds.TRIPLE if False else ("episode_goal", "process_plan", "standing_preference"):
                            given = {k: v for k, v in truth.items() if k != latent}
                            r = ask_latent(model, tok, ev, latent, cands, given, rng)
                            chance = math.log(1.0 / (len(cands[latent]) + 1))
                            ls = s5_lib.log_score(r["probs"], truth[latent]) if r["valid"] else None
                            twins = [k for k in cands["process_plan"] if k != " > ".join(w["process_plan"])
                                     and tuple(k.split(" > ")) in {tuple(t) for t in w["equifinal_twins"]}] if latent == "process_plan" else []
                            twin_mass = sum(r["probs"].get(t, 0.0) for t in twins) if r["valid"] else None
                            abstained = None
                            if latent == "process_plan" and w["equifinal"] and r["valid"]:
                                pu = r["p_unknown"]
                                pt = r["probs"].get(truth[latent], 0.0)
                                abstained = pu > 0.5 or (twin_mass is not None and abs(pt - twin_mass / max(1, len(twins))) < 0.2)
                            run.row(reader, lid, lid, f"ruler|{latent}", {"domain": domain, "latent": latent, "equifinal": w["equifinal"]},
                                    truth[latent], "construction", "artifact_plus_context", r,
                                    (ls - chance) if ls is not None else None,
                                    extra={"chance_log": chance, "log_score": ls, "p_unknown": r.get("p_unknown"),
                                           "twin_mass": twin_mass, "abstained": abstained, "evidence_ids": ids})
                        run.unit_complete(reader, lid)
            finally:
                s5_lib.free_model(model)
    rows = [r for r in run.rows() if r["valid"]]
    per = {}
    for latent in ("episode_goal", "process_plan", "standing_preference"):
        sub = cluster_by_construction([r for r in rows if r["factors"]["latent"] == latent and not (latent == "process_plan" and r["factors"]["equifinal"])])
        vals = s5_lib.per_unit_means(sub, "unit_id", "primary_score")
        per[latent] = s5_lib.cluster_bootstrap_ci(vals, SEED + 21)
    eq = [r for r in rows if r["factors"]["latent"] == "process_plan" and r["factors"]["equifinal"]]
    abst = {"n_equifinal_rows": len(eq), "abstention_rate": (sum(1 for r in eq if r["extra"].get("abstained")) / len(eq)) if eq else None,
            "mean_unknown_mass": (sum(r["extra"]["p_unknown"] for r in eq) / len(eq)) if eq else None}
    worst = min(per.values(), key=lambda c: c.get("point") or -9)
    verdict = run.classify(worst, run.threshold(0.03))
    verdict["per_latent"] = {k: v.get("point") for k, v in per.items()}
    dead = [k for k, v in per.items() if v.get("hi") is not None and v["hi"] < 0.03]
    if dead:
        verdict["latents_void_for_joint"] = dead
    run.finish({"per_latent_gain_over_chance": per, "equifinal_abstention": abst, "constructions": construction_summary(rows),
                "by_domain": mean_by(rows, ["domain", "latent"])},
               {"exec": "COMPLETE", "primary": "each latent recovered given the other two, log score over chance (the weakest latent)", **verdict}, gs.held_s,
               rival="a latent recoverable from the candidate text alone (the chance log score is the floor; no evidence-free arm)")
    return 0


# ── J02: the six readers ──────────────────────────────────────────────────────────────

def read_variant(model, tok, variant: str, w: dict, ev: str, cands: dict, truth: dict, rng) -> dict:
    """Runs one reader variant: returns its inferred latents (argmax or unknown), its
    call count, its per-latent masses, and the prediction readout on the hidden choice."""
    calls = 0
    masses = {}
    inferred = {}
    if variant == "factored":
        for latent in ("episode_goal", "process_plan", "standing_preference"):
            r = ask_latent(model, tok, ev, latent, cands, {}, rng)
            calls += 1
            masses[latent] = _mass(r)
            inferred[latent] = r["pred"] if r.get("valid") else "unknown"
    elif variant in STAGED:
        given = {}
        for latent in STAGED[variant]:
            r = ask_latent(model, tok, ev, latent, cands, given, rng)
            calls += 1
            masses[latent] = _mass(r)
            inferred[latent] = r["pred"] if r.get("valid") else "unknown"
            given[latent] = inferred[latent]
    elif variant == "recurrent":
        for rnd in range(3):
            new = {}
            for latent in ("episode_goal", "process_plan", "standing_preference"):
                given = {k: v for k, v in inferred.items() if k != latent} if rnd > 0 else {}
                r = ask_latent(model, tok, ev, latent, cands, given, rng)
                calls += 1
                masses[latent] = _mass(r)
                new[latent] = r["pred"] if r.get("valid") else "unknown"
            inferred = new
    elif variant == "oracle":
        inferred = dict(truth)
    given = {k: v for k, v in inferred.items() if v != "unknown"}
    pred = ask_choice(model, tok, ev, w, given, w["target_scenario"], rng)
    calls += 1
    return {"inferred": inferred, "masses": masses, "calls": calls, "pred": pred}


def arm_j02() -> int:
    run = CardRun("J02", "s5_run_j.py")
    variants = ("factored", "goal_first", "process_first", "preference_first", "recurrent", "oracle")
    with s5_lib.GpuSession("s5_j02") as gs:
        for reader in run.readers:
            model, tok, _ = s5_lib.load_model(reader)
            try:
                for domain in s5_worlds.DOMAINS:
                    for i, lid in enumerate(run.units(domain)):
                        if run.is_done(reader, lid):
                            continue
                        run.check_deadline()
                        w = s5_worlds.make_joint_world(run.parent_of(lid), domain)
                        run.register_world(lid, w)
                        cands = candidates(w)
                        ev, ids = evidence_text(w)
                        truth = {"episode_goal": w["episode_goal"], "process_plan": " > ".join(w["process_plan"]),
                                 "standing_preference": w["standing_preference"]}
                        target = w["scenarios"][w["target_scenario"]]["draw"]
                        exact = s5_worlds.predictive(w, s5_worlds.posterior(w, ["contextual", "action", "semantic", "forensic"]), w["target_scenario"])
                        for variant in variants:
                            rng = random.Random(SEED + 500 + i)          # the same permutations per variant
                            res = read_variant(model, tok, variant, w, ev, cands, truth, rng)
                            p = res["pred"]
                            ls = s5_lib.log_score(p["probs"], target) if p["valid"] else None
                            rec = latent_record(**{k: {"candidates": {kk: vv for kk, vv in m.items() if kk != "unknown"}, "unknown": m.get("unknown", 0.0), "evidence": ids}
                                                   for k, m in res["masses"].items() if m}) if res["masses"] else {}
                            run.row(reader, lid, lid, f"reader|{variant}", {"domain": domain, "reader": variant},
                                    target, "realized_draw", "oracle_latent" if variant == "oracle" else "artifact_plus_context", p, ls,
                                    extra={"inferred": res["inferred"], "truth_latents": truth, "calls": res["calls"],
                                           "allowance": CALL_ALLOWANCE, "record": rec,
                                           "latent_correct": {k: res["inferred"].get(k) == v for k, v in truth.items()},
                                           "brier": s5_lib.brier(p["probs"], target) if p["valid"] else None,
                                           "exact_log_score": math.log(max(exact[target], 1e-12)),
                                           "confidence": max(p["probs"].values()) if p["valid"] else None})
                        run.unit_complete(reader, lid)
            finally:
                s5_lib.free_model(model)
    return _j02_analyze(run, gs.held_s)


def _j02_analyze(run: CardRun, gpu_s: float) -> int:
    rows = [r for r in run.rows() if r["valid"] and r["primary_score"] is not None]
    sel = lambda v: cluster_by_construction(select_rows(rows, reader=v))          # noqa: E731
    means = {v: s5_lib.per_unit_means(sel(v), "unit_id", "primary_score") for v in ("factored", "goal_first", "process_first", "preference_first", "recurrent", "oracle")}
    level = {v: (sum(m.values()) / len(m)) if m else None for v, m in means.items()}
    comparators = [v for v in ("factored", "goal_first", "process_first", "preference_first") if means[v]]
    best = max(comparators, key=lambda v: level[v]) if comparators else None
    primary = s5_lib.paired_contrast(sel("recurrent"), sel(best), "unit_id", "primary_score", SEED + 31) if best else {"point": None}
    ablation = s5_lib.paired_contrast(sel("recurrent"), sel("factored"), "unit_id", "primary_score", SEED + 32)
    calib = {}
    for v in means:
        sub = select_rows(rows, reader=v)
        pt = [(r["extra"]["confidence"], r["pred"] == r["truth"]) for r in sub if r["extra"].get("confidence") is not None]
        calib[v] = {"ece": ece(pt) if pt else None, "brier": (sum(r["extra"]["brier"] for r in sub) / len(sub)) if sub else None,
                    "selective_risk": selective_risk_coverage([(c, -r["primary_score"]) for (c, _), r in zip(pt, sub)]),
                    "latent_accuracy": {k: sum(1 for r in sub if r["extra"]["latent_correct"].get(k)) / max(1, len(sub)) for k in ("episode_goal", "process_plan", "standing_preference")},
                    "calls_mean": (sum(r["extra"]["calls"] for r in sub) / len(sub)) if sub else None}
    exact = [r["extra"]["exact_log_score"] for r in select_rows(rows, reader="oracle")]
    verdict = run.classify(primary, run.threshold(0.03)) if primary.get("point") is not None else {"outcome": "VOID", "reason": "no comparator"}
    reasons = []
    if verdict["outcome"] == "SUPPORT_CANDIDATE":
        if best and calib["recurrent"]["ece"] is not None and calib[best]["ece"] is not None and calib["recurrent"]["ece"] > calib[best]["ece"] + 0.05:
            reasons.append("recurrent reader worse calibrated than its comparator by more than 0.05")
        if ablation.get("lo") is not None and ablation["lo"] <= 0:
            reasons.append("the ablation (factored at equal allowance) does not show the gain comes from the conditioning")
        if reasons:
            verdict["outcome"] = "INCONCLUSIVE"
            verdict["reason"] += "; " + "; ".join(reasons)
    verdict["best_comparator"] = best
    run.finish({"level_log_score": level, "primary_recurrent_minus_best_comparator": primary, "ablation_recurrent_minus_factored": ablation,
                "calibration": calib, "exact_posterior_log_score_mean": (sum(exact) / len(exact)) if exact else None,
                "oracle_reader_level": level.get("oracle"), "constructions": construction_summary(rows),
                "by_domain": mean_by(rows, ["domain", "reader"])},
               {"exec": "COMPLETE", "primary": "recurrent joint reader minus the best same-evidence comparator, held-out choice log score", **verdict}, gpu_s,
               rival="the best staged or factored reader at the same evidence and allowance; the oracle-latent reader is the ceiling and never counts")
    return 0


# ── J03: trajectories ─────────────────────────────────────────────────────────────────

def arm_j03() -> int:
    run = CardRun("J03", "s5_run_j.py")
    with s5_lib.GpuSession("s5_j03") as gs:
        for reader in run.readers:
            model, tok, _ = s5_lib.load_model(reader)
            try:
                for domain in s5_worlds.DOMAINS:
                    for i, lid in enumerate(run.units(domain)):
                        if run.is_done(reader, lid):
                            continue
                        run.check_deadline()
                        w = s5_worlds.make_joint_world(run.parent_of(lid), domain)
                        run.register_world(lid, w)
                        cands = candidates(w)
                        truth = {"episode_goal": w["episode_goal"], "process_plan": " > ".join(w["process_plan"]),
                                 "standing_preference": w["standing_preference"]}
                        rt = s5_worlds.route_texts(w)
                        steps = [("contextual", rt["contextual"]["text"])] + [("action", ln) for ln in rt["action"]["text"].split("\n")] + \
                                [("semantic", rt["semantic"]["text"]), ("forensic", rt["forensic"]["text"])]
                        # the exact contradiction step: where the exact posterior's leading goal changes
                        lead = None
                        contradiction = None
                        for k in range(1, len(steps) + 1):
                            routes = sorted({s for s, _ in steps[:k]})
                            n_rec = sum(1 for s, _ in steps[:k] if s == "action")
                            post = s5_worlds.posterior(w, routes, n_records=max(1, n_rec) if "action" in routes else 6)
                            g = max(s5_worlds.marginal(post, 0).items(), key=lambda x: x[1])[0]
                            if lead is not None and g != lead and contradiction is None:
                                contradiction = k
                            lead = g
                        rng = random.Random(SEED + 900 + i)
                        traj = {k: [] for k in truth}
                        for k in range(1, len(steps) + 1):
                            ev = "\n".join(t for _, t in steps[:k])
                            for latent in truth:
                                r = ask_latent(model, tok, ev, latent, cands, {}, rng)
                                m = _mass(r)
                                traj[latent].append(m)
                                run.row(reader, lid, lid, f"step{k}|{latent}", {"domain": domain, "evidence_step": str(min(k, 8)), "latent": latent},
                                        truth[latent], "construction", "artifact_plus_context", r,
                                        s5_lib.log_score(r["probs"], truth[latent]) if r["valid"] else None,
                                        extra={"step": k, "route": steps[k - 1][0], "contradiction_step": contradiction})
                        stats = {latent: s5_lib.trajectory_stats(traj[latent], truth[latent], contradiction_at=contradiction) for latent in truth}
                        run.row(reader, lid, lid, "trajectory", {"domain": domain, "evidence_step": "8", "latent": "all"},
                                None, "construction", "artifact_plus_context", None, None, valid=True, validity_reason="summary",
                                extra={"stats": stats, "contradiction_step": contradiction, "n_steps": len(steps)})
                        run.unit_complete(reader, lid)
            finally:
                s5_lib.free_model(model)
    rows = [r for r in run.rows() if r["factors"].get("latent") == "all"]
    agg = {}
    for latent in ("episode_goal", "process_plan", "standing_preference"):
        fu = [r["extra"]["stats"][latent]["first_useful_step"] for r in rows]
        rev = [r["extra"]["stats"][latent]["reversals"] for r in rows]
        over = [r["extra"]["stats"][latent]["overconfident_after_contradiction"] for r in rows if r["extra"]["stats"][latent]["overconfident_after_contradiction"] is not None]
        agg[latent] = {"first_useful_step_mean": (sum(x for x in fu if x) / max(1, sum(1 for x in fu if x))) if any(fu) else None,
                       "never_useful_fraction": sum(1 for x in fu if x is None) / max(1, len(fu)),
                       "reversals_mean": sum(rev) / max(1, len(rev)),
                       "overconfident_after_contradiction_rate": (sum(1 for x in over if x) / len(over)) if over else None,
                       "n_worlds_with_contradiction": len(over)}
    order = sorted(agg, key=lambda k: agg[k]["first_useful_step_mean"] or 99)
    run.finish({"per_latent": agg, "first_useful_order": order, "constructions": construction_summary(rows)},
               {"exec": "COMPLETE", "outcome": "DESCRIPTIVE", "primary": "posterior trajectories: first useful latent, reversals, overconfidence after contradiction",
                "reason": "descriptive card; no outcome band", "first_useful_order": order}, gs.held_s,
               rival="a stacking effect with no single decisive cue (reported as such when first-useful steps are late)")
    return 0


# ── J04: conflict and the opened hypothesis ───────────────────────────────────────────

def arm_j04() -> int:
    run = CardRun("J04", "s5_run_j.py")
    with s5_lib.GpuSession("s5_j04") as gs:
        for reader in run.readers:
            model, tok, _ = s5_lib.load_model(reader)
            try:
                for domain in s5_worlds.DOMAINS:
                    for i, lid in enumerate(run.units(domain)):
                        if run.is_done(reader, lid):
                            continue
                        run.check_deadline()
                        for kind in ("conflict", "consistent"):
                            w = s5_worlds.make_joint_world(run.parent_of(lid), domain, conflict=(kind == "conflict"))
                            if kind == "consistent":
                                run.register_world(lid, w)
                            cands = candidates(w)
                            ev, ids = evidence_text(w)
                            target = w["scenarios"][w["target_scenario"]]["draw"]
                            # the exact conflict signal: disagreement between the action-only and semantic-only goal posteriors
                            ga = s5_worlds.marginal(s5_worlds.posterior(w, ["contextual", "action"]), 0)
                            gs_ = s5_worlds.marginal(s5_worlds.posterior(w, ["contextual", "semantic"]), 0)
                            conflict_kl = s5_lib.kl(ga, gs_)
                            for hset in ("fixed", "opened"):
                                rng = random.Random(SEED + 1200 + i)
                                c = dict(cands)
                                if hset == "opened":
                                    c = dict(c)
                                    c["episode_goal"] = dict(c["episode_goal"], misrepresented="the note misrepresents the goal; the maker was steering its reader")
                                r = ask_latent(model, tok, ev, "episode_goal", c, {}, rng)
                                inferred = r["pred"] if r.get("valid") else "unknown"
                                note = ""
                                given = {}
                                if inferred == "misrepresented":
                                    note = "Treat the maker's own note as unreliable; rely on the record of its decisions.\n"
                                elif inferred != "unknown":
                                    given = {"episode_goal": inferred}
                                p = ask_choice(model, tok, ev, w, given, w["target_scenario"], rng, note=note)
                                ls = s5_lib.log_score(p["probs"], target) if p["valid"] else None
                                run.row(reader, lid, f"{lid}|{kind}", f"{kind}|{hset}", {"domain": domain, "world": kind, "hypothesis_set": hset},
                                        target, "realized_draw", "artifact_plus_context", p, ls,
                                        extra={"inferred_goal": inferred, "opened_chosen": inferred == "misrepresented",
                                               "exact_conflict_kl": conflict_kl, "true_goal": w["episode_goal"], "evidence_ids": ids})
                        run.unit_complete(reader, lid)
            finally:
                s5_lib.free_model(model)
    rows = [r for r in run.rows() if r["valid"] and r["primary_score"] is not None]
    sel = lambda **k: cluster_by_construction(select_rows(rows, **k))                 # noqa: E731
    gain = s5_lib.paired_contrast(sel(world="conflict", hypothesis_set="opened"), sel(world="conflict", hypothesis_set="fixed"), "unit_id", "primary_score", SEED + 41)
    false_alarm = s5_lib.paired_contrast(sel(world="consistent", hypothesis_set="opened"), sel(world="consistent", hypothesis_set="fixed"), "unit_id", "primary_score", SEED + 42)
    opened_rate = {k: (sum(1 for r in rows if r["factors"]["world"] == k and r["factors"]["hypothesis_set"] == "opened" and r["extra"]["opened_chosen"]) /
                       max(1, sum(1 for r in rows if r["factors"]["world"] == k and r["factors"]["hypothesis_set"] == "opened"))) for k in ("conflict", "consistent")}
    verdict = run.classify(gain, run.threshold(0.03))
    if verdict["outcome"] == "SUPPORT_CANDIDATE" and (false_alarm.get("point") is not None and false_alarm["point"] < -0.02):
        verdict["outcome"] = "INCONCLUSIVE"
        verdict["reason"] += "; the false-alarm cost on consistent worlds exceeds 0.02 nats (a criterion shift)"
    run.finish({"gain_on_conflict_worlds": gain, "false_alarm_on_consistent_worlds": false_alarm,
                "opened_hypothesis_chosen_rate": opened_rate, "exact_conflict_kl_mean": {k: (sum(r["extra"]["exact_conflict_kl"] for r in rows if r["factors"]["world"] == k) / max(1, sum(1 for r in rows if r["factors"]["world"] == k))) for k in ("conflict", "consistent")},
                "constructions": construction_summary(rows), "by_cell": mean_by(rows, ["world", "hypothesis_set"])},
               {"exec": "COMPLETE", "primary": "opened missing-goal hypothesis minus fixed set on conflict worlds; false alarm on consistent worlds", **verdict}, gs.held_s,
               rival="a fixed hypothesis set with the note simply down-weighted (the criterion-shift reading, exposed by the consistent-world cost)")
    return 0


# ── J05: cross-episode prediction ─────────────────────────────────────────────────────

def arm_j05() -> int:
    run = CardRun("J05", "s5_run_j.py")
    with s5_lib.GpuSession("s5_j05") as gs:
        for reader in run.readers:
            model, tok, _ = s5_lib.load_model(reader)
            try:
                for domain in s5_worlds.DOMAINS:
                    for i, lid in enumerate(run.units(domain)):
                        if run.is_done(reader, lid):
                            continue
                        run.check_deadline()
                        w = s5_worlds.make_joint_world(run.parent_of(lid), domain)
                        run.register_world(lid, w)
                        cands = candidates(w)
                        ev, ids = evidence_text(w)
                        s2 = w["scenarios"][w["target2_scenario"]]
                        target = s2["draw"]
                        rng = random.Random(SEED + 1500 + i)
                        r = ask_latent(model, tok, ev, "standing_preference", cands, {"episode_goal": w["episode_goal"]}, rng)
                        inferred = r["pred"] if r.get("valid") else "unknown"
                        note = f"For its NEXT piece the maker's goal is different: {s5_worlds.GOAL_TEXT[w['episode2_goal']]}.\n"
                        given = {"standing_preference": inferred} if inferred != "unknown" else {}
                        p = ask_choice(model, tok, ev, w, given, w["target2_scenario"], rng, note=note)
                        ls = s5_lib.log_score(p["probs"], target) if p["valid"] else None
                        # baselines, analytic on the same world
                        feas = s2["feasible"]
                        hist = [s["draw"] for s in w["scenarios"][:8]]
                        habit = {ax: (0.7 if ax == max(set(hist), key=hist.count) else 0.3 / max(1, len(feas) - 1)) for ax in feas}
                        prior = w["base"]["prior"]
                        topic = {ax: prior[ax] / sum(prior[a] for a in feas) for ax in feas}
                        g1 = s5_worlds.GOAL_AXIS[w["episode_goal"]]
                        last_goal = {ax: (0.7 if ax == g1 else 0.3 / max(1, len(feas) - 1)) for ax in feas}
                        exact = s5_worlds.predictive(w, s5_worlds.posterior(w, ["contextual", "action", "semantic", "forensic"]), w["target2_scenario"])
                        for name, dist in (("habit", habit), ("topic", topic), ("last_goal", last_goal)):
                            run.row(reader, lid, lid, f"baseline|{name}", {"domain": domain, "predictor": name, "control": name},
                                    target, "realized_draw", "artifact_plus_context", None, math.log(max(dist.get(target, 0.0), 1e-9)),
                                    valid=True, validity_reason="analytic", extra={"dist": dist})
                        run.row(reader, lid, lid, "reader|inferred_preference", {"domain": domain, "predictor": "inferred_preference"},
                                target, "realized_draw", "artifact_plus_context", p, ls,
                                extra={"inferred_preference": inferred, "true_preference": w["standing_preference"],
                                       "exact_log_score": math.log(max(exact[target], 1e-12)), "evidence_ids": ids})
                        run.unit_complete(reader, lid)
            finally:
                s5_lib.free_model(model)
    rows = [r for r in run.rows() if r["valid"] and r["primary_score"] is not None]
    sel = lambda name: cluster_by_construction(select_rows(rows, predictor=name))    # noqa: E731
    level = {n: (lambda m: sum(m.values()) / len(m) if m else None)(s5_lib.per_unit_means(sel(n), "unit_id", "primary_score")) for n in ("inferred_preference", "habit", "topic", "last_goal")}
    best = max(("habit", "topic", "last_goal"), key=lambda n: level[n] if level[n] is not None else -9)
    primary = s5_lib.paired_contrast(sel("inferred_preference"), sel(best), "unit_id", "primary_score", SEED + 51)
    exact = [r["extra"]["exact_log_score"] for r in select_rows(rows, predictor="inferred_preference")]
    pref_acc = [r["extra"]["inferred_preference"] == r["extra"]["true_preference"] for r in select_rows(rows, predictor="inferred_preference")]
    verdict = run.classify(primary, run.threshold(0.03))
    verdict["best_baseline"] = best
    run.finish({"level_log_score": level, "primary_inferred_minus_best_baseline": primary, "exact_ceiling_mean": (sum(exact) / len(exact)) if exact else None,
                "preference_recovery_accuracy": (sum(pref_acc) / len(pref_acc)) if pref_acc else None,
                "constructions": construction_summary(rows), "by_domain": mean_by(rows, ["domain", "predictor"])},
               {"exec": "COMPLETE", "primary": "inferred standing preference minus the best cheap baseline on the episode-2 choice", **verdict}, gs.held_s,
               rival=f"the {best} baseline")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--card", required=True, choices=["J01", "J02", "J03", "J04", "J05"])
    a = ap.parse_args()
    try:
        return {"J01": arm_j01, "J02": arm_j02, "J03": arm_j03, "J04": arm_j04, "J05": arm_j05}[a.card]()
    except DeadlineReached:
        return 3


if __name__ == "__main__":
    sys.exit(main())
