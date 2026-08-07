"""Are the three layers three DEPTHS, or three SUBSPACES of one residual stream?

── THE QUESTION ──────────────────────────────────────────────────────────────────────────────

The architecture in `docs/theory/THREE_COGNITIVE_LAYERS.md` assumes a model reconstructs human
affective structure at three depths. **The evidence has been running against that.** Our own depth
sweep found the affective-response profile identical on intent-laden and no-maker text — a property
of the architecture carrying no information. And a 2026 study finds valence encoding emerging at
**very different depths in different model families**: early-then-collapse in one, late-progressive
in another.

**The curator's worry, stated 2026-08-07:** *"I do worry that there are no three layers in AI node
structures at all."* If there is no consistent shape, the whole bootstrap plan — supply a little
structure and let it converge — becomes a manual build instead.

── THE CANDIDATE WAY OUT ─────────────────────────────────────────────────────────────────────

We assumed depth-in-the-network maps onto depth-in-the-brain because both look like processing
stages. **A transformer's computation is strictly ordered — that is not in doubt.** What is in doubt
is whether *abstraction* is partitioned along that ordering, because **every layer reads from and
writes to the same residual stream.** There is no anatomical separation between stages.

> **So affect appearing throughout the layers is not evidence against three layers. It is evidence
> that layer index may not be where the structure lives.**

If the structure is a **subspace threaded through the whole stream** rather than a band of depths,
then the affect subspace measured at one layer should be largely the *same* subspace measured at
another — even where the *magnitude* profile across depth is architectural noise.

── WHAT THIS MEASURES ────────────────────────────────────────────────────────────────────────

Fit the affect directions at every layer, take the subspace they span, and compare subspaces across
depth using **principal angles** — the standard way to ask how much two subspaces overlap. Reported
as the mean cosine of the principal angles, where 1.0 is identical and 0.0 is orthogonal.

    alignment       mean principal-angle cosine between the affect subspace at layer i and layer j
    null            the same, for matched RANDOM subspaces of identical dimension. **In high
                    dimensions two random subspaces are near-orthogonal, so the null is close to
                    zero and any real overlap is visible against it**
    profile         the magnitude of affect response per layer -- the thing that turned out to be
                    architectural. Reported alongside so the two can be compared directly

── PRE-REGISTERED, BEFORE THE RUN ────────────────────────────────────────────────────────────

    SUBSPACE     alignment stays high across depth (mean well above its null, and not decaying to
                 the null at distant layer pairs) in EVERY model family tested. The structure is one
                 subspace threaded through the stream, we have been measuring the wrong axis, and
                 the bootstrap becomes a binding problem rather than an amplification problem
    DEPTH        alignment falls off with layer distance, so nearby layers share a subspace and
                 distant ones do not. Depth-partitioned after all, and the original architecture
                 survives
    NEITHER      alignment is at or near its null everywhere. **There is no coherent affect subspace
                 at all**, which is the worst outcome for the project and the one that would make
                 the build manual

**NEITHER is a live outcome and it retracts the most.** It is also the outcome the depth sweep's
result mildly predicts, so this is not a test the framework is expected to pass.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "subspace"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--n-random", type=int, default=20)
    args = ap.parse_args()

    import numpy as np                                               # noqa: PLC0415

    from soundingline.probe.activations import (DEFAULT_MODEL, Reader,  # noqa: PLC0415
                                                fit_directions)
    from runners.run_b import split                                  # noqa: PLC0415

    model_name = args.model or DEFAULT_MODEL
    print(f"loading {model_name} ...", flush=True)
    reader = Reader(model_name, device=args.device)
    fit, _ = split()
    dirs = fit_directions(reader, fit)
    n_layers = dirs.n_layers
    concepts = list(dirs.concepts)
    print(f"  {n_layers} layers, {len(concepts)} affect concepts\n", flush=True)

    def basis(L: int) -> np.ndarray:
        """Orthonormal basis for the subspace spanned by the affect directions at layer L."""
        M = np.array([np.asarray(dirs.vecs[c][L], dtype=float) for c in concepts])
        M = M - M.mean(0)
        q, _ = np.linalg.qr(M.T)
        return q[:, : min(M.shape[0], M.shape[1])]

    B = [basis(L) for L in range(n_layers)]
    widths = [b.shape[0] for b in B]
    k = min(b.shape[1] for b in B)

    def align(A: np.ndarray, C: np.ndarray) -> float:
        """Mean cosine of the principal angles between two subspaces."""
        s = np.linalg.svd(A[:, :k].T @ C[:, :k], compute_uv=False)
        return float(np.clip(s, 0, 1).mean())

    rng = np.random.default_rng(11)
    A_mat = np.zeros((n_layers, n_layers))
    for i in range(n_layers):
        for j in range(n_layers):
            A_mat[i, j] = align(B[i], B[j])

    # null: random subspaces of identical dimension in the same ambient width
    nulls = []
    for _ in range(args.n_random):
        R = []
        for L in range(n_layers):
            q, _ = np.linalg.qr(rng.standard_normal((widths[L], k)))
            R.append(q)
        nulls.append(np.mean([align(R[i], R[j])
                              for i in range(n_layers) for j in range(i + 1, n_layers)
                              if widths[i] == widths[j]]))
    null_mean = float(np.mean(nulls))
    null_hi = float(np.percentile(nulls, 97.5))

    off = [(i, j) for i in range(n_layers) for j in range(i + 1, n_layers)]
    mean_align = float(np.mean([A_mat[i, j] for i, j in off]))
    adjacent = float(np.mean([A_mat[i, i + 1] for i in range(n_layers - 1)]))
    distant = float(np.mean([A_mat[i, j] for i, j in off if j - i >= n_layers // 2]))

    print(f"{'layer pair distance':>22}{'mean alignment':>17}")
    print("-" * 40)
    for d in range(1, n_layers, max(1, n_layers // 8)):
        v = [A_mat[i, i + d] for i in range(n_layers - d)]
        print(f"{d:>22}{np.mean(v):>17.3f}")

    print(f"\n  adjacent layers        {adjacent:.3f}")
    print(f"  distant layers         {distant:.3f}")
    print(f"  all pairs              {mean_align:.3f}")
    print(f"  random subspace null   {null_mean:.3f}   (97.5th pct {null_hi:.3f})")
    print(f"  subspace dimension     {k} of {widths[0]}")

    beats_null = distant > null_hi
    decays = adjacent - distant > 0.15
    if not beats_null:
        verdict = "NEITHER"
    elif decays:
        verdict = "DEPTH"
    else:
        verdict = "SUBSPACE"
    print(f"\n  >>> {verdict}")
    if verdict == "SUBSPACE":
        print("  Distant layers share the affect subspace as much as adjacent ones.")
        print("  Layer index is not where the structure lives.")
    elif verdict == "DEPTH":
        print("  Alignment falls off with distance -- the structure is depth-partitioned.")
    else:
        print("  No coherent affect subspace at any distance. The worst outcome available.")

    RESULTS.mkdir(parents=True, exist_ok=True)
    tag = model_name.split("/")[-1]
    (RESULTS / f"{tag}.json").write_text(json.dumps(
        {"model": model_name, "n_layers": n_layers, "subspace_dim": k,
         "adjacent": adjacent, "distant": distant, "all_pairs": mean_align,
         "null_mean": null_mean, "null_hi": null_hi, "verdict": verdict,
         "matrix": A_mat.round(4).tolist()}, indent=2), encoding="utf-8", newline="\n")
    print(f"\nwrote {(RESULTS / f'{tag}.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
