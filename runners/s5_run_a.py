"""Stage 5 appraisal, audience, and strategic-communication cards (brief §6 A01-A05,
§1.4-§1.5, §7.3).

DESIGN CHECK (2026-08-29)
lessons read: LESSONS §3 (the readout class matches the behavior; a criterion shift is
  not discrimination, so criterion and discrimination are reported apart; every hidden
  factor is realized as a predicted BEHAVIOR; surface collisions force abstention; truth
  marginals balanced by construction), CONTROLS §6.
gates and bands:
  - A01 primary: the mean log score over the three owned questions (intended audience
    effect, maker appraisal, content support) minus the chance log score of their
    candidate sets; NULL: 0; ALTERNATIVE: at or above 0.03 nats, with the owner-swap
    stratum (the maker induces what it does not believe) reported apart; the reader's own
    response is measured, never scored, and its agreement with the maker-appraisal
    answer is the merging-owners check (pre-mortem 4: high agreement is projection).
  - A02 primary: log score over chance on the predicted divergent behaviors (evidence
    selection under a fresh opportunity, correction after counterevidence, the private
    action), paired by world; NULL: 0; ALTERNATIVE: at or above 0.03 for the selection
    behavior; abstention on the collision twins for the two hidden factors is reported
    (unknown mass above 0.5 or a split within 0.2 across the pair); confident opposite
    answers on identical text are projection, counted.
  - A03 primary: the reader-model x maker-mechanism interaction on the content-support
    log score: (audience minus ordinary reader | audience-modeling maker) minus (audience
    minus ordinary | plain maker); NULL: 0; ALTERNATIVE: at or above 0.03; a main effect
    of the audience prompt on every maker is blanket distrust, not inverse-inverse
    reading, and is reported as such.
  - A04 primary: support discrimination (AUROC) under source labeling, influence
    awareness, and causal reappraisal minus none; NULL: 0; ALTERNATIVE: at or above 0.05
    with acceptance of TRUE helpful advice not lowered by more than 0.03 (the criterion
    apart); a condition that lowers all acceptance without raising AUROC is a criterion
    shift (the T03 lesson) and never protection.
  - A05 primary: uptake (following the call) under a reliable history minus an
    unreliable one, paired by world, with the content-support and communicative-goal
    posteriors reported to move by less than 0.02; NULL: 0; ALTERNATIVE: at or above
    0.05; trust that rewrites the content posterior is not the factored bridge the card
    asks for.
  every appraisal contrast is signed in the predicted direction. under the null the
  reader's log score over the owned questions equals the chance score of the candidate
  sets (0 nats of gain) and the twin worlds draw the same answer as their originals;
  under the alternative the gain reaches the threshold on the originals while the twins
  are met with abstention, and the failure direction guarded is a confident answer on a
  surface twin (a reader that scores from the surface alone), reported before any
  support is named.
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
import math
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from runners import s5_lib, s5_sources as S                                        # noqa: E402
from runners.s5_run_common import (CardRun, DeadlineReached, cluster_by_construction,   # noqa: E402
                                   construction_summary, mean_by, select_rows)

SEED = s5_lib.SEED0 + 300
CONDITIONS = {"none": "",
              "source_label": "This was posted by an anonymous account with no standing in the matter.\n",
              "influence_awareness": "Notices like this can be written to make you feel a certain way, whatever the facts.\n",
              "reappraisal": "Before answering, consider why this source chose this framing and these particular cases.\n"}


def _world(run: CardRun, lid: str, domain: str) -> dict:
    w = S.make_source_world(run.parent_of(lid), domain)
    run.register_world(lid, w)
    return w


def _body(w: dict, question: str, prefix: str = "") -> str:
    return f"{prefix}A notice you received:\n\"{w['text']}\"\n\n{question}"


def _chance(n: int) -> float:
    return math.log(1.0 / (n + 1))


# ── A01: the four owners ──────────────────────────────────────────────────────────────

def arm_a01() -> int:
    run = CardRun("A01", "s5_run_a.py")
    with s5_lib.GpuSession("s5_a01") as gs:
        for reader in run.readers:
            model, tok, _ = s5_lib.load_model(reader)
            try:
                for domain in S.SOURCE_DOMAINS:
                    for i, lid in enumerate(run.units(domain)):
                        if run.is_done(reader, lid):
                            continue
                        run.check_deadline()
                        w = _world(run, lid, domain)
                        f = w["factors"]
                        swap = (f["belief"] == "low") != (f["arousal_goal"] == "low")     # induces what it does not hold
                        rng = random.Random(SEED + i)
                        # the reader's own response: measured, no truth
                        rr = s5_lib.candidate_likelihood(model, tok, _body(w, "What would you do about it yourself?"),
                                                         {a: a for a in S.ACTION_OPTIONS}, rng, unknown=False)
                        run.row(reader, lid, lid, "owner|reader_response", {"domain": domain, "owner": "reader_response", "swap": swap},
                                None, "construction", "artifact_only", rr, None, extra={"measured_only": True})
                        own_act = rr["pred"] if rr["valid"] else None
                        qs = {"audience_effect_goal": ("What did the source want its readers to feel and do?", S.AUDIENCE_GOALS, w["audience_goal"]),
                              "maker_appraisal": ("How did the source itself judge the matter, and how did it present it?", S.APPRAISALS, w["appraisal"]),
                              "content_support": ("Setting the notice's tone aside, how much of the actual record bears the claim out?", S.SUPPORT_OPTIONS, f["support"])}
                        for owner, (q, opts, truth) in qs.items():
                            r = s5_lib.candidate_likelihood(model, tok, _body(w, q), opts, rng, unknown=True)
                            ls = s5_lib.log_score(r["probs"], truth) if r["valid"] else None
                            run.row(reader, lid, lid, f"owner|{owner}", {"domain": domain, "owner": owner, "swap": swap, "region": w["region"]},
                                    truth, "construction", "artifact_only", r, (ls - _chance(len(opts))) if ls is not None else None,
                                    extra={"chance_log": _chance(len(opts)), "log_score": ls, "p_unknown": r.get("p_unknown"),
                                           "reader_own_action": own_act,
                                           "merged_with_own_response": (owner == "maker_appraisal" and r["valid"] and
                                                                        ((own_act == "keep away from it") == r["pred"].startswith("believed")))})
                        run.unit_complete(reader, lid)
            finally:
                s5_lib.free_model(model)
    rows = [r for r in run.rows() if r["valid"] and r["primary_score"] is not None]
    owned = cluster_by_construction([r for r in rows if r["factors"]["owner"] != "reader_response"])
    primary = s5_lib.cluster_bootstrap_ci(s5_lib.per_unit_means(owned, "unit_id", "primary_score"), SEED + 11)
    per_owner = {o: s5_lib.cluster_bootstrap_ci(s5_lib.per_unit_means(cluster_by_construction(select_rows(rows, owner=o)), "unit_id", "primary_score"), SEED + 12)
                 for o in ("audience_effect_goal", "maker_appraisal", "content_support")}
    swap = {str(sw): s5_lib.cluster_bootstrap_ci(s5_lib.per_unit_means(cluster_by_construction([r for r in owned if r["factors"]["swap"] == sw]), "unit_id", "primary_score"), SEED + 13) for sw in (True, False)}
    merged = [r["extra"]["merged_with_own_response"] for r in rows if r["factors"]["owner"] == "maker_appraisal"]
    verdict = run.classify(primary, run.threshold(0.03))
    run.finish({"primary_owned_log_score_over_chance": primary, "per_owner": per_owner, "owner_swap_stratum": swap,
                "own_response_agreement_with_appraisal": (sum(merged) / len(merged)) if merged else None,
                "by_region": mean_by(owned, ["region", "owner"]), "constructions": construction_summary(rows)},
               {"exec": "COMPLETE", "primary": "owned questions' log score over chance; the swap stratum apart", **verdict}, gs.held_s,
               rival="projection: the reader's own response standing in for the maker's appraisal (the agreement rate)")
    return 0


# ── A02: divergent behaviors and collision twins ──────────────────────────────────────

def arm_a02() -> int:
    run = CardRun("A02", "s5_run_a.py")
    with s5_lib.GpuSession("s5_a02") as gs:
        for reader in run.readers:
            model, tok, _ = s5_lib.load_model(reader)
            try:
                for domain in S.SOURCE_DOMAINS:
                    for i, lid in enumerate(run.units(domain)):
                        if run.is_done(reader, lid):
                            continue
                        run.check_deadline()
                        w0 = _world(run, lid, domain)
                        pool_text, _ = S.fresh_pool_text(run.parent_of(lid), domain)
                        for twin_name, w in (("original", w0), ("twin", S.collision_twin(w0))):
                            f = w["factors"]
                            rng = random.Random(SEED + 400 + i)
                            qs = {"selection": (f"{pool_text} Which of these would it show?", S.SELECTION_OPTIONS, f["selection"]),
                                  "correction": (f"Suppose that later: {w['counterevidence']} What would the source do?", S.CORRECTION_OPTIONS, f["correction"]),
                                  "private_action": ("Away from its readers, what did the source itself do about the claim?", S.PRIVATE_OPTIONS, f["belief"])}
                            for beh, (q, opts, truth) in qs.items():
                                r = s5_lib.candidate_likelihood(model, tok, _body(w, q), opts, rng, unknown=True)
                                ls = s5_lib.log_score(r["probs"], truth) if r["valid"] else None
                                run.row(reader, lid, f"{lid}|{twin_name}", f"{beh}|{twin_name}",
                                        {"domain": domain, "behavior": beh, "twin": twin_name, "region": w["region"], "hidden": beh != "selection"},
                                        truth, "construction", "artifact_only", r, (ls - _chance(len(opts))) if ls is not None else None,
                                        extra={"chance_log": _chance(len(opts)), "log_score": ls, "p_unknown": r.get("p_unknown"),
                                               "pred": r.get("pred"), "surface_key": w["text"][:80]})
                        run.unit_complete(reader, lid)
            finally:
                s5_lib.free_model(model)
    rows = [r for r in run.rows() if r["valid"] and r["primary_score"] is not None]
    sel_rows = cluster_by_construction(select_rows(rows, behavior="selection", twin="original"))
    primary = s5_lib.cluster_bootstrap_ci(s5_lib.per_unit_means(sel_rows, "unit_id", "primary_score"), SEED + 21)
    per_beh = {b: s5_lib.cluster_bootstrap_ci(s5_lib.per_unit_means(cluster_by_construction(select_rows(rows, behavior=b, twin="original")), "unit_id", "primary_score"), SEED + 22)
               for b in ("selection", "correction", "private_action")}
    # abstention on twins for the hidden behaviors: per (unit, behavior) the original/twin pair
    pairs = {}
    for r in rows:
        if r["factors"]["hidden"]:
            pairs.setdefault((r["model_id"], r["unit_id"], r["factors"]["behavior"]), {})[r["factors"]["twin"]] = r   # keyed on the unit (the lineage field carries the twin suffix; L266's bookkeeping defect)
    abst = {"n_pairs": 0, "abstained": 0, "confident_opposite": 0, "confident_same": 0}
    for k, pr in pairs.items():
        if "original" in pr and "twin" in pr:
            a, b = pr["original"], pr["twin"]
            abst["n_pairs"] += 1
            unk = (a["extra"]["p_unknown"] + b["extra"]["p_unknown"]) / 2
            # abstention is mass on unknown; the former near-equal clause was vacuous on identical
            # text (identical probabilities) and reported every pair as abstained (L296, TODO (u))
            if unk > 0.5:
                abst["abstained"] += 1
            elif a["pred"] != b["pred"]:
                abst["confident_opposite"] += 1
            else:
                abst["confident_same"] += 1
    verdict = run.classify(primary, run.threshold(0.03))
    verdict["abstention_rate_on_twins"] = (abst["abstained"] / abst["n_pairs"]) if abst["n_pairs"] else None
    run.finish({"primary_selection_over_chance": primary, "per_behavior": per_beh, "twin_abstention": abst,
                "by_region": mean_by(select_rows(rows, twin="original"), ["region", "behavior"]), "constructions": construction_summary(rows)},
               {"exec": "COMPLETE", "primary": "predicted evidence-selection behavior log score over chance; abstention on collision twins", **verdict}, gs.held_s,
               rival="surface classification of a region (which cannot pass without the predicted behavior, §7.3)")
    return 0


# ── A03: inverse-inverse planning ─────────────────────────────────────────────────────

def arm_a03() -> int:
    run = CardRun("A03", "s5_run_a.py")
    with s5_lib.GpuSession("s5_a03") as gs:
        for reader in run.readers:
            model, tok, _ = s5_lib.load_model(reader)
            try:
                for domain in S.SOURCE_DOMAINS:
                    for i, lid in enumerate(run.units(domain)):
                        if run.is_done(reader, lid):
                            continue
                        run.check_deadline()
                        w = _world(run, lid, domain)
                        f = w["factors"]
                        if f["selection"] == "uncertain":
                            run.unit_complete(reader, lid)
                            continue
                        maker = "audience_modeling" if f["selection"] in ("cherry", "fabricated") else "plain"
                        rng = random.Random(SEED + 700 + i)
                        for rm, prefix in (("ordinary", ""), ("audience", "The source chose which cases to show you and may have chosen them to shape your conclusion.\n")):
                            r = s5_lib.candidate_likelihood(model, tok, _body(w, "Setting the notice's tone aside, how much of the actual record bears the claim out?", prefix),
                                                            S.SUPPORT_OPTIONS, rng, unknown=True)
                            ls = s5_lib.log_score(r["probs"], f["support"]) if r["valid"] else None
                            run.row(reader, lid, lid, f"{maker}|{rm}", {"domain": domain, "maker": maker, "reader_model": rm},
                                    f["support"], "construction", "artifact_only", r, ls,
                                    extra={"p_unknown": r.get("p_unknown"), "selection": f["selection"]})
                        run.unit_complete(reader, lid)
            finally:
                s5_lib.free_model(model)
    rows = [r for r in run.rows() if r["valid"] and r["primary_score"] is not None]
    sel = lambda **k: cluster_by_construction(select_rows(rows, **k))                 # noqa: E731
    eff = {m: s5_lib.paired_contrast(sel(maker=m, reader_model="audience"), sel(maker=m, reader_model="ordinary"), "unit_id", "primary_score", SEED + 31)
           for m in ("audience_modeling", "plain")}
    # the interaction, per world: (audience - ordinary) on audience-modeling worlds minus the plain worlds' mean
    a = s5_lib.per_unit_means(sel(maker="audience_modeling", reader_model="audience"), "unit_id", "primary_score")
    o = s5_lib.per_unit_means(sel(maker="audience_modeling", reader_model="ordinary"), "unit_id", "primary_score")
    plain_gain = eff["plain"].get("point") or 0.0
    inter = {u: (a[u] - o[u]) - plain_gain for u in a if u in o}
    interaction = s5_lib.cluster_bootstrap_ci(inter, SEED + 32)
    verdict = run.classify(interaction, run.threshold(0.03))
    if verdict["outcome"] == "SUPPORT_CANDIDATE" and eff["plain"].get("lo") is not None and eff["plain"]["lo"] > 0 and eff["plain"]["point"] >= 0.5 * (eff["audience_modeling"].get("point") or 0):
        verdict["outcome"] = "INCONCLUSIVE"
        verdict["reason"] += "; the audience prompt helps on plain makers too (blanket distrust rather than inverse-inverse reading)"
    run.finish({"audience_minus_ordinary_by_maker": eff, "interaction": interaction, "by_cell": mean_by(rows, ["maker", "reader_model"]),
                "constructions": construction_summary(rows)},
               {"exec": "COMPLETE", "primary": "reader-model x maker-mechanism interaction on content-support log score", **verdict}, gs.held_s,
               rival="blanket distrust: the audience prompt helping on every maker alike")
    return 0


# ── A04: labeling, awareness, reappraisal ─────────────────────────────────────────────

def arm_a04() -> int:
    run = CardRun("A04", "s5_run_a.py")
    with s5_lib.GpuSession("s5_a04") as gs:
        for reader in run.readers:
            model, tok, _ = s5_lib.load_model(reader)
            try:
                for domain in S.SOURCE_DOMAINS:
                    for i, lid in enumerate(run.units(domain)):
                        if run.is_done(reader, lid):
                            continue
                        run.check_deadline()
                        w = _world(run, lid, domain)
                        f = w["factors"]
                        rng = random.Random(SEED + 1000 + i)
                        for cond, prefix in CONDITIONS.items():
                            r = s5_lib.candidate_likelihood(model, tok, _body(w, "Is the claim in this notice borne out by the record?", prefix),
                                                            {"true": "yes, largely borne out", "false": "no, largely not borne out"}, rng, unknown=False)
                            truth = "true" if f["support"] == "high" else "false"
                            run.row(reader, lid, lid, f"{cond}|reliability", {"domain": domain, "condition": cond, "score": "reliability"},
                                    truth, "construction", "artifact_only", r, s5_lib.log_score(r["probs"], truth) if r["valid"] else None,
                                    extra={"p_true": r["probs"]["true"] if r["valid"] else None, "accepted": r["valid"] and r["probs"]["true"] > 0.5,
                                           "brier": s5_lib.brier(r["probs"], truth) if r["valid"] else None})
                            if f["action_goal"] == "present":
                                r2 = s5_lib.candidate_likelihood(model, tok, _body(w, "Will you do what the notice asks?", prefix),
                                                                 {"follow": "yes, I will do as it asks", "refuse": "no, I will not"}, rng, unknown=False)
                                run.row(reader, lid, lid, f"{cond}|uptake", {"domain": domain, "condition": cond, "score": "uptake", "true_advice": w["true_advice"]},
                                        "follow" if w["true_advice"] else "refuse", "construction", "artifact_only", r2, None,
                                        extra={"p_follow": r2["probs"]["follow"] if r2["valid"] else None, "followed": r2["valid"] and r2["probs"]["follow"] > 0.5})
                        run.unit_complete(reader, lid)
            finally:
                s5_lib.free_model(model)
    rows = [r for r in run.rows() if r["valid"]]
    rel = [r for r in rows if r["factors"]["score"] == "reliability"]
    up = [r for r in rows if r["factors"]["score"] == "uptake"]
    per = {}
    for cond in CONDITIONS:
        sub = [r for r in rel if r["factors"]["condition"] == cond]
        pos = [r["extra"]["p_true"] for r in sub if r["truth"] == "true"]
        neg = [r["extra"]["p_true"] for r in sub if r["truth"] == "false"]
        us = [r for r in up if r["factors"]["condition"] == cond]
        per[cond] = {"auroc": s5_lib.auroc(pos, neg), "acceptance": (sum(r["extra"]["accepted"] for r in sub) / len(sub)) if sub else None,
                     "brier": (sum(r["extra"]["brier"] for r in sub) / len(sub)) if sub else None,
                     "true_advice_followed": (sum(r["extra"]["followed"] for r in us if r["factors"]["true_advice"]) / max(1, sum(1 for r in us if r["factors"]["true_advice"]))),
                     "false_advice_followed": (sum(r["extra"]["followed"] for r in us if not r["factors"]["true_advice"]) / max(1, sum(1 for r in us if not r["factors"]["true_advice"]))),
                     "n": len(sub)}
    # per-unit AUROC contrast: bootstrap over worlds of the AUROC difference (worlds resampled)
    def auroc_diff_units(cond):
        base = {r["unit_id"]: r for r in rel if r["factors"]["condition"] == "none"}
        out = {}
        for r in rel:
            if r["factors"]["condition"] == cond and r["unit_id"] in base:
                # a per-world proxy: the signed probability margin toward the truth, condition minus none
                sgn = 1.0 if r["truth"] == "true" else -1.0
                out[r["unit_id"]] = sgn * (r["extra"]["p_true"] - base[r["unit_id"]]["extra"]["p_true"])
        return out
    contrasts = {c: s5_lib.cluster_bootstrap_ci(auroc_diff_units(c), SEED + 41) for c in ("source_label", "influence_awareness", "reappraisal")}
    best = max(contrasts, key=lambda c: contrasts[c].get("point") or -9)
    prim = {"point": (per[best]["auroc"] or 0) - (per["none"]["auroc"] or 0), "lo": contrasts[best]["lo"], "hi": contrasts[best]["hi"], "n_units": contrasts[best]["n_units"]}
    verdict = run.classify(contrasts[best], run.threshold(0.05))
    verdict["auroc_gain_best"] = prim["point"]
    verdict["best_condition"] = best
    crit_shift = per[best]["acceptance"] is not None and per["none"]["acceptance"] is not None and per[best]["acceptance"] < per["none"]["acceptance"] - 0.05
    true_loss = per[best]["true_advice_followed"] < per["none"]["true_advice_followed"] - 0.03
    if verdict["outcome"] == "SUPPORT_CANDIDATE" and true_loss:
        verdict["outcome"] = "INCONCLUSIVE"
        verdict["reason"] += "; true-advice uptake fell by more than 3 points (protection bought with blanket rejection)"
    if verdict["outcome"] != "SUPPORT_CANDIDATE" and crit_shift:
        verdict["note"] = "acceptance fell without a discrimination gain: a criterion shift"
    run.finish({"per_condition": per, "signed_margin_contrasts_vs_none": contrasts, "constructions": construction_summary(rows)},
               {"exec": "COMPLETE", "primary": "support discrimination under labeling and reappraisal beyond none; criterion and true-advice uptake apart", **verdict}, gs.held_s,
               rival="a criterion shift (lower acceptance of everything) wearing the face of discrimination")
    return 0


# ── A05: trust after reconstruction ───────────────────────────────────────────────────

def arm_a05() -> int:
    run = CardRun("A05", "s5_run_a.py")
    with s5_lib.GpuSession("s5_a05") as gs:
        for reader in run.readers:
            model, tok, _ = s5_lib.load_model(reader)
            try:
                for domain in S.SOURCE_DOMAINS:
                    for i, lid in enumerate(run.units(domain)):
                        if run.is_done(reader, lid):
                            continue
                        run.check_deadline()
                        w = _world(run, lid, domain)
                        f = w["factors"]
                        if f["action_goal"] != "present" or f["selection"] == "uncertain":
                            run.unit_complete(reader, lid)
                            continue
                        episode = "honest" if (f["support"] == "high" and f["selection"] == "representative") else \
                                  "deceptive" if (f["support"] == "low" and f["selection"] in ("cherry", "fabricated")) else "mixed"
                        rng = random.Random(SEED + 1300 + i)
                        for hist in ("reliable", "unreliable"):
                            prefix = S.history_block(run.parent_of(lid), domain, hist == "reliable") + "\n"
                            r1 = s5_lib.candidate_likelihood(model, tok, _body(w, "Setting the notice's tone aside, how much of the actual record bears the claim out?", prefix), S.SUPPORT_OPTIONS, rng, unknown=True)
                            r2 = s5_lib.candidate_likelihood(model, tok, _body(w, "What was the source trying to do with this notice?", prefix),
                                                             {"inform": "to inform", "warn": "to warn", "mislead": "to mislead", "conceal": "to hold something back"}, rng, unknown=True)
                            r3 = s5_lib.candidate_likelihood(model, tok, _body(w, "Will you do what the notice asks?", prefix),
                                                             {"follow": "yes, I will do as it asks", "refuse": "no, I will not"}, rng, unknown=False)
                            fac = {"domain": domain, "history": hist, "episode": episode}
                            run.row(reader, lid, lid, f"{hist}|support", {**fac, "readout": "content_support", "control": "content_unchanged"}, f["support"], "construction", "artifact_plus_context", r1,
                                    s5_lib.log_score(r1["probs"], f["support"]) if r1["valid"] else None, extra={"p_high": r1["probs"].get("high") if r1["valid"] else None})
                            run.row(reader, lid, lid, f"{hist}|goal", {**fac, "readout": "communicative_goal", "control": "goal_unchanged"}, w["communicative_goal"], "construction", "artifact_plus_context", r2,
                                    s5_lib.log_score(r2["probs"], w["communicative_goal"]) if r2["valid"] else None, extra={"p_mislead": r2["probs"].get("mislead") if r2["valid"] else None})
                            run.row(reader, lid, lid, f"{hist}|uptake", {**fac, "readout": "uptake"}, "follow" if w["true_advice"] else "refuse", "construction", "artifact_plus_context", r3,
                                    r3["probs"]["follow"] if r3["valid"] else None, extra={"true_advice": w["true_advice"]})
                        run.unit_complete(reader, lid)
            finally:
                s5_lib.free_model(model)
    rows = [r for r in run.rows() if r["valid"] and r["primary_score"] is not None]
    sel = lambda **k: cluster_by_construction(select_rows(rows, **k))                 # noqa: E731
    uptake = s5_lib.paired_contrast(sel(readout="uptake", history="reliable"), sel(readout="uptake", history="unreliable"), "unit_id", "primary_score", SEED + 51)
    support_shift = s5_lib.paired_contrast(sel(readout="content_support", history="reliable"), sel(readout="content_support", history="unreliable"), "unit_id", "primary_score", SEED + 52)
    goal_shift = s5_lib.paired_contrast(sel(readout="communicative_goal", history="reliable"), sel(readout="communicative_goal", history="unreliable"), "unit_id", "primary_score", SEED + 53)
    verdict = run.classify(uptake, run.threshold(0.05))
    factored = all(abs(x.get("point") or 0) < 0.02 for x in (support_shift, goal_shift))
    if verdict["outcome"] == "SUPPORT_CANDIDATE" and not factored:
        verdict["outcome"] = "INCONCLUSIVE"
        verdict["reason"] += "; trust moved the content-support or communicative-goal posterior by 0.02 nats or more (not the factored bridge)"
    verdict["factored"] = factored
    run.finish({"uptake_reliable_minus_unreliable": uptake, "content_support_shift": support_shift, "communicative_goal_shift": goal_shift,
                "by_cell": mean_by(rows, ["history", "episode", "readout"]), "constructions": construction_summary(rows)},
               {"exec": "COMPLETE", "primary": "uptake under a reliable minus an unreliable history, content and goal posteriors unchanged", **verdict}, gs.held_s,
               rival="trust rewriting the content posterior (a merged bridge) rather than the policy alone")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--card", required=True, choices=["A01", "A02", "A03", "A04", "A05"])
    a = ap.parse_args()
    try:
        return {"A01": arm_a01, "A02": arm_a02, "A03": arm_a03, "A04": arm_a04, "A05": arm_a05}[a.card]()
    except DeadlineReached:
        return 3


if __name__ == "__main__":
    sys.exit(main())
