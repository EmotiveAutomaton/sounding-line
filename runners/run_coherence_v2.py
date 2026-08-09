"""G105 — a coherence statistic that can measure agreement, with its known-answer gate built in.

The old statistic was geometrically incapable: centred directions sum to zero, so eight-way
agreement was impossible and the number was an arbitrary-axis projection (audit L26). This one
uses **uncentred per-concept contrasts** — the standardized mean of each concept's fitting
sentences, no global subtraction — and **mean pairwise sign agreement** of the projections.

── KNOWN-ANSWER GATE (runs first, refuses to continue if failed) ─────────────────────────────

Synthetic vectors where all concepts agree must score ~1.0; independent random signs must score
~0.5. A statistic that cannot pass this on data whose answer is known measures nothing.

── THE RE-ADJUDICATION (G33) ─────────────────────────────────────────────────────────────────

Per band (early/middle/late thirds), coherence-v2 against rung:

    RISES-WHEN-CLEAR   late-band agreement rises with rung (p < 0.05) — the original prediction
    FALLS / FLAT       recorded as found; three ladders per family
"""

from __future__ import annotations

import argparse
import itertools
import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "coherence_v2"


def pairwise_sign_agreement(vals: list[float]) -> float:
    pairs = list(itertools.combinations(vals, 2))
    return sum(1.0 for a, b in pairs if a * b > 0) / len(pairs)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()

    import numpy as np                                                # noqa: PLC0415
    from scipy import stats                                           # noqa: PLC0415

    # ── known-answer gate on the statistic itself, before any model loads ──
    rng = np.random.default_rng(0)
    agree = [pairwise_sign_agreement(list(s * np.abs(rng.standard_normal(8))))
             for s in rng.choice([-1.0, 1.0], 200)]
    rand = [pairwise_sign_agreement(list(rng.choice([-1.0, 1.0], 8) * np.abs(rng.standard_normal(8))))
            for _ in range(200)]
    ka_agree, ka_rand = float(np.mean(agree)), float(np.mean(rand))
    print(f"known-answer gate: all-agree {ka_agree:.3f} (want ~1.0), random {ka_rand:.3f} (want ~0.5)")
    assert ka_agree > 0.99 and 0.4 < ka_rand < 0.6, "statistic fails its own known answers"

    from runners.run_b import split                                   # noqa: PLC0415
    from runners.run_layer_ratio import windows                       # noqa: PLC0415
    from soundingline.probe.activations import (DEFAULT_MODEL, Reader,  # noqa: PLC0415
                                                fit_directions)

    model_name = args.model or DEFAULT_MODEL
    print(f"loading {model_name} ...", flush=True)
    reader = Reader(model_name, device=args.device)
    fit, _ = split()
    dirs = fit_directions(reader, fit)          # for the z-parameters and layer count
    n = dirs.n_layers
    concepts = list(dirs.concepts)

    # uncentred contrasts: standardized mean per concept, no global subtraction — these need NOT
    # sum to zero, so same-sign agreement is possible and meaningful
    mu = [np.asarray(m, dtype=float) for m in dirs.mu]
    sd = [np.asarray(s, dtype=float) + 1e-9 for s in dirs.sd]
    U: dict[str, list[np.ndarray]] = {c: [np.zeros_like(mu[L]) for L in range(n)] for c in concepts}
    counts = {c: 0 for c in concepts}
    for c, sents in fit.items():
        for s in sents:
            a = reader.read(s)
            for L in range(n):
                U[c][L] += (np.asarray(a.acts[L]) - mu[L]) / sd[L]
        counts[c] = len(sents)
    for c in concepts:
        for L in range(n):
            U[c][L] /= max(counts[c], 1)
            U[c][L] /= (np.linalg.norm(U[c][L]) + 1e-9)

    thirds = {"early": range(0, n // 3), "middle": range(n // 3, 2 * n // 3),
              "late": range(2 * n // 3, n)}
    out = {"model": model_name, "known_answer": {"agree": ka_agree, "random": ka_rand},
           "corpora": {}}
    for corpus in ("ladder", "ladder2", "ladder3"):
        d = REPO / "corpora" / corpus
        man = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
        rows = []
        for it in man["items"]:
            p = d / f"{it['id']}.txt"
            if not p.exists() or not isinstance(it.get("rung"), int):
                continue
            per_layer = np.zeros(n)
            nw = 0
            for w in windows(p.read_text(encoding="utf-8")):
                a = reader.read(w)
                for L in range(n):
                    z = (np.asarray(a.acts[L]) - mu[L]) / sd[L]
                    per_layer[L] += pairwise_sign_agreement([float(z @ U[c][L]) for c in concepts])
                nw += 1
            if nw:
                rows.append({"rung": it["rung"], "coh": (per_layer / nw).tolist()})
        rung = np.array([r["rung"] for r in rows], float)
        band = {}
        print(f"\n{corpus} (n={len(rows)}):")
        for name, idx in thirds.items():
            v = np.array([statistics.fmean(r["coh"][L] for L in idx) for r in rows])
            rho, p = stats.spearmanr(rung, v)
            band[name] = {"rho": float(rho), "p": float(p), "mean": float(v.mean())}
            print(f"  {name:>7}: agreement {v.mean():.3f}  vs rung {rho:+.3f}  p={p:.4f}")
        late = band["late"]
        band["verdict"] = ("RISES-WHEN-CLEAR" if late["rho"] > 0 and late["p"] < 0.05 else
                           "FALLS" if late["rho"] < 0 and late["p"] < 0.05 else "FLAT")
        print(f"  >>> late band: {band['verdict']}")
        out["corpora"][corpus] = band

    RESULTS.mkdir(parents=True, exist_ok=True)
    tag = model_name.split("/")[-1]
    (RESULTS / f"{tag}.json").write_text(json.dumps(out, indent=2),
                                         encoding="utf-8", newline="\n")
    print(f"\nwrote {(RESULTS / f'{tag}.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
