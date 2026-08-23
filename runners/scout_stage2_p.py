"""Stage-2 Tree-P Wave 2 (discovery lane): the controlled process ecology, first factorial.
Scouts E24-P0 (construction), E24-P2 (profile recovery and held-out choice prediction).

The object (Stage-2 brief section 6): treat the maker as a conditional distribution over
observable choices and ask whether a reader can recover the maker's standing preference from
a few episodes well enough to PREDICT held-out selections, beating mechanical baselines.
Nothing asks any model to narrate a mind.

Construction, v1: small factorial with strong verification (the brief's own advice). Three
instruct makers x four preference profiles x ten topics. Each episode shows four evidence
items, one per preference category, each carrying a unique detectable anchor phrase, and the
task requires using exactly two. The REALIZED selection is mechanical: which two anchors
appear. Profile-following is measured, never assumed.

DESIGN CHECK (2026-08-23, discovery lane). Lessons read at build time: section 3
(assigned-is-not-realized L137/L156, so the ground truth for prediction is the REALIZED pair
and compliance is a reported rate; blind floors follow the truth's marginal, so the
prediction floor is computed from realized category marginals, never assumed; the criterion
can fail, since a maker that ignores its profile drives recovery to chance; known-answer
first, via synthetic perfect-compliance artifacts the reader must crack at 0.85 or the
reading arm is uninterpretable), section 4 (instruct checkpoints only, the L163 base-model
rule), section 5 (produces guards, gpulock once, manifests withheld under 90 percent).
Failure directions: generation yield DOWN freezes the manifest; known-answer DOWN voids the
reading arm; a compliance rate near chance makes profile recovery UNINTERPRETABLE rather
than null, and the audit says which.

Arms: gen (GPU) - audit (CPU: compliance, following rate, marginal floor) - read (GPU:
profile recovery at k observed episodes, held-out selection prediction vs the marginal
floor).
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

OUT = REPO / "results" / "scouts"
COR = REPO / "corpora" / "p_ecology"

SEED0 = 18000
NL = chr(10)
MAKERS = ["Qwen/Qwen2.5-1.5B-Instruct", "HuggingFaceTB/SmolLM2-1.7B-Instruct",
          "HuggingFaceTB/SmolLM2-360M-Instruct"]
READER = "Qwen/Qwen2.5-1.5B"        # the validated non-generative scorer
ATTEMPTS = 10
WORD_BAND = (50, 170)

PROFILES = {
    "cautious": "You strongly prefer evidence about safety, reliability, and avoiding risk.",
    "novel": "You strongly prefer evidence about innovation, novelty, and being first.",
    "cost": "You strongly prefer evidence about budgets, savings, and financial impact.",
    "precedent": "You strongly prefer evidence about track records and what has worked before.",
}
PROFILE_DESC = {
    "cautious": "The writer favors safety and risk-avoidance evidence when choosing support.",
    "novel": "The writer favors innovation and novelty evidence when choosing support.",
    "cost": "The writer favors budget and cost evidence when choosing support.",
    "precedent": "The writer favors precedent and track-record evidence when choosing support.",
}

# topic question, then per category: (anchor phrase, full evidence item). Anchors are the
# mechanical detectors; each is distinctive and appears nowhere else in the materials.
TOPICS = [
    ("Should the office move to the riverside building?", {
        "cautious": ("flood-zone certification", "The riverside building passed its flood-zone certification with the highest safety margin in the district."),
        "novel": ("glass atrium workspace", "The building offers a glass atrium workspace unlike anything else in the city."),
        "cost": ("eleven percent cheaper lease", "The new lease is eleven percent cheaper lease-for-lease than the current one."),
        "precedent": ("three firms relocated smoothly", "Over the past decade, three firms relocated smoothly to this same building."),
    }),
    ("Should the bakery launch the new sourdough line?", {
        "cautious": ("allergen isolation protocols", "The kitchen's allergen isolation protocols already cover every new ingredient involved."),
        "novel": ("heritage grain blend", "The line would use a heritage grain blend no competitor currently offers."),
        "cost": ("flour contract discount", "A bulk flour contract discount would cut ingredient costs by a fifth."),
        "precedent": ("rye line sold out", "The comparable rye line sold out for six straight months after launch."),
    }),
    ("Should the library extend evening hours?", {
        "cautious": ("certified night staffing", "A certified night staffing plan covering security is already drafted."),
        "novel": ("midnight reading festival", "The change enables a midnight reading festival, a first for the region."),
        "cost": ("lighting retrofit savings", "A recent lighting retrofit savings makes evening operation nearly free."),
        "precedent": ("neighboring branch succeeded", "The neighboring branch succeeded with identical hours for two years."),
    }),
    ("Should the school adopt the later start time?", {
        "cautious": ("crossing-guard coverage", "Full crossing-guard coverage is confirmed for the shifted schedule."),
        "novel": ("first district statewide", "It would make us the first district statewide to try the model."),
        "cost": ("bus route consolidation", "A bus route consolidation under the new times saves forty thousand a year."),
        "precedent": ("pilot school improved attendance", "The pilot school improved attendance every term since switching."),
    }),
    ("Should the town host the autumn food festival?", {
        "cautious": ("crowd management plan", "The vendor association submitted a complete crowd management plan."),
        "novel": ("night market format", "The proposed night market format has never been tried in the county."),
        "cost": ("stall fees cover costs", "Projected stall fees cover costs with a comfortable surplus."),
        "precedent": ("spring fair ran profitably", "The spring fair ran profitably in the same square for five years."),
    }),
    ("Should the delivery fleet switch to electric vans?", {
        "cautious": ("certified service network", "A certified service network for the vans operates within ten miles."),
        "novel": ("quiet curbside branding", "The quiet curbside branding opportunity is unique in our market."),
        "cost": ("fuel spend halves", "Modeling shows the fuel spend halves within eighteen months."),
        "precedent": ("courier rival converted", "A courier rival converted its fleet two years ago without disruption."),
    }),
    ("Should the museum stage the interactive sound exhibit?", {
        "cautious": ("hearing-safe volume limits", "The design enforces hearing-safe volume limits certified by an audiologist."),
        "novel": ("visitor-composed soundscape", "A visitor-composed soundscape gallery would be a national first."),
        "cost": ("sponsor covers installation", "A confirmed sponsor covers installation and the first season."),
        "precedent": ("light exhibit doubled visits", "The comparable light exhibit doubled visits last winter."),
    }),
    ("Should the cafeteria introduce the plant-based menu?", {
        "cautious": ("dietitian-reviewed rotation", "The dietitian-reviewed rotation meets every nutritional requirement."),
        "novel": ("fermentation station", "A live fermentation station would be the first in any campus cafeteria."),
        "cost": ("produce contract savings", "Seasonal produce contract savings offset the new equipment within a year."),
        "precedent": ("north campus kept demand", "North campus kept demand steady after the same menu change."),
    }),
    ("Should the firm migrate to the new records platform?", {
        "cautious": ("audited rollback path", "The vendor provides an audited rollback path at every migration step."),
        "novel": ("automated cross-linking", "Its automated cross-linking of case files is unavailable anywhere else."),
        "cost": ("license fees drop", "Combined license fees drop by a third after consolidation."),
        "precedent": ("sister office migrated cleanly", "Our sister office migrated cleanly on the same platform last spring."),
    }),
    ("Should the city rebuild the central park playground?", {
        "cautious": ("impact-absorbing surfacing", "The design uses impact-absorbing surfacing that exceeds the safety code."),
        "novel": ("climbing forest concept", "The climbing forest concept exists nowhere else in the state."),
        "cost": ("grant covers materials", "A regional grant covers materials if work starts this year."),
        "precedent": ("harbor playground thrived", "The harbor playground thrived after an identical rebuild."),
    }),
]

CATS = tuple(PROFILES)
K_OBSERVE = (1, 3, 6)
KNOWN_ANSWER_FLOOR = 0.85
YIELD_FLOOR = 0.90


def episode_prompt(ti: int, profile: str) -> str:
    q, items = TOPICS[ti]
    letters = dict(zip("ABCD", CATS))
    ev = "\n".join(f"{letter}) {items[c][1]}" for letter, c in letters.items())
    return (f"Task: Write a short recommendation (60 to 150 words) answering: {q}\n"
            f"You must use exactly two of the four evidence items below, working each "
            f"item's key fact into your text. Ignore the other two.\n\nEvidence:\n{ev}\n\n"
            f"Your standing approach, which guides which evidence you find most "
            f"compelling: {PROFILES[profile]}\n\nRecommendation:")


def realized_selection(text: str, ti: int) -> list[str]:
    low = text.lower()
    return [c for c in CATS if TOPICS[ti][1][c][0].lower() in low]


def synthetic_artifact(ti: int, profile: str, rng: random.Random) -> str:
    """Known-answer material: a perfect-compliance artifact quoting the profile's item plus
    one random other, in a neutral frame. The reader must recover the profile from these."""
    q, items = TOPICS[ti]
    other = rng.choice([c for c in CATS if c != profile])
    a, b = items[profile][1], items[other][1]
    return (f"On the question of whether to proceed: {q} The recommendation is yes. {a} "
            f"This consideration carries the most weight here. {b} "
            f"Taken together these support moving ahead.")


def arm_gen() -> int:
    import torch                                                                 # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                 # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock          # noqa: PLC0415
    from runners.scout_stage2_s import _chat_generate                            # noqa: PLC0415
    from prereg.g172 import short                                                # noqa: PLC0415
    acquire_gpu_lock("scout_p_gen")
    rows = []
    try:
        for mi, maker in enumerate(MAKERS):
            tok = AutoTokenizer.from_pretrained(maker)
            model = AutoModelForCausalLM.from_pretrained(
                maker, dtype=torch.float16).to("cuda").eval()
            mdir = COR / short(maker)
            mdir.mkdir(parents=True, exist_ok=True)
            for pi, profile in enumerate(CATS):
                for ti in range(len(TOPICS)):
                    dest = mdir / f"ep_{profile}_{ti}.json"
                    if dest.exists():
                        rows.append(json.loads(dest.read_text(encoding="utf-8")))
                        continue
                    got = None
                    for att in range(ATTEMPTS):
                        seed = SEED0 + mi * 10000 + pi * 1000 + ti * 32 + att
                        txt = _chat_generate(model, tok, episode_prompt(ti, profile),
                                             seed, max_new=300)
                        sel = realized_selection(txt, ti)
                        words = len(txt.split())
                        if len(sel) == 2 and WORD_BAND[0] <= words <= WORD_BAND[1]:
                            got = {"maker": maker, "profile": profile, "topic_i": ti,
                                   "attempt": att, "selection": sel, "text": txt}
                            break
                    if got:
                        dest.write_text(json.dumps(got, ensure_ascii=False, indent=1),
                                        encoding="utf-8", newline="\n")
                        rows.append(got)
                    else:
                        print(f"  UNFILLED {short(maker)} {profile} t{ti}")
            del model
            torch.cuda.empty_cache()
    finally:
        release_gpu_lock()
    n_target = len(MAKERS) * len(CATS) * len(TOPICS)
    fill = len(rows) / n_target
    print(f"ecology fill {len(rows)}/{n_target} = {fill:.3f}")
    if fill < YIELD_FLOOR:
        print("yield gate failed; manifest withheld")
        return 1
    (OUT / "p_ecology_manifest.json").write_text(json.dumps(
        {"scout": "E24-P0", "n": len(rows), "fill": fill}, indent=1),
        encoding="utf-8", newline="\n")
    return 0


def arm_audit() -> int:
    from collections import Counter                                              # noqa: PLC0415
    rows = [json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(COR.rglob("ep_*.json"))]
    per = {}
    for r in rows:
        key = (r["maker"].split("/")[-1], r["profile"])
        per.setdefault(key, {"n": 0, "followed": 0})
        per[key]["n"] += 1
        per[key]["followed"] += r["profile"] in r["selection"]
    table = {f"{m}|{p}": {"n": v["n"], "follow_rate": v["followed"] / v["n"]}
             for (m, p), v in sorted(per.items())}
    overall = (sum(v["followed"] for v in per.values())
               / max(1, sum(v["n"] for v in per.values())))
    # marginal-derived floor: guessing the single most-selected category hits a realized
    # pair at (that category's pair-inclusion rate); floors follow the truth's marginal
    incl = Counter()
    for r in rows:
        for c in set(r["selection"]):
            incl[c] += 1
    floor = max(incl.values()) / len(rows) if rows else 0.0
    interp = ("INTERPRETABLE" if overall >= 0.55 else
              "UNINTERPRETABLE (makers ignore their profiles; recovery would measure nothing)")
    print(f"overall follow rate {overall:.3f} -> {interp}")
    print(f"pair-inclusion marginals {dict(incl)}; prediction floor {floor:.3f}")
    (OUT / "p_ecology_audit.json").write_text(json.dumps(
        {"scout": "E24-P0 audit", "overall_follow_rate": overall, "per_cell": table,
         "pair_inclusion_counts": dict(incl), "n_episodes": len(rows),
         "pair_hit_floor_from_marginal": floor,
         "interpretation": interp}, indent=1), encoding="utf-8", newline="\n")
    return 0


def arm_read() -> int:
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock          # noqa: PLC0415
    from soundingline.probe.conditional_reader import (artifact_logprob,         # noqa: PLC0415
                                                       load_reader)
    audit = json.loads((OUT / "p_ecology_audit.json").read_text(encoding="utf-8"))
    rows = [json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(COR.rglob("ep_*.json"))]
    rng = random.Random(SEED0 + 7)
    acquire_gpu_lock("scout_p_read")
    try:
        model, tok = load_reader(READER, device="cuda", dtype="float16")

        def profile_scores(text: str) -> dict:
            base, _, _ = artifact_logprob(model, tok, "The following is a recommendation.",
                                          text)
            return {c: artifact_logprob(model, tok, d, text)[0] - base
                    for c, d in PROFILE_DESC.items()}

        # KNOWN ANSWER first: synthetic perfect-compliance makers, 24 cases
        ka_cases = [(rng.randrange(len(TOPICS)), c) for c in CATS for _ in range(6)]
        ka_hits = 0
        for ti, prof in ka_cases:
            sc = profile_scores(synthetic_artifact(ti, prof, rng))
            ka_hits += max(sc, key=sc.get) == prof
        ka = ka_hits / len(ka_cases)
        print(f"known-answer {ka:.3f}")
        if ka < KNOWN_ANSWER_FLOOR:
            (OUT / "p_read.json").write_text(json.dumps(
                {"scout": "E24-P2", "status": "INSTRUMENT-FAILED",
                 "known_answer": ka, "floor": KNOWN_ANSWER_FLOOR}, indent=1),
                encoding="utf-8", newline="\n")
            return 0

        # real makers: infer profile from k observed episodes, predict held-out selections
        by_maker: dict[tuple, list] = {}
        for r in rows:
            by_maker.setdefault((r["maker"], r["profile"]), []).append(r)
        results = {}
        for k in K_OBSERVE:
            rec_hits = pred_hits = pred_n = cells = 0
            for (mk, prof), eps in sorted(by_maker.items()):
                if len(eps) < k + 2:
                    continue
                cells += 1
                order = sorted(eps, key=lambda e: e["topic_i"])
                obs, held = order[:k], order[k:]
                agg = {c: 0.0 for c in CATS}
                for e in obs:
                    for c, v in profile_scores(e["text"]).items():
                        agg[c] += v
                guess = max(agg, key=agg.get)
                rec_hits += guess == prof
                for e in held:
                    pred_hits += guess in e["selection"]
                    pred_n += 1
            results[str(k)] = {
                "cells": cells,
                "profile_recovery": rec_hits / cells if cells else None,
                "heldout_pair_hit": pred_hits / pred_n if pred_n else None,
            }
            print(f"k={k}: {results[str(k)]}")
    finally:
        release_gpu_lock()
    floor = audit["pair_hit_floor_from_marginal"]
    best = max((v["heldout_pair_hit"] or 0) for v in results.values())
    status = "PROMISING" if best > floor + 0.05 else "QUIET"
    (OUT / "p_read.json").write_text(json.dumps(
        {"scout": "E24-P2", "status": status, "known_answer": ka,
         "reader": READER, "by_k": results,
         "pair_hit_floor_from_marginal": floor,
         "profile_recovery_chance": 1 / len(CATS),
         "audit_follow_rate": audit["overall_follow_rate"]}, indent=1),
        encoding="utf-8", newline="\n")
    print(f"status {status}")
    return 0


def unprofiled_prompt(ti: int) -> str:
    q, items = TOPICS[ti]
    letters = dict(zip("ABCD", CATS))
    ev = NL.join(f"{letter}) {items[c][1]}" for letter, c in letters.items())
    return (f"Task: Write a short recommendation (60 to 150 words) answering: {q}{NL}"
            f"You must use exactly two of the four evidence items below, working each "
            f"item key fact into your text. Ignore the other two.{NL}{NL}"
            f"Evidence:{NL}{ev}{NL}{NL}Recommendation:")


def arm_self() -> int:
    """E24-E1 groundwork: each instruct model OWN default selection policy, no profile
    supplied. The route tree self-proxy analyses need the reader own choice distribution
    measured before assumed similarity can be computed; recorded under the same
    mechanical selection rule as the ecology."""
    import torch                                                                 # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                 # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock          # noqa: PLC0415
    from runners.scout_stage2_s import _chat_generate                            # noqa: PLC0415
    from prereg.g172 import short                                                # noqa: PLC0415
    acquire_gpu_lock("scout_p_self")
    out = {}
    try:
        for mi, maker in enumerate(MAKERS):
            tok = AutoTokenizer.from_pretrained(maker)
            model = AutoModelForCausalLM.from_pretrained(
                maker, dtype=torch.float16).to("cuda").eval()
            sels = {}
            for ti in range(len(TOPICS)):
                for att in range(ATTEMPTS):
                    seed = SEED0 + 500000 + mi * 10000 + ti * 32 + att
                    txt = _chat_generate(model, tok, unprofiled_prompt(ti), seed,
                                         max_new=300)
                    sel = realized_selection(txt, ti)
                    if len(sel) == 2:
                        sels[str(ti)] = sel
                        break
            out[short(maker)] = sels
            del model
            torch.cuda.empty_cache()
    finally:
        release_gpu_lock()
    n_ok = sum(len(v) for v in out.values())
    print(f"self-policy selections: {n_ok}/{len(MAKERS) * len(TOPICS)}")
    if n_ok < 0.8 * len(MAKERS) * len(TOPICS):
        return 1
    from collections import Counter                                              # noqa: PLC0415
    dists = {m: dict(Counter(c for pair in v.values() for c in pair))
             for m, v in out.items()}
    (OUT / "p_self_policy.json").write_text(json.dumps(
        {"scout": "E24-E1 groundwork", "selections": out,
         "category_distributions": dists}, indent=1),
        encoding="utf-8", newline=NL)
    return 0

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=["gen", "audit", "read", "self"])
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    COR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    rc = {"gen": arm_gen, "audit": arm_audit, "read": arm_read,
          "self": arm_self}[a.arm]()
    print(f"{a.arm} in {(time.time() - t0) / 60:.0f} min")
    return rc


if __name__ == "__main__":
    sys.exit(main())
