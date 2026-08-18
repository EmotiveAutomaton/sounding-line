"""2.0E's leakage reference — how much provenance do bare surface features read on the pilot?

The evaluation contract requires a plain surface-feature reference model whose job is to
REVEAL leakage: if cheap statics separate human from machine on the benchmark, every fancier
detector's score is suspect until it beats this floor for reasons the slices can show. First
read on the free-path pilot: G153's 240 process-recorded machine artifacts against the
ArgRewrite Draft1 human essays, with lineage grouping (an r3 rewrite and its human source
share a lineage_id and never straddle train/test).

    FEATURES    the nine statics + 40-dim function-word profile per document (pan25 builders)
    MODEL       gradient-boosted trees, GroupKFold by lineage, 5 folds
    REPORT      overall accuracy/AUC; per-regime slices (thin-prompt vs rewrite; per family);
                the confusion direction that matters is human-called-machine

CPU, minutes. Output: results/g153_pilot/surface_ref.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "runners"))

RESULTS = REPO / "results" / "g153_pilot"
PILOT = REPO / "corpora" / "g153_pilot"
ESSAYS = REPO / "corpora" / "public" / "argrewrite" / "essays" / "Draft1"


def main() -> None:
    import numpy as np                                                # noqa: PLC0415
    from sklearn.ensemble import HistGradientBoostingClassifier       # noqa: PLC0415
    from sklearn.metrics import roc_auc_score                         # noqa: PLC0415
    from sklearn.model_selection import GroupKFold                    # noqa: PLC0415
    from build_pan25_channels import fw_profile, statics              # noqa: PLC0415

    docs = []
    for fam_dir in sorted(PILOT.iterdir()):
        if not fam_dir.is_dir():
            continue
        for f in sorted(fam_dir.glob("*.json")):
            if f.name == "manifest.json":
                continue
            r = json.loads(f.read_text(encoding="utf-8"))
            docs.append({"text": r["text"], "y": 1, "family": r["family"],
                         "regime": r["regime"], "group": r["lineage_id"]})
    for f in sorted(ESSAYS.glob("*.txt")):
        docs.append({"text": f.read_text(encoding="utf-8", errors="replace").strip(),
                     "y": 0, "family": "human", "regime": "human_draft1",
                     "group": f"argrewrite_d1_{f.stem}"})

    X = np.array([statics(d["text"], {}) + fw_profile(d["text"]) for d in docs], float)
    y = np.array([d["y"] for d in docs])
    groups = np.array([d["group"] for d in docs])

    pred = np.full(len(y), -1.0)
    for tr, te in GroupKFold(n_splits=5).split(X, y, groups):
        clf = HistGradientBoostingClassifier(max_iter=300, random_state=42)
        clf.fit(X[tr], y[tr])
        pred[te] = clf.predict_proba(X[te])[:, 1]
    hard = (pred >= 0.5).astype(int)

    def slice_acc(mask):
        return round(float((hard[mask] == y[mask]).mean()), 4) if mask.any() else None

    fams = sorted({d["family"] for d in docs if d["y"] == 1})
    regs = sorted({d["regime"] for d in docs if d["y"] == 1})
    out = {
        "n_machine": int(y.sum()), "n_human": int((1 - y).sum()),
        "features": "9 statics + 40 function-word rates, document level",
        "cv": "GroupKFold(5) by lineage (rewrites never straddle their sources)",
        "accuracy": round(float((hard == y).mean()), 4),
        "auc": round(float(roc_auc_score(y, pred)), 4),
        "human_called_machine_rate": round(float(hard[y == 0].mean()), 4),
        "machine_called_human_rate": round(float(1 - hard[y == 1].mean()), 4),
        "per_family_accuracy": {f: slice_acc(np.array([d["family"] == f for d in docs]))
                                for f in fams},
        "per_regime_accuracy": {r: slice_acc(np.array([d["regime"] == r for d in docs]))
                                for r in regs},
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    dest = RESULTS / "surface_ref.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1))
    print(f"wrote {dest.relative_to(REPO)}")


if __name__ == "__main__":
    main()
