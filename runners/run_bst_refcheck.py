"""G137 — reference-data gate: do the digitized figure columns reproduce every printed
correlation under our own correlation machinery?

This validates two things at once: the digitized reference data (against the paper's printed
values) and our pooling convention (plain Pearson over all conditions and judgment points
pooled, which is what Baker's own correlation code does). Passing here licenses the reference
human means as the fitting target for the model-side figure arm.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
REF = REPO / "results" / "bst2009_reference"
OUT = REPO / "results" / "bst_gridworld" / "refcheck.json"

PRINTED = {
    "exp1": {"M1_b0.5": 0.83, "M2_b2.0_g0.25": 0.98, "M3_b2.5_k0.5": 0.94,
             "H_b2.5": 0.97},
    "exp2": {"M1_b0.5": 0.58, "M2_b0.5_g0.65": 0.95, "M3_b1.0_k0.95": 0.59,
             "H_b2.5": 0.92},
}


def load(name: str) -> list[dict]:
    with (REF / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main() -> None:
    out: dict = {"experiments": {}, "verdict": "PASS"}
    for exp, fname, hcol in (("exp1", "SL_BST2009_exp1_from_fig5.csv", "human_mean"),
                             ("exp2", "SL_BST2009_exp2_from_fig8.csv", "human_mean")):
        rows = load(fname)
        h = np.array([float(r[hcol]) for r in rows])
        res = {}
        for col, printed in PRINTED[exp].items():
            m = np.array([float(r[col]) for r in rows])
            r_val = float(np.corrcoef(h, m)[0, 1])
            ok = abs(round(r_val, 2) - printed) <= 0.011
            res[col] = {"r": round(r_val, 4), "printed": printed, "match": ok}
            if not ok:
                out["verdict"] = "FAIL"
            print(f"{exp} {col}: r {r_val:.4f} vs printed {printed} "
                  f"-> {'ok' if ok else 'MISMATCH'}")
        out["experiments"][exp] = res

    exp3 = load("SL_BST2009_exp3_from_fig10.csv")
    h3 = [float(r["human_P_path2"]) for r in exp3 if r["human_P_path2"]]
    out["experiments"]["exp3"] = {"n_human": len(h3),
                                  "note": "human side complete; model column partial in "
                                          "source figure, model-side r owed to the arm"}
    print(f"exp3: {len(h3)} human values carried; model comparison owed to the figure arm")
    print(f">>> {out['verdict']}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
