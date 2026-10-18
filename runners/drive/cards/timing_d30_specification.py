"""D30.s: paired two-specification curve and raw within-writer outcome null.

DESIGN CHECK: LESSONS sections 3-5 and CONTROLS sections 1-4 read 2026-10-18.
NULL: aligned and shuffled median coefficients center at zero on constructed
zero-signal data. ALTERNATIVE: a planted positive association produces a positive
median with a small upper-tail permutation probability; reversal remains negative.
Invalid, negative, null, marginal and positive bands use states_v2. All fixed
draws must fit; no dropped draws, seed search, threshold or eligibility changes.
Raw outcome permutation breaks nuisance relationships too: descriptive reference,
not a conditional causal test. Earlier positive writer-shuffle controls survive.
"""
from __future__ import annotations
import hashlib
import json
import math
import time
from pathlib import Path
import numpy as np
from . import timing_d30 as original, timing_d30_outcome as prior
from . import states_v2 as states
from .timing_census import read, write, filehash
from .timing_p6 import gzread, gzip_equal, write_equal
from .timing_stats import sufficient, fit, bind, check_binding

CONFIG = dict(card="D30.s", bootstrap_draws=2000, permutations=2000,
              seed=20261017, permutation_seed=20261018)
NAMES = ["original_adjustment", "plus_own_marker_count"]


def designs(rows, mode):
    if mode not in {"per_character", "per_word"}:
        raise ValueError("D30.s requires valid pause timing, not a revision fallback")
    matrix, markers = prior.design(rows, mode)
    labels, _ = original.classify_markers(rows)
    supported = set(matrix["writers"])
    counts = []
    for r in rows:
        if r["writer"] not in supported or (r["writer"], r["marker"]) not in labels:
            continue
        if r["pause_seconds"] is None or r["pause_seconds"] <= 0 or r["population_surprisal"] is None:
            continue
        if mode == "per_character" and r["first_delta_characters"] != 1:
            continue
        counts.append(labels[(r["writer"], r["marker"])]["own_count"])
    if len(counts) != len(matrix["y"]):
        raise ValueError("paired eligibility differs")
    matrix["designs"] = [matrix.pop("x"), None]
    matrix["designs"][1] = [x + [n] for x, n in zip(matrix["designs"][0], counts)]
    matrix["timing_mode"] = mode
    return matrix, markers


def source(inputs, config):
    if config != CONFIG or set(inputs) != {"primary_completion", "extension_completion"}:
        raise ValueError("frozen configuration or input keys differ")
    sources = []
    for key, extension in [("primary_completion", False), ("extension_completion", True)]:
        terminal = Path(inputs[key]); root = terminal.parent
        complete = read(terminal)
        if complete.get("status") != "COMPLETE" or not complete.get("fresh_process_verified"):
            raise ValueError("source is not verified complete")
        names = ["PLAN.json", "output/D30_INTERMEDIATES.json.gz", "output/D30_PRIMARY.json", "output/D30_MARKERS.json"]
        for name in names:
            if complete["outputs"].get(name) != filehash(root / name):
                raise ValueError("source completion binding changed: " + name)
        plan = read(root / "PLAN.json")
        expected = dict(prior.ORIGINAL_CONFIG, extension=extension)
        if plan["config"] != expected or plan["module"] != "runners.drive.cards.timing_d30":
            raise ValueError("wrong source model")
        for name, digest in plan["pins"].items():
            if filehash(name) != digest:
                raise ValueError("source pin changed")
        saved = gzread(root / names[1])
        if saved["config"] != expected:
            raise ValueError("source intermediate configuration changed")
        sources.append((saved, read(root / names[2]), read(root / names[3])))
    a, b = sources
    if a[0]["rows"] != b[0]["rows"] or a[0]["timing_mode"] != b[0]["timing_mode"]:
        raise ValueError("source occurrence populations differ")
    matrix, markers = designs(a[0]["rows"], a[0]["timing_mode"])
    for x, (_, baseline, saved_markers) in zip(matrix["designs"], sources):
        effect = fit(sufficient(x, matrix["y"], matrix["writers"], within=True))[0]
        if markers != saved_markers or not math.isclose(effect, baseline["effect"], rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError("original point or marker parity failed")
        if baseline["observations"] != len(matrix["y"]) or baseline["writers"] != len(set(matrix["writers"])):
            raise ValueError("original denominator parity failed")
    return matrix


def coefficient_weights(x, writers):
    """Exact fixed-design OLS target linear functional; no refitting approximation."""
    a = np.asarray(x, float).copy(); owners = np.asarray(writers)
    for w in sorted(set(writers)):
        where = owners == w
        a[where] -= a[where].mean(axis=0)
    xx = a.T @ a
    keep = np.flatnonzero(np.diag(xx) > 1e-10)
    if 0 not in keep:
        raise ValueError("primary contrast has no within-writer support")
    scale = np.sqrt(np.diag(xx)[keep])
    z = a[:, keep] / scale
    normal = z.T @ z
    if np.linalg.matrix_rank(normal, tol=1e-9) != len(keep):
        raise ValueError("regression design not identifiable")
    target = np.zeros(len(keep)); target[0] = 1 / scale[0]
    return z @ np.linalg.solve(normal, target)


def draw_series(directory, binding, count, make_draw, on_tenth=None, yield_requested=None):
    """Retain paired vectors in consecutive checked blocks; regenerate RNG on resume."""
    path = Path(directory) if directory else None
    samples = []
    if path:
        path.mkdir(parents=True, exist_ok=True)
        for j, block in enumerate(sorted(path.glob("block-*.json"))):
            if block.name != f"block-{j:05d}.json" or not block.with_suffix(".sha256").exists():
                raise ValueError("checkpoint sequence differs")
            if block.with_suffix(".sha256").read_text().strip() != filehash(block):
                raise ValueError("checkpoint hash differs")
            r = read(block); expected = min(100, count-len(samples))
            if expected <= 0 or r["binding"] != binding or r["start"] != len(samples) or len(r["samples"]) != expected:
                raise ValueError("checkpoint binding differs")
            samples.extend(r["samples"])
        if samples and (np.asarray(samples).shape != (len(samples), 2) or not np.isfinite(samples).all()):
            raise ValueError("invalid saved paired fits")
    retained = len(samples)
    for i in range(count):
        result = make_draw(i >= retained)
        if i < retained:
            continue
        if len(result) != 2 or not np.isfinite(result).all():
            raise ValueError("undefined paired draw")
        samples.append(result)
        boundary = len(samples) % 100 == 0 or len(samples) == count
        if path and boundary:
            start = i // 100 * 100
            block = path / f"block-{i // 100:05d}.json"
            write_equal(block, dict(binding=binding, start=start, samples=samples[start:]))
            block.with_suffix(".sha256").write_bytes((filehash(block)+"\n").encode("ascii"))
        if on_tenth and i+1 == math.ceil(count/10):
            on_tenth()
        if boundary and yield_requested and yield_requested():
            return None
    return samples


def compute(matrix, config, checkpoint=None, on_tenth=None):
    xs, y, owners = matrix["designs"], matrix["y"], matrix["writers"]
    if len(xs) != 2 or len(set(owners)) < 3:
        raise ValueError("two specifications and at least three writers required")
    groups = [sufficient(x, y, owners, within=True) for x in xs]
    points = [fit(g)[0] for g in groups]
    binding = hashlib.sha256(json.dumps(dict(matrix=matrix, config=config), sort_keys=True,
                                        allow_nan=False).encode()).hexdigest()
    rng = np.random.default_rng(config["seed"])
    def boot(calculate):
        selected = rng.integers(0, len(groups[0]), len(groups[0]))
        return [fit([g[i] for i in selected])[0] for g in groups] if calculate else None
    directory = Path(checkpoint) if checkpoint else None
    should_yield = (lambda: (directory.parent / "YIELD_REQUEST.json").exists()) if directory else None
    samples = draw_series(directory / "bootstrap" if directory else None, binding+"bootstrap",
                          config["bootstrap_draws"], boot, on_tenth, should_yield)
    if samples is None:
        return dict(status="yielded", phase="bootstrap")
    weights = np.array([coefficient_weights(x, owners) for x in xs])
    if not np.allclose(weights @ y, points, rtol=1e-10, atol=1e-12):
        raise ValueError("linear-functional parity failed")
    rng = np.random.default_rng(config["permutation_seed"])
    a = np.asarray(owners); positions = [np.flatnonzero(a == w) for w in sorted(set(owners))]
    values = np.asarray(y)
    def permute(calculate):
        indices = np.arange(len(y))
        for p in positions:
            indices[p] = rng.permutation(p)
        return (weights @ values[indices]).tolist() if calculate else None
    null = draw_series(directory / "permutation" if directory else None, binding+"permutation",
                       config["permutations"], permute, None, should_yield)
    if null is None:
        return dict(status="yielded", phase="permutation")
    median_samples = np.median(samples, axis=1)
    median_null = np.median(null, axis=1)
    point = float(np.median(points))
    lo, hi = np.quantile(median_samples, [.025,.975]).tolist()
    specs = []
    for j, name in enumerate(NAMES):
        low, high = np.quantile(np.asarray(samples)[:,j], [.025,.975]).tolist()
        specs.append(dict(name=name, effect=points[j], ci_low=low, ci_high=high,
                          state=states.classify(points[j], low, high, 1)))
    primary = dict(effect=point, ci_low=lo, ci_high=hi,
        bootstrap_se=float(np.std(median_samples, ddof=1)),
        state=states.classify(point,lo,hi,1), expected_direction=1,
        upper_tail_permutation_p=float((1+np.count_nonzero(median_null >= point))/(len(null)+1)),
        permutation_reference="Raw log pauses permuted within writer, both designs held fixed; not a conditional causal test",
        null_median_effect=float(np.median(median_null)), null_mean_effect=float(np.mean(median_null)),
        null_95_interval=np.quantile(median_null,[.025,.975]).tolist(),
        bootstrap_draws=config["bootstrap_draws"], permutations=config["permutations"])
    return dict(card=config["card"], primary=primary, specifications=specs,
        observations=len(y), writers=len(set(owners)), timing_mode=matrix["timing_mode"],
        descriptive=True, scientific_admission=False,
        interval="Paired writer bootstrap of the median of the two refitted coefficients; frozen marker labels",
        original_control_warning="Positive extension writer-label shuffle remains; no person-location or automaticity admission")


def execute(output, inputs, config):
    output = Path(output); started = time.monotonic()
    matrix = source(inputs, config)
    write_equal(output / "RUN_BINDINGS.json", dict(config=config, inputs={k:filehash(v) for k,v in inputs.items()}))
    if (output / "SUMMARY.json").exists():
        return verify(output,inputs,config)["summary"]
    gzip_equal(output / "INTERMEDIATES.json.gz", matrix)
    def tenth():
        if not (output / "FIRST_TENTH.json").exists():
            elapsed = time.monotonic()-started
            write(output / "FIRST_TENTH.json", dict(active_seconds=elapsed,
                projected_cpu_seconds=elapsed*40, forecast_cpu_seconds=600,
                method="Conservative 40 times preparation plus first tenth of paired bootstrap, covering permutations and fresh replay"))
    result = compute(matrix,config,output/"draws",tenth)
    if result.get("status") == "yielded":
        return result
    write_equal(output/"SUMMARY.json",result)
    bind(output,inputs,config,["INTERMEDIATES.json.gz","SUMMARY.json"])
    return result


def verify(output, inputs, config):
    output = Path(output); check_binding(output,inputs,config)
    matrix = source(inputs,config)
    if matrix != gzread(output/"INTERMEDIATES.json.gz"):
        raise ValueError("saved paired matrix differs")
    result = compute(matrix,config)
    if result != read(output/"SUMMARY.json"):
        raise ValueError("fresh specification replay differs")
    return dict(verified=True,summary=result)

