"""The induction check, applied to the layer ratio — because the hole affects it too.

`runners/run_induction_check.py` closed a hole in the echo control: a specification can produce a
feature without containing it. That check killed two of three candidate measures outright and
reduced the third below significance.

**The same hole threatens the layer ratio**, which is this project's only replicated effect. It is
measured from a reading model rather than from text, but that does not protect it: if more-specified
prompts induce a different *kind* of writing, the reader responds to the writing.

Standing rule, from the curator: **a hole found in the battery means re-running what it touches,
without being asked.** This is that.

    INDUCTION   the rung effect collapses once the identity of the drawn specifications is
                accounted for
    SURVIVES    it holds -- the effect is about HOW MUCH intent was specified, not which words
                were used to specify it

Reported at three levels of stringency, because the honest answer depends on how much is removed:
raw, after specification identity, and after specification identity **and** length together. The
third is the bar the feature candidates failed.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "induction"


def main() -> None:
    import numpy as np                                               # noqa: PLC0415
    from scipy import stats                                          # noqa: PLC0415
    from scipy.stats import rankdata                                 # noqa: PLC0415
    from sklearn.linear_model import RidgeCV                         # noqa: PLC0415
    from sklearn.model_selection import KFold                        # noqa: PLC0415

    from runners.make_intent_ladder import RUNGS, SPECS, TOPICS, build  # noqa: PLC0415
    from soundingline.probe.activations import (DEFAULT_MODEL, Reader,  # noqa: PLC0415
                                                fit_directions)
    from runners.run_b import split                                  # noqa: PLC0415
    from runners.run_layer_ratio import ratio_for                    # noqa: PLC0415

    d = REPO / "corpora" / "ladder2"
    print(f"loading {DEFAULT_MODEL} ...", flush=True)
    reader = Reader(DEFAULT_MODEL, device="cuda")
    fit, _ = split()
    dirs = fit_directions(reader, fit)
    print("  loci frozen, directions fitted identically to the replication\n", flush=True)

    rows = []
    for r in RUNGS:
        for i in range(20):
            name = f"r{r}_{i:02d}"
            p = d / f"{name}.txt"
            if not p.exists():
                continue
            rng = random.Random(90000 + r * 1000 + i)
            _ = TOPICS[(i + 5) % len(TOPICS)]
            picks = rng.sample(SPECS, r) if r else []
            t = p.read_text(encoding="utf-8")
            rows.append({"id": name, "rung": r, "specs": set(picks),
                         "words": len(t.split()), "ratio": ratio_for(reader, dirs, t)})
        print(f"  rung {r:>2} done", flush=True)

    X = np.array([[1.0 if s in row["specs"] else 0.0 for s in SPECS] for row in rows])
    y = np.array([row["ratio"] for row in rows])
    rung = np.array([row["rung"] for row in rows], dtype=float)
    words = np.array([row["words"] for row in rows], dtype=float)

    raw, p_raw = stats.spearmanr(rung, y)

    pred = np.zeros_like(y)
    for tr, te in KFold(n_splits=5, shuffle=True, random_state=0).split(X):
        pred[te] = RidgeCV(alphas=np.logspace(-2, 3, 20)).fit(X[tr], y[tr]).predict(X[te])
    explained, _ = stats.spearmanr(pred, y)
    resid = y - pred
    after, p_after = stats.spearmanr(rung, resid)

    def rres(a, b):
        a, b = rankdata(a), rankdata(b)
        return a - np.polyval(np.polyfit(b, a, 1), b)

    both, p_both = stats.spearmanr(rres(resid, words), rres(rung, words))
    len_only, p_len = stats.spearmanr(rres(y, words), rres(rung, words))

    print(f"\n{'':<34}{'strength':>10}{'p':>11}")
    print(f"{'raw':<34}{raw:>+10.3f}{p_raw:>11.4f}")
    print(f"{'length removed':<34}{len_only:>+10.3f}{p_len:>11.4f}")
    print(f"{'specification identity removed':<34}{after:>+10.3f}{p_after:>11.4f}")
    print(f"{'BOTH removed':<34}{both:>+10.3f}{p_both:>11.4f}   <- the bar the features failed")
    print(f"\nspecification identity alone explains: {explained:+.3f} of the ratio")

    verdict = ("SURVIVES" if abs(both) > 0.2 and p_both < 0.05 else "INDUCTION")
    print(f"\n>>> {verdict}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "layer_ratio_induction.json").write_text(json.dumps(
        {"raw": float(raw), "p_raw": float(p_raw),
         "length_removed": float(len_only), "p_length": float(p_len),
         "specs_removed": float(after), "p_specs": float(p_after),
         "both_removed": float(both), "p_both": float(p_both),
         "specs_explain": float(explained), "verdict": verdict},
        indent=2), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
