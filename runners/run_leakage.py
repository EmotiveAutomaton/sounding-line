"""Option A — the leaked layer from function words. CPU only, no model.

Reports three things and never an affect label:

  1. per-half function-word rates, with the documented categories called out
  2. separability of the halves in function-word space (the D-0 statistic, run here on real text)
  3. per-artifact deviation from the corpus baseline

── WHAT THE FIRST RUN FOUND, RECORDED HERE BECAUSE IT IS A NEGATIVE ──────────────────────────

The documented categories DO differ sharply between the halves:

    half A    I=15.5   exclusive=8.2   negation=12.0   tentative=4.1
    half B    I= 5.7   exclusive=2.9   negation= 4.5   tentative=1.1

But the mean between/within variance ratio is **0.27** — within-half variance dominates, so this
is not a classifier. And the largest difference, first-person-singular, is very likely REGISTER
rather than leakage: personal essays say "I" and commercial pages do not. That is exactly the
baseline problem `measures/leakage.py` documents, and it is why a per-maker baseline is the thing
this needs and does not have.

**One speculation of mine was falsified cheaply, which is the point of building it.** I proposed
that exclusive words (`but`, `except`, `without`, `unless`) are a non-conscious lexical proxy for
the probe's `named_alternative_rate` — excluding a possibility requires having modelled it, which
is the depth construct in lexical form. Against Gate 2's readings: **rho = -0.22, p = 0.45, n = 14.**
Not supported, and in the wrong direction.

Caveat that keeps it honest: `named_alternative_rate` is itself a suspect measure — Gate 1 found
the previous stage-B wording turned `support` into a keyword detector. So this is two measures
disagreeing, not proof that exclusives carry nothing.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from soundingline.measures.leakage import (Baseline, CATEGORIES, DOCUMENTED,  # noqa: E402
                                           leakage, profile, separability)
from runners.run_gate3 import load_corpus                                     # noqa: E402

RESULTS = REPO / "results" / "leakage"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=6, help="most deviant artifacts to print")
    args = ap.parse_args()

    corpus = load_corpus()
    halves = {"A": [t for _, h, t in corpus if h == "A"],
              "B": [t for _, h, t in corpus if h == "B"]}
    print(f"corpus {len(corpus)}  A={len(halves['A'])} B={len(halves['B'])}  "
          f"(CPU only, no model)\n")

    print("DOCUMENTED CATEGORIES, rates per 1,000 tokens")
    print(f"  {'':<12}" + "".join(f"{k:>12}" for k in DOCUMENTED))
    for h, ts in halves.items():
        row = "".join(f"{statistics.fmean(profile(t).rates[k] for t in ts):>12.1f}"
                      for k in DOCUMENTED)
        print(f"  half {h:<7}{row}")

    sep = separability(halves)
    print(f"\nSEPARABILITY  mean between/within ratio = {sep['mean_ratio']:.2f}"
          f"   (1.0 = no group information)")
    for k, v in sep["top"]:
        print(f"    {k:<12} {v:.2f}")
    print("  >>> " + ("separates" if sep["mean_ratio"] > 1.0 else
                      "DOES NOT separate - within-half variance dominates"))

    base = Baseline.over([t for _, _, t in corpus])
    rows = [(aid, h, leakage(t, base)) for aid, h, t in corpus]
    rows.sort(key=lambda r: -r[2].magnitude)
    print(f"\nMOST DEVIANT from the corpus baseline (magnitude is NOT an affect reading)")
    for aid, h, lk in rows[: args.top]:
        top = "  ".join(f"{k}{v:+.1f}" for k, v in lk.most_deviant(3))
        print(f"    {aid:<14} {h}  |{lk.magnitude:5.2f}|   {top}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "leakage.json").write_text(json.dumps({
        "n": len(corpus),
        "separability": sep,
        "half_means": {h: {k: statistics.fmean(profile(t).rates[k] for t in ts)
                           for k in CATEGORIES} for h, ts in halves.items()},
        "artifacts": [{"id": a, "half": h, "magnitude": l.magnitude,
                       "z": l.z, "documented": l.documented} for a, h, l in rows],
    }, indent=2), encoding="utf-8")
    print(f"\nwrote {(RESULTS / 'leakage.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
