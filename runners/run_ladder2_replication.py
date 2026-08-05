"""Ladder 2 — the held-out replication of the layer ratio. ONE test, hyperparameters frozen.

── THE PRE-REGISTRATION, FROM `runners/make_ladder2.py`, WRITTEN BEFORE GENERATION ───────────

    REPLICATES   rho < -0.2 with p < 0.01 on ladder 2 ALONE
    FAILS        rho >= -0.1, or p > 0.05
    AMBIGUOUS    between -- and at n = 100 that would mean the effect is too small to chase

**Nothing about the measure may be re-tuned here.** The loci stay at round(n*0.07) and round(n*0.76)
exactly as `ratio_for()` has them. That is the entire point: known weakness 3 is that those split
points were chosen by looking at a prior result on the same model, so more data alone would only
give a tighter estimate of a quantity chosen on the data. A held-out set with frozen hyperparameters
is the only version of "raise the power" that is worth anything.

The pooled n = 150 number is printed for completeness and **is not the test.**

── THE COMPLICATION LADDER 2 ALREADY HANDED US ───────────────────────────────────────────────

Generation reported its own void check:

    rung vs output length:  rho = +0.401   (ladder 1 was +0.403)

**The length confound reproduced almost exactly.** So the ladder is, by construction, mildly a length
ladder in both halves, and any measure correlated with length will appear to rank the rungs. That was
already enough to void ladder 1 on the pre-registered 0.400 threshold.

Therefore the primary statistic here is the **partial correlation of rung against ratio, controlling
word count** (rank-residualised), reported alongside the raw. If the raw replicates and the partial
does not, the effect is length and the replication has killed it rather than confirmed it.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "ladder2"


def load(name: str) -> list[dict]:
    d = REPO / "corpora" / name
    man = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
    out = []
    for it in man["items"]:
        p = d / f"{it['id']}.txt"
        if p.exists():
            t = p.read_text(encoding="utf-8")
            out.append({"id": it["id"], "rung": it["rung"], "text": t,
                        "words": len(t.split())})
    return out


def partial_spearman(y: list[float], x: list[float], z: list[float]):
    """Spearman of y vs x controlling z, via rank residuals."""
    import numpy as np                                                # noqa: PLC0415
    from scipy import stats                                           # noqa: PLC0415
    from scipy.stats import rankdata                                  # noqa: PLC0415

    def resid(a, b):
        a, b = rankdata(a), rankdata(b)
        return a - np.polyval(np.polyfit(b, a, 1), b)

    return stats.spearmanr(resid(y, z), resid(x, z))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--model", default=None)
    args = ap.parse_args()

    from scipy import stats                                           # noqa: PLC0415
    from soundingline.probe.activations import (DEFAULT_MODEL, Reader,  # noqa: PLC0415
                                                fit_directions)
    from runners.run_b import split                                   # noqa: PLC0415
    from runners.run_layer_ratio import ratio_for                     # noqa: PLC0415

    name = args.model or DEFAULT_MODEL
    print(f"loading {name} on {args.device} ...", flush=True)
    reader = Reader(name, device=args.device)
    fit, _ = split()
    print("fitting affect directions (identical procedure to ladder 1) ...", flush=True)
    dirs = fit_directions(reader, fit)
    print(f"  {len(dirs.concepts)} concepts x {dirs.n_layers} layers", flush=True)
    print("  loci FROZEN at 0.07 and 0.76 of depth — not refitted\n", flush=True)

    rows = load("ladder2")
    print(f"ladder2: {len(rows)} artifacts", flush=True)
    for r in rows:
        r["ratio"] = ratio_for(reader, dirs, r["text"])

    rungs = sorted({r["rung"] for r in rows})
    for g in rungs:
        v = [r["ratio"] for r in rows if r["rung"] == g]
        print(f"  rung {g:>2}: {statistics.fmean(v):.4f}  n={len(v)}")

    rho, p = stats.spearmanr([r["rung"] for r in rows], [r["ratio"] for r in rows])
    rho_len, p_len = stats.spearmanr([r["words"] for r in rows], [r["ratio"] for r in rows])
    prho, pp = partial_spearman([r["ratio"] for r in rows], [r["rung"] for r in rows],
                                [r["words"] for r in rows])

    print(f"\n  HELD-OUT  rung vs ratio        rho={rho:+.3f}  p={p:.4f}")
    print(f"            ratio vs word count   rho={rho_len:+.3f}  p={p_len:.4f}")
    print(f"            PARTIAL, length ctrl  rho={prho:+.3f}  p={pp:.4f}   <- primary")

    verdict = ("REPLICATES" if rho < -0.2 and p < 0.01 else
               "FAILS" if rho >= -0.1 or p > 0.05 else "AMBIGUOUS")
    partial_ok = prho < -0.2 and pp < 0.01
    final = verdict if partial_ok or verdict == "FAILS" else f"{verdict}_BUT_LENGTH"

    print(f"\n  >>> {verdict}" + ("" if partial_ok else "  — and the partial does NOT hold"))
    if verdict != "FAILS" and not partial_ok:
        print("      The raw effect survives length control poorly. Ladder 2 reproduced the")
        print("      length void at rho=+0.401, so this is the outcome that was most at risk.")

    # pooled, reported and explicitly NOT the test
    l1 = load("ladder")
    for r in l1:
        r["ratio"] = ratio_for(reader, dirs, r["text"])
    allr = l1 + rows
    prho_all, pp_all = stats.spearmanr([r["rung"] for r in allr], [r["ratio"] for r in allr])
    print(f"\n  pooled n={len(allr)} (NOT the test): rho={prho_all:+.3f} p={pp_all:.4f}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "replication.json").write_text(json.dumps(
        {"n": len(rows), "rho": rho, "p": p, "rho_vs_length": rho_len,
         "partial_rho": prho, "partial_p": pp, "verdict": verdict, "final": final,
         "pooled_rho": prho_all, "pooled_p": pp_all, "pooled_n": len(allr),
         "by_rung": {str(g): statistics.fmean(r["ratio"] for r in rows if r["rung"] == g)
                     for g in rungs}}, indent=2, default=float), encoding="utf-8", newline="\n")
    print(f"\nwrote {(RESULTS / 'replication.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
