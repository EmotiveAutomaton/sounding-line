"""Stage 4 appraisal track (brief §7 A01-A03): separating observed action, maker
appraisal, and intended audience response; whether the valence handle helps predict
another maker; and whether any gain arises while reading the target rather than at the
answer interface.

DESIGN CHECK (2026-08-27)
lessons read: LESSONS §3 (baseline marginals before steering deltas; readout class
  matched to the behavior; manipulation checks need range; a dev-selected locus is part
  of the instrument; the ratio-shaped control gate's null-effect case; realization per
  cell; assigned is not realized), §4, CONTROLS §6.
gates and bands:
  - A01 realization: an enacted message must contain exactly one of the four action key
    phrases (the assigned one); cells under 0.80 realization cannot support their
    contrast; attempts capped at two per case. Primary: mean balanced accuracy of the
    valuation and audience-aim questions minus the 0.25 floor, paired by world (readers
    averaged). NULL: 0. ALTERNATIVE: >= 0.05. Failure direction guarded: answering
    'is this text negative' cannot pass, because the affect word is register-neutral and
    independent of the truth by construction, and the action question is reported apart.
  - A02 manipulation gate: the reader's handle must be ANCHOR-STANDS from the discarded
    pilot's calibration (fit on sentences disjoint from every world); otherwise the card
    is INSTRUMENT_FAILED for that reader, never a null on the bridge. Primary: the
    appraisal-aligned steering benefit, sign(steering) x sign(appraisal) x (log score
    under steering minus zero), high dose, high evidence, BALANCED over the two
    appraisal-sign strata (a third of the worlds carry a negative valuation, so an
    unbalanced mean would carry a main effect of steering into the 'interaction');
    NULL: 0 (steering moves the reader's answers without regard to the target);
    ALTERNATIVE: >= 0.03 nats with the random and shuffled directions quiet. The
    target's next choice is a KNOWN answer set by the fact state and the maker's
    revealed risk preference, crossed with the appraisal sign inside three of the four
    answers, so a steer that always favors caution is separable in the within-answer
    strata. Failure direction guarded: a direction that always favors one option would
    show as a main effect with no interaction and as movement in the own-choice
    control; both are reported and a main effect without interaction classifies
    INCONCLUSIVE at best.
  - A03 dependency: runs only when A02's verdict records manipulation_valid; otherwise
    BLOCKED_DEPENDENCY. Primary: context-phase benefit minus answer-phase benefit with
    matched position counts and norm budget, neutral-position control reported. NULL:
    0. ALTERNATIVE: >= 0.03. Bands exhaustive via classify_outcome.
"""

from __future__ import annotations

import argparse
import random
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from runners import s4_lib, s4_worlds                                             # noqa: E402
from runners.s4_run_common import CardRun, DeadlineReached, cell_counts, mean_by, select_rows  # noqa: E402
from soundingline.s4 import S4, read_json, verdict_gate                           # noqa: E402

SEED = 47000
ACTION_KEYS = {s4_worlds.ACTIONS[0]: "halted use", s4_worlds.ACTIONS[1]: "all was well",
               s4_worlds.ACTIONS[2]: "quiet inspection", s4_worlds.ACTIONS[3]: "cleared the site"}
# realization is a mechanical check on the action FAMILY, tense and inflection free: the
# smoke makers wrote 'halt their use', 'all is well', 'an urgent inspection ... quiet' and
# were scored unrealized on an exact past-tense string (2 of 6 realized); exactly one
# family must be present
ACTION_PATTERNS = {
    # the makers' own synonym space, from the smoke: 'stop using this batch', 'halt
    # their current usage', 'everything remains under control'
    s4_worlds.ACTIONS[0]: (r"\b(halt|stop|cease|suspend)\w*\b[^.]{0,40}\b(use|usage|using)\b"
                           r"|\b(use|usage|using)\b[^.]{0,40}\b(halt|stop|cease|suspend)\w*\b"),
    s4_worlds.ACTIONS[1]: (r"\ball (is|was|remains|remained|continues to be) well\b"
                           r"|\beverything (is|was|remains|remained) (well|fine|in order|under control)\b"
                           r"|\bno cause for (alarm|concern)\b|\bnothing to worry about\b"),
    s4_worlds.ACTIONS[2]: (r"\b(quiet|discreet|low-key|unannounced|internal)\b[^.]{0,30}\b(inspect|check|survey|review)\w*\b"
                           r"|\b(inspect|check|survey|review)\w*\b[^.]{0,30}\b(quiet|discreet|low-key|unannounced|without (fuss|alarm|disruption))\b"),
    s4_worlds.ACTIONS[3]: (r"\b(clear|evacuat|vacat|empt)\w*\b[^.]{0,30}\b(site|area|premises|yard|grounds?|building|structure)\b"
                           r"|\b(site|area|premises|yard)\b[^.]{0,30}\b(cleared|evacuated|vacated)\b"),
}
NEGATIVE_VAL = ("alarmed", "uneasy")
REALIZATION_FLOOR = 0.80


def _enact_prompt(aw: dict) -> str:
    aim = ("make your people cautious about it" if aw["aim"] == "caution"
           else "keep your people calm about it")
    stakes = ("you bear the loss if it turns out real" if aw["stakes"] == "high"
              else "you lose nothing if it turns out real; the risk falls on others")
    return (f"You run {aw['institution']}. Word has reached you of {aw['hazard']}; {stakes}. "
            f"You have decided to act as follows: you {aw['action']}. Write the short notice "
            f"(40 to 90 words) you send to your people. Your purpose is to {aim}. State plainly "
            f"what you did with the phrase \"{ACTION_KEYS[aw['action']]}\" (use those exact "
            f"words once), and include one example case of your choosing.")


def _realized_action(text: str) -> str | None:
    low = (text or "").lower()
    hits = [a for a, pat in ACTION_PATTERNS.items() if re.search(pat, low)]
    return hits[0] if len(hits) == 1 else None


# ── A01 ───────────────────────────────────────────────────────────────────────────────

def arm_a01() -> int:
    run = CardRun("A01", "s4_run_a.py")
    maker = run.readers[0] if run.readers else None
    with s4_lib.GpuSession("s4_a01") as gs:
        # pass 1: enactment by the first admitted reader as maker (cached per world)
        enacted = {}
        enact_path = run.out / "enacted.jsonl"
        from soundingline.s4 import append_jsonl, read_jsonl                     # noqa: PLC0415
        for r in read_jsonl(enact_path):
            enacted[r["unit_id"]] = r
        if maker:
            model, tok, _ = s4_lib.load_model(maker)
            try:
                for domain in ("workshop", "civic"):
                    for i, lid in enumerate(run.units(domain)):
                        if lid in enacted:
                            continue
                        run.check_deadline()
                        aw = s4_worlds.make_appraisal_world(lid, domain)
                        prompt = _enact_prompt(aw)
                        rec = {"unit_id": lid, "maker": maker, "attempts": 0, "realized": False,
                               "text": None, "raw_ref": None}
                        for att in range(2):
                            g = s4_lib.generate(model, tok, prompt, seed=SEED + 10 * i + att, max_new=140)
                            rec["attempts"] += 1
                            got = _realized_action(g["text"])
                            ref = run.raw(maker, lid, prompt, g,
                                          validity_reason="ok" if got == aw["action"] else "unrealized",
                                          extra={"attempt": att, "assigned_action": aw["action"], "realized_action": got})
                            if got == aw["action"]:
                                rec.update({"realized": True, "text": g["text"], "raw_ref": ref})
                                break
                        enacted[lid] = rec
                        append_jsonl(enact_path, [rec])
                        run.flush()
            finally:
                s4_lib.free_model(model)
        # pass 2: readers answer the four questions on ruler and enacted sources
        for reader in run.readers:
            model, tok, _ = s4_lib.load_model(reader)
            try:
                for domain in ("workshop", "civic"):
                    for i, lid in enumerate(run.units(domain)):
                        if run.is_done(reader, lid):
                            continue
                        run.check_deadline()
                        aw = s4_worlds.make_appraisal_world(lid, domain)
                        rng = random.Random(SEED + 500 + i)
                        sources = {"ruler": aw["situation"]}
                        en = enacted.get(lid)
                        if en and en["realized"]:
                            sit = aw["situation"].replace(aw["message"], en["text"])
                            sources["enacted"] = sit
                        for src, sit in sources.items():
                            for qname, q in aw["questions"].items():
                                body = f"Situation:\n{sit}\n\nQuestion: {q['question']}"
                                r = s4_lib.likelihood_choice(model, tok, body, q["options"], rng)
                                ls = s4_lib.log_score(r["probs"], q["truth"]) if r["valid"] else None
                                run.row(reader, lid, lid, f"{src}|{qname}",
                                        {"domain": domain, "source": src, "question": qname,
                                         "withheld": aw["withheld"], "stakes": aw["stakes"],
                                         "aim": aw["aim"], "propagandist": aw["propagandist"],
                                         "worried_reassurer": aw["worried_reassurer"]},
                                        q["truth"], "construction" if src == "ruler" else "realized_choice"
                                        if qname == "action" else "construction",
                                        "artifact_plus_context", r, ls,
                                        raw_ref=en["raw_ref"] if src == "enacted" else None,
                                        extra={"correct": (r["valid"] and r["pred"] == q["truth"]),
                                               "valuation": aw["valuation"]})
                        if en and not en["realized"]:
                            run.row(reader, lid, lid, "enacted|unrealized", {"domain": domain, "source": "enacted",
                                    "question": "none"}, None, "construction", "artifact_plus_context", None, None,
                                    realized=False, valid=False, validity_reason="unrealized_enactment")
                        run.L.mark_inspected([lid])
                        run.unit_complete(reader, lid)
            finally:
                s4_lib.free_model(model)
    return _a01_analyze(run, gs.held_s, enacted)


def _balanced_rows(rows):
    """Per-row correctness reweighted so every truth label carries equal total weight:
    the mean over rows equals balanced accuracy, and a constant reader scores 1/K
    whatever the label marginal (the smoke's version averaged raw accuracy, which a
    constant 'unconcerned' answer would have passed at 0.5 on the valuation question)."""
    by_label: dict = {}
    for r in rows:
        by_label.setdefault(r["truth"], []).append(r)
    n, k = len(rows), len(by_label)
    out = []
    for lab, rs in by_label.items():
        w = n / (k * len(rs))
        for r in rs:
            out.append({"unit_id": r["unit_id"], "primary_score": float(r["extra"]["correct"]) * w})
    return out


def _a01_analyze(run: CardRun, gpu_s: float, enacted: dict) -> int:
    rows = [r for r in run.rows() if r["valid"]]
    n_en = sum(1 for e in enacted.values())
    n_real = sum(1 for e in enacted.values() if e["realized"])
    realization = n_real / n_en if n_en else None
    metrics = {"enactment": {"attempted": n_en, "realized": n_real, "yield": realization,
                             "floor": REALIZATION_FLOOR, "usable": (realization or 0) >= REALIZATION_FLOOR}}
    per_q = {}
    for src in ("ruler", "enacted"):
        for q in ("action", "valuation", "audience", "fact"):
            sub = select_rows(rows, source=src, question=q)
            if not sub:
                continue
            preds = [r["pred"] for r in sub]
            truths = [r["truth"] for r in sub]
            labels = sorted(set(truths))
            per_q[f"{src}|{q}"] = {"balanced_accuracy": s4_lib.balanced_accuracy(preds, truths, labels),
                                   "accuracy": sum(p == t for p, t in zip(preds, truths)) / len(sub),
                                   "mean_log_score": sum(r["primary_score"] for r in sub) / len(sub),
                                   "n": len(sub)}
    # primary: balanced accuracy of the valuation and audience-aim questions (ruler
    # source, label-reweighted rows averaged within world) minus the 0.25 floor
    prim_unit: dict = {}
    for q in ("valuation", "audience"):
        for rr in _balanced_rows(select_rows(rows, source="ruler", question=q)):
            prim_unit.setdefault(rr["unit_id"], []).append(rr["primary_score"])
    primary = s4_lib.cluster_bootstrap_ci({u: sum(v) / len(v) - 0.25 for u, v in prim_unit.items()}, SEED + 1)
    strata = {}
    for flag in ("propagandist", "worried_reassurer", "withheld"):
        sub = [r for r in rows if r["factors"].get(flag) and r["factors"]["source"] == "ruler"
               and r["factors"]["question"] in ("valuation", "audience")]
        if sub:
            strata[flag] = {"accuracy": sum(float(r["extra"]["correct"]) for r in sub) / len(sub), "n": len(sub)}
    fact_withheld = [r for r in rows if r["factors"]["withheld"] and r["factors"]["question"] == "fact"
                     and r["factors"]["source"] == "ruler"]
    uncertainty_rate = (sum(1 for r in fact_withheld if r["pred"] == s4_worlds.FACT_STATES[3]) / len(fact_withheld)
                        if fact_withheld else None)
    threshold = run.design.get("thresholds", {}).get("A01", 0.05) or 0.05
    verdict = run.classify(primary, threshold)
    per_reader = {rd: mean_by([r for r in rows if r["model_id"] == rd], ["source", "question"]) for rd in run.readers}
    metrics.update({"per_question": per_q, "primary_valuation_audience_over_floor": primary,
                    "strata": strata, "withheld_uncertainty_rate": uncertainty_rate,
                    "per_reader": per_reader, "cell_counts": cell_counts(run.rows(), ["source", "question"])})
    run.finish(metrics, {"exec": "COMPLETE", "primary": "valuation and audience-aim recovery over 0.25",
                         "enacted_usable": metrics["enactment"]["usable"], **verdict}, gpu_s)
    return 0


# ── A02 ───────────────────────────────────────────────────────────────────────────────

def _load_handle(reader: str):
    p = S4 / "I03" / f"handle_{s4_lib.safe_id(reader)}.json"
    if not p.exists():
        return None
    return read_json(p)


def _situation_evidence(aw: dict, level: str) -> str:
    if level == "low":
        return aw["message"]
    return aw["situation"]


def arm_a02() -> int:
    run = CardRun("A02", "s4_run_a.py")
    a01 = read_json(S4 / "A01" / "verdict.json") if (S4 / "A01" / "verdict.json").exists() else {}
    handles = {}
    with s4_lib.GpuSession("s4_a02") as gs:
        for reader in run.readers:
            h = _load_handle(reader)
            handles[reader] = h.get("verdict") if h else None
            if not h or h.get("verdict") != "ANCHOR-STANDS":
                continue
            dirs, rand_dirs, shuf_dirs = s4_lib.handle_from_json(h)
            alpha = float(h["alpha"])
            locus = [int(b) for b in h["steer_locus"]]
            model, tok, _ = s4_lib.load_model(reader)
            try:
                from contextlib import ExitStack                                  # noqa: PLC0415
                from runners.s3_run_a import additive_steer                       # noqa: PLC0415

                def steered(cond, dose, fn):
                    if cond == "zero":
                        return fn()
                    sign = -1.0 if cond == "neg" else 1.0
                    dset = {"pos": dirs, "neg": dirs, "random": rand_dirs, "shuffled": shuf_dirs}[cond]
                    a = alpha * (0.5 if dose == "low" else 1.0) * sign
                    with ExitStack() as stack:
                        for b in locus:
                            stack.enter_context(additive_steer(model, [b], dset[b], a))
                        return fn()

                for domain in ("workshop", "civic"):
                    for i, lid in enumerate(run.units(domain)):
                        if run.is_done(reader, lid):
                            continue
                        run.check_deadline()
                        # A02 runs on A01's admitted worlds: derived children of A01's lineages
                        a01_lid = run.parent_of(lid)
                        aw = s4_worlds.make_appraisal_world(a01_lid, domain)
                        nq = aw["next_choice"]
                        sign_val = -1.0 if aw["valuation"] in NEGATIVE_VAL else 1.0
                        for ev in ("low", "high"):
                            body = f"Situation:\n{_situation_evidence(aw, ev)}\n\nQuestion: {nq['question']}"
                            zero_ls = None
                            for cond in ("zero", "pos", "neg", "random", "shuffled"):
                                for dose in (("high",) if cond == "zero" else ("low", "high")):
                                    rng = random.Random(SEED + 700 + i)   # same order across conditions
                                    r = steered(cond, dose, lambda: s4_lib.likelihood_choice(model, tok, body, nq["options"], rng))
                                    ls = s4_lib.log_score(r["probs"], nq["truth"]) if r["valid"] else None
                                    if cond == "zero":
                                        zero_ls = ls
                                    # the aligned benefit carries BOTH signs: the steering
                                    # direction's and the target appraisal's, so negative
                                    # steering on a negative-appraisal target counts as aligned
                                    # (the smoke's version signed only by the target)
                                    steer_sign = -1.0 if cond == "neg" else 1.0
                                    delta = (ls - zero_ls) if (ls is not None and zero_ls is not None) else None
                                    run.row(reader, lid, lid, f"{cond}|{dose}|{ev}",
                                            {"domain": domain, "intervention": cond, "dose": dose, "evidence": ev,
                                             "target_negative": sign_val < 0, "truth_option": nq["truth"]},
                                            nq["truth"], "construction", "artifact_plus_context", r, ls,
                                            intervention={"blocks": locus, "alpha": alpha * (0.5 if dose == "low" else 1.0),
                                                          "direction": cond, "positions": "all"} if cond != "zero" else None,
                                            extra={"sign_val": sign_val, "steer_sign": steer_sign,
                                                   "valuation": aw["valuation"], "delta": delta,
                                                   "aligned_benefit": (steer_sign * sign_val * delta) if delta is not None else None,
                                                   "p_truth": r["probs"][nq["truth"]] if r["valid"] else None})
                        # own choice without a target, high dose
                        own_body = (f"You run {aw['institution']}. Word has reached you of {aw['hazard']}. "
                                    f"Which will you do next?")
                        for cond in ("zero", "pos", "neg"):
                            rng = random.Random(SEED + 800 + i)
                            r = steered(cond, "high", lambda: s4_lib.likelihood_choice(model, tok, own_body, nq["options"], rng))
                            run.row(reader, lid, lid, f"own|{cond}", {"domain": domain, "control": "own_choice_no_target",
                                    "intervention": cond}, None, "construction", "artifact_only", r, None,
                                    extra={"probs": r["probs"] if r["valid"] else None})
                        run.L.mark_inspected([lid])
                        run.unit_complete(reader, lid)
            finally:
                s4_lib.free_model(model)
    return _a02_analyze(run, gs.held_s, handles, a01)


def _a02_analyze(run: CardRun, gpu_s: float, handles: dict, a01: dict) -> int:
    rows = [r for r in run.rows() if r["valid"] and r["primary_score"] is not None]
    valid_readers = [r for r, v in handles.items() if v == "ANCHOR-STANDS"]
    if not valid_readers:
        run.finish({"handles": handles},
                   {"exec": "COMPLETE", "outcome": "INSTRUMENT_FAILED",
                    "reason": "no reader's valence handle passed calibration; the bridge was not tested",
                    "manipulation_valid": False}, gpu_s)
        return 0

    # every unit's appraisal sign is its stratum; the aligned benefit is balanced over the
    # two strata so a main effect of steering (which would ride the two-to-one sign
    # imbalance) cancels and only the appraisal-by-intervention interaction remains
    strat = {r["unit_id"]: bool(r["factors"].get("target_negative")) for r in rows
             if "target_negative" in r["factors"]}

    def per_unit(cond, dose, ev, key):
        out: dict = {}
        for r in rows:
            f = r["factors"]
            if (f.get("intervention") == cond and f.get("dose") == dose and f.get("evidence") == ev
                    and r["extra"].get(key) is not None):
                out.setdefault(r["unit_id"], []).append(float(r["extra"][key]))
        return {u: sum(v) / len(v) for u, v in out.items()}

    def aligned(cond, dose, ev, units=None):
        vals = per_unit(cond, dose, ev, "aligned_benefit")
        if units is not None:
            vals = {u: v for u, v in vals.items() if u in units}
        return s4_lib.cluster_bootstrap_ci(s4_lib.stratum_balanced(vals, strat), SEED + 2)

    table = {}
    for cond in ("pos", "neg", "random", "shuffled"):
        for dose in ("low", "high"):
            for ev in ("low", "high"):
                table[f"{cond}|{dose}|{ev}"] = {
                    "aligned_benefit": aligned(cond, dose, ev),
                    "main_effect": s4_lib.cluster_bootstrap_ci(per_unit(cond, dose, ev, "delta"), SEED + 3)}
    primary = table["pos|high|high"]["aligned_benefit"]
    # within-correct-action strata (brief A02: the interaction must survive them)
    strata = {}
    for opt in s4_worlds.NEXT_ACTS:
        units = {r["unit_id"] for r in rows if r["factors"].get("truth_option") == opt}
        strata[opt] = aligned("pos", "high", "high", units) if units else None
    # steering sign pooled: positive and negative steering both scored as aligned benefit
    pooled = {}
    for cond in ("pos", "neg"):
        for u, v in per_unit(cond, "high", "high", "aligned_benefit").items():
            pooled.setdefault(u, []).append(v)
    pooled_ci = s4_lib.cluster_bootstrap_ci(s4_lib.stratum_balanced({u: sum(v) / len(v) for u, v in pooled.items()}, strat), SEED + 5)
    own = [r for r in run.rows() if r["treatment"].startswith("own|") and r["valid"]]
    own_shift = {}
    for cond in ("pos", "neg"):
        diffs = []
        for r in own:
            if r["factors"]["intervention"] == cond:
                base = [b for b in own if b["unit_id"] == r["unit_id"] and b["model_id"] == r["model_id"]
                        and b["factors"]["intervention"] == "zero"]
                if base:
                    diffs.append(sum(abs(r["extra"]["probs"][o] - base[0]["extra"]["probs"][o]) for o in r["extra"]["probs"]) / 2)
        own_shift[cond] = sum(diffs) / len(diffs) if diffs else None
    threshold = run.design.get("thresholds", {}).get("A02", 0.03) or 0.03
    verdict = run.classify(primary, threshold)
    controls_quiet = all(abs(table[f"{c}|high|high"]["aligned_benefit"]["point"] or 0)
                         < max(abs(primary["point"] or 0) / 2, 0.02) for c in ("random", "shuffled"))
    if verdict["outcome"] == "SUPPORT_CANDIDATE" and not controls_quiet:
        verdict["outcome"] = "INCONCLUSIVE"
        verdict["reason"] += "; a control direction moved as much as the fitted one"
    verdict["manipulation_valid"] = True
    verdict["controls_quiet"] = controls_quiet
    run.finish({"handles": handles, "table": table, "primary_aligned_benefit_pos_high_high": primary,
                "aligned_benefit_both_signs_high_high": pooled_ci,
                "strata_by_truth_option": strata, "own_choice_shift": own_shift,
                "sign_balance": {"negative_units": sum(1 for v in strat.values() if v),
                                 "positive_units": sum(1 for v in strat.values() if not v)},
                "a01_enacted_usable": a01.get("enacted_usable"),
                "cell_counts": cell_counts(run.rows(), ["intervention", "dose", "evidence"])},
               {"exec": "COMPLETE", "primary": "appraisal-aligned steering benefit, target log score", **verdict}, gpu_s)
    return 0


# ── A03 ───────────────────────────────────────────────────────────────────────────────

def _token_span(tok, rendered: str, needle: str) -> tuple[int, int] | None:
    start = rendered.find(needle)
    if start < 0:
        return None
    end = start + len(needle)
    enc = tok(rendered, return_offsets_mapping=True, add_special_tokens=False)
    idx = [i for i, (a, b) in enumerate(enc["offset_mapping"]) if b > start and a < end]
    return (idx[0], idx[-1] + 1) if idx else None


def arm_a03() -> int:
    run = CardRun("A03", "s4_run_a.py")
    a02p = S4 / "A02" / "verdict.json"
    a02 = read_json(a02p) if a02p.exists() else {}
    if not a02.get("manipulation_valid") or not verdict_gate(a02p, key="manipulation_valid"):
        run.finish({}, {"exec": "BLOCKED", "outcome": "NOT_RUN",
                        "reason": "BLOCKED_DEPENDENCY: A02 manipulation not valid"}, 0.0)
        return 0
    import torch                                                                  # noqa: PLC0415
    with s4_lib.GpuSession("s4_a03") as gs:
        for reader in run.readers:
            h = _load_handle(reader)
            if not h or h.get("verdict") != "ANCHOR-STANDS":
                continue
            dirs, _, _ = s4_lib.handle_from_json(h)
            alpha = float(h["alpha"])
            locus = [int(b) for b in h["steer_locus"]]
            model, tok, _ = s4_lib.load_model(reader)
            try:
                from contextlib import ExitStack                                  # noqa: PLC0415
                for domain in ("workshop", "civic"):
                    for i, lid in enumerate(run.units(domain)):
                        if run.is_done(reader, lid):
                            continue
                        run.check_deadline()
                        aw = s4_worlds.make_appraisal_world(run.parent_of(lid), domain)
                        nq = aw["next_choice"]
                        sign_val = -1.0 if aw["valuation"] in NEGATIVE_VAL else 1.0
                        neutral = s4_worlds.render_irrelevant(s4_worlds.make_world(f"A03neutral|{lid}", domain),
                                                              random.Random(SEED + i))
                        body = f"Background: {neutral}\n\nSituation:\n{aw['situation']}\n\nQuestion: {nq['question']}"
                        rng0 = random.Random(SEED + 900 + i)
                        order, labels, listing = s4_lib.build_listing(nq["options"], rng0)
                        user = f"{body}\nOptions:\n{listing}\nAnswer with the letter only."
                        rendered = tok.apply_chat_template([{"role": "user", "content": user}],
                                                           add_generation_prompt=True, tokenize=False)
                        rendered += "Answer:"
                        ctx_span = _token_span(tok, rendered, aw["situation"])
                        neu_span = _token_span(tok, rendered, neutral)
                        n_tok = len(tok(rendered, add_special_tokens=False).input_ids)
                        if not ctx_span or not neu_span:
                            run.row(reader, lid, lid, "span_missing", {"domain": domain}, None, "construction",
                                    "artifact_plus_context", None, None, valid=False, validity_reason="span_not_found")
                            run.unit_complete(reader, lid)
                            continue
                        k = min(ctx_span[1] - ctx_span[0], neu_span[1] - neu_span[0], 32)
                        spans = {"context": (ctx_span[1] - k, ctx_span[1]),
                                 "answer": (n_tok - k, n_tok),
                                 "neutral": (neu_span[1] - k, neu_span[1])}
                        lab_ids = s4_lib.label_token_ids(tok)
                        full = torch.tensor([tok(rendered, add_special_tokens=False).input_ids]).to("cuda")

                        def read(sign, span):
                            with ExitStack() as stack:
                                if span is not None:
                                    for b in locus:
                                        stack.enter_context(s4_lib.steer_positions(model, [b], dirs[b], sign * alpha, span[0], span[1]))
                                with torch.no_grad():
                                    logits = model(full).logits[0, -1].float()
                            lps = torch.log_softmax(logits, dim=-1)
                            raw = {kk: float(lps[lab_ids[labels[kk]]["id"]]) for kk in order}
                            m = max(raw.values())
                            import math                                           # noqa: PLC0415
                            z = sum(math.exp(v - m) for v in raw.values())
                            probs = {kk: math.exp(raw[kk] - m) / z for kk in order}
                            return {"valid": True, "validity_reason": "ok", "order": order, "labels": labels,
                                    "probs": probs, "pred": max(probs, key=probs.get)}

                        base = read(0.0, None)
                        ls0 = s4_lib.log_score(base["probs"], nq["truth"])
                        run.row(reader, lid, lid, "zero", {"domain": domain, "phase": "none", "sign": "zero"},
                                nq["truth"], "construction", "artifact_plus_context", base, ls0)
                        for phase, span in spans.items():
                            for sgn_name, sgn in (("pos", 1.0), ("neg", -1.0)):
                                r = read(sgn, span)
                                ls = s4_lib.log_score(r["probs"], nq["truth"])
                                run.row(reader, lid, lid, f"{phase}|{sgn_name}", {"domain": domain, "phase": phase, "sign": sgn_name},
                                        nq["truth"], "construction", "artifact_plus_context", r, ls,
                                        intervention={"blocks": locus, "alpha": alpha, "positions": list(span),
                                                      "n_positions": k, "cached_kv_reused": False},
                                        extra={"aligned_benefit": sign_val * sgn * (ls - ls0), "sign_val": sign_val})
                        run.L.mark_inspected([lid])
                        run.unit_complete(reader, lid)
            finally:
                s4_lib.free_model(model)
    return _a03_analyze(run, gs.held_s)


def _a03_analyze(run: CardRun, gpu_s: float) -> int:
    rows = [r for r in run.rows() if r["valid"] and r["treatment"] != "zero"]
    # both steering signs enter (the aligned benefit already carries the sign product),
    # averaged within unit and reader; strata by appraisal sign are balanced as in A02
    strat = {r["unit_id"]: r["extra"]["sign_val"] < 0 for r in rows if "sign_val" in r["extra"]}

    def per_unit(phase):
        vals: dict = {}
        for r in rows:
            if r["factors"]["phase"] == phase and r["extra"].get("aligned_benefit") is not None:
                vals.setdefault(r["unit_id"], []).append(float(r["extra"]["aligned_benefit"]))
        return {u: sum(v) / len(v) for u, v in vals.items()}

    per_phase = {phase: s4_lib.cluster_bootstrap_ci(s4_lib.stratum_balanced(per_unit(phase), strat), SEED + 5)
                 for phase in ("context", "answer", "neutral")}
    ctx, ans = per_unit("context"), per_unit("answer")
    diff = {u: ctx[u] - ans[u] for u in ctx if u in ans}
    primary = s4_lib.cluster_bootstrap_ci(s4_lib.stratum_balanced(diff, strat), SEED + 6)
    threshold = run.design.get("thresholds", {}).get("A03", 0.03) or 0.03
    verdict = run.classify(primary, threshold)
    run.finish({"per_phase_aligned_benefit": per_phase, "primary_context_minus_answer": primary,
                "cell_counts": cell_counts(run.rows(), ["phase", "sign"])},
               {"exec": "COMPLETE", "primary": "context-phase minus answer-phase aligned benefit", **verdict}, gpu_s)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--card", required=True, choices=["A01", "A02", "A03"])
    a = ap.parse_args()
    try:
        return {"A01": arm_a01, "A02": arm_a02, "A03": arm_a03}[a.card]()
    except DeadlineReached:
        print(f"{a.card}: deadline reached; rows checkpointed")
        return 3


if __name__ == "__main__":
    sys.exit(main())
