"""GAT2, November 24 ruling. Within-rater logistic fits and whole-rater resampling."""
import numpy as np
import pandas as pd
from scipy.special import expit, logit

RATINGS = ["intel", "amb", "intel3_1", "amb3_1"]
COLS = ["iid", "wave", "order", "dec", *RATINGS]
READINGS = ("mean", "intelligence", "ambition")


def cohort(frame):
    frame = frame[COLS].apply(pd.to_numeric, errors="raise")
    if frame.iid.isna().any() or frame.wave.isna().any() or frame.groupby("iid").wave.nunique().max() != 1:
        raise ValueError("Unbound rater or occasion")
    complete = frame.dec.isin([0, 1]) & frame[RATINGS].ge(1).all(axis=1) & frame[RATINGS].le(10).all(axis=1)
    valid = frame.loc[complete].copy()
    counts = {"source_rows": len(frame), "source_raters": frame.iid.nunique(), "invalid_or_missing_rows": int((~complete).sum())}
    counts["raters_without_complete_rows"] = frame.iid.nunique() - valid.iid.nunique()
    own = valid.groupby("iid")[RATINGS[2:]].nunique()
    inconsistent = own.index[(own > 1).any(axis=1)]
    counts["inconsistent_self_raters"] = len(inconsistent)
    valid = valid.loc[~valid.iid.isin(inconsistent)]
    sizes = valid.groupby("iid").size()
    counts["insufficient_repeat_raters"] = int((sizes < 2).sum())
    valid = valid.loc[valid.iid.isin(sizes.index[sizes >= 2])]
    deviations = valid.groupby("iid")[RATINGS[:2]].transform("std", ddof=0)
    usable = (deviations > 0).all(axis=1)
    counts["zero_spread_raters"] = valid.loc[~usable, "iid"].nunique()
    valid = valid.loc[usable]
    counts.update(analysed_raters=valid.iid.nunique(), analysed_rows=len(valid))
    return valid, counts


def designs(frame):
    ids = pd.factorize(frame.iid, sort=True)[0]
    n = np.bincount(ids)
    y = frame.dec.to_numpy(float)
    partners = frame[RATINGS[:2]]
    mean = partners.groupby(frame.iid).transform("mean").to_numpy()
    sd = partners.groupby(frame.iid).transform("std", ddof=0).to_numpy()
    partner_z = (partners.to_numpy() - mean) / sd
    gaps = (partners.to_numpy() - frame[RATINGS[2:]].to_numpy()) / sd
    other = logit((np.bincount(ids, weights=y)[ids] - y + 0.5) / n[ids])
    matrices = []
    for rating, gap in [(partner_z.mean(axis=1), gaps.mean(axis=1)), *zip(partner_z.T, gaps.T)]:
        advantage = np.maximum(gap, 0)
        advantage -= (np.bincount(ids, weights=advantage) / n)[ids]
        matrices.append(np.column_stack([np.ones(len(y)), rating, rating**2, advantage, other]))
    return ids, y, matrices


def slope(x, y, weights):
    beta = np.zeros(x.shape[1])
    for _ in range(60):
        p = expit(x @ beta)
        information = x.T @ ((weights * p * (1 - p))[:, None] * x)
        if np.linalg.matrix_rank(information) != len(beta):
            return None
        step = np.linalg.solve(information, x.T @ (weights * (y - p)))
        beta += np.clip(step, -2, 2)
        if np.max(np.abs(step)) < 1e-7:
            return float(beta[3])
    return None


def disposition(intervals):
    if any(bounds is None for bounds in intervals):
        return "undecided"
    main, intelligence, ambition = intervals
    if (intelligence[0] > 0 and ambition[1] < 0) or (ambition[0] > 0 and intelligence[1] < 0):
        return "undecided, opposite clear attribute readings"
    return "registered bar met" if main[0] > 0 else "registered bar not met"


def fit(frame, progress, draws=2000):
    frame, counts = cohort(frame)
    rows = {name: {"coefficient": None, "interval": None, "valid_draws": 0} for name in READINGS}
    if counts["analysed_raters"] >= 2:
        ids, y, xs = designs(frame)
        n = counts["analysed_raters"]
        points = [slope(x, y, np.ones(len(y))) for x in xs]
        samples = [[] for _ in xs]
        rng = np.random.default_rng(2026112402)
        for i in range(draws):
            weights = rng.multinomial(n, np.full(n, 1/n))[ids]
            for j, x in enumerate(xs):
                if points[j] is not None:
                    value = slope(x, y, weights)
                    if value is not None:
                        samples[j].append(value)
            if (i + 1) % 100 == 0:
                progress(i + 1)
        for name, point, values in zip(READINGS, points, samples):
            rows[name] = {"coefficient": point, "valid_draws": len(values), "interval": np.quantile(values, [.025, .975]).tolist() if len(values) == draws else None}
    return {"support": counts, "rows": rows, "draws_requested": draws, "disposition": disposition([row["interval"] for row in rows.values()])}

