"""Two questions the data on disk already answers, and nobody has asked either.

── QUESTION 1: DOES THE SIGNAL MOVE DEEPER AS INTENT RISES? ───────────────────────────────────

Observed 2026-08-07, across three ladders run at different manipulation strengths:

    first ladder     0/1/3/6/10 specifications     strongest layer 14
    held-out ladder  0/1/3/6/10 specifications     strongest layer 19
    extreme ladder   0/2/10/30/60 specifications   strongest layer 23

**The curator's reading:** *"as intention increases, later layers have to be used to extract it. We
need incredibly deep networks in order to extract the tiniest pieces."* If more specified intent
requires more depth to recover, that is a claim about what depth is *for* — and it predicts that the
strongest layer should shift **within** a single ladder, not only between ladders of different
strengths.

**Between-ladder is confounded three ways** — different corpora, different sizes, different seeds. So
this asks the question **within** one corpus: split the artifacts by rung, and for each rung
separately find where the intent signal peaks.

    SHIFTS       the peak layer rises monotonically with rung, in more than one corpus. Deeper intent
                 needs deeper machinery to read
    FIXED        the peak sits at the same depth regardless of rung, and the between-ladder difference
                 was corpus, not intent
    NOISE        the peak location is unstable within rung -- no claim either way

── QUESTION 2: DOES LATE COHERENCE RISE WHEN THE GOAL IS CLEAR? ───────────────────────────────

**Pre-registered in `docs/theory/THREE_COGNITIVE_LAYERS.md` §6e**, from the curator: *"you might also
have more agreement in the late, IF the goal is clear. What you get at the end is my guess. And the
middle -- yeah, it's convergent."*

So the coherence prediction is **conditional rather than flat** — an interaction between depth and how
clearly the goal is specified. On a ladder that is directly testable and **the depth sweep has been
emitting the ingredients all along without anyone reading the interaction out.**

Coherence here is how much the eight affect concepts **agree** with each other at a layer: high when
they point the same way, low when they scatter.

    CONDITIONAL  late-layer coherence rises with rung and middle-layer coherence does not
    FLAT         coherence does not track rung at any depth
    INVERTED     coherence falls with rung, which nothing predicts

**Neither question needs a GPU or a new corpus. Both are readouts of files already on disk**, which is
why they run first.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "depth_readouts"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpora", default="ladder,ladder2,ladder3")
    ap.add_argument("--model", default=None)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()

    import numpy as np                                               # noqa: PLC0415
    from scipy import stats                                          # noqa: PLC0415

    from soundingline.probe.activations import (DEFAULT_MODEL, Reader,  # noqa: PLC0415
                                                fit_directions)
    from runners.run_b import split                                  # noqa: PLC0415
    from runners.run_layer_ratio import windows                      # noqa: PLC0415

    model_name = args.model or DEFAULT_MODEL
    print(f"loading {model_name} ...", flush=True)
    reader = Reader(model_name, device=args.device)
    fit, _ = split()
    dirs = fit_directions(reader, fit)
    n_layers = dirs.n_layers
    concepts = list(dirs.concepts)

    out = {}
    for corpus in args.corpora.split(","):
        d = REPO / "corpora" / corpus
        man_path = d / "manifest.json"
        if not man_path.exists():
            print(f"  {corpus}: no manifest, skipping")
            continue
        man = json.loads(man_path.read_text(encoding="utf-8"))
        rows = []
        for it in man["items"]:
            p = d / f"{it['id']}.txt"
            if not p.exists():
                continue
            rung = it.get("rung")
            if not isinstance(rung, int):
                continue
            rows.append((rung, p.read_text(encoding="utf-8")))
        if len(rows) < 20:
            print(f"  {corpus}: {len(rows)} usable artifacts, skipping")
            continue
        print(f"\n{corpus}: {len(rows)} artifacts, {n_layers} layers", flush=True)

        sig = np.zeros((len(rows), n_layers))     # mean |affect projection| per layer
        coh = np.zeros((len(rows), n_layers))     # agreement among the eight concepts
        rungs = np.array([r for r, _ in rows], dtype=float)
        for i, (_, text) in enumerate(rows):
            ws = windows(text)
            s = np.zeros((len(ws), n_layers))
            c = np.zeros((len(ws), n_layers))
            for wi, w in enumerate(ws):
                p = dirs.project(reader.read(w))
                M = np.array([[p[cn][L] for L in range(n_layers)] for cn in concepts])
                s[wi] = np.abs(M).mean(0)
                # coherence: how much the eight concepts agree in sign and size at this layer
                denom = np.abs(M).sum(0)
                c[wi] = np.abs(M.sum(0)) / np.where(denom == 0, 1.0, denom)
            sig[i] = s.mean(0)
            coh[i] = c.mean(0)
            if (i + 1) % 25 == 0:
                print(f"  {i + 1}/{len(rows)}", flush=True)

        # ── Q1: where does the signal peak, per rung ──────────────────────────────────────────
        peaks = {}
        print(f"\n  {'rung':>6}{'n':>5}{'peak layer':>12}{'peak |rho| vs rung':>22}")
        print("  " + "-" * 46)
        for rung in sorted(set(rungs)):
            m = rungs == rung
            if m.sum() < 5:
                continue
            prof = sig[m].mean(0)
            pk = int(np.argmax(prof))
            peaks[float(rung)] = pk
            print(f"  {rung:>6.0f}{int(m.sum()):>5}{pk:>12}")
        ks = sorted(peaks)
        if len(ks) >= 3:
            r_peak, p_peak = stats.spearmanr(ks, [peaks[k] for k in ks])
        else:
            r_peak, p_peak = float("nan"), float("nan")
        print(f"\n  peak layer against rung: rho = {r_peak:+.3f}  (p = {p_peak:.3f})")

        # ── Q2: coherence against rung, per depth band ────────────────────────────────────────
        thirds = {"early": range(0, n_layers // 3),
                  "middle": range(n_layers // 3, 2 * n_layers // 3),
                  "late": range(2 * n_layers // 3, n_layers)}
        band = {}
        print(f"\n  {'band':>8}{'coherence vs rung':>20}{'p':>10}")
        print("  " + "-" * 38)
        for name, idx in thirds.items():
            v = coh[:, list(idx)].mean(1)
            r, p = stats.spearmanr(rungs, v)
            band[name] = {"rho": float(r), "p": float(p), "mean": float(v.mean())}
            print(f"  {name:>8}{r:>+20.3f}{p:>10.4f}")

        late, mid = band["late"], band["middle"]
        if late["p"] < 0.05 and late["rho"] > 0 and not (mid["p"] < 0.05 and mid["rho"] > 0):
            v2 = "CONDITIONAL"
        elif late["rho"] < 0 and late["p"] < 0.05:
            v2 = "INVERTED"
        else:
            v2 = "FLAT"
        v1 = ("SHIFTS" if (not np.isnan(r_peak) and r_peak > 0.7) else
              "FIXED" if (not np.isnan(r_peak) and abs(r_peak) < 0.4) else "NOISE")
        print(f"\n  >>> depth-of-peak: {v1}     late coherence: {v2}")
        out[corpus] = {"n": len(rows), "peak_by_rung": peaks,
                       "peak_vs_rung_rho": float(r_peak), "peak_vs_rung_p": float(p_peak),
                       "coherence": band, "verdict_peak": v1, "verdict_coherence": v2}

    RESULTS.mkdir(parents=True, exist_ok=True)
    tag = model_name.split("/")[-1]
    (RESULTS / f"{tag}.json").write_text(json.dumps(
        {"model": model_name, "corpora": out}, indent=2), encoding="utf-8", newline="\n")
    print(f"\nwrote {(RESULTS / f'{tag}.json').relative_to(REPO)}")

    if out:
        shifts = [v["verdict_peak"] for v in out.values()]
        print(f"\n  across {len(out)} corpora — depth-of-peak: "
              f"{', '.join(f'{k}={v[chr(39)]}' if False else f'{k}={v['verdict_peak']}' for k, v in out.items())}")


if __name__ == "__main__":
    main()
