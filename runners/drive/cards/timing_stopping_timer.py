"""Conditional D29 timer-bunching extension, separate from frozen reliability.

DESIGN CHECK: fixed 30-second bins; estimate excess mass in [600,660) against
a linear right-side counterfactual fitted in [660,900). The unavailable pre-
timer finish option is not treated as a symmetric control. Positive/null/reverse
planted histograms identify sign. Whole writers are bootstrapped; a negative
predicted bin mass in the point or any fixed bootstrap draw invalidates the
reading rather than being clipped. The smooth extrapolation assumption cannot
identify a personal/internal target. Original log duration is retained.
"""
from __future__ import annotations

import math
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

from runners.drive.cards import states_v2 as states
from runners.drive.cards import timing_stopping as primary
from runners.drive.cards.timing_census import read, write, filehash
from runners.drive.cards.timing_events import CooperativeYield
from runners.drive.cards.timing_stats import bind, check_binding
from runners.stage14.common import atomic, freeze

CONFIG = dict(card="D29", extension=True, bootstrap_draws=2000, seed=20261017)


def authorize(inputs, config):
    if config != CONFIG or set(config) != set(CONFIG) or any(type(config[k]) is not type(v) for k, v in CONFIG.items()):
        raise ValueError("exact frozen D29 timer configuration required")
    if set(inputs) != primary.INPUTS | {"primary_complete"}:
        raise ValueError("exact D29 timer input set required")
    source = {k: inputs[k] for k in primary.INPUTS}
    complete_path = Path(inputs["primary_complete"])
    complete = read(complete_path)
    output = complete_path.parent / "output"
    if complete.get("status") != "COMPLETE" or complete.get("fresh_process_verified") is not True:
        raise ValueError("completed fresh-verified primary required")
    for name in ("STOPPING_ROWS.json", "STOPPING_DETAILS.json", "STOPPING_PRIMARY.json", "TIMING_BINDINGS.json"):
        if complete["outputs"].get("output/" + name) != filehash(output / name):
            raise ValueError("primary completion does not authenticate outputs")
    result = primary.verify(output, source, primary.CONFIG)["primary"]
    if result["state"] not in {"positive", "marginal"}:
        raise ValueError("D29 primary does not permit conditional extension")
    return source


def histogram_rows(rows, cutoff=600):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["writer"]].append(row)
    records = []
    for writer in sorted(grouped):
        sessions = grouped[writer]
        counts = np.zeros(10, dtype=np.int64)
        for row in sessions:
            position = int((row["duration_seconds"] - cutoff) // 30)
            if 0 <= position < 10:
                counts[position] += 1
        records.append(dict(writer=writer, sessions=len(sessions), counts=counts.tolist()))
    return records


def infer(records, config):
    n = len(records)
    if n < 3:
        return dict(state="invalid", reason="fewer than three writers", writers=n)
    counts = np.array([r["counts"] for r in records], dtype=np.int64)
    totals = np.array([r["sessions"] for r in records], dtype=float)
    if np.sum(counts[:, 2:]) == 0:
        return dict(state="invalid", reason="no right-side counterfactual support", writers=n)
    # Integer linear-regression coefficients give exact zero on flat counts.
    # x=2,...,9 are baseline bins; extrapolate the means at x=0 and x=1.
    x = np.arange(2, 10)
    first = (counts[:, 2:] @ (71 - 11 * x)) / (84 * totals)
    second = (counts[:, 2:] @ (60 - 9 * x)) / (84 * totals)
    observed = counts[:, :2].sum(1) / totals
    differences = (84 * counts[:, :2].sum(1) - counts[:, 2:] @ (131 - 20 * x)) / (84 * totals)
    rng = np.random.default_rng(config["seed"])
    selected = rng.integers(0, n, (config["bootstrap_draws"], n))
    baseline = np.array([first.mean(), second.mean()])
    sampled_baseline = np.stack([first[selected].mean(1), second[selected].mean(1)], axis=1)
    if not np.isfinite(baseline).all() or np.any(baseline < 0) or not np.isfinite(sampled_baseline).all() or np.any(sampled_baseline < 0):
        return dict(state="invalid", reason="negative or undefined extrapolated counterfactual bin mass", writers=n,
                    predicted_first_two_bin_masses=baseline.tolist())
    samples = differences[selected].mean(1)
    effect = float(differences.mean())
    low, high = np.quantile(samples, [.025, .975]).tolist()
    se = float(np.std(samples, ddof=1))
    z = effect / se if se > 0 else None
    return dict(effect=effect, ci_low=low, ci_high=high, bootstrap_se=se, z=z,
                wald_p_two_sided=math.erfc(abs(z) / math.sqrt(2)) if z is not None else None,
                p_reference="approximate two-sided normal Wald; descriptive; state remains percentile-CI based",
                state=states.contrast_state(effect, low, high), writers=n, expected_direction=1,
                observed_first_two_bin_mass=float(observed.mean()), predicted_first_two_bin_masses=baseline.tolist(),
                bootstrap_draws=config["bootstrap_draws"], seed=config["seed"],
                interval="whole-writer percentile bootstrap; linear right-side baseline refit by equivalent sufficient statistics")


def summarize(rows, config):
    records = histogram_rows(rows)
    result = infer(records, config)
    # One fixed outcome-bin shuffle retains each writer's observed window mass.
    rng = np.random.default_rng(config["seed"] + 1)
    shuffled = [dict(r, counts=rng.permutation(r["counts"]).tolist()) for r in records]
    result.update(card="D29", extension=True, descriptive=True,
                  contrast="equal-writer excess duration mass in [600,660) over a linear right-side baseline from [660,900)",
                  controls=dict(within_writer_duration_bin_shuffle=infer(shuffled, config)),
                  duration_definition="P2 last logged event minus first logged event; not inferred finish-button time",
                  assumption="The 660-900 second density extrapolates linearly to 600-660 seconds absent timer bunching; no internal-target identification",
                  weighting="Each writer equal; each bin count divided by all that writer's sessions, including sessions outside the displayed window")
    return result, dict(writer_histograms=records, cutoff_seconds=600, bin_width_seconds=30,
                        target_bins=[600, 630], fit_bins=list(range(660, 900, 30)),
                        shifted_cutoff_780_diagnostic=infer(histogram_rows(rows, 780), config))


def execute(output: Path, inputs: dict, config: dict) -> dict:
    output = Path(output)
    started = time.monotonic()
    source = authorize(inputs, config)
    if (output / "TIMING_BINDINGS.json").exists():
        return verify(output, inputs, config)["primary"]
    freeze(output / "TIMER_RUN_BINDINGS.json", dict(config=config, source_sha256=filehash(__file__),
           inputs={k: str(Path(v).resolve()) if Path(v).is_dir() else filehash(v) for k, v in inputs.items()}))
    prior = read(output / "STOPPING_PROGRESS.json")["active_seconds"] if (output / "STOPPING_PROGRESS.json").exists() else 0.
    elapsed = lambda: prior + time.monotonic() - started
    try:
        rows = primary.extract(source, output, elapsed)
    except CooperativeYield as exc:
        return dict(status="yielded", card="D29", reason=str(exc))
    result, details = summarize(rows, config)
    if elapsed() > 3 * primary.FORECAST_SECONDS:
        raise RuntimeError("D29 timer threefold active-time ceiling")
    freeze(output / "TIMER_ROWS.json", rows)
    freeze(output / "TIMER_DETAILS.json", details)
    freeze(output / "TIMER_PRIMARY.json", result)
    freeze(output / "TIMER_TIMING.json", dict(wall_seconds=elapsed(), forecast_cpu_seconds=primary.FORECAST_SECONDS))
    bind(output, inputs, config, ["TIMER_ROWS.json", "TIMER_DETAILS.json", "TIMER_PRIMARY.json"])
    return result


def verify(output: Path, inputs: dict, config: dict) -> dict:
    source = authorize(inputs, config)
    check_binding(output, inputs, config)
    rows = primary.extract(source)
    if rows != read(Path(output) / "TIMER_ROWS.json"):
        raise ValueError("timer rows do not reconstruct from authenticated sources")
    result, details = summarize(rows, config)
    if result != read(Path(output) / "TIMER_PRIMARY.json") or details != read(Path(output) / "TIMER_DETAILS.json"):
        raise ValueError("timer primary does not recompute")
    return dict(verified=True, primary=result)
