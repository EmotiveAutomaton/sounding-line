"""The intent ladder — a no-maker set where the AMOUNT of intent is the manipulated variable.

── WHY THE FIRST VERSION WAS NOT GOOD ENOUGH ─────────────────────────────────────────────────

`corpora/nomaker/` has a `rich` arm that ranked above `thin` on density at p = 0.0032. The curator
caught the flaw and he is right:

    Name three things you decided not to cover... the prompts shouldn't be quite so identifiable.
    If anything the prompts should be randomly varied as well, in everything but length.

**The `rich` prompt explicitly instructed the model to include decision markers** — *"name at least
three things you decided NOT to cover"*, *"be direct about what you are uncertain about"*. A measure
separating `rich` from `thin` could be reading **instruction-following**, not intent. Same flaw
class as the five confounds already found: the instrument sees something real that is not the thing
wanted.

── THE FIX ───────────────────────────────────────────────────────────────────────────────────

**Prompt length is the manipulated variable. Prompt content is randomised.**

    rung 0   nothing but the topic
    rung 1   one specification, drawn at random
    rung 2   three specifications, drawn at random
    rung 3   six specifications, drawn at random
    rung 4   ten specifications, drawn at random

Specifications come from a pool of thirty and are sampled **without replacement, per artifact**.
No two prompts at the same rung are alike, so nothing in the prompt is identifiable except how
much of it there is.

**And no specification names a decision, an alternative, an uncertainty, or a thing not covered.**
That was the whole flaw. The pool describes *the situation the maker is in* — who they are writing
for, what the reader already believes, what the piece must not become — never *the marks a maker
leaves*. If a measure recovers intent, it has to recover it from what the situation produced.

── WHAT THIS TESTS ───────────────────────────────────────────────────────────────────────────

**Monotonicity, which is much harder to fake than a two-group difference.**

    A machine detector must see all five rungs as identical: every one is machine-written.
    An intent measure must rank them IN ORDER, because intent is added a rung at a time.

A two-group split can be produced by any incidental difference. **A five-rung monotone ordering,
with randomised content and length as the only systematic variable, cannot be.** Spearman's rho
against rung is the statistic, and the pre-registration is below.

── PRE-REGISTERED, BEFORE THE RUN ────────────────────────────────────────────────────────────

    PASS       rho > 0.4 against rung, p < 0.01, AND the effect survives the shuffle control
    FAIL       rho at or below 0.2, or the shuffle control shows the effect is vocabulary
    AMBIGUOUS  between

**The shuffle control is mandatory** and is why density's result died: word-shuffling preserves
vocabulary and length exactly, so a measure that survives it is a vocabulary statistic. Any rung
effect that survives shuffling is not an intent effect.

**Output length is held as constant as the model allows** and is reported per rung — if longer
prompts produce longer articles, the ladder is a length ladder and that voids it.
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

from soundingline.probe.client import make_client                     # noqa: E402

OUT = REPO / "corpora" / "ladder"
RUNGS = (0, 1, 3, 6, 10)

TOPICS = [
    "choosing a mattress", "writing a technical postmortem", "affiliate marketing",
    "why small teams ship faster", "maintaining an internal tool", "hiring a locksmith",
    "what makes a good bug report", "buying a used car", "how sleep trackers work",
    "planning a kitchen renovation", "home networking", "the case for boring technology",
]

# Thirty specifications about THE SITUATION THE MAKER IS IN. None of them names a decision, an
# alternative, an uncertainty, or something left out — that instruction is what made the first
# version measure instruction-following rather than intent.
SPECS = [
    "for readers who have never done this before",
    "for readers who have done it badly once already",
    "for an audience that is mildly anxious about getting it wrong",
    "for people who will act on it within the week",
    "for someone who has already read three other guides and found them useless",
    "for a reader who distrusts anyone selling anything",
    "so the reader can make one specific choice by the end",
    "so the reader stops worrying about a thing they should not worry about",
    "so the reader knows when to stop researching",
    "so a reader who disagrees still finds it useful",
    "in a register that would not embarrass a professional",
    "warmly, as though to someone you like",
    "plainly, with no attempt to impress",
    "with the impatience of someone who has explained this many times",
    "as someone who has changed their mind about it",
    "as someone who got it wrong the first time",
    "as someone who does this for a living and is slightly tired of it",
    "as someone who is still learning it",
    "grounded in specifics rather than principles",
    "with concrete numbers wherever possible",
    "using ordinary language rather than the field's vocabulary",
    "without the usual introduction",
    "without pretending the reader has unlimited time",
    "without pretending the answer is simple",
    "in a way that would survive being read by an expert",
    "in a way that would survive being read by a sceptic",
    "acknowledging that the reader may not follow the advice",
    "acknowledging that circumstances vary a lot",
    "for a reader whose situation is probably not the standard one",
    "for someone who has been given bad advice about this before",
]

SYSTEM = ("You write long-form prose. Write at least 1400 words. No headings, no lists, no "
          "bullet points. Write only the piece.")


def build(topic: str, n_specs: int, rng: random.Random) -> str:
    if n_specs == 0:
        return f"Write about {topic}."
    picks = rng.sample(SPECS, n_specs)
    return f"Write about {topic}, " + ", ".join(picks) + "."


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", default="local")
    ap.add_argument("--per-rung", type=int, default=10)
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    items = []
    for rung in RUNGS:
        for i in range(args.per_rung):
            rng = random.Random(70000 + rung * 1000 + i)
            topic = TOPICS[i % len(TOPICS)]
            prompt = build(topic, rung, rng)
            c = make_client(args.arm, seed=70000 + rung * 1000 + i)
            try:
                text = c.read_text(SYSTEM, prompt)
            except Exception as e:                                    # noqa: BLE001
                print(f"  rung {rung} #{i}: {type(e).__name__}", flush=True)
                continue
            name = f"r{rung}_{i:02d}"
            (OUT / f"{name}.txt").write_text(text, encoding="utf-8", newline="\n")
            items.append({"id": name, "rung": rung, "topic": topic,
                          "n_specs": rung, "prompt_words": len(prompt.split()),
                          "n_words": len(text.split())})
            (OUT / "manifest.json").write_text(json.dumps(
                {"why": "intent ladder; see runners/make_intent_ladder.py",
                 "rungs": list(RUNGS), "items": items}, indent=2), encoding="utf-8")
        got = [m for m in items if m["rung"] == rung]
        if got:
            print(f"  rung {rung:>2} ({rung} specs): n={len(got)}  "
                  f"prompt {statistics.median(m['prompt_words'] for m in got):>3.0f}w  "
                  f"output median {statistics.median(m['n_words'] for m in got):.0f}w", flush=True)

    print("\nOUTPUT LENGTH BY RUNG — if this climbs, the ladder is a length ladder and is void")
    for rung in RUNGS:
        got = [m["n_words"] for m in items if m["rung"] == rung]
        if got:
            print(f"  rung {rung:>2}: median {statistics.median(got):>6.0f}  "
                  f"mean {statistics.fmean(got):>6.0f}")


if __name__ == "__main__":
    main()
