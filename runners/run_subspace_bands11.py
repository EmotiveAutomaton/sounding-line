"""G42b + G44a — the two-band split on all eleven families, and a first bite at the rotation
transform.

G42's two-band-at-layer-2 claim was tested in four families; the audit surfaced seven more runs
that were never given the same test (owed in the G42 row). And G44 asks whether the depth transform
is *recoverable* — the alignment matrix "already contains the data to fit it." The cheapest
recoverability check is **composability**: if one lawful transform carries the subspace through
depth, then alignment(i,k) should be predictable from alignment(i,j) and alignment(j,k).

── PRE-REGISTERED ────────────────────────────────────────────────────────────────────────────

    G42b   per family: does the best two-way split sit at layer 2 (±1)? Count across 11
    G44a   per family: R² of align(i,k) predicted by align(i,j)·align(j,k) over all i<j<k.
           COMPOSABLE if median R² >= 0.5 across families — the transform is lawful enough
           to fit; NOT-COMPOSABLE otherwise, and G44 needs the bases, not the matrix
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "subspace_bands11"


def main() -> None:
    import numpy as np                                                # noqa: PLC0415

    rows = []
    print(f"{'family':<16}{'best split':>11}{'at 2±1?':>9}{'compose R2':>12}")
    for f in sorted((REPO / "results" / "subspace").glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        A = np.array(d["matrix"])
        n = A.shape[0]

        def split_score(k):
            w, x = [], []
            for i in range(n):
                for j in range(i + 1, n):
                    (w if (i < k) == (j < k) else x).append(A[i, j])
            return float(np.mean(w) - np.mean(x))

        scores = {k: split_score(k) for k in range(1, n - 1)}
        best = max(scores, key=scores.get)

        pred, obs = [], []
        for i in range(n):
            for j in range(i + 1, n):
                for k in range(j + 1, n):
                    pred.append(A[i, j] * A[j, k])
                    obs.append(A[i, k])
        pred, obs = np.array(pred), np.array(obs)
        ss_res = float(((obs - pred) ** 2).sum())
        ss_tot = float(((obs - obs.mean()) ** 2).sum())
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
        rows.append({"family": f.stem, "n_layers": n, "best_split": int(best),
                     "at_layer2": bool(abs(best - 2) <= 1), "compose_r2": r2})
        print(f"{f.stem:<16}{best:>11}{'yes' if abs(best - 2) <= 1 else 'NO':>9}{r2:>12.3f}")

    at2 = sum(r["at_layer2"] for r in rows)
    med = float(np.median([r["compose_r2"] for r in rows]))
    v42 = f"LAYER-2 BREAK IN {at2}/{len(rows)}"
    v44 = "COMPOSABLE" if med >= 0.5 else "NOT-COMPOSABLE"
    print(f"\n  G42b: {v42}   G44a: median compose R² {med:.3f} → {v44}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "summary.json").write_text(json.dumps(
        {"rows": rows, "layer2_count": at2, "median_compose_r2": med,
         "verdict_g42b": v42, "verdict_g44a": v44}, indent=2),
        encoding="utf-8", newline="\n")
    print(f"wrote {(RESULTS / 'summary.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
