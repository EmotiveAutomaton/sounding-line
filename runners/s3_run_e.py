"""Stage 3 Trunk E runners: E01 self-policy profiles, E02 route ruler (the E-trunk
known-positive gate), E03 similarity x route factorial. Cards E24-S3-E01..E03.

DESIGN CHECK (2026-08-24). Lessons applied: E02 is the known-answer gate and runs BEFORE
any similarity factorial spends GPU (L139 — known-positive before signal); targets are
programmatic makers whose profiles are known exactly, so the gate has ground truth; the
prediction readout is mechanical anchor extraction (accept-time realization, L156);
compute-matched deliberation control included so "records help" is not "more tokens help";
the exact Bayes posterior is reported beside every route as the ceiling; per-route CELLS
are reported beside contrasts (L168 — averages hid a head-to-head flip); failure direction
declared: if records-aware does not beat target-only on known-policy targets, the route
instrument cannot support E03/E04 and the cell is INSTRUMENT_FAILED.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from runners.s3_lib import (AXES, PROFILE_W, bayes_profile_posterior, chat_gen,   # noqa: E402
                            choice_probs, episode_prompt, hash_stable, perm_p,
                            realized_choice, scenarios, utilities)
from soundingline.s3 import S3, set_status                                        # noqa: E402

SEED0 = 30000
READERS = ["Qwen/Qwen2.5-1.5B-Instruct", "HuggingFaceTB/SmolLM2-1.7B-Instruct"]
OUT_E = S3 / "E"


def _load(mk):
    import torch                                                                  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                  # noqa: PLC0415
    tok = AutoTokenizer.from_pretrained(mk)
    model = AutoModelForCausalLM.from_pretrained(
        mk, dtype=torch.float16).to("cuda").eval()
    return model, tok


def _free(model):
    import torch                                                                  # noqa: PLC0415
    del model
    torch.cuda.empty_cache()


def target_history(profile: str, k: int, seed: int, domain: str, holdout: int):
    """k past choices of a known-profile programmatic maker, avoiding the held-out
    scenario. Returns (scen_ids, choices) using the maker's argmax under seed-1 utilities."""
    rng = random.Random(SEED0 + seed)
    pool = [i for i in range(len(scenarios(domain))) if i != holdout]
    sids = [rng.choice(pool) for _ in range(k)]
    chs = []
    for si in sids:
        probs = choice_probs(utilities(si, 1, domain), PROFILE_W[profile])
        chs.append(AXES[max(range(4), key=lambda j: probs[j])])
    return sids, chs


def history_block(sids, chs, domain: str) -> str:
    lines = []
    for si, ch in zip(sids, chs):
        ctx, _, opts = scenarios(domain)[si]
        lines.append(f"- Faced with: {ctx} They chose the {opts[ch]}.")
    return "\n".join(lines)


def predict_prompt(route: str, profile: str, holdout: int, domain: str,
                   seed: int) -> str:
    ctx, _, opts = scenarios(domain)[holdout]
    letters = dict(zip("ABCD", AXES))
    body = "\n".join(f"{letter}) the {opts[ax]}" for letter, ax in letters.items())
    task = (f"\nNow this maker faces a new decision: {ctx}\nOptions:\n{body}\n"
            f"Predict which option this maker will choose. Answer in one or two "
            f"sentences that work the chosen option's full key phrase into your text, "
            f"and no other option's key phrase.\n\nPrediction:")
    if route == "records":
        sids, chs = target_history(profile, 8, seed, domain, holdout)
        return ("You are predicting the behavior of a decision-maker. Here is their "
                "documented choice record:\n" + history_block(sids, chs, domain) + task)
    if route == "target_only":
        return ("You are predicting the behavior of a decision-maker you have no "
                "records for." + task)
    if route == "generic":
        # compute-matched: same token budget of text, zero target information
        sids, _ = target_history(profile, 8, seed, domain, holdout)
        filler = "\n".join(
            f"- A committee once faced: {scenarios(domain)[si][0]} Deliberation "
            f"weighed all four options carefully." for si in sids)
        return ("You are predicting the behavior of a decision-maker. Here are notes "
                "from unrelated committees:\n" + filler + task)
    if route == "self_first":
        sids, chs = target_history(profile, 8, seed, domain, holdout)
        return ("First: faced with the decision below, state in one sentence which "
                "option YOU would choose. Then read the maker's documented record:\n"
                + history_block(sids, chs, domain)
                + "\nSecond: adjust for how the maker differs from you." + task)
    raise ValueError(route)


def arm_e02() -> int:
    """Route ruler on known-policy targets. Four routes x 4 profiles x 12 held-out
    scenarios x 2 readers. Records-aware must beat target-only; else INSTRUMENT_FAILED."""
    cell = "E24-S3-E02"
    t0 = time.time()
    out = OUT_E / "E02"
    out.mkdir(parents=True, exist_ok=True)
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415

    routes = ("records", "target_only", "generic", "self_first")
    domain = "infra"
    rows = []      # (reader, route, profile, holdout, predicted, truth, correct)
    ceiling_hits = 0
    ceiling_n = 0
    acquire_gpu_lock("s3_e02")
    try:
        for mk in READERS:
            model, tok = _load(mk)
            short = mk.split("/")[-1]
            for profile in AXES:
                for holdout in range(12):
                    probs = choice_probs(utilities(holdout, 1, domain),
                                         PROFILE_W[profile])
                    truth = AXES[max(range(4), key=lambda j: probs[j])]
                    if mk == READERS[0]:
                        # exact Bayes ceiling, once per (profile, holdout)
                        sids, chs = target_history(profile, 8, holdout, domain, holdout)
                        post = bayes_profile_posterior(chs, sids, 1, domain)
                        best_prof = max(post, key=post.get)
                        bp = choice_probs(utilities(holdout, 1, domain),
                                          PROFILE_W[best_prof])
                        ceiling_hits += AXES[max(range(4), key=lambda j: bp[j])] == truth
                        ceiling_n += 1
                    for route in routes:
                        dest = out / f"p_{short[:8]}_{route}_{profile}_{holdout}.json"
                        if dest.exists():
                            rows.append(tuple(json.loads(
                                dest.read_text(encoding="utf-8"))))
                            continue
                        prompt = predict_prompt(route, profile, holdout, domain,
                                                holdout)
                        pred = None
                        for att in range(4):
                            txt = chat_gen(model, tok, prompt,
                                           SEED0 + hash_stable(dest.name) % 9999
                                           + att, max_new=180)
                            pred = realized_choice(txt, holdout, domain)
                            if pred is not None:
                                break
                        row = (short, route, profile, holdout, pred, truth,
                               int(pred == truth))
                        dest.write_text(json.dumps(row), encoding="utf-8",
                                        newline="\n")
                        rows.append(row)
            _free(model)
    finally:
        release_gpu_lock()

    # per-route accuracy, cells beside contrasts
    acc = {}
    for r in ("records", "target_only", "generic", "self_first"):
        sub = [x for x in rows if x[1] == r]
        realized = [x for x in sub if x[4] is not None]
        acc[r] = {"n": len(sub), "realized": len(realized),
                  "acc": (sum(x[6] for x in realized) / len(realized))
                  if realized else None,
                  "per_reader": {mk.split("/")[-1]: (
                      lambda s: sum(x[6] for x in s) / len(s) if s else None)(
                      [x for x in realized if x[0] == mk.split("/")[-1]])
                      for mk in READERS}}
    # paired sign-flip: records vs target_only on shared (reader, profile, holdout)
    by_key = {}
    for x in rows:
        if x[4] is not None:
            by_key.setdefault((x[0], x[2], x[3]), {})[x[1]] = x[6]
    diffs = [v["records"] - v["target_only"] for v in by_key.values()
             if "records" in v and "target_only" in v]
    obs, p = perm_p(diffs, SEED0) if diffs else (None, None)
    gate_pass = (acc["records"]["acc"] or 0) > (acc["target_only"]["acc"] or 1) and \
                (acc["records"]["acc"] or 0) > (acc["generic"]["acc"] or 1)
    (out / "gate.json").write_text(json.dumps(
        {"cell": cell, "gate_pass": gate_pass, "route_accuracy": acc,
         "bayes_ceiling": ceiling_hits / ceiling_n if ceiling_n else None,
         "records_minus_targetonly": obs, "perm_p": p, "perm_seed": SEED0,
         "n_paired": len(diffs)}, indent=1), encoding="utf-8", newline="\n")
    set_status(cell, "LANDED" if gate_pass else "INSTRUMENT_FAILED",
               closure_reason=None if gate_pass else
               "records-aware route failed to beat target-only on known-policy targets",
               actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"E02 gate_pass={gate_pass}; acc={ {k: v['acc'] for k, v in acc.items()} }; "
          f"ceiling={ceiling_hits}/{ceiling_n}; p={p}")
    return 0


def arm_e01() -> int:
    """Self-policy profiles: each reader answers episodes with NO policy line; the exact
    posterior over axis profiles from its realized choices is its self-policy. Stability:
    split-half top-profile agreement and a paraphrased frame."""
    cell = "E24-S3-E01"
    t0 = time.time()
    out = OUT_E / "E01"
    out.mkdir(parents=True, exist_ok=True)
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415
    rng = random.Random(SEED0 + 1)

    report = {}
    acquire_gpu_lock("s3_e01")
    try:
        for mk in READERS + ["HuggingFaceTB/SmolLM2-360M-Instruct"]:
            model, tok = _load(mk)
            short = mk.split("/")[-1]
            report[short] = {}
            for domain in ("infra", "process"):
                for frame in ("plain", "paraphrase"):
                    recs = []
                    for j in range(40):
                        si = rng.randrange(len(scenarios(domain)))
                        dest = out / f"c_{short[:12]}_{domain}_{frame}_{j}.json"
                        if dest.exists():
                            recs.append(json.loads(dest.read_text(encoding="utf-8")))
                            continue
                        prompt = episode_prompt(si, domain)
                        if frame == "paraphrase":
                            prompt = prompt.replace(
                                "Write a short recommendation",
                                "Draft a brief memo").replace(
                                "committing to exactly one option",
                                "settling firmly on a single option")
                        ch = None
                        for att in range(4):
                            txt = chat_gen(model, tok, prompt,
                                           SEED0 + j * 31 + att)
                            ch = realized_choice(txt, si, domain)
                            if ch is not None:
                                break
                        rec = {"si": si, "ch": ch}
                        dest.write_text(json.dumps(rec), encoding="utf-8",
                                        newline="\n")
                        recs.append(rec)
                    good = [r for r in recs if r["ch"] is not None]
                    post = bayes_profile_posterior([r["ch"] for r in good],
                                                   [r["si"] for r in good], 1,
                                                   domain) if good else None
                    halves = (good[0::2], good[1::2])
                    tops = []
                    for h in halves:
                        if h:
                            ph = bayes_profile_posterior([r["ch"] for r in h],
                                                         [r["si"] for r in h], 1,
                                                         domain)
                            tops.append(max(ph, key=ph.get))
                    report[short][f"{domain}|{frame}"] = {
                        "n": len(recs), "realized": len(good),
                        "posterior": post,
                        "top": max(post, key=post.get) if post else None,
                        "split_half_agree": (len(tops) == 2 and tops[0] == tops[1]),
                    }
            _free(model)
    finally:
        release_gpu_lock()

    e01_analyze(report, out, cell)
    set_status(cell, "LANDED", actual_gpu_minutes=(time.time() - t0) / 60)
    return 0


E01_MIN_YIELD = 0.75


def e01_analyze(report, out, cell="E24-S3-E01") -> dict:
    """Realization-gated stability verdict. A cell counts only if at least 75 percent
    of its 40 episodes realized (audit 2026-08-24: the Qwen paraphrase frame realized
    1/40 and 0/40 and its posterior was being compared anyway)."""
    stability = {}
    for short, cells_ in report.items():
        per_domain = {}
        for domain in ("infra", "process"):
            cp = cells_.get(f"{domain}|plain", {})
            cq = cells_.get(f"{domain}|paraphrase", {})
            def valid(c):
                return c.get("n", 0) > 0 and c.get("realized", 0) / c["n"] >= E01_MIN_YIELD
            vp, vq = valid(cp), valid(cq)
            per_domain[domain] = {
                "plain": cp.get("top") if vp else None,
                "plain_yield": (cp.get("realized", 0) / cp["n"]) if cp.get("n") else None,
                "paraphrase": cq.get("top") if vq else None,
                "paraphrase_yield": (cq.get("realized", 0) / cq["n"]) if cq.get("n") else None,
                "frame_stable": (cp.get("top") == cq.get("top")) if (vp and vq) else None,
                "note": None if (vp and vq) else
                "instrument: a frame realized under 75 percent; stability undetermined"}
        stability[short] = per_domain
    (out / "profiles.json").write_text(json.dumps(
        {"cell": cell, "min_cell_yield": E01_MIN_YIELD, "stability": stability,
         "detail": report}, indent=1), encoding="utf-8", newline="\n")
    print(f"E01 analysis: {json.dumps(stability)}")
    return stability


def arm_e01_analyze() -> int:
    """Re-run the E01 analysis from cached episode files, no GPU."""
    out = OUT_E / "E01"
    report = {}
    for mk in READERS + ["HuggingFaceTB/SmolLM2-360M-Instruct"]:
        short = mk.split("/")[-1]
        report[short] = {}
        for domain in ("infra", "process"):
            for frame in ("plain", "paraphrase"):
                recs = []
                for j in range(40):
                    p2 = out / f"c_{short[:12]}_{domain}_{frame}_{j}.json"
                    if p2.exists():
                        recs.append(json.loads(p2.read_text(encoding="utf-8")))
                good = [r for r in recs if r["ch"] is not None]
                post = bayes_profile_posterior([r["ch"] for r in good],
                                               [r["si"] for r in good], 1,
                                               domain) if good else None
                report[short][f"{domain}|{frame}"] = {
                    "n": len(recs), "realized": len(good), "posterior": post,
                    "top": max(post, key=post.get) if post else None}
    e01_analyze(report, out)
    return 0


# ── E03: similarity x route factorial (card E24-S3-E03) ─────────────────────────────
# The question in plain language: is another mind easier to read the more it is like
# you? Targets at three similarity levels — the reader ITSELF as maker, the other
# instruct family, and a programmatic maker — crossed with the E02-validated routes.
# DESIGN CHECK: runs only behind the E02 gate (the queue's needs enforces it, L139);
# truth for model targets is the target's OWN realized held-out choice, generated
# accept-time, not the environment argmax (the similarity question is about the actual
# maker, L156); routes include target_only as the in-design floor; per-cell accuracy
# beside the contrast (L168); histories cached once per (target, policy).

OUT_E03 = OUT_E / "E03"
E03_HIST_SIDS = list(range(8))
E03_HOLDOUTS = [8, 9, 10, 11]
E03_DOMAIN = "infra"


def _model_history(model, tok, mk_tag: str, policy: str):
    """8 realized policy-prompted choices on the history scenarios, cached."""
    from runners.s3_lib import POLICY_LINES, episode_prompt                       # noqa: PLC0415
    dest = OUT_E03 / f"hist_{mk_tag}_{policy}.json"
    if dest.exists():
        return json.loads(dest.read_text(encoding="utf-8"))
    out = []
    for si in E03_HIST_SIDS:
        ch = None
        for att in range(5):
            txt = chat_gen(model, tok,
                           episode_prompt(si, E03_DOMAIN, POLICY_LINES[policy]),
                           SEED0 + 900 + si * 16 + att)
            ch = realized_choice(txt, si, E03_DOMAIN)
            if ch is not None:
                break
        out.append({"si": si, "ch": ch})
    dest.write_text(json.dumps(out), encoding="utf-8", newline="\n")
    return out


def _model_truth(model, tok, mk_tag: str, policy: str, holdout: int,
                 draw: int = 0):
    """One realized draw of the target's own choice. draw=1 is the independent
    second draw for the self-consistency ceiling (audit: a stochastic maker's single
    draw is a noisy truth; the ceiling is how often two draws agree)."""
    from runners.s3_lib import POLICY_LINES, episode_prompt                       # noqa: PLC0415
    tag = "" if draw == 0 else f"_d{draw}"
    dest = OUT_E03 / f"truth_{mk_tag}_{policy}_{holdout}{tag}.json"
    if dest.exists():
        return json.loads(dest.read_text(encoding="utf-8"))["ch"]
    ch = None
    for att in range(5):
        txt = chat_gen(model, tok,
                       episode_prompt(holdout, E03_DOMAIN, POLICY_LINES[policy]),
                       SEED0 + 1300 + draw * 777 + holdout * 16 + att)
        ch = realized_choice(txt, holdout, E03_DOMAIN)
        if ch is not None:
            break
    dest.write_text(json.dumps({"ch": ch}), encoding="utf-8", newline="\n")
    return ch


def _e03_predict_prompt(route: str, hist, holdout: int) -> str:
    ctx, _, opts = scenarios(E03_DOMAIN)[holdout]
    letters = dict(zip("ABCD", AXES))
    body = "\n".join(f"{letter}) the {opts[ax]}"
                      for letter, ax in letters.items())
    task = (f"\nNow this maker faces a new decision: {ctx}\nOptions:\n{body}\n"
            f"Predict which option this maker will choose. Answer in one or two "
            f"sentences that work the chosen option's full key phrase into your "
            f"text, and no other option's key phrase.\n\nPrediction:")
    hb = history_block([h["si"] for h in hist if h["ch"]],
                       [h["ch"] for h in hist if h["ch"]], E03_DOMAIN)
    if route == "records":
        return ("You are predicting the behavior of a decision-maker. Here is "
                "their documented choice record:\n" + hb + task)
    if route == "target_only":
        return ("You are predicting the behavior of a decision-maker you have no "
                "records for." + task)
    if route == "self_first":
        return ("First: faced with the decision below, state in one sentence which "
                "option YOU would choose. Then read the maker's documented "
                "record:\n" + hb
                + "\nSecond: adjust for how the maker differs from you." + task)
    raise ValueError(route)


def arm_e03() -> int:
    cell = "E24-S3-E03"
    t0 = time.time()
    OUT_E03.mkdir(parents=True, exist_ok=True)
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415
    from runners.s3_lib import perm_p                                             # noqa: PLC0415
    routes = ("records", "target_only", "self_first")
    tags = {mk: mk.split("/")[-1][:12] for mk in READERS}
    rows = []
    acquire_gpu_lock("s3_e03")
    try:
        # 1) target-side generation: histories and truths for both model makers
        models = {}
        for mk in READERS:
            models[mk] = _load(mk)
        hists, truths, truths2 = {}, {}, {}
        for mk in READERS:
            model, tok = models[mk]
            for pol in AXES:
                hists[(tags[mk], pol)] = _model_history(model, tok, tags[mk], pol)
                for ho in E03_HOLDOUTS:
                    truths[(tags[mk], pol, ho)] = _model_truth(
                        model, tok, tags[mk], pol, ho)
                    truths2[(tags[mk], pol, ho)] = _model_truth(
                        model, tok, tags[mk], pol, ho, draw=1)
        # programmatic target: argmax history and truth
        from runners.s3_lib import choice_probs, utilities, PROFILE_W             # noqa: PLC0415
        for pol in AXES:
            hists[("prog", pol)] = [
                {"si": si, "ch": AXES[max(range(4), key=lambda j: choice_probs(
                    utilities(si, 1, E03_DOMAIN), PROFILE_W[pol])[j])]}
                for si in E03_HIST_SIDS]
            for ho in E03_HOLDOUTS:
                truths[("prog", pol, ho)] = AXES[max(range(4), key=lambda j:
                    choice_probs(utilities(ho, 1, E03_DOMAIN),
                                 PROFILE_W[pol])[j])]
        # 2) reader-side prediction over the full factorial
        for mk in READERS:
            model, tok = models[mk]
            rtag = tags[mk]
            for tgt_tag in list(tags.values()) + ["prog"]:
                sim = ("self" if tgt_tag == rtag else
                       "prog" if tgt_tag == "prog" else "other_family")
                for pol in AXES:
                    for ho in E03_HOLDOUTS:
                        truth = truths[(tgt_tag, pol, ho)]
                        if truth is None:
                            continue
                        for route in routes:
                            dest = OUT_E03 / (f"p_{rtag}_{tgt_tag}_{pol}_"
                                              f"{ho}_{route}.json")
                            if dest.exists():
                                rows.append(json.loads(
                                    dest.read_text(encoding="utf-8")))
                                continue
                            pred = None
                            for att in range(4):
                                txt = chat_gen(
                                    model, tok,
                                    _e03_predict_prompt(
                                        route, hists[(tgt_tag, pol)], ho),
                                    SEED0 + 1700
                                    + hash_stable(dest.name) % 9999 + att,
                                    max_new=180)
                                pred = realized_choice(txt, ho, E03_DOMAIN)
                                if pred is not None:
                                    break
                            row = {"reader": rtag, "target": tgt_tag,
                                   "similarity": sim, "policy": pol,
                                   "holdout": ho, "route": route,
                                   "pred": pred, "truth": truth,
                                   "correct": int(pred == truth)}
                            dest.write_text(json.dumps(row), encoding="utf-8",
                                            newline="\n")
                            rows.append(row)
        for mk in READERS:
            _free(models[mk][0])
    finally:
        release_gpu_lock()

    realized = [r for r in rows if r["pred"] is not None]
    cells = {}
    for sim in ("self", "other_family", "prog"):
        for route in routes:
            sub = [r for r in realized if r["similarity"] == sim
                   and r["route"] == route]
            cells[f"{sim}|{route}"] = {
                "n": len(sub),
                "acc": sum(r["correct"] for r in sub) / len(sub) if sub else None}
    per_reader = {}
    for rtag in tags.values():
        for sim in ("self", "other_family", "prog"):
            for route in routes:
                sub = [r for r in realized if r["reader"] == rtag
                       and r["similarity"] == sim and r["route"] == route]
                per_reader[f"{rtag}|{sim}|{route}"] = {
                    "n": len(sub),
                    "acc": sum(r["correct"] for r in sub) / len(sub)
                    if sub else None}
    # self-consistency ceiling for model targets: two independent truth draws
    agree = [int(truths[k] == truths2[k]) for k in truths
             if k[0] != "prog" and truths[k] is not None
             and truths2.get(k) is not None]
    consistency_ceiling = sum(agree) / len(agree) if agree else None
    # similarity contrast on the records route: self vs other_family, paired by
    # (reader-policy-holdout) where both cells realized
    by_key = {}
    for r in realized:
        if r["route"] == "records" and r["similarity"] in ("self", "other_family"):
            by_key.setdefault((r["reader"], r["policy"], r["holdout"]),
                              {})[r["similarity"]] = r["correct"]
    diffs = [v["self"] - v["other_family"] for v in by_key.values()
             if len(v) == 2]
    obs, p = perm_p(diffs, SEED0 + 6) if diffs else (None, None)
    (OUT_E03 / "verdict.json").write_text(json.dumps(
        {"cell": cell, "cells": cells, "per_reader_cells": per_reader,
         "model_target_consistency_ceiling": consistency_ceiling,
         "self_minus_other_on_records": obs, "perm_p": p,
         "perm_seed": SEED0 + 6, "n_paired": len(diffs),
         "yield": len(realized) / len(rows) if rows else 0}, indent=1),
        encoding="utf-8", newline="\n")
    set_status(cell, "LANDED", actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"E03 landed: cells "
          f"{json.dumps({k: v['acc'] for k, v in cells.items()})}; "
          f"self-other {obs} (p={p})")
    return 0


# ── E04: conflict and correction (card E24-S3-E04) ──────────────────────────────────
# The question in plain language: when the target's record points AWAY from what the
# reader itself would choose, do the reader's errors lean toward its own preference —
# self-projection intruding on evidence? Uses each reader's E01 self-profile; targets
# are programmatic makers whose profile is the reader-self-profile's rival; every item
# has three distinguished options: the record's answer, the reader's own-profile answer,
# and two others. Error DIRECTION is the measurement.
# DESIGN CHECK: needs E01 (self profiles) and E02 (route gate) — queue-enforced;
# items constructed so record-answer differs from self-answer (else no conflict);
# mechanical readout; the null is symmetric errors (permutation over error directions);
# cells per reader (L168).

def arm_e04() -> int:
    cell = "E24-S3-E04"
    t0 = time.time()
    out = OUT_E / "E04"
    out.mkdir(parents=True, exist_ok=True)
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415
    from runners.s3_lib import choice_probs, utilities, PROFILE_W                 # noqa: PLC0415
    prof_path = OUT_E / "E01" / "profiles.json"
    profs = json.loads(prof_path.read_text(encoding="utf-8"))["stability"]
    domain = "infra"
    rows = []
    acquire_gpu_lock("s3_e04")
    try:
        for mk in READERS:
            shortname = mk.split("/")[-1]
            self_prof = profs.get(shortname, {}).get(domain, {}).get("plain")
            if self_prof is None:
                continue
            target_prof = {"robust": "cheap", "cheap": "fast", "fast": "precedent",
                           "precedent": "robust"}[self_prof]
            model, tok = _load(mk)
            for holdout in range(12):
              for hseed in range(3):      # three independent record draws per holdout
                def amax(prof, si=holdout):
                    pr = choice_probs(utilities(si, 1, domain), PROFILE_W[prof])
                    return AXES[max(range(4), key=lambda j: pr[j])]
                rec_ans = amax(target_prof)
                self_ans = amax(self_prof)
                if rec_ans == self_ans:
                    continue
                dest = out / f"r_{shortname[:12]}_{holdout}_h{hseed}.json"
                if dest.exists():
                    rows.append(json.loads(dest.read_text(encoding="utf-8")))
                    continue
                prompt = predict_prompt("records", target_prof, holdout, domain,
                                        holdout + 100 * hseed)
                pred = None
                for att in range(4):
                    txt = chat_gen(model, tok, prompt,
                                   SEED0 + 2500 + holdout * 16 + hseed * 4096 + att,
                                   max_new=180)
                    pred = realized_choice(txt, holdout, domain)
                    if pred is not None:
                        break
                row = {"reader": shortname, "self_prof": self_prof,
                       "target_prof": target_prof, "holdout": holdout,
                       "hseed": hseed,
                       "pred": pred, "rec_ans": rec_ans, "self_ans": self_ans,
                       "outcome": ("correct" if pred == rec_ans else
                                   "self_intrusion" if pred == self_ans else
                                   "other_error" if pred else "unrealized")}
                dest.write_text(json.dumps(row), encoding="utf-8", newline="\n")
                rows.append(row)
            _free(model)
    finally:
        release_gpu_lock()
    cells = {}
    for mk in READERS:
        shortname = mk.split("/")[-1]
        sub = [r for r in rows if r["reader"] == shortname]
        n_err = sum(1 for r in sub if r["outcome"] in ("self_intrusion",
                                                       "other_error"))
        cells[shortname] = {
            "n": len(sub),
            "correct": sum(1 for r in sub if r["outcome"] == "correct"),
            "self_intrusion": sum(1 for r in sub
                                  if r["outcome"] == "self_intrusion"),
            "other_error": sum(1 for r in sub if r["outcome"] == "other_error"),
            "intrusion_share_of_errors": (
                sum(1 for r in sub if r["outcome"] == "self_intrusion") / n_err
                if n_err else None),
            "symmetric_null_share": 1 / 3}
    (out / "verdict.json").write_text(json.dumps(
        {"cell": cell, "cells": cells,
         "note": "errors could land on 3 non-record options; self option is 1 of "
                 "3, so intrusion share above 1/3 = projection pull"}, indent=1),
        encoding="utf-8", newline="\n")
    set_status(cell, "LANDED", actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"E04 landed: {json.dumps(cells)}")
    return 0


# ── E05: active probing (card E24-S3-E05) ───────────────────────────────────────────
# The question in plain language: offered one more record to inspect, does the reader
# pick the record that would teach it MORE — the scenario with the higher exact
# expected information gain about the maker's profile — over the one that teaches
# less? (Audit 2026-08-24: the first design's "uninformative scenario" cannot exist in
# this environment — every profile's argmax is its own option everywhere — so the
# known answer is now graded EIG, computed exactly from the environment likelihood.)
# DESIGN CHECK: EIG exact per offer given the shown history; offers are the max-EIG
# and min-EIG scenarios, and the pair is kept only when their EIG ratio exceeds 1.5
# so the known answer is not a coin flip; ambiguous 1-1 histories by construction;
# mechanical readout by unique 20-char context key; counterbalanced presentation;
# per-reader cells with yield (L168).

def eig_of_offer(h_sids, h_chs, offer_si, domain="infra"):
    """Expected reduction in posterior entropy over the four profiles from seeing the
    maker's choice on offer_si, under the environment's own likelihood."""
    import math                                                                   # noqa: PLC0415
    post = bayes_profile_posterior(h_chs, h_sids, 1, domain)
    def H(p):
        return -sum(v * math.log(v) for v in p.values() if v > 1e-12)
    h0 = H(post)
    U = utilities(offer_si, 1, domain)
    pred = {ax: sum(post[pf] * choice_probs(U, PROFILE_W[pf])[AXES.index(ax)]
                    for pf in AXES) for ax in AXES}
    h1 = 0.0
    for ax in AXES:
        if pred[ax] <= 1e-12:
            continue
        p2 = bayes_profile_posterior(h_chs + [ax], h_sids + [offer_si], 1, domain)
        h1 += pred[ax] * H(p2)
    return h0 - h1


def e05_items():
    import random as _r                                                          # noqa: PLC0415
    domain = "infra"
    rivals = {"robust": "cheap", "cheap": "fast", "fast": "precedent",
              "precedent": "robust"}

    def amax(si, prof):
        pr = choice_probs(utilities(si, 1, domain), PROFILE_W[prof])
        return AXES[max(range(4), key=lambda j: pr[j])]

    items = []
    for p_prof in AXES:
        q_prof = rivals[p_prof]
        for rep_i in range(8):
            rng = _r.Random(SEED0 + 4000 + hash_stable(f"{p_prof}|{rep_i}"))
            s1, s2 = rng.sample(range(12), 2)
            h_sids = [s1, s2]
            h_chs = [amax(s1, p_prof), amax(s2, q_prof)]     # 1-1 ambiguous
            pool = [x for x in range(12) if x not in (s1, s2)]
            eigs = {si: eig_of_offer(h_sids, h_chs, si, domain) for si in pool}
            hi = max(eigs, key=eigs.get)
            lo = min(eigs, key=eigs.get)
            if eigs[lo] <= 0 or eigs[hi] / eigs[lo] < 1.5:
                continue
            items.append({"p": p_prof, "q": q_prof, "h_sids": h_sids,
                          "h_chs": h_chs, "offer_hi": hi, "offer_lo": lo,
                          "eig_hi": eigs[hi], "eig_lo": eigs[lo],
                          "flip": rep_i % 2})
    return items


def arm_e05() -> int:
    cell = "E24-S3-E05"
    t0 = time.time()
    out = OUT_E / "E05"
    out.mkdir(parents=True, exist_ok=True)
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415
    domain = "infra"
    items = e05_items()
    rows = []
    acquire_gpu_lock("s3_e05")
    try:
        for mk in READERS:
            model, tok = _load(mk)
            shortm = mk.split("/")[-1][:12]
            for ii, it in enumerate(items):
                dest = out / f"r_{shortm}_{ii}.json"
                if dest.exists():
                    rows.append(json.loads(dest.read_text(encoding="utf-8")))
                    continue
                hb = history_block(it["h_sids"], it["h_chs"], domain)
                ctx_hi = scenarios(domain)[it["offer_hi"]][0]
                ctx_lo = scenarios(domain)[it["offer_lo"]][0]
                first, second = (ctx_hi, ctx_lo) if it["flip"] == 0 \
                    else (ctx_lo, ctx_hi)
                ask = ("You are studying a decision-maker. Their known record:\n"
                       + hb + "\nYou may see ONE more of their past decisions. "
                       "Which would teach you more about how they decide?\n"
                       f"1) Their choice when: {first}\n"
                       f"2) Their choice when: {second}\n"
                       "Answer by restating, word for word, the situation "
                       "sentence of the one you pick.\n\nAnswer:")
                picked = None
                txt = ""
                for att in range(3):
                    txt = chat_gen(model, tok, ask, SEED0 + 4100 + ii * 8 + att,
                                   max_new=120)
                    low = txt.lower()
                    k_hi = ctx_hi.lower()[:20]
                    k_lo = ctx_lo.lower()[:20]
                    picked = ("hi" if k_hi in low and k_lo not in low else
                              "lo" if k_lo in low and k_hi not in low else None)
                    if picked is not None:
                        break
                row = {"reader": shortm, "item": ii, "picked": picked,
                       "flip": it["flip"], "eig_ratio": it["eig_hi"] / it["eig_lo"],
                       "text": txt[:300]}
                dest.write_text(json.dumps(row), encoding="utf-8", newline="\n")
                rows.append(row)
            _free(model)
    finally:
        release_gpu_lock()
    realized2 = [r for r in rows if r["picked"] is not None]
    cells = {}
    for mk in READERS:
        shortm = mk.split("/")[-1][:12]
        allr = [r for r in rows if r["reader"] == shortm]
        sub = [r for r in realized2 if r["reader"] == shortm]
        cells[shortm] = {
            "n_attempted": len(allr), "n_realized": len(sub),
            "yield": len(sub) / len(allr) if allr else None,
            "informative_rate": (sum(1 for r in sub if r["picked"] == "hi")
                                 / len(sub)) if sub else None,
            "first_position_rate": (sum(1 for r in sub if
                                        (r["picked"] == "hi") == (r["flip"] == 0))
                                    / len(sub)) if sub else None}
    (out / "verdict.json").write_text(json.dumps(
        {"cell": cell, "cells": cells, "chance": 0.5, "n_items": len(items),
         "mean_eig_ratio": sum(it["eig_hi"] / it["eig_lo"] for it in items)
         / len(items) if items else None,
         "yield": len(realized2) / len(rows) if rows else 0}, indent=1),
        encoding="utf-8", newline="\n")
    set_status(cell, "LANDED", actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"E05 landed: {json.dumps(cells)}")
    return 0


# ── E06: context ordering (card E24-S3-E06) ─────────────────────────────────────────
# The question in plain language: does the reader use a record better when it arrives
# BEFORE the question than after it — is record-reading order-sensitive where exact
# inference is not? Same items as the E02 records route, two presentations.
# DESIGN CHECK: contentically identical prompts, order the only factor; paired
# permutation; per-reader cells (the E02 asymmetry rule: never pool alone).

def arm_e06() -> int:
    cell = "E24-S3-E06"
    t0 = time.time()
    out = OUT_E / "E06"
    out.mkdir(parents=True, exist_ok=True)
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415
    from runners.s3_lib import choice_probs, utilities, PROFILE_W, perm_p         # noqa: PLC0415
    domain = "infra"
    rows = []
    acquire_gpu_lock("s3_e06")
    try:
        for mk in READERS:
            model, tok = _load(mk)
            shortm = mk.split("/")[-1][:12]
            for profile in AXES:
                for holdout in range(12):
                    probs = choice_probs(utilities(holdout, 1, domain),
                                         PROFILE_W[profile])
                    truth = AXES[max(range(4), key=lambda j: probs[j])]
                    sids, chs = target_history(profile, 8, holdout, domain,
                                               holdout)
                    hb = history_block(sids, chs, domain)
                    ctx, _, opts = scenarios(domain)[holdout]
                    letters = dict(zip("ABCD", AXES))
                    body = "\n".join(f"{letter}) the {opts[ax]}"
                                      for letter, ax in letters.items())
                    q = (f"This maker faces a new decision: {ctx}\nOptions:\n"
                         f"{body}\nPredict which option this maker will "
                         f"choose. Answer in one or two sentences that work "
                         f"the chosen option's full key phrase into your text, "
                         f"and no other option's key phrase.")
                    for order in ("record_first", "question_first"):
                        if order == "record_first":
                            prompt = ("You are predicting the behavior of a "
                                      "decision-maker. Their documented choice "
                                      "record:\n" + hb + "\n" + q
                                      + "\n\nPrediction:")
                        else:
                            prompt = ("You are predicting the behavior of a "
                                      "decision-maker. " + q
                                      + "\nTheir documented choice record:\n"
                                      + hb + "\n\nPrediction:")
                        dest = out / f"r_{shortm}_{profile}_{holdout}_{order}.json"
                        if dest.exists():
                            rows.append(json.loads(
                                dest.read_text(encoding="utf-8")))
                            continue
                        pred = None
                        for att in range(4):
                            txt = chat_gen(model, tok, prompt,
                                           SEED0 + 5000
                                           + hash_stable(dest.name) % 9999
                                           + att, max_new=180)
                            pred = realized_choice(txt, holdout, domain)
                            if pred is not None:
                                break
                        row = {"reader": shortm, "profile": profile,
                               "holdout": holdout, "order": order,
                               "pred": pred, "truth": truth,
                               "correct": int(pred == truth)}
                        dest.write_text(json.dumps(row), encoding="utf-8",
                                        newline="\n")
                        rows.append(row)
            _free(model)
    finally:
        release_gpu_lock()
    realized2 = [r for r in rows if r["pred"] is not None]
    cells = {}
    for mk in READERS:
        shortm = mk.split("/")[-1][:12]
        for order in ("record_first", "question_first"):
            sub = [r for r in realized2 if r["reader"] == shortm
                   and r["order"] == order]
            cells[f"{shortm}|{order}"] = {
                "n": len(sub),
                "acc": sum(r["correct"] for r in sub) / len(sub)
                if sub else None}
    by_key = {}
    for r in realized2:
        by_key.setdefault((r["reader"], r["profile"], r["holdout"]),
                          {})[r["order"]] = r["correct"]
    diffs = [v["record_first"] - v["question_first"] for v in by_key.values()
             if len(v) == 2]
    obs, pv = perm_p(diffs, SEED0 + 51) if diffs else (None, None)
    (out / "verdict.json").write_text(json.dumps(
        {"cell": cell, "cells": cells,
         "recordfirst_minus_questionfirst": obs, "perm_p": pv,
         "perm_seed": SEED0 + 51, "n_paired": len(diffs)}, indent=1),
        encoding="utf-8", newline="\n")
    set_status(cell, "LANDED", actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"E06 landed: {json.dumps({k: v['acc'] for k, v in cells.items()})}; "
          f"order diff {obs} (p={pv})")
    return 0


E03_BLENDS = {
    "robust_precedent": (1.0, 0.15, 0.15, 0.7),
    "robust_cheap": (1.0, 0.7, 0.15, 0.15),
    "cheap_fast": (0.15, 1.0, 0.7, 0.15),
    "fast_precedent": (0.15, 0.15, 1.0, 0.7),
    "cheap_precedent": (0.15, 1.0, 0.15, 0.7),
    "robust_fast": (1.0, 0.15, 0.7, 0.15),
}


def _e03_prog_battery(cell: str, profiles: dict, domain: str, tag: str,
                      produce: str) -> int:
    """Programmatic-target record-route battery over a profile set and domain.
    DESIGN CHECK: reads E02's VERDICT, not its file (the 2026-08-26 lesson);
    record-first prompt order (L195); per-reader cells with yields (L168); blend
    identifiability 29/30 recorded at build."""
    t0 = time.time()
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415
    OUT_E03.mkdir(parents=True, exist_ok=True)
    gate = json.loads((OUT_E / "E02" / "gate.json").read_text(encoding="utf-8"))
    if not gate.get("gate_pass"):
        (OUT_E03 / produce).write_text(json.dumps(
            {"cell": cell, "status": "INSTRUMENT-FAILED",
             "reason": "E02 route gate does not stand"}, indent=1),
            encoding="utf-8", newline="\n")
        set_status(cell, "INSTRUMENT_FAILED",
                   closure_reason="blocked by E02", actual_gpu_minutes=0.0)
        return 0
    hist_sids = list(range(8))
    holdouts = [8, 9, 10, 11]

    def amax_w(si, w):
        pr = choice_probs(utilities(si, 1, domain), w)
        return AXES[max(range(4), key=lambda j: pr[j])]

    rows = []
    acquire_gpu_lock(f"s3_e03{tag}")
    try:
        for mk in READERS:
            model, tok = _load(mk)
            rtag = mk.split("/")[-1][:12]
            for pname, w in profiles.items():
                hist_chs = [amax_w(si, w) for si in hist_sids]
                hb = history_block(hist_sids, hist_chs, domain)
                for ho in holdouts:
                    truth = amax_w(ho, w)
                    ctx, _, opts = scenarios(domain)[ho]
                    letters = dict(zip("ABCD", AXES))
                    body = "\n".join(f"{letter}) the {opts[ax]}"
                                      for letter, ax in letters.items())
                    prompt = ("You are predicting the behavior of a decision-"
                              "maker. Here is their documented choice record:\n"
                              + hb + f"\nNow this maker faces a new decision: "
                              f"{ctx}\nOptions:\n{body}\nPredict which option "
                              f"this maker will choose. Answer in one or two "
                              f"sentences that work the chosen option's full key "
                              f"phrase into your text, and no other option's key "
                              f"phrase.\n\nPrediction:")
                    dest = OUT_E03 / f"p{tag}_{rtag}_{pname}_{ho}.json"
                    if dest.exists():
                        rows.append(json.loads(dest.read_text(encoding="utf-8")))
                        continue
                    pred = None
                    for att in range(4):
                        txt = chat_gen(model, tok, prompt,
                                       SEED0 + 7000
                                       + hash_stable(dest.name) % 9999 + att,
                                       max_new=180)
                        pred = realized_choice(txt, ho, domain)
                        if pred is not None:
                            break
                    row = {"reader": rtag, "profile": pname, "holdout": ho,
                           "pred": pred, "truth": truth,
                           "correct": int(pred == truth)}
                    dest.write_text(json.dumps(row), encoding="utf-8",
                                    newline="\n")
                    rows.append(row)
            _free(model)
    finally:
        release_gpu_lock()
    realized2 = [r for r in rows if r["pred"] is not None]
    cells = {}
    for mk in READERS:
        rtag = mk.split("/")[-1][:12]
        allr = [r for r in rows if r["reader"] == rtag]
        sub = [r for r in realized2 if r["reader"] == rtag]
        cells[rtag] = {"n_attempted": len(allr), "n_realized": len(sub),
                       "yield": len(sub) / len(allr) if allr else None,
                       "acc": sum(r["correct"] for r in sub) / len(sub)
                       if sub else None}
    per_prof = {}
    for pname in profiles:
        sub = [r for r in realized2 if r["profile"] == pname]
        per_prof[pname] = {"n": len(sub),
                           "acc": sum(r["correct"] for r in sub) / len(sub)
                           if sub else None}
    (OUT_E03 / produce).write_text(json.dumps(
        {"cell": cell, "domain": domain, "per_reader": cells,
         "per_profile": per_prof, "chance": 0.25,
         "identifiability_note": "extended-set exact recovery 29/30 at build"},
        indent=1), encoding="utf-8", newline="\n")
    set_status(cell, "LANDED", actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"{cell}: {json.dumps({k: v['acc'] for k, v in cells.items()})}")
    return 0


def arm_e03x1() -> int:
    return _e03_prog_battery("E24-S3-E03/X1", E03_BLENDS, "infra", "x1",
                             "policies7to12.json")


def arm_e03x4() -> int:
    return _e03_prog_battery("E24-S3-E03/X4", dict(PROFILE_W), "process", "x4",
                             "domain2.json")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True,
                    choices=["e01", "e01_analyze", "e02", "e03", "e03x1",
                             "e03x4", "e04", "e05", "e06"])
    a = ap.parse_args()
    return {"e01": arm_e01, "e01_analyze": arm_e01_analyze, "e02": arm_e02,
            "e03": arm_e03, "e03x1": arm_e03x1, "e03x4": arm_e03x4,
            "e04": arm_e04, "e05": arm_e05, "e06": arm_e06}[a.arm]()


if __name__ == "__main__":
    sys.exit(main())
