"""G130b — the decisive lexical-matching control. L42's relabel hangs on this.

The claim under test: "content" revisions remain identifiable after lexical sophistication is
unavailable as a shortcut. Content and surface revisions are matched on the program's named
variables (insertion/deletion size, word-count change, word rarity shift, sentence position,
original sentence difficulty), then the surface/content classification is re-run on the matched
set with the same diff-features arm that scores 0.857 unmatched.

    SURVIVES   matched-set macro-F1 stays well above chance (>= 0.65) -- content is more than
               sophistication and L42's demoted claim regains a leg
    COLLAPSES  matched-set F1 falls toward chance -- L42 was a sophistication measure, closed

Matching is 1:1 greedy nearest-neighbour on z-scored covariates, content events to surface
events, caliper 1.0 SD overall distance; unmatched events are dropped and the drop is reported.
Covariate balance before/after is reported, since a matching that does not balance is theatre.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "arg_baselines"
EVENTS = RESULTS / "events.json"

COMMON = None


def rare_rate(text: str) -> float:
    global COMMON
    if COMMON is None:
        from wordfreq import top_n_list                               # noqa: PLC0415
        COMMON = set(top_n_list("en", 5000))
    ws = [w.strip(".,;:!?\"'()").lower() for w in text.split()]
    ws = [w for w in ws if w]
    if not ws:
        return 0.0
    return sum(w not in COMMON for w in ws) / len(ws)


def main() -> None:
    import numpy as np                                                # noqa: PLC0415
    from scipy.spatial.distance import cdist                          # noqa: PLC0415
    from sklearn.feature_extraction.text import TfidfVectorizer      # noqa: PLC0415
    from sklearn.linear_model import LogisticRegression               # noqa: PLC0415
    from sklearn.model_selection import GroupKFold                    # noqa: PLC0415
    from sklearn.metrics import f1_score                              # noqa: PLC0415

    events = [e for e in json.loads(EVENTS.read_text(encoding="utf-8"))["events"]
              if e["coarse"] in ("surface", "content")]

    def covs(e):
        o, n = e["old"].split(), e["new"].split()
        os_, ns_ = set(w.lower() for w in o), set(w.lower() for w in n)
        return [len(ns_ - os_), len(os_ - ns_), len(n) - len(o),
                rare_rate(e["new"]) - rare_rate(e["old"]),
                min(len(o), 60), rare_rate(e["old"])]

    C = np.array([covs(e) for e in events], float)
    y = np.array([e["coarse"] == "content" for e in events])
    Z = (C - C.mean(0)) / (C.std(0) + 1e-9)

    ci, si = np.where(y)[0], np.where(~y)[0]
    D = cdist(Z[ci], Z[si])
    used, pairs = set(), []
    order = np.argsort(D.min(axis=1))
    for row in order:
        cols = np.argsort(D[row])
        for c in cols:
            if c not in used and D[row, c] < 1.0 * np.sqrt(Z.shape[1]):
                used.add(c)
                pairs.append((ci[row], si[c]))
                break
    keep = sorted({i for p in pairs for i in p})
    print(f"{len(events)} events -> {len(pairs)} matched pairs "
          f"({len(events) - len(keep)} dropped)")

    def smd(idx):
        a = C[[p[0] for p in pairs]] if idx == "after_c" else None
        cc = C[y][:, :] if idx == "before" else C[[p[0] for p in pairs]]
        ss = C[~y][:, :] if idx == "before" else C[[p[1] for p in pairs]]
        return [round(float(abs(cc[:, j].mean() - ss[:, j].mean())
                            / (C[:, j].std() + 1e-9)), 3) for j in range(C.shape[1])]

    balance = {"before": smd("before"), "after": smd("after")}
    print("standardized mean differences before:", balance["before"])
    print("                            after:  ", balance["after"])
    if max(balance["after"]) > 0.25:
        print(">>> MATCHING-FAILED -- covariates not balanced; no verdict")
        RESULTS.joinpath("matched_control.json").write_text(json.dumps(
            {"verdict": "MATCHING-FAILED", "balance": balance, "n_pairs": len(pairs)},
            indent=1), encoding="utf-8", newline="\n")
        sys.exit(1)

    sub = [events[i] for i in keep]
    ys = [e["coarse"] for e in sub]
    groups = [e["author"] for e in sub]

    def diff_text(e):
        o, n = set(e["old"].lower().split()), set(e["new"].lower().split())
        return (" ".join(f"ADD_{w}" for w in sorted(n - o)) + " " +
                " ".join(f"DEL_{w}" for w in sorted(o - n)) +
                f" || {e['old']} || {e['new']}")

    vec = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
    X = vec.fit_transform([diff_text(e) for e in sub])
    preds = [None] * len(ys)
    for tr, te in GroupKFold(n_splits=5).split(X, ys, groups):
        clf = LogisticRegression(max_iter=2000).fit(X[tr], [ys[i] for i in tr])
        for i, p in zip(te, clf.predict(X[te])):
            preds[i] = p
    f1 = float(f1_score(ys, preds, average="macro"))
    verdict = "SURVIVES" if f1 >= 0.65 else "COLLAPSES"
    print(f"matched-set macro-F1 {f1:.3f} (unmatched arm was 0.857)\n  >>> {verdict}")

    RESULTS.joinpath("matched_control.json").write_text(json.dumps(
        {"n_pairs": len(pairs), "balance": balance, "matched_macro_f1": f1,
         "unmatched_reference": 0.857, "verdict": verdict}, indent=1),
        encoding="utf-8", newline="\n")
    print(f"wrote {(RESULTS / 'matched_control.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
