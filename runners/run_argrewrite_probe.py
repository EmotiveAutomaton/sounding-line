"""Does a reader's INTERNAL state change as an author revises? — probing, not surface features.

── THE QUESTION, IN HIS WORDS ────────────────────────────────────────────────────────────────

    I tend to find surface-level feature analysis just not as interesting. I'm wondering whether we
    can go deeper -- probing, mechanistic interpretability. Whether there's some behaviour there
    that would increase with revision. Length wouldn't even matter, because we're talking about
    activation within the network.

**He is right that length matters less here**, though not that it cannot matter at all: activations
are read over fixed-size windows, so a longer text contributes more windows but each window is the
same size. Length-matched truncation is still run as a control because "less" is not "none".

── THE TERM HE WAS REACHING FOR ──────────────────────────────────────────────────────────────

**Probing** — specifically a *probing classifier* or *linear probe*: fit a direction in a model's
activation space that corresponds to some property, then read how strongly a new input projects onto
it. That is the family. The wider field is **mechanistic interpretability**; the sub-technique for
reading a concept out of activations is **representation engineering**, and for testing whether the
model *uses* it, **activation patching**.

── WHAT IS MEASURED ──────────────────────────────────────────────────────────────────────────

The same instrument as `results/ladder2` — affect directions fitted from contrast sentences, then the
ratio of low-order to high-order affective activation, read over fixed windows. It is the project's
only replicated effect, and it has never been pointed at human text where the maker is controlled.

**Paired within author, draft 1 against draft 3.** Between-person variation cannot contribute.

── PRE-REGISTERED, BEFORE THE RUN ────────────────────────────────────────────────────────────

    PASS       the ratio moves within author across drafts, signed-rank p < 0.01, sign-consistent
               in a clear majority of the 86 authors, AND it survives length-matched truncation
    FAIL       no movement within author

**No direction is predicted.** On the ladder the ratio FALLS as specified intent rises. Whether
revision is the same axis as specification is exactly what is unknown — revision might add intent
(ratio falls) or might be convergence and clean-up (ratio rises). Committing to no sign here means
we cannot claim one afterwards.

**Why this is the interesting version of L5.** The surface result — words get longer, rarer, fewer
function words — is polish. If the reader's internal affective response *also* moves, that is a
different quantity moving in the same corpus, and it is the one the project actually cares about.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "argrewrite"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--length-matched", action="store_true")
    args = ap.parse_args()

    import numpy as np                                               # noqa: PLC0415
    from scipy import stats                                          # noqa: PLC0415

    from runners.run_argrewrite import load                          # noqa: PLC0415
    from soundingline.probe.activations import (DEFAULT_MODEL, Reader,  # noqa: PLC0415
                                                fit_directions)
    from runners.run_b import split                                  # noqa: PLC0415
    from runners.run_layer_ratio import ratio_for                    # noqa: PLC0415

    authors = load()
    print(f"{len(authors)} authors with all three drafts", flush=True)
    print(f"loading {DEFAULT_MODEL} ...", flush=True)
    reader = Reader(DEFAULT_MODEL, device=args.device)
    fit, _ = split()
    dirs = fit_directions(reader, fit)
    print("  loci frozen, directions fitted identically to every prior run\n", flush=True)

    rows = []
    for i, (aid, drafts) in enumerate(authors.items()):
        if args.length_matched:
            n = min(len(t.split()) for t in drafts.values())
            drafts = {d: " ".join(t.split()[:n]) for d, t in drafts.items()}
        r = {"author": aid, "words": {d: len(t.split()) for d, t in drafts.items()},
             "ratio": {d: ratio_for(reader, dirs, t) for d, t in drafts.items()}}
        rows.append(r)
        if (i + 1) % 20 == 0:
            print(f"  {i + 1}/{len(authors)}", flush=True)

    for d in (1, 2, 3):
        v = [r["ratio"][d] for r in rows]
        w = [r["words"][d] for r in rows]
        print(f"\n  draft {d}: ratio {statistics.fmean(v):.4f}  "
              f"median {statistics.median(w):.0f}w")

    d1 = np.array([r["ratio"][1] for r in rows])
    d2 = np.array([r["ratio"][2] for r in rows])
    d3 = np.array([r["ratio"][3] for r in rows])
    delta = d3 - d1
    stat, p13 = stats.wilcoxon(d1, d3)
    _, p12 = stats.wilcoxon(d1, d2)
    agree = float(np.mean(np.sign(delta) == np.sign(np.median(delta))))
    rho_len, p_len = stats.spearmanr([r["words"][3] - r["words"][1] for r in rows], delta)

    print(f"\n  draft 1 -> 3   median change {np.median(delta):+.4f}   "
          f"sign agreement {agree:.0%}   p={p13:.4g}")
    print(f"  draft 1 -> 2   p={p12:.4g}")
    print(f"  change vs length change   {rho_len:+.3f} (p={p_len:.3f})"
          + ("   [length matched, so this should be ~0]" if args.length_matched else ""))

    verdict = ("PASS" if p13 < 0.01 and agree > 0.6 else
               "FAIL" if p13 > 0.05 else "AMBIGUOUS")
    print(f"\n  >>> {verdict}"
          + ("" if verdict == "PASS" else "  — no within-author movement in the reader's internals"))

    RESULTS.mkdir(parents=True, exist_ok=True)
    name = "probe_length_matched.json" if args.length_matched else "probe.json"
    (RESULTS / name).write_text(json.dumps(
        {"n": len(rows), "length_matched": args.length_matched,
         "mean_ratio": {str(d): statistics.fmean(r["ratio"][d] for r in rows) for d in (1, 2, 3)},
         "median_delta_1_3": float(np.median(delta)), "p_1_3": float(p13),
         "p_1_2": float(p12), "sign_agreement": agree,
         "delta_vs_length_change": float(rho_len), "verdict": verdict},
        indent=2), encoding="utf-8", newline="\n")
    print(f"\nwrote {(RESULTS / name).relative_to(REPO)}")


if __name__ == "__main__":
    main()
