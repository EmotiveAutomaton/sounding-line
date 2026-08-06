"""Is our affect ratio measuring affect, or is it measuring the size of the activations?

── WHY THIS EXISTS, AND IT IS URGENT ─────────────────────────────────────────────────────────

The project's only replicated measure is a **ratio of affective activation in early layers to late
layers**. A literature sweep returned a null explanation that would produce that measure's entire
behaviour with **no affect involved at all**:

    projection = ||h|| * cos(theta)

Residual-stream norms grow with depth — roughly 8x across a large model — and separately, "massive
activations" concentrated in one or two dimensions appear around layer 2, hold steady, and fade in
the last few layers. **That is exactly the high-early, low-late shape we have been reading as
leaked affect.**

**The dispositive test is cheap.** For a random unit vector u, the expected absolute projection is
proportional to ||h||/sqrt(d). So **a random direction's early:late ratio IS the norm curve.** If our
affect directions do not separate from a random-direction null, we have spent three days plotting the
norm of the residual stream.

── WHAT IS MEASURED ──────────────────────────────────────────────────────────────────────────

Three quantities on the same texts, same windows, same layers:

    affect      the fitted affect directions -- what we have been using
    random      matched random unit directions, same count, same per-layer standardisation
    norm        the raw residual-stream norm ratio, early vs late, no directions at all

── PRE-REGISTERED, BEFORE THE RUN ────────────────────────────────────────────────────────────

    SURVIVES   the affect ratio sits outside the middle 95% of the random-direction ratios, AND
               its correlation with specified intent is not reproduced by random directions
    DEAD       random directions give the same ratio and the same rung correlation. The measure is
               the norm curve wearing a costume
    PARTIAL    affect separates on magnitude but random directions also track rung -- meaning the
               rung effect is architectural rather than affective

**The second outcome would retire the measure**, and with it the only replicated effect this project
has. That is the point of running it.

Method credit: the random-direction control was proposed by a literature scout, from
Timkey & van Schijndel on rogue dimensions and Sun et al. on massive activations.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "random_null"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="ladder2")
    ap.add_argument("--n-random", type=int, default=20)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()

    import numpy as np                                               # noqa: PLC0415
    import torch                                                     # noqa: PLC0415
    from scipy import stats                                          # noqa: PLC0415

    from soundingline.probe.activations import (DEFAULT_MODEL, Reader,  # noqa: PLC0415
                                                fit_directions)
    from runners.run_b import split                                  # noqa: PLC0415
    from runners.run_layer_ratio import WINDOW_WORDS, windows        # noqa: PLC0415

    print(f"loading {DEFAULT_MODEL} ...", flush=True)
    reader = Reader(DEFAULT_MODEL, device=args.device)
    fit, _ = split()
    dirs = fit_directions(reader, fit)
    n_layers = dirs.n_layers
    lo_hi = max(2, round(n_layers * 0.07))
    hi_lo = round(n_layers * 0.76)
    print(f"  {len(dirs.concepts)} concepts x {n_layers} layers; "
          f"early 0..{lo_hi - 1}, late {hi_lo}..{n_layers - 1}\n", flush=True)

    d = REPO / "corpora" / args.corpus
    man = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
    items = [(it["rung"], (d / f"{it['id']}.txt").read_text(encoding="utf-8"))
             for it in man["items"] if (d / f"{it['id']}.txt").exists()]
    print(f"{args.corpus}: {len(items)} artifacts", flush=True)

    # random unit directions, matched in count and shape to the fitted ones
    rng = np.random.default_rng(11)
    probe = reader.read("a short probe sentence for shape")
    widths = [len(probe.acts[L]) for L in range(n_layers)]
    rand_dirs = [[rng.standard_normal(widths[L]) for L in range(n_layers)]
                 for _ in range(args.n_random)]
    print(f"  hidden width {widths[0]}; {args.n_random} random directions per layer\n",
          flush=True)

    def ratios(text: str) -> tuple[float, float, list[float]]:
        """affect ratio, raw-norm ratio, and one ratio per random direction, same windows.

        **The random directions are z-scored with the SAME per-layer mu/sd and compared by COSINE**,
        exactly as `Directions.project` does. That matters: our measure was already scale-invariant
        by construction, so the residual-norm objection does not apply to it directly. The raw-norm
        ratio is reported anyway, so the size of that non-threat is visible rather than assumed.
        """
        import math                                                  # noqa: PLC0415
        a_e, a_l, n_e, n_l = [], [], [], []
        rand_e = [[] for _ in range(args.n_random)]
        rand_l = [[] for _ in range(args.n_random)]
        for w in windows(text):
            acts = reader.read(w)
            p = dirs.project(acts)
            a_e.append(statistics.fmean(abs(v[L]) for v in p.values() for L in range(lo_hi)))
            a_l.append(statistics.fmean(abs(v[L]) for v in p.values()
                                        for L in range(hi_lo, n_layers)))
            zs, norms = [], []
            for L in range(n_layers):
                h = np.asarray(acts.acts[L], dtype=float)
                norms.append(float(np.linalg.norm(h)))
                mu = np.asarray(dirs.mu[L], dtype=float)
                sd = np.asarray(dirs.sd[L], dtype=float)
                zs.append((h - mu) / np.where(sd == 0, 1.0, sd))
            n_e.append(statistics.fmean(norms[:lo_hi]))
            n_l.append(statistics.fmean(norms[hi_lo:]))
            for r in range(args.n_random):
                cos = []
                for L in range(n_layers):
                    z = zs[L]
                    u = rand_dirs[r][L]
                    denom = np.linalg.norm(z) * np.linalg.norm(u)
                    cos.append(abs(float(z @ u) / denom) if denom else 0.0)
                rand_e[r].append(statistics.fmean(cos[:lo_hi]))
                rand_l[r].append(statistics.fmean(cos[hi_lo:]))
        af = statistics.fmean(a_e) / statistics.fmean(a_l)
        nr = statistics.fmean(n_e) / statistics.fmean(n_l)
        rr = [statistics.fmean(rand_e[r]) / statistics.fmean(rand_l[r])
              for r in range(args.n_random)]
        return af, nr, rr

    rows = []
    for i, (rung, text) in enumerate(items):
        af, nr, rr = ratios(text)
        rows.append({"rung": rung, "affect": af, "norm": nr, "random": rr})
        if (i + 1) % 20 == 0:
            print(f"  {i + 1}/{len(items)}", flush=True)

    rung = [r["rung"] for r in rows]
    aff = [r["affect"] for r in rows]
    nrm = [r["norm"] for r in rows]
    rnd = np.array([r["random"] for r in rows])          # artifacts x n_random

    print(f"\n{'quantity':<26}{'mean ratio':>12}{'rho vs rung':>13}{'p':>10}")
    print("-" * 62)
    ra, pa = stats.spearmanr(rung, aff)
    print(f"{'AFFECT directions':<26}{statistics.fmean(aff):>12.4f}{ra:>+13.3f}{pa:>10.4f}")
    rn, pn = stats.spearmanr(rung, nrm)
    print(f"{'raw residual norm':<26}{statistics.fmean(nrm):>12.4f}{rn:>+13.3f}{pn:>10.4f}")
    rhos = [stats.spearmanr(rung, rnd[:, r]).statistic for r in range(args.n_random)]
    print(f"{'random directions':<26}{rnd.mean():>12.4f}{np.mean(rhos):>+13.3f}"
          f"{'':>10}   (spread {np.percentile(rhos, 2.5):+.3f} to {np.percentile(rhos, 97.5):+.3f})")

    mag_sep = not (np.percentile(rnd.mean(0), 2.5) <= statistics.fmean(aff)
                   <= np.percentile(rnd.mean(0), 97.5))
    rho_sep = not (np.percentile(rhos, 2.5) <= ra <= np.percentile(rhos, 97.5))
    verdict = ("SURVIVES" if mag_sep and rho_sep else
               "DEAD" if not rho_sep else "PARTIAL")
    print(f"\n  magnitude separates from random: {mag_sep}")
    print(f"  rung correlation separates:      {rho_sep}")
    print(f"\n  >>> {verdict}")
    if verdict == "DEAD":
        print("      Random directions reproduce the rung effect. The measure is the residual")
        print("      norm curve, and every result built on it needs withdrawing.")

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"{args.corpus}.json").write_text(json.dumps(
        {"corpus": args.corpus, "n": len(rows), "n_random": args.n_random,
         "affect_mean": statistics.fmean(aff), "affect_rho": float(ra), "affect_p": float(pa),
         "norm_mean": statistics.fmean(nrm), "norm_rho": float(rn),
         "random_mean": float(rnd.mean()), "random_rho_mean": float(np.mean(rhos)),
         "random_rho_ci": [float(np.percentile(rhos, 2.5)), float(np.percentile(rhos, 97.5))],
         "magnitude_separates": bool(mag_sep), "rho_separates": bool(rho_sep),
         "verdict": verdict}, indent=2), encoding="utf-8", newline="\n")
    print(f"\nwrote {(RESULTS / f'{args.corpus}.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
