"""Does the prompt INDUCE the feature, rather than contain it?

── THE HOLE THIS CLOSES ──────────────────────────────────────────────────────────────────────

The echo check asks whether a prompt *contains* the feature it is accused of causing. Three
candidate measures passed it with a score of exactly zero. But a specification can produce a feature
without containing it:

    "acknowledging that circumstances vary a lot"      contains no conditionals -> induces them
    "warmly, as though to someone you like"            contains no contractions -> induces them

**That is semantic induction, and the echo check is blind to it.** Same class of error as the first
rich arm, which the curator caught.

── THE TEST ──────────────────────────────────────────────────────────────────────────────────

Specifications are drawn at random **without replacement** per artifact, so two artifacts at the same
rung got different specifications. That randomisation is what makes this answerable.

For each candidate feature:

1. Learn, **out of fold**, how well the identity of the drawn specifications alone predicts the
   feature. Cross-validated, so it cannot memorise.
2. Take what that prediction cannot explain — the residual.
3. Ask whether the rung still predicts the residual.

    INDUCTION   the rung effect collapses once spec identity is accounted for
    SURVIVES    the rung effect holds -- the effect is about HOW MUCH intent was specified, not
                about WHICH words were used to specify it

Also reported: how much of the feature spec identity explains on its own. A feature that spec
identity predicts well is suspect even if the residual test passes.

**Scope.** This tests the ladder's own specification pool. It cannot rule out that *any* statement of
purpose induces conditionals in *any* generator -- only that our particular pool is not doing it
through a few identifiable phrases.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "induction"
CANDIDATES = ["biber_COND", "biber_CONT", "biber_PHC"]


def main() -> None:
    import numpy as np                                               # noqa: PLC0415
    from scipy import stats                                          # noqa: PLC0415
    from sklearn.linear_model import RidgeCV                         # noqa: PLC0415
    from sklearn.model_selection import KFold                        # noqa: PLC0415

    from runners.make_intent_ladder import RUNGS, SPECS, TOPICS, build  # noqa: PLC0415

    cache = json.loads((REPO / "results" / "features" / "ladder2.json").read_text(encoding="utf-8"))
    items = {it["id"]: it for it in cache["items"]}

    # rebuild exactly which specifications each artifact received, from its generation seed
    rows = []
    for r in RUNGS:
        for i in range(20):
            name = f"r{r}_{i:02d}"
            if name not in items:
                continue
            rng = random.Random(90000 + r * 1000 + i)
            _ = TOPICS[(i + 5) % len(TOPICS)]
            picks = rng.sample(SPECS, r) if r else []
            rows.append({"id": name, "rung": r, "specs": set(picks),
                         "words": items[name]["n_words"], "f": items[name]["whole"]})

    print(f"{len(rows)} artifacts, specification pool of {len(SPECS)}\n")
    X = np.array([[1.0 if s in row["specs"] else 0.0 for s in SPECS] for row in rows])
    rung = np.array([row["rung"] for row in rows], dtype=float)
    words = np.array([row["words"] for row in rows], dtype=float)

    out = {}
    print(f"{'feature':<22}{'rung effect':>13}{'specs explain':>15}{'after removal':>15}  verdict")
    print("-" * 80)
    for feat in CANDIDATES:
        y = np.array([row["f"].get(feat, np.nan) for row in rows], dtype=float)
        if np.isnan(y).any():
            print(f"{feat:<22}  missing from cache")
            continue

        raw, _ = stats.spearmanr(rung, y)

        # out-of-fold prediction from specification identity alone
        pred = np.zeros_like(y)
        kf = KFold(n_splits=5, shuffle=True, random_state=0)
        for tr, te in kf.split(X):
            m = RidgeCV(alphas=np.logspace(-2, 3, 20)).fit(X[tr], y[tr])
            pred[te] = m.predict(X[te])
        explained, _ = stats.spearmanr(pred, y)

        resid = y - pred
        after, p_after = stats.spearmanr(rung, resid)

        # and the same with length also removed, since length is a suppressor here
        from scipy.stats import rankdata                             # noqa: PLC0415

        def rres(a, b):
            a, b = rankdata(a), rankdata(b)
            return a - np.polyval(np.polyfit(b, a, 1), b)

        after_len, p_len = stats.spearmanr(rres(resid, words), rres(rung, words))

        verdict = ("INDUCTION" if abs(after) < 0.2 or p_after > 0.05 else "SURVIVES")
        print(f"{feat:<22}{raw:>+13.3f}{explained:>+15.3f}{after:>+15.3f}  {verdict}"
              f"   (p={p_after:.2g}; with length also removed {after_len:+.3f}, p={p_len:.2g})")
        out[feat] = {"raw_rho": float(raw), "specs_explain_rho": float(explained),
                     "rho_after_removal": float(after), "p_after": float(p_after),
                     "rho_after_removal_and_length": float(after_len), "p": float(p_len),
                     "verdict": verdict}

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "induction.json").write_text(json.dumps(out, indent=2), encoding="utf-8",
                                            newline="\n")
    surv = [k for k, v in out.items() if v["verdict"] == "SURVIVES"]
    print("\n" + "=" * 80)
    print(f">>> {len(surv)} of {len(out)} survive the induction check"
          + (f": {', '.join(surv)}" if surv else ""))
    print("=" * 80)


if __name__ == "__main__":
    main()
