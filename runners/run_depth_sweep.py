"""The depth sweep — every layer, with its own null, and the four questions that need it.

── WHY ONE RUNNER FOR FOUR QUESTIONS ─────────────────────────────────────────────────────────

They all need the same expensive thing: affect-direction scores at **every** layer, over many texts.
Computing that once and asking four questions of it costs a quarter of what asking separately would.

    G1  is the depth profile one-, two- or three-humped?   we found two; the field mostly finds one;
                                                            the curator predicts three
    G2  is the middle NOISY or SILENT?                      a two-way split smears a present-but-
                                                            incoherent middle into both halves
    G4  does each layer beat a RANDOM direction?            the magnitude of our old ratio did not
    H2  is there a fast-then-persistent structure?          the 2025 cross-species biphasic result

── AND IT RETIRES A KNOWN WEAKNESS ───────────────────────────────────────────────────────────

Every layer-ratio result so far used **two hand-picked loci** chosen by looking at a prior result on
the same model. That is a forking path and it has been flagged in `FINDINGS.md` since the loci were
chosen. **Sweeping every layer removes the choice entirely** — the profile is reported, not selected.

── THE FOUR MEASUREMENTS, PER LAYER ──────────────────────────────────────────────────────────

    signal        mean |cosine| against the fitted affect directions
    coherence     agreement ACROSS the eight concepts at that layer. High signal with low coherence
                  is the curator's "noisy middle"; low signal is a silent one. **These are different
                  and no previous run could tell them apart.**
    null          the same statistics for matched random directions, z-scored identically.
                  Every layer carries its own null, so no claim rests on an unpriced comparison
    rung          correlation with specified intent at that layer alone

── PRE-REGISTERED, BEFORE THE RUN ────────────────────────────────────────────────────────────

**Written before looking, because the stopping criterion is what drives the answer** — Lin & Adolphs
(2025) recovered 27 dimensions versus 3 from identical stimuli by varying exactly that choice.

    peaks         a maximum in signal-above-null whose PROMINENCE -- its rise above the surrounding
                  troughs -- exceeds 10% of the full excess range, and which also clears its own
                  null. Prominence rather than bare local maxima, because a smoke test on six
                  artifacts returned "6-MODAL" purely from noise. That is the artifact Lin & Adolphs
                  (2025) describe, where the number of components is set by the stopping criterion
                  rather than the data, and the fix was applied BEFORE the real run.
    TRIMODAL      three such peaks
    BIMODAL       two
    UNIMODAL      one -- which is what most of the field reports
    NOISY MIDDLE  a middle region where signal is above null AND coherence is below its own median
    SILENT MIDDLE signal at or below null in the middle

**No outcome here is favourable or unfavourable to the project.** The architecture predicts three
peaks and a noisy middle; the literature's modal finding is one peak. Both are stated in advance.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "depth_sweep"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="ladder2")
    ap.add_argument("--model", default=None)
    ap.add_argument("--n-random", type=int, default=12)
    ap.add_argument("--cap", type=int, default=0)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()

    import numpy as np                                               # noqa: PLC0415
    from scipy import stats                                          # noqa: PLC0415

    from soundingline.probe.activations import (DEFAULT_MODEL, Reader,  # noqa: PLC0415
                                                fit_directions)
    from runners.run_b import split                                  # noqa: PLC0415
    from runners.run_layer_ratio import windows                      # noqa: PLC0415

    model_name = args.model or DEFAULT_MODEL
    print(f"loading {model_name} on {args.device} ...", flush=True)
    reader = Reader(model_name, device=args.device)
    fit, _ = split()
    dirs = fit_directions(reader, fit)
    n_layers = dirs.n_layers
    concepts = list(dirs.concepts)
    print(f"  {len(concepts)} concepts x {n_layers} layers\n", flush=True)

    d = REPO / "corpora" / args.corpus
    man = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
    items = [(it.get("rung", 0), (d / f"{it['id']}.txt").read_text(encoding="utf-8"))
             for it in man["items"] if (d / f"{it['id']}.txt").exists()]
    if args.cap:
        items = items[: args.cap]
    print(f"{args.corpus}: {len(items)} artifacts", flush=True)

    rng = np.random.default_rng(5)
    probe = reader.read("shape probe")
    widths = [len(probe.acts[L]) for L in range(n_layers)]
    rand = [[rng.standard_normal(widths[L]) for L in range(n_layers)]
            for _ in range(args.n_random)]

    sig = np.zeros((len(items), n_layers))
    coh = np.zeros((len(items), n_layers))
    nul = np.zeros((len(items), n_layers))
    rungs = np.array([r for r, _ in items], dtype=float)

    for i, (_, text) in enumerate(items):
        ws = windows(text)
        s = np.zeros((len(ws), n_layers))
        c = np.zeros((len(ws), n_layers))
        n = np.zeros((len(ws), n_layers))
        for wi, w in enumerate(ws):
            acts = reader.read(w)
            p = dirs.project(acts)
            M = np.array([[p[cc][L] for L in range(n_layers)] for cc in concepts])
            s[wi] = np.abs(M).mean(0)
            # coherence: how much the eight concepts agree at this layer. A single dominant
            # direction gives high coherence; eight disagreeing ones give low.
            for L in range(n_layers):
                col = M[:, L]
                denom = np.abs(col).sum()
                c[wi, L] = (abs(col.sum()) / denom) if denom > 1e-12 else 0.0
            for L in range(n_layers):
                h = np.asarray(acts.acts[L], dtype=float)
                mu = np.asarray(dirs.mu[L], dtype=float)
                sd = np.asarray(dirs.sd[L], dtype=float)
                z = (h - mu) / np.where(sd == 0, 1.0, sd)
                zn = np.linalg.norm(z)
                vals = [abs(float(z @ u) / (zn * np.linalg.norm(u))) if zn else 0.0
                        for u in (rand[r][L] for r in range(args.n_random))]
                n[wi, L] = statistics.fmean(vals)
        sig[i], coh[i], nul[i] = s.mean(0), c.mean(0), n.mean(0)
        if (i + 1) % 20 == 0:
            print(f"  {i + 1}/{len(items)}", flush=True)

    excess = sig.mean(0) - nul.mean(0)
    null_sd = nul.std(0)
    coh_m = coh.mean(0)
    coh_med = float(np.median(coh_m))

    print(f"\n{'layer':>6}{'signal':>10}{'null':>9}{'excess':>10}{'coherence':>11}"
          f"{'rho vs rung':>13}")
    print("-" * 60)
    rhos = []
    for L in range(n_layers):
        r, _ = stats.spearmanr(rungs, sig[:, L]) if len(set(rungs)) > 1 else (float("nan"), 1)
        rhos.append(float(r))
        mark = " <" if excess[L] > null_sd[L] else ""
        print(f"{L:>6}{sig[:, L].mean():>10.4f}{nul[:, L].mean():>9.4f}{excess[L]:>+10.4f}"
              f"{coh_m[L]:>11.3f}{r:>+13.3f}{mark}")

    # peaks: local maxima in excess that clear the null's own spread
    # PROMINENCE, not bare local maxima. A smoke test on 6 artifacts returned "6-MODAL" from
    # noise, which is exactly the artifact Lin & Adolphs (2025) describe: the answer is set by the
    # stopping criterion. Fixed here BEFORE the real run: a peak must rise above its surrounding
    # troughs by at least 10% of the full excess range.
    from scipy.signal import find_peaks                              # noqa: PLC0415
    prominence = 0.10 * float(np.ptp(excess))
    peaks = [int(x) for x in find_peaks(excess, prominence=prominence)[0]
             if excess[x] > null_sd[x]]
    shape = {3: "TRIMODAL", 2: "BIMODAL", 1: "UNIMODAL"}.get(len(peaks), f"{len(peaks)}-MODAL")

    mid = slice(n_layers // 3, 2 * n_layers // 3)
    mid_above = bool((excess[mid] > null_sd[mid]).mean() > 0.5)
    mid_incoherent = bool(coh_m[mid].mean() < coh_med)
    middle = ("NOISY (signal above null, coherence below median)" if mid_above and mid_incoherent
              else "SILENT (signal at or below null)" if not mid_above
              else "COHERENT (signal above null, coherence at or above median)")

    print(f"\n  peaks at layers {peaks}  ->  {shape}")
    print(f"  middle third: {middle}")
    print(f"  layers beating their own null: {int((excess > null_sd).sum())}/{n_layers}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    tag = f"{args.corpus}_{model_name.split('/')[-1]}"
    (RESULTS / f"{tag}.json").write_text(json.dumps(
        {"corpus": args.corpus, "model": model_name, "n": len(items), "n_layers": n_layers,
         "signal": sig.mean(0).tolist(), "null": nul.mean(0).tolist(),
         "excess": excess.tolist(), "null_sd": null_sd.tolist(),
         "coherence": coh_m.tolist(), "rho_vs_rung": rhos,
         "peaks": peaks, "shape": shape, "middle": middle,
         "layers_beating_null": int((excess > null_sd).sum())},
        indent=2), encoding="utf-8", newline="\n")
    print(f"\nwrote {(RESULTS / f'{tag}.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
