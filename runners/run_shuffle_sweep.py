"""Redo every verdict a WORD shuffle previously decided, using the granularity curve instead.

── WHY ───────────────────────────────────────────────────────────────────────────────────────

`results/rung_minus1/VERDICT.md` measured the thing the word shuffle actually does to an
order-sensitive measure. On the ladder, where register/topic/format/generator are constant by
construction:

    the whole ladder, rung 0 -> rung 10        0.050
    what word-shuffling moves the layer ratio  0.140      ~3x the signal

**A control that perturbs a measure three times harder than the effect it is adjudicating is not a
control.** So `results/layer_ratio/VERDICT_CONTROL.md`'s C1 -- which concluded "the human/machine
gap is vocabulary, 121% survival" -- was retracted. This runner replaces it.

── WHAT IS RUN ───────────────────────────────────────────────────────────────────────────────

The human/machine layer-ratio comparison at all four granularities, plus a positive control that
has a known answer.

    paragraph   destroys argument order       stays grammatical, in distribution
    sentence    destroys discourse flow       stays grammatical, in distribution   <- the verdict
    phrase      destroys syntax               leaves the local window
    word        destroys everything           out of distribution; reported, not trusted

── PRE-REGISTERED, BEFORE THE RUN ────────────────────────────────────────────────────────────

The verdict is taken at the SENTENCE grain, because that is the coarsest perturbation that both
stays in distribution and destroys the order a reader would use to follow an argument.

    ORDER      the gap shrinks by more than half under sentence-shuffling
               -> the measure reads something structural
    LEXICAL    the gap is essentially unchanged under sentence-shuffling
               -> it is carried by word choice and/or register; C3 already says register
    NOISE      the gap grows                                  -> as with the word shuffle, the
               perturbation has moved the measure rather than ablated it, and the grain is void

**C3 is not re-run and does not need to be.** It is a construction control -- half B is commercial
copy, and it landed 26% of the way from half A toward machine at p = 0.0033. It never depended on
shuffling and it already settles that this is not a human/machine discriminator. What is open is
*why*, and that is what this measures.

── THE POSITIVE CONTROL, AND IT HAS A KNOWN ANSWER ───────────────────────────────────────────

Burrows' Delta on author identification is a forty-year-old solved result and it is **provably
permutation-invariant** -- it is built from function-word frequencies, so no shuffle at any grain
can move it.

Running it here is not a test of Delta. **It is a test of the harness.** If author ID does not come
back at ~7.6x, or if any grain moves it at all, the shuffling code is wrong and every number in this
file is void. That is the check that would have caught `separability()` four results earlier.
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

from runners.run_rung_minus1 import GRAINS                              # noqa: E402

RESULTS = REPO / "results" / "shuffle_sweep"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--model", default=None)
    ap.add_argument("--seed", type=int, default=47)
    ap.add_argument("--gate3", type=int, default=30)
    args = ap.parse_args()

    from scipy import stats                                             # noqa: PLC0415
    from soundingline.measures.leakage import delta_classify            # noqa: PLC0415
    from runners.run_gate3 import load_corpus                           # noqa: PLC0415

    out: dict = {"seed": args.seed}

    # ── the positive control: a known answer, run FIRST ───────────────────────────────────────
    print("=" * 72)
    print("POSITIVE CONTROL -- author ID via Burrows' Delta.")
    print("Known answer ~7.6x. Permutation-invariant, so every grain must return the SAME number.")
    print("If it does not, the harness is broken and nothing below is readable.")
    print("=" * 72, flush=True)

    from runners.run_g import load_books, windows                      # noqa: PLC0415

    by_author: dict[str, list[str]] = {}
    for b in load_books():
        # 4,000-word windows, the length G-1 reported 7.6x at, capped so a long book
        # cannot outvote a short one.
        by_author.setdefault(b["author"], []).extend(windows(b["text"], 4000, cap=4))

    pc = {}
    if len(by_author) >= 3:
        base = delta_classify(by_author)
        print(f"  intact      {base['accuracy']:.1%} vs {base['chance']:.1%} "
              f"= {base['lift']:.2f}x", flush=True)
        pc["intact"] = base
        for gname, gfun in GRAINS.items():
            rng = random.Random(args.seed)
            g = {a: [gfun(t, rng) for t in ts] for a, ts in by_author.items()}
            r = delta_classify(g)
            same = abs(r["accuracy"] - base["accuracy"]) < 1e-9
            print(f"  {gname:<10}  {r['accuracy']:.1%}  = {r['lift']:.2f}x   "
                  f"{'ok — invariant' if same else '>>> HARNESS FAULT: a grain moved it'}",
                  flush=True)
            pc[gname] = {**r, "invariant": same}
        pc["harness_ok"] = all(v.get("invariant", True) for v in pc.values()
                               if isinstance(v, dict))
    else:
        print("  SKIPPED — book corpus not loadable; the sweep below is unvalidated")
        pc["harness_ok"] = None
    out["positive_control"] = pc
    print(flush=True)

    # ── the sweep ─────────────────────────────────────────────────────────────────────────────
    from soundingline.probe.activations import (DEFAULT_MODEL, Reader,   # noqa: PLC0415
                                                fit_directions)
    from runners.run_b import split                                      # noqa: PLC0415
    from runners.run_layer_ratio import ratio_for, load                  # noqa: PLC0415

    name = args.model or DEFAULT_MODEL
    print(f"loading {name} on {args.device} ...", flush=True)
    reader = Reader(name, device=args.device)
    fit, _ = split()
    print("fitting affect directions ...", flush=True)
    dirs = fit_directions(reader, fit)
    print(f"  {len(dirs.concepts)} concepts x {dirs.n_layers} layers\n", flush=True)

    human = [t for _, _, t in load_corpus()[: args.gate3]]
    machine = [x["text"] for x in load(REPO / "corpora" / "nomaker", "kind")]
    print(f"human n={len(human)}   machine n={len(machine)}\n", flush=True)

    def gap(hs: list[str], ms: list[str]) -> dict:
        h = [ratio_for(reader, dirs, t) for t in hs]
        m = [ratio_for(reader, dirs, t) for t in ms]
        t, p = stats.ttest_ind(h, m, equal_var=False)
        return {"human": statistics.fmean(h), "machine": statistics.fmean(m),
                "gap": statistics.fmean(h) - statistics.fmean(m), "p": float(p)}

    base = gap(human, machine)
    print(f"{'grain':<12}{'human':>9}{'machine':>10}{'gap':>10}{'p':>11}{'vs intact':>12}")
    print(f"{'intact':<12}{base['human']:>9.4f}{base['machine']:>10.4f}"
          f"{base['gap']:>+10.4f}{base['p']:>11.2e}{'—':>12}")
    out["intact"] = base

    for gname, gfun in GRAINS.items():
        rng = random.Random(args.seed)
        r = gap([gfun(t, rng) for t in human], [gfun(t, rng) for t in machine])
        frac = r["gap"] / base["gap"] if base["gap"] else float("nan")
        r["gap_fraction_of_intact"] = frac
        print(f"{gname:<12}{r['human']:>9.4f}{r['machine']:>10.4f}"
              f"{r['gap']:>+10.4f}{r['p']:>11.2e}{frac:>11.0%}")
        out[gname] = r

    # ── the verdict, taken at the sentence grain as pre-registered ────────────────────────────
    f = out["sentence"]["gap_fraction_of_intact"]
    verdict = ("ORDER" if f < 0.5 else
               "NOISE" if f > 1.05 else
               "LEXICAL")
    out["verdict"] = verdict
    out["verdict_grain"] = "sentence"
    print("\n" + "=" * 72)
    print(f">>> {verdict} — the gap retains {f:.0%} of itself under sentence-shuffling")
    if verdict == "LEXICAL":
        print("    Carried by word choice and/or register. C3 already identifies register:")
        print("    commercial copy sits 26% of the way from essays toward machine, p=0.0033.")
    elif verdict == "ORDER":
        print("    The gap needs discourse order. That would be the first time on human text.")
    else:
        print("    The perturbation moved the measure rather than ablating it. Grain void.")
    print("=" * 72)

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "shuffle_sweep.json").write_text(
        json.dumps(out, indent=2, default=float), encoding="utf-8")
    print(f"\nwrote {(RESULTS / 'shuffle_sweep.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
