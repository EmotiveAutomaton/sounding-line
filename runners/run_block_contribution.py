"""G126 — the three per-block quantities the analogue research says we should have been measuring.

From `docs/method/NEURAL_ANALOGUES.md`: raw magnitude is disqualified (depth growth, massive
activations); the defensible per-block readings are —

    write norm      ||z_{l+1} - z_l|| in standardized space — the analogue of what BOLD indexes
    affect work     (z_{l+1} - z_l) . u_c — signed push along each concept; telescopes exactly
    d-prime         between-class mean projection gap over within-class SD, held-out — decoding SNR
    rogue share     top-3 dimensions' share of projection magnitude — the artifact-QC alarm

Profiles per corpus (ladder2 + nomaker), plus d' per block from held-out fitting sentences.
Descriptive first pass: the pre-registered check is only that the QC alarm stays low (< 0.5) —
if it spikes, every profile in the file is contaminated regardless of shape.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "block_contribution"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--per-corpus", type=int, default=40)
    args = ap.parse_args()

    import numpy as np                                                # noqa: PLC0415

    from runners.run_b import split                                   # noqa: PLC0415
    from runners.run_layer_ratio import windows                       # noqa: PLC0415
    from soundingline.probe.activations import (DEFAULT_MODEL, Reader,  # noqa: PLC0415
                                                fit_directions)

    model_name = args.model or DEFAULT_MODEL
    print(f"loading {model_name} ...", flush=True)
    reader = Reader(model_name, device=args.device)
    fit, held = split()
    dirs = fit_directions(reader, fit)
    n = dirs.n_layers
    concepts = list(dirs.concepts)
    mu = [np.asarray(m, float) for m in dirs.mu]
    sd = [np.asarray(s, float) + 1e-9 for s in dirs.sd]
    V = {c: [np.asarray(dirs.vecs[c][L], float) for L in range(n)] for c in concepts}
    for c in concepts:
        for L in range(n):
            V[c][L] = V[c][L] / (np.linalg.norm(V[c][L]) + 1e-9)

    def zstack(text: str) -> list:
        a = reader.read(text)
        return [(np.asarray(a.acts[L]) - mu[L]) / sd[L] for L in range(n)]

    # ── d' per block from held-out fitting sentences ──
    held_z: dict[str, list] = {}
    for c, sents in held.items():
        held_z[c] = [zstack(s) for s in sents]
    dprime = []
    for L in range(1, n):
        per_class = {c: [float(z[L] @ V[c][L]) for z in zs] for c, zs in held_z.items()}
        own = [v for c in per_class for v in per_class[c]]
        between = np.std([np.mean(per_class[c]) for c in per_class])
        within = np.mean([np.std(per_class[c]) for c in per_class]) + 1e-9
        dprime.append(float(between / within))
        _ = own

    out = {"model": model_name, "dprime_by_block": dprime, "corpora": {}}
    print("d' by block:", " ".join(f"{d:.2f}" for d in dprime))

    for corpus in ("ladder2", "nomaker"):
        d = REPO / "corpora" / corpus
        man = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
        wn = np.zeros(n - 1)
        work = np.zeros(n - 1)
        rogue = np.zeros(n - 1)
        m = 0
        for it in man["items"][: args.per_corpus]:
            p = d / f"{it['id']}.txt"
            if not p.exists():
                continue
            for w in windows(p.read_text(encoding="utf-8"))[:4]:
                zs = zstack(w)
                for L in range(n - 1):
                    delta = zs[L + 1] - zs[L]
                    wn[L] += float(np.linalg.norm(delta))
                    work[L] += float(np.mean([abs(delta @ V[c][L + 1]) for c in concepts]))
                    proj = np.abs(delta)
                    top3 = float(np.sort(proj)[-3:].sum() / (proj.sum() + 1e-9))
                    rogue[L] += top3
                m += 1
        wn, work, rogue = wn / max(m, 1), work / max(m, 1), rogue / max(m, 1)
        out["corpora"][corpus] = {"n_windows": m, "write_norm": wn.tolist(),
                                  "affect_work": work.tolist(), "rogue_share": rogue.tolist()}
        print(f"{corpus}: windows {m}  peak write at block {int(np.argmax(wn))}  "
              f"peak work at {int(np.argmax(work))}  max rogue share {rogue.max():.2f}")

    max_rogue = max(max(c["rogue_share"]) for c in out["corpora"].values())
    out["qc"] = "CLEAN" if max_rogue < 0.5 else "CONTAMINATED"
    print(f"\n  >>> QC {out['qc']} (max rogue share {max_rogue:.2f})")

    RESULTS.mkdir(parents=True, exist_ok=True)
    tag = model_name.split("/")[-1]
    (RESULTS / f"{tag}.json").write_text(json.dumps(out, indent=2),
                                         encoding="utf-8", newline="\n")
    print(f"wrote {(RESULTS / f'{tag}.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
