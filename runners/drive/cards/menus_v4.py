"""V4 planted taste/habit calibration, with retained worlds and reader fits.

DESIGN CHECK: LESSONS 3-5 and EXECUTION read October 17. At delta zero the
generating probabilities equal the frozen population probabilities exactly.
Under a recoverable alternative the stipulated likelihood-ratio rejection rate
increases; last-20%-session half-Brier gain is measured separately. States are
exhaustive: sees requires >=.8 at .4 and <=.1 at zero; sees-large-only requires
>=.8 at .8 with the zero rate <=.1; otherwise blind. A null size-check rejection
share above .1 also forces blind, never a scientific null. Numerical failures
raise rather than count as non-detection. No p threshold is repaired after runs.

Pre-run clarifications accepted by the owner: taste plants the menu mean of
offered-suggestion projections (never the chosen option); each option projection
is retained. Habit is centered on each writer's frozen base accept probability,
initialized to that base vector, not centered on the future realized world mean.
The chi-square reference is stipulated and empirically size-checked, not assumed
conservative after factor-direction and hyperparameter estimation.
"""
from __future__ import annotations

import copy
import heapq
import shutil
import time
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.special import softmax
from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer

from . import states
from .menus_io import assert_equal, input_hashes, read, sha256, write
from .menus_p4 import chronological_partitions, brier
from .menus_v4_stats import variance_reader, predict, taste_directions
from runners.drive.statistics import cluster_interval
from runners.drive.v1_phase0_v2 import fit_world, wilson

ACTIONS = ("accept", "edit", "dismiss", "ignore")
PLANTS = ("taste_lexical", "taste_matched", "habit")
SIZES = (0., .2, .4, .8)
READERS = ("R-kernel", "R-taste", "R-both", "R-oracle", "R-Phase0")


def make_geometry(sessions, records, vectors, seed):
    row_map = {row["key"]: row for session in sessions for row in session["rows"]}
    records = sorted(records, key=lambda row: row["key"])
    if len(records) != len(row_map) or {row["key"] for row in records} != set(row_map):
        raise ValueError("V4 representation support mismatch")
    texts, mini, slices = [], [], []
    for feature in records:
        row = row_map[feature["key"]]
        if len(row["menu"]) != len(feature["options"]):
            raise ValueError("V4 menu representation mismatch")
        start = len(texts); texts.extend(row["menu"]); mini.extend(vectors[feature["options"]])
        slices.append((start, len(texts)))
    tfidf = TfidfVectorizer(analyzer="char", ngram_range=(3, 3), lowercase=True, dtype=np.float64)
    lexical = tfidf.fit_transform(texts)
    if min(lexical.shape) <= 16 or len(mini) <= 16:
        raise ValueError("fewer than 16 supported representation dimensions")
    svd = TruncatedSVD(n_components=16, random_state=seed)
    lexical16 = svd.fit_transform(lexical)
    pca = PCA(n_components=16, svd_solver="randomized", random_state=seed)
    mini16 = pca.fit_transform(np.asarray(mini))
    basis, _ = np.linalg.qr(np.random.default_rng(seed + 11).normal(size=(16, 4)))
    return dict(keys=[row["key"] for row in records], slices=np.asarray(slices, int),
                lexical=lexical16, mini=mini16, basis=basis,
                menu_lexical=np.asarray([lexical16[a:b].mean(0) for a, b in slices]),
                menu_mini=np.asarray([mini16[a:b].mean(0) for a, b in slices]),
                vocabulary_size=len(tfidf.vocabulary_), lexical_explained=svd.explained_variance_ratio_.tolist(),
                mini_explained=pca.explained_variance_ratio_.tolist())


def frozen_centers(rows, base):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["writer"]].append(base[row["key"]])
    return {writer: np.asarray(values, float).mean(0) for writer, values in grouped.items()}


def construct(sessions, base, geometry, plant, delta, seed):
    if plant not in PLANTS or delta not in SIZES:
        raise ValueError("undeclared V4 plant or dose")
    generated = copy.deepcopy(sessions)
    rows = sorted((row for session in generated for row in session["rows"]), key=lambda row: (row["open_at"], row["key"]))
    index = {key: i for i, key in enumerate(geometry["keys"])}
    if set(index) != {row["key"] for row in rows} or set(base) != set(index):
        raise ValueError("V4 base/source/geometry support mismatch")
    rng = np.random.default_rng(seed); writers = sorted({row["writer"] for row in rows})
    centers = frozen_centers(rows, base)
    latent = {writer: rng.normal(size=4) for writer in writers}
    latent = {writer: value / np.linalg.norm(geometry["basis"] @ value) for writer, value in latent.items()}
    habit_slopes = {writer: float(rng.normal()) for writer in writers}
    feature_space = "mini" if plant == "taste_matched" else "lexical"
    raw_coords = geometry["menu_" + feature_space] @ geometry["basis"]
    standard = {}
    for writer in writers:
        ids = [index[row["key"]] for row in rows if row["writer"] == writer]
        scores = raw_coords[ids] @ latent[writer]
        scale = float(scores.std())
        standard[writer] = (raw_coords[ids].mean(0), scale if scale > 1e-12 else 1.)
    kernels = {writer: centers[writer].copy() for writer in writers}; pending = []
    histories = defaultdict(list); trace = []; oracle = {}
    for row in rows:
        while pending and pending[0][0] <= row["open_at"]:
            _, key, writer, opened, outcome = heapq.heappop(pending)
            kernels[writer] = .7 * kernels[writer] + .3 * np.eye(4)[outcome]
            histories[writer].append((opened, key, outcome))
        writer = row["writer"]; gi = index[row["key"]]
        past = sorted(histories[writer]); row["previous_handling"] = ACTIONS[past[-1][2]] if past else None
        mean, scale = standard[writer]
        coords = (raw_coords[gi] - mean) / scale
        start, stop = geometry["slices"][gi]
        options = ((geometry[feature_space][start:stop] @ geometry["basis"] - mean) @ latent[writer]) / scale
        kernel = float(kernels[writer][0] - centers[writer][0])
        scalar = kernel * habit_slopes[writer] if plant == "habit" else float(coords @ latent[writer])
        probability = np.asarray(base[row["key"]], float)
        if probability.shape != (4,) or not np.all(probability > 0) or not np.isclose(probability.sum(), 1, atol=1e-12):
            raise ValueError("invalid frozen population vector")
        shift = delta * scalar
        q = probability.copy() if shift == 0 else softmax(np.log(probability) + [shift, 0., 0., 0.])
        outcome = int(rng.choice(4, p=q)); row["handling"] = ACTIONS[outcome]
        heapq.heappush(pending, (row["resolved_at"], row["key"], writer, row["open_at"], outcome))
        oracle[row["key"]] = [kernel] if plant == "habit" else coords.tolist()
        trace.append(dict(key=row["key"], writer=writer, session=row["session"], outcome=outcome,
                          probabilities=q.tolist(), shift=shift, scalar=scalar, kernel=kernel,
                          previous_key=past[-1][1] if past else None,
                          option_projections=options.tolist() if plant != "habit" else None))
    return generated, trace, oracle


def kernel_features(rows, base, decay):
    centers = frozen_centers(rows, base); kernel = {key: value.copy() for key, value in centers.items()}
    pending, values = [], {}
    for row in sorted(rows, key=lambda row: (row["open_at"], row["key"])):
        while pending and pending[0][0] <= row["open_at"]:
            _, key, writer, outcome = heapq.heappop(pending)
            kernel[writer] = decay * kernel[writer] + (1 - decay) * np.eye(4)[outcome]
        values[row["key"]] = float(kernel[row["writer"]][0] - centers[row["writer"]][0])
        heapq.heappush(pending, (row["resolved_at"], row["key"], row["writer"], ACTIONS.index(row["handling"])))
    return np.asarray([[values[row["key"]]] for row in rows])


def masks_for(sessions, rows):
    splits, excluded = chronological_partitions(sessions)
    names = {name: set(session["session"] for group in splits.values() for session in group[name])
             for name in ("train", "calibration", "test")}
    masks = {name: np.asarray([row["session"] in names[name] for row in rows]) for name in names}
    if any(not mask.any() for mask in masks.values()):
        raise ValueError("empty V4 train/calibration/test support")
    return masks, excluded


def read_world(sessions, trace, oracle, geometry, base, config):
    rows = sorted((row for session in sessions for row in session["rows"]), key=lambda row: row["key"])
    population_forecasts, population_fits = fit_world(sessions, lambda *_: None)
    forecast = {row["key"]: row for row in population_forecasts}
    population = np.asarray([forecast[row["key"]]["probabilities"]["B-pop"] for row in rows])
    phase0 = np.asarray([forecast[row["key"]]["probabilities"]["B-mixlogit"] for row in rows])
    y = np.asarray([ACTIONS.index(row["handling"]) for row in rows]); accept = (y == 0).astype(float)
    writers = np.asarray([row["writer"] for row in rows]); masks, exclusions = masks_for(sessions, rows)
    train, cal, test = (masks[name] for name in ("train", "calibration", "test")); fit_mask = train | cal
    gi = {key: i for i, key in enumerate(geometry["keys"])}
    raw = np.asarray([geometry["menu_mini"][gi[row["key"]]] for row in rows])
    mean, sd = raw[train].mean(0), raw[train].std(0); sd[sd < 1e-10] = 1.; raw = (raw - mean) / sd
    candidates, candidate_fits = {}, {}
    def fit_design(design, mask):
        return variance_reader(design[mask], accept[mask], population[mask, 0], writers[mask], int(config.get("optimizer_maxiter", 100)))
    def select(designs):
        scores = []
        for name, design in designs.items():
            reader = fit_design(design, train)
            score = float(brier(predict(reader, design[cal], population[cal], writers[cal]), y[cal]).mean())
            candidate_fits[name] = dict(fit=reader, calibration_half_brier=score)
            scores.append((score, name))
        name = min(scores)[1]
        return name, designs[name]
    taste = {}
    directions = {}
    for k in (2, 4):
        direction = taste_directions(raw, accept, population[:, 0], writers, train, k)
        taste[str(k)] = raw @ direction; directions[str(k)] = direction.tolist()
    taste_name, taste_x = select({"taste_" + key: value for key, value in taste.items()})
    kernels = {"kernel_" + str(decay): kernel_features(rows, base, decay) for decay in (.5, .8, .95)}
    kernel_name, kernel_x = select(kernels)
    designs = {"R-taste": taste_x, "R-kernel": kernel_x, "R-both": np.c_[taste_x, kernel_x],
               "R-oracle": np.asarray([oracle[row["key"]] for row in rows])}
    fits, predictions = {}, {"R-Phase0": phase0[test].tolist()}
    for name, design in designs.items():
        fit = fit_design(design, fit_mask); fits[name] = fit
        predictions[name] = predict(fit, design[test], population[test], writers[test]).tolist()
    saved = dict(keys=[row["key"] for row, selected in zip(rows, test) if selected],
                 writers=writers[test].tolist(), truth=y[test].tolist(), population=population[test].tolist(), predictions=predictions,
                 fits=fits, candidates=candidate_fits, selected_taste=taste_name, selected_kernel=kernel_name,
                 taste_directions=directions, train_keys=[row["key"] for row, selected in zip(rows, train) if selected],
                 calibration_keys=[row["key"] for row, selected in zip(rows, cal) if selected],
                 excluded_writers=exclusions, population_fit_count=len(population_fits))
    return saved


def score_world(saved, seed=20261017):
    truth = np.asarray(saved["truth"], int); population = np.asarray(saved["population"])
    baseline = brier(population, truth); results = {}
    for name in READERS:
        gains = baseline - brier(saved["predictions"][name], truth)
        interval = cluster_interval(gains, saved["writers"], seed=seed, draws=2000)
        if name == "R-Phase0":
            detected, pvalue, statistic = interval["interval95"][0] > 0, None, None
            reference = "V1 continuity: writer-cluster lower half-Brier bound above zero"
        else:
            from scipy.stats import chi2
            fit = saved["fits"][name]; statistic = max(0., 2 * (fit["fitted_log_likelihood"] - fit["null_log_likelihood"]))
            k = fit["dimensions"]
            pvalue = 1. if statistic == 0 else float((.5 if k == 1 else 1.) * chi2.sf(statistic, k))
            detected, reference = pvalue < .05, fit["reference"]
            if not np.isclose(statistic, fit["likelihood_ratio"], rtol=1e-10, atol=1e-10):
                raise ValueError("retained likelihood ratio disagrees")
        results[name] = dict(detected=bool(detected), p_value=pvalue, likelihood_ratio=statistic,
                             reference=reference, usefulness=interval)
    return dict(readers=results, scored_decisions=len(truth), writers=len(set(saved["writers"])))


def cell_seed(plant, delta, replicate, seed):
    return seed + PLANTS.index(plant) * 100000 + SIZES.index(delta) * 1000 + replicate * 7


def instrument_label(rate_zero, rate_medium, rate_large, size_check_valid=True):
    if not size_check_valid or rate_zero > .1:
        return "blind"
    if rate_medium >= .8:
        return "sees"
    if rate_large >= .8:
        return "sees large only"
    return "blind"


def summarize(worlds, null_worlds, mode):
    if mode == "pilot":
        return dict(card="V4", state=states.instrument_state(True), execution_only=True,
                    worlds=len(worlds), scientific_primary=None,
                    world_seconds=[world["wall_seconds"] for world in worlds])
    if len(null_worlds) != 20:
        raise ValueError("V4 requires all 20 session-permuted null worlds")
    null_check = {name: dict(rejections=sum(world["readers"][name]["detected"] for world in null_worlds), worlds=20)
                  for name in READERS}
    curves, labels, primaries = [], {}, []
    for plant in PLANTS:
        rates = {}
        for delta in SIZES:
            selected = [world for world in worlds if world["cell"]["plant"] == plant and world["cell"]["delta"] == delta]
            if len(selected) not in (5, 10) or (delta in (0., .4) and len(selected) != 10):
                raise ValueError("incomplete V4 cell")
            for name in READERS:
                count = sum(world["readers"][name]["detected"] for world in selected)
                curves.append(dict(plant=plant, delta=delta, reader=name, detections=count, worlds=len(selected),
                                   rate=count / len(selected), interval95=wilson(count, len(selected))))
                rates[(name, delta)] = count / len(selected)
        for name in READERS:
            size_valid = null_check[name]["rejections"] <= 2
            labels[plant + ":" + name] = instrument_label(rates[name, 0.], rates[name, .4], rates[name, .8], size_valid)
        a = next(row for row in curves if row["plant"] == plant and row["reader"] == "R-both" and row["delta"] == .4)
        b = next(row for row in curves if row["plant"] == plant and row["reader"] == "R-both" and row["delta"] == 0.)
        from scipy.stats import norm
        effect = a["rate"] - b["rate"]
        interval = [a["interval95"][0] - b["interval95"][1], a["interval95"][1] - b["interval95"][0]]
        standard_error = (interval[1] - interval[0]) / (2 * 1.959963984540054)
        primaries.append(dict(plant=plant, estimate=effect,
                              interval95=interval, standard_error=standard_error,
                              p_value_approx=float(2 * norm.sf(abs(effect / standard_error))) if standard_error > 0 else None,
                              p_value_method="two-sided Wald approximation from conservative interval width; descriptive",
                              direction="positive", interval_method="conservative difference of Wilson world-recovery bounds"))
    return dict(card="V4", descriptive=True, state="blind" if any(labels[p + ":R-both"] == "blind" for p in ("taste_lexical", "habit")) else "positive",
                labels=labels, primary=primaries, curves=curves, null_size_check=null_check,
                asymptotic_reference="stipulated and size-checked; not asserted conservative after selection",
                clarifications=["Taste is mean offered-option projection, standardized within writer; no selected-option leakage.",
                    "Habit center and initial kernel are frozen writer base probabilities, not future realized means."],
                route="sees: descriptive personal panel candidate; blind: instrument limit, no FX1 admission; oracle-only detection calls for improved representation")


def execute(output: Path, inputs: dict, config: dict) -> dict:
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    mode = config.get("mode", "pilot")
    if mode not in ("pilot", "full"):
        raise ValueError("unknown V4 execution mode")
    seed = int(config.get("seed", 20261017)); sessions = read(inputs["sessions"])
    source_predictions = read(inputs["predictions"])
    base = {row["key"]: row["probabilities"]["B-pop"] for row in source_predictions}
    geometry = make_geometry(sessions, read(inputs["records"]), np.load(inputs["vectors"], mmap_mode="r", allow_pickle=False), seed)
    write(output / "GEOMETRY.json", {key: geometry[key] for key in ("keys", "vocabulary_size", "lexical_explained", "mini_explained")})
    with (output / "GEOMETRY.npz").open("xb") as stream:
        np.savez_compressed(stream, **{key: geometry[key] for key in ("slices", "lexical", "mini", "basis", "menu_lexical", "menu_mini")})
    identity = input_hashes(inputs); worlds, null_worlds = [], []
    def run_cell(plant, delta, replicate, permuted=False):
        started = time.perf_counter(); cell = dict(plant=plant, delta=delta, replicate=replicate, permuted=permuted)
        name = ("null-" if permuted else "") + plant + "-" + str(delta) + "-" + str(replicate)
        folder = output / "worlds" / name
        generated, trace, oracle = construct(sessions, base, geometry, plant, delta,
            cell_seed(plant, delta, replicate, seed) + (900000 if permuted else 0))
        if permuted:
            names = np.random.default_rng(seed + 700000 + replicate).permutation([session["writer"] for session in generated])
            for session, writer in zip(generated, names):
                session["writer"] = str(writer)
                for row in session["rows"]:
                    row["writer"] = str(writer)
        write(folder / "CONSTRUCTION.json", dict(cell=cell, rows=trace, oracle=oracle))
        saved = read_world(generated, trace, oracle, geometry, base, config)
        write(folder / "READERS.json", saved)
        result = dict(cell=cell, **score_world(saved, seed), wall_seconds=time.perf_counter() - started,
                      input_hashes=identity, construction_sha256=sha256(folder / "CONSTRUCTION.json"), readers_sha256=sha256(folder / "READERS.json"))
        write(folder / "RESULT.json", result)
        return result
    # Pilot worlds are fixed .4, replicate zero, one for each plant. Full mode
    # recomputes these same fixed cells unless a future reviewed reuse is added.
    if mode == "pilot":
        for plant in PLANTS:
            worlds.append(run_cell(plant, .4, 0))
    else:
        if "pilot_summary" not in inputs:
            raise ValueError("full V4 requires a frozen measured pilot summary")
        pilot = read(inputs["pilot_summary"])
        if not pilot.get("execution_only") or pilot.get("mode") != "pilot":
            raise ValueError("invalid V4 pilot receipt")
        for key in ("sessions", "predictions", "records", "vectors"):
            if pilot["input_hashes"].get(key) != identity[key]:
                raise ValueError("V4 pilot and full sources differ")
        for plant in PLANTS:
            for delta in SIZES:
                first = [run_cell(plant, delta, replicate) for replicate in range(5)]
                worlds.extend(first)
                detections = sum(world["readers"]["R-both"]["detected"] for world in first)
                if delta in (0., .4) or detections in (2, 3):
                    worlds.extend(run_cell(plant, delta, replicate) for replicate in range(5, 10))
        null_worlds = [run_cell("taste_lexical", 0., replicate, True) for replicate in range(20)]
    write(output / "WORLDS.json", worlds); write(output / "NULL_WORLDS.json", null_worlds)
    report = summarize(worlds, null_worlds, mode)
    report.update(mode=mode, input_hashes=identity,
                  projected_full_seconds=max(world["wall_seconds"] for world in worlds) * 140 if mode == "pilot" else None,
                  intermediate_hashes={name: sha256(output / name) for name in ("GEOMETRY.json", "GEOMETRY.npz", "WORLDS.json", "NULL_WORLDS.json")})
    write(output / "SUMMARY.json", report)
    return report


def verify(output: Path, inputs: dict, config: dict) -> dict:
    output = Path(output); report = read(output / "SUMMARY.json")
    assert_equal(report["input_hashes"], input_hashes(inputs))
    for name, expected in report["intermediate_hashes"].items():
        if sha256(output / name) != expected:
            raise ValueError("V4 intermediate changed")
    worlds, null_worlds = read(output / "WORLDS.json"), read(output / "NULL_WORLDS.json")
    for world in worlds + null_worlds:
        cell = world["cell"]; name = ("null-" if cell["permuted"] else "") + cell["plant"] + "-" + str(cell["delta"]) + "-" + str(cell["replicate"])
        folder = output / "worlds" / name
        if sha256(folder / "CONSTRUCTION.json") != world["construction_sha256"] or sha256(folder / "READERS.json") != world["readers_sha256"]:
            raise ValueError("V4 retained world changed")
        actual = score_world(read(folder / "READERS.json"), int(config.get("seed", 20261017)))
        assert_equal(actual, {key: world[key] for key in actual})
    actual = summarize(worlds, null_worlds, report["mode"])
    assert_equal(actual, {key: report[key] for key in actual})
    return dict(verified=True, primary_recomputed=actual.get("primary"), state=actual["state"], execution_only=report["mode"] == "pilot")
