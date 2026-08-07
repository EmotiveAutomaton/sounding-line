"""Is the component count a property of the text, or a property of how much text we read?

── WHY THIS EXISTS ───────────────────────────────────────────────────────────────────────────

`run_decomposition.py` reported **49.3 components** in the middle layers at 1,200 utterances and
**92.9** at 5,000, in the same model on the same corpus with every setting frozen. That is not a
measurement of anything. **A quantity that roughly doubles when you quadruple the sample is tracking
the sample.**

The curator predicted exactly this before seeing it: *"deciding on where to cut off a PCA is one of
the things that has an art to it in science."* This runner turns the art into a curve.

── THE PROBLEM, STATED PROPERLY ──────────────────────────────────────────────────────────────

Parallel analysis compares each eigenvalue against the 95th percentile of eigenvalues from
column-shuffled data of identical shape. When the number of dimensions is comparable to or larger
than the number of samples (here 896–2048 dimensions against 1,200 rows), the sample eigenvalue
spectrum is dominated by **Marchenko-Pastur** noise, and the shuffled null does not correct for it,
because shuffling preserves the aspect ratio that causes the problem. **The criterion is
n-dependent by construction and nobody should have expected otherwise.**

── WHAT THIS RUNS ────────────────────────────────────────────────────────────────────────────

Read activations **once** at the largest affordable sample, cache them, then subsample. Every
criterion sees identical text at every sample size, so the only thing varying is n.

Four criteria, chosen because they fail in different ways:

    parallel        the one we used. Expected to climb with n
    kaiser          eigenvalue > 1. Expected to climb with n
    var90           components to reach 90% of variance. Expected to climb with n
    cross-validated held out ENTRIES of the matrix, reconstruct them from k components, and keep the
                    k that minimises held-out error. **This one has a real stopping point** -- adding
                    components past the true rank makes held-out error worse, not better, so it can
                    go down as well as up
    participation   a continuous dimensionality: (sum of eigenvalues)^2 / sum of (eigenvalues^2).
                    No threshold at all, so no threshold to tune. Standard in systems neuroscience

── AND A NULL THAT SHOULD RETURN NOTHING ─────────────────────────────────────────────────────

The same pipeline on **row-shuffled activations** -- every dimension independently permuted across
utterances, which destroys all cross-dimension structure while keeping each dimension's marginal
distribution exactly. **A criterion that reports many components here is reporting noise.** This is
the control the original run did not have.

── PRE-REGISTERED, BEFORE THE RUN ────────────────────────────────────────────────────────────

    STABLE      the cross-validated count and the participation ratio both flatten by the largest n,
                agreeing within a factor of two. Then there IS a number and we can quote it
    UNSTABLE    they keep climbing like parallel analysis does. Then no count is available from this
                method at this sample size, and the honest report is a lower bound
    NULL-FAIL   the shuffled control returns a large count. Then the criterion is broken outright and
                every number it has produced is void

**NULL-FAIL is the outcome that would retract the most.** It is also the one worth running first.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "decomp_scaling"
CACHE = REPO / "results" / "decomp_scaling" / "cache"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=4000, help="utterances to read once, then subsample")
    ap.add_argument("--model", default=None)
    ap.add_argument("--min-words", type=int, default=12)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--repeats", type=int, default=3, help="subsamples per sample size")
    args = ap.parse_args()

    import numpy as np                                               # noqa: PLC0415

    from soundingline.probe.activations import DEFAULT_MODEL, Reader  # noqa: PLC0415

    model_name = args.model or DEFAULT_MODEL
    tag = model_name.split("/")[-1]
    CACHE.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE / f"{tag}_{args.n}.npz"

    if cache_file.exists():
        print(f"loading cached activations from {cache_file.name} ...", flush=True)
        z = np.load(cache_file)
        acts = [z[f"L{i}"] for i in range(int(z["n_layers"]))]
    else:
        from datasets import load_dataset                            # noqa: PLC0415

        print(f"loading {model_name} ...", flush=True)
        reader = Reader(model_name, device=args.device)

        print("streaming the human portion of jzhang92/LLM-Emotion ...", flush=True)
        ds = load_dataset("jzhang92/LLM-Emotion", split="train", streaming=True)
        texts = []
        for row in ds:
            if str(row.get("source", "")).lower() != "raw":
                continue
            t = row.get("text") or row.get("utterance") or row.get("content") or ""
            if not isinstance(t, str) or len(t.split()) < args.min_words:
                continue
            texts.append(t)
            if len(texts) >= args.n:
                break
        print(f"  {len(texts)} human utterances\n", flush=True)

        probe = reader.read("shape probe")
        n_layers = probe.n_layers
        acts = [np.zeros((len(texts), len(probe.acts[L])), dtype=np.float32)
                for L in range(n_layers)]
        for i, t in enumerate(texts):
            a = reader.read(t)
            for L in range(n_layers):
                acts[L][i] = np.asarray(a.acts[L], dtype=np.float32)
            if (i + 1) % 500 == 0:
                print(f"  read {i + 1}/{len(texts)}", flush=True)
        np.savez_compressed(cache_file, n_layers=n_layers,
                            **{f"L{i}": acts[i] for i in range(n_layers)})
        print(f"  cached to {cache_file.name}\n", flush=True)

    n_layers = len(acts)
    N = acts[0].shape[0]
    rng = np.random.default_rng(19)

    def eigs(X):
        Z = (X - X.mean(0)) / np.where(X.std(0) == 0, 1.0, X.std(0))
        Z = Z[:, np.isfinite(Z).all(0)]
        k = min(Z.shape) - 1
        return np.linalg.svd(Z, compute_uv=False)[:k] ** 2 / (Z.shape[0] - 1), Z

    def criteria(X: np.ndarray) -> dict:
        ev, Z = eigs(X)
        nulls = []
        for _ in range(3):
            S = np.column_stack([rng.permutation(Z[:, j]) for j in range(Z.shape[1])])
            nulls.append(np.linalg.svd(S, compute_uv=False)[:len(ev)] ** 2 / (S.shape[0] - 1))
        thresh = np.percentile(np.array(nulls), 95, axis=0)
        var = ev / ev.sum()
        # participation ratio: continuous, threshold-free
        pr = float(ev.sum() ** 2 / (ev ** 2).sum())
        # cross-validated: hold out a random 10% of MATRIX ENTRIES, reconstruct from k components
        mask = rng.random(Z.shape) < 0.10
        Ztr = Z.copy()
        Ztr[mask] = 0.0
        U, S_, Vt = np.linalg.svd(Ztr, full_matrices=False)
        best_k, best_err = 0, float(np.mean(Z[mask] ** 2))
        errs = []
        ks = [k for k in range(1, min(120, len(S_)) + 1)]
        for k in ks:
            R = (U[:, :k] * S_[:k]) @ Vt[:k]
            e = float(np.mean((Z[mask] - R[mask]) ** 2))
            errs.append(e)
            if e < best_err:
                best_err, best_k = e, k
        return {"parallel": int((ev > thresh).sum()),
                "kaiser": int((ev > 1.0).sum()),
                "var90": int(np.searchsorted(np.cumsum(var), 0.90) + 1),
                "cv": int(best_k),
                "participation": pr}

    sizes = [n for n in (150, 300, 600, 1200, 2400, 4000) if n <= N]
    mids = list(range(n_layers // 3, 2 * n_layers // 3))
    print(f"{tag}: {N} utterances, {n_layers} layers, "
          f"middle layers {mids[0]}-{mids[-1]}\n", flush=True)

    out = []
    print(f"{'n':>6}{'parallel':>10}{'kaiser':>9}{'var90':>8}{'cross-val':>11}"
          f"{'particip.':>11}{'shuffled':>10}")
    print("-" * 65)
    for n in sizes:
        agg = {k: [] for k in ("parallel", "kaiser", "var90", "cv", "participation")}
        nullpar = []
        for rep in range(args.repeats):
            idx = rng.choice(N, size=n, replace=False)
            for L in mids:
                X = acts[L][idx].astype(float)
                c = criteria(X)
                for k in agg:
                    agg[k].append(c[k])
            # the null: one middle layer, every dimension independently permuted across rows
            L = mids[len(mids) // 2]
            Xn = acts[L][idx].astype(float).copy()
            for j in range(Xn.shape[1]):
                Xn[:, j] = rng.permutation(Xn[:, j])
            nullpar.append(criteria(Xn)["parallel"])
        row = {"n": n, **{k: float(np.mean(v)) for k, v in agg.items()},
               "shuffled_parallel": float(np.mean(nullpar))}
        out.append(row)
        print(f"{n:>6}{row['parallel']:>10.1f}{row['kaiser']:>9.1f}{row['var90']:>8.1f}"
              f"{row['cv']:>11.1f}{row['participation']:>11.1f}"
              f"{row['shuffled_parallel']:>10.1f}")

    def growth(key):
        a, b = out[0][key], out[-1][key]
        return b / a if a else float("nan")

    print(f"\n  sample size grew {sizes[-1] / sizes[0]:.0f}x from {sizes[0]} to {sizes[-1]}")
    for k, label in [("parallel", "parallel analysis"), ("kaiser", "eigenvalue > 1"),
                     ("var90", "90% of variance"), ("cv", "cross-validated"),
                     ("participation", "participation ratio")]:
        print(f"    {label:<22} grew {growth(k):>5.2f}x   "
              f"{out[0][k]:.1f} -> {out[-1][k]:.1f}")

    null_max = max(o["shuffled_parallel"] for o in out)
    cv_growth, pr_growth = growth("cv"), growth("participation")
    if null_max > 5:
        verdict = "NULL-FAIL"
    elif cv_growth < 1.5 and pr_growth < 1.5:
        verdict = "STABLE"
    else:
        verdict = "UNSTABLE"
    print(f"\n  largest count on fully-shuffled activations: {null_max:.1f} "
          f"(should be ~0)")
    print(f"\n  >>> {verdict}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"{tag}.json").write_text(json.dumps(
        {"model": model_name, "n_read": N, "n_layers": n_layers,
         "middle_layers": [mids[0], mids[-1]], "repeats": args.repeats,
         "rows": out, "verdict": verdict,
         "growth": {k: growth(k) for k in
                    ("parallel", "kaiser", "var90", "cv", "participation")}},
        indent=2), encoding="utf-8", newline="\n")
    print(f"\nwrote {(RESULTS / f'{tag}.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
