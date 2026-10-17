"""D34 primary: persistent directions in Phase 0 handling residuals.

DESIGN CHECK: see menus_d34_stats for the exhaustive verdict derivation.
Representations fit on all offered suggestions from OTHER writers, without
outcomes. Each menu contributes its mean option projection before choice.
Acceptance means the frozen four-class reader's `accept` class, as in V4.
This route is the Phase 0 primary; P4's conditional extension is separate.
"""
from __future__ import annotations

import copy
import gzip
import hashlib
import json
import math
import time
from pathlib import Path
import numpy as np
from scipy.linalg import eigh

from . import states_v2 as states
from . import menus_d34_stats as stats
from .menus_io import assert_equal, input_hashes, read, sha256, write
from runners.stage14_midweek.baselines import matrix

ACTIONS = ("accept", "edit", "dismiss", "ignore")


def read_any(path):
    if str(path).endswith(".gz"):
        with gzip.open(path, "rt", encoding="utf8") as stream:
            return json.load(stream)
    return read(path)


def require_complete(path):
    receipt = read(path)
    if str(receipt.get("status", "")).upper() != "COMPLETE":
        raise ValueError("completed source required")
    return receipt


def bind_completed_artifact(completion, artifact):
    receipt = require_complete(completion)
    relative = Path(artifact).resolve().relative_to(Path(completion).resolve().parent).as_posix()
    outputs = {name.replace("\\", "/"): digest for name, digest in receipt.get("outputs", {}).items()}
    if outputs.get(relative) != sha256(artifact):
        raise ValueError("artifact is not bound by its completion receipt")


def load_predictions(path, model="B-mixlogit", format="ordinary"):
    source = read_any(path)
    if format == "v4":
        source = [dict(key=key, truth=ACTIONS[truth], writer=writer, probabilities={model: probability})
                  for key, truth, writer, probability in zip(source["keys"], source["truth"], source["writers"], source["predictions"]["R-Phase0"])]
    result = {}
    for row in source:
        probability = np.asarray(row["probabilities"][model], float)
        if probability.shape != (4,) or not np.isfinite(probability).all() or np.any(probability < 0) or not np.isclose(probability.sum(), 1, atol=1e-10, rtol=0):
            raise ValueError("invalid reader probability simplex")
        if row["key"] in result or row["truth"] not in ACTIONS:
            raise ValueError("duplicate or invalid forecast target")
        result[row["key"]] = dict(truth=row["truth"], probability=float(probability[0]), writer=row["writer"])
    return result


def representations(sessions, records, vectors, dimensions=16):
    rows = sorted((row for session in sessions for row in session["rows"]), key=lambda row: (row["open_at"], row["key"]))
    features = {row["key"]: row for row in records}; index = {row["key"]: i for i, row in enumerate(rows)}
    if len(index) != len(rows) or set(index) != set(features):
        raise ValueError("content/source support differs")
    writers = sorted({row["writer"] for row in rows}); option_ids = []; option_writers = []
    menu = []
    for row in rows:
        feature = features[row["key"]]
        if feature["writer"] != row["writer"] or feature["session"] != row["session"] or len(feature["options"]) != len(row["menu"]) or not row["menu"]:
            raise ValueError("menu representation identity differs")
        ids = feature["options"]; option_ids.extend(ids); option_writers.extend([row["writer"]] * len(ids))
        menu.append(np.asarray(vectors[ids], float).mean(axis=0))
    offered = np.asarray(vectors[option_ids], float); menu = np.asarray(menu); option_writers = np.asarray(option_writers)
    if not np.isfinite(offered).all() or offered.shape[1] < dimensions:
        raise ValueError("invalid or insufficient content dimensions")
    moments = {}
    for writer in writers:
        own = offered[option_writers == writer]
        moments[writer] = (len(own), own.sum(0), own.T @ own)
    content = np.zeros((len(rows), dimensions)); pca = {}
    reader = matrix(rows, False); state = []; last = {}
    for row in rows:
        elapsed = max(0., (row["open_at"] - row["session_time"]) / 1000)
        gap = max(0., (row["open_at"] - last.get(row["session"], row["session_time"])) / 1000)
        state.append([np.log1p(row["decision_index"]), np.log1p(elapsed), np.log1p(gap)])
        last[row["session"]] = row["open_at"]
    state = np.asarray(state); normalized_state = np.zeros_like(state); normalized_reader = np.zeros_like(reader)
    row_writers = np.asarray([row["writer"] for row in rows])
    for writer in writers:
        donors = [moments[name] for name in writers if name != writer]
        n = sum(moment[0] for moment in donors)
        if n <= dimensions:
            raise ValueError("insufficient other-writer options for frozen PCA")
        total = sum((moment[1] for moment in donors), np.zeros(offered.shape[1])); mean = total / n
        cross = sum((moment[2] for moment in donors), np.zeros((offered.shape[1], offered.shape[1])))
        covariance = (cross - n * np.outer(mean, mean)) / (n - 1)
        values, axes = eigh(covariance, subset_by_index=(covariance.shape[0] - dimensions, covariance.shape[0] - 1))
        axes = axes[:, ::-1]; values = values[::-1]
        signs = np.sign(axes[np.argmax(np.abs(axes), axis=0), np.arange(dimensions)]); axes *= signs
        mask = row_writers == writer; content[mask] = (menu[mask] - mean) @ axes
        pca[writer] = dict(mean=mean.tolist(), components=axes.T.tolist(), eigenvalues=values.tolist(),
                           training_options=n, excluded_writer=writer)
        for raw, normalized in ((state, normalized_state), (reader, normalized_reader)):
            center = raw[~mask].mean(0); sd = raw[~mask].std(0); sd[sd < 1e-12] = 1.
            normalized[mask] = (raw[mask] - center) / sd
    return rows, dict(content=content, state=normalized_state, reader=normalized_reader), pca


def dataset_metrics(rows, features, forecasts, config, checkpoint, binding, tick, shuffle=False, content_only=False):
    source_keys = {row["key"] for row in rows}
    if not set(forecasts) <= source_keys:
        raise ValueError("forecast key absent from source")
    rng = np.random.default_rng(int(config.get("seed", 20261017)) + 3491)
    metrics = {}; excluded = []
    for writer in sorted({row["writer"] for row in rows}):
        ids = [i for i, row in enumerate(rows) if row["writer"] == writer and row["key"] in forecasts]
        if len({rows[i]["session"] for i in ids}) < 2:
            excluded.append(dict(writer=writer, reason="fewer than two forecast sessions")); continue
        if any(forecasts[rows[i]["key"]]["writer"] != writer for i in ids):
            raise ValueError("forecast writer differs")
        truth = np.asarray([forecasts[rows[i]["key"]]["truth"] == "accept" for i in ids], float)
        if shuffle:
            truth = rng.permutation(truth)
        probabilities = np.asarray([forecasts[rows[i]["key"]]["probability"] for i in ids])
        token = hashlib.sha256(writer.encode()).hexdigest()[:20]; path = checkpoint / (token + ".json")
        if path.exists():
            if sha256(path) != read(path.with_suffix(".seal.json"))["sha256"]:
                raise ValueError("D34 writer checkpoint changed")
            saved = read(path); assert_equal(saved["binding"], binding)
        else:
            selected = {name: value[ids] for name, value in features.items() if not content_only or name == "content"}
            result = stats.writer_statistic(truth - probabilities, probabilities, [rows[i]["session"] for i in ids],
                [rows[i]["session_time"] for i in ids], selected, int(config.get("permutations", 1000)),
                int(config.get("seed", 20261017)) + int(hashlib.sha256(writer.encode()).hexdigest()[:8], 16))
            saved = dict(binding=binding, writer=writer, keys=[rows[i]["key"] for i in ids], metrics=result)
            write(path, saved); write(path.with_suffix(".seal.json"), dict(sha256=sha256(path)))
        metrics[writer] = saved["metrics"]
        if tick():
            return None, excluded
    return metrics, excluded


def execute(output: Path, inputs: dict, config: dict) -> dict:
    output = Path(output); output.mkdir(parents=True, exist_ok=True); started = time.perf_counter()
    if int(config.get("permutations", 1000)) != 1000 or int(config.get("dimensions", 16)) != 16:
        raise ValueError("D34 freezes 16 PCs and 1,000 residual permutations")
    bind_completed_artifact(inputs["prediction_completion"], inputs["predictions"])
    hashes = input_hashes(inputs); binding = dict(inputs=hashes, config=config, code_sha256=sha256(__file__), statistic_sha256=sha256(stats.__file__))
    if (output / "BINDING.json").exists():
        assert_equal(read(output / "BINDING.json"), binding)
    else:
        write(output / "BINDING.json", binding)
    sessions = read(inputs["sessions"]); forecasts = load_predictions(inputs["predictions"])
    source_truth = {row["key"]: row["handling"] for session in sessions for row in session["rows"]}
    if set(forecasts) != set(source_truth) or any(row["truth"] != source_truth[key] for key, row in forecasts.items()):
        raise ValueError("Phase 0 forecast target/support differs from source")
    if (output / "FEATURE_MANIFEST.json").exists():
        for name, digest in read(output / "FEATURE_MANIFEST.json").items():
            if sha256(output / name) != digest:
                raise ValueError("D34 feature checkpoint changed")
        rows = read(output / "ROWS.json")
        with np.load(output / "FEATURES.npz", allow_pickle=False) as arrays:
            features = {key: arrays[key] for key in arrays.files}
    else:
        rows, features, pca = representations(sessions, read(inputs["records"]), np.load(inputs["vectors"], mmap_mode="r", allow_pickle=False), 16)
        write(output / "ROWS.json", [{key: row[key] for key in ("key", "writer", "session", "session_time")} for row in rows])
        write(output / "PCA.json", pca)
        with (output / "FEATURES.npz").open("xb") as stream:
            np.savez_compressed(stream, **features)
        write(output / "FEATURE_MANIFEST.json", {name: sha256(output / name) for name in ("ROWS.json", "PCA.json", "FEATURES.npz")})
    controls = read(inputs["positive_controls"])
    if len(controls) != 5 or [item["replicate"] for item in controls] != list(range(5)):
        raise ValueError("D34 requires fixed first five taste worlds at .4")
    source_pins = {}; control_forecasts = []
    for item in controls:
        require_complete(item["completion"])
        bind_completed_artifact(item["completion"], item["predictions"])
        bind_completed_artifact(item["completion"], item["result"])
        for key in ("predictions", "result", "completion"):
            digest = sha256(item[key]); source_pins[item[key]] = digest
            if item["sha256"][key] != digest:
                raise ValueError("planted world source changed")
        cell = read_any(item["result"])["cell"]
        if cell["replicate"] != item["replicate"] or cell["delta"] != .4 or cell.get("effect", cell.get("plant")) not in ("content", "taste_lexical"):
            raise ValueError("wrong planted control cell")
        control_forecasts.append(load_predictions(item["predictions"], format=item.get("format", "ordinary")))
    if (output / "SOURCE_PINS.json").exists():
        assert_equal(read(output / "SOURCE_PINS.json"), source_pins)
    else:
        write(output / "SOURCE_PINS.json", source_pins)
    total_units = 7 * len({row["writer"] for row in rows}); completed = 0
    def tick():
        nonlocal completed
        completed += 1
        if completed >= max(1, math.ceil(total_units / 10)) and not (output / "FIRST_TENTH.json").exists():
            elapsed = time.perf_counter() - started
            write(output / "FIRST_TENTH.json", dict(completed_writer_units=completed, total_writer_units=total_units,
                  projected_seconds=elapsed * total_units / completed))
        return (output / "YIELD_REQUEST.json").exists()
    if (output / "YIELD_REQUEST.json").exists():
        return dict(status="yielded", card="D34", completed_writer_units=0)
    all_metrics = {}; support = {}
    for name, predictions, shuffle, content_only in [("observed", forecasts, False, False), ("shuffle", forecasts, True, False)] + [
            ("control_" + str(i), predicted, False, True) for i, predicted in enumerate(control_forecasts)]:
        unit_binding = dict(run=binding, dataset=name)
        metrics, exclusions = dataset_metrics(rows, features, predictions, config, output / "units" / name, unit_binding, tick, shuffle, content_only)
        if metrics is None:
            return dict(status="yielded", card="D34", completed_writer_units=completed)
        all_metrics[name] = metrics; support[name] = exclusions
    write(output / "WRITER_METRICS.json", all_metrics); write(output / "SUPPORT.json", support)
    result = report_from_metrics(all_metrics, config)
    result.update(card="D34", descriptive=True, input_hashes=hashes, elapsed_seconds=time.perf_counter() - started,
        positive_control_source=[item.get("format", "ordinary") for item in controls],
        centering="session-center residuals and features separately before their product; menu mean predecision PCs fit on other writers",
        zero_direction_policy="zero-length session vectors contribute zero alignment; unsupported held-last-session sign tests excluded and counted",
        extension_run=False, extension="same contrast with completed P4 forecasts; conditional on positive/marginal primary",
        route="HIDDEN GOAL: descriptive unexplained-direction probe; NOISE AT THIS POWER: residual noise bands; other verdicts retain rivals or insufficient power",
        intermediate_hashes={name: sha256(output / name) for name in ("WRITER_METRICS.json", "SUPPORT.json", "FEATURE_MANIFEST.json", "ROWS.json", "PCA.json", "FEATURES.npz", "SOURCE_PINS.json", "BINDING.json")})
    write(output / "SUMMARY.json", result)
    return result


def report_from_metrics(metrics, config):
    primary = stats.summarize(metrics["observed"], config); shuffle = stats.summarize(metrics["shuffle"], config)
    controls = [stats.summarize(metrics["control_" + str(i)], config) for i in range(5)]
    detected = sum(item["state"] == "positive" for item in controls)
    return dict(**primary, verdict=stats.verdict(primary, detected), outcome_shuffle_control=shuffle,
                positive_controls=controls, positive_control_detections=detected,
                daily_screen_flag=shuffle["state"] == "positive", controls_required=5)


def verify(output: Path, inputs: dict, config: dict) -> dict:
    output = Path(output); result = read(output / "SUMMARY.json")
    assert_equal(input_hashes(inputs), result["input_hashes"])
    for name, digest in result["intermediate_hashes"].items():
        if sha256(output / name) != digest:
            raise ValueError("D34 saved intermediate changed")
    for path, digest in read(output / "SOURCE_PINS.json").items():
        if sha256(path) != digest:
            raise ValueError("D34 control source changed")
    metrics = read(output / "WRITER_METRICS.json")
    for dataset in metrics.values():
        for writer in dataset.values():
            for arm in writer["arms"].values():
                if not np.isclose(float(stats.pair_cosine(arm["session_vectors"])), arm["observed"], atol=1e-12, rtol=0):
                    raise ValueError("D34 observed direction statistic differs")
    actual = report_from_metrics(metrics, config)
    assert_equal(actual, {key: result[key] for key in actual})
    return dict(verified=True, primary_recomputed=actual["primary"], state=actual["state"], verdict=actual["verdict"])
