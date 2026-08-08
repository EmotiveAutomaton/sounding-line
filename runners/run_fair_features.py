"""G100 — re-try L2's three executed candidates under the fair induction control.

L2 killed conditional constructions, contractions and phrasal coordination with the old induction
control. **L22 showed that control's regressors contain the dose** (row-sum of the spec indicator =
rung), and L23 showed the flagship effect comes back *stronger* under the within-rung fair control.
**A feature that genuinely tracks dose would have been executed exactly like an induced one.** So the
three deaths are suspended until this runs.

CPU-only: feature values come from the caches in results/features/, specifications from the verified
reconstruction arithmetic. Same machinery as run_induction_v2, pointed at features instead of the
ratio.

    REVIVED   the feature survives length + within-rung specification identity (p < 0.05) with a
              consistent sign on at least two ladders
    DEAD      it does not — the kill stands, now for the right reason
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "fair_features"
LADDERS = {"ladder": (70000, "base"), "ladder2": (90000, "base"), "ladder3": (110000, "extended")}
PATTERNS = {"conditionals": ["biber_cond"], "contractions": ["biber_cont"], "coordination": ["biber_phc"]}


def main() -> None:
    import numpy as np                                                # noqa: PLC0415
    from scipy import stats                                           # noqa: PLC0415
    from scipy.stats import rankdata                                  # noqa: PLC0415
    from sklearn.linear_model import RidgeCV                          # noqa: PLC0415
    from sklearn.model_selection import KFold                         # noqa: PLC0415

    from runners.make_intent_ladder import SPECS as BASE              # noqa: PLC0415
    from runners.make_ladder3 import SPECS as EXT                     # noqa: PLC0415

    def rres(a, b):
        a, b = rankdata(a), rankdata(b)
        return a - np.polyval(np.polyfit(b, a, 1), b)

    out = {"features_matched": {}, "corpora": {}}
    for corpus, (seed, poolname) in LADDERS.items():
        cache = REPO / "results" / "features" / f"{corpus}.json"
        if not cache.exists():
            print(f"{corpus}: no feature cache"); continue
        raw = json.loads(cache.read_text(encoding="utf-8"))
        items = raw["items"] if isinstance(raw, dict) else raw
        if not items:
            print(f"{corpus}: cache shape unrecognised: {type(raw)} keys {list(raw)[:6]}"); continue
        feats0 = items[0].get("whole") or items[0].get("features", items[0])
        keys = list(feats0.keys())
        matched = {name: [k for k in keys if any(p in k.lower() for p in pats)]
                   for name, pats in PATTERNS.items()}
        out["features_matched"] = matched
        pool = list(EXT if poolname == "extended" else BASE)

        man = json.loads((REPO / "corpora" / corpus / "manifest.json").read_text(encoding="utf-8"))
        words_by_id = {it["id"]: it.get("n_words") for it in man["items"]}
        rung_by_id = {it["id"]: it.get("rung") for it in man["items"]}

        rows = []
        for it in items:
            iid = it.get("id")
            rung = rung_by_id.get(iid, it.get("group"))
            if not isinstance(rung, int):
                continue
            f = it.get("whole") or it.get("features", it)
            w = words_by_id.get(iid) or it.get("n_words") or 0
            idx = int(iid.split("_")[1])
            drawn = (random.Random(seed + rung * 1000 + idx).sample(pool, rung)
                     if rung > 0 else [])
            rows.append({"rung": rung, "words": w, "f": f,
                         "spec_idx": [pool.index(s) for s in drawn]})
        n = len(rows)
        if n < 30:
            print(f"{corpus}: only {n} usable rows"); continue
        rung = np.array([r["rung"] for r in rows], float)
        words = np.array([r["words"] for r in rows], float)
        X = np.zeros((n, len(pool)))
        for i, r in enumerate(rows):
            X[i, r["spec_idx"]] = 1.0
        Xc = X.copy()
        for g in sorted(set(rung)):
            m = rung == g
            Xc[m] -= Xc[m].mean(0)

        def oof(M, y):
            pred = np.zeros(n)
            for tr, te in KFold(5, shuffle=True, random_state=0).split(M):
                pred[te] = RidgeCV(alphas=np.logspace(-2, 3, 20)).fit(M[tr], y[tr]).predict(M[te])
            return pred

        res = {}
        print(f"\n{corpus} (n={n}, pool={len(pool)})")
        print(f"  {'feature':<26}{'raw':>8}{'old ctl':>9}{'FAIR ctl':>10}{'p fair':>9}")
        for name, ks in matched.items():
            for k in ks:
                y = np.array([float(r["f"].get(k, 0.0) or 0.0) for r in rows])
                if np.std(y) == 0:
                    continue
                r_raw = float(stats.spearmanr(rung, y).statistic)
                vals = {}
                for tag, M in (("old", X), ("fair", Xc)):
                    resid = y - oof(M, y)
                    rho, p = stats.spearmanr(rres(resid, words), rres(rung, words))
                    vals[tag] = (float(rho), float(p))
                res[k] = {"group": name, "raw": r_raw,
                          "old": vals["old"], "fair": vals["fair"]}
                print(f"  {k:<26}{r_raw:>+8.3f}{vals['old'][0]:>+9.3f}"
                      f"{vals['fair'][0]:>+10.3f}{vals['fair'][1]:>9.4f}")
        out["corpora"][corpus] = res

    # verdict per feature group: significant + same sign on >= 2 ladders under the fair control
    verdicts = {}
    for name in PATTERNS:
        hits = []
        for corpus, res in out["corpora"].items():
            for k, v in res.items():
                if v["group"] == name and v["fair"][1] < 0.05:
                    hits.append((corpus, k, v["fair"][0]))
        signs = {np.sign(h[2]) for h in hits}
        verdicts[name] = ("REVIVED" if len({h[0] for h in hits}) >= 2 and len(signs) == 1
                          else "DEAD")
        print(f"\n  {name}: {verdicts[name]}  ({len(hits)} significant fair-control results)")
    out["verdicts"] = verdicts

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "summary.json").write_text(json.dumps(out, indent=2),
                                          encoding="utf-8", newline="\n")
    print(f"\nwrote {(RESULTS / 'summary.json').relative_to(REPO)}")


if __name__ == "__main__":
    import numpy as np                                                # noqa: PLC0415
    main()
