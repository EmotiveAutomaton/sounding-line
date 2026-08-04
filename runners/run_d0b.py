"""D-0b — the powered rerun. Pre-registered with the power computed FIRST this time.

── WHAT D-0 GOT WRONG ────────────────────────────────────────────────────────────────────────

380-word generations give ~5 tokens in a function-word category. Poisson noise on five counts is
most of the within-group variance the statistic divides by. Planting a real 2.4x effect, the D-0
design had **38% power** and a median outcome BELOW its own pass threshold. It could not have found
what it was looking for, so its failure was not evidence. `results/d0/VERDICT.md`.

── THE DESIGN, AND ITS POWER, BOTH FIXED BEFORE THE RUN ──────────────────────────────────────

    affect only, purpose and topic held FIXED
    2,000+ words per generation, k = 10
    power 99% against a 2.4x effect in I-rate; false-positive rate 0% under the null

**The statistic is the one that works.** D-0 used the univariate separability measure, which was
later shown to report "no group information" on author identification -- the most established
result in stylometry. `results/g/VERDICT.md`. This uses Burrows' Delta with a nearest-centroid
classifier, leave-one-out, which recovers that signal at 5.2x chance.

    PASS   classification accuracy > 2x chance (chance = 25% over four affects)
    FAIL   at or below chance
    Between is AMBIGUOUS and licenses nothing.

── AND THE SECOND READING, WHICH IS NOT OPTIONAL ─────────────────────────────────────────────

A pass here is a pass on MACHINE-GENERATED text. There is a mechanistic account of why it might
fail that is a finding rather than a defect:

    The model has no leaked layer, because it has nothing unchosen. Told to be angry it writes
    angrier CONTENT; it has no involuntary production to bend.

If D-0b fails, that account is the leading explanation and the contrast test -- human artifacts of
adequate length, with known-ish states -- becomes the next thing, not a rescue.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from soundingline.measures.leakage import delta_classify, profile   # noqa: E402
from soundingline.probe.client import make_client                   # noqa: E402

RESULTS = REPO / "results" / "d0b"

# Purpose and topic FIXED. Only the affect varies -- D-0 crossed purpose x affect and could
# attribute nothing.
TOPIC = ("the decade you spent maintaining an internal system almost nobody outside the company "
         "ever saw, and what you learned from it")
PURPOSE = "pass on something the reader did not know, for the reader's benefit"

AFFECTS = {
    "seeking": "absorbed and curious, still enjoying working the problem out after all this time",
    "rage": "irritated and aggrieved about how the whole thing was handled",
    "fear": "anxious about being judged for it, covering every base you can think of",
    "care": "concerned that the reader succeeds where you struggled, and spending effort on it",
}

SYSTEM = ("You are writing a long piece of real prose, as the described person would have written "
          "it. Do not describe the person, do not mention their goal or their state, and do not "
          "use the words you are given. Just write the piece. AT LEAST 2000 WORDS -- this is a "
          "long-form essay, not a summary. Write it in full.")

PROMPT = ("Write a long essay about {topic}.\n\n"
          "The person writing it is trying to {purpose} They are, while writing, {affect}\n\n"
          "Write at least 2000 words. Write only the essay.")

MIN_WORDS = 1200        # below this the sample is not what the power calculation assumed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", default="local")
    ap.add_argument("--k", type=int, default=10)
    args = ap.parse_args()

    print(f"D-0b | arm={args.arm} | {len(AFFECTS)} affects x k={args.k} "
          f"| purpose and topic FIXED | target 2000+ words\n", flush=True)

    texts: dict[str, list[str]] = {a: [] for a in AFFECTS}
    short = []
    for ai, (a, gloss) in enumerate(AFFECTS.items()):
        for s in range(args.k):
            c = make_client(args.arm, seed=5000 + ai * 100 + s)
            try:
                out = c.read_text(SYSTEM, PROMPT.format(topic=TOPIC, purpose=PURPOSE, affect=gloss))
            except Exception as e:                                   # noqa: BLE001
                short.append(f"{a}/{s}: {type(e).__name__}")
                continue
            w = len(out.split())
            if w < MIN_WORDS:
                short.append(f"{a}/{s}: {w}w")
                continue
            texts[a].append(out)
        n = len(texts[a])
        mw = statistics.fmean(len(t.split()) for t in texts[a]) if n else 0
        print(f"  {a:<10} {n}/{args.k} usable   mean {mw:.0f} words", flush=True)
        RESULTS.mkdir(parents=True, exist_ok=True)
        (RESULTS / "generations.json").write_text(
            json.dumps({"topic": TOPIC, "purpose": PURPOSE, "short": short, "texts": texts},
                       indent=2), encoding="utf-8")

    usable = {a: v for a, v in texts.items() if len(v) >= 3}
    if len(usable) < 3:
        print(f"\nonly {len(usable)} affects with 3+ usable samples — cannot score")
        return

    print("\n" + "=" * 72)
    r = delta_classify(usable)
    lift = r["lift"]
    verdict = "PASS" if lift > 2.0 else "FAIL" if r["accuracy"] <= r["chance"] else "AMBIGUOUS"
    print(f"D-0b  Burrows' Delta, leave-one-out, {len(usable)} affects")
    print(f"      {r['accuracy']:.1%} vs {r['chance']:.1%} chance = {lift:.2f}x   n={r['n']}")
    for c, v in sorted(r["per_class"].items(), key=lambda kv: -kv[1]):
        print(f"        {c:<10}{v:.0%}")
    print(f"\n>>> D-0b {verdict}")
    if verdict == "PASS":
        print("    Function words track maker STATE, not only identity. On generated text.")
        print("    Does NOT license believing it holds for humans -- E38's warning stands.")
    elif verdict == "FAIL":
        print("    The leading account: the model has no leaked layer, because it has nothing")
        print("    unchosen. That is a finding about machines, and the contrast test on human")
        print("    text is the next step rather than a rescue.")

    # Which categories carry it -- and whether `I` behaves as D-0's post-hoc look suggested.
    print("\n      per-affect I-rate (D-0 saw rage/fear high, care/seeking low at k=3):")
    for a, v in usable.items():
        print(f"        {a:<10}{statistics.fmean(profile(t).rates['i'] for t in v):>7.1f}")

    (RESULTS / "d0b.json").write_text(json.dumps(
        {"verdict": verdict, "result": r, "short": short,
         "i_rate": {a: statistics.fmean(profile(t).rates["i"] for t in v)
                    for a, v in usable.items()}}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
