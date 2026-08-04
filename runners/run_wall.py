"""E — the wall, measured inside the reader.

── THE IDEA, AND WHY IT IS NOT ANOTHER SURFACE STATISTIC ─────────────────────────────────────

Five instruments have now failed the same way: each measured a property of the input that was not
the thing wanted — denominator instability, one dimension of a joint signal, five tokens of noise,
the difference between a sentence and a document, and word count. `results/density_VERDICT.md`.

**The space of surface statistics on text is dominated by length, register and vocabulary.** So
this one does not compute a statistic on the text at all. It measures **what happens to a reader.**

The mechanism comes from *Emotion Concepts and their Function in a Large Language Model*
(arXiv 2604.07729), which found that a model **tracks a character's emotional state temporarily
while reading about them, then returns to representing its own assistant persona.**

It already does the other-agent thing. So:

    When the model reads an artifact with a recoverable maker, does it move away from its own
    default state to represent one? And when it reads the wall -- legible and empty -- does it
    fail to, and stay where it was?

That is E37 turned from a claim about artifacts into a measurable event inside the reader.
Non-invertibility stops being "the posterior is diffuse" and becomes **"the reader could not build
a separate agent to attribute this to."**

── WHY THIS IS THE ONE THE ARCHITECTURE IS FOR ───────────────────────────────────────────────

Version 9's ablation programme: *the wall is the only finding that needs the reader to hold a
distribution rather than a best guess.* Everything else the simulation found survives replacing the
maker-modelling reader with a surface classifier. This is the one that does not.

── PRE-REGISTERED, AND THE CONFOUND NAMED FIRST ──────────────────────────────────────────────

**W-1.** Human artifacts displace the reader's state further from baseline than machine-generated
artifacts do.

    PASS   generated displacement is lower, and the gap survives length matching
    FAIL   no difference, or generated displaces MORE

**THE CONFOUND IS LENGTH AND IT HAS ALREADY EATEN ONE MEASURE TODAY.** So:

  * every artifact is read in **fixed-size windows**, never whole;
  * displacement is the **mean over windows**, so a long artifact contributes no more per window
    than a short one;
  * the correlation between displacement and word count is computed and reported **before** any
    verdict, and a correlation above 0.5 voids the result whatever it says.

**W-2, the harder one.** Displacement should be lower for generated content *and* the readings
should be more mutually similar — a reader that cannot build a distinct maker has nothing to vary
between artifacts. Measured as the spread of displacement within each group.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "wall"
_WS = re.compile(r"\s+")

# One window size, fixed, for everything. Long enough to carry a maker's voice, short enough that
# most artifacts supply several.
WINDOW_WORDS = 200
MAX_WINDOWS = 12

# The reader's own resting state. Neutral prose with no maker to speak of and no affect -- what the
# model looks like when it is reading and has nobody to represent.
BASELINE = [
    "The document is divided into sections. Each section contains several paragraphs.",
    "The following table lists the available options and their default values.",
    "This page was last updated. See the index for related entries.",
    "Items are numbered sequentially. Refer to the appropriate number when required.",
]


def windows(text: str, n: int = WINDOW_WORDS, cap: int = MAX_WINDOWS) -> list[str]:
    w = _WS.split(text.strip())
    out = [" ".join(w[i:i + n]) for i in range(0, max(len(w) - n + 1, 1), n)]
    if len(out) <= cap:
        return out
    step = len(out) / cap
    return [out[int(i * step)] for i in range(cap)]


def _cos(x, y):
    num = sum(a * b for a, b in zip(x, y))
    nx = math.sqrt(sum(a * a for a in x)) or 1e-9
    ny = math.sqrt(sum(b * b for b in y)) or 1e-9
    return num / (nx * ny)


def displacement(reader, text: str, base: list[list[float]], layers: list[int]) -> float:
    """Mean cosine distance from the reader's resting state, over fixed windows and chosen layers.

    Mean over WINDOWS rather than over the whole text, so length enters only through how many
    windows are averaged — and averaging more samples of the same quantity does not change its
    expectation, which is the property word-count-based measures did not have.
    """
    ds = []
    for w in windows(text):
        a = reader.read(w)
        ds.append(statistics.fmean(1.0 - _cos(a.acts[L], base[L]) for L in layers))
    return statistics.fmean(ds) if ds else float("nan")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--artifacts", type=int, default=20)
    args = ap.parse_args()

    from soundingline.probe.activations import DEFAULT_MODEL, Reader   # noqa: PLC0415
    from runners.run_gate3 import load_corpus                          # noqa: PLC0415

    name = args.model or DEFAULT_MODEL
    print(f"loading {name} on {args.device} ...", flush=True)
    r = Reader(name, device=args.device)

    print("establishing the reader's resting state ...", flush=True)
    bs = [r.read(s) for s in BASELINE]
    n_layers = min(a.n_layers for a in bs)
    base = [[statistics.fmean(a.acts[L][i] for a in bs) for i in range(len(bs[0].acts[L]))]
            for L in range(n_layers)]
    # Late layers only. Early layers are near-lexical -- the layer-0 result in results/b/VERDICT.md
    # scored 43.8% while bag-of-words scored chance, which says the embedding layer separates on
    # something, and something near vocabulary is exactly what must not drive this.
    layers = list(range(2 * n_layers // 3, n_layers))
    print(f"  {n_layers} layers; using {layers[0]}-{layers[-1]}\n", flush=True)

    corpus = load_corpus()[: args.artifacts]
    gen = [(p.stem, "generated", p.read_text(encoding="utf-8"))
           for p in sorted((REPO / "docs" / "gate1" / "artifacts").glob("item_*.md"))]
    items = [(a, h, t) for a, h, t in corpus] + gen

    rows = []
    print(f"{'artifact':<16}{'group':>11}{'displace':>10}{'words':>8}")
    for aid, grp, text in items:
        d = displacement(r, text, base, layers)
        rows.append({"id": aid, "group": grp, "displacement": d, "words": len(text.split())})
        print(f"{aid:<16}{grp:>11}{d:>10.4f}{len(text.split()):>8}", flush=True)

    human = [x for x in rows if x["group"] in ("A", "B")]
    machine = [x for x in rows if x["group"] == "generated"]

    # THE CONFOUND CHECK RUNS BEFORE THE VERDICT.
    from scipy import stats                                            # noqa: PLC0415
    rho, prho = stats.spearmanr([x["words"] for x in rows], [x["displacement"] for x in rows])
    print(f"\nCONFOUND  displacement vs word count: rho={rho:+.3f} p={prho:.4f}")
    voided = abs(rho) > 0.5
    print(f"  >>> {'VOID — this is a length measure again' if voided else 'no length confound'}")

    hm = statistics.fmean(x["displacement"] for x in human)
    mm = statistics.fmean(x["displacement"] for x in machine)
    hs = statistics.pstdev(x["displacement"] for x in human)
    ms = statistics.pstdev(x["displacement"] for x in machine)
    t, pv = stats.ttest_ind([x["displacement"] for x in human],
                            [x["displacement"] for x in machine], equal_var=False)
    print(f"\nW-1  human {hm:.4f} (sd {hs:.4f}, n={len(human)})   "
          f"generated {mm:.4f} (sd {ms:.4f}, n={len(machine)})")
    print(f"     diff {hm - mm:+.4f}   p={pv:.4f}")
    verdict = "VOID" if voided else ("PASS" if hm > mm and pv < 0.05 else "FAIL")
    print(f"     >>> W-1 {verdict}")
    if verdict == "PASS":
        print("     The reader moves further from its own resting state for a human maker than")
        print("     for machine content. The wall is an event inside the reader.")

    print(f"\nW-2  spread: human sd {hs:.4f}  generated sd {ms:.4f}   "
          f"{'as predicted' if ms < hs else 'REVERSED'}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "wall.json").write_text(json.dumps(
        {"model": name, "window_words": WINDOW_WORDS, "layers": layers,
         "confound_rho": float(rho), "voided": bool(voided), "verdict": verdict,
         "human_mean": hm, "generated_mean": mm, "p": float(pv), "rows": rows}, indent=2),
        encoding="utf-8")


if __name__ == "__main__":
    main()
