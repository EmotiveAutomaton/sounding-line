"""Exact DR1 style-prefix parity and control-work timing, without control outcomes.

DESIGN CHECK (2026-10-22): LESSONS sections 3-5 and CONTROLS sections 1-7.
NULL/ALTERNATIVE: this optimization must preserve every identification flag,
tie, absent-prefix refusal and censored endpoint in both helpful and harmful
worlds. Any mismatch refuses readiness. It does not repair absent controls.
The original full comparator, gallery, denominator and tolerance are unchanged.
Runtime projections are provisional; future controls still require validation.
"""
from collections import defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from . import week_directed_reading as base
from .events_d4_sources import bind_completed
from .menus_io import read, sha256, write

CONFIG = dict(card="DR1-style-parity", schema_version=1,
              full_config=base.CONFIG, forecast_control_copies=201, margin=2)


def style_prefixes(rows, dictionary, indices):
    """Integer cumulative counts preserve the original pooled denominator."""
    counts, totals = [], []
    for row in rows:
        maps = (row["word_counts"], row["punctuation_counts"])
        values = [value for mapping in maps for value in mapping.values()]
        if any(type(v) is not int or v < 0 for v in values):
            raise ValueError("Style counts must be nonnegative integers")
        counts.append([maps[0].get(k, 0) for k in dictionary["words"]]
                      + [maps[1].get(k, 0) for k in dictionary["punctuation"]])
        totals.append(sum(values))
    if sum(totals) > 2**53:
        raise ValueError("Counts exceed exact integer arithmetic range")
    if len(indices) != len(rows) or sorted(indices) != list(range(len(rows))):
        raise ValueError("Order is not a full permutation")
    numerator = np.cumsum(np.asarray(counts, dtype=np.int64)[indices], axis=0)
    denominator = np.cumsum(np.asarray(totals, dtype=np.int64)[indices])
    return np.divide(numerator, denominator[:, None],
                     out=np.full(numerator.shape, np.nan), where=denominator[:, None] > 0)


def evaluate(rows, dictionary, indices, gallery, writer_index):
    values = style_prefixes(rows, dictionary, indices)
    mean, scale, keep, reference = gallery
    supported = np.isfinite(values).any(axis=1)
    filled = np.where(np.isfinite(values), values, mean)
    normalized = (filled[:, keep] - mean[keep]) / scale[keep]
    distances = np.sum((normalized[:, None, :] - reference[None, :, :])**2, axis=2)
    nearest = np.isclose(distances, distances.min(axis=1)[:, None], atol=1e-12, rtol=1e-12)
    flags = (supported & nearest[:, writer_index] & (nearest.sum(axis=1) == 1)).tolist()
    return dict(identification_curve=flags, identification=base.stable_time(flags))


def audit(rows, dictionary, primary, ledger):
    start = time.perf_counter()
    if primary.get("status") != "complete" or primary["writers"] != len(primary["writer_rows"]):
        raise ValueError("Complete original comparison required")
    groups = defaultdict(list)
    for row in rows:
        groups[row["writer"]].append(row)
    writers = [r["writer"] for r in primary["writer_rows"]]
    if writers != sorted(set(writers)):
        raise ValueError("Canonical unique writer order required")
    own = {w: sorted(groups[w], key=lambda r: r["session"]) for w in writers}
    reference = [base.profile(own[w], dictionary)["style"] for w in writers]
    gallery = base.gallery_model(reference)
    grouped = defaultdict(list)
    for unit in ledger:
        grouped[unit["writer"]].append(unit)
    if set(grouped) != set(writers):
        raise ValueError("Original order population differs")
    expected = {("chronological", 0), ("directed", 0), ("directed_random20", 0)}
    expected.update(("random", i) for i in range(base.CONFIG["random_orders"]))
    units, timings = [], []
    prefixes = 0
    for wi, writer in enumerate(writers):
        orders = grouped[writer]
        if len(orders) != len(expected) or {(x["policy"], x["replicate"]) for x in orders} != expected:
            raise ValueError("Incomplete or duplicate original policy bank")
        position = {r["session"]: i for i, r in enumerate(own[writer])}
        if len(position) != len(own[writer]):
            raise ValueError("Duplicate source session")
        elapsed = []
        for order in orders:
            indices = [position[step["session"]] for step in order["steps"]]
            before = time.perf_counter()
            result = evaluate(own[writer], dictionary, indices, gallery, wi)
            elapsed.append(time.perf_counter()-before)
            saved = order["recovery"]["style"]
            if any(result[k] != saved[k] for k in result):
                raise ValueError("Style parity failed")
            encoded = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
            units.append(dict(writer=writer, policy=order["policy"], replicate=order["replicate"],
                              prefixes=len(indices), sha256=hashlib.sha256(encoded).hexdigest()))
            prefixes += len(indices)
        timings.append(dict(writer=writer, orders=len(orders), max_order_seconds=max(elapsed),
                            sum_order_seconds=sum(elapsed)))
    work = dict(status="complete", exact_all_style_flags_and_endpoints=True,
                writers=len(writers), sessions=sum(len(v) for v in own.values()), orders=len(units),
                prefixes=prefixes, units=units, scientific_admission=False,
                empirical_controls_run=False, route="retain chronological default")
    timing = dict(wall_seconds=time.perf_counter()-start, writers=timings)
    return work, timing


def run(output, inputs, config, verify=False):
    if config != CONFIG or set(inputs) != {"dr1_completion"}:
        raise ValueError("Frozen parity configuration and original completion required")
    source = Path(inputs["dr1_completion"])
    names = ["PLAN.json", "output/DR1_PRIMARY.json", "output/DR1_ORDERS.json.gz", "output/DR1_BINDINGS.json"]
    for name in names:
        bind_completed(source, source.parent/name)
    original = read(source.parent/"PLAN.json")
    binding = read(source.parent/"output/DR1_BINDINGS.json")
    if original["config"] != base.CONFIG or binding["config"] != base.CONFIG:
        raise ValueError("Original scientific configuration differs")
    if binding["inputs"] != {k: sha256(v) for k, v in original["inputs"].items()}:
        raise ValueError("Original source binding differs")
    rows, dictionary = base.load(original["inputs"])
    primary = read(source.parent/"output/DR1_PRIMARY.json")
    with gzip.open(source.parent/"output/DR1_ORDERS.json.gz", "rt", encoding="utf8") as stream:
        ledger = json.load(stream)
    work, timing = audit(rows, dictionary, primary, ledger)
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    bound = dict(config=config, inputs={k: sha256(v) for k,v in inputs.items()})
    for name, value in [("PARITY.json", work), ("BINDINGS.json", bound)]:
        if verify:
            if read(output/name) != value:
                raise ValueError("Fresh parity reconstruction differs: "+name)
        else:
            write(output/name, value)
    write(output/("VERIFY_TIMING.json" if verify else "EXECUTE_TIMING.json"), timing)
    if verify:
        first = read(output/"EXECUTE_TIMING.json")
        slow = sum(max(a["max_order_seconds"], b["max_order_seconds"])*a["orders"]
                   for a,b in zip(first["writers"], timing["writers"], strict=True))
        overhead = max(first["wall_seconds"], timing["wall_seconds"])
        forecast = 2*config["margin"]*(config["forecast_control_copies"]*slow+overhead)+30
        write(output/"FORECAST.json", dict(combined_seconds=forecast,
              projected_complete_style_banks=config["forecast_control_copies"], full_random_orders=200,
              timing_only=True, controls_implemented=False, scientific_admission=False,
              limitation="Timing model only: actual control transformations and paired inference still require validation"))
        return dict(verified=True, exact_style_parity=True, scientific_admission=False)
    return dict(status="complete", scientific_admission=False)


def execute(output, inputs, config):
    return run(output, inputs, config)


def verify(output, inputs, config):
    return run(output, inputs, config, verify=True)
