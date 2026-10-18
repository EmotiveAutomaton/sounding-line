"""V4.c steps a/c/d/f on authenticated, immutable V4 saved worlds.

DESIGN CHECK: LESSONS 3-5 and the October18 errata read. A null statistic
below the empirical threshold is not a calibrated non-detection: step a is
descriptive and cannot open a route. Identical forecasts give exactly zero
gain; correct/reversed forecasts give positive/negative gain. Unrepresented
planted variation gives low overlap, exact writer-specific linear span gives
one. Constant targets have undefined R-squared, never a fabricated perfect fit.
No split test, new fit of outcomes, primary state or scientific admission is
produced here. Original V4 labels remain unchanged.
"""
from __future__ import annotations

import copy
import heapq
import math
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

from . import states_v2 as states
from .menus_io import assert_equal, input_hashes, read, sha256, write
from runners.drive.statistics import half_brier

ACTIONS = ("accept", "edit", "dismiss", "ignore")
READERS = ("R-kernel", "R-taste", "R-both", "R-oracle", "R-Phase0")
PLANTS = ("taste_lexical", "taste_matched", "habit")
SIZES = (0., .2, .4, .8)
INPUTS = {"sessions", "predictions", "v4_plan", "v4_complete", "v4_summary",
          "worlds", "null_worlds", "geometry", "geometry_arrays", "likelihood_source"}


def world_name(cell):
    return ("null-" if cell["permuted"] else "") + cell["plant"] + "-" + str(cell["delta"]) + "-" + str(cell["replicate"])


def roster():
    return [dict(plant=p, delta=d, replicate=r, permuted=False)
            for p in PLANTS for d in SIZES for r in range(10 if d in (0., .4) else 5)] + [
                dict(plant="taste_lexical", delta=0., replicate=r, permuted=True) for r in range(20)]


def load(inputs, config):
    if set(inputs) != INPUTS:
        raise ValueError("V4 diagnostics require the exact declared source set")
    if config != dict(bootstrap_draws=2000, bootstrap_seed=20261017):
        raise ValueError("V4 saved-output diagnostic configuration is frozen")
    identity = input_hashes(inputs)
    if len(identity) != len(INPUTS):
        raise ValueError("missing V4 diagnostic source")
    plan, complete = read(inputs["v4_plan"]), read(inputs["v4_complete"])
    if plan["module"] != "runners.drive.cards.menus_v4_full" or complete.get("status") != "COMPLETE" or not complete.get("fresh_process_verified"):
        raise ValueError("complete verified original V4 required")
    root = Path(inputs["v4_complete"]).parent.resolve()
    output = Path(inputs["v4_summary"]).parent.resolve()
    if output != root / "output":
        raise ValueError("V4 completion/output root mismatch")
    for key in ("sessions", "predictions", "likelihood_source"):
        path = str(Path(inputs[key]).resolve())
        if plan["pins"].get(path) != identity[key]:
            raise ValueError("V4 original source pin changed")
    for key in ("sessions", "predictions"):
        if Path(plan["inputs"][key]).resolve() != Path(inputs[key]).resolve():
            raise ValueError("V4 original input path changed")
    for key in ("v4_plan", "v4_summary", "worlds", "null_worlds", "geometry", "geometry_arrays"):
        rel = Path(inputs[key]).resolve().relative_to(root).as_posix()
        if complete["outputs"].get(rel) != identity[key]:
            raise ValueError("V4 source lacks completed artifact binding")
    worlds = read(inputs["worlds"]) + read(inputs["null_worlds"])
    expected = {world_name(cell): cell for cell in roster()}
    actual = {world_name(world["cell"]): world for world in worlds}
    if len(actual) != len(worlds) or set(actual) != set(expected):
        raise ValueError("V4 requires exactly the saved 90 calibration and 20 shuffled worlds")
    for name, cell in expected.items():
        assert_equal(actual[name]["cell"], cell)
    geometry = read(inputs["geometry"])
    with np.load(inputs["geometry_arrays"], allow_pickle=False) as arrays:
        geometry.update({name: arrays[name] for name in arrays.files})
    sessions = read(inputs["sessions"])
    base = {r["key"]: r["probabilities"]["B-pop"] for r in read(inputs["predictions"])}
    return dict(identity=identity, plan=plan, complete=complete, root=root, output=output,
                worlds=[actual[world_name(cell)] for cell in roster()], geometry=geometry,
                sessions=sessions, base=base, binding=read(output / "BINDING.json"))


def load_world(source, world):
    folder = source["output"] / "worlds" / world_name(world["cell"])
    checkpoint = read(folder / "CHECKPOINT.json")
    assert_equal(checkpoint["binding"], dict(run=source["binding"], cell=world["cell"]))
    for name in ("CONSTRUCTION.json", "READERS.json", "RESULT.json", "CHECKPOINT.json"):
        path = folder / name
        digest = sha256(path)
        if source["complete"]["outputs"].get(path.relative_to(source["root"]).as_posix()) != digest:
            raise ValueError("V4 saved world artifact changed")
        if name != "CHECKPOINT.json" and checkpoint["hashes"].get(name) != digest:
            raise ValueError("V4 saved world seal changed")
    assert_equal(read(folder / "RESULT.json"), world)
    construction, saved = read(folder / "CONSTRUCTION.json"), read(folder / "READERS.json")
    assert_equal(construction["cell"], world["cell"])
    return construction, saved


def rebuild(sessions, construction, seed):
    """Rehydrate saved outcomes, without resampling a world or fitting a model."""
    generated = copy.deepcopy(sessions)
    trace = {r["key"]: r for r in construction["rows"]}
    rows = [r for s in generated for r in s["rows"]]
    if len(trace) != len(construction["rows"]) or set(trace) != {r["key"] for r in rows} or len(rows) != len(trace):
        raise ValueError("V4 construction/source key support differs")
    for row in rows:
        t = trace[row["key"]]
        if t["writer"] != row["writer"] or t["session"] != row["session"]:
            raise ValueError("V4 original construction identity differs")
        row["handling"] = ACTIONS[t["outcome"]]
        row["previous_handling"] = ACTIONS[trace[t["previous_key"]]["outcome"]] if t["previous_key"] is not None else None
    cell = construction["cell"]
    if cell["permuted"]:
        names = np.random.default_rng(seed + 700000 + cell["replicate"]).permutation([s["writer"] for s in generated])
        for session, writer in zip(generated, names):
            session["writer"] = str(writer)
            for row in session["rows"]:
                row["writer"] = str(writer)
    return sorted(rows, key=lambda row: row["key"])


def kernel(rows, base, decay):
    groups = defaultdict(list)
    for row in rows:
        groups[row["writer"]].append(base[row["key"]])
    centers = {name: np.asarray(values).mean(0) for name, values in groups.items()}
    current = {name: value.copy() for name, value in centers.items()}
    pending, values = [], {}
    for row in sorted(rows, key=lambda r: (r["open_at"], r["key"])):
        while pending and pending[0][0] <= row["open_at"]:
            _, key, writer, outcome = heapq.heappop(pending)
            current[writer] = decay * current[writer] + (1 - decay) * np.eye(4)[outcome]
        values[row["key"]] = float(current[row["writer"]][0] - centers[row["writer"]][0])
        heapq.heappush(pending, (row["resolved_at"], row["key"], row["writer"], ACTIONS.index(row["handling"])))
    return np.asarray([[values[row["key"]]] for row in rows])


def reader_designs(rows, saved, construction, geometry, base):
    keys = [row["key"] for row in rows]
    index = {key: i for i, key in enumerate(geometry["keys"])}
    if set(index) != set(keys) or len(index) != len(keys):
        raise ValueError("V4 geometry/source support differs")
    train = np.isin(keys, saved["train_keys"])
    if not train.any() or train.sum() != len(saved["train_keys"]):
        raise ValueError("V4 saved training keys differ")
    raw = np.asarray([geometry["menu_mini"][index[key]] for key in keys])
    mean, sd = raw[train].mean(0), raw[train].std(0)
    sd[sd < 1e-10] = 1.
    raw = (raw - mean) / sd
    k = saved["selected_taste"].removeprefix("taste_")
    if k not in ("2", "4"):
        raise ValueError("V4 undeclared taste dimension")
    taste = raw @ np.asarray(saved["taste_directions"][k])
    decay = float(saved["selected_kernel"].removeprefix("kernel_"))
    if decay not in (.5, .8, .95):
        raise ValueError("V4 undeclared kernel")
    history = kernel(rows, base, decay)
    return {"R-taste": taste, "R-kernel": history, "R-both": np.c_[taste, history],
            "R-oracle": np.asarray([construction["oracle"][key] for key in keys])}


def overlap(x, target, writers):
    """Conditional writer slopes/intercepts, matching the random-slope span.

    Fits are descriptive projections of known planted scalars, not outcome fits.
    Within-writer centering prevents writer baselines from inflating overlap.
    """
    x, y, writers = np.asarray(x, float), np.asarray(target, float), np.asarray(writers)
    if x.ndim != 2 or y.shape != (len(x),) or writers.shape != y.shape or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("invalid planted-feature regression support")
    sse = sst = 0.; ranks = []; constant = 0
    for writer in sorted(set(writers)):
        ids = writers == writer
        a, b = x[ids], y[ids]
        a, b = a - a.mean(0), b - b.mean()
        coefficient, _, rank, _ = np.linalg.lstsq(a, b, rcond=None)
        sse += float(np.sum((b - a @ coefficient) ** 2)); sst += float(b @ b)
        ranks.append(int(rank)); constant += bool(float(b @ b) <= 1e-20)
    return dict(r_squared=None if sst <= 1e-20 else float(1 - sse / sst), residual_sum_squares=sse,
                within_writer_sum_squares=sst, rows=len(y), writers=len(ranks),
                rank_min=min(ranks), rank_max=max(ranks), constant_target_writers=int(constant),
                method="within-writer centered scalar on reader features, separate writer slopes; descriptive in-sample span")


def interval(gains, writers, seed, draws):
    writers, gains = np.asarray(writers), np.asarray(gains, float)
    names = sorted(set(writers))
    if len(names) < 2 or len(gains) != len(writers) or not np.isfinite(gains).all():
        raise ValueError("V4 predictive interval needs finite rows and two writers")
    sums = np.asarray([gains[writers == name].sum() for name in names])
    counts = np.asarray([np.sum(writers == name) for name in names])
    picks = np.random.default_rng(seed).integers(len(names), size=(draws, len(names)))
    bootstrap = sums[picks].sum(1) / counts[picks].sum(1)
    estimate = float(gains.mean()); ci = np.quantile(bootstrap, [.025, .975]).tolist()
    se = float(bootstrap.std(ddof=1))
    p = math.erfc(abs(estimate) / se / math.sqrt(2)) if se else float(estimate == 0.)
    return dict(estimate=estimate, interval95=ci, standard_error=se, approximate_two_sided_wald_p=p,
                state=states.contrast_state(estimate, *ci), detected=ci[0] > 0,
                clusters=len(names), bootstrap_draws=draws, seed=seed,
                conditional_on_saved_predictions=True, selection_adjusted=False)


def diagnose_world(source, world, config):
    construction, saved = load_world(source, world)
    rows = rebuild(source["sessions"], construction, source["plan"]["config"]["seed"])
    lookup = {row["key"]: row for row in rows}
    if len(set(saved["keys"])) != len(saved["keys"]):
        raise ValueError("duplicate V4 test key")
    for key, writer, truth in zip(saved["keys"], saved["writers"], saved["truth"]):
        if lookup[key]["writer"] != writer or ACTIONS.index(lookup[key]["handling"]) != truth:
            raise ValueError("V4 held-out source identity differs")
    if not len(saved["keys"]) == len(saved["writers"]) == len(saved["truth"]):
        raise ValueError("V4 held-out source length differs")
    truth = np.asarray(saved["truth"], int)
    baseline = half_brier(saved["population"], truth)
    designs = reader_designs(rows, saved, construction, source["geometry"], source["base"])
    trace = {r["key"]: r for r in construction["rows"]}
    scalar = np.asarray([trace[r["key"]]["scalar"] for r in rows])
    writer = np.asarray([r["writer"] for r in rows])
    tested = np.isin([r["key"] for r in rows], saved["keys"])
    results = {}
    for name in READERS:
        gain = baseline - half_brier(saved["predictions"][name], truth)
        predictive = interval(gain, saved["writers"], config["bootstrap_seed"], config["bootstrap_draws"])
        retained = world["readers"][name]["usefulness"]
        if not np.allclose([predictive["estimate"], *predictive["interval95"]],
                           [retained["estimate"], *retained["interval95"]], atol=2e-12, rtol=2e-12):
            raise ValueError("V4 retained predictive statistic does not replay")
        fit = saved["fits"].get(name)
        statistic = None if fit is None else max(0., 2 * (fit["fitted_log_likelihood"] - fit["null_log_likelihood"]))
        if fit is not None and (fit["method"] != "Laplace marginal likelihood; centered normal writer coefficients" or
                not np.isclose(statistic, world["readers"][name]["likelihood_ratio"], atol=1e-10, rtol=1e-10)):
            raise ValueError("V4 retained likelihood construction differs")
        results[name] = dict(likelihood_ratio=statistic, predictive=predictive,
            original_detected=world["readers"][name]["detected"],
            overlap_all=None if name not in designs else overlap(designs[name], scalar, writer),
            overlap_test=None if name not in designs else overlap(designs[name][tested], scalar[tested], writer[tested]))
    return dict(cell=world["cell"], readers=results, original_training_direction_test_overlap=True)


def aggregate(worlds):
    result = {}
    null = [w for w in worlds if w["cell"]["permuted"] or w["cell"]["delta"] == 0.]
    if len(null) != 50:
        raise ValueError("exactly 50 saved null worlds required")
    for reader in READERS:
        values = [w["readers"][reader]["likelihood_ratio"] for w in null]
        threshold = None if reader == "R-Phase0" else float(np.quantile(values, .95, method="linear"))
        cells = []
        for plant in PLANTS:
            for delta in SIZES:
                group = [w["readers"][reader] for w in worlds if not w["cell"]["permuted"] and w["cell"]["plant"] == plant and w["cell"]["delta"] == delta]
                r2 = [g["overlap_test"]["r_squared"] for g in group if g["overlap_test"] is not None and g["overlap_test"]["r_squared"] is not None]
                cells.append(dict(plant=plant, delta=delta, worlds=len(group),
                    empirical_detection_share=None if threshold is None else sum(g["likelihood_ratio"] > threshold for g in group) / len(group),
                    predictive_detection_share=sum(g["predictive"]["detected"] for g in group) / len(group),
                    mean_test_overlap=None if not r2 else float(np.mean(r2)), defined_overlap_worlds=len(r2)))
        result[reader] = dict(null_count=50, empirical_95th_percentile=threshold, cells=cells,
            threshold_method="linear empirical percentile; strict greater; descriptive reuse of null sample",
            original_likelihood_unavailable=reader == "R-Phase0")
    return result


def report(source, worlds):
    return dict(card="V4.c-saved-diagnostics", status="complete", diagnostic_only=True, primary=None,
        split_test_status="not_implemented_here", scientific_admission=False, original_v4_route_unchanged=True,
        input_hashes=source["identity"], world_count=len(worlds), cells=aggregate(worlds),
        likelihood_check=dict(approximation="Laplace marginal likelihood", unpenalized_plugin_writer_likelihood=False,
            modes_used_inside_integration_approximation=True, prior_penalty=True, hessian_logdet_correction=True,
            degrees_of_freedom_not_writer_count_times_K=True,
            original_direction_training="chronological training only",
            original_LR_support="training plus calibration, overlapping direction-learning rows",
            heldout_forecast_support="chronological test sessions; separate from the original LR"),
        overlap_scope="Known planted scalar on selected reader span with writer-specific slopes; no outcome refit, causal or generalization claim.",
        controls="Saved 30 zero-effect and 20 shuffled worlds reread descriptively; no new primary or calibrated reference.")


def execute(output: Path, inputs: dict, config: dict) -> dict:
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    source = load(inputs, config)
    binding = dict(inputs=source["identity"], config=config, code=sha256(__file__))
    if (output / "BINDING.json").exists():
        assert_equal(read(output / "BINDING.json"), binding)
    else:
        write(output / "BINDING.json", binding)
    start = time.perf_counter(); results = []
    for world in source["worlds"]:
        name = world_name(world["cell"]); path = output / "worlds" / (name + ".json")
        seal = path.with_suffix(".seal.json")
        if seal.exists():
            if read(seal) != dict(binding=binding, sha256=sha256(path)):
                raise ValueError("V4 diagnostic checkpoint changed")
            result = read(path)
        else:
            if (output / "YIELD_REQUEST.json").exists():
                return dict(status="yielded", completed_worlds=len(results))
            result = diagnose_world(source, world, config)
            write(path, result); write(seal, dict(binding=binding, sha256=sha256(path)))
        results.append(result)
        if len(results) == 11 and not (output / "FIRST_TENTH.json").exists():
            write(output / "FIRST_TENTH.json", dict(completed_worlds=11, projected_seconds=10 * (time.perf_counter() - start)))
    summary = report(source, results)
    if (output / "SUMMARY.json").exists():
        assert_equal(read(output / "SUMMARY.json"), summary)
    else:
        write(output / "SUMMARY.json", summary)
    return summary


def verify(output: Path, inputs: dict, config: dict) -> dict:
    output = Path(output); source = load(inputs, config); results = []
    binding = dict(inputs=source["identity"], config=config, code=sha256(__file__))
    assert_equal(read(output / "BINDING.json"), binding)
    for world in source["worlds"]:
        path = output / "worlds" / (world_name(world["cell"]) + ".json")
        assert_equal(read(path.with_suffix(".seal.json")), dict(binding=binding, sha256=sha256(path)))
        actual = diagnose_world(source, world, config)
        assert_equal(read(path), actual); results.append(actual)
    assert_equal(read(output / "SUMMARY.json"), report(source, results))
    return dict(verified=True, card="V4.c-saved-diagnostics", world_count=len(results), recomputed_from_completed_sources=True)
