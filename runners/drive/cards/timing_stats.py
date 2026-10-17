"""Writer-cluster inference from sufficient statistics, with canonical ordering."""
from __future__ import annotations

import numpy as np
import math
import time
from pathlib import Path
from scipy.optimize import minimize_scalar

from runners.drive.cards import states_v2 as states
from runners.drive.cards.timing_census import read, write, filehash


def bind(output, inputs, config, artifacts):
    write(Path(output) / "TIMING_BINDINGS.json", dict(config=config,
          inputs={k: (str(Path(v).resolve()) if Path(v).is_dir() else filehash(v)) for k, v in inputs.items()},
          outputs={name: filehash(Path(output) / name) for name in artifacts}))


def check_binding(output, inputs, config):
    binding = read(Path(output) / "TIMING_BINDINGS.json")
    if binding["config"] != config or binding["inputs"] != {k: (str(Path(v).resolve()) if Path(v).is_dir() else filehash(v)) for k, v in inputs.items()}:
        raise ValueError("timing card inputs or configuration changed")
    if any(filehash(Path(output) / name) != expected for name, expected in binding["outputs"].items()):
        raise ValueError("timing card intermediate/output changed")


def sufficient(x, y, writers, within=False):
    x, y, writers = np.asarray(x, float), np.asarray(y, float), np.asarray(writers)
    if x.ndim != 2 or len(x) != len(y) or len(y) != len(writers) or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("invalid regression observations")
    groups = []
    for writer in sorted(set(writers)):
        a, b = x[writers == writer], y[writers == writer]
        if within:
            a, b = a - a.mean(0), b - b.mean()
        groups.append(dict(n=len(b), xx=a.T @ a, xy=a.T @ b, yy=float(b @ b), sx=a.sum(0), sy=float(b.sum())))
    return groups


def fit(groups, random_intercept=False):
    xx = sum(g["xx"] for g in groups)
    xy = sum(g["xy"] for g in groups)
    yy = sum(g["yy"] for g in groups)
    n = sum(g["n"] for g in groups)
    # Constant nuisance columns are absent from the estimand, but the target
    # column may never be removed or silently replaced.
    keep = np.flatnonzero(np.diag(xx) > 1e-10)
    if 0 not in keep:
        raise ValueError("primary contrast has no within-writer support")

    def solve(ratio):
        a, b, c = xx.copy(), xy.copy(), yy
        if ratio:
            for g in groups:
                weight = ratio / (1 + g["n"] * ratio)
                a -= weight * np.outer(g["sx"], g["sx"])
                b -= weight * g["sx"] * g["sy"]
                c -= weight * g["sy"] ** 2
        a, b = a[np.ix_(keep, keep)], b[keep]
        scale = np.sqrt(np.maximum(np.diag(a), 1e-30))
        standardized = a / np.outer(scale, scale)
        if np.linalg.matrix_rank(standardized, tol=1e-9) != len(keep):
            raise ValueError("regression design not identifiable")
        beta = np.linalg.solve(standardized, b / scale) / scale
        rss = max(c - float(beta @ b), np.finfo(float).tiny)
        objective = n * np.log(rss / n) + sum(np.log1p(g["n"] * ratio) for g in groups)
        return objective, beta

    ratio = 0.
    if random_intercept:
        optimum = minimize_scalar(lambda log_r: solve(float(np.exp(log_r)))[0], bounds=(-15, 15), method="bounded",
                                  options={"xatol": 1e-5})
        candidate = float(np.exp(optimum.x))
        if optimum.success and solve(candidate)[0] < solve(0.)[0]:
            ratio = candidate
    _, beta = solve(ratio)
    return float(beta[np.flatnonzero(keep == 0)[0]]), ratio


def regression(x, y, writers, *, within=False, random_intercept=False, draws=2000, seed=20261017, direction=1, on_tenth=None):
    started = time.monotonic()
    groups = sufficient(x, y, writers, within)
    if len(groups) < 3:
        return dict(state="invalid", reason="fewer than three independent writers", writers=len(groups))
    try:
        effect, variance_ratio = fit(groups, random_intercept)
    except ValueError as exc:
        return dict(state="invalid", reason=str(exc), writers=len(groups))
    rng = np.random.default_rng(seed)
    samples = []
    for draw in range(draws):
        selected = rng.integers(0, len(groups), len(groups))
        try:
            samples.append(fit([groups[i] for i in selected], random_intercept)[0])
        except ValueError as exc:
            return dict(state="invalid", reason="undefined bootstrap fit: " + str(exc), writers=len(groups))
        if on_tenth is not None and draw + 1 == math.ceil(draws / 10):
            on_tenth(dict(primary_seconds=time.monotonic() - started, completed_draws=draw + 1, total_draws=draws))
    low, high = np.quantile(samples, [.025, .975]).tolist()
    se = float(np.std(samples, ddof=1))
    z = effect / se if se > 0 else None
    return dict(effect=effect, ci_low=low, ci_high=high, writers=len(groups), observations=len(y),
                bootstrap_se=se, z=z, wald_p_two_sided=math.erfc(abs(z) / math.sqrt(2)) if z is not None else None,
                p_reference="approximate two-sided normal Wald test; descriptive; state remains percentile-CI based",
                state=states.contrast_state(effect, low, high, direction), expected_direction=direction,
                bootstrap_draws=draws, seed=seed, variance_ratio=variance_ratio,
                interval="writer-cluster percentile bootstrap, refit per resample")
