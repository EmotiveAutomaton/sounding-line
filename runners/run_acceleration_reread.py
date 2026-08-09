"""PD-19 close-out — the acceleration re-read the row itself asked for, over L23's saved rows.

L17 found no acceleration at the top of the extreme ladder (+0.10 lower half, −0.01 upper), but it
read the raw ratio before the fair control existed. The per-artifact rows run_induction_v2 saved
make the re-read CPU-only: length-partialled ratio against rung, lower rungs {0,2,10} versus upper
{10,30,60}, on all three ladders.

    ACCELERATES      upper-half |rho| clearly exceeds lower-half |rho| on the extreme ladder
    STRAIGHT         it does not — PD-19 stays NOT SUPPORTED, now on the modern rows
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "acceleration"


def main() -> None:
    import numpy as np                                                # noqa: PLC0415
    from scipy import stats                                           # noqa: PLC0415
    from scipy.stats import rankdata                                  # noqa: PLC0415

    def rres(a, b):
        a, b = rankdata(a), rankdata(b)
        return a - np.polyval(np.polyfit(b, a, 1), b)

    out = {}
    print(f"{'corpus':<10}{'lower rho':>11}{'p':>8}{'upper rho':>11}{'p':>8}")
    for corpus in ("ladder", "ladder2", "ladder3"):
        p = REPO / "results" / "induction_v2" / f"{corpus}.json"
        if not p.exists():
            continue
        rows = json.loads(p.read_text(encoding="utf-8"))["rows"]
        rungs = sorted({r["rung"] for r in rows})
        mid = rungs[len(rungs) // 2]

        def half(sel):
            sub = [r for r in rows if r["rung"] in sel]
            rung = np.array([r["rung"] for r in sub], float)
            wds = np.array([r["words"] for r in sub], float)
            val = np.array([r["ratio"] for r in sub], float)
            rho, pv = stats.spearmanr(rres(val, wds), rres(rung, wds))
            return float(rho), float(pv), len(sub)

        lo = half([g for g in rungs if g <= mid])
        hi = half([g for g in rungs if g >= mid])
        out[corpus] = {"lower": lo, "upper": hi, "pivot_rung": mid}
        print(f"{corpus:<10}{lo[0]:>+11.3f}{lo[1]:>8.3f}{hi[0]:>+11.3f}{hi[1]:>8.3f}")

    l3 = out.get("ladder3")
    verdict = ("ACCELERATES" if l3 and abs(l3["upper"][0]) > abs(l3["lower"][0]) + 0.15
               and l3["upper"][1] < 0.05 else "STRAIGHT")
    print(f"\n  >>> {verdict}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "summary.json").write_text(json.dumps(
        {"per_corpus": out, "verdict": verdict}, indent=2), encoding="utf-8", newline="\n")
    print(f"wrote {(RESULTS / 'summary.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
