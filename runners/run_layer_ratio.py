"""The layer ratio — low-order against high-order affective activation in a reading model.

── THE CURATOR'S MEASURE, AND WHY IT IS THE ONE ──────────────────────────────────────────────

    They literally have Panksepp's lower-order features near their sensory input channels and
    Barrett's emotional prediction and control in cortical networks further away at the higher-
    order prediction space... we can catch the leakage specifically and extract it using how much
    it highlights these lower-order features in a reading LLM.
    ...
    Human text should trigger MORE low-order affective activation relative to high-order.

**Nine measures have died and eight of them died to length, vocabulary, or a scale mismatch.**
This one is structurally different: it is a **ratio between two layers of the same reader on the
same text.** Whatever a text's length, register or vocabulary do, they do it to *both* terms.
The confound that killed everything else largely cancels.

That is not a guarantee. It is the first measure whose *construction* argues against the specific
failure mode this project keeps meeting, and it is the reason it is worth the GPU.

── WHAT IS MEASURED ──────────────────────────────────────────────────────────────────────────

Affect directions are fitted from contrast sentences (`results/b/VERDICT.md`: real at 4x chance on
held-out sentences, and NOT lexical — bag-of-words on the same sentences scores exactly chance).
Then for each window of an artifact:

    early   mean |projection| onto the affect directions, over the first third of layers
    late    the same, over the last third
    ratio   early / late

`results/b/VERDICT.md` also found the accuracy profile is **bimodal across depth** — an early
locus, a dead middle, a late locus. That is the structure this measure needs and it was found
before this measure was proposed.

── THE THREE POPULATIONS, AND WHY ALL THREE ──────────────────────────────────────────────────

    ladder      50 artifacts, five rungs of known increasing specified intent, content randomised
    no-maker    36 artifacts, three kinds
    Gate 3      51 real web artifacts, two halves

**The ladder is the hard test.** A binary human/machine split can be produced by any incidental
difference. A five-rung monotone ordering with randomised content cannot.

── PRE-REGISTERED, WITH EVERY GRAVE CHECKED FIRST ────────────────────────────────────────────

    PASS       ratio ranks the ladder rungs, |rho| > 0.4 at p < 0.01, AND the effect DIES under
               word-shuffling, AND |rho| against word count is below 0.4
    FAIL       |rho| at or below 0.2 against rung
    VOCAB      survives shuffling — it is a vocabulary statistic like the other eight
    VOID       correlates with length above 0.4

**Secondary, and it is the curator's original claim:** human artifacts show a higher ratio than
no-maker artifacts. Reported whatever the ladder does.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "layer_ratio"
WINDOW_WORDS = 200
MAX_WINDOWS = 8


def windows(text: str, n: int = WINDOW_WORDS, cap: int = MAX_WINDOWS) -> list[str]:
    w = text.split()
    out = [" ".join(w[i:i + n]) for i in range(0, max(len(w) - n + 1, 1), n)]
    if len(out) <= cap:
        return out
    step = len(out) / cap
    return [out[int(i * step)] for i in range(cap)]


def ratio_for(reader, dirs, text: str) -> float:
    """Mean early/late affective-activation ratio over fixed windows."""
    vals = []
    for w in windows(text):
        p = dirs.project(reader.read(w))
        n = dirs.n_layers
        # SPLIT BY THE VALIDATED STRUCTURE, NOT BY THIRDS.
        # results/b/VERDICT.md found held-out affect accuracy is BIMODAL across depth: a locus at
        # layers 0-1, a dead middle, a second locus at 22-27 on a 29-layer model. Thirds average
        # that dead middle into both terms and dilute both. These are the loci themselves.
        lo_hi = max(2, round(n * 0.07))          # the early locus
        hi_lo = round(n * 0.76)                  # the late locus
        early = statistics.fmean(abs(v[L]) for v in p.values() for L in range(lo_hi))
        late = statistics.fmean(abs(v[L]) for v in p.values() for L in range(hi_lo, n))
        if late > 1e-9:
            vals.append(early / late)
    return statistics.fmean(vals) if vals else float("nan")


def load(path: Path, key: str) -> list[dict]:
    man = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
    out = []
    for it in man["items"]:
        p = path / f"{it['id']}.txt"
        if p.exists():
            out.append({"id": it["id"], "group": it[key], "text": p.read_text(encoding="utf-8")})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--gate3", type=int, default=30)
    args = ap.parse_args()

    from soundingline.probe.activations import (DEFAULT_MODEL, Reader,   # noqa: PLC0415
                                                fit_directions)
    from runners.run_b import split                                      # noqa: PLC0415
    from runners.run_gate3 import load_corpus                            # noqa: PLC0415
    from scipy import stats                                              # noqa: PLC0415

    name = args.model or DEFAULT_MODEL
    print(f"loading {name} on {args.device} ...", flush=True)
    r = Reader(name, device=args.device)
    fit, _ = split()
    print("fitting affect directions ...", flush=True)
    d = fit_directions(r, fit)
    print(f"  {len(d.concepts)} concepts x {d.n_layers} layers\n", flush=True)

    rng = random.Random(23)

    def shuf(t):
        w = t.split()
        rng.shuffle(w)
        return " ".join(w)

    out: dict = {"model": name}

    # ── THE LADDER: the hard test ─────────────────────────────────────────────────────────────
    lad = load(REPO / "corpora" / "ladder", "rung")
    print(f"LADDER  {len(lad)} artifacts", flush=True)
    for x in lad:
        x["ratio"] = ratio_for(r, d, x["text"])
        x["ratio_shuf"] = ratio_for(r, d, shuf(x["text"]))
        x["words"] = len(x["text"].split())
    for g in sorted({x["group"] for x in lad}):
        v = [x["ratio"] for x in lad if x["group"] == g]
        print(f"  rung {g:>2}: {statistics.fmean(v):.4f}  n={len(v)}")
    rho, pv = stats.spearmanr([x["group"] for x in lad], [x["ratio"] for x in lad])
    rho_s, _ = stats.spearmanr([x["group"] for x in lad], [x["ratio_shuf"] for x in lad])
    rho_l, _ = stats.spearmanr([x["words"] for x in lad], [x["ratio"] for x in lad])
    print(f"  rung vs ratio      rho={rho:+.3f} p={pv:.4f}")
    print(f"  SHUFFLED           rho={rho_s:+.3f}   (must collapse)")
    print(f"  vs word count      rho={rho_l:+.3f}   (must stay under 0.4)")

    survives = abs(rho_s) > 0.5 * abs(rho) if abs(rho) > 0.05 else True
    verdict = ("VOID" if abs(rho_l) > 0.4 else
               "VOCAB" if survives and abs(rho) > 0.4 else
               "PASS" if abs(rho) > 0.4 and pv < 0.01 else
               "FAIL" if abs(rho) <= 0.2 else "AMBIGUOUS")
    print(f"  >>> LADDER {verdict}")
    out["ladder"] = {"rho": rho, "p": pv, "rho_shuffled": rho_s, "rho_length": rho_l,
                     "verdict": verdict,
                     "by_rung": {str(g): statistics.fmean(x["ratio"] for x in lad
                                                          if x["group"] == g)
                                 for g in sorted({x["group"] for x in lad})}}

    # ── the original claim: human vs no-maker ─────────────────────────────────────────────────
    nm = load(REPO / "corpora" / "nomaker", "kind")
    corpus = load_corpus()[: args.gate3]
    print(f"\nHUMAN vs NO-MAKER   human n={len(corpus)}  no-maker n={len(nm)}", flush=True)
    hr = [ratio_for(r, d, t) for _, _, t in corpus]
    for k in sorted({x["group"] for x in nm}):
        v = [ratio_for(r, d, x["text"]) for x in nm if x["group"] == k]
        t, p = stats.ttest_ind(hr, v, equal_var=False)
        print(f"  human {statistics.fmean(hr):.4f}  vs {k:<9} {statistics.fmean(v):.4f}"
              f"   diff {statistics.fmean(hr) - statistics.fmean(v):+.4f}  p={p:.4f}")
        out.setdefault("human_vs_nomaker", {})[k] = {
            "human": statistics.fmean(hr), "nomaker": statistics.fmean(v), "p": float(p)}

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "layer_ratio.json").write_text(json.dumps(out, indent=2, default=float),
                                              encoding="utf-8")
    print(f"\nwrote {(RESULTS / 'layer_ratio.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
