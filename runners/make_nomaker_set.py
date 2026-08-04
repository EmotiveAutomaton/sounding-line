"""Build a proper no-maker control set. The binding constraint on four separate measures.

── WHY THIS IS THE SMALLEST UNBLOCKED THING ON THE LIST ──────────────────────────────────────

Four measures have now been tested against the same three artifacts — `item_A`, `item_B`, `item_C`,
written for Gate 1 in a different context, ~560 words each, and never intended to be a control set:

    method unlock          generated 1.111 against commercial 0.917   — the failure that started this
    gated unlock           never run for want of anything to run it against
    density by compression generated 0.201 against human 0.323        — which turned out to be length
    the wall inside reader generated 0.2932 against human 0.2884, n = 3

**n = 3 cannot carry any of them.** And in the density case the three were short enough that their
length alone produced the entire apparent effect. A control set that is short, few, and written for
another purpose is not a control set.

── WHAT A NO-MAKER SET HAS TO BE ─────────────────────────────────────────────────────────────

Not "AI-written". **Written so that no maker-state is recoverable**, which is a stronger and more
specific thing, and the reason is E37: the wall is *legible and empty*, not *badly written*.

Three kinds, because they predict different things and building only the first would be
constructing the control that flatters the theory — the same argument `ghost-scale-sim`'s E55 makes
about groomed corpora.

    thin        a bare prompt, no direction, nothing specified. The obvious case.
    rich        a long, detailed prompt with a purpose and an audience specified. This one SHOULD
                have recoverable intent -- the prompt-writer's -- and if a measure calls it empty,
                the measure is detecting machines rather than reading intent, which is the thing
                this project explicitly refuses to do.
    averaged    generated, then rewritten twice more to smooth it. The regression-to-the-mean case
                the theory names directly: "the latent space is a graveyard of idiosyncrasies,
                ground down into a frictionless paste of human expectation."

**Length-matched to the human corpus** — median 2,914 words — because a control that is short is a
length control, and today proved that costs a whole instrument.

── AND THE HONEST LIMIT ──────────────────────────────────────────────────────────────────────

These are produced by the same local model the probe uses. E38: a machine-matched reader reads
machine content far better than human content, so the probe reading its own family's output is the
easy case, not a neutral one. **A no-maker set from a different model family would be better** and
is a later acquisition. This one is still strictly better than three short artifacts from Gate 1.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from soundingline.probe.client import make_client                     # noqa: E402

OUT = REPO / "corpora" / "nomaker"
TARGET_WORDS = 2500

TOPICS = [
    "choosing a mattress", "how to write a technical postmortem",
    "affiliate marketing for beginners", "why small teams ship faster",
    "maintaining an internal tool nobody sees", "the economics of local locksmiths",
    "what makes a good bug report", "buying a used car without being cheated",
    "how sleep tracking devices work", "planning a kitchen renovation",
    "getting started with home networking", "the case for boring technology",
]

THIN = "Write about {topic}."

RICH = ("Write a {n}-word article about {topic} for an audience of people who have never dealt "
        "with this before and are mildly anxious about getting it wrong. Your purpose is to leave "
        "them able to make one specific decision confidently. Use concrete examples. Name at least "
        "three things you decided NOT to cover and why. Be direct about what you are uncertain "
        "about. Do not use headings.")

SMOOTH = ("Rewrite the following so it reads more smoothly and professionally. Keep all the "
          "information. Do not add headings.\n\n{text}")


def gen(client, prompt: str, target: int) -> str:
    return client.read_text(
        f"You write long-form prose. Write at least {target} words. No headings, no lists.",
        prompt)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", default="local")
    ap.add_argument("--per-kind", type=int, default=12)
    ap.add_argument("--words", type=int, default=TARGET_WORDS)
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    manifest = []
    for i in range(args.per_kind):
        topic = TOPICS[i % len(TOPICS)]
        for kind in ("thin", "rich", "averaged"):
            c = make_client(args.arm, seed=9000 + i * 10 + ("thin", "rich", "averaged").index(kind))
            try:
                if kind == "thin":
                    text = gen(c, THIN.format(topic=topic), args.words)
                elif kind == "rich":
                    text = gen(c, RICH.format(topic=topic, n=args.words), args.words)
                else:
                    base = gen(c, THIN.format(topic=topic), args.words)
                    for _ in range(2):
                        base = c.read_text("You rewrite prose.", SMOOTH.format(text=base[:9000]))
                    text = base
            except Exception as e:                                    # noqa: BLE001
                print(f"  {kind}/{i}: {type(e).__name__}", flush=True)
                continue
            name = f"{kind}_{i:02d}"
            (OUT / f"{name}.txt").write_text(text, encoding="utf-8", newline="\n")
            manifest.append({"id": name, "kind": kind, "topic": topic,
                             "n_words": len(text.split()), "n_chars": len(text)})
            print(f"  {name:<14} {kind:<9} {len(text.split()):>5}w  {topic}", flush=True)
            (OUT / "manifest.json").write_text(json.dumps(
                {"why": "no-maker control set; see runners/make_nomaker_set.py",
                 "arm": args.arm, "items": manifest}, indent=2), encoding="utf-8")

    import statistics
    for kind in ("thin", "rich", "averaged"):
        ws = [m["n_words"] for m in manifest if m["kind"] == kind]
        if ws:
            print(f"\n{kind:<10} n={len(ws)}  median {statistics.median(ws):.0f} words")


if __name__ == "__main__":
    main()
