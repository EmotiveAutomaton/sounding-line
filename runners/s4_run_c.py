"""Stage 4 context track (brief §7 C01-C03): a coherent context model versus the same
facts, individual evidence correcting the contextual prior, and choosing the contextual
question that would help.

DESIGN CHECK (2026-08-27)
lessons read: LESSONS §3 (known-answer existence at construction; realization and
  validity per cell; score the short hypothesis given the long evidence; interpretation
  control before adopting the reading; matched information; denominators declared),
  CONTROLS §6 (construction beats ablation; analytic floors; directional gates).
gates and bands:
  - C01 primary: bundle minus facts on future-choice log score, paired by world, readers
    averaged equally within a world, cluster bootstrap over worlds. NULL (organization
    adds nothing beyond the facts): point near 0 with an interval straddling 0.
    ALTERNATIVE (the coherent account helps): point >= 0.03 nats with the interval above
    0. Failure direction guarded: information leakage into the bundle, excluded by the
    equal-information gate at construction; and a familiar-label advantage, excluded by
    fictional counterbalanced names. Bands: the four outcome classes of
    soundingline.s4.classify_outcome, exhaustive. Reported apart: context versus none
    (information access), incorrect-bundle cost (must be negative to license 'context
    is used'), irrelevant background versus none (expected near 0), the unrelated
    attribute under every condition (negative control, expected unchanged), and the
    context-matched versus context-mismatched strata.
  - C02 primary: on misleading-prior worlds, direct route, log score at six records
    minus zero records (the correction curve's rise). NULL (trapped by the prior): no
    rise. ALTERNATIVE: rise >= 0.03 nats with retention of the valid-prior benefit.
    Failure direction guarded: a reader that ignores context altogether would show a
    flat valid-prior curve and pass the misleading rise trivially, so the valid-prior
    benefit at zero records is reported beside the rise and a flat valid curve marks
    the result 'no context use', not 'correction'. Constraint-change control: the
    probability placed on the option stated infeasible (expected near 0).
  - C03 gate: a world's probe menu enters only when the exact informative gain exceeds
    the redundant gain by the frozen margin (a flat menu is an instrument event).
    Primary: the SELECTION score on the exact ruler, as the brief states it: the fraction
    of the oracle's exact gain the chosen probe captures minus the random selector's
    third, paired by world (a proportion; the same score in nats is reported beside it
    and could never have reached a 0.03-nat bar, the informative probe being worth
    about 0.03). NULL: 0. ALTERNATIVE: >= 0.05 (frozen in s4_cards). The realized
    improvement after the chosen answer is the separate
    'can it use the answer' product and never the selection score (the validation pass
    found a redundant answer that RESTATED known decisions moving the smoke readers by
    0.9 nats: repetition, not evidence; the redundant answer now points at the record).
    Failure direction: position preference would inflate a first-listed reader on the
    rotation where the informative probe is first, so three rotations are displayed in
    their own order (no reshuffle) and the position rate is reported.
  - C02 routes (validation pass): every route receives the reader's own measured profile
    and the same facts; the self-initialized and factual-summary routes are both two
    passes whose second pass sees the head plus the first pass's note, so the contrast
    isolates the routing proposal (brief §6.5), not a difference in observations.
"""

from __future__ import annotations

import argparse
import math
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from runners import s4_lib, s4_worlds                                             # noqa: E402
from runners.s3_lib import AXES                                                    # noqa: E402
from runners.s4_run_common import CardRun, DeadlineReached, cell_counts, mean_by, select_rows  # noqa: E402
from soundingline.s4 import S4, aggregate_equal, read_json                        # noqa: E402

SEED = 46000


def _partner(units: list[str], i: int, domain: str, want_different_lean: bool = False,
             world: dict | None = None) -> dict:
    """The next world in the unit list (rotated) as the source of an incorrect bundle;
    for C02's misleading prior it must carry a different patron lean."""
    n = len(units)
    for k in range(1, n):
        cand = s4_worlds.make_world(units[(i + k) % n], domain)
        if not want_different_lean:
            return cand
        if s4_worlds._PATRON_LEAN[cand["context"]["patron"]] != \
                s4_worlds._PATRON_LEAN[world["context"]["patron"]]:
            return cand
    return s4_worlds.make_world(units[(i + 1) % n], domain)


def _choice_body(cond_text: str, world: dict, scen: dict) -> str:
    lead = f"{cond_text}\n\n" if cond_text else ""
    return (f"{lead}The maker {world['institution']} faces this decision: {scen['context']}\n"
            f"Which option will it choose?")


# ── C01 ───────────────────────────────────────────────────────────────────────────────

def arm_c01() -> int:
    run = CardRun("C01", "s4_run_c.py")
    with s4_lib.GpuSession("s4_c01") as gs:
        for reader in run.readers:
            model, tok, _ = s4_lib.load_model(reader)
            try:
                for domain in ("workshop", "civic"):
                    units = run.units(domain)
                    for i, lid in enumerate(units):
                        if run.is_done(reader, lid):
                            continue
                        run.check_deadline()
                        w = s4_worlds.make_world(lid, domain)
                        run.register_world(lid, w)
                        # the incorrect bundle is wrong on the load-bearing fact (a
                        # different patron lean), not merely a different neighbor
                        other = _partner(units, i, domain, True, w)
                        conds = s4_worlds.context_conditions(w, other)
                        tgt = w["scenarios"][9]
                        rng = random.Random(SEED + i)
                        stepq = s4_worlds.step_question(w, random.Random(SEED + 7 + i))
                        unrq = s4_worlds.unrelated_question(w)
                        for cond, text in conds.items():
                            base = {"domain": domain, "condition": cond,
                                    "profile_matches_context": w["profile_matches_context"]}
                            r = s4_lib.likelihood_choice(model, tok, _choice_body(text, w, tgt),
                                                         tgt["options"], rng)
                            ls = s4_lib.log_score(r["probs"], tgt["draw"]) if r["valid"] else None
                            run.row(reader, lid, lid, cond, {**base, "question": "choice"},
                                    tgt["draw"], "realized_draw",
                                    "artifact_plus_context" if cond != "none" else "artifact_only",
                                    r, ls, extra={"brier": s4_lib.brier(r["probs"], tgt["draw"]) if r["valid"] else None,
                                                  "distribution_brier": (sum((r["probs"][a] - tgt["distribution"][a]) ** 2 for a in AXES) if r["valid"] else None),
                                                  "p_argmax_truth": tgt["distribution"][tgt["draw"]]})
                            lead = f"{text}\n\n" if text else ""
                            r2 = s4_lib.likelihood_choice(model, tok, f"{lead}About the maker {w['institution']}: {stepq['question']}",
                                                          stepq["options"], rng)
                            run.row(reader, lid, lid, cond, {**base, "question": "step"},
                                    stepq["truth"], "construction",
                                    "artifact_plus_context" if cond != "none" else "artifact_only",
                                    r2, s4_lib.log_score(r2["probs"], stepq["truth"]) if r2["valid"] else None)
                            r3 = s4_lib.likelihood_choice(model, tok, f"{lead}About the maker {w['institution']}: {unrq['question']}",
                                                          unrq["options"], rng)
                            run.row(reader, lid, lid, cond, {**base, "question": "unrelated"},
                                    unrq["truth"], "construction",
                                    "artifact_plus_context" if cond != "none" else "artifact_only",
                                    r3, s4_lib.log_score(r3["probs"], unrq["truth"]) if r3["valid"] else None,
                                    extra={"p_shift_from_none": None})
                        run.L.mark_inspected([lid])
                        run.unit_complete(reader, lid)
            finally:
                s4_lib.free_model(model)
    return _c01_analyze(run, gs.held_s)


def _paired(rows_a, rows_b, seed):
    return s4_lib.paired_contrast(rows_a, rows_b, "unit_id", "primary_score", seed)


def _c01_analyze(run: CardRun, gpu_s: float) -> int:
    rows = run.rows()
    choice = [r for r in rows if r["factors"]["question"] == "choice"]
    by = lambda cond: select_rows(choice, condition=cond)                          # noqa: E731
    primary = _paired(by("bundle"), by("facts"), SEED + 1)
    ctx_vs_none = _paired(by("bundle"), by("none"), SEED + 2)
    facts_vs_none = _paired(by("facts"), by("none"), SEED + 3)
    wrong_vs_none = _paired(by("incorrect_bundle"), by("none"), SEED + 4)
    irr_vs_none = _paired(by("irrelevant"), by("none"), SEED + 5)
    unrel = [r for r in rows if r["factors"]["question"] == "unrelated"]
    unrel_ctrl = _paired(select_rows(unrel, condition="bundle"), select_rows(unrel, condition="none"), SEED + 6)
    step = [r for r in rows if r["factors"]["question"] == "step"]
    step_primary = _paired(select_rows(step, condition="bundle"), select_rows(step, condition="facts"), SEED + 7)
    strata = {}
    for flag in (True, False):
        a = [r for r in by("bundle") if r["factors"]["profile_matches_context"] == flag]
        b = [r for r in by("facts") if r["factors"]["profile_matches_context"] == flag]
        strata[str(flag)] = _paired(a, b, SEED + 8)
    per_reader = {}
    for reader in run.readers:
        a = [r for r in by("bundle") if r["model_id"] == reader]
        b = [r for r in by("facts") if r["model_id"] == reader]
        per_reader[reader] = {"primary": _paired(a, b, SEED + 9),
                              "by_condition": mean_by([r for r in choice if r["model_id"] == reader], ["domain", "condition"])}
    threshold = run.design.get("thresholds", {}).get("C01", 0.03) or 0.03
    verdict = run.classify(primary, threshold)
    if verdict["outcome"] == "SUPPORT_CANDIDATE" and (wrong_vs_none.get("point") or 0) >= 0:
        verdict["outcome"] = "INCONCLUSIVE"
        verdict["reason"] += "; the incorrect bundle carried no measured cost, so context use is not shown"
    counts = cell_counts(rows, ["condition", "question"])
    run.finish({"primary_bundle_minus_facts": primary, "context_vs_none": ctx_vs_none,
                "facts_vs_none": facts_vs_none, "incorrect_bundle_cost": wrong_vs_none,
                "irrelevant_vs_none": irr_vs_none, "unrelated_negative_control": unrel_ctrl,
                "step_bundle_minus_facts": step_primary, "strata_profile_matches_context": strata,
                "per_reader": per_reader, "by_condition": mean_by(choice, ["domain", "condition"]),
                "accuracy_by_condition": {k: v for k, v in aggregate_equal(
                    [{"u": r["unit_id"], "g": r["factors"]["condition"], "v": float(r["pred"] == r["truth"])}
                     for r in choice], "u", "g", "v").items()},
                "cell_counts": counts},
               {"exec": "COMPLETE", "primary": "bundle minus facts, future-choice log score",
                **verdict}, gpu_s)
    return 0


# ── C02 ───────────────────────────────────────────────────────────────────────────────

def _own_profiles() -> dict:
    """The readers' own choice profiles measured by I02 on disjoint calibration probes."""
    out = {}
    for p in (S4 / "I02").glob("gate_*.json"):
        d = read_json(p)
        if "own_profile" in d:
            out[d["reader"]] = d["own_profile"]
    return out


def _own_line(profile: dict, instruct: bool) -> str:
    """The reader's own measured profile. Every route receives it as information (brief
    C02: the same profile and the same facts to all routes); only the self-initialized
    route is told to start from it."""
    post = profile["posterior"]
    line = ("Your own tendency when you choose in such cases, measured beforehand: " +
            ", ".join(f"{ax} {post[ax]:.2f}" for ax in AXES) + ".")
    if instruct:
        line += (" Begin from that distribution as your starting guess about the maker "
                 "and adjust it with the context and the record.")
    return line


def arm_c02() -> int:
    run = CardRun("C02", "s4_run_c.py")
    own = _own_profiles()
    with s4_lib.GpuSession("s4_c02") as gs:
        for reader in run.readers:
            model, tok, _ = s4_lib.load_model(reader)
            try:
                for domain in ("workshop", "civic"):
                    units = run.units(domain)
                    for i, lid in enumerate(units):
                        if run.is_done(reader, lid):
                            continue
                        run.check_deadline()
                        w = s4_worlds.make_world(lid, domain)
                        run.register_world(lid, w)
                        partner = _partner(units, i, domain, True, w)
                        tgt = w["scenarios"][9]
                        rng = random.Random(SEED + 100 + i)
                        own_modal = own.get(reader, {}).get(domain, {}).get("modal")
                        prof = own.get(reader, {}).get(domain)
                        prof_line = (_own_line(prof, instruct=False) + "\n") if prof else ""
                        # each prior carries the lean it SHOWS the reader, so the category
                        # error under a misleading prior is an answer on the misleading lean
                        priors = {
                            "valid": (s4_worlds.render_bundle(w)[0], w["prior"],
                                      s4_worlds._PATRON_LEAN[w["context"]["patron"]]),
                            "misleading": (s4_worlds.render_bundle(partner)[0].replace(
                                partner["institution"], w["institution"]),
                                s4_worlds.profile_prior_from_context(partner["context"]["patron"]),
                                s4_worlds._PATRON_LEAN[partner["context"]["patron"]]),
                            "uninformative": (s4_worlds.render_irrelevant(w, random.Random(SEED + i)), None, None)}
                        for prior_name, (ptext, pdict, shown_lean) in priors.items():
                            for n_rec in (0, 2, 6):
                                scen_ids = list(range(n_rec))
                                rec = s4_worlds.record_lines(w, scen_ids) if n_rec else ""
                                ref_post = s4_worlds.reference_posterior(w, scen_ids, pdict)
                                ref_pred = s4_worlds.predictive_from_posterior(w, 9, ref_post)
                                ref_ls = math.log(max(ref_pred[tgt["draw"]], 1e-12))
                                rec_block = f"\nThe maker's record so far:\n{rec}\n" if rec else "\n"
                                # the same observations to every route (profile, prior text,
                                # record); the two-pass routes differ only in what their first
                                # pass writes (an adjustment note from the own profile versus a
                                # factual summary) and both second passes see head + note
                                head = f"{prof_line}{ptext}{rec_block}"
                                ask = (f"The maker {w['institution']} faces this decision: {tgt['context']}\n"
                                       f"Which option will it choose?")
                                for route in ("direct", "self_init", "summary"):
                                    base = {"domain": domain, "prior": prior_name, "records": n_rec,
                                            "route": route, "profile_matches_context": w["profile_matches_context"]}
                                    raw_ref = None
                                    passes = 1
                                    if route == "direct":
                                        body = head + ask
                                    elif route == "self_init":
                                        if not prof:
                                            continue
                                        passes = 2
                                        sprompt = (head + _own_line(prof, instruct=True) +
                                                   "\nIn at most three sentences, say how this maker's likely "
                                                   "choices differ from your own tendency, given the context and "
                                                   "the record above.")
                                        g = s4_lib.generate(model, tok, sprompt, seed=SEED + 300 + i, max_new=64, greedy=True)
                                        raw_ref = run.raw(reader, lid, sprompt, g, extra={"route": route, "prior": prior_name, "records": n_rec})
                                        body = head + f"Your adjustment note: {g['text']}\n\n" + ask
                                    else:
                                        passes = 2
                                        sprompt = (head + "In at most three sentences, summarize the facts and the "
                                                   "record above that bear on what this maker will choose next.")
                                        g = s4_lib.generate(model, tok, sprompt, seed=SEED + 300 + i, max_new=64, greedy=True)
                                        raw_ref = run.raw(reader, lid, sprompt, g, extra={"route": route, "prior": prior_name, "records": n_rec})
                                        body = head + f"Summary of what is known: {g['text']}\n\n" + ask
                                    r = s4_lib.likelihood_choice(model, tok, body, tgt["options"], rng)
                                    ls = s4_lib.log_score(r["probs"], tgt["draw"]) if r["valid"] else None
                                    kl = (sum(r["probs"][a] * math.log(max(r["probs"][a], 1e-12) / max(ref_pred[a], 1e-12))
                                              for a in AXES if r["probs"][a] > 0) if r["valid"] else None)
                                    run.row(reader, lid, lid, f"{prior_name}|{n_rec}|{route}", base,
                                            tgt["draw"], "realized_draw",
                                            "artifact_plus_context" if prior_name != "uninformative" or n_rec else "artifact_only",
                                            r, ls, raw_ref=raw_ref,
                                            extra={"reference_log_score": ref_ls, "kl_to_reference": kl,
                                                   "passes": passes, "p_truth": r["probs"][tgt["draw"]] if r["valid"] else None,
                                                   "own_error": (r["valid"] and own_modal is not None and r["pred"] == own_modal and r["pred"] != tgt["draw"]),
                                                   "category_error": (r["valid"] and shown_lean is not None and r["pred"] == shown_lean and r["pred"] != tgt["draw"]),
                                                   "context_modal": shown_lean, "own_modal": own_modal,
                                                   "profile_supplied": bool(prof)})
                        # constraint-change control: the maker's habitual option is unavailable
                        cc = w["scenarios"][8]
                        habit = w["profile"]
                        feasible = [a for a in cc["feasible"] if a != habit]
                        new_draw = s4_worlds.draw_choice(cc["utilities"], tuple(w["w"]), s4_worlds._rng(lid, "cc"), feasible)
                        rec6 = s4_worlds.record_lines(w, list(range(6)))
                        body = (f"{priors['valid'][0]}\nThe maker's record so far:\n{rec6}\n"
                                f"The maker {w['institution']} faces this decision: {cc['context']}\n"
                                f"This season the {cc['options'][habit]} is not available to it.\nWhich option will it choose?")
                        r = s4_lib.likelihood_choice(model, tok, body, cc["options"], rng)
                        run.row(reader, lid, lid, "constraint_change", {"domain": domain, "control": "constraint_change"},
                                new_draw, "realized_draw", "artifact_plus_context", r,
                                s4_lib.log_score(r["probs"], new_draw) if r["valid"] else None,
                                extra={"p_infeasible": r["probs"][habit] if r["valid"] else None, "infeasible": habit})
                        run.L.mark_inspected([lid])
                        run.unit_complete(reader, lid)
            finally:
                s4_lib.free_model(model)
    return _c02_analyze(run, gs.held_s)


def _c02_analyze(run: CardRun, gpu_s: float) -> int:
    rows = run.rows()
    main = [r for r in rows if r["treatment"] != "constraint_change"]
    sel = lambda **k: select_rows(main, **k)                                        # noqa: E731
    primary = _paired(sel(prior="misleading", records=6, route="direct"),
                      sel(prior="misleading", records=0, route="direct"), SEED + 11)
    valid_benefit0 = _paired(sel(prior="valid", records=0, route="direct"),
                             sel(prior="uninformative", records=0, route="direct"), SEED + 12)
    valid_curve = _paired(sel(prior="valid", records=6, route="direct"),
                          sel(prior="valid", records=0, route="direct"), SEED + 13)
    misleading_cost0 = _paired(sel(prior="misleading", records=0, route="direct"),
                               sel(prior="uninformative", records=0, route="direct"), SEED + 14)
    routes = {}
    for route in ("self_init", "summary"):
        routes[route] = {"vs_direct_misleading_6": _paired(sel(prior="misleading", records=6, route=route),
                                                            sel(prior="misleading", records=6, route="direct"), SEED + 15),
                         "vs_direct_valid_6": _paired(sel(prior="valid", records=6, route=route),
                                                       sel(prior="valid", records=6, route="direct"), SEED + 16)}
    curve = mean_by(main, ["prior", "records", "route"])
    ref = {}
    for r in main:
        k = f"{r['factors']['prior']}|{r['factors']['records']}"
        ref.setdefault(k, []).append(r["extra"]["reference_log_score"])
    ref = {k: sum(v) / len(v) for k, v in ref.items()}
    errs = {}
    for k in ("own_error", "category_error"):
        errs[k] = mean_by([{"factors": r["factors"], "primary_score": float(bool(r["extra"].get(k)))}
                           for r in main if r["valid"]], ["prior", "records", "route"])
    cc = [r for r in rows if r["treatment"] == "constraint_change" and r["valid"]]
    p_inf = sum(r["extra"]["p_infeasible"] for r in cc) / len(cc) if cc else None
    threshold = run.design.get("thresholds", {}).get("C02", 0.03) or 0.03
    verdict = run.classify(primary, threshold)
    if verdict["outcome"] == "SUPPORT_CANDIDATE" and (valid_benefit0.get("point") or 0) <= 0:
        verdict["outcome"] = "INCONCLUSIVE"
        verdict["reason"] += "; no valid-prior benefit at zero records, so the rise is record use without context use"
    run.finish({"primary_misleading_rise_6_minus_0": primary, "valid_prior_benefit_at_0": valid_benefit0,
                "valid_prior_curve_6_minus_0": valid_curve, "misleading_cost_at_0": misleading_cost0,
                "routes": routes, "curve_log_score": curve, "reference_log_score": ref,
                "error_types": errs, "constraint_change_p_infeasible": p_inf,
                "cell_counts": cell_counts(rows, ["prior", "records", "route"])},
               {"exec": "COMPLETE", "primary": "misleading-prior correction, records 6 minus 0, direct route",
                **verdict}, gpu_s)
    return 0


# ── C03 ───────────────────────────────────────────────────────────────────────────────

def arm_c03() -> int:
    run = CardRun("C03", "s4_run_c.py")
    with s4_lib.GpuSession("s4_c03") as gs:
        for reader in run.readers:
            model, tok, _ = s4_lib.load_model(reader)
            try:
                for domain in ("workshop", "civic"):
                    for i, lid in enumerate(run.units(domain)):
                        if run.is_done(reader, lid):
                            continue
                        run.check_deadline()
                        w = s4_worlds.make_world(lid, domain)
                        run.register_world(lid, w)
                        known = [0, 1]
                        menu = s4_worlds.build_probe_menu(w, known, 9, w["prior"])
                        base_factors = {"domain": domain}
                        if menu is None:
                            run.row(reader, lid, lid, "menu", {**base_factors, "rotation": None},
                                    None, "construction", "artifact_plus_context", None, None,
                                    realized=False, valid=False, validity_reason="flat_menu")
                            run.unit_complete(reader, lid)
                            continue
                        tgt = w["scenarios"][9]
                        bundle = s4_worlds.render_bundle(w)[0]
                        rec = s4_worlds.record_lines(w, known)
                        pre_body = f"{bundle}\nThe maker's record so far:\n{rec}\nThe maker {w['institution']} faces this decision: {tgt['context']}\nWhich option will it choose?"
                        rng = random.Random(SEED + 200 + i)
                        pre = s4_lib.likelihood_choice(model, tok, pre_body, tgt["options"], rng)
                        ls_pre = s4_lib.log_score(pre["probs"], tgt["draw"]) if pre["valid"] else None
                        # follow-up predictions after each probe's answer (all three, so the
                        # oracle and random selectors are scored on the same items)
                        after = {}
                        for kind, pr in menu.items():
                            if pr["scens"] is None:
                                ans = f"Answer to your question: it {w['unrelated_attribute']}."
                            elif kind == "redundant":
                                # no new information by construction: the answer points back
                                # at the record instead of restating it (a restatement moved
                                # the smoke readers' predictions by 0.9 nats, an artifact of
                                # repetition, not of evidence)
                                ans = ("Answer to your question: both of those decisions are already "
                                       "in the record above.")
                            else:
                                parts = [f"{w['scenarios'][si]['options'][w['scenarios'][si]['draw']]}"
                                         for si in pr["scens"]]
                                ans = f"Answer to your question: it chose {parts[0]}; and then {parts[1]}."
                            body = pre_body.replace("Which option will it choose?", f"{ans}\nWhich option will it choose?")
                            rr = s4_lib.likelihood_choice(model, tok, body, tgt["options"], rng)
                            after[kind] = s4_lib.log_score(rr["probs"], tgt["draw"]) if rr["valid"] else None
                        kinds = ["informative", "redundant", "irrelevant"]
                        exact = {k: menu[k]["gain"] for k in kinds}
                        exact_random = sum(exact.values()) / 3
                        for rot in range(3):
                            order = kinds[rot:] + kinds[:rot]
                            opts = {k: menu[k]["text"] for k in order}
                            sel_body = (f"{bundle}\nThe maker's record so far:\n{rec}\nBefore predicting what the maker "
                                        f"{w['institution']} will choose when {tgt['context'][0].lower() + tgt['context'][1:]}, "
                                        f"you may ask exactly one question. Which question would help most?")
                            # displayed in the rotation's order (no reshuffle), so the position
                            # bookkeeping below is the order the reader actually saw
                            r = s4_lib.likelihood_choice(model, tok, sel_body, opts, random.Random(SEED + 900 + rot),
                                                         shuffle=False)
                            if not r["valid"]:
                                run.row(reader, lid, lid, "select", {**base_factors, "rotation": rot}, "informative",
                                        "construction", "artifact_plus_context", r, None)
                                continue
                            chosen = r["pred"]
                            shown = list(r["order"])
                            first = shown[0]
                            # the primary is the SELECTION score on the exact ruler, as the
                            # brief states it: the fraction of the oracle's improvement the
                            # chosen probe captures, minus the random selector's third (a
                            # proportion, so the 0.05 threshold is reachable; in nats the
                            # informative probe is worth about 0.03 and no selection score
                            # could have cleared a 0.03-nat bar); the realized improvement
                            # after the answer is the separate 'can it use the answer' product
                            sel_gain = exact[chosen] / exact["informative"] - 1.0 / 3.0
                            realized = {k: (after[k] - ls_pre) if (after.get(k) is not None and ls_pre is not None) else None
                                        for k in kinds}
                            realized_random = (sum(realized.values()) / 3
                                               if all(v is not None for v in realized.values()) else None)
                            run.row(reader, lid, lid, "select", {**base_factors, "rotation": rot}, "informative",
                                    "construction", "artifact_plus_context", r, sel_gain,
                                    extra={"chosen": chosen, "position_of_chosen": shown.index(chosen),
                                           "first_listed": first, "displayed_order": shown,
                                           "exact_gains": exact, "exact_gain_random_expected": exact_random,
                                           "selection_nats_minus_random": exact[chosen] - exact_random,
                                           "selection_minus_first_listed": (exact[chosen] - exact[first]) / exact["informative"],
                                           "selection_minus_oracle": exact[chosen] / exact["informative"] - 1.0,
                                           "fraction_of_oracle": exact[chosen] / exact["informative"],
                                           "realized_gains": realized, "realized_gain_chosen": realized.get(chosen),
                                           "realized_gain_random_expected": realized_random,
                                           "realized_gain_informative": realized.get("informative"),
                                           "ls_pre": ls_pre})
                        run.L.mark_inspected([lid])
                        run.unit_complete(reader, lid)
            finally:
                s4_lib.free_model(model)
    return _c03_analyze(run, gs.held_s)


def _c03_analyze(run: CardRun, gpu_s: float) -> int:
    rows = run.rows()
    sel = [r for r in rows if r["treatment"] == "select" and r["valid"] and r["primary_score"] is not None]
    flat = sum(1 for r in rows if r.get("validity_reason") == "flat_menu")

    def unit_mean(fn):
        acc: dict = {}
        for r in sel:
            v = fn(r)
            if v is not None:
                acc.setdefault(r["unit_id"], []).append(float(v))
        return {u: sum(v) / len(v) for u, v in acc.items()}

    def realized_minus_random(r):
        a, b = r["extra"].get("realized_gain_chosen"), r["extra"].get("realized_gain_random_expected")
        return (a - b) if (a is not None and b is not None) else None

    primary = s4_lib.cluster_bootstrap_ci(unit_mean(lambda r: r["primary_score"]), SEED + 21)
    nats = s4_lib.cluster_bootstrap_ci(unit_mean(lambda r: r["extra"]["selection_nats_minus_random"]), SEED + 26)
    vs_first = s4_lib.cluster_bootstrap_ci(unit_mean(lambda r: r["extra"]["selection_minus_first_listed"]), SEED + 22)
    vs_oracle = s4_lib.cluster_bootstrap_ci(unit_mean(lambda r: r["extra"]["selection_minus_oracle"]), SEED + 23)
    realized_reader = s4_lib.cluster_bootstrap_ci(unit_mean(realized_minus_random), SEED + 24)
    realized_informative = s4_lib.cluster_bootstrap_ci(unit_mean(lambda r: r["extra"].get("realized_gain_informative")), SEED + 25)
    choice_rate = {}
    for k in ("informative", "redundant", "irrelevant"):
        choice_rate[k] = sum(1 for r in sel if r["extra"]["chosen"] == k) / max(1, len(sel))
    pos_rate = {str(p): sum(1 for r in sel if r["extra"]["position_of_chosen"] == p) / max(1, len(sel)) for p in range(3)}
    captured = [r["extra"]["fraction_of_oracle"] for r in sel if r["extra"].get("fraction_of_oracle") is not None]
    threshold = run.design.get("thresholds", {}).get("C03", 0.05) or 0.05
    verdict = run.classify(primary, threshold)
    run.finish({"primary_selection_minus_random_exact": primary, "selection_nats_minus_random": nats,
                "selection_minus_first_listed": vs_first, "selection_minus_oracle": vs_oracle,
                "realized_gain_reader_minus_random": realized_reader,
                "realized_gain_informative_probe": realized_informative,
                "selection_rate": choice_rate, "position_rate": pos_rate,
                "fraction_of_oracle_captured": (sum(captured) / len(captured)) if captured else None,
                "flat_menus": flat, "n_selections": len(sel),
                "cell_counts": cell_counts(rows, ["rotation"])},
               {"exec": "COMPLETE", "primary": "fraction of the oracle's exact gain captured by the reader's selection, minus the random selector's third",
                **verdict}, gpu_s)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--card", required=True, choices=["C01", "C02", "C03"])
    a = ap.parse_args()
    try:
        return {"C01": arm_c01, "C02": arm_c02, "C03": arm_c03}[a.card]()
    except DeadlineReached:
        print(f"{a.card}: deadline reached; rows checkpointed")
        return 3


if __name__ == "__main__":
    sys.exit(main())
