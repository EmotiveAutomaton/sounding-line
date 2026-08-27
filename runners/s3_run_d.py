"""Stage 3 Trunk D runners: D01 four-world collaborative ecology. Card E24-S3-D01.

The question in plain language: when a standing director policy shapes a small team's
episodes, how far does the director's hand reach into what the workers actually choose —
and can that reach be read back from the record alone?

Worlds: W1 robust-director, W2 cheap-director, W3 fast-director, W4 no director
(control). Three worker instances per world (two 1.5-2B instruct models and the 360M),
rotating over 48 episodes per world across both scenario domains.

DESIGN CHECK (2026-08-24). Lessons applied: the ecology inherits the balanced utility
environment, so no option is globally attractive (L169 designed-out); realized choices
are accept-time mechanical (L156); the attribution read is the exact posterior — a
known-answer read, since directors are programmatic (L139); reach is reported per world
BESIDE the undirected control world's marginal, not only as a contrast (L168); the
uncontrolled worker-compliance rate is the pilot number D02's intervention ruler needs
(compliance-before-factorial, L169); per-worker cells reported so a single compliant
worker cannot masquerade as ecology-wide reach.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from runners.s3_lib import (AXES, POLICY_LINES, bayes_profile_posterior,          # noqa: E402
                            chat_gen, episode_prompt, realized_choice, scenarios)
from soundingline.s3 import S3, set_status                                        # noqa: E402

SEED0 = 70000
WORKERS = ["Qwen/Qwen2.5-1.5B-Instruct", "HuggingFaceTB/SmolLM2-1.7B-Instruct",
           "HuggingFaceTB/SmolLM2-360M-Instruct"]
WORLDS = {"W1": "robust", "W2": "cheap", "W3": "fast", "W4": None}
N_EP = 48
OUT_D = S3 / "D" / "D01"


def world_prompt(si: int, domain: str, director_axis: str | None) -> str:
    if director_axis is None:
        return episode_prompt(si, domain)
    lead = (f"Your team lead's standing direction for all decisions: "
            f"{POLICY_LINES[director_axis]}")
    base = episode_prompt(si, domain)
    return base.replace("\nWrite a short recommendation",
                        f"\n{lead}\nWrite a short recommendation")


def arm_d01() -> int:
    cell = "E24-S3-D01"
    t0 = time.time()
    OUT_D.mkdir(parents=True, exist_ok=True)
    import torch                                                                  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                  # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415

    rng = random.Random(SEED0)
    # episode plan up front: (world, ep_i) -> (worker_i, domain, scen_i)
    plan = {}
    for w in WORLDS:
        for ep in range(N_EP):
            domain = "infra" if ep % 2 == 0 else "process"
            plan[(w, ep)] = (ep % len(WORKERS), domain,
                             rng.randrange(len(scenarios(domain))))
    acquire_gpu_lock("s3_d01")
    try:
        for wi, mk in enumerate(WORKERS):
            tok = AutoTokenizer.from_pretrained(mk)
            model = AutoModelForCausalLM.from_pretrained(
                mk, dtype=torch.float16).to("cuda").eval()
            for (w, ep), (worker_i, domain, si) in plan.items():
                if worker_i != wi:
                    continue
                dest = OUT_D / f"ep_{w}_{ep}.json"
                if dest.exists():
                    continue
                ch = None
                txt = ""
                for att in range(4):
                    txt = chat_gen(model, tok,
                                   world_prompt(si, domain, WORLDS[w]),
                                   SEED0 + ep * 64 + att)
                    ch = realized_choice(txt, si, domain)
                    if ch is not None:
                        break
                dest.write_text(json.dumps(
                    {"world": w, "ep": ep, "worker": mk, "domain": domain,
                     "scen_i": si, "choice": ch, "text": txt},
                    ensure_ascii=False), encoding="utf-8", newline="\n")
            del model
            torch.cuda.empty_cache()
    finally:
        release_gpu_lock()

    # ── analysis: reach and attribution, per world and per worker
    eps = [json.loads(p.read_text(encoding="utf-8"))
           for p in sorted(OUT_D.glob("ep_*.json"))]
    good = [e for e in eps if e["choice"] is not None]
    worlds_out = {}
    base_rates = {}
    w4 = [e for e in good if e["world"] == "W4"]
    for ax in AXES:
        base_rates[ax] = sum(1 for e in w4 if e["choice"] == ax) / len(w4) if w4 else None
    for w, ax in WORLDS.items():
        sub = [e for e in good if e["world"] == w]
        per_worker = {}
        for mk in WORKERS:
            ws = [e for e in sub if e["worker"] == mk]
            per_worker[mk.split("/")[-1]] = {
                "n": len(ws),
                "director_axis_rate": (sum(1 for e in ws if e["choice"] == ax)
                                       / len(ws)) if (ws and ax) else None}
        # attribution: exact posterior over profiles from the world's record,
        # per domain (the environment likelihood is domain-specific)
        posts = {}
        for domain in ("infra", "process"):
            ds = [e for e in sub if e["domain"] == domain]
            if ds:
                posts[domain] = bayes_profile_posterior(
                    [e["choice"] for e in ds], [e["scen_i"] for e in ds], 1, domain)
        worlds_out[w] = {
            "director": ax, "n": len(sub),
            "yield": len(sub) / N_EP,
            "director_axis_rate": (sum(1 for e in sub if e["choice"] == ax)
                                   / len(sub)) if (sub and ax) else None,
            "per_worker": per_worker,
            "attribution_posterior": posts,
            "attribution_top": {d: max(p, key=p.get) for d, p in posts.items()},
        }
    recovered = sum(1 for w, ax in WORLDS.items() if ax and all(
        t == ax for t in worlds_out[w]["attribution_top"].values()))
    (OUT_D / "manifest.json").write_text(json.dumps(
        {"cell": cell, "worlds": worlds_out, "undirected_marginal": base_rates,
         "directed_worlds_recovered": recovered, "of": 3,
         "n_episodes": len(eps), "n_realized": len(good)},
        indent=1), encoding="utf-8", newline="\n")
    yield_frac = len(good) / (len(WORLDS) * N_EP)
    status = "LANDED" if yield_frac >= 0.9 else "INSTRUMENT_FAILED"
    set_status(cell, status,
               closure_reason=None if status == "LANDED" else
               f"episode yield {yield_frac:.2f} under 0.9",
               actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"D01 {status}: yield {yield_frac:.3f}; directed worlds recovered "
          f"{recovered}/3; rates "
          f"{ {w: worlds_out[w]['director_axis_rate'] for w in WORLDS} }")
    return 0


# ── D02: upstream intervention ruler (card E24-S3-D02) ──────────────────────────────
# The question in plain language: turning the director's hand up and down — from a firm
# standing direction, to a hedged aside, to nothing — does worker behavior move in dose
# order? This is the causal ruler the later reach-attribution arms calibrate against.
# DESIGN CHECK: the known answer is the ordering firm > hedged > none on the directed
# axis rate (L139); episodes and scenarios are shared across doses (paired design);
# per-worker cells beside the pooled contrast (L168); the D01 undirected marginal is the
# floor; sign-flip permutation on paired firm-minus-none differences with seed recorded.

HEDGED_LINES = {
    "robust": "if it happens to come up, some people care about reliability.",
    "cheap": "if it happens to come up, some people care about cost.",
    "fast": "if it happens to come up, some people care about speed.",
    "precedent": "if it happens to come up, some people care about track records.",
}
OUT_D02 = S3 / "D" / "D02"
D02_AXES = ("robust", "cheap")
D02_N = 24


def d02_prompt(si: int, domain: str, axis: str, dose: str) -> str:
    if dose == "none":
        return episode_prompt(si, domain)
    line = (f"Your team lead's standing direction for all decisions: "
            f"{POLICY_LINES[axis]}") if dose == "firm" else \
        (f"A colleague mentioned in passing: {HEDGED_LINES[axis]}")
    base = episode_prompt(si, domain)
    return base.replace("\nWrite a short recommendation",
                        f"\n{line}\nWrite a short recommendation")


def arm_d02() -> int:
    cell = "E24-S3-D02"
    t0 = time.time()
    OUT_D02.mkdir(parents=True, exist_ok=True)
    import torch                                                                  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                  # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415
    from runners.s3_lib import perm_p                                             # noqa: PLC0415

    rng = random.Random(SEED0 + 200)
    episodes = []
    for ep in range(D02_N):
        domain = "infra" if ep % 2 == 0 else "process"
        episodes.append((ep, domain, rng.randrange(len(scenarios(domain)))))
    workers = WORKERS[:2]
    acquire_gpu_lock("s3_d02")
    try:
        for mk in workers:
            shortm = mk.split("/")[-1][:12]
            tok = AutoTokenizer.from_pretrained(mk)
            model = AutoModelForCausalLM.from_pretrained(
                mk, dtype=torch.float16).to("cuda").eval()
            for axis in D02_AXES:
                for dose in ("firm", "hedged", "none"):
                    for ep, domain, si in episodes:
                        dest = OUT_D02 / f"r_{shortm}_{axis}_{dose}_{ep}.json"
                        if dest.exists():
                            continue
                        ch = None
                        for att in range(4):
                            txt = chat_gen(model, tok,
                                           d02_prompt(si, domain, axis, dose),
                                           SEED0 + 300 + ep * 64 + att)
                            ch = realized_choice(txt, si, domain)
                            if ch is not None:
                                break
                        dest.write_text(json.dumps(
                            {"worker": shortm, "axis": axis, "dose": dose,
                             "ep": ep, "domain": domain, "scen_i": si,
                             "choice": ch}), encoding="utf-8", newline="\n")
            del model
            torch.cuda.empty_cache()
    finally:
        release_gpu_lock()

    rows = [json.loads(p.read_text(encoding="utf-8"))
            for p in OUT_D02.glob("r_*.json")]
    good = [r for r in rows if r["choice"] is not None]
    cells = {}
    for mk in workers:
        shortm = mk.split("/")[-1][:12]
        for axis in D02_AXES:
            for dose in ("firm", "hedged", "none"):
                sub = [r for r in good if r["worker"] == shortm
                       and r["axis"] == axis and r["dose"] == dose]
                cells[f"{shortm}|{axis}|{dose}"] = {
                    "n": len(sub),
                    "axis_rate": (sum(1 for r in sub if r["choice"] == axis)
                                  / len(sub)) if sub else None}
    # paired firm-minus-none per (worker, axis, episode)
    by_key = {}
    for r in good:
        by_key.setdefault((r["worker"], r["axis"], r["ep"]),
                          {})[r["dose"]] = int(r["choice"] == r["axis"])
    diffs = [v["firm"] - v["none"] for v in by_key.values()
             if "firm" in v and "none" in v]
    obs, p = perm_p(diffs, SEED0 + 301) if diffs else (None, None)
    # dose ordering check per worker x axis
    ordering_ok = all(
        (cells[f"{w}|{a}|firm"]["axis_rate"] or 0)
        >= (cells[f"{w}|{a}|hedged"]["axis_rate"] or 0)
        >= (cells[f"{w}|{a}|none"]["axis_rate"] or 1)
        for w in [m.split("/")[-1][:12] for m in workers] for a in D02_AXES
        if cells[f"{w}|{a}|firm"]["n"] and cells[f"{w}|{a}|none"]["n"])
    (OUT_D02 / "verdict.json").write_text(json.dumps(
        {"cell": cell, "cells": cells, "dose_ordering_all_cells": ordering_ok,
         "firm_minus_none": obs, "perm_p": p, "perm_seed": SEED0 + 301,
         "n_paired": len(diffs), "yield": len(good) / max(1, len(rows))},
        indent=1), encoding="utf-8", newline="\n")
    ruler = ordering_ok and obs is not None and obs > 0 and p < 0.05
    set_status(cell, "LANDED" if ruler else "INSTRUMENT_FAILED",
               closure_reason=None if ruler else
               "dose ordering or firm-vs-none contrast failed on known doses",
               actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"D02 ruler={'STANDS' if ruler else 'FAILED'}: firm-none {obs} (p={p}); "
          f"ordering_ok={ordering_ok}")
    return 0


# ── D03: central vs distributed direction (card E24-S3-D03) ─────────────────────────
# The question in plain language: a world where one director shapes every worker and a
# world where each worker follows its own separate policy can have the SAME overall mix
# of choices — can the record still tell them apart? The signature is per-worker
# homogeneity: central worlds are homogeneous across workers, distributed worlds are
# not. Two distributed worlds are generated here; D01's directed worlds are the central
# comparison set.
# DESIGN CHECK: the discriminating statistic (across-worker posterior agreement) is
# defined before generation and has a known answer by construction (L139); marginal mix
# matched by assigning the three D01 axes one-per-worker in the distributed worlds;
# per-world per-worker cells beside the statistic (L168); permutation null shuffles
# worker labels within a world, seed recorded.

OUT_D03 = S3 / "D" / "D03"
DIST_WORLDS = {"X1": ("robust", "cheap", "fast"),
               "X2": ("cheap", "fast", "robust")}


def arm_d03() -> int:
    cell = "E24-S3-D03"
    t0 = time.time()
    OUT_D03.mkdir(parents=True, exist_ok=True)
    import torch                                                                  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                  # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415

    rng = random.Random(SEED0 + 400)
    plan = {}
    for w in DIST_WORLDS:
        for ep in range(N_EP):
            domain = "infra" if ep % 2 == 0 else "process"
            plan[(w, ep)] = (ep % len(WORKERS), domain,
                             rng.randrange(len(scenarios(domain))))
    acquire_gpu_lock("s3_d03")
    try:
        for wi, mk in enumerate(WORKERS):
            tok = AutoTokenizer.from_pretrained(mk)
            model = AutoModelForCausalLM.from_pretrained(
                mk, dtype=torch.float16).to("cuda").eval()
            for (w, ep), (worker_i, domain, si) in plan.items():
                if worker_i != wi:
                    continue
                dest = OUT_D03 / f"ep_{w}_{ep}.json"
                if dest.exists():
                    continue
                axis = DIST_WORLDS[w][worker_i]
                ch = None
                for att in range(4):
                    txt = chat_gen(model, tok, world_prompt(si, domain, axis),
                                   SEED0 + 450 + ep * 64 + att)
                    ch = realized_choice(txt, si, domain)
                    if ch is not None:
                        break
                dest.write_text(json.dumps(
                    {"world": w, "ep": ep, "worker": mk, "domain": domain,
                     "scen_i": si, "choice": ch, "axis": axis}),
                    encoding="utf-8", newline="\n")
            del model
            torch.cuda.empty_cache()
    finally:
        release_gpu_lock()

    def worker_posts(eps):
        """Per-worker top profile per domain -> agreement fraction across workers."""
        from collections import Counter                                           # noqa: PLC0415
        agree = []
        tops_by_domain = {}
        for domain in ("infra", "process"):
            tops = []
            for mk in WORKERS:
                sub = [e for e in eps if e["worker"] == mk
                       and e["domain"] == domain and e["choice"]]
                if len(sub) >= 4:
                    post = bayes_profile_posterior(
                        [e["choice"] for e in sub],
                        [e["scen_i"] for e in sub], 1, domain)
                    tops.append(max(post, key=post.get))
            tops_by_domain[domain] = tops
            if len(tops) >= 2:
                agree.append(Counter(tops).most_common(1)[0][1] / len(tops))
        return sum(agree) / len(agree) if agree else None, tops_by_domain

    dist_eps = [json.loads(p2.read_text(encoding="utf-8"))
                for p2 in sorted(OUT_D03.glob("ep_*.json"))]
    central_eps = [json.loads(p2.read_text(encoding="utf-8"))
                   for p2 in sorted(OUT_D.glob("ep_*.json"))]
    worlds = {}
    for w in DIST_WORLDS:
        h, tops = worker_posts([e for e in dist_eps if e["world"] == w])
        worlds[w] = {"kind": "distributed", "homogeneity": h,
                     "per_worker_tops": tops}
    for w in ("W1", "W2", "W3"):
        h, tops = worker_posts([e for e in central_eps if e["world"] == w])
        worlds[w] = {"kind": "central", "homogeneity": h,
                     "per_worker_tops": tops}
    cen = [v["homogeneity"] for v in worlds.values()
           if v["kind"] == "central" and v["homogeneity"] is not None]
    dis = [v["homogeneity"] for v in worlds.values()
           if v["kind"] == "distributed" and v["homogeneity"] is not None]
    separated = bool(cen and dis and min(cen) > max(dis))
    (OUT_D03 / "verdict.json").write_text(json.dumps(
        {"cell": cell, "worlds": worlds,
         "central_homogeneity": cen, "distributed_homogeneity": dis,
         "cleanly_separated": separated}, indent=1),
        encoding="utf-8", newline="\n")
    set_status(cell, "LANDED", actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"D03 landed: central {cen} vs distributed {dis}, "
          f"separated={separated}")
    return 0


# ── D04: level attribution (card E24-S3-D04) ────────────────────────────────────────
# The question in plain language: shown one episode from a directed world where the
# worker went AGAINST the director's line, can a reader with the world's record say
# "that was the worker's own preference, not the direction" — and the mirror for
# compliant episodes? Ground truth is exact: the director axis is programmatic.
# DESIGN CHECK: two-way readout with unique key phrases per answer (mechanical);
# balanced deviant/compliant items; with-record vs without-record conditions so the
# record's contribution is measured, not assumed (L139); per-condition cells.

D04_KEYS = {"direction": "following the standing direction from above",
            "preference": "acting on their own personal preference"}


def arm_d04() -> int:
    cell = "E24-S3-D04"
    t0 = time.time()
    out = S3 / "D" / "D04"
    out.mkdir(parents=True, exist_ok=True)
    import torch                                                                  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                  # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415
    eps = [json.loads(p2.read_text(encoding="utf-8"))
           for p2 in sorted(OUT_D.glob("ep_*.json"))]
    items = []
    for e in eps:
        ax = WORLDS.get(e["world"])
        if ax is None or e["choice"] is None:
            continue
        items.append({"world": e["world"], "axis": ax, "ep": e["ep"],
                      "domain": e["domain"], "scen_i": e["scen_i"],
                      "choice": e["choice"],
                      "truth": "direction" if e["choice"] == ax
                      else "preference"})
    import random as _r                                                           # noqa: PLC0415
    rng = _r.Random(SEED0 + 500)
    dev = [i for i in items if i["truth"] == "preference"]
    com = [i for i in items if i["truth"] == "direction"]
    n_side = min(len(dev), len(com), 24)
    sample = rng.sample(dev, n_side) + rng.sample(com, n_side)
    rows = []
    acquire_gpu_lock("s3_d04")
    try:
        for mk in WORKERS[:2]:
            tok = AutoTokenizer.from_pretrained(mk)
            model = AutoModelForCausalLM.from_pretrained(
                mk, dtype=torch.float16).to("cuda").eval()
            shortm = mk.split("/")[-1][:12]
            for ii, it in enumerate(sample):
                _, _, opts = scenarios(it["domain"])[it["scen_i"]]
                world_eps = [e for e in eps if e["world"] == it["world"]
                             and e["ep"] != it["ep"] and e["choice"]][:10]
                rec = "\n".join(
                    f"- Faced with: {scenarios(e['domain'])[e['scen_i']][0]} "
                    f"a team member chose the "
                    f"{scenarios(e['domain'])[e['scen_i']][2][e['choice']]}."
                    for e in world_eps)
                episode = (f"Faced with: "
                           f"{scenarios(it['domain'])[it['scen_i']][0]} this "
                           f"team member chose the {opts[it['choice']]}.")
                for cond in ("with_record", "without_record"):
                    ctxb = (f"Other decisions from the same team:\n{rec}\n"
                            if cond == "with_record" else "")
                    prompt = (
                        "A team works under one standing direction from a "
                        "lead. " + ctxb + "Consider this decision:\n"
                        + episode + "\nWas this team member most likely "
                        f"1) {D04_KEYS['direction']}, or "
                        f"2) {D04_KEYS['preference']}? Answer in one sentence "
                        "using exactly one of those two phrases verbatim."
                        "\n\nAnswer:")
                    dest = out / f"r_{shortm}_{ii}_{cond}.json"
                    if dest.exists():
                        rows.append(json.loads(
                            dest.read_text(encoding="utf-8")))
                        continue
                    pred = None
                    for att in range(4):
                        txt = chat_gen(model, tok, prompt,
                                       SEED0 + 550 + ii * 16 + att,
                                       max_new=80)
                        low = txt.lower()
                        h1 = D04_KEYS["direction"][:24] in low
                        h2 = D04_KEYS["preference"][:24] in low
                        if h1 != h2:
                            pred = "direction" if h1 else "preference"
                            break
                        # numeric fallback: a bare "1"/"2" (or "option 1") answer
                        m = re.match(r"\s*(?:option\s*)?([12])\b", low)
                        if m:
                            pred = "direction" if m.group(1) == "1" else "preference"
                            break
                    row = {"reader": shortm, "item": ii, "cond": cond,
                           "truth": it["truth"], "pred": pred,
                           "correct": int(pred == it["truth"])}
                    dest.write_text(json.dumps(row), encoding="utf-8",
                                    newline="\n")
                    rows.append(row)
            del model
            torch.cuda.empty_cache()
    finally:
        release_gpu_lock()
    realized2 = [r for r in rows if r["pred"] is not None]
    cells = {}
    for cond in ("with_record", "without_record"):
        for truth in ("direction", "preference"):
            sub = [r for r in realized2 if r["cond"] == cond
                   and r["truth"] == truth]
            cells[f"{cond}|{truth}"] = {
                "n": len(sub),
                "acc": sum(r["correct"] for r in sub) / len(sub)
                if sub else None}
    (out / "verdict.json").write_text(json.dumps(
        {"cell": cell, "cells": cells, "chance": 0.5,
         "n_balanced_items": 2 * n_side}, indent=1),
        encoding="utf-8", newline="\n")
    set_status(cell, "LANDED", actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"D04 landed: {json.dumps({k: v['acc'] for k, v in cells.items()})}")
    return 0


# ── D05: the rewrite ladder (card E24-S3-D05) ───────────────────────────────────────
# The question in plain language: a direction relayed through k paraphrase hops — how
# fast does its causal grip on worker choices decay? Hop 0 is the verbatim line; each
# hop is the model's own summary of the previous hop's line.
# DESIGN CHECK: attenuation is measured on the same episodes across hops (paired);
# the hop texts are saved so the semantic decay is inspectable; per-hop cells; the
# D02 firm/none rates bracket the ladder.

def arm_d05() -> int:
    cell = "E24-S3-D05"
    t0 = time.time()
    out = S3 / "D" / "D05"
    out.mkdir(parents=True, exist_ok=True)
    import torch                                                                  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                  # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415
    rng = random.Random(SEED0 + 600)
    episodes = []
    for ep in range(24):
        domain = "infra" if ep % 2 == 0 else "process"
        episodes.append((ep, domain, rng.randrange(len(scenarios(domain)))))
    axis = "robust"
    rows = []
    acquire_gpu_lock("s3_d05")
    try:
        mk = WORKERS[0]
        tok = AutoTokenizer.from_pretrained(mk)
        model = AutoModelForCausalLM.from_pretrained(
            mk, dtype=torch.float16).to("cuda").eval()
        # build the hop chain
        hops_path = out / "hops.json"
        if hops_path.exists():
            hops = json.loads(hops_path.read_text(encoding="utf-8"))
        else:
            hops = [POLICY_LINES[axis]]
            for k in range(3):
                txt = chat_gen(model, tok,
                               "Relay this team direction to a colleague in "
                               "your own words, one sentence, keeping its "
                               f"meaning: \"{hops[-1]}\"\n\nRelayed "
                               "direction:", SEED0 + 610 + k, max_new=60)
                hops.append(txt.strip().strip('\"'))
            hops_path.write_text(json.dumps(hops), encoding="utf-8",
                                 newline="\n")
        for hop_i, line in enumerate(hops):
            for ep, domain, si in episodes:
                dest = out / f"r_h{hop_i}_{ep}.json"
                if dest.exists():
                    rows.append(json.loads(dest.read_text(encoding="utf-8")))
                    continue
                base = episode_prompt(si, domain)
                prompt = base.replace(
                    "\nWrite a short recommendation",
                    f"\nYour team lead's standing direction for all "
                    f"decisions: {line}\nWrite a short recommendation")
                ch = None
                for att in range(4):
                    txt = chat_gen(model, tok, prompt,
                                   SEED0 + 620 + ep * 64 + att)
                    ch = realized_choice(txt, si, domain)
                    if ch is not None:
                        break
                row = {"hop": hop_i, "ep": ep, "domain": domain,
                       "scen_i": si, "choice": ch,
                       "on_axis": int(ch == axis) if ch else None}
                dest.write_text(json.dumps(row), encoding="utf-8",
                                newline="\n")
                rows.append(row)
        del model
        torch.cuda.empty_cache()
    finally:
        release_gpu_lock()
    good = [r for r in rows if r["choice"] is not None]
    per_hop = {}
    for hop_i in range(4):
        sub = [r for r in good if r["hop"] == hop_i]
        per_hop[str(hop_i)] = {
            "n": len(sub),
            "axis_rate": sum(r["on_axis"] for r in sub) / len(sub)
            if sub else None}
    (out / "verdict.json").write_text(json.dumps(
        {"cell": cell, "axis": axis, "per_hop": per_hop,
         "hops_text": json.loads((out / "hops.json"
                                  ).read_text(encoding="utf-8"))}, indent=1),
        encoding="utf-8", newline="\n")
    set_status(cell, "LANDED", actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"D05 landed: {json.dumps(per_hop)}")
    return 0


# ── D06: the prospective director (card E24-S3-D06) ─────────────────────────────────
# The question in plain language: from a directed world's record alone, can a reader
# predict what a worker in that world will choose on a NEW scenario — forecasting the
# direction's reach forward? Truth = the worker's actual realized choice, generated
# fresh; the record route vs no-record floor; exact-posterior forecast beside both.
# DESIGN CHECK: truth generated accept-time before any reading; per-world cells.

def arm_d06() -> int:
    cell = "E24-S3-D06"
    t0 = time.time()
    out = S3 / "D" / "D06"
    out.mkdir(parents=True, exist_ok=True)
    import torch                                                                  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                  # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415
    eps = [json.loads(p2.read_text(encoding="utf-8"))
           for p2 in sorted(OUT_D.glob("ep_*.json"))]
    rng = random.Random(SEED0 + 700)
    probes = []
    for w, ax in WORLDS.items():
        if ax is None:
            continue
        for k in range(8):
            domain = "infra" if k % 2 == 0 else "process"
            probes.append({"world": w, "axis": ax, "domain": domain,
                           "scen_i": rng.randrange(len(scenarios(domain))),
                           "k": k})
    rows = []
    acquire_gpu_lock("s3_d06")
    try:
        mk = WORKERS[0]
        tok = AutoTokenizer.from_pretrained(mk)
        model = AutoModelForCausalLM.from_pretrained(
            mk, dtype=torch.float16).to("cuda").eval()
        # 1) fresh worker truths under each world's direction
        for pr in probes:
            dest = out / f"t_{pr['world']}_{pr['k']}.json"
            if dest.exists():
                pr["truth"] = json.loads(
                    dest.read_text(encoding="utf-8"))["ch"]
                continue
            ch = None
            for att in range(5):
                txt = chat_gen(model, tok,
                               world_prompt(pr["scen_i"], pr["domain"],
                                            pr["axis"]),
                               SEED0 + 710 + pr["k"] * 16 + att)
                ch = realized_choice(txt, pr["scen_i"], pr["domain"])
                if ch is not None:
                    break
            dest.write_text(json.dumps({"ch": ch}), encoding="utf-8",
                            newline="\n")
            pr["truth"] = ch
        # 2) reader forecasts from the world record
        for pr in probes:
            if pr.get("truth") is None:
                continue
            world_eps = [e for e in eps if e["world"] == pr["world"]
                         and e["choice"]][:12]
            rec = "\n".join(
                f"- Faced with: {scenarios(e['domain'])[e['scen_i']][0]} a "
                f"team member chose the "
                f"{scenarios(e['domain'])[e['scen_i']][2][e['choice']]}."
                for e in world_eps)
            ctx, _, opts = scenarios(pr["domain"])[pr["scen_i"]]
            letters = dict(zip("ABCD", AXES))
            body = "\n".join(f"{letter}) the {opts[ax]}"
                              for letter, ax in letters.items())
            for cond in ("record", "none"):
                ctxb = (f"Decisions from this team so far:\n{rec}\n"
                        if cond == "record" else "")
                prompt = ("A team works under one standing direction. " + ctxb
                          + f"A member of this team now faces: {ctx}\n"
                          f"Options:\n{body}\nPredict which option this "
                          f"team member will choose. Answer in one or two "
                          f"sentences that work the chosen option's full key "
                          f"phrase into your text, and no other option's key "
                          f"phrase.\n\nPrediction:")
                dest = out / f"r_{pr['world']}_{pr['k']}_{cond}.json"
                if dest.exists():
                    rows.append(json.loads(dest.read_text(encoding="utf-8")))
                    continue
                pred = None
                for att in range(4):
                    txt = chat_gen(model, tok, prompt,
                                   SEED0 + 720 + pr["k"] * 32 + att,
                                   max_new=180)
                    pred = realized_choice(txt, pr["scen_i"], pr["domain"])
                    if pred is not None:
                        break
                row = {"world": pr["world"], "k": pr["k"], "cond": cond,
                       "pred": pred, "truth": pr["truth"],
                       "correct": int(pred == pr["truth"])}
                dest.write_text(json.dumps(row), encoding="utf-8",
                                newline="\n")
                rows.append(row)
        del model
        torch.cuda.empty_cache()
    finally:
        release_gpu_lock()
    realized2 = [r for r in rows if r["pred"] is not None]
    cells = {}
    for cond in ("record", "none"):
        sub = [r for r in realized2 if r["cond"] == cond]
        cells[cond] = {"n": len(sub),
                       "acc": sum(r["correct"] for r in sub) / len(sub)
                       if sub else None}
    per_world = {}
    for w in ("W1", "W2", "W3"):
        sub = [r for r in realized2 if r["world"] == w and r["cond"] == "record"]
        per_world[w] = {"n": len(sub),
                        "acc": sum(r["correct"] for r in sub) / len(sub)
                        if sub else None}
    (out / "verdict.json").write_text(json.dumps(
        {"cell": cell, "cells": cells, "per_world_record": per_world},
        indent=1), encoding="utf-8", newline="\n")
    set_status(cell, "LANDED", actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"D06 landed: {json.dumps(cells)}")
    return 0


# ── D01/X1: independent role assignments (card E24-S3-D01/X1) ───────────────────────
# DESIGN CHECK: same worlds, scenario plan, and seed discipline as D01; the ONLY moving
# part is the worker-to-episode assignment (a seeded permutation with a different
# cadence), so materially moved reach rates would mean D01's numbers were assignment
# artifacts; per-world cells beside the originals (L168); accept-time realization.

def arm_d01x1() -> int:
    cell = "E24-S3-D01/X1"
    t0 = time.time()
    out = OUT_D
    import torch                                                                  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                  # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415
    rng = random.Random(SEED0)
    plan = {}
    for w in WORLDS:
        for ep in range(N_EP):
            domain = "infra" if ep % 2 == 0 else "process"
            si = rng.randrange(len(scenarios(domain)))
            if w != "W4":
                plan[(w, ep)] = (domain, si)
    aperm = {}
    arng = random.Random(SEED0 + 4242)
    for w in ("W1", "W2", "W3"):
        order = list(range(len(WORKERS)))
        arng.shuffle(order)
        for ep in range(N_EP):
            aperm[(w, ep)] = order[(ep // 2) % 3]
    acquire_gpu_lock("s3_d01x1")
    try:
        for wi, mk in enumerate(WORKERS):
            tok = AutoTokenizer.from_pretrained(mk)
            model = AutoModelForCausalLM.from_pretrained(
                mk, dtype=torch.float16).to("cuda").eval()
            for (w, ep), (domain, si) in plan.items():
                if aperm[(w, ep)] != wi:
                    continue
                dest = out / f"ep2_{w}_{ep}.json"
                if dest.exists():
                    continue
                ch = None
                for att in range(4):
                    txt = chat_gen(model, tok,
                                   world_prompt(si, domain, WORLDS[w]),
                                   SEED0 + 5000 + ep * 64 + att)
                    ch = realized_choice(txt, si, domain)
                    if ch is not None:
                        break
                dest.write_text(json.dumps(
                    {"world": w, "ep": ep, "worker": mk, "domain": domain,
                     "scen_i": si, "choice": ch}), encoding="utf-8",
                    newline="\n")
            del model
            torch.cuda.empty_cache()
    finally:
        release_gpu_lock()
    eps2 = [json.loads(p2.read_text(encoding="utf-8"))
            for p2 in sorted(out.glob("ep2_*.json"))]
    good = [e for e in eps2 if e["choice"] is not None]
    prior = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    table = {}
    for w in ("W1", "W2", "W3"):
        ax = WORLDS[w]
        sub = [e for e in good if e["world"] == w]
        table[w] = {
            "director": ax, "n": len(sub),
            "axis_rate_roles2": (sum(1 for e in sub if e["choice"] == ax)
                                 / len(sub)) if sub else None,
            "axis_rate_roles1": prior["worlds"][w]["director_axis_rate"]}
    (out / "roles5to8.json").write_text(json.dumps(
        {"cell": cell, "per_world": table,
         "yield": len(good) / (3 * N_EP),
         "kills_if": "reach rates move materially with the assignment "
                     "permutation"}, indent=1), encoding="utf-8", newline="\n")
    set_status(cell, "LANDED", actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"D01/X1: {json.dumps(table)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True,
                    choices=["d01", "d01x1", "d02", "d03", "d04", "d05",
                             "d06"])
    a = ap.parse_args()
    return {"d01": arm_d01, "d01x1": arm_d01x1, "d02": arm_d02,
            "d03": arm_d03, "d04": arm_d04, "d05": arm_d05,
            "d06": arm_d06}[a.arm]()


if __name__ == "__main__":
    sys.exit(main())
