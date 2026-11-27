"""Within-responder offer surprise and change, with whole-player intervals.

DESIGN CHECK: independent planted slopes must survive a large personal baseline.
A collinear gap or a sign without variation cannot supply a coefficient.
An interrupted trial sequence never creates a previous-offer comparison.
"""
import numpy as np
import pandas as pd


COLUMNS = "sub role trial reward RP RPE EP_X1 EP_Y1 feedback_X1 feedback_Y1 EPE_X1 EPE_Y1".split()
TERMS = (("offer", "gap", "change"), ("larger_positive_gap",), ("larger_negative_gap",))


def responders(frame):
    if frame["sub"].isna().any() or not frame.role.isin(["self", "other"]).all():
        raise ValueError("Unknown player or role")
    if frame.groupby("sub").role.nunique().ne(1).any():
        raise ValueError("Role changes within player")
    rows = frame.loc[frame.role.eq("self")].copy().sort_values(["sub", "trial"])
    if rows.empty or rows.duplicated(["sub", "trial"]).any():
        raise ValueError("Missing or duplicate responder trials")
    if not rows.trial.isin(range(1, 21)).all():
        raise ValueError("Unbound trial order")
    for col in ("reward", "RP"):
        if not rows[col].dropna().between(0, .5).all():
            raise ValueError("Amount outside the documented responder scale")
    rows["gap"] = rows.reward - rows.RP
    for actual, expected in ((rows.gap, rows.RPE),
                             (rows.feedback_X1 - rows.EP_X1, rows.EPE_X1),
                             (rows.feedback_Y1 - rows.EP_Y1, rows.EPE_Y1)):
        if not np.allclose(actual, expected, atol=1e-9, rtol=0, equal_nan=True):
            raise ValueError("Released prediction-error binding disagrees")
    grouped = rows.groupby("sub")
    adjacent = rows.trial.sub(grouped.trial.shift()).eq(1)
    rows["change"] = (rows.reward - grouped.reward.shift()).where(adjacent)
    rows["gap_size"] = rows.gap.abs()
    return rows


def sufficient(frame, columns, outcome, roster):
    k = len(columns)
    xtx = np.zeros((len(roster), k, k))
    xty = np.zeros((len(roster), k))
    complete = frame.dropna(subset=[*columns, outcome])
    if not np.isfinite(complete[[*columns, outcome]].to_numpy(float)).all():
        raise ValueError("Nonfinite analysis values")
    contributors = 0
    for person, records in complete.groupby("sub"):
        arr = records[[*columns, outcome]].to_numpy(float)
        arr -= arr.mean(axis=0)
        x, y = arr[:, :-1], arr[:, -1]
        i = roster[person]
        xtx[i] = x.T @ x
        xty[i] = x.T @ y
        contributors += int(np.any(x))
    return xtx, xty, {"complete_trials": len(complete), "varying_players": contributors}


def fit(frame, draws=2000):
    rows = responders(frame)
    ids = rows["sub"].unique()
    roster = {p: i for i, p in enumerate(ids)}
    rng = np.random.default_rng(20261122)
    counts = np.array([np.bincount(rng.integers(len(ids), size=len(ids)), minlength=len(ids))
                       for _ in range(draws)])
    models = [(rows, ["reward", "gap", "change"], "feedback_X1"),
              (rows[rows.gap.gt(0)], ["gap_size"], "feedback_Y1"),
              (rows[rows.gap.lt(0)], ["gap_size"], "feedback_Y1")]
    results, models_support = {}, []
    for names, (sample, columns, outcome) in zip(TERMS, models, strict=True):
        a, b, support = sufficient(sample, columns, outcome, roster)
        cross = a.sum(axis=0)
        support["rank"] = int(np.linalg.matrix_rank(cross))
        models_support.append(support)
        if support["rank"] != len(names):
            for name in names:
                results[name] = {"identified": False}
            continue
        point = np.linalg.solve(cross, b.sum(axis=0))
        bank_a = np.einsum("dp,pij->dij", counts, a)
        bank_b = counts @ b
        ok = np.linalg.matrix_rank(bank_a) == len(names)
        estimates = np.linalg.solve(bank_a[ok], bank_b[ok, :, None])[:, :, 0]
        for i, name in enumerate(names):
            interval = np.quantile(estimates[:, i], [.025, .975]).tolist() if ok.all() else None
            results[name] = dict(identified=True, estimate=float(point[i]), interval=interval,
                                 valid_draws=int(ok.sum()), bootstrap_se=float(estimates[:, i].std(ddof=1)) if ok.sum()>1 else None)
    required = [results[k].get("interval") for k in ("gap","change","larger_positive_gap","larger_negative_gap")]
    return dict(terms=results, registered_bar_met=all(x is not None and x[0]>0 for x in required),
                responders=len(ids), responder_trials=len(rows), observer_trials=int(frame.role.eq("other").sum()),
                observer_players=frame.loc[frame.role.eq("other"),"sub"].nunique(),
                trials_without_previous=int(rows.change.isna().sum()), zero_gap_trials=int(rows.gap.eq(0).sum()),
                models=models_support, whole_player_draws=draws)

