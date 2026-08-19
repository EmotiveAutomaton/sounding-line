"""G97 — maker as a random effect: do the within-maker positives survive a hierarchical
refit that gives every author their own intercept?

Owed since the methods pass (L93; the reporting clause of the G129 card called for "the
G97 machinery when it lands"). The PD-33 family's decomposition (L57) showed the
polish-side's excess between-share follows the author; this runner asks the harder
question those variance shares approximate: fit the polish-minus-depth contrast per
window as a mixed model with author random intercepts, and report whether the fixed
effect survives when author clustering is modeled instead of pooled — plus the intraclass
correlation, which is the maker-signature quantity itself.

Method: from the same feature cache as the decomposition (`argrewrite_w80.json`, 80-word
windows over 258 items = 86 authors x up to 3 drafts), z-score every polish feature and
every depth feature over the pool, form per-window composites (mean of z's per side), and
fit  diff = polish_z - depth_z  ~ 1 + (1 | author)  by REML (statsmodels MixedLM). The
same model refits each side separately, and a draft-within-author variance component is
read from the author_draft grouping run as a nested check.

DESIGN CHECK (2026-08-19, at design time). Lessons read: LESSONS §3 (bounded statistics,
every verdict statistic on disk, no silent bands), §4, §5; CONTROLS 6/7. Exploratory
refit of standing positives, no verdict bands, nothing VOIDs. Expectations, both ways:
under the maker-signature reading (L57), the author random-intercept variance is large
(high ICC) and the fixed effect's clustered standard error grows but the contrast
survives; under the pooled-artifact alternative (the positives were pseudoreplication),
the fixed effect's significance collapses once windows stop being counted as independent
— THE GUARDED FAILURE, direction: p rises toward 1 as the effective n falls from windows
to authors. Both outcomes are informative and preregistered as such: survival upgrades
the positives' evidence tier, collapse downgrades them and every downstream row says so
(the re-run-what-it-touches rule). Instrument failure direction: singular fits (variance
component at the boundary) are reported as UNRESOLVED, never coerced.

Output: results/g97/maker_effect.json. CPU only.
"""

from __future__ import annotations

import json
import re
import sys
import warnings
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "runners"))
from run_pd33_decomposition import (CACHE, POLISH_PATTERNS,            # noqa: E402
                                    DEPTH_PATTERNS, parse_ids)

OUT = REPO / "results" / "g97"


def main() -> None:
    import numpy as np
    import pandas as pd
    from statsmodels.regression.mixed_linear_model import MixedLM

    items = [it for it in json.loads(CACHE.read_text(encoding="utf-8"))["items"]
             if it.get("windows")]
    keys = sorted(set.intersection(*(set(it["windows"][0]) for it in items)))
    pol = [k for k in keys if any(p in k.lower() for p in POLISH_PATTERNS)]
    dep = [k for k in keys if any(p in k.lower() for p in DEPTH_PATTERNS)]

    rows = []
    for it in items:
        author, draft = parse_ids(it["id"])
        for wi, w in enumerate(it["windows"]):
            rows.append({"author": author, "draft": draft, "item": it["id"], "wi": wi,
                         **{k: float(w.get(k, 0.0) or 0.0) for k in pol + dep}})
    df = pd.DataFrame(rows)
    for k in pol + dep:
        v = df[k]
        df[k] = (v - v.mean()) / (v.std() if v.std() > 0 else 1.0)
    df["polish_z"] = df[pol].mean(axis=1)
    df["depth_z"] = df[dep].mean(axis=1)
    df["diff"] = df["polish_z"] - df["depth_z"]

    def fit(col, groups):
        with warnings.catch_warnings(record=True) as wlist:
            warnings.simplefilter("always")
            m = MixedLM(df[col], np.ones((len(df), 1)), groups=df[groups]).fit(reml=True)
            singular = any("singular" in str(x.message).lower()
                           or "boundary" in str(x.message).lower() for x in wlist)
        var_re = float(m.cov_re.iloc[0, 0])
        var_resid = float(m.scale)
        icc = var_re / (var_re + var_resid) if (var_re + var_resid) > 0 else None
        return {"fixed_effect": round(float(m.params.iloc[0]), 5),
                "se_clustered": round(float(m.bse.iloc[0]), 5),
                "p": float(f"{m.pvalues.iloc[0]:.3e}"),
                "var_author": round(var_re, 5), "var_resid": round(var_resid, 5),
                "icc": round(icc, 4) if icc is not None else None,
                "singular_or_boundary": singular,
                "n_windows": int(len(df)), "n_groups": int(df[groups].nunique())}

    # pooled comparison: the naive per-window t-test the mixed model disciplines
    from scipy import stats
    t, p_naive = stats.ttest_1samp(df["diff"], 0.0)

    df["author_draft"] = df["author"] + "_" + df["draft"]
    out = {
        "prereg": "runner docstring DESIGN CHECK (exploratory refit; no verdict bands)",
        "cache": str(CACHE.relative_to(REPO)),
        "n_authors": int(df["author"].nunique()),
        "n_features": {"polish": len(pol), "depth": len(dep)},
        "naive_pooled_t": {"t": round(float(t), 3), "p": float(f"{p_naive:.3e}"),
                           "note": "windows treated as independent — the form the mixed "
                                   "model exists to discipline"},
        "diff_author_RE": fit("diff", "author"),
        "diff_authordraft_RE": fit("diff", "author_draft"),
        "polish_author_RE": fit("polish_z", "author"),
        "depth_author_RE": fit("depth_z", "author"),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "maker_effect.json").write_text(json.dumps(out, indent=1),
                                           encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
