"""Ladder 3 — the extremes, with length nailed down by rejection sampling.

── THE CURATOR'S TWO OBJECTIONS, BUILT INTO ONE CORPUS ───────────────────────────────────────

**Objection 1 — the manipulation was too weak.** He does not accept the ruled-out verdict on
machine-text-written-with-purpose:

    If you gave a machine a bunch of different goals and told it to balance all of them before it
    wrote something, it would get more of a purpose ranking along any intent register. We should
    start at the extremes -- three pages of different motivations stacked on top of each other that
    are all reasonably capable of aligning, against a machine writing with just one or two.

Ladders 1 and 2 topped out at **ten** short specifications. This goes to **sixty**, and the pool is
doubled so that even the top rung is a random draw rather than the whole pool.

**Objection 2 — length is running rampant.** Both previous ladders produced a correlation of ~+0.40
between how many specifications a prompt carried and how long the output came out, against a
pre-registered ceiling of 0.40. That voided ladder 1 and forced every result since to be reported
length-controlled.

    Sure does seem like length is something we can just control for. We should absolutely control
    for length hard when we're doing generations.

**So length is controlled by construction rather than by arithmetic afterwards.** Every artifact is
generated and then **rejected and regenerated** until it falls inside a narrow word band. A measure
that ranks these rungs cannot be ranking length, because length does not vary with rung.

── AND IT IS THE FIRST TEST OF E2 ────────────────────────────────────────────────────────────

`docs/theory/CURATOR_GUESSES.md` E2: **values may be the constraint that every goal is partially
satisfied at once**, rather than a separate factor. Sixty simultaneous specifications that must all
be honoured is the closest thing to that constraint we can manufacture. If the effect is not merely
monotone but **accelerates** at the top rungs, that is evidence the constraint is doing something the
count alone does not.

── PRE-REGISTERED, BEFORE GENERATION ─────────────────────────────────────────────────────────

    rungs        0, 2, 10, 30, 60 specifications, drawn at random without replacement
    length       every artifact within 1,350-1,450 words, enforced by regeneration
    n            15 per rung

    VALID        rung vs output length correlation below 0.15 -- otherwise the control failed and
                 the corpus is no better than ladder 1
    PASS         the layer ratio ranks the rungs at strength above 0.3, p < 0.01, WITHOUT any
                 length correction being applied
    ACCELERATES  the gap between rungs 30 and 60 exceeds the gap between rungs 0 and 10

**The length band is the whole point.** If rejection sampling cannot hit it, that failure is itself
reportable: it would mean output length is not independently controllable at these prompt sizes, and
every ladder result stays conditional on a correction.
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from runners.make_intent_ladder import SPECS as BASE_SPECS, TOPICS      # noqa: E402
from soundingline.probe.client import make_client                       # noqa: E402

OUT = REPO / "corpora" / "ladder3"
RUNGS = (0, 2, 10, 30, 60)
LO, HI = 1350, 1450
MAX_TRIES = 6
SEED_BASE = 110000

# The pool must exceed the top rung or rung 60 stops being a random draw. Thirty more, same rule as
# the original: describe THE SITUATION THE MAKER IS IN, never the marks a maker leaves.
EXTRA_SPECS = [
    "for a reader who will be quoting this to someone else",
    "for a reader who has to justify the decision to a colleague",
    "for someone deciding under time pressure",
    "for someone who has plenty of time and wants to get it right",
    "for a reader who has already spent money on this once",
    "for a reader who cannot easily undo the choice",
    "for a reader in a country where the usual advice does not apply",
    "for a reader whose budget is the binding constraint",
    "for a reader for whom money is not the constraint",
    "so the reader can explain it to someone less informed",
    "so the reader recognises when to ask for help",
    "so the reader can tell a good supplier from a bad one",
    "so the reader is not embarrassed by what they end up choosing",
    "so the reader has a way to check the outcome afterwards",
    "in the voice of someone who has done it more than once",
    "in the voice of someone who learned it from a person rather than a manual",
    "as someone who finds the conventional wisdom mostly right",
    "as someone who finds the conventional wisdom mostly wrong",
    "as someone whose own situation was unusual",
    "with the seasonality of the thing in mind",
    "with the reader's likely constraints made explicit",
    "with an eye to what goes wrong six months later",
    "with attention to what is reversible and what is not",
    "without assuming the reader has anyone to ask",
    "without assuming the reader is starting from scratch",
    "without treating cost and quality as the same axis",
    "in a way that stays true if the market changes",
    "in a way that a careful reader could disagree with productively",
    "for a reader who has been burned by exactly this",
    "for a reader who is helping someone else decide",
]
SPECS = BASE_SPECS + EXTRA_SPECS

SYSTEM = ("You write long-form prose. Write between 1380 and 1420 words — this length requirement is "
          "strict and matters as much as the content. No headings, no lists, no bullet points. "
          "Write only the piece.")


def build(topic: str, n: int, rng: random.Random) -> str:
    if n == 0:
        return f"Write about {topic}."
    picks = rng.sample(SPECS, n)
    return (f"Write about {topic}. Every one of the following must be honoured, and they are all "
            f"simultaneously true of your situation: " + "; ".join(picks) + ".")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", default="local")
    ap.add_argument("--per-rung", type=int, default=15)
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    print(f"pool of {len(SPECS)} specifications; band {LO}-{HI} words; "
          f"up to {MAX_TRIES} attempts each\n", flush=True)

    items = []
    for rung in RUNGS:
        for i in range(args.per_rung):
            name = f"r{rung}_{i:02d}"
            if (OUT / f"{name}.json").exists():
                items.append(json.loads((OUT / f"{name}.json").read_text(encoding="utf-8")))
                continue
            topic = TOPICS[(i + 3) % len(TOPICS)]
            best, best_gap, tries = None, None, 0
            for attempt in range(MAX_TRIES):
                tries = attempt + 1
                seed = SEED_BASE + rung * 1000 + i * 10 + attempt
                rng = random.Random(SEED_BASE + rung * 1000 + i)   # SAME draw across retries
                prompt = build(topic, rung, rng)
                try:
                    text = make_client(args.arm, seed=seed).read_text(SYSTEM, prompt)
                except Exception as e:                                # noqa: BLE001
                    print(f"  {name}: {type(e).__name__}", flush=True)
                    continue
                n_words = len(text.split())
                gap = 0 if LO <= n_words <= HI else min(abs(n_words - LO), abs(n_words - HI))
                if best is None or gap < best_gap:
                    best, best_gap = (text, n_words), gap
                if gap == 0:
                    break
            if best is None:
                continue
            text, n_words = best
            (OUT / f"{name}.txt").write_text(text, encoding="utf-8", newline="\n")
            rec = {"id": name, "rung": rung, "topic": topic, "n_specs": rung,
                   "n_words": n_words, "tries": tries, "in_band": LO <= n_words <= HI}
            (OUT / f"{name}.json").write_text(json.dumps(rec), encoding="utf-8", newline="\n")
            items.append(rec)
            (OUT / "manifest.json").write_text(json.dumps(
                {"why": "extreme ladder, length controlled by rejection; see make_ladder3.py",
                 "rungs": list(RUNGS), "band": [LO, HI], "items": items}, indent=2),
                encoding="utf-8", newline="\n")
        got = [m for m in items if m["rung"] == rung]
        if got:
            inb = sum(m["in_band"] for m in got)
            print(f"  rung {rung:>2}: n={len(got)}  median {statistics.median(m['n_words'] for m in got):.0f}w  "
                  f"in band {inb}/{len(got)}  mean tries {statistics.fmean(m['tries'] for m in got):.1f}",
                  flush=True)

    print("\nTHE CONTROL CHECK — rung vs output length (ladders 1 and 2 both failed at +0.40)")
    from scipy import stats                                            # noqa: PLC0415
    rho, p = stats.spearmanr([m["rung"] for m in items], [m["n_words"] for m in items])
    ok = abs(rho) < 0.15
    print(f"  strength {rho:+.3f}  p={p:.4f}   >>> {'CONTROLLED' if ok else 'CONTROL FAILED'}")
    print(f"  in band: {sum(m['in_band'] for m in items)}/{len(items)}")


if __name__ == "__main__":
    main()
