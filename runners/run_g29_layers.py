"""G29 — which layer carries the maker? Predicted in advance: if one fails, it is leaked.

Analysis-only, over the G28 triples (L88): author classification from the eight-concept
profiles, per arm. If the leaked layer is the record of the maker (DECISION_TRACES §3), the
leaked profiles should carry author identity; the emblematic profiles carry the performed,
situational layer and should carry less of it.

Lessons applied (LESSONS §3): the floor is the measured majority-class share, never assumed
uniform; each arm carries a label-permutation null; the retest arm doubles as a stability
reference (agreement between leaked and leaked2 accuracies bounds reader noise).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PART = REPO / "results" / "g28_twolayers" / "partial.jsonl"
OUT = REPO / "results" / "g28_twolayers" / "g29_layers.json"
CONCEPTS = ["seeking", "rage", "fear", "lust", "care", "panic_grief", "play",
            "none_recoverable"]


def main() -> None:
    import numpy as np                                                # noqa: PLC0415
    from sklearn.linear_model import LogisticRegression               # noqa: PLC0415
    from sklearn.model_selection import StratifiedKFold, cross_val_score  # noqa: PLC0415
    from sklearn.pipeline import make_pipeline                        # noqa: PLC0415
    from sklearn.preprocessing import StandardScaler                  # noqa: PLC0415

    rows = [json.loads(l) for l in PART.read_text(encoding="utf-8").splitlines()]
    by: dict[str, dict[str, list]] = {}
    for r in rows:
        by.setdefault(r["arm"], {})[r["id"]] = [r["profile"][c] for c in CONCEPTS]

    ids = sorted(set.intersection(*(set(v) for v in by.values())))
    authors = np.array([i.split("__")[0] for i in ids])
    n_auth = len(set(authors))
    shares = {a: float((authors == a).mean()) for a in set(authors)}
    floor = max(shares.values())
    print(f"{len(ids)} texts, {n_auth} authors, majority-share floor {floor:.3f}")

    def acc(arm, y):
        X = np.array([by[arm][i] for i in ids])
        clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, C=1.0))
        cv = StratifiedKFold(5, shuffle=True, random_state=0)
        return float(np.mean(cross_val_score(clf, X, y, cv=cv)))

    rng = np.random.default_rng(29)
    res = {}
    for arm in ("leaked", "emblematic", "leaked2"):
        a = acc(arm, authors)
        null = [acc(arm, rng.permutation(authors)) for _ in range(60)]
        p = float((np.sum(np.array(null) >= a) + 1) / (len(null) + 1))
        res[arm] = {"acc": round(a, 3), "perm_p": round(p, 4),
                    "null_mean": round(float(np.mean(null)), 3)}
        print(f"{arm:10s} author-acc {a:.3f} (floor {floor:.3f}, "
              f"perm null {np.mean(null):.3f}, p {p:.4f})")

    lk, em = res["leaked"]["acc"], res["emblematic"]["acc"]
    sig_l = res["leaked"]["perm_p"] < 0.05 and lk > floor
    sig_e = res["emblematic"]["perm_p"] < 0.05 and em > floor
    if sig_l and not sig_e:
        verdict = "LEAKED-CARRIES"
    elif sig_e and not sig_l:
        verdict = "EMBLEMATIC-CARRIES, against the advance prediction"
    elif sig_l and sig_e:
        verdict = "BOTH-CARRY"
    else:
        verdict = "NEITHER-CARRIES"
    out = {"n_texts": len(ids), "n_authors": n_auth, "floor_majority_share": round(floor, 3),
           "arms": res, "verdict": verdict,
           "note": "8-dim profiles from a single reader; author here also spans era and "
                   "genre, so identity is the easy direction and a null is informative"}
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print(f">>> {verdict}")
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
