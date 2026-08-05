"""False-discovery control — the half of the feature sweep that is not optional.

── WHY THIS IS NOT OPTIONAL ──────────────────────────────────────────────────────────────────

`FINDINGS.md`, known weakness 1: **this project has never corrected for multiple comparisons.**
Roughly twenty-five tests have been run at p < 0.05, and at least one false positive is expected
from chance alone.

`measures/features.py` now supplies **342 candidate features**. Testing 342 at p < 0.05 produces
**~17 false positives by construction**. Screening them without correction would be strictly worse
than having no features at all, because it would manufacture exactly the kind of result this project
has spent three days learning to distrust.

So the two modules ship together and the sweep runners always call this one.

── WHAT IS USED ──────────────────────────────────────────────────────────────────────────────

tsfresh's `calculate_relevance_table`, which is the FRESH procedure: an appropriate hypothesis test
per feature given its type and the target's type (Kendall rank, Kolmogorov-Smirnov, or Fisher's
exact), then **Benjamini-Yekutieli** over the resulting p-values.

**Benjamini-Yekutieli rather than Benjamini-Hochberg on purpose.** BH controls the false discovery
rate only under independence or positive dependence. Our features are heavily and *unknown-signedly*
correlated — LFTK, BiberPlus and TextDescriptives all count overlapping things on the same text — so
the BH assumption does not hold. BY is valid under arbitrary dependence. It is more conservative,
and that is the correct trade here.
"""

from __future__ import annotations

from typing import Any

DEFAULT_FDR = 0.05


def relevance(names: list[str], matrix: list[list[float]], target: list[float],
              fdr_level: float = DEFAULT_FDR, ml_task: str = "regression") -> Any:
    """The full tsfresh relevance table: p-value and BY-corrected keep/drop per feature.

    `target` is the thing being predicted — the ladder rung, for our purposes. Returns a DataFrame
    sorted by p-value with a boolean `relevant` column.
    """
    import pandas as pd                                              # noqa: PLC0415
    from tsfresh.feature_selection.relevance import (                # noqa: PLC0415
        calculate_relevance_table)

    X = pd.DataFrame(matrix, columns=names)
    y = pd.Series(target)
    # drop constant columns first: they carry no information and tsfresh warns per column
    keep = [c for c in X.columns if X[c].nunique() > 1]
    X = X[keep]
    return calculate_relevance_table(X, y, ml_task=ml_task, fdr_level=fdr_level,
                                     hypotheses_independent=False)


def significant(names: list[str], matrix: list[list[float]], target: list[float],
                fdr_level: float = DEFAULT_FDR, ml_task: str = "regression") -> list[dict]:
    """Only the features that survive BY correction, most significant first.

    **An empty list is a real and useful answer.** It means 342 off-the-shelf linguistic features,
    every one of them validated somewhere in the literature, carry nothing about the target once
    multiplicity is accounted for — which would be a far stronger negative result than ten
    hand-written misses, and worth reporting as such.
    """
    tbl = relevance(names, matrix, target, fdr_level, ml_task)
    out = []
    for _, r in tbl.iterrows():
        if bool(r["relevant"]):
            out.append({"feature": str(r["feature"]), "p": float(r["p_value"]),
                        "type": str(r.get("type", ""))})
    return out


def summarise(names: list[str], matrix: list[list[float]], target: list[float],
              fdr_level: float = DEFAULT_FDR) -> dict:
    """Counts worth printing before any individual feature is looked at.

    Reporting `n_uncorrected` alongside `n_relevant` is the point: the gap between them is the
    number of features we would have believed without the correction.
    """
    tbl = relevance(names, matrix, target, fdr_level)
    n_raw = int((tbl["p_value"] < 0.05).sum())
    n_rel = int(tbl["relevant"].sum())
    return {"n_features_tested": int(len(tbl)),
            "n_uncorrected_p05": n_raw,
            "n_expected_by_chance": round(0.05 * len(tbl), 1),
            "n_relevant_after_BY": n_rel,
            "fdr_level": fdr_level,
            "top": [{"feature": str(r["feature"]), "p": float(r["p_value"])}
                    for _, r in tbl.head(10).iterrows()]}
