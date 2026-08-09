"""G46 — do weaker models place their affective structure more poorly? CPU, from saved results.

The live worry (§8) asks whether models have a human-shaped structure to amplify at all, and his
second test of it: *"Is there evidence of worse models having more poorly placed emotional
concepts?"* If placement improves with capability, placement is **learned**, and the amplification
story needs a scale story. If it does not, the structure is architectural — the strongest thing §8
could return.

── THE TEST ──────────────────────────────────────────────────────────────────────────────────

Placement quality per family, from the saved subspace alignment matrices (11 families):

    break_strength   how much a layer-2 two-band split beats the mean off-split — the sharpness
                     of the one boundary G42 found
    decay_r2         how lawfully alignment decays with layer distance (R² of log-alignment on
                     distance) — a structure well-placed rotates smoothly

Each correlated with parameter count across families (Spearman).

    PLACEMENT-SCALES   |rho| >= 0.6 at p < 0.05 on either metric
    ARCHITECTURAL      neither metric tracks size — placement is not a capability
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "placement_scale"

PARAMS = {"Qwen2.5-0.5B": 0.5, "Qwen2.5-1.5B": 1.5, "Qwen2.5-3B": 3.0,
          "SmolLM2-360M": 0.36, "SmolLM2-1.7B": 1.7,
          "gpt2-medium": 0.355, "gpt2-large": 0.774, "gpt2-xl": 1.558,
          "pythia-410m": 0.41, "pythia-1.4b": 1.4, "pythia-2.8b": 2.8}


def main() -> None:
    import numpy as np                                                # noqa: PLC0415
    from scipy import stats                                           # noqa: PLC0415

    rows = []
    print(f"{'family':<16}{'params(B)':>10}{'break@2':>9}{'decay R2':>10}")
    for f in sorted((REPO / "results" / "subspace").glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        tag = f.stem
        if tag not in PARAMS:
            m = re.sub(r"\.json$", "", tag)
            if m not in PARAMS:
                continue
            tag = m
        A = np.array(d["matrix"])
        n = A.shape[0]
        # break strength at layer 2: mean within-band minus mean cross-band alignment
        def split_score(k):
            w, x = [], []
            for i in range(n):
                for j in range(i + 1, n):
                    (w if (i < k) == (j < k) else x).append(A[i, j])
            return float(np.mean(w) - np.mean(x))
        s2 = split_score(2)
        base = float(np.mean([split_score(k) for k in range(3, n - 2)]))
        brk = s2 - base
        # decay lawfulness: R^2 of log-alignment on distance
        di, dv = [], []
        for i in range(n):
            for j in range(i + 1, n):
                if A[i, j] > 1e-6:
                    di.append(j - i)
                    dv.append(np.log(A[i, j]))
        r = stats.pearsonr(di, dv).statistic
        rows.append({"family": tag, "params_b": PARAMS[tag],
                     "break_strength": brk, "decay_r2": float(r * r)})
        print(f"{tag:<16}{PARAMS[tag]:>10.2f}{brk:>9.3f}{r * r:>10.3f}")

    p_arr = [r["params_b"] for r in rows]
    verdicts = {}
    print()
    for metric in ("break_strength", "decay_r2"):
        v = [r[metric] for r in rows]
        rho, p = stats.spearmanr(p_arr, v)
        verdicts[metric] = {"rho": float(rho), "p": float(p)}
        print(f"  {metric:<16} vs params: rho {rho:+.3f}  p={p:.4f}")
    scales = any(abs(v["rho"]) >= 0.6 and v["p"] < 0.05 for v in verdicts.values())
    verdict = "PLACEMENT-SCALES" if scales else "ARCHITECTURAL"
    print(f"\n  >>> {verdict}  (n = {len(rows)} families — small; the rho is the result, "
          f"the label is a summary)")

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "summary.json").write_text(json.dumps(
        {"rows": rows, "correlations": verdicts, "verdict": verdict}, indent=2),
        encoding="utf-8", newline="\n")
    print(f"wrote {(RESULTS / 'summary.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
