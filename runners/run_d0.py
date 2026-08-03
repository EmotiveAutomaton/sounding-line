"""D-0 — the two-hour test that decides whether option D is real.

── THE QUESTION ──────────────────────────────────────────────────────────────────────────────

Option D inverts a generative model of maker → artifact. `ghost-scale-sim` already implements the
inversion; the gap is one function, text → feature vector, and `docs/theory/LEAKAGE.md` argues
function-word distributions are that vector.

That argument is worthless unless:

> **D-0. Do function-word vectors separate artifacts written under DIFFERENT SPECIFIED MAKER
> STATES?**

If yes, the emission model exists and D is engineering. If no, function words carry maker
IDENTITY but not maker STATE, the feature channel is wrong, and D dies for two hours of compute
instead of two weeks.

This is N28 discipline applied before a build rather than after one.

── PRE-REGISTERED, BEFORE THE RUN ────────────────────────────────────────────────────────────

  PASS      mean between/within variance ratio > 1.5 across states, AND at least three categories
            individually above 2.0. One category above threshold is a lexical artefact of the
            state description leaking into the prompt; three is a profile.
  FAIL      ratio at or below 1.0. Function words do not track state.
  AMBIGUOUS in between — report as ambiguous and do not proceed on it.

  The states are crossed, not sampled, so no state is over-represented.

  CONFOUND, AND IT IS THE ONE THAT MATTERS: the topic is held FIXED across every cell. If topic
  varied with state, separation would be topic separation wearing a costume, and function words
  are supposed to be the topic-independent channel — so letting topic vary would destroy the
  only property that makes them worth using.

── AND THE SECOND READING, WHICH IS NOT OPTIONAL ─────────────────────────────────────────────

A pass here is a pass on MACHINE-GENERATED text. E38 says a machine-matched reader reads machine
content far better than human content, and the generative analogue is that a model's own emissions
may be more separable than a person's. So a D-0 pass licenses building D; it does not license
believing D will work on human artifacts. That needs the same test against human text with
known-ish states, which is what the curator's reading sessions are for.
"""

from __future__ import annotations

import argparse
import itertools
import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from soundingline.measures.leakage import profile, separability   # noqa: E402
from soundingline.probe.client import make_client                 # noqa: E402

RESULTS = REPO / "results" / "d0"

# Topic held FIXED. Chosen to be answerable under every state without strain — a topic that fights
# one of the states would produce separation from the fight rather than from the state.
TOPIC = ("how a small team decided which parts of an old internal tool to rewrite and which "
         "to leave alone")

PURPOSES = ("inform", "persuade", "sell", "entertain")
AFFECTS = ("seeking", "rage", "fear", "care")

SYSTEM = ("You are writing a short piece of real prose. Write it as the described person would "
          "have written it. Do not describe the person, do not mention their goal or their state, "
          "and do not use the words given to you. Just write the piece. 250-350 words, no "
          "headings, no lists.")

PROMPT = ("Write a short piece about {topic}.\n\n"
          "The person writing it is trying to {purpose_gloss} They are, while writing, "
          "{affect_gloss}\n\n"
          "Write only the piece.")

PURPOSE_GLOSS = {
    "inform": "pass on something the reader did not know, for the reader's benefit.",
    "persuade": "move the reader's position on something they hold a stake in.",
    "sell": "cause the reader to buy something.",
    "entertain": "hold the reader's attention as an end in itself.",
}
AFFECT_GLOSS = {
    "seeking": "absorbed and curious, enjoying working the problem out.",
    "rage": "irritated and aggrieved about how things went.",
    "fear": "anxious about being judged, covering every base they can think of.",
    "care": "concerned that the reader succeeds, and spending effort to make it land.",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    # Local by default: no API key is configured, and 48 short generations against a Gate 3 run
    # that has eleven hours left is about 3% contention. Cheap enough to just pay.
    ap.add_argument("--arm", default="local")
    ap.add_argument("--k", type=int, default=3, help="samples per cell")
    ap.add_argument("--purposes", type=int, default=len(PURPOSES))
    ap.add_argument("--affects", type=int, default=len(AFFECTS))
    args = ap.parse_args()

    cells = list(itertools.product(PURPOSES[: args.purposes], AFFECTS[: args.affects]))
    print(f"D-0 | arm={args.arm} | {len(cells)} cells x k={args.k} = "
          f"{len(cells) * args.k} generations | topic FIXED\n", flush=True)

    texts: dict[str, list[str]] = {}
    fails = []
    for pi, (p, a) in enumerate(cells):
        key = f"{p}|{a}"
        texts[key] = []
        for s in range(args.k):
            c = make_client(args.arm, seed=1000 + pi * 10 + s)
            try:
                out = c.read_text(SYSTEM, PROMPT.format(
                    topic=TOPIC, purpose_gloss=PURPOSE_GLOSS[p], affect_gloss=AFFECT_GLOSS[a]))
            except Exception as e:                                  # noqa: BLE001
                fails.append(f"{key}/{s}: {type(e).__name__}")
                continue
            if len(out.split()) < 120:
                fails.append(f"{key}/{s}: too short ({len(out.split())}w)")
                continue
            texts[key].append(out)
        n = len(texts[key])
        print(f"  {key:<20} {n}/{args.k}"
              f"  mean {statistics.fmean(len(t.split()) for t in texts[key]):.0f}w"
              if n else f"  {key:<20} 0/{args.k}  ALL FAILED", flush=True)

    usable = {k: v for k, v in texts.items() if len(v) >= 2}
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "generations.json").write_text(
        json.dumps({"arm": args.arm, "k": args.k, "topic": TOPIC,
                    "failures": fails, "texts": texts}, indent=2), encoding="utf-8")

    if len(usable) < 4:
        print(f"\nonly {len(usable)} usable cells — D-0 cannot be scored")
        return

    print("\n" + "=" * 74)
    full = separability(usable)
    by_purpose = separability({p: [t for k, v in usable.items() if k.startswith(p + "|")
                                   for t in v] for p in PURPOSES[: args.purposes]})
    by_affect = separability({a: [t for k, v in usable.items() if k.endswith("|" + a)
                                  for t in v] for a in AFFECTS[: args.affects]})

    for name, s in (("all cells", full), ("purpose only", by_purpose), ("affect only", by_affect)):
        above2 = [k for k, v in s["per_category"].items() if v > 2.0]
        print(f"{name:<14} ratio {s['mean_ratio']:>6.2f}   categories>2.0: {len(above2)}"
              f"   top: " + ", ".join(f"{k}={v:.1f}" for k, v in s["top"][:3]))

    above2 = sum(1 for v in full["per_category"].values() if v > 2.0)
    verdict = ("PASS" if full["mean_ratio"] > 1.5 and above2 >= 3
               else "FAIL" if full["mean_ratio"] <= 1.0 else "AMBIGUOUS")
    print("=" * 74)
    print(f">>> D-0 {verdict}   (ratio {full['mean_ratio']:.2f}, {above2} categories above 2.0)")
    if verdict == "PASS":
        print("    Function words track maker STATE, not only identity. Option D is engineering.")
        print("    Does NOT license believing D works on human text — that is E38's warning, and")
        print("    the same test must run against human artifacts with known-ish states.")
    elif verdict == "FAIL":
        print("    The feature channel is wrong. D dies here, for two hours instead of two weeks.")
    else:
        print("    Ambiguous. Do not proceed on it; raise k or widen the state grid first.")

    (RESULTS / "d0.json").write_text(json.dumps({
        "verdict": verdict, "all_cells": full, "by_purpose": by_purpose,
        "by_affect": by_affect, "n_cells": len(usable), "failures": fails}, indent=2),
        encoding="utf-8")


if __name__ == "__main__":
    main()
