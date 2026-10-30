"""Week 3 DR1 exact rank supplement; original policy outputs stay immutable.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-7 reread 2026-10-29.
NULL: order-invariant endpoints yield uniform randomized ranks, including all
ties. ALTERNATIVE: an early useful record lowers rank, a late one raises it.
Exact small enumeration validates the convolution; missing/changed original
banks refuse. Retrospective ranks cannot alone license person or routing claims.
"""
from collections import defaultdict
from functools import lru_cache
import gzip
from pathlib import Path

import numpy as np
from threadpoolctl import threadpool_limits

from . import week_directed_reading as old
from . import week_directed_style_parity as parity
from .week_reading_order import make_order
from .events_d4_sources import bind_completed
from .menus_io import read, sha256, write

CONFIG = dict(card="DR1-week3-ranks", schema=1, seed=20261026,
              random_orders=200, calibration_worlds=4096, calibration_writers=29)
CONFIGS = {mode: dict(CONFIG, mode=mode) for mode in ("constructed", "human")}


@lru_cache(maxsize=32)
def uniform_sum(n, width):
    if type(n) is not int or type(width) is not int or n < 1 or width < 2:
        raise ValueError("Positive writer count and rank width required")
    mass = np.ones(1)
    for _ in range(n):
        mass = np.convolve(mass, np.full(width, 1 / width))
    if not np.isclose(mass.sum(), 1., atol=1e-12, rtol=0):
        raise ValueError("Rank probability mass lost")
    mass.setflags(write=False)
    return mass


def rank_one(endpoint, random_endpoints, rng):
    bank = np.asarray(random_endpoints)
    if (type(endpoint) is not int or endpoint < 1 or bank.shape != (200,)
            or not np.issubdtype(bank.dtype, np.integer) or np.any(bank < 1)):
        raise ValueError("Complete 200-order integer endpoint bank required")
    below = int(np.count_nonzero(bank < endpoint))
    ties = int(np.count_nonzero(bank == endpoint))
    rank = below + int(rng.integers(1, ties + 2))
    return dict(randomized_rank=rank, midrank=below + (ties + 2) / 2,
                less=below, equal=ties, total=201)


def rank_test(endpoints, banks, seed=20261026):
    if len(endpoints) < 2 or len(endpoints) != len(banks):
        raise ValueError("At least two paired writers and complete banks required")
    rng = np.random.default_rng(seed)
    detail = [rank_one(e, b, rng) for e, b in zip(endpoints, banks, strict=True)]
    total = sum(r["randomized_rank"] for r in detail)
    mass = uniform_sum(len(detail), 201)
    index = total - len(detail)
    strict = float(mass[:index].sum()); point = float(mass[index])
    return dict(writers=len(detail), mean_rank=total / len(detail),
                mean_midrank=float(np.mean([r["midrank"] for r in detail])),
                null_mean_rank=101., inclusive_p=min(1., strict+point),
                mid_p=min(1., strict+.5*point),
                lower_tail=bool(strict+point < .05), rows=detail)


def style_world(kind):
    if kind not in ("constant", "early", "late", "tied"):
        raise ValueError("Unknown constructed world")
    dictionary = dict(words=["common", "w0", "w1", "w2"], punctuation=[], character_bigrams=[])
    groups, orders = {}, {}
    for wi in range(3):
        writer = f"w{wi}"
        metadata = [dict(session=f"{writer}-{j:02}", writer=writer, prompt=f"p{j%3}",
                         timestamp=j, typed_words=20) for j in range(12)]
        directed = make_order(metadata, "directed", old.CONFIG["seed"]+wi*1000)
        selected = directed["steps"][0 if kind == "early" else -1]["session"]
        groups[writer] = [dict(**m, word_counts={writer if kind == "constant" or
                            (kind != "tied" and m["session"] == selected) else "common":20},
                            punctuation_counts={}) for m in metadata]
        policies = [("directed", 0), ("chronological", 0)] + [("random", i) for i in range(200)]
        orders[writer] = [make_order(metadata, policy, old.CONFIG["seed"]+wi*1000+i)
                          for policy, i in policies]
    reference = [parity.style_prefixes(groups[w], dictionary, list(range(12)))[-1].tolist()
                 for w in sorted(groups)]
    gallery = old.gallery_model(reference); endpoints = []; banks = []
    complete_flags = []
    for wi, writer in enumerate(sorted(groups)):
        positions = {r["session"]:i for i, r in enumerate(groups[writer])}
        evaluated = [parity.evaluate(groups[writer], dictionary,
                     [positions[s["session"]] for s in order["steps"]], gallery, wi)
                     for order in orders[writer]]
        endpoints.append(evaluated[0]["identification"]["sessions"])
        banks.append([r["identification"]["sessions"] for r in evaluated[2:]])
        complete_flags.append(evaluated)
    return dict(kind=kind, rank=rank_test(endpoints, banks), endpoints=endpoints,
                random_endpoints=banks, complete_flags=complete_flags)


def calibration(config):
    if config != CONFIGS["constructed"]:
        raise ValueError("Frozen constructed configuration required")
    worlds = {kind:style_world(kind) for kind in ("constant", "early", "late", "tied")}
    # A common endpoint (including censoring) means order literally cannot matter.
    mass = uniform_sum(config["calibration_writers"], 201)
    cdf = np.cumsum(mass)
    exact_size = float(mass[cdf < .05].sum())
    rejections = 0; sums = []
    bank = [12]*200
    for index in range(config["calibration_worlds"]):
        rng = np.random.default_rng(np.random.SeedSequence([config["seed"], index]))
        total = sum(rank_one(12, bank, rng)["randomized_rank"]
                    for _ in range(config["calibration_writers"]))
        sums.append(total)
        rejections += bool(cdf[total-config["calibration_writers"]] < .05)
    rate = rejections/config["calibration_worlds"]
    gates = dict(exact_size=exact_size <= .05+1e-12,
                 empirical_size=.035 <= rate <= .065,
                 helpful=worlds["early"]["rank"]["lower_tail"],
                 harmful=worlds["late"]["rank"]["mean_midrank"] > 101 and
                         not worlds["late"]["rank"]["lower_tail"],
                 constant=all(e == 1 for e in worlds["constant"]["endpoints"]),
                 tied=all(e == 13 for e in worlds["tied"]["endpoints"]))
    return dict(gates=gates, passed=all(gates.values()), exact_null_size=exact_size,
                empirical_null_rejections=rejections, empirical_null_rate=rate,
                calibration_worlds=config["calibration_worlds"], rank_sums=sums,
                worlds=worlds, human_claim=False)


def load_original(completion):
    root = Path(completion).parent
    for name in ("PLAN.json", "output/DR1_PRIMARY.json", "output/DR1_ORDERS.json.gz", "output/DR1_BINDINGS.json"):
        bind_completed(completion, root/name)
    plan = read(root/"PLAN.json"); binding = read(root/"output/DR1_BINDINGS.json")
    if plan["config"] != old.CONFIG or binding["config"] != old.CONFIG:
        raise ValueError("Original scientific configuration differs")
    if binding["inputs"] != {k:sha256(v) for k, v in plan["inputs"].items()}:
        raise ValueError("Original source binding differs")
    rows, dictionary = old.load(plan["inputs"])
    primary = read(root/"output/DR1_PRIMARY.json")
    with gzip.open(root/"output/DR1_ORDERS.json.gz", "rt", encoding="utf8") as stream:
        ledger = __import__("json").load(stream)
    return rows, dictionary, primary, ledger


def human(inputs):
    if set(inputs) != {"dr1_completion", "calibration_completion"}:
        raise ValueError("Original and full calibration completions required")
    completion = Path(inputs["calibration_completion"])
    bind_completed(completion, completion.parent/"output/RANKS.json")
    cal = read(completion.parent/"output/RANKS.json")
    if not cal["passed"] or cal["calibration_worlds"] != 4096:
        raise ValueError("Full passing rank calibration required")
    rows, dictionary, primary, ledger = load_original(inputs["dr1_completion"])
    audit, _ = parity.audit(rows, dictionary, primary, ledger)
    groups = defaultdict(list)
    for unit in ledger: groups[unit["writer"]].append(unit)
    writers = sorted(groups); policies = {}
    for number, policy in enumerate(("directed", "chronological")):
        endpoints, banks = [], []
        for writer in writers:
            own = groups[writer]
            endpoints.append(next(r for r in own if r["policy"] == policy)["recovery"]["style"]["identification"]["sessions"])
            random = sorted((r for r in own if r["policy"] == "random"), key=lambda r:r["replicate"])
            banks.append([r["recovery"]["style"]["identification"]["sessions"] for r in random])
        policies[policy] = rank_test(endpoints, banks, CONFIG["seed"]+number)
    return dict(status="complete", policies=policies, writers=writers,
                parity={k:audit[k] for k in ("writers", "sessions", "orders", "prefixes", "exact_all_style_flags_and_endpoints")},
                primary="directed", scientific_admission=False,
                scope="retrospective overlapping-reference rank supplement; identification controls remain separate",
                original_result_unchanged=True)


def run(output, inputs, config, verification=False):
    if config not in CONFIGS.values(): raise ValueError("Frozen configuration required")
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    with threadpool_limits(limits=2):
        if config["mode"] == "constructed":
            if inputs: raise ValueError("Constructed mode accepts no human data")
            result = calibration(config)
        else: result = human(inputs)
    binding = dict(config=config, inputs={k:sha256(v) for k, v in inputs.items()})
    for name, value in (("RANKS.json", result), ("BINDINGS.json", binding)):
        if verification:
            if read(output/name) != value: raise ValueError("Fresh rank replay differs: "+name)
        else: write(output/name, value)
    return dict(verified=True, full_fresh_replay=True) if verification else dict(status="complete")


def execute(output, inputs, config): return run(output, inputs, config)
def verify(output, inputs, config): return run(output, inputs, config, True)
