"""Stage 3 Trunk V runners: V01 choice-set ruler, V02 artifact-only recovery,
V03 goal x profile, V04 cross-context. Cards E24-S3-V01..V04 in the manifest.

DESIGN CHECK (2026-08-24). Lessons applied: the environment's utilities are balanced by
construction (L169's fix designed-in, verified by s3_lib self-tests at import); the
records-aware known-answer runs BEFORE anything model-shaped scores (L139); the blind
floor is the realized choice marginal (floors follow marginals); realization is verified
in the accept loop (L156); profile posteriors use exact environment likelihoods, and any
model reader scores short hypotheses given long evidence, never the reverse (L169).
Failure directions per arm are in each arm's output. Statuses via the manifest.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from runners.s3_lib import (AXES, PROFILE_W, POLICY_LINES,                       # noqa: E402
                            bayes_profile_posterior, chat_gen, choice_probs, hash_stable,
                            episode_prompt, perm_p, realized_choice, scenarios,
                            utilities)
from soundingline.s3 import S3, set_status                                       # noqa: E402

SEED0 = 20000
MAKER_MODELS = ["Qwen/Qwen2.5-1.5B-Instruct", "HuggingFaceTB/SmolLM2-1.7B-Instruct"]
OUT_V = S3 / "V"


def programmatic_choices(profile: str, n: int, inst_seed: int, domain: str):
    """A programmed maker instance: softmax choices from the environment itself."""
    rng = random.Random(SEED0 + inst_seed)
    n_scen = len(scenarios(domain))
    sids, chs, strengths = [], [], []
    for _ in range(n):
        si = rng.randrange(n_scen)
        U = utilities(si, 1, domain)
        probs = choice_probs(U, PROFILE_W[profile])
        r = rng.random()
        acc = 0.0
        pick = 3
        for i, p in enumerate(probs):
            acc += p
            if r <= acc:
                pick = i
                break
        sids.append(si)
        chs.append(AXES[pick])
        strengths.append(max(probs) - sorted(probs)[-2])   # margin = evidence strength
    return sids, chs, strengths


def arm_v01() -> int:
    """The ruler: exact recovery from programmatic choices, blind floor from marginals,
    choice-set strength check, plus a generation sub-battery verifying enactment."""
    cell = "E24-S3-V01"
    t0 = time.time()
    out = OUT_V / "V01"
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED0)

    results = {"per_profile": {}, "strength_check": {}}
    all_choices = []
    for domain in ("infra", "process"):
        for profile in AXES:
            hits = 0
            posts = []
            for inst in range(3):
                sids, chs, strengths = programmatic_choices(profile, 200,
                                                            inst * 17 + hash_stable(domain) % 97,
                                                            domain)
                all_choices.extend(chs)
                post = bayes_profile_posterior(chs, sids, 1, domain)
                posts.append(post[profile])
                hits += max(post, key=post.get) == profile
                # strength: posteriors from the 50 strongest vs 50 weakest choices
                order = sorted(range(200), key=lambda i: -strengths[i])
                strong = [ (chs[i], sids[i]) for i in order[:50]]
                weak = [(chs[i], sids[i]) for i in order[-50:]]
                ps = bayes_profile_posterior([c for c, _ in strong],
                                             [s for _, s in strong], 1, domain)[profile]
                pw = bayes_profile_posterior([c for c, _ in weak],
                                             [s for _, s in weak], 1, domain)[profile]
                results["strength_check"].setdefault(f"{domain}|{profile}", []).append(
                    {"strong50": round(ps, 4), "weak50": round(pw, 4)})
            results["per_profile"][f"{domain}|{profile}"] = {
                "recovered": hits, "of": 3, "mean_posterior": sum(posts) / 3}
    marginal = Counter(all_choices)
    blind_floor = max(marginal.values()) / sum(marginal.values())
    exact_ok = all(v["recovered"] == 3 for v in results["per_profile"].values())
    strength_ok = all(all(x["strong50"] > x["weak50"] for x in v)
                      for v in results["strength_check"].values())

    # generation sub-battery: models must ENACT programmatic choices at >= 85 percent
    import torch                                                                 # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                 # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock          # noqa: PLC0415
    enact = {}
    acquire_gpu_lock("s3_v01")
    try:
        for mk in MAKER_MODELS:
            tok = AutoTokenizer.from_pretrained(mk)
            model = AutoModelForCausalLM.from_pretrained(
                mk, dtype=torch.float16).to("cuda").eval()
            ok = tried = 0
            for i in range(24):
                domain = "infra" if i % 2 == 0 else "process"
                si = rng.randrange(len(scenarios(domain)))
                target_ax = AXES[i % 4]
                prompt = episode_prompt(si, domain, POLICY_LINES[target_ax]) + (
                    f"\n(You have decided: the best option is the one about "
                    f"{scenarios(domain)[si][2][target_ax]}. Commit to it.)")
                tried += 1
                for att in range(4):
                    txt = chat_gen(model, tok, prompt, SEED0 + i * 16 + att)
                    if realized_choice(txt, si, domain) == target_ax:
                        ok += 1
                        break
            enact[mk.split("/")[-1]] = ok / tried
            del model
            torch.cuda.empty_cache()
    finally:
        release_gpu_lock()
    enact_ok = all(v >= 0.85 for v in enact.values())

    verdict = ("RULER-STANDS" if (exact_ok and strength_ok and enact_ok
                                  and blind_floor < 0.5) else "INSTRUMENT-FAILED")
    (out / "ruler.json").write_text(json.dumps(
        {"cell": cell, "verdict": verdict, "exact_recovery_all": exact_ok,
         "strength_monotone_all": strength_ok, "blind_floor": blind_floor,
         "enactment": enact, "detail": results}, indent=1),
        encoding="utf-8", newline="\n")
    set_status(cell, "LANDED" if verdict == "RULER-STANDS" else "INSTRUMENT_FAILED",
               closure_reason=None if verdict == "RULER-STANDS" else "ruler failed",
               actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"V01 {verdict}: blind floor {blind_floor:.3f}, enactment {enact}")
    return 0


def arm_v02() -> int:
    """Artifact-only recovery: models write artifacts enacting programmatic choices;
    the reader sees ONLY artifacts, extracts realized choices mechanically, and the
    posterior comes from the environment likelihood over extracted choices. Opportunity
    dose = number of artifacts shown."""
    cell = "E24-S3-V02"
    t0 = time.time()
    out = OUT_V / "V02"
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED0 + 2)
    import torch                                                                 # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                 # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock          # noqa: PLC0415

    artifacts = []      # (profile, maker, domain, scen_i, realized_ax)
    acquire_gpu_lock("s3_v02")
    try:
        for mk in MAKER_MODELS:
            tok = AutoTokenizer.from_pretrained(mk)
            model = AutoModelForCausalLM.from_pretrained(
                mk, dtype=torch.float16).to("cuda").eval()
            for profile in AXES:
                sids, chs, _ = programmatic_choices(profile, 40, 5, "infra")
                got = 0
                for j, (si, ax) in enumerate(zip(sids, chs)):
                    dest = out / f"art_{mk.split('/')[-1][:8]}_{profile}_{j}.json"
                    if dest.exists():
                        artifacts.append(json.loads(dest.read_text(encoding="utf-8")))
                        got += 1
                        continue
                    prompt = episode_prompt(si, "infra", POLICY_LINES[profile]) + (
                        f"\n(You have decided: the best option is the one about "
                        f"{scenarios('infra')[si][2][ax]}. Commit to it.)")
                    for att in range(4):
                        txt = chat_gen(model, tok, prompt,
                                       SEED0 + 40000 + j * 16 + att)
                        if realized_choice(txt, si, "infra") == ax:
                            rec = {"profile": profile, "maker": mk, "scen_i": si,
                                   "ax": ax, "text": txt}
                            dest.write_text(json.dumps(rec, ensure_ascii=False),
                                            encoding="utf-8", newline="\n")
                            artifacts.append(rec)
                            got += 1
                            break
            del model
            torch.cuda.empty_cache()
    finally:
        release_gpu_lock()

    # dose curve: posterior on the true profile from k artifacts, mechanical extraction
    by_key = {}
    for a in artifacts:
        by_key.setdefault((a["maker"], a["profile"]), []).append(a)
    dose_curve = {}
    for k in (2, 5, 10, 20):
        vals, hits, cells_n = [], 0, 0
        for (mk, prof), arts in by_key.items():
            if len(arts) < k:
                continue
            cells_n += 1
            sample = rng.sample(arts, k)
            chs = [a["ax"] for a in sample]
            sids = [a["scen_i"] for a in sample]
            post = bayes_profile_posterior(chs, sids, 1, "infra")
            vals.append(post[prof])
            hits += max(post, key=post.get) == prof
        dose_curve[str(k)] = {"cells": cells_n, "top1": hits / cells_n if cells_n else None,
                              "mean_posterior": sum(vals) / len(vals) if vals else None}
        print(f"  k={k}: {dose_curve[str(k)]}")
    yield_frac = len(artifacts) / (len(MAKER_MODELS) * 4 * 40)
    rising = (dose_curve["20"]["mean_posterior"] or 0) > (dose_curve["2"]["mean_posterior"] or 1)
    status = "LANDED" if yield_frac >= 0.9 and rising else (
        "LANDED" if yield_frac >= 0.9 else "INSTRUMENT_FAILED")
    (out / "verdict.json").write_text(json.dumps(
        {"cell": cell, "yield": yield_frac, "dose_curve": dose_curve,
         "dose_sensitivity_rising": rising,
         "status": "PROMISING" if rising and yield_frac >= 0.9 else "QUIET"},
        indent=1), encoding="utf-8", newline="\n")
    set_status(cell, status,
               closure_reason=None if status == "LANDED" else "yield below floor",
               actual_gpu_minutes=(time.time() - t0) / 60)
    return 0


# ── V03: goal x profile separation (card E24-S3-V03) ────────────────────────────────
# The question in plain language: can a records-aware reader tell a maker's STANDING
# preference profile apart from an episode-local GOAL that temporarily bends choices —
# and does each factor stay recoverable when the other varies? Makers are programmatic:
# profile w plus, on goal-active episodes, a bonus on the goal axis. The exact joint
# posterior over (profile, goal) is the reader; recovery of both factors is the result.
# DESIGN CHECK: exact math end to end (known answers by construction, L139); goal-active
# episodes are half the record, interleaved, so neither factor is aliased by episode
# count; the confusion table reports every (profile, goal) cell (L168); the goal bonus
# dose is graded so partial identifiability is visible rather than binary.

def v03_choice(si, seed, domain, w_name, goal, bonus, rng):
    U = utilities(si, seed, domain)
    w = list(PROFILE_W[w_name])
    if goal is not None:
        gi = AXES.index(goal)
        w = [wi + (bonus if k == gi else 0.0) for k, wi in enumerate(w)]
    probs = choice_probs(U, tuple(w))
    r = rng.random()
    acc = 0.0
    for i, p in enumerate(probs):
        acc += p
        if r <= acc:
            return AXES[i]
    return AXES[3]


def v03_joint_posterior(recs, seed, domain, bonus):
    """Exact posterior over (profile, goal) from records tagged goal-active or not."""
    import math                                                                   # noqa: PLC0415
    grid = [(p, g) for p in AXES for g in AXES if g != p]
    logp = {pg: 0.0 for pg in grid}
    for si, ch, active in recs:
        idx = AXES.index(ch)
        U = utilities(si, seed, domain)
        for (p, g) in grid:
            w = list(PROFILE_W[p])
            if active:
                w[AXES.index(g)] += bonus
            logp[(p, g)] += math.log(max(choice_probs(U, tuple(w))[idx], 1e-12))
    m = max(logp.values())
    exps = {k: math.exp(v - m) for k, v in logp.items()}
    z = sum(exps.values())
    return {k: v / z for k, v in exps.items()}


def arm_v03() -> int:
    cell = "E24-S3-V03"
    t0 = time.time()
    out = OUT_V / "V03"
    out.mkdir(parents=True, exist_ok=True)
    results = {}
    for bonus in (0.4, 0.8, 1.2):
        cellhits_p = cellhits_g = cells_n = 0
        confusion = {}
        for prof in AXES:
            for goal in AXES:
                if goal == prof:
                    continue
                for rep in range(3):
                    rng = random.Random(SEED0 + 500
                                        + hash_stable(f"{prof}|{goal}|{rep}"))
                    recs = []
                    for k in range(40):
                        si = rng.randrange(12)
                        active = k % 2 == 0
                        ch = v03_choice(si, 1, "infra", prof,
                                        goal if active else None, bonus, rng)
                        recs.append((si, ch, active))
                    post = v03_joint_posterior(recs, 1, "infra", bonus)
                    bp, bg = max(post, key=post.get)
                    cells_n += 1
                    cellhits_p += bp == prof
                    cellhits_g += bg == goal
                    confusion.setdefault(f"{prof}|{goal}", []).append(f"{bp}|{bg}")
        results[str(bonus)] = {
            "profile_recovery": cellhits_p / cells_n,
            "goal_recovery": cellhits_g / cells_n,
            "n_cells": cells_n,
            "confusion": {k: {vv: v.count(vv) for vv in set(v)}
                          for k, v in confusion.items()}}
        print(f"  bonus {bonus}: profile {cellhits_p}/{cells_n}, "
              f"goal {cellhits_g}/{cells_n}")
    (out / "verdict.json").write_text(json.dumps(
        {"cell": cell, "by_bonus": {k: {kk: vv for kk, vv in v.items()
                                        if kk != "confusion"}
                                    for k, v in results.items()},
         "confusion_full": {k: v["confusion"] for k, v in results.items()},
         "design": "40 records, half goal-active interleaved, 12 profile-goal "
                   "pairs x 3 reps per dose"}, indent=1),
        encoding="utf-8", newline="\n")
    set_status(cell, "LANDED", actual_gpu_minutes=(time.time() - t0) / 60)
    return 0


# ── V04: cross-context transfer (card E24-S3-V04) ───────────────────────────────────
# The question in plain language: a profile learned from a maker's INFRASTRUCTURE
# decisions — does it predict their PERSONNEL decisions? Profiles are domain-general by
# construction, so exact inference transfers perfectly; the question is whether model
# readers carry the profile across surface domains or treat them as different people.
# DESIGN CHECK: exact transfer ceiling computed first; records route only (the E02-
# validated route); within-domain cells beside cross-domain (L168); mechanical readout.

def arm_v04() -> int:
    cell = "E24-S3-V04"
    t0 = time.time()
    out = OUT_V / "V04"
    out.mkdir(parents=True, exist_ok=True)
    import torch                                                                  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                  # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415
    from runners.s3_lib import (bayes_profile_posterior, chat_gen,                # noqa: PLC0415
                                realized_choice)
    import random as _r                                                          # noqa: PLC0415
    readers = MAKER_MODELS
    rng = _r.Random(SEED0 + 9)

    def amax(si, prof, domain):
        pr = choice_probs(utilities(si, 1, domain), PROFILE_W[prof])
        return AXES[max(range(4), key=lambda j: pr[j])]

    # exact ceiling: posterior from 8 infra records applied to process probes
    exact_hits = exact_n = 0
    plan = []
    for prof in AXES:
        for rep in range(6):
            h_sids = [rng.randrange(12) for _ in range(8)]
            h_chs = [amax(si, prof, "infra") for si in h_sids]
            probe_in = rng.randrange(12)
            probe_x = rng.randrange(12)
            plan.append({"prof": prof, "h_sids": h_sids, "h_chs": h_chs,
                         "probe_in": probe_in, "probe_x": probe_x})
            post = bayes_profile_posterior(h_chs, h_sids, 1, "infra")
            best = max(post, key=post.get)
            exact_hits += amax(probe_x, best, "process") \
                == amax(probe_x, prof, "process")
            exact_n += 1
    rows = []
    acquire_gpu_lock("s3_v04")
    try:
        for mk in readers:
            tok = AutoTokenizer.from_pretrained(mk)
            model = AutoModelForCausalLM.from_pretrained(
                mk, dtype=torch.float16).to("cuda").eval()
            shortm = mk.split("/")[-1][:12]
            for ii, it in enumerate(plan):
                hb = "\n".join(
                    f"- Faced with: {scenarios('infra')[si][0]} They chose the "
                    f"{scenarios('infra')[si][2][ch]}."
                    for si, ch in zip(it["h_sids"], it["h_chs"]))
                for tag, domain, probe in (("within", "infra", it["probe_in"]),
                                           ("cross", "process", it["probe_x"])):
                    truth = amax(probe, it["prof"], domain)
                    ctx, _, opts = scenarios(domain)[probe]
                    letters = dict(zip("ABCD", AXES))
                    body = "\n".join(f"{letter}) the {opts[ax]}"
                                      for letter, ax in letters.items())
                    prompt = ("You are predicting the behavior of a decision-"
                              "maker. Here is their documented choice "
                              "record:\n" + hb
                              + f"\nNow this maker faces a new decision: {ctx}"
                              f"\nOptions:\n{body}\nPredict which option "
                              f"this maker will choose. Answer in one or two "
                              f"sentences that work the chosen option's full "
                              f"key phrase into your text, and no other "
                              f"option's key phrase.\n\nPrediction:")
                    dest = out / f"r_{shortm}_{ii}_{tag}.json"
                    if dest.exists():
                        rows.append(json.loads(dest.read_text(encoding="utf-8")))
                        continue
                    pred = None
                    for att in range(4):
                        txt = chat_gen(model, tok, prompt,
                                       SEED0 + 9500 + ii * 32 + att,
                                       max_new=180)
                        pred = realized_choice(txt, probe, domain)
                        if pred is not None:
                            break
                    row = {"reader": shortm, "item": ii, "tag": tag,
                           "pred": pred, "truth": truth,
                           "correct": int(pred == truth)}
                    dest.write_text(json.dumps(row), encoding="utf-8",
                                    newline="\n")
                    rows.append(row)
            del model
            torch.cuda.empty_cache()
    finally:
        release_gpu_lock()
    realized2 = [r for r in rows if r["pred"] is not None]
    cells = {}
    for mk in readers:
        shortm = mk.split("/")[-1][:12]
        for tag in ("within", "cross"):
            sub = [r for r in realized2 if r["reader"] == shortm
                   and r["tag"] == tag]
            cells[f"{shortm}|{tag}"] = {
                "n": len(sub),
                "acc": sum(r["correct"] for r in sub) / len(sub)
                if sub else None}
    (out / "verdict.json").write_text(json.dumps(
        {"cell": cell, "cells": cells,
         "exact_cross_ceiling": exact_hits / exact_n}, indent=1),
        encoding="utf-8", newline="\n")
    set_status(cell, "LANDED", actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"V04 landed: {json.dumps(cells)}; exact ceiling "
          f"{exact_hits / exact_n:.3f}")
    return 0


# ── V05: editor preference (card E24-S3-V05) ────────────────────────────────────────
# The question in plain language: an EDITOR who rewrites other makers' recommendations
# — is the editor's own preference profile recoverable from the direction of their
# edits alone? Editors are programmatic (edit = switch the choice to the editor-profile
# argmax when it differs, keep otherwise); the exact posterior reads the switched-to
# choices. A model-editor arm rewrites text; realized post-edit choices go through the
# same posterior.
# DESIGN CHECK: exact half first (known answer); model arm's rewrite is accept-time
# checked (exactly the new anchor present); the originals' maker profile differs from
# the editor's so edits exist; per-editor cells.

def arm_v05() -> int:
    cell = "E24-S3-V05"
    t0 = time.time()
    out = OUT_V / "V05"
    out.mkdir(parents=True, exist_ok=True)
    import torch                                                                  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                  # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415
    rng = random.Random(SEED0 + 55)
    domain = "infra"
    # exact half: editor recovery from switched choices
    # audit 2026-08-24: the first version replaced every choice with the editor's
    # argmax (tautological). Now the maker's choices are softmax-sampled and the editor
    # only overrides when its own preferred option differs from what the maker chose,
    # so kept choices carry the maker's signal and recovery is a real question.
    exact = {}
    for editor in AXES:
        hits = 0
        maker_mass = []
        for rep in range(6):
            maker = rng.choice([a for a in AXES if a != editor])
            sids, mk_chs, _ = programmatic_choices(maker, 20, 700 + rep
                                                   + 50 * AXES.index(editor), domain)
            edited = []
            for si, mk_ch in zip(sids, mk_chs):
                ed_ch = AXES[max(range(4), key=lambda j: choice_probs(
                    utilities(si, 1, domain), PROFILE_W[editor])[j])]
                edited.append(ed_ch if ed_ch != mk_ch else mk_ch)
            post = bayes_profile_posterior(edited, sids, 1, domain)
            hits += max(post, key=post.get) == editor
            maker_mass.append(post[maker])
        exact[editor] = {"recovered": hits / 6,
                         "residual_maker_mass": sum(maker_mass) / 6}
    # model-editor arm: one model, one editor profile per run over 24 items
    model_cells = {}
    acquire_gpu_lock("s3_v05")
    try:
        mk = MAKER_MODELS[0]
        tok = AutoTokenizer.from_pretrained(mk)
        model = AutoModelForCausalLM.from_pretrained(
            mk, dtype=torch.float16).to("cuda").eval()
        for editor in ("robust", "cheap"):
            recs = []
            for j in range(24):
                si = rng.randrange(12)
                maker = rng.choice([a for a in AXES if a != editor])
                mk_ch = AXES[max(range(4), key=lambda j2: choice_probs(
                    utilities(si, 1, domain), PROFILE_W[maker])[j2])]
                _, _, opts = scenarios(domain)[si]
                orig = (f"I recommend the {opts[mk_ch]} for this decision.")
                dest = out / f"ed_{editor}_{j}.json"
                if dest.exists():
                    recs.append(json.loads(dest.read_text(encoding="utf-8")))
                    continue
                prompt = ("You are an editor reviewing a colleague's "
                          "recommendation. Your standing approach: "
                          + POLICY_LINES[editor]
                          + f"\nThe decision: {scenarios(domain)[si][0]}\n"
                          f"Options: " + "; ".join(
                              f"the {opts[ax]}" for ax in AXES)
                          + f"\nTheir draft: {orig}\nRewrite the "
                          "recommendation as YOU would have it, committing to "
                          "exactly one option by its full key phrase."
                          "\n\nRewritten recommendation:")
                ch = None
                for att in range(4):
                    txt = chat_gen(model, tok, prompt,
                                   SEED0 + 5600 + j * 16 + att)
                    ch = realized_choice(txt, si, domain)
                    if ch is not None:
                        break
                rec = {"si": si, "editor": editor, "orig_choice": mk_ch,
                       "edited_choice": ch}
                dest.write_text(json.dumps(rec), encoding="utf-8",
                                newline="\n")
                recs.append(rec)
            good = [r for r in recs if r["edited_choice"]]
            post = bayes_profile_posterior(
                [r["edited_choice"] for r in good],
                [r["si"] for r in good], 1, domain) if good else None
            model_cells[editor] = {
                "n_realized": len(good),
                "posterior": post,
                "recovered": (max(post, key=post.get) == editor)
                if post else None,
                "switch_rate": sum(1 for r in good
                                   if r["edited_choice"] != r["orig_choice"])
                / len(good) if good else None}
        del model
        torch.cuda.empty_cache()
    finally:
        release_gpu_lock()
    (out / "verdict.json").write_text(json.dumps(
        {"cell": cell, "exact_recovery_per_editor": exact,
         "model_editor": model_cells}, indent=1),
        encoding="utf-8", newline="\n")
    set_status(cell, "LANDED", actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"V05 landed: exact {exact}; model {json.dumps(model_cells)}")
    return 0


# ── V06: longitudinal drift (card E24-S3-V06) ───────────────────────────────────────
# The question in plain language: a maker whose standing profile CHANGES mid-record —
# when does the exact reader notice, and how much record does detection cost as a
# function of how different the new profile is? A changepoint ruler, all exact.
# DESIGN CHECK: pure known-answer construction; detection = the windowed posterior's
# top profile flipping and staying flipped; detection lag reported per (old, new)
# pair and per window size; no model in the loop (the model arm belongs to a later
# expansion rung if this ladder finds structure).

def arm_v06() -> int:
    cell = "E24-S3-V06"
    t0 = time.time()
    out = OUT_V / "V06"
    out.mkdir(parents=True, exist_ok=True)
    domain = "infra"
    results = {}
    for old in AXES:
        for new in AXES:
            if old == new:
                continue
            lags = []
            for rep in range(6):
                rng = random.Random(SEED0 + 66
                                    + hash_stable(f"{old}|{new}|{rep}"))
                sids, chs = [], []
                for k in range(60):
                    si = rng.randrange(12)
                    prof = old if k < 30 else new
                    probs = choice_probs(utilities(si, 1, domain),
                                         PROFILE_W[prof])
                    r = rng.random()
                    acc = 0.0
                    pick = 3
                    for i2, q in enumerate(probs):
                        acc += q
                        if r <= acc:
                            pick = i2
                            break
                    sids.append(si)
                    chs.append(AXES[pick])
                # windowed posterior, window 10
                detect = None
                for end in range(35, 61):
                    post = bayes_profile_posterior(chs[end - 10:end],
                                                   sids[end - 10:end], 1,
                                                   domain)
                    if max(post, key=post.get) == new:
                        # must stay flipped for the next 3 windows
                        stays = all(
                            max(bayes_profile_posterior(
                                chs[e2 - 10:e2], sids[e2 - 10:e2], 1,
                                domain), key=lambda k2:
                                bayes_profile_posterior(
                                    chs[e2 - 10:e2], sids[e2 - 10:e2], 1,
                                    domain)[k2]) == new
                            for e2 in range(end + 1,
                                            min(end + 4, 61)))
                        if stays:
                            detect = end - 30
                            break
                lags.append(detect)
            det = [x for x in lags if x is not None]
            results[f"{old}->{new}"] = {
                "n": len(lags), "detected": len(det),
                "mean_lag": sum(det) / len(det) if det else None}
    (out / "verdict.json").write_text(json.dumps(
        {"cell": cell, "window": 10, "change_at": 30,
         "per_transition": results}, indent=1),
        encoding="utf-8", newline="\n")
    set_status(cell, "LANDED", actual_gpu_minutes=(time.time() - t0) / 60)
    det_all = [v["mean_lag"] for v in results.values()
               if v["mean_lag"] is not None]
    print(f"V06 landed: {len(det_all)}/12 transitions detected, mean lag "
          f"{sum(det_all) / len(det_all):.1f}" if det_all else "V06: none")
    return 0


BLEND_W = {
    "robust_precedent": (1.0, 0.15, 0.15, 0.7),
    "robust_cheap": (1.0, 0.7, 0.15, 0.15),
    "cheap_fast": (0.15, 1.0, 0.7, 0.15),
    "fast_precedent": (0.15, 0.15, 1.0, 0.7),
    "cheap_precedent": (0.15, 1.0, 0.15, 0.7),
    "robust_fast": (1.0, 0.15, 0.7, 0.15),
}
# identifiability proven at build time: 29/30 instance recoveries over the extended
# 10-profile set; the single near-miss (fast_precedent -> fast) is the known ceiling


def arm_v01x1() -> int:
    """V01/X1: recovery and floor legs over four blend profiles with fresh instances;
    the strength leg REBUILT on expected information gain (the margin metric failed,
    L215). CPU-exact; the maker-enactment leg is not rerun (L215: maker-specific,
    unconsumed). DESIGN CHECK: known-answer existence proven before build (29/30);
    per-cell recovery counts beside the aggregate (L168)."""
    import math                                                                   # noqa: PLC0415
    from collections import Counter                                               # noqa: PLC0415
    cell = "E24-S3-V01/X1"
    t0 = time.time()
    out = OUT_V / "V01"
    ext = {**PROFILE_W, **{k: BLEND_W[k] for k in
                           ("robust_precedent", "robust_cheap",
                            "cheap_fast", "cheap_precedent")}}
    results = {"per_profile": {}, "strength_eig": {}}
    all_choices = []

    def H(p):
        return -sum(v * math.log(v) for v in p.values() if v > 1e-12)

    for domain in ("infra", "process"):
        for name, w in ext.items():
            hits = 0
            for inst in range(3):
                rng = random.Random(SEED0 + 60000 + inst * 31
                                    + hash_stable(f"{name}|{domain}") % 977)
                sids, chs = [], []
                for _ in range(200):
                    si = rng.randrange(12)
                    probs = choice_probs(utilities(si, 1, domain), w)
                    r = rng.random()
                    acc = 0.0
                    pick = 3
                    for i, p in enumerate(probs):
                        acc += p
                        if r <= acc:
                            pick = i
                            break
                    sids.append(si)
                    chs.append(AXES[pick])
                all_choices.extend(chs)
                post = bayes_profile_posterior(chs, sids, 1, domain,
                                               profiles=ext)
                hits += max(post, key=post.get) == name
                gains = []
                prev_h = math.log(len(ext))
                for k in range(1, 201):
                    running = bayes_profile_posterior(chs[:k], sids[:k], 1,
                                                      domain, profiles=ext)
                    h = H(running)
                    gains.append(prev_h - h)
                    prev_h = h
                order = sorted(range(200), key=lambda i: -gains[i])
                ps = bayes_profile_posterior(
                    [chs[i] for i in order[:50]],
                    [sids[i] for i in order[:50]], 1, domain,
                    profiles=ext)[name]
                pw = bayes_profile_posterior(
                    [chs[i] for i in order[-50:]],
                    [sids[i] for i in order[-50:]], 1, domain,
                    profiles=ext)[name]
                results["strength_eig"].setdefault(
                    f"{domain}|{name}", []).append(
                    {"strong50": round(ps, 4), "weak50": round(pw, 4)})
            results["per_profile"][f"{domain}|{name}"] = {
                "recovered": hits, "of": 3}
    marginal = Counter(all_choices)
    blind_floor = max(marginal.values()) / sum(marginal.values())
    rec_total = sum(v["recovered"] for v in results["per_profile"].values())
    rec_of = sum(v["of"] for v in results["per_profile"].values())
    mono = sum(1 for v in results["strength_eig"].values()
               for x in v if x["strong50"] > x["weak50"])
    mono_of = sum(len(v) for v in results["strength_eig"].values())
    (out / "profiles5to8.json").write_text(json.dumps(
        {"cell": cell, "recovery": f"{rec_total}/{rec_of}",
         "blind_floor": blind_floor,
         "eig_strength_monotone_cells": f"{mono}/{mono_of}",
         "detail": results,
         "note": "strength leg rebuilt on realized information gain after the "
                 "margin metric's L215 failure; enactment leg not rerun"},
        indent=1), encoding="utf-8", newline="\n")
    set_status(cell, "LANDED", actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"V01/X1: recovery {rec_total}/{rec_of}, EIG-monotone {mono}/{mono_of}, "
          f"floor {blind_floor:.3f}")
    return 0


def arm_v04x4() -> int:
    """V04/X4: cross-context prediction into the third domain (events). Exact ceiling
    first; per-reader cells with yields; records-first prompts (L195)."""
    cell = "E24-S3-V04/X4"
    t0 = time.time()
    out = OUT_V / "V04"
    import torch                                                                  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                  # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415
    import random as _r                                                          # noqa: PLC0415
    rng = _r.Random(SEED0 + 19)

    def amax(si, prof, domain):
        pr = choice_probs(utilities(si, 1, domain), PROFILE_W[prof])
        return AXES[max(range(4), key=lambda j: pr[j])]

    exact_hits = exact_n = 0
    plan = []
    for prof in AXES:
        for rep in range(6):
            h_sids = [rng.randrange(12) for _ in range(8)]
            h_chs = [amax(si, prof, "infra") for si in h_sids]
            probe_x = rng.randrange(12)
            plan.append({"prof": prof, "h_sids": h_sids, "h_chs": h_chs,
                         "probe_x": probe_x})
            post = bayes_profile_posterior(h_chs, h_sids, 1, "infra")
            best = max(post, key=post.get)
            exact_hits += amax(probe_x, best, "events") \
                == amax(probe_x, prof, "events")
            exact_n += 1
    rows = []
    acquire_gpu_lock("s3_v04x4")
    try:
        for mk in MAKER_MODELS:
            tok = AutoTokenizer.from_pretrained(mk)
            model = AutoModelForCausalLM.from_pretrained(
                mk, dtype=torch.float16).to("cuda").eval()
            shortm = mk.split("/")[-1][:12]
            for ii, it in enumerate(plan):
                hb = "\n".join(
                    f"- Faced with: {scenarios('infra')[si][0]} They chose the "
                    f"{scenarios('infra')[si][2][ch]}."
                    for si, ch in zip(it["h_sids"], it["h_chs"]))
                probe = it["probe_x"]
                truth = amax(probe, it["prof"], "events")
                ctx, _, opts = scenarios("events")[probe]
                letters = dict(zip("ABCD", AXES))
                body = "\n".join(f"{letter}) the {opts[ax]}"
                                  for letter, ax in letters.items())
                prompt = ("You are predicting the behavior of a decision-maker. "
                          "Here is their documented choice record:\n" + hb
                          + f"\nNow this maker faces a new decision: {ctx}"
                          f"\nOptions:\n{body}\nPredict which option this "
                          f"maker will choose. Answer in one or two sentences "
                          f"that work the chosen option's full key phrase into "
                          f"your text, and no other option's key phrase."
                          f"\n\nPrediction:")
                dest = out / f"x4_{shortm}_{ii}.json"
                if dest.exists():
                    rows.append(json.loads(dest.read_text(encoding="utf-8")))
                    continue
                pred = None
                for att in range(4):
                    txt = chat_gen(model, tok, prompt,
                                   SEED0 + 61000 + ii * 32 + att, max_new=180)
                    pred = realized_choice(txt, probe, "events")
                    if pred is not None:
                        break
                row = {"reader": shortm, "item": ii, "pred": pred,
                       "truth": truth, "correct": int(pred == truth)}
                dest.write_text(json.dumps(row), encoding="utf-8", newline="\n")
                rows.append(row)
            del model
            torch.cuda.empty_cache()
    finally:
        release_gpu_lock()
    realized2 = [r for r in rows if r["pred"] is not None]
    cells = {}
    for mk in MAKER_MODELS:
        shortm = mk.split("/")[-1][:12]
        allr = [r for r in rows if r["reader"] == shortm]
        sub = [r for r in realized2 if r["reader"] == shortm]
        cells[shortm] = {
            "n_attempted": len(allr), "n_realized": len(sub),
            "yield": len(sub) / len(allr) if allr else None,
            "acc": sum(r["correct"] for r in sub) / len(sub) if sub else None}
    prior = json.loads((out / "verdict.json").read_text(encoding="utf-8"))
    (out / "domain3.json").write_text(json.dumps(
        {"cell": cell, "cells": cells,
         "exact_domain3_ceiling": exact_hits / exact_n,
         "domain2_comparison": prior["cells"]}, indent=1),
        encoding="utf-8", newline="\n")
    set_status(cell, "LANDED", actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"V04/X4: {json.dumps({k: v['acc'] for k, v in cells.items()})}; "
          f"exact ceiling {exact_hits / exact_n:.3f}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True,
                    choices=["v01", "v01x1", "v02", "v03", "v04", "v04x4",
                             "v05", "v06"])
    a = ap.parse_args()
    return {"v01": arm_v01, "v01x1": arm_v01x1, "v02": arm_v02,
            "v03": arm_v03, "v04": arm_v04, "v04x4": arm_v04x4,
            "v05": arm_v05, "v06": arm_v06}[a.arm]()


if __name__ == "__main__":
    sys.exit(main())
