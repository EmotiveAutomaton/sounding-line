"""Packet 20261017 section 3.5: D30's within-writer outcome-shuffle control.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-4 reread 2026-10-17.
NULL: permuting eligible log pauses within writer removes their alignment with
fixed labels/covariates; the signed contrast is centered at zero. ALTERNATIVE:
a positive shuffled contrast flags the day's screen; reverse, marginal and null
remain distinct, and an invalid fit leaves coverage incomplete. This raw outcome
shuffle also breaks nuisance associations; it is not a conditional causal test.
No original source/result is changed. The original primary, not its extension,
defines eligibility, order, covariates, direction and the 2000 writer draws.
One fixed permutation is used; no seed search or resampling until a pass.
"""
from __future__ import annotations

import math
import time
from pathlib import Path

import numpy as np

from . import timing_d30 as original
from .timing_census import read, write, filehash
from .timing_p6 import gzread, gzip_equal, write_equal
from .timing_stats import bind, check_binding, sufficient, fit
from .timing_checkpoint import regression

CONFIG = dict(card="D30-outcome-shuffle", bootstrap_draws=2000, seed=20261017,
              permutation_seed=20261017)
ORIGINAL_CONFIG = dict(card="D30", bootstrap_draws=2000, seed=20261017, extension=False)


def design(rows, mode):
    """Exact original primary's eligibility and design; no result-dependent cuts."""
    if mode not in {"per_character", "per_word", "invalid"}:
        raise ValueError("unknown original timing mode")
    revision = mode == "invalid"
    labels, markers = original.classify_markers(rows)
    eligible = []
    for row in rows:
        label = labels.get((row["writer"], row["marker"]))
        if label is None:
            continue
        if not revision and (row["pause_seconds"] is None or row["pause_seconds"] <= 0
                             or row["population_surprisal"] is None):
            continue
        if not revision and mode == "per_character" and row["first_delta_characters"] != 1:
            continue
        eligible.append(dict(row, **label))
    classes = {}
    for row in eligible:
        classes.setdefault(row["writer"], set()).add(row["label"])
    supported = {w for w, values in classes.items() if values == {"local", "pervasive"}}
    eligible = [r for r in eligible if r["writer"] in supported]
    if len(supported) < 3:
        raise ValueError("fewer than three supported writers")
    x, y, writers = [], [], []
    for row in eligible:
        nuisance = [] if revision else [row["length"], row["population_log_frequency"],
            int(row["sentence_start"]), int(row["after_punctuation"]), row["population_surprisal"]]
        x.append([int(row["label"] == ("pervasive" if revision else "local"))] + nuisance)
        y.append(float(row["revised"]) if revision else math.log(row["pause_seconds"]))
        writers.append(row["writer"])
    return dict(x=x, y=y, writers=writers, direction=-1 if revision else 1), markers


def permutation(writers, seed):
    rng = np.random.default_rng(seed)
    owners = np.asarray(writers)
    indices = np.arange(len(writers))
    for writer in sorted(set(writers)):
        positions = np.flatnonzero(owners == writer)
        indices[positions] = rng.permutation(positions)
    return indices.tolist()


def source(inputs, config):
    if config != CONFIG or set(inputs) != {"source_completion"}:
        raise ValueError("control configuration differs from frozen contract")
    terminal = Path(inputs["source_completion"])
    complete = read(terminal)
    if complete.get("status") != "COMPLETE" or not complete.get("fresh_process_verified"):
        raise ValueError("original D30 is not verified complete")
    names = ["PLAN.json", "output/D30_INTERMEDIATES.json.gz", "output/D30_PRIMARY.json", "output/D30_MARKERS.json"]
    for name in names:
        if complete["outputs"].get(name) != filehash(terminal.parent / name):
            raise ValueError("original completion binding changed: " + name)
    plan = read(terminal.parent / "PLAN.json")
    if plan["config"] != ORIGINAL_CONFIG or plan["module"] != "runners.drive.cards.timing_d30":
        raise ValueError("source must be the frozen original D30 primary")
    for name, expected in plan["pins"].items():
        if filehash(name) != expected:
            raise ValueError("original source pin changed")
    saved = gzread(terminal.parent / names[1])
    if saved["config"] != ORIGINAL_CONFIG:
        raise ValueError("original intermediate configuration changed")
    matrix, markers = design(saved["rows"], saved["timing_mode"])
    if markers != read(terminal.parent / names[3]):
        raise ValueError("original marker reconstruction differs")
    baseline = read(terminal.parent / names[2])
    effect, _ = fit(sufficient(matrix["x"], matrix["y"], matrix["writers"], within=True))
    if (not math.isclose(effect, baseline["effect"], rel_tol=1e-12, abs_tol=1e-12)
        or baseline["observations"] != len(matrix["y"])
        or baseline["writers"] != len(set(matrix["writers"]))
        or baseline["expected_direction"] != matrix["direction"]):
        raise ValueError("unchanged primary parity failed")
    indices = permutation(matrix["writers"], config["permutation_seed"])
    matrix.update(permutation=indices, shuffled_y=[matrix["y"][i] for i in indices],
                  original_effect=effect, timing_mode=saved["timing_mode"])
    return matrix


def compute(matrix, config, checkpoint=None, on_tenth=None):
    result = regression(matrix["x"], matrix["shuffled_y"], matrix["writers"], within=True,
        draws=config["bootstrap_draws"], seed=config["seed"], direction=matrix["direction"],
        checkpoint=checkpoint, on_tenth=on_tenth,
        yield_requested=(lambda: (Path(checkpoint).parent / "YIELD_REQUEST.json").exists()) if checkpoint else None)
    if result.get("status") == "yielded":
        return result
    result.update(card=config["card"], descriptive=True, scientific_admission=False,
                  control="outcomes shuffled within writer, fixed eligible occurrence order",
                  permutation_seed=config["permutation_seed"], source_card="D30 original primary",
                  timing_mode=matrix["timing_mode"], daily_screen_failure_flag=result["state"] == "positive",
                  coverage_complete=result["state"] != "invalid")
    return result


def execute(output, inputs, config):
    output = Path(output)
    started = time.monotonic()
    matrix = source(inputs, config)
    write_equal(output / "RUN_BINDINGS.json", dict(config=config, source_sha256=filehash(inputs["source_completion"])))
    if (output / "PRIMARY.json").exists():
        return verify(output, inputs, config)["primary"]
    gzip_equal(output / "INTERMEDIATES.json.gz", matrix)
    def tenth(receipt):
        if not (output / "FIRST_TENTH.json").exists():
            elapsed = time.monotonic() - started
            write(output / "FIRST_TENTH.json", dict(**receipt, active_seconds=elapsed,
                projected_cpu_seconds=elapsed + receipt["primary_seconds"] * 19,
                forecast_cpu_seconds=3600, method="preparation plus 20 tenths for execution and fresh replay"))
    result = compute(matrix, config, output / "outcome_shuffle", tenth)
    if result.get("status") == "yielded":
        return result
    write_equal(output / "PRIMARY.json", result)
    bind(output, inputs, config, ["INTERMEDIATES.json.gz", "PRIMARY.json"])
    return result


def verify(output, inputs, config):
    output = Path(output)
    check_binding(output, inputs, config)
    matrix = source(inputs, config)
    if matrix != gzread(output / "INTERMEDIATES.json.gz"):
        raise ValueError("saved control design or permutation changed")
    result = compute(matrix, config)
    if result != read(output / "PRIMARY.json"):
        raise ValueError("control fresh replay differs")
    return dict(verified=True, primary=result)
