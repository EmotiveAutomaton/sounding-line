"""D30.p crossed writer/marker REML estimator and counted feasibility pilot.

DESIGN CHECK: every occurrence is retained; globally equal marker strings share
one random intercept across writers. Writer-bootstrap copies have independent
writer intercepts and shared marker intercepts. Sparse Woodbury evaluation is
checked against direct dense covariance on known data, not approximated by
writer demeaning. Fixed effects include the registered own-marker count.
This handler measures cost and numerical feasibility only; no scientific main
or inferential state is admitted by its five pilot bootstrap fits.
"""
from __future__ import annotations

import math
import time
from pathlib import Path

import numpy as np
from scipy import sparse
from scipy.optimize import minimize
from scipy.sparse.linalg import splu

from runners.drive.cards import timing_d30_specification as specification
from runners.drive.cards import timing_d30 as original
from runners.drive.cards.timing_census import read, filehash
from runners.drive.cards.timing_p6 import gzread
from runners.drive.cards.timing_stats import bind, check_binding
from runners.stage14.common import atomic, freeze

CONFIG = dict(card="D30.p-pilot", bootstrap_pilot_draws=5, seed=20261017)
FORECAST_SECONDS = 600
MAX_RATIO = 1e6


def source(inputs, config):
    if config != CONFIG or set(config) != set(CONFIG) or any(type(config[k]) is not type(v) for k, v in CONFIG.items()):
        raise ValueError("exact crossed-pilot configuration required")
    matrix = specification.source(inputs, specification.CONFIG)
    saved = gzread(Path(inputs["extension_completion"]).parent / "output/D30_INTERMEDIATES.json.gz")
    labels, _ = original.classify_markers(saved["rows"])
    supported = set(matrix["writers"])
    marker_ids = []
    for row in saved["rows"]:
        if row["writer"] not in supported or (row["writer"], row["marker"]) not in labels:
            continue
        if row["pause_seconds"] is None or row["pause_seconds"] <= 0 or row["population_surprisal"] is None:
            continue
        if matrix["timing_mode"] == "per_character" and row["first_delta_characters"] != 1:
            continue
        marker_ids.append(row["marker"])
    if len(marker_ids) != len(matrix["y"]):
        raise ValueError("crossed marker identity order differs from original rows")
    return dict(x=matrix["designs"][1], y=matrix["y"], writers=matrix["writers"], markers=marker_ids)


def prepare(x, y, writers, markers):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if x.ndim != 2 or len(x) != len(y) or len(y) != len(writers) or len(y) != len(markers) or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("invalid crossed-model observations")
    scale = x.std(0)
    keep = np.flatnonzero(scale > 1e-12)
    if 0 not in keep:
        raise ValueError("crossed target has no variation")
    a = np.column_stack([x[:, keep] / scale[keep], np.ones(len(x))])
    if np.linalg.matrix_rank(a) != a.shape[1] or len(a) <= a.shape[1]:
        raise ValueError("crossed fixed effects are not identifiable")
    writer_levels, marker_levels = sorted(set(writers)), sorted(set(markers))
    if len(writer_levels) < 3 or len(marker_levels) < 3:
        raise ValueError("crossed model needs at least three writers and markers")
    wi, mi = {v: j for j, v in enumerate(writer_levels)}, {v: j for j, v in enumerate(marker_levels)}
    n, nw = len(y), len(writer_levels)
    z = sparse.coo_matrix((np.ones(2*n), (np.repeat(np.arange(n), 2),
                          np.column_stack([[wi[w] for w in writers], [nw+mi[m] for m in markers]]).ravel())),
                         shape=(n, nw+len(marker_levels))).tocsc()
    h = np.column_stack([a, y])
    return dict(n=n, p=a.shape[1], writer_levels=nw, marker_levels=len(marker_levels),
                ztz=(z.T @ z).tocsc(), zth=np.asarray(z.T @ h), hth=h.T @ h,
                target_scale=float(scale[0]), kept_columns=keep.tolist())


def evaluate(prepared, ratios):
    ratios = np.asarray(ratios, float)
    if ratios.shape != (2,) or not np.isfinite(ratios).all() or np.any(ratios < 0):
        raise ValueError("invalid crossed variance ratios")
    nw, nm = prepared["writer_levels"], prepared["marker_levels"]
    diagonal = np.sqrt(np.r_[np.repeat(ratios[0], nw), np.repeat(ratios[1], nm)])
    d = sparse.diags(diagonal, format="csc")
    system = sparse.eye(nw+nm, format="csc") + d @ prepared["ztz"] @ d
    factor = splu(system)
    u = diagonal[:, None] * prepared["zth"]
    cross = prepared["hth"] - u.T @ factor.solve(u)
    a, b, yy = cross[:-1, :-1], cross[:-1, -1], cross[-1, -1]
    sign, fixed_logdet = np.linalg.slogdet(a)
    if sign <= 0 or not np.isfinite(cross).all():
        raise ValueError("undefined crossed GLS system")
    beta = np.linalg.solve(a, b)
    rss = float(yy - b @ beta)
    df = prepared["n"] - prepared["p"]
    if not math.isfinite(rss) or rss <= 0:
        raise ValueError("undefined crossed residual variance")
    covariance_logdet = float(np.log(np.abs(factor.U.diagonal())).sum())
    objective = covariance_logdet + fixed_logdet + df * math.log(rss / df)
    return dict(objective=float(objective), effect=float(beta[0] / prepared["target_scale"]),
                residual_variance=rss/df, writer_variance_ratio=float(ratios[0]), marker_variance_ratio=float(ratios[1]))


def fit(x, y, writers, markers):
    prepared = prepare(x, y, writers, markers)
    def objective(theta):
        return evaluate(prepared, np.expm1(theta))["objective"]
    result = minimize(objective, np.log1p([.1, .1]), method="L-BFGS-B",
                      bounds=[(0., math.log1p(MAX_RATIO))] * 2,
                      options=dict(maxiter=200, ftol=1e-10, gtol=1e-6))
    ratios = np.expm1(result.x)
    if not result.success or not np.isfinite(result.fun) or np.any(ratios >= MAX_RATIO * .999):
        raise ValueError("crossed REML failed convergence or hit the variance ceiling: " + str(result.message))
    answer = evaluate(prepared, ratios)
    answer.update(converged=True, iterations=int(result.nit), objective_evaluations=int(result.nfev),
                  observations=prepared["n"], writers=prepared["writer_levels"], markers=prepared["marker_levels"],
                  kept_columns=prepared["kept_columns"], estimator="crossed random-intercept Gaussian REML, sparse exact Woodbury")
    return answer


def resample(matrix, selected):
    writers = sorted(set(matrix["writers"]))
    groups = {w: np.flatnonzero(np.array(matrix["writers"]) == w) for w in writers}
    indices, copy_ids = [], []
    for copy, selection in enumerate(selected):
        rows = groups[writers[int(selection)]]
        indices.extend(rows.tolist())
        copy_ids.extend([f"copy-{copy}"] * len(rows))
    return dict(x=[matrix["x"][i] for i in indices], y=[matrix["y"][i] for i in indices], writers=copy_ids,
                markers=[matrix["markers"][i] for i in indices])


def pilot(matrix, config, output=None, elapsed=None):
    fits, times = [], []
    rng = np.random.default_rng(config["seed"])
    n = len(set(matrix["writers"]))
    for index in range(config["bootstrap_pilot_draws"] + 1):
        candidate = matrix if index == 0 else resample(matrix, rng.integers(0, n, n))
        unit = Path(output) / "fits" / f"fit-{index:02d}.json" if output else None
        started = time.monotonic()
        if unit is not None and unit.exists():
            saved = read(unit)
            if read(unit.with_suffix(".receipt.json"))["sha256"] != filehash(unit):
                raise ValueError("crossed pilot checkpoint changed")
            value, seconds = saved["fit"], saved["seconds"]
        else:
            value = fit(**candidate)
            seconds = time.monotonic() - started
            if unit is not None:
                freeze(unit, dict(fit=value, seconds=seconds))
                freeze(unit.with_suffix(".receipt.json"), dict(sha256=filehash(unit)))
        fits.append(value)
        times.append(seconds)
        if output:
            atomic(Path(output) / "CROSSED_PROGRESS.json", dict(completed_fits=index+1, total_fits=config["bootstrap_pilot_draws"]+1, active_seconds=elapsed()))
            if index == 0 and not (Path(output) / "FIRST_TENTH.json").exists():
                projection = elapsed() * (config["bootstrap_pilot_draws"]+1) * 2
                freeze(Path(output) / "FIRST_TENTH.json", dict(completed_fits=1, total_fits=6, elapsed_seconds=elapsed(), projected_cpu_seconds=projection,
                       forecast_cpu_seconds=FORECAST_SECONDS, boundary="first complete fit, earliest safe checkpoint at16.7%"))
                if projection > 2 * FORECAST_SECONDS:
                    atomic(Path(output) / "YIELD_REQUEST.json", dict(reason="first_tenth_projection_exceeds_twice_forecast"))
            if elapsed() > 3 * FORECAST_SECONDS:
                raise RuntimeError("crossed pilot threefold time ceiling")
            if (Path(output) / "YIELD_REQUEST.json").exists():
                return dict(status="yielded", card="D30.p-pilot", reason="saved complete fit")
    return dict(state="positive", instrument_only=True, scientific_main_admitted=False,
                observations=fits[0]["observations"], writers=fits[0]["writers"], markers=fits[0]["markers"],
                fits=fits, fit_seconds=times,
                projected_2000_draw_execute_and_replay_seconds=2 * 2001 * max(times),
                projection_basis="twice measured source reconstruction plus twice2001 times slowest measured complete fit",
                limitation="Five pilot bootstrap fits measure cost/convergence, not uncertainty or scientific effect")


def execute(output: Path, inputs: dict, config: dict) -> dict:
    output = Path(output)
    if (output / "TIMING_BINDINGS.json").exists():
        return verify(output, inputs, config)["primary"]
    freeze(output / "CROSSED_RUN_BINDINGS.json", dict(config=config, source_sha256=filehash(__file__), inputs={k: filehash(v) for k, v in inputs.items()}))
    prior = read(output / "CROSSED_PROGRESS.json")["active_seconds"] if (output / "CROSSED_PROGRESS.json").exists() else 0.
    started = time.monotonic()
    elapsed = lambda: prior + time.monotonic() - started
    matrix = source(inputs, config)
    source_seconds = time.monotonic() - started
    result = pilot(matrix, config, output, elapsed)
    if result.get("status") == "yielded":
        return result
    result["source_seconds"] = source_seconds
    result["projected_2000_draw_execute_and_replay_seconds"] += 2 * source_seconds
    freeze(output / "CROSSED_DESIGN.json", matrix)
    freeze(output / "CROSSED_PRIMARY.json", result)
    freeze(output / "CROSSED_TIMING.json", dict(wall_seconds=elapsed(), forecast_cpu_seconds=FORECAST_SECONDS))
    bind(output, inputs, config, ["CROSSED_DESIGN.json", "CROSSED_PRIMARY.json"])
    return result


def verify(output: Path, inputs: dict, config: dict) -> dict:
    check_binding(output, inputs, config)
    matrix = source(inputs, config)
    if matrix != read(Path(output) / "CROSSED_DESIGN.json"):
        raise ValueError("crossed design does not reconstruct from frozen originals")
    saved = read(Path(output) / "CROSSED_PRIMARY.json")
    rebuilt = pilot(matrix, config)
    # Wall times are observations, not deterministically replayable quantities.
    for key in rebuilt:
        if key not in {"fit_seconds", "projected_2000_draw_execute_and_replay_seconds"} and rebuilt[key] != saved[key]:
            raise ValueError("crossed pilot fits do not recompute")
    if not all(math.isfinite(t) and t > 0 for t in saved["fit_seconds"]) or not math.isfinite(saved["source_seconds"]) or saved["source_seconds"] < 0 or saved["projected_2000_draw_execute_and_replay_seconds"] != 2 * 2001 * max(saved["fit_seconds"]) + 2 * saved["source_seconds"]:
        raise ValueError("crossed pilot timing projection differs")
    return dict(verified=True, primary=saved)
