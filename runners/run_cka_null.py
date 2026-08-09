"""G128 — the permutation null the event alignment (L45) still owes.

The alignment's best-match assignment has no null: with 25 to 37 blocks per family, a lawful-
looking landing pattern may fall out of any smooth similarity matrix. This recomputes the block
matching with TEXT CORRESPONDENCE BROKEN (reference activations of text i paired against target
activations of a permuted text j), 100 permutations per family. If the observed landing depths
are an artifact of matrix smoothness, the null landings cluster the same way; if the alignment is
carried by shared per-text computation, the null scatters.

    REAL        observed early/late landing depths sit outside the null's central 95% band
    SMOOTHNESS  the null reproduces the landings -- L45 is withdrawn as evidence
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "cka_alignment"
FAMILIES = ["Qwen/Qwen2.5-1.5B", "openai-community/gpt2-medium", "EleutherAI/pythia-1.4b",
            "HuggingFaceTB/SmolLM2-360M", "openai-community/gpt2-large", "Qwen/Qwen2.5-0.5B"]
N_PERM = 100


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--n-texts", type=int, default=30)
    args = ap.parse_args()

    import numpy as np                                                # noqa: PLC0415

    from soundingline.probe.activations import Reader                 # noqa: PLC0415

    d = REPO / "corpora" / "ladder2"
    man = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
    texts = []
    for it in man["items"]:
        p = d / f"{it['id']}.txt"
        if p.exists():
            texts.append(" ".join(p.read_text(encoding="utf-8").split()[:200]))
        if len(texts) >= args.n_texts:
            break

    def reps(model_name):
        reader = Reader(model_name, device=args.device)
        R = None
        for t in texts:
            a = reader.read(t)
            if R is None:
                R = [[] for _ in range(len(a.acts))]
            for L in range(len(a.acts)):
                R[L].append(a.acts[L])
        del reader
        import torch                                                  # noqa: PLC0415
        torch.cuda.empty_cache()
        return [np.array(r) for r in R]

    def cka(X, Y):
        X = X - X.mean(0)
        Y = Y - Y.mean(0)
        num = np.linalg.norm(Y.T @ X, "fro") ** 2
        den = np.linalg.norm(X.T @ X, "fro") * np.linalg.norm(Y.T @ Y, "fro")
        return float(num / (den + 1e-12))

    rng = np.random.default_rng(19)
    print(f"reference: {FAMILIES[0]}", flush=True)
    ref = reps(FAMILIES[0])
    n_ref = len(ref)
    loci = {"early": max(2, round(n_ref * 0.07)), "late": round(n_ref * 0.76)}
    out = {"reference": FAMILIES[0], "n_perm": N_PERM, "families": {}}

    for fam in FAMILIES[1:]:
        print(f"null for {fam} ...", flush=True)
        tgt = reps(fam)
        n_tgt = len(tgt)

        def land(perm=None):
            idx = perm if perm is not None else np.arange(len(texts))
            res = {}
            for name, L in loci.items():
                row = [cka(ref[L], tgt[j][idx]) for j in range(n_tgt)]
                res[name] = int(np.argmax(row)) / (n_tgt - 1)
            return res

        obs = land()
        null = {"early": [], "late": []}
        for _ in range(N_PERM):
            r = land(rng.permutation(len(texts)))
            for k in null:
                null[k].append(r[k])
        verdicts = {}
        for k in ("early", "late"):
            lo, hi = np.percentile(null[k], [2.5, 97.5])
            inside = lo <= obs[k] <= hi
            verdicts[k] = "SMOOTHNESS" if inside else "REAL"
            print(f"  {k}: observed {obs[k]:.2f}, null band [{lo:.2f}, {hi:.2f}] -> {verdicts[k]}")
        out["families"][fam] = {"observed": obs,
                                "null_band": {k: [float(np.percentile(null[k], 2.5)),
                                                  float(np.percentile(null[k], 97.5))]
                                              for k in null},
                                "verdicts": verdicts}

    reals = sum(v["verdicts"][k] == "REAL" for v in out["families"].values()
                for k in ("early", "late"))
    out["verdict"] = f"{reals} of {2 * len(out['families'])} loci-cells REAL"
    print(f"  >>> {out['verdict']}")
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "null_g128.json").write_text(json.dumps(out, indent=2),
                                            encoding="utf-8", newline="\n")
    print(f"wrote {(RESULTS / 'null_g128.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
