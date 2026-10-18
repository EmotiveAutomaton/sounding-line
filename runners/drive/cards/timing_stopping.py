"""D29: chronological odd/even reliability of final nonprompt word counts.

DESIGN CHECK (LESSONS 3-5, October 18): identical odd/even writer rankings
recover +1; reversed rankings recover -1; orthogonal rankings recover zero.
Whole writer pairs, never individual sessions, are bootstrap units. Tied
chronology and absent halves are disclosed. A shuffled even-half identity can
fail the signal. Fresh verification rebuilds every session from authenticated
P2 and foundation-pinned metadata. These are stopping associations, not proof
of internal targets. The timer extension has a separate, conditional handler.
"""
from __future__ import annotations

import hashlib
import math
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from runners.drive.cards import states_v2 as states
from runners.drive.cards.timing_census import read, write, filehash
from runners.drive.cards.timing_events import source_sessions, session_words, CooperativeYield
from runners.drive.cards.timing_stats import bind, check_binding
from runners.stage14.common import atomic, freeze

FORECAST_SECONDS = 600
CONFIG = dict(card="D29", extension=False, bootstrap_draws=2000, seed=20261017)
INPUTS = {"session_index", "foundation_complete", "foundation_plan", "repo_root", "prepared_sessions"}


def validate(config, inputs):
    if config != CONFIG or set(config) != set(CONFIG) or any(type(config[k]) is not type(v) for k, v in CONFIG.items()):
        raise ValueError("exact frozen D29 primary configuration required")
    if set(inputs) != INPUTS:
        raise ValueError("exact D29 source input set required")


def extract(inputs, output=None, elapsed=None):
    rows, total = [], len(read(inputs["session_index"]))
    for done, (index, timeline, metadata) in enumerate(source_sessions(inputs, "prepared_sessions"), 1):
        duration = timeline["duration_seconds"]
        if isinstance(duration, bool) or not math.isfinite(duration) or duration < 0:
            raise ValueError("invalid logged session duration")
        row = dict(session=index["session"], writer=index["writer"], timestamp=metadata["timestamp"],
                   words=session_words(timeline), duration_seconds=duration)
        if output is not None:
            checkpoint = output / "sessions" / (hashlib.sha256(index["session"].encode()).hexdigest() + ".json")
            # Tiny extraction is repeated to authenticate the saved unit itself;
            # source hashes alone would not detect forged checkpoint rows.
            freeze(checkpoint, dict(source_sha256=index["sha256"], row=row))
            active = elapsed()
            atomic(output / "STOPPING_PROGRESS.json", dict(completed_sessions=done, total_sessions=total, active_seconds=active))
            overshoot = False
            if done == math.ceil(total / 10) and not (output / "FIRST_TENTH.json").exists():
                projection = 2 * active * total / done + 30
                overshoot = projection > 2 * FORECAST_SECONDS
                write(output / "FIRST_TENTH.json", dict(completed_sessions=done, total_sessions=total, elapsed_seconds=active,
                      projected_cpu_seconds=projection, forecast_cpu_seconds=FORECAST_SECONDS,
                      forecast_overshoot=overshoot, includes_fresh_source_verification=True, reserved_statistics_seconds=30))
            if active > 3 * FORECAST_SECONDS:
                raise RuntimeError("D29 threefold active-time ceiling")
            if overshoot or (output / "YIELD_REQUEST.json").exists():
                if overshoot and not (output / "YIELD_REQUEST.json").exists():
                    atomic(output / "YIELD_REQUEST.json", dict(reason="first_tenth_projection_exceeds_twice_forecast"))
                raise CooperativeYield("saved authenticated session checkpoint")
        rows.append(row)
    return rows


def correlation(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    a, b = a - a.mean(axis=-1, keepdims=True), b - b.mean(axis=-1, keepdims=True)
    denominator = np.sqrt(np.sum(a * a, axis=-1) * np.sum(b * b, axis=-1))
    if np.any(denominator == 0):
        raise ValueError("constant split-half means in point or bootstrap sample")
    return np.sum(a * b, axis=-1) / denominator


def pair_inference(pairs, config):
    n = len(pairs)
    if n < 3:
        return dict(state="invalid", reason="fewer than three writers with both halves", writers=n)
    values = np.asarray([[p["odd_mean"], p["even_mean"]] for p in pairs])
    rng = np.random.default_rng(config["seed"])
    selected = rng.integers(0, n, (config["bootstrap_draws"], n))
    try:
        effect = float(correlation(values[:, 0], values[:, 1]))
        samples = correlation(values[selected, 0], values[selected, 1])
    except ValueError as exc:
        return dict(state="invalid", reason=str(exc), writers=n)
    low, high = np.quantile(samples, [.025, .975]).tolist()
    se = float(np.std(samples, ddof=1))
    z = effect / se if se > 0 else None
    return dict(effect=effect, ci_low=low, ci_high=high, bootstrap_se=se, z=z,
                wald_p_two_sided=math.erfc(abs(z) / math.sqrt(2)) if z is not None else None,
                p_reference="approximate two-sided normal Wald; descriptive; state remains percentile-CI based",
                state=states.contrast_state(effect, low, high), writers=n, expected_direction=1,
                bootstrap_draws=config["bootstrap_draws"], seed=config["seed"],
                interval="percentile bootstrap of complete writer odd/even pairs")


def summarize(rows, config):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["writer"]].append(row)
    pairs, exclusions = [], []
    for writer in sorted(grouped):
        sessions = sorted(grouped[writer], key=lambda r: (r["timestamp"], r["session"]))
        if len({r["timestamp"] for r in sessions}) != len(sessions):
            exclusions.append(dict(writer=writer, reason="tied session start times"))
        elif len(sessions) < 2:
            exclusions.append(dict(writer=writer, reason="fewer than two sessions"))
        else:
            odd, even = sessions[::2], sessions[1::2]
            pairs.append(dict(writer=writer, odd_mean=float(np.mean([r["words"] for r in odd])),
                              even_mean=float(np.mean([r["words"] for r in even])),
                              odd_sessions=[r["session"] for r in odd], even_sessions=[r["session"] for r in even]))
    result = pair_inference(pairs, config)
    rng = np.random.default_rng(config["seed"] + 1)
    permutation = rng.permutation(len(pairs))
    shuffled = [dict(row, even_mean=pairs[int(permutation[i])]["even_mean"]) for i, row in enumerate(pairs)]
    control = pair_inference(shuffled, config)
    if len(pairs) >= 3 and result["state"] != "invalid":
        a, b = [p["odd_mean"] for p in pairs], np.array([p["even_mean"] for p in pairs])
        permuted = [float(correlation(a, rng.permutation(b))) for _ in range(config["bootstrap_draws"])]
        result["permutation_p_two_sided"] = (1 + sum(abs(v) >= abs(result["effect"]) for v in permuted)) / (1 + len(permuted))
    result.update(card="D29", extension=False, descriptive=True,
                  contrast="Pearson correlation of writer mean final nonprompt words in odd versus even chronological sessions",
                  controls=dict(even_half_writer_identity_shuffle=control),
                  excluded_writers=len(exclusions), sessions=len(rows), zero_word_sessions=sum(r["words"] == 0 for r in rows),
                  duration_definition="P2 last logged event minus first logged event in seconds; not inferred finish-button time",
                  word_definition="final lexical words wholly outside prompt-origin text, including typed and accepted words",
                  route="Reliability describes stable stopping length; neither consistency nor timer bunching identifies internal targets.")
    # Frozen bins and residues are descriptive only; no outcome-selected peak search.
    detail = dict(writer_pairs=pairs, excluded_writers=exclusions,
                  word_bins_25={str(k): v for k, v in sorted(Counter(25 * (r["words"] // 25) for r in rows).items())},
                  duration_bins_30={str(k): v for k, v in sorted(Counter(30 * int(r["duration_seconds"] // 30) for r in rows).items())},
                  word_residues_50=[sum(r["words"] % 50 == j for r in rows) for j in range(50)],
                  word_residues_100=[sum(r["words"] % 100 == j for r in rows) for j in range(100)],
                  histogram_convention="left-closed right-open bins, all sessions; final-length round-number residues descriptive",
                  shuffled_even_writer_order=[pairs[int(i)]["writer"] for i in permutation])
    return result, detail


def execute(output: Path, inputs: dict, config: dict) -> dict:
    validate(config, inputs)
    output = Path(output)
    if (output / "TIMING_BINDINGS.json").exists():
        return verify(output, inputs, config)["primary"]
    freeze(output / "STOPPING_RUN_BINDINGS.json", dict(config=config, source_sha256=filehash(__file__),
           inputs={k: str(Path(v).resolve()) if Path(v).is_dir() else filehash(v) for k, v in inputs.items()}))
    prior = read(output / "STOPPING_PROGRESS.json")["active_seconds"] if (output / "STOPPING_PROGRESS.json").exists() else 0.
    started = time.monotonic()
    elapsed = lambda: prior + time.monotonic() - started
    try:
        rows = extract(inputs, output, elapsed)
    except CooperativeYield as exc:
        return dict(status="yielded", card="D29", reason=str(exc))
    result, details = summarize(rows, config)
    if elapsed() > 3 * FORECAST_SECONDS:
        raise RuntimeError("D29 threefold active-time ceiling")
    freeze(output / "STOPPING_ROWS.json", rows)
    freeze(output / "STOPPING_DETAILS.json", details)
    freeze(output / "STOPPING_PRIMARY.json", result)
    freeze(output / "STOPPING_TIMING.json", dict(wall_seconds=elapsed(), forecast_cpu_seconds=FORECAST_SECONDS))
    bind(output, inputs, config, ["STOPPING_ROWS.json", "STOPPING_DETAILS.json", "STOPPING_PRIMARY.json"])
    return result


def verify(output: Path, inputs: dict, config: dict) -> dict:
    validate(config, inputs)
    check_binding(output, inputs, config)
    rows = extract(inputs)
    if rows != read(Path(output) / "STOPPING_ROWS.json"):
        raise ValueError("stopping rows do not reconstruct from authenticated sources")
    result, details = summarize(rows, config)
    if result != read(Path(output) / "STOPPING_PRIMARY.json") or details != read(Path(output) / "STOPPING_DETAILS.json"):
        raise ValueError("stopping primary does not recompute")
    return dict(verified=True, primary=result)
