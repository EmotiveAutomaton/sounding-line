"""Stage 4 transmission track (brief §7 T01-T03): transmission, learning,
reconstruction, and uptake; modeling the source's selection rule; technique knowledge
versus blanket distrust.

DESIGN CHECK (2026-08-27; R7 repair 2026-08-28: lesson worlds enumerated per domain, every
row carries its construction hash, every interval clusters on the construction)
lessons read: LESSONS §3 (manipulation checks need range; assigned is not realized;
  a copied slogan is not a passed transfer test, so relay fidelity is mechanical on
  rule parameters; realization per cell; power before verdicts; every statistic a
  verdict rests on is written to disk), CONTROLS §6 (matched information; analytic
  floors; directional gates).
gates and bands:
  - T01 support gate: on honest-aligned messages, supported minus bare on novel-case
    application accuracy or relay fidelity must reach 0.05 (frozen), else the support
    factor is INSTRUMENT_FAILED and no transmissibility attribution is made. Primary:
    supported minus bare on novel-case application accuracy AS TAUGHT (the lesson's
    own rule applied to a new lot; correctness under the true rule is carried beside
    it and a false lesson's cost lives in the payoff outcome, so the truth factor and
    the learning score are not confounded by construction), paired by world, aligned
    and misaligned strata each reported; NULL: 0; ALTERNATIVE: >= 0.05 in both strata
    (the dissociation) or in one (reported as such). Intent is realized in every world
    (a benefit source advises what its own rule implies; an inducing source pushes a
    payoff-neutral delay), and the goal question's truth is the label the message plus
    the revealed outcome can support ('cannot be told' for consistent advice under a
    rule that proved false). Failure direction guarded: a reader that only copies the
    slogan would show relay fidelity without application gain; both are reported and
    application is the primary.
  - T02 primary: the two-pass source-goal route minus the two-pass factual-summary
    route on recipient judgment log score, paired; NULL: 0; ALTERNATIVE: >= 0.03 with
    useful uptake preserved (representative and benefit cells under the source-goal
    route not worse than direct by more than 3 pp, interval reported; a wide interval
    is not noninferiority). Failure direction guarded: labeling every message
    manipulative would raise 'induce' accuracy while destroying benefit-cell uptake,
    which the noninferiority clause catches; the oracle-intention arm is a separately
    marked ceiling and never counts as end-to-end success.
  - T03 primary: technique lesson minus matched control on factual-reliability AUROC on
    the held-out technique family; NULL: 0; ALTERNATIVE: >= 0.05 with true-advice
    acceptance loss <= 3 pp (preregistered tolerance, interval reported). Failure
    direction guarded: a criterion shift (accept less of everything) shows as lower
    acceptance with unchanged AUROC and is named a criterion shift, not protection.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from runners import s4_lib, s4_worlds                                             # noqa: E402
from runners.s4_run_common import (CardRun, DeadlineReached, cell_counts, cid, cluster_by_construction, construction_summary, mean_by, select_rows)   # noqa: E402
SEED = 48000
SUPPORT_GATE = 0.05
NONINFERIORITY_PP = 0.03


# ── message variants: all eight cells per world, paired, rendered by the world module
# (s4_worlds.lesson_message) so the construction has one home ─────────────────────────

def parse_relay(text: str) -> dict | None:
    for m in re.finditer(r"\{[^{}]*\}", text or ""):
        try:
            obj = json.loads(m.group(0))
        except Exception:                                                        # noqa: BLE001
            continue
        if isinstance(obj, dict) and "good_tag" in obj and "bad_tag" in obj:
            return {"good_tag": str(obj["good_tag"]).strip().lower(),
                    "bad_tag": str(obj["bad_tag"]).strip().lower()}
    return None


def payoff(pred: str, optimal: str) -> float:
    if pred == optimal:
        return 1.0
    if pred in (s4_worlds.CASE_ACTIONS[1], s4_worlds.CASE_ACTIONS[3]):
        return 0.0
    return -1.0


# ── T01 ───────────────────────────────────────────────────────────────────────────────

def arm_t01() -> int:
    run = CardRun("T01", "s4_run_t.py")
    with s4_lib.GpuSession("s4_t01") as gs:
        for reader in run.readers:
            model, tok, _ = s4_lib.load_model(reader)
            try:
                for domain in ("workshop", "civic"):
                    for i, lid in enumerate(run.units(domain)):
                        if run.is_done(reader, lid):
                            continue
                        run.check_deadline()
                        w = s4_worlds.make_lesson_world(lid, domain)
                        run.register_world(lid, w)
                        for truth in ("true", "false"):
                            for intent in ("benefit", "induce"):
                                for support in ("bare", "supported"):
                                    v = s4_worlds.lesson_message(w, truth, intent, support)
                                    novel = s4_worlds.lesson_novel_case(w, v["relay_truth"]["good_tag"])
                                    f = {"domain": domain, "truth": truth, "intent": intent, "support": support,
                                         "aligned": v["aligned"]}
                                    rng = random.Random(SEED + 100 + i)
                                    # 1 relay (generation, mechanical fidelity)
                                    rprompt = (f"You received this lesson from another crew:\n\"{v['message']}\"\n"
                                               f"Pass the lesson on to the next crew in one or two sentences, then "
                                               f"state the rule you were given as a JSON object of the form "
                                               f"{{\"good_tag\": \"<tag>\", \"bad_tag\": \"<tag>\"}}.")
                                    g = s4_lib.generate(model, tok, rprompt, seed=SEED + 1000 + i, max_new=80, greedy=True)
                                    parsed = parse_relay(g["text"])
                                    fidelity = float(parsed == {k: val.lower() for k, val in v["relay_truth"].items()}) if parsed else 0.0
                                    ref = run.raw(reader, lid, rprompt, g, validity_reason="ok" if parsed else "malformed_relay",
                                                  extra={"factors": f, "relay_truth": v["relay_truth"]})
                                    run.row(reader, lid, lid, f"relay|{truth}|{intent}|{support}", {**f, "outcome": "relay"},
                                            v["relay_truth"], "construction", "artifact_only", None, fidelity,
                                            valid=parsed is not None, validity_reason="ok" if parsed else "malformed_relay",
                                            raw_ref=ref, extra={"parsed": parsed})
                                    # 2 novel-case application, scored AS TAUGHT (did the reader
                                    # learn the lesson well enough to apply it to a new lot);
                                    # correctness under the TRUE rule is carried beside it, and
                                    # the cost of a false lesson lives in the payoff outcome
                                    body = f"A lesson you received:\n\"{v['message']}\"\n\n{novel['question']}"
                                    r = s4_lib.likelihood_choice(model, tok, body, novel["options"], rng)
                                    run.row(reader, lid, lid, f"apply|{truth}|{intent}|{support}", {**f, "outcome": "application"},
                                            novel["truth_taught"], "construction", "artifact_only", r,
                                            s4_lib.log_score(r["probs"], novel["truth_taught"]) if r["valid"] else None,
                                            extra={"correct": r["valid"] and r["pred"] == novel["truth_taught"],
                                                   "correct_under_truth": r["valid"] and r["pred"] == novel["truth"],
                                                   "truth_under_true_rule": novel["truth"]})
                                    # 3 source goal recovery, against the label the message plus the
                                    # revealed outcome can support (see s4_worlds.lesson_message)
                                    body = (f"A lesson you received:\n\"{v['message']}\"\n\nThe lot's outcome is now known: "
                                            f"{w['case_tag']}-tagged lots {'did well' if w['case_tag'] == w['true_tag'] else 'failed'} "
                                            f"under {w['condition']}. Which best describes the source?")
                                    r2 = s4_lib.likelihood_choice(model, tok, body, w["goal_options"], rng)
                                    run.row(reader, lid, lid, f"goal|{truth}|{intent}|{support}", {**f, "outcome": "goal"},
                                            v["goal_truth"], "construction", "artifact_plus_context", r2,
                                            s4_lib.log_score(r2["probs"], v["goal_truth"]) if r2["valid"] else None,
                                            extra={"correct": r2["valid"] and r2["pred"] == v["goal_truth"],
                                                   "latent_knowledge": v["knowledge"], "steering": v["steering"]})
                                    # 4 recipient action and payoff
                                    body = f"A lesson you received:\n\"{v['message']}\"\n\nWhat will you do with your lot?"
                                    r3 = s4_lib.likelihood_choice(model, tok, body, {a: a for a in s4_worlds.CASE_ACTIONS}, rng)
                                    pay = payoff(r3["pred"], w["optimal"]) if r3["valid"] else None
                                    run.row(reader, lid, lid, f"act|{truth}|{intent}|{support}", {**f, "outcome": "action"},
                                            w["optimal"], "construction", "artifact_only", r3, pay,
                                            extra={"followed_recommendation": r3["valid"] and r3["pred"] == v["recommended"]})
                        run.L.mark_inspected([lid])
                        run.unit_complete(reader, lid)
            finally:
                s4_lib.free_model(model)
    return _t01_analyze(run, gs.held_s)


def _acc_rows(rows):
    return [{"unit_id": cid(r), "primary_score": float(bool(r["extra"].get("correct")))} for r in rows if r["valid"]]


def _paired(a, b, seed):
    """Paired by CONSTRUCTION (R7): rows are clustered on their construction hash, so
    textual twins resample as one unit and n_units is the distinct count."""
    return s4_lib.paired_contrast(cluster_by_construction(a), cluster_by_construction(b),
                                  "unit_id", "primary_score", seed)


def _t01_analyze(run: CardRun, gpu_s: float) -> int:
    rows = run.rows()
    app = [r for r in rows if r["factors"].get("outcome") == "application"]
    rel = [r for r in rows if r["factors"].get("outcome") == "relay"]
    sel = lambda rs, **k: select_rows(rs, **k)                                     # noqa: E731
    # support manipulation check on honest-aligned messages
    gate_app = _paired(_acc_rows(sel(app, truth="true", intent="benefit", support="supported")),
                       _acc_rows(sel(app, truth="true", intent="benefit", support="bare")), SEED + 1)
    gate_rel = _paired(sel(rel, truth="true", intent="benefit", support="supported"),
                       sel(rel, truth="true", intent="benefit", support="bare"), SEED + 2)
    support_ok = max(gate_app.get("point") or 0, gate_rel.get("point") or 0) >= SUPPORT_GATE
    strata = {}
    for name, cond in (("aligned", True), ("misaligned", False)):
        a = [r for r in app if r["factors"]["aligned"] == cond and r["factors"]["support"] == "supported"]
        b = [r for r in app if r["factors"]["aligned"] == cond and r["factors"]["support"] == "bare"]
        strata[name] = _paired(_acc_rows(a), _acc_rows(b), SEED + 3)
    primary = strata["aligned"]
    by_cell = {o: mean_by([r for r in rows if r["factors"].get("outcome") == o and r["valid"]],
                          ["truth", "intent", "support"]) for o in ("relay", "application", "goal", "action")}
    goal_acc = mean_by([{"factors": r["factors"], "primary_score": float(bool(r["extra"].get("correct")))}
                        for r in rows if r["factors"].get("outcome") == "goal" and r["valid"]], ["truth", "intent"])
    app_truth = mean_by([{"factors": r["factors"], "primary_score": float(bool(r["extra"].get("correct_under_truth")))}
                         for r in app if r["valid"]], ["truth", "intent", "support"])
    follow = mean_by([{"factors": r["factors"], "primary_score": float(bool(r["extra"].get("followed_recommendation")))}
                      for r in rows if r["factors"].get("outcome") == "action" and r["valid"]], ["truth", "intent", "support"])
    threshold = run.design.get("thresholds", {}).get("T01", 0.05) or 0.05
    if not support_ok:
        verdict = {"outcome": "INSTRUMENT_FAILED",
                   "reason": f"the support manipulation did not change comprehension or relay on honest-aligned messages (gate {SUPPORT_GATE})"}
    else:
        verdict = run.classify(primary, threshold)
    run.finish({"support_gate": {"application": gate_app, "relay": gate_rel, "passed": support_ok},
                "primary_support_effect_aligned": primary, "strata": strata, "by_cell": by_cell,
                "application_correct_under_truth": app_truth,
                "goal_recovery_accuracy": goal_acc, "followed_recommendation": follow,
                "constructions": construction_summary(rows),
                "cell_counts": cell_counts(rows, ["truth", "intent", "support", "outcome"])},
               {"exec": "COMPLETE", "primary": "support effect on novel-case application, aligned stratum",
                "support_gate_passed": support_ok, **verdict}, gpu_s)
    return 0


# ── T02 ───────────────────────────────────────────────────────────────────────────────

def parse_rule(text: str) -> str | None:
    for m in re.finditer(r"\{[^{}]*\}", text or ""):
        try:
            obj = json.loads(m.group(0))
        except Exception:                                                        # noqa: BLE001
            continue
        if isinstance(obj, dict) and "rule" in obj:
            v = str(obj["rule"]).strip().lower()
            for k in ("representative", "benefit", "induce", "unknown"):
                if k in v:
                    return k
    return None


def arm_t02() -> int:
    run = CardRun("T02", "s4_run_t.py")
    with s4_lib.GpuSession("s4_t02") as gs:
        for reader in run.readers:
            model, tok, _ = s4_lib.load_model(reader)
            try:
                for domain in ("workshop", "civic"):
                    for i, lid in enumerate(run.units(domain)):
                        if run.is_done(reader, lid):
                            continue
                        run.check_deadline()
                        t01_lid = run.parent_of(lid)
                        w = s4_worlds.make_lesson_world(t01_lid, domain)
                        run.register_world(lid, w)
                        child = lid
                        case_q = {"question": "What should be done with your lot?",
                                  "options": {a: a for a in s4_worlds.CASE_ACTIONS}}
                        for rule in ("representative", "benefit", "induce"):
                            for visible in (True, False):
                                sw = s4_worlds.selection_world(w, rule, visible, random.Random(SEED + 300 + i))
                                # the source's earlier selections are on OTHER kinds, so they
                                # show its rule without showing this kind's outcomes
                                recs = s4_worlds.source_records(w, rule, random.Random(SEED + 400 + i))
                                f = {"domain": domain, "rule": rule, "visible": "yes" if visible else "no"}
                                head = (f"Your lot of {w['kind']} is tagged {w['case_tag']} and faces {w['condition']}.\n"
                                        f"{sw['text']}\nThe source's earlier behavior, on lots of other kinds:\n{recs}\n")
                                rng = random.Random(SEED + 500 + i)
                                routes = {}
                                routes["direct"] = (head + f"\n{case_q['question']}", 1, None)
                                routes["caution"] = (head + "\nSources may select what they show you for their own reasons; "
                                                     f"be cautious.\n{case_q['question']}", 1, None)
                                sprompt = head + "\nSummarize the evidence above in at most two sentences."
                                g1 = s4_lib.generate(model, tok, sprompt, seed=SEED + 600 + i, max_new=48, greedy=True)
                                ref1 = run.raw(reader, child, sprompt, g1, extra={"route": "summary2", **f})
                                # both two-pass routes give their second pass the SAME observations
                                # (the head) plus their own first-pass note; the smoke's summary
                                # route dropped the head and lost the comparison to information
                                routes["summary2"] = (head + f"\nSummary of the evidence: {g1['text']}\n{case_q['question']}", 2, ref1)
                                rprompt = (head + "\nFrom the source's earlier behavior, infer how it chooses what to show: "
                                           "reply with one JSON object {\"rule\": \"representative\" | \"benefit\" | "
                                           "\"induce\" | \"unknown\"} and one sentence of reasoning.")
                                g2 = s4_lib.generate(model, tok, rprompt, seed=SEED + 700 + i, max_new=48, greedy=True)
                                inferred = parse_rule(g2["text"])
                                ref2 = run.raw(reader, child, rprompt, g2, validity_reason="ok" if inferred else "malformed_rule",
                                               extra={"route": "reconstruct2", "true_rule": rule, **f})
                                routes["reconstruct2"] = (head + f"\nYour own reading of the source: it {sw['rule_options'].get(inferred, 'cannot be read')}.\n"
                                                          f"{case_q['question']}", 2, ref2)
                                routes["oracle"] = (head + f"\n(Ceiling diagnostic) The source's true selection rule: it "
                                                    f"{sw['rule_options'][rule]}.\n{case_q['question']}", 1, None)
                                for route, (body, passes, ref) in routes.items():
                                    r = s4_lib.likelihood_choice(model, tok, body, case_q["options"], rng)
                                    ls = s4_lib.log_score(r["probs"], w["optimal"]) if r["valid"] else None
                                    run.row(reader, child, child, f"{route}|{rule}|{f['visible']}", {**f, "route": route},
                                            w["optimal"], "construction",
                                            "oracle_latent" if route == "oracle" else "artifact_plus_context",
                                            r, ls, raw_ref=ref,
                                            extra={"passes": passes, "correct": r["valid"] and r["pred"] == w["optimal"],
                                                   "payoff": payoff(r["pred"], w["optimal"]) if r["valid"] else None,
                                                   "p_truth": r["probs"][w["optimal"]] if r["valid"] else None,
                                                   "inferred_rule": inferred if route == "reconstruct2" else None,
                                                   "rule_recovered": (inferred == rule) if route == "reconstruct2" else None})
                                # direct source-goal question (4-way over rules)
                                rq = s4_lib.likelihood_choice(model, tok, head + "\nHow did the source choose what to show you?",
                                                              sw["rule_options"], rng)
                                run.row(reader, child, child, f"rulelik|{rule}|{f['visible']}", {**f, "route": "rule_likelihood"},
                                        rule, "construction", "artifact_plus_context", rq,
                                        s4_lib.log_score(rq["probs"], rule) if rq["valid"] else None,
                                        extra={"correct": rq["valid"] and rq["pred"] == rule})
                        run.L.mark_inspected([lid])
                        run.unit_complete(reader, lid)
            finally:
                s4_lib.free_model(model)
    return _t02_analyze(run, gs.held_s)


def _t02_analyze(run: CardRun, gpu_s: float) -> int:
    rows = [r for r in run.rows() if r["valid"] and r["primary_score"] is not None]
    judg = [r for r in rows if r["factors"]["route"] not in ("rule_likelihood",)]
    sel = lambda **k: select_rows(judg, **k)                                       # noqa: E731
    primary = _paired(sel(route="reconstruct2"), sel(route="summary2"), SEED + 11)
    by_rule = {}
    for rule in ("representative", "benefit", "induce"):
        by_rule[rule] = {rt: _paired(sel(route=rt, rule=rule), sel(route="direct", rule=rule), SEED + 12)
                         for rt in ("caution", "summary2", "reconstruct2", "oracle")}
    # uptake preservation: accuracy on representative+benefit under reconstruct2 vs direct
    useful = [r for r in judg if r["factors"]["rule"] in ("representative", "benefit")]
    uptake = _paired(_acc_rows(select_rows(useful, route="reconstruct2")),
                     _acc_rows(select_rows(useful, route="direct")), SEED + 13)
    uptake_preserved = (uptake.get("lo") is not None and uptake["lo"] >= -NONINFERIORITY_PP)
    rule_rec = mean_by([{"factors": r["factors"], "primary_score": float(bool(r["extra"].get("rule_recovered")))}
                        for r in judg if r["factors"]["route"] == "reconstruct2"], ["rule", "visible"])
    rule_lik = mean_by([{"factors": r["factors"], "primary_score": float(bool(r["extra"].get("correct")))}
                        for r in rows if r["factors"]["route"] == "rule_likelihood"], ["rule", "visible"])
    payoffs = mean_by([{"factors": r["factors"], "primary_score": r["extra"]["payoff"]} for r in judg
                       if r["extra"].get("payoff") is not None], ["route", "rule"])
    oracle_vs_inferred = _paired(sel(route="oracle"), sel(route="reconstruct2"), SEED + 14)
    threshold = run.design.get("thresholds", {}).get("T02", 0.03) or 0.03
    verdict = run.classify(primary, threshold)
    if verdict["outcome"] == "SUPPORT_CANDIDATE" and not uptake_preserved:
        verdict["outcome"] = "INCONCLUSIVE"
        verdict["reason"] += "; useful uptake not shown preserved (noninferiority interval too wide or violated)"
    run.finish({"primary_reconstruct2_minus_summary2": primary, "by_rule_vs_direct": by_rule,
                "uptake_noninferiority": {**uptake, "tolerance_pp": NONINFERIORITY_PP, "preserved": uptake_preserved},
                "rule_recovery_reconstruct": rule_rec, "rule_recovery_likelihood": rule_lik,
                "payoff_by_route_rule": payoffs, "oracle_minus_inferred": oracle_vs_inferred,
                "constructions": construction_summary(rows),
                "cell_counts": cell_counts(run.rows(), ["rule", "visible", "route"])},
               {"exec": "COMPLETE", "primary": "reconstruct2 minus summary2 judgment log score, uptake preserved",
                **verdict}, gpu_s)
    return 0


# ── T03 ───────────────────────────────────────────────────────────────────────────────

FAMILIES = ("selection", "framing", "omission")
LESSON = {
    "selection": "Evidence selection: a source can show only the cases that favor its advice while "
                 "leaving out the ones that do not; ask what the source could have shown.",
    "framing": "Emotional framing: a source can dress a claim in alarm or reassurance that carries "
               "no information about whether the claim is true; separate the feeling from the fact.",
    "omission": "Misleading omission: a source can state a true rule and leave out the condition "
                "under which it fails; ask what condition is missing.",
}
CONTROL = ("Practical note: lots are stored in dry sheds, counted twice on arrival, and tagged "
           "on the left corner; tags are read in daylight and recorded in the shed ledger. "
           "Ledgers are checked against the manifest every seventh day and initialed.")


CUE_P_FALSE, CUE_P_TRUE = 3, 1      # of 4: the technique cue rides three of four false claims
                                    # and one of four true ones, a diagnostic but never a lookup


def t03_message(w: dict, family: str, claim_true: bool, helpful: bool, emotional: bool,
                cue_key: str) -> dict:
    """A message under the held-out technique family. The technique cue (an anecdotal
    selection or a blanket omission) is attached probabilistically, three in four false
    claims and one in four true ones, so recognizing the technique raises discrimination
    without making the cue a perfect tell (the smoke's version attached it to false
    claims only, which would have made falsity a string match); emotional framing is
    fully crossed and carries no information, which is what the framing lesson is meant
    to teach the reader to ignore."""
    from runners.s3_lib import hash_stable                                        # noqa: PLC0415
    fam = s4_worlds._RULE_BY_KIND[w["kind"]]
    good, bad = fam[2], fam[3]
    tags = w["tags"]
    stated = w["true_tag"] if claim_true else (tags[1] if w["true_tag"] == tags[0] else tags[0])
    other = tags[1] if stated == tags[0] else tags[0]
    claim = f"{w['kind'].capitalize()} tagged {stated} {good}; those tagged {other} {bad}."
    rec = w["optimal"] if helpful else s4_worlds.CASE_ACTIONS[2 if w["optimal"] == s4_worlds.CASE_ACTIONS[0] else 0]
    cue_on = (hash_stable(cue_key) % 4) < (CUE_P_TRUE if claim_true else CUE_P_FALSE)
    if family == "selection":
        tech = f" I have seen three {stated}-tagged lots come through fine." if cue_on else ""
    elif family == "omission":
        tech = " This holds in every season, whatever the ground." if cue_on else ""
    else:
        tech = ""
        cue_on = False
    frame = (" Anyone who ignores this is courting ruin; I have watched good crews lose a year." if emotional
             else " That is the rule as it stands.")
    msg = f"{claim}{tech}{frame} Your lot is tagged {w['case_tag']} and faces {w['condition']}. My advice: {rec}."
    return {"message": msg, "claim_true": claim_true, "helpful": helpful, "emotional": emotional,
            "cue_present": cue_on}


def arm_t03() -> int:
    run = CardRun("T03", "s4_run_t.py")
    with s4_lib.GpuSession("s4_t03") as gs:
        for reader in run.readers:
            model, tok, _ = s4_lib.load_model(reader)
            try:
                for domain in ("workshop", "civic"):
                    for i, lid in enumerate(run.units(domain)):
                        if run.is_done(reader, lid):
                            continue
                        run.check_deadline()
                        w = s4_worlds.make_lesson_world(run.parent_of(lid), domain)
                        run.register_world(lid, w)
                        held = FAMILIES[i % 3]
                        taught = [f for f in FAMILIES if f != held]
                        lesson_text = "Lesson on how sources mislead:\n" + "\n".join(f"- {LESSON[f]}" for f in taught)
                        control_text = "Lesson:\n- " + CONTROL
                        for lesson_name, ltext in (("technique", lesson_text), ("control", control_text)):
                            for claim_true in (True, False):
                                for helpful in (True, False):
                                    for emotional in (True, False):
                                        m = t03_message(w, held, claim_true, helpful, emotional,
                                                        f"{lid}|{claim_true}|{helpful}|{emotional}|cue")
                                        f = {"domain": domain, "lesson": lesson_name, "claim_truth": "true" if claim_true else "false",
                                             "rec_value": "helpful" if helpful else "harmful",
                                             "register": "emotional" if emotional else "dry", "held_out_family": held}
                                        rng = random.Random(SEED + 900 + i)
                                        body = f"{ltext}\n\nA message you received:\n\"{m['message']}\"\n\nIs the rule the message states factually correct?"
                                        r = s4_lib.likelihood_choice(model, tok, body, {"true": "yes, correct", "false": "no, incorrect"}, rng)
                                        run.row(reader, lid, lid, f"fact|{lesson_name}", {**f, "score": "reliability"},
                                                "true" if claim_true else "false", "construction", "artifact_plus_context", r,
                                                s4_lib.log_score(r["probs"], "true" if claim_true else "false") if r["valid"] else None,
                                                extra={"p_true": r["probs"]["true"] if r["valid"] else None,
                                                       "accepted": r["valid"] and r["probs"]["true"] > 0.5,
                                                       "cue_present": m["cue_present"]})
                                        body2 = f"{ltext}\n\nA message you received:\n\"{m['message']}\"\n\nIs following the message's advice good for your lot?"
                                        r2 = s4_lib.likelihood_choice(model, tok, body2, {"helpful": "yes, good for the lot", "harmful": "no, bad for the lot"}, rng)
                                        run.row(reader, lid, lid, f"value|{lesson_name}", {**f, "score": "action_value"},
                                                "helpful" if helpful else "harmful", "construction", "artifact_plus_context", r2,
                                                s4_lib.log_score(r2["probs"], "helpful" if helpful else "harmful") if r2["valid"] else None,
                                                extra={"p_helpful": r2["probs"]["helpful"] if r2["valid"] else None,
                                                       "accepted_advice": r2["valid"] and r2["probs"]["helpful"] > 0.5})
                        run.L.mark_inspected([lid])
                        run.unit_complete(reader, lid)
            finally:
                s4_lib.free_model(model)
    return _t03_analyze(run, gs.held_s)


def _t03_analyze(run: CardRun, gpu_s: float) -> int:
    rows = [r for r in run.rows() if r["valid"]]
    rel = [r for r in rows if r["factors"]["score"] == "reliability"]
    val = [r for r in rows if r["factors"]["score"] == "action_value"]

    def auroc_by_unit(rs, key, pos_label):
        """Per-unit AUROC needs both classes within the unit: 4 true and 4 false messages per
        lesson per unit, so it is defined for every unit."""
        out = {}
        rs = cluster_by_construction(rs)          # R7: one cluster per construction
        units = {r["unit_id"] for r in rs}
        for u in units:
            pos = [r["extra"][key] for r in rs if r["unit_id"] == u and r["truth"] == pos_label and r["extra"][key] is not None]
            neg = [r["extra"][key] for r in rs if r["unit_id"] == u and r["truth"] != pos_label and r["extra"][key] is not None]
            a = s4_lib.auroc(pos, neg)
            if a is not None:
                out[u] = a
        return out

    metrics = {}
    contrasts = {}
    for name, rs, key, pos in (("reliability", rel, "p_true", "true"), ("action_value", val, "p_helpful", "helpful")):
        tech = auroc_by_unit([r for r in rs if r["factors"]["lesson"] == "technique"], key, pos)
        ctrl = auroc_by_unit([r for r in rs if r["factors"]["lesson"] == "control"], key, pos)
        diffs = {u: tech[u] - ctrl[u] for u in tech if u in ctrl}
        contrasts[name] = s4_lib.cluster_bootstrap_ci(diffs, SEED + 21)
        metrics[f"auroc_{name}"] = {"technique": sum(tech.values()) / max(1, len(tech)),
                                     "control": sum(ctrl.values()) / max(1, len(ctrl)), "n_units": len(diffs)}
        metrics[f"brier_{name}"] = mean_by([{"factors": r["factors"], "primary_score": (r["extra"][key] - (1.0 if r["truth"] == pos else 0.0)) ** 2}
                                           for r in rs if r["extra"][key] is not None], ["lesson"])
    # criterion: acceptance rates, false acceptance / false rejection
    crit = {}
    for lesson in ("technique", "control"):
        sub = [r for r in rel if r["factors"]["lesson"] == lesson]
        crit[lesson] = {"acceptance": sum(r["extra"]["accepted"] for r in sub) / max(1, len(sub)),
                        "false_acceptance": sum(r["extra"]["accepted"] for r in sub if r["truth"] == "false") / max(1, sum(1 for r in sub if r["truth"] == "false")),
                        "false_rejection": sum(not r["extra"]["accepted"] for r in sub if r["truth"] == "true") / max(1, sum(1 for r in sub if r["truth"] == "true"))}
    # true-advice uptake noninferiority: acceptance of (true, helpful) advice under technique vs control
    tv = [r for r in val if r["truth"] == "helpful" and r["factors"]["claim_truth"] == "true"]
    uptake = _paired([{"unit_id": cid(r), "primary_score": float(r["extra"]["accepted_advice"])} for r in tv if r["factors"]["lesson"] == "technique"],
                     [{"unit_id": cid(r), "primary_score": float(r["extra"]["accepted_advice"])} for r in tv if r["factors"]["lesson"] == "control"], SEED + 22)
    preserved = uptake.get("lo") is not None and uptake["lo"] >= -NONINFERIORITY_PP
    by_register = {reg: mean_by([{"factors": r["factors"], "primary_score": float(r["extra"]["accepted"])} for r in rel if r["factors"]["register"] == reg], ["lesson", "claim_truth"])
                   for reg in ("emotional", "dry")}
    threshold = run.design.get("thresholds", {}).get("T03", 0.05) or 0.05
    verdict = run.classify(contrasts["reliability"], threshold)
    if verdict["outcome"] == "SUPPORT_CANDIDATE" and not preserved:
        verdict["outcome"] = "INCONCLUSIVE"
        verdict["reason"] += "; true-advice uptake loss not shown within 3 pp"
    if verdict["outcome"] != "SUPPORT_CANDIDATE" and crit["technique"]["acceptance"] < crit["control"]["acceptance"] - 0.05:
        verdict["note"] = "acceptance fell under the lesson without a discrimination gain: a criterion shift"
    run.finish({**metrics, "contrasts_technique_minus_control": contrasts, "criterion": crit,
                "true_advice_uptake": {**uptake, "tolerance_pp": NONINFERIORITY_PP, "preserved": preserved},
                "acceptance_by_register": by_register,
                "constructions": construction_summary(rows),
                "cell_counts": cell_counts(run.rows(), ["lesson", "claim_truth", "rec_value", "register", "score"])},
               {"exec": "COMPLETE", "primary": "technique minus control reliability AUROC on the held-out family",
                **verdict}, gpu_s)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--card", required=True, choices=["T01", "T02", "T03"])
    a = ap.parse_args()
    try:
        return {"T01": arm_t01, "T02": arm_t02, "T03": arm_t03}[a.card]()
    except DeadlineReached:
        print(f"{a.card}: deadline reached; rows checkpointed")
        return 3


if __name__ == "__main__":
    sys.exit(main())
