"""2.1.6 — the leakage reference on MATCHED cells: does the 0.98 trivia detector collapse
when length and register are matched by construction?

L135 measured the unmatched pilot: nine statics plus forty function-word rates read
provenance at 0.9785 accuracy / 0.9921 AUC, which made matched cells a measured
requirement, not a preference. This runner is the first matched cell: argumentative
essays on both sides (register matched by class), machine side = the G153 thin-prompt
essays plus the G159 rewrites, human side = ArgRewrite Draft1 essays, length matched by
stratified subsampling into shared word-count deciles (documents outside the overlap are
dropped and counted). Same features, same model, GroupKFold by lineage. The per-cell
accuracy of this reference is the cell's standing shortcut label (HUMAN_NEGATIVES_2_0 §4).

DESIGN CHECK (2026-08-19, at design time). Lessons read: LESSONS §3 to §5, CONTROLS 6/7.
Exploratory infrastructure measurement, no verdict bands, nothing VOIDs. Expectations
both ways: under the L135 alternative (the unmatched number was carried by length and
register trivia) accuracy falls substantially toward the topic/style floor; under the
null (the statics carry provenance beyond length and register) it stays high — BOTH
outcomes are informative and neither is a detector claim (contract §3b: this instrument
is an I1 diagnostic). Failure direction of the instrument: over-matching (subsampling so
aggressively that n collapses) fakes a drop — n per cell and the dropped counts are
reported beside the accuracy, and cells under 30 per side are labeled uninterpretable.

CPU, minutes. Output: results/g153_pilot/matched_ref.json
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
REBUILD = REPO / "corpora" / "g159_rebuild"
ESSAYS = REPO / "corpora" / "public" / "argrewrite" / "essays" / "Draft1"
SEED = 15960


def main() -> None:
    import numpy as np
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import GroupKFold
    from build_pan25_channels import fw_profile, statics

    rng = np.random.default_rng(SEED)
    docs = []
    for root in (PILOT, REBUILD):
        for fam_dir in sorted(root.iterdir()):
            if not fam_dir.is_dir():
                continue
            for f in sorted(fam_dir.glob("*.json")):
                if f.name == "manifest.json":
                    continue
                r = json.loads(f.read_text(encoding="utf-8"))
                docs.append({"text": r["text"], "y": 1, "family": r.get("family", "?"),
                             "group": r.get("lineage_id", f"{root.name}_{f.stem}")})
    for f in sorted(ESSAYS.glob("*.txt")):
        docs.append({"text": f.read_text(encoding="utf-8", errors="replace").strip(),
                     "y": 0, "family": "human", "group": f"argrewrite_d1_{f.stem}"})

    for d in docs:
        d["nw"] = len(d["text"].split())

    # shared word-count deciles over the OVERLAP, equal counts per side per decile
    h = [d for d in docs if d["y"] == 0]
    m = [d for d in docs if d["y"] == 1]
    lo = max(min(d["nw"] for d in h), min(d["nw"] for d in m))
    hi = min(max(d["nw"] for d in h), max(d["nw"] for d in m))
    inside = [d for d in docs if lo <= d["nw"] <= hi]
    dropped = len(docs) - len(inside)
    edges = np.quantile([d["nw"] for d in inside], np.linspace(0, 1, 6))  # quintiles
    kept = []
    per_stratum = []
    for a, b in zip(edges[:-1], edges[1:]):
        sh = [d for d in inside if d["y"] == 0 and a <= d["nw"] <= b]
        sm = [d for d in inside if d["y"] == 1 and a <= d["nw"] <= b]
        n = min(len(sh), len(sm))
        per_stratum.append({"band": [int(a), int(b)], "n_per_side": n})
        for pool in (sh, sm):
            idx = rng.permutation(len(pool))[:n]
            kept.extend(pool[i] for i in idx)

    X = np.array([statics(d["text"], {}) + fw_profile(d["text"]) for d in kept], float)
    y = np.array([d["y"] for d in kept])
    groups = np.array([d["group"] for d in kept])
    pred = np.full(len(y), -1.0)
    for tr, te in GroupKFold(n_splits=5).split(X, y, groups):
        clf = HistGradientBoostingClassifier(max_iter=300, random_state=SEED)
        clf.fit(X[tr], y[tr])
        pred[te] = clf.predict_proba(X[te])[:, 1]
    hard = (pred >= 0.5).astype(int)

    out = {
        "seed": SEED,
        "matching": "register by class (argumentative essays both sides); length by "
                    "equal-count quintile strata inside the shared word-count overlap",
        "n_dropped_outside_overlap": dropped,
        "strata": per_stratum,
        "n_machine": int(y.sum()), "n_human": int((1 - y).sum()),
        "accuracy": round(float((hard == y).mean()), 4),
        "auc": round(float(roc_auc_score(y, pred)), 4),
        "human_called_machine_rate": round(float(hard[y == 0].mean()), 4),
        "unmatched_reference": {"accuracy": 0.9785, "auc": 0.9921, "source": "L135"},
        "interpretation_rule": "this cell's accuracy is its standing shortcut label; a "
                               "large fall from L135 = the unmatched number was length "
                               "and register trivia; persistence = the statics carry "
                               "more than the match controls (both informative, neither "
                               "a detector claim)",
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "matched_ref.json").write_text(json.dumps(out, indent=1),
                                              encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
