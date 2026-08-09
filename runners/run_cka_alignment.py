"""G124 / G112 — align families by computational events, not percentage depth.

Fixed depth fractions (7%/76%) have failed to transfer everywhere: signs flip, big members fade.
CKA (Kornblith et al.) compares representations across separately trained networks. This computes
per-block representations on thirty shared texts for every family, CKA-aligns each family's blocks
to the flagship's, and reports where the flagship's two loci actually land per family.

    Descriptive first pass — the deliverable is the aligned-loci table and whether the mirror
    families' loci land in regions with opposite-signed intent correlation (the G112 lead).
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
        n = None
        R = None
        for i, t in enumerate(texts):
            a = reader.read(t)
            if R is None:
                n = len(a.acts)
                R = [[] for _ in range(n)]
            for L in range(n):
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

    print(f"reference: {FAMILIES[0]}", flush=True)
    ref = reps(FAMILIES[0])
    n_ref = len(ref)
    loci = {"early": max(2, round(n_ref * 0.07)), "late": round(n_ref * 0.76)}
    out = {"reference": FAMILIES[0], "n_texts": len(texts), "loci_ref": loci, "families": {}}

    for fam in FAMILIES[1:]:
        print(f"aligning {fam} ...", flush=True)
        tgt = reps(fam)
        M = np.array([[cka(ref[i], tgt[j]) for j in range(len(tgt))] for i in range(n_ref)])
        aligned = {name: int(np.argmax(M[L])) for name, L in loci.items()}
        frac = {name: aligned[name] / (len(tgt) - 1) for name in loci}
        out["families"][fam] = {"n_blocks": len(tgt), "aligned_loci": aligned,
                                "aligned_fractions": frac,
                                "row_max": [int(np.argmax(M[L])) for L in range(n_ref)]}
        print(f"  early locus (ref block {loci['early']}) -> block {aligned['early']} "
              f"({frac['early']:.0%} depth); late (ref {loci['late']}) -> {aligned['late']} "
              f"({frac['late']:.0%})")

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "summary.json").write_text(json.dumps(out, indent=2),
                                          encoding="utf-8", newline="\n")
    print(f"wrote {(RESULTS / 'summary.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
