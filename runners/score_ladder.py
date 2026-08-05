"""Score any ladder — layer ratio, length, and induction — in one pass.

Generalises `run_ladder2_replication.py` and `run_lr_induction.py` so a new ladder can be scored
without new code. Ladder 3 is the first corpus that needs this and it will not be the last.

── WHAT IT REPORTS, AND IN WHICH ORDER ───────────────────────────────────────────────────────

    raw                            the plain relationship between specified intent and the ratio
    length removed                 length has been a SUPPRESSOR here, not a confound
    specification identity removed  whether the drawn specifications explain it
    BOTH removed                   the bar that killed all three text-feature candidates

**For ladder 3 the length column should be uninteresting**, because length is controlled by
construction there rather than by arithmetic. If it is not uninteresting, the rejection sampling
failed and the corpus is no better than ladder 1 — which the control check at the end reports
directly.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

# every ladder's generation parameters, so specifications can be reconstructed from seeds
LADDERS = {
    "ladder":  {"seed": 70000,  "per_rung": 10, "topic_off": 0, "pool": "base"},
    "ladder2": {"seed": 90000,  "per_rung": 20, "topic_off": 5, "pool": "base"},
    "ladder3": {"seed": 110000, "per_rung": 15, "topic_off": 3, "pool": "extended"},
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="ladder3")
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()

    import numpy as np                                                # noqa: PLC0415
    from scipy import stats                                           # noqa: PLC0415
    from scipy.stats import rankdata                                  # noqa: PLC0415
    from sklearn.linear_model import RidgeCV                          # noqa: PLC0415
    from sklearn.model_selection import KFold                         # noqa: PLC0415

    from runners.make_intent_ladder import SPECS as BASE, TOPICS      # noqa: PLC0415
    from soundingline.probe.activations import (DEFAULT_MODEL, Reader,  # noqa: PLC0415
                                                fit_directions)
    from runners.run_b import split                                   # noqa: PLC0415
    from runners.run_layer_ratio import ratio_for                     # noqa: PLC0415

    cfg = LADDERS[args.corpus]
    if cfg["pool"] == "extended":
        from runners.make_ladder3 import SPECS as POOL                # noqa: PLC0415
    else:
        POOL = BASE

    d = REPO / "corpora" / args.corpus
    man = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
    rungs = sorted({it["rung"] for it in man["items"]})

    print(f"loading {DEFAULT_MODEL} ...", flush=True)
    reader = Reader(DEFAULT_MODEL, device=args.device)
    fit, _ = split()
    dirs = fit_directions(reader, fit)
    print(f"scoring {args.corpus}: {len(man['items'])} artifacts, rungs {rungs}\n", flush=True)

    rows = []
    for it in man["items"]:
        p = d / f"{it['id']}.txt"
        if not p.exists():
            continue
        rung, idx = it["rung"], int(it["id"].split("_")[1])
        rng = random.Random(cfg["seed"] + rung * 1000 + idx)
        _ = TOPICS[(idx + cfg["topic_off"]) % len(TOPICS)]
        picks = rng.sample(POOL, rung) if rung else []
        t = p.read_text(encoding="utf-8")
        rows.append({"rung": rung, "specs": set(picks), "words": len(t.split()),
                     "ratio": ratio_for(reader, dirs, t)})

    import statistics                                                 # noqa: PLC0415
    for g in rungs:
        v = [r["ratio"] for r in rows if r["rung"] == g]
        w = [r["words"] for r in rows if r["rung"] == g]
        print(f"  rung {g:>3}: ratio {statistics.fmean(v):.4f}  "
              f"median {statistics.median(w):.0f}w  n={len(v)}")

    X = np.array([[1.0 if s in r["specs"] else 0.0 for s in POOL] for r in rows])
    y = np.array([r["ratio"] for r in rows])
    rung = np.array([r["rung"] for r in rows], dtype=float)
    words = np.array([r["words"] for r in rows], dtype=float)

    def rres(a, b):
        a, b = rankdata(a), rankdata(b)
        return a - np.polyval(np.polyfit(b, a, 1), b)

    raw, p_raw = stats.spearmanr(rung, y)
    len_rho, p_lrho = stats.spearmanr(rung, words)
    len_only, p_len = stats.spearmanr(rres(y, words), rres(rung, words))
    pred = np.zeros_like(y)
    for tr, te in KFold(n_splits=5, shuffle=True, random_state=0).split(X):
        pred[te] = RidgeCV(alphas=np.logspace(-2, 3, 20)).fit(X[tr], y[tr]).predict(X[te])
    resid = y - pred
    spec_only, p_spec = stats.spearmanr(rung, resid)
    both, p_both = stats.spearmanr(rres(resid, words), rres(rung, words))

    print(f"\n{'':<34}{'strength':>10}{'p':>11}")
    print(f"{'raw':<34}{raw:>+10.3f}{p_raw:>11.4f}")
    print(f"{'length removed':<34}{len_only:>+10.3f}{p_len:>11.4f}")
    print(f"{'specification identity removed':<34}{spec_only:>+10.3f}{p_spec:>11.4f}")
    print(f"{'BOTH removed':<34}{both:>+10.3f}{p_both:>11.4f}")

    print(f"\nCONTROL CHECK — rung vs output length: {len_rho:+.3f} (p={p_lrho:.4f})")
    controlled = abs(len_rho) < 0.15
    print(f"  >>> {'LENGTH CONTROLLED BY CONSTRUCTION' if controlled else 'length still varies with rung'}")
    if controlled:
        print("      The raw column is therefore the honest headline for this corpus;")
        print("      no length correction is needed to read it.")

    # acceleration: does the top of the ladder move more than the bottom? (E2)
    means = {g: statistics.fmean(r["ratio"] for r in rows if r["rung"] == g) for g in rungs}
    lo_gap = means[rungs[0]] - means[rungs[len(rungs) // 2]]
    hi_gap = means[rungs[len(rungs) // 2]] - means[rungs[-1]]
    print(f"\nACCELERATION (E2) — lower half {lo_gap:+.4f}, upper half {hi_gap:+.4f}   "
          f">>> {'ACCELERATES' if abs(hi_gap) > abs(lo_gap) else 'no acceleration'}")

    out = REPO / "results" / args.corpus
    out.mkdir(parents=True, exist_ok=True)
    (out / "score.json").write_text(json.dumps(
        {"corpus": args.corpus, "n": len(rows), "raw": float(raw), "p_raw": float(p_raw),
         "length_removed": float(len_only), "specs_removed": float(spec_only),
         "both_removed": float(both), "p_both": float(p_both),
         "rung_vs_length": float(len_rho), "length_controlled": bool(controlled),
         "by_rung": {str(g): means[g] for g in rungs},
         "acceleration": {"lower_half": lo_gap, "upper_half": hi_gap,
                          "accelerates": bool(abs(hi_gap) > abs(lo_gap))}},
        indent=2), encoding="utf-8", newline="\n")
    print(f"\nwrote {(out / 'score.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
