"""Ordered role-pair rates using the filed BG census and whole-meeting draws."""
from collections import Counter
from pathlib import Path

import numpy as np

from .batch_runtime import filehash, freeze, read
from .week6_la7_role_panel_v1 import design, table
from .week6_la78_source_v1 import checked_table
from .week6_la78_support_v1 import group_by

RULES = ("single", "latest", "fractional")
SEED = 202611207
DRAWS = 2000


def load_meetings(inputs):
    census = Path(inputs["support"])
    filed = Path(inputs["support_receipt"])
    if filehash(census) != inputs["support_sha256"] or filehash(filed) != inputs["support_receipt_sha256"]:
        raise ValueError("BG support or filed receipt changed")
    receipt = read(filed)
    record = read(census)
    if (not receipt["full_write_through"] or receipt["support_sha256"] != filehash(census)
            or record["amendment"] != "BG" or record["original_terminal_sha256"] != inputs["original_sha256"]
            or record["extended_terminal_sha256"] != inputs["extended_sha256"]):
        raise ValueError("Filed pre-outcome support required")
    acts = group_by(checked_table(inputs, "acts"), "meeting")
    laughs = group_by(checked_table(inputs, "laughs"), "meeting")
    metadata = checked_table(inputs, "metadata")
    meetings = []
    tied = 0
    for key, meta in sorted(metadata.items()):
        data = design(acts[key], laughs[key], meta)
        if data is not None:
            exposure, counts, ties = data
            meetings.append((exposure, counts))
            tied += ties
    support = record["populations"]["LA7"]
    if len(meetings) != support["eligible_meetings"]:
        raise ValueError("Eligible role meetings differ from original census")
    for rule in RULES:
        actual = sum(sum(counts[rule].values()) for _, counts in meetings)
        expected = support["single" if rule == "single" else "candidate"]
        if not np.isclose(actual, expected, rtol=0, atol=1e-7):
            raise ValueError("Role counts differ from the original census")
    return meetings, support, tied


def encode(meetings):
    cells = sorted({cell for exposure, counts in meetings
                    for source in (exposure, *counts.values()) for cell in source})
    matrix = np.array([[[source.get(cell, 0.) for cell in cells]
                        for source in (exposure, *(counts[rule] for rule in RULES))]
                       for exposure, counts in meetings], dtype=float)
    return cells, matrix


def estimate(cells, matrix, weights):
    weights = np.asarray(weights)
    if weights.shape != (len(matrix),) or np.any(weights < 0) or np.any(weights != np.floor(weights)):
        raise ValueError("Invalid whole-meeting weights")
    totals = np.tensordot(weights, matrix, axes=1)
    exposure, *counts = [Counter(dict(zip(cells, row.tolist()))) for row in totals]
    return table([(exposure, dict(zip(RULES, counts)))])


def run(output, inputs, config):
    output = Path(output)
    if config.get("draws") != DRAWS or config.get("max_new_draws") not in (100, DRAWS):
        raise ValueError("Expected fixed pilot or complete meeting draw sequence")
    output.mkdir(parents=True, exist_ok=True)
    meetings, support, ties = load_meetings(inputs)
    cells, matrix = encode(meetings)
    size = len(meetings)
    point = estimate(cells, matrix, np.ones(size, dtype=int))
    binding = {"support": inputs["support_sha256"], "runner": filehash(__file__),
               "seed": SEED, "meetings": size}
    draws = []
    new_draws = 0
    for begin in range(0, DRAWS, 10):
        path = output / f"draws-{begin:04d}.json"
        if path.exists():
            block = read(path)
            if block["binding"] != binding or block["begin"] != begin or len(block["draws"]) != 10:
                raise ValueError("Mismatched checkpoint")
        else:
            if new_draws >= config["max_new_draws"] or (output / "YIELD_REQUEST.json").exists() or (output.parent / "YIELD_REQUEST.json").exists():
                return dict(status="yielded", completed=len(draws), total=DRAWS)
            new_draws += 10
            values = []
            for ordinal in range(begin, begin+10):
                rng = np.random.default_rng(np.random.SeedSequence([SEED, ordinal]))
                weights = np.bincount(rng.integers(size, size=size), minlength=size)
                result = estimate(cells, matrix, weights)
                if [(r["laugher_role"], r["target_role"]) for r in result] != [
                        (r["laugher_role"], r["target_role"]) for r in point]:
                    raise ValueError("Different ordered role cells in a meeting draw")
                values.append([[row["single"]["rate"], row["single"]["excess_rate"]] for row in result])
            block = dict(binding=binding, begin=begin, draws=values)
            freeze(path, block)
        draws.extend(block["draws"])
    if len(draws) != DRAWS:
        return dict(status="yielded", completed=len(draws), total=DRAWS)
    for idx, row in enumerate(point):
        for col, key in enumerate(("primary_rate_interval", "primary_excess_interval")):
            values = [sample[idx][col] for sample in draws]
            row[key] = None if None in values else np.quantile(values, [.025, .975]).tolist()
            row[key+"_undefined_draws"] = values.count(None)
    result = dict(status="computed", card="LA7", registered_direction=None, support=support,
                  latest_end_tied_laughs=ties, rows=point, draws=DRAWS,
                  limit_single_under_half=support["single_under_half"], source_binding=binding)
    path = output / "ROLE_TABLE.json"
    if path.exists():
        if read(path) != result:
            raise ValueError("Prior role result differs")
    else:
        freeze(path, result)
    return result


def execute(output, inputs, config):
    return run(output, inputs, config)


def verify(output, inputs, config):
    output = Path(output)
    result = run(output / "independent-replay", inputs, config)
    if result["status"] == "yielded":
        return result
    if result != read(output / "ROLE_TABLE.json"):
        raise ValueError("Fresh original-source role fit differs")
    for begin in range(0, DRAWS, 10):
        name = f"draws-{begin:04d}.json"
        if read(output / name) != read(output / "independent-replay" / name):
            raise ValueError("Fresh whole-meeting draws differ")
    return dict(verified=True, checked_draws=DRAWS, support_match=True)
