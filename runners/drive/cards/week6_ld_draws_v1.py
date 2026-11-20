"""Counted Round 29 diary draws, checkpoints and fresh replay.

DESIGN CHECK: LESSONS 3–5. Each source has a fixed all-person roster and
indexed random bank. Preserve undefined cells in place under either sign.
Each interval needs all 2,000 draws. Verification reconstructs and compares
every cell, including undefined cells and source denominators.
"""
import json
import math
import time
from pathlib import Path

import numpy as np

from .batch_runtime import freeze, read
from .week6_lattice_diary_v1 import person_draw


DRAWS = 2000
CHUNK = 25
SOURCE_SEEDS = {"0056": 202611190056, "0057": 202611190057}


class RequestedYield(Exception):
    """The caller has reached a monitored operational boundary."""


def _values(result, keys):
    if set(result) != set(keys):
        raise ValueError("Producer omitted or added a metric")
    row = [None if result[k] is None else float(result[k]) for k in keys]
    if any(v is not None and not math.isfinite(v) for v in row):
        raise ValueError("Nonfinite estimate must have explicit undefined status")
    return row


def compare(a, b):
    if len(a) != len(b):
        raise ValueError("Replay metric width differs")
    for left, right in zip(a, b):
        if left is None or right is None:
            if left is not right:
                raise ValueError("Independent replay disagrees on identification")
        elif not math.isclose(left, right, abs_tol=1e-8, rel_tol=1e-7):
            raise ValueError("Independent replay differs numerically")


def load_blocks(directory, keys, draws=DRAWS):
    rows = []
    for path in sorted(directory.glob("draws-*.json")):
        block = read(path)
        start, values = block["start"], block["values"]
        if (type(start) is not int or start != len(rows)
                or path.name != f"draws-{start:04d}.json" or not 0 < len(values) <= CHUNK
                or any(len(row) != len(keys) for row in values) or start + len(values) > draws):
            raise ValueError("Noncontiguous or malformed authenticated diary checkpoint")
        rows.extend(values)
    return rows


def summarize(keys, specs, point, rows):
    if len(rows) != DRAWS:
        raise ValueError("Exactly 2,000 indexed draws required for intervals")
    table = {}
    for j, key in enumerate(keys):
        data = [row[j] for row in rows]
        invalid = data.count(None)
        item = dict(specs[key], estimate=point[j], draws=DRAWS, invalid_draws=invalid,
                    interval=None, bootstrap_sd=None)
        if point[j] is not None and invalid == 0:
            item["interval"] = np.quantile(data, [.025, .975]).tolist()
            item["bootstrap_sd"] = float(np.std(data, ddof=1))
            item["sees"] = 2.8 * item["bootstrap_sd"]
            if item.get("bar") is not None:
                item["supports_at"] = item["bar"] + item["sees"]
        table[key] = item
    return table


def run_draws(directory, producer, prepared, member, guard, *, verify=False, original=None,
              max_new_draws=DRAWS, progress=None, source_digest=None):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    keys = sorted(prepared.specs)
    if not keys or not isinstance(prepared.people, (int, np.integer)) or prepared.people < 2:
        raise ValueError("A complete source roster and declared metrics are required")
    point = _values(producer.evaluate(prepared, None, guard, verify=verify), keys)
    schema = dict(keys=keys, specs=prepared.specs, metadata=prepared.metadata,
                  people=int(prepared.people), member=member, source_seed=SOURCE_SEEDS[member],
                  draws=DRAWS, resampling="all-source-person multiplicities, same draw id across cards")
    if source_digest is not None:
        if not isinstance(source_digest, str) or len(source_digest) != 64 or any(
                c not in "0123456789abcdef" for c in source_digest):
            raise ValueError("Invalid source digest for diary checkpoints")
        schema["source_sha256"] = source_digest
    schema = json.loads(json.dumps(schema, allow_nan=False))
    if (directory / "SCHEMA.json").exists():
        if read(directory / "SCHEMA.json") != schema:
            raise ValueError("Checkpoint source, specification or roster differs")
        compare(read(directory / "POINT.json"), point)
    else:
        freeze(directory / "SCHEMA.json", schema)
        freeze(directory / "POINT.json", point)
    rows = load_blocks(directory, keys)
    reference = None
    if verify:
        if read(original / "SCHEMA.json") != schema:
            raise ValueError("Fresh source support or schema differs")
        compare(read(original / "POINT.json"), point)
        reference = load_blocks(original, keys)
        if len(reference) != DRAWS:
            raise ValueError("Incomplete execution cannot be verified")
        for j, row in enumerate(rows):
            compare(reference[j], row)
    first = len(rows)
    units = np.arange(prepared.people)
    started = time.monotonic()
    while len(rows) < min(DRAWS, first + max_new_draws):
        start = len(rows)
        batch = []
        try:
            for draw in range(start, min(start + CHUNK, first + max_new_draws, DRAWS)):
                guard()
                weight = person_draw(units, source_seed=SOURCE_SEEDS[member], draw=draw)
                values = _values(producer.evaluate(prepared, weight, guard, verify=verify), keys)
                if verify:
                    compare(reference[draw], values)
                batch.append(values)
        finally:
            if batch:
                freeze(directory / f"draws-{start:04d}.json", dict(start=start, values=batch))
                rows.extend(batch)
                if progress:
                    progress(len(rows), time.monotonic() - started)
    if len(rows) < DRAWS:
        raise RequestedYield("draw quantum")
    table = summarize(keys, prepared.specs, point, rows)
    return dict(status="complete", member=member, verified=verify,
                replay_compared_every_cell=verify, metrics=table, support=prepared.metadata,
                source_seed=SOURCE_SEEDS[member], draws=DRAWS)
