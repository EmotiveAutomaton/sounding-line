"""DR1 timing admission only; preserve the full gallery and original functions.

DESIGN CHECK (2026-10-22): LESSONS sections 3-5.
NULL/ALTERNATIVE: scientific outcomes cannot change timing selection or admission.
Every eligible writer runs the three fixed orders and random replicates 0-4.
Full-run counts stay 200 random orders and 2000 draws. Changed sources, missing
work or changed replay refuse. Timing is a conservative forecast, not a proof;
the native full-run cap remains binding. No pilot contrast is reported.
"""
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import time

import numpy as np

from . import week_directed_reading as base
from .menus_io import read, sha256, write

CONFIG = dict(card="DR1-timing", schema_version=1, random_replicates=5,
              forecast_margin=2, full_config=base.CONFIG)


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf8")


def prepare(rows, dictionary):
    if len({r["session"] for r in rows}) != len(rows):
        raise ValueError("Duplicate session identity")
    groups = defaultdict(list)
    for row in rows:
        groups[row["writer"]].append(row)
    eligible = {w: sorted(own, key=lambda r: r["session"]) for w, own in sorted(groups.items())
                if len(own) >= 12 and len({r["prompt"] for r in own}) >= 3}
    references = {w: base.profile(own, dictionary) for w, own in eligible.items()}
    supported = [w for w in eligible if np.isfinite(np.asarray(references[w]["style"], float)).any()]
    if len(supported) < 2:
        raise ValueError("Timing pilot lacks full style-supported gallery")
    galleries = {c: base.gallery_model([references[w][c] for w in supported]) for c in base.CHANNELS}
    return eligible, references, supported, galleries


def benchmark(rows, dictionary):
    start = time.perf_counter()
    eligible, references, supported, galleries = prepare(rows, dictionary)
    work, timings = [], []
    for wi, writer in enumerate(supported):
        own = eligible[writer]
        metadata = [dict(session=r["session"], writer=r["writer"], prompt=r["prompt"],
                         timestamp=r["timestamp"], typed_words=sum(r["word_counts"].values())) for r in own]
        ref = {c: np.asarray(references[writer][c], float) for c in base.CHANNELS}
        single = [base.profile([r], dictionary) for r in own]
        deviations = {}
        for channel in base.CHANNELS:
            matrix = np.asarray([p[channel] for p in single], float)
            counts = np.isfinite(matrix).sum(axis=0)
            mean = np.divide(np.nansum(matrix, axis=0), counts, out=np.zeros(matrix.shape[1]), where=counts > 0)
            centered = np.where(np.isfinite(matrix), matrix-mean, 0)
            variance = np.divide(np.sum(centered**2, axis=0), counts-1,
                                 out=np.full(matrix.shape[1], np.nan), where=counts > 1)
            deviations[channel] = np.sqrt(variance)
        policies = [(p, 0) for p in ("chronological", "directed", "directed_random20")]
        policies += [("random", i) for i in range(CONFIG["random_replicates"])]
        for policy, replicate in policies:
            tick = time.perf_counter()
            order = base.make_order(metadata, policy, base.CONFIG["seed"]+wi*1000+replicate)
            recovery = base.evaluate_order(own, dictionary, order, ref, deviations, galleries, wi)
            blob = encoded(dict(writer=writer, replicate=replicate, **order, recovery=recovery))
            work.append(dict(writer=writer, sessions=len(own), policy=policy, replicate=replicate,
                             output_sha256=hashlib.sha256(blob).hexdigest(), serialized_bytes=len(blob)))
            timings.append(time.perf_counter()-tick)
    return dict(writers=supported, gallery_size=len(supported), source_sessions=len(rows),
                eligible_sessions=sum(len(eligible[w]) for w in supported), units=work), dict(
                unit_seconds=timings, benchmark_seconds=time.perf_counter()-start)


def forecast(work, measurements):
    units = work["units"]
    if len(measurements) != 2:
        raise ValueError("Both execution and fresh replay timings required")
    grouped = defaultdict(list)
    for i, unit in enumerate(units):
        grouped[unit["writer"]].append((i, unit))
    full_seconds, full_bytes = 0., 0
    for writer in work["writers"]:
        own = grouped[writer]
        if {(r["policy"], r["replicate"]) for _, r in own} != {
                (p, 0) for p in ("chronological", "directed", "directed_random20")} | {
                ("random", i) for i in range(5)} or len(own) != 8:
            raise ValueError("Incomplete or duplicate timing work")
        durations = [(r, max(m["unit_seconds"][i] for m in measurements)) for i, r in own]
        if any(not math.isfinite(t) or t <= 0 for _, t in durations):
            raise ValueError("Invalid timing measurement")
        full_seconds += sum(t for r, t in durations if r["policy"] != "random")
        full_seconds += 200 * max(t for r, t in durations if r["policy"] == "random")
        full_bytes += sum(r["serialized_bytes"] for _, r in own if r["policy"] != "random")
        full_bytes += 200 * max(r["serialized_bytes"] for _, r in own if r["policy"] == "random")
    overhead = max(m["elapsed_seconds"]-sum(m["unit_seconds"]) for m in measurements)
    # Two complete passes, 2x measured-work margin, plus fixed startup/bootstrap allowance.
    return dict(combined_wall_seconds=4*(full_seconds+max(0., overhead))+30,
                maximum_uncompressed_ledger_bytes=2*full_bytes,
                full_random_orders=200, full_writer_draws=2000,
                full_gallery_size=work["gallery_size"], scientific_admission=False,
                outcome_used_for_admission=False)


def run(output, inputs, config, verify=False):
    if config != CONFIG:
        raise ValueError("Frozen DR1 timing configuration differs")
    start = time.perf_counter()
    rows, dictionary = base.load(inputs)
    work, timing = benchmark(rows, dictionary)
    timing["elapsed_seconds"] = time.perf_counter()-start
    binding = dict(config=config, inputs={k: sha256(v) for k, v in inputs.items()})
    output = Path(output)
    if verify:
        if read(output/"BINDINGS.json") != binding or read(output/"WORK.json") != work:
            raise ValueError("DR1 timing fresh reconstruction differs")
        if (output/"VERIFY_TIMING.json").exists():
            raise ValueError("Timing replay already recorded; retain original measurements")
        write(output/"VERIFY_TIMING.json", timing)
        write(output/"FORECAST.json", forecast(work, [read(output/"EXECUTE_TIMING.json"), timing]))
        return dict(verified=True, full_gallery_replayed=True, no_scientific_contrast=True)
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise ValueError("Timing attempt already exists")
    for name, value in (("BINDINGS.json", binding), ("WORK.json", work), ("EXECUTE_TIMING.json", timing)):
        write(output/name, value)
    return dict(status="complete", scientific_admission=False, no_scientific_contrast=True)


def execute(output, inputs, config):
    return run(output, inputs, config)


def verify(output, inputs, config):
    return run(output, inputs, config, verify=True)
