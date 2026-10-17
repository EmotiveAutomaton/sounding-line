"""Saved-boundary version of the unchanged writer-bootstrap regression.

DESIGN CHECK: LESSONS 3-5 reread 2026-10-17. NULL and ALTERNATIVE retain
the same fixed draws, fit and interval. Changed data/configuration, damaged
receipts or undefined fits fail closed. Yield is operational, never a null;
fresh verification uses no saved fits. No running source is replaced.
"""
from __future__ import annotations

import hashlib
import json
import math
import time
from pathlib import Path

import numpy as np

from .timing_stats import sufficient, fit
from .timing_census import read, write, filehash
from . import states_v2 as states


def regression(x, y, writers, *, within=False, random_intercept=False,
               draws=2000, seed=20261017, direction=1, on_tenth=None,
               checkpoint=None, yield_requested=None):
    started = time.monotonic()
    groups = sufficient(x, y, writers, within)
    if len(groups) < 3:
        return dict(state="invalid", reason="fewer than three independent writers", writers=len(groups))
    try:
        effect, variance_ratio = fit(groups, random_intercept)
    except ValueError as exc:
        return dict(state="invalid", reason=str(exc), writers=len(groups))
    binding = hashlib.sha256(json.dumps(dict(
        groups=[{k: v.tolist() if isinstance(v, np.ndarray) else v for k, v in g.items()} for g in groups],
        draws=draws, seed=seed, direction=direction, within=within,
        random_intercept=random_intercept), sort_keys=True, allow_nan=False).encode()).hexdigest()
    checkpoint = Path(checkpoint) if checkpoint is not None else None
    samples = []
    block_size = min(100, max(1, math.ceil(draws / 10)))
    if checkpoint is not None:
        checkpoint.mkdir(parents=True, exist_ok=True)
        paths = sorted(checkpoint.glob("block-*.json"))
        for j, path in enumerate(paths):
            if path.name != f"block-{j:05d}.json":
                raise ValueError("nonconsecutive regression checkpoint")
            receipt = path.with_suffix(".sha256")
            if not receipt.exists() or receipt.read_text().strip() != filehash(path):
                raise ValueError("regression checkpoint hash changed")
            record = read(path)
            expected = min(block_size, draws - len(samples))
            if record["binding"] != binding or record["start"] != len(samples) or len(record["samples"]) != expected or expected <= 0:
                raise ValueError("regression checkpoint binding changed")
            samples.extend(record["samples"])
        if not np.isfinite(samples).all():
            raise ValueError("nonfinite saved regression fit")
    retained = len(samples)
    rng = np.random.default_rng(seed)
    for draw in range(draws):
        selected = rng.integers(0, len(groups), len(groups))
        if draw < retained:
            continue
        try:
            samples.append(fit([groups[i] for i in selected], random_intercept)[0])
        except ValueError as exc:
            return dict(state="invalid", reason="undefined bootstrap fit: " + str(exc), writers=len(groups))
        boundary = len(samples) % block_size == 0 or len(samples) == draws
        if checkpoint is not None and boundary:
            start = (draw // block_size) * block_size
            path = checkpoint / f"block-{draw // block_size:05d}.json"
            write(path, dict(binding=binding, start=start, samples=samples[start:]))
            path.with_suffix(".sha256").write_bytes((filehash(path) + "\n").encode("ascii"))
        if on_tenth is not None and draw + 1 == math.ceil(draws / 10):
            on_tenth(dict(primary_seconds=time.monotonic() - started,
                          completed_draws=draw + 1, total_draws=draws))
        if boundary and yield_requested is not None and yield_requested():
            return dict(status="yielded", completed_draws=len(samples), total_draws=draws)
    low, high = np.quantile(samples, [.025, .975]).tolist()
    se = float(np.std(samples, ddof=1))
    z = effect / se if se > 0 else None
    return dict(effect=effect, ci_low=low, ci_high=high, writers=len(groups), observations=len(y),
                bootstrap_se=se, z=z, wald_p_two_sided=math.erfc(abs(z) / math.sqrt(2)) if z is not None else None,
                p_reference="approximate two-sided normal Wald test; descriptive; state remains percentile-CI based",
                state=states.contrast_state(effect, low, high, direction), expected_direction=direction,
                bootstrap_draws=draws, seed=seed, variance_ratio=variance_ratio,
                interval="writer-cluster percentile bootstrap, refit per resample")
