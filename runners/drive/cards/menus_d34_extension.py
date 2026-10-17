"""D34 conditional extension on P4's completed held-out predictions.

The P4 reader-feature rival is the exact saved augmented design. Its forecasts
are reproduced before any residual statistic. Phase 0 planted-control power is
not transferred to the stronger reader; absent matched P4 worlds a null extension
stays undetermined as a mechanism verdict, while its CI state still routes.
"""
from __future__ import annotations

import math
import time
from pathlib import Path
import joblib
import numpy as np
from scipy.special import softmax

from . import states_v2 as states
from . import menus_d34 as primary
from . import menus_d34_stats as stats
from .menus_io import assert_equal, input_hashes, read, sha256, write


def saved_inputs(inputs):
    primary.bind_completed_artifact(inputs["d34_completion"], inputs["d34_summary"])
    primary.bind_completed_artifact(inputs["p4_completion"], inputs["p4_summary"])
    d34_report = read(inputs["d34_summary"]); p4_report = read(inputs["p4_summary"])
    if d34_report["state"] not in ("positive", "marginal"):
        raise ValueError("D34 extension requires a positive or marginal primary")
    if p4_report.get("execution_only") or p4_report.get("card") != "P4":
        raise ValueError("completed P4 full forecasts required")
    for key in ("sessions", "records", "vectors"):
        if d34_report["input_hashes"][key] != p4_report["input_hashes"][key]:
            raise ValueError("D34/P4 source identities differ")
    d34_root = Path(inputs["d34_summary"]).parent; p4_root = Path(inputs["p4_summary"]).parent; pins = {}
    for folder, report, names in ((d34_root, d34_report, ("FEATURES.npz", "ROWS.json")),
            (p4_root, p4_report, ("FEATURES.npz", "FEATURE_ROWS.json", "PREDICTIONS.json", "FITS.json"))):
        for name in names:
            path = folder / name; digest = sha256(path)
            if digest != report["intermediate_hashes"][name]:
                raise ValueError("completed primary intermediate changed")
            pins[str(path)] = digest
    rows = read(d34_root / "ROWS.json"); index = {row["key"]: i for i, row in enumerate(rows)}
    with np.load(d34_root / "FEATURES.npz", allow_pickle=False) as arrays:
        features = {name: arrays[name] for name in ("content", "state")}
    p4_rows = read(p4_root / "FEATURE_ROWS.json"); p4_index = {row["key"]: i for i, row in enumerate(p4_rows)}
    with np.load(p4_root / "FEATURES.npz", allow_pickle=False) as arrays:
        base, scalars, embeddings = [arrays[name] for name in ("backbone", "scalars", "embeddings")]
    fits = read(p4_root / "FITS.json"); predictions = read(p4_root / "PREDICTIONS.json")
    if len({row["key"] for row in predictions}) != len(predictions):
        raise ValueError("duplicate P4 prediction")
    forecasts = primary.load_predictions(p4_root / "PREDICTIONS.json", model="content")
    prediction_map = {row["key"]: row for row in predictions}
    dimensions = max(fit["pca_dimensions"] for fit in fits)
    reader = np.zeros((len(rows), base.shape[1] + scalars.shape[1] + dimensions)); rebuilt = set()
    for fit in fits:
        path = p4_root / "primary" / (fit["writer"] + ".joblib")
        if sha256(path) != fit["model_sha256"]:
            raise ValueError("P4 fitted model changed")
        pins[str(path)] = fit["model_sha256"]; model = joblib.load(path)
        keys = fit["test_keys"]
        if any(key not in forecasts or key not in index or rows[index[key]]["writer"] != fit["writer"] for key in keys):
            raise ValueError("P4 fitted test support differs")
        ids = [p4_index[key] for key in keys]; out_ids = [index[key] for key in keys]
        content = np.c_[scalars[ids], model["projection"].transform(embeddings[ids])]
        design = np.c_[base[ids], (content - model["scalar_mean"]) / model["scalar_sd"]]
        reader[np.ix_(out_ids, np.arange(design.shape[1]))] = design
        if model["selected_booster"] is None:
            logits = design @ model["logistic_weights"]
        else:
            estimator = model["selected_booster"]; probability = np.zeros((len(ids), 4))
            probability[:, estimator.classes_.astype(int)] = estimator.predict_proba(design)
            logits = np.log(np.maximum(probability, 1e-15))
        computed = softmax(logits, axis=1)
        expected = np.asarray([prediction_map[key]["probabilities"]["content"] for key in keys])
        if not np.allclose(computed, expected, rtol=0, atol=1e-12):
            raise ValueError("P4 actual augmented-design forecast replay differs")
        if rebuilt.intersection(keys):
            raise ValueError("repeated fitted test key")
        rebuilt.update(keys)
    if rebuilt != set(forecasts):
        raise ValueError("unreconstructed P4 forecasts")
    features["reader"] = reader
    return rows, features, forecasts, pins, d34_report


def result_from_metrics(metrics, config):
    result = stats.summarize(metrics["observed"], config); shuffle = stats.summarize(metrics["shuffle"], config)
    return dict(card="D34.extension", descriptive=True, **result, verdict=stats.verdict(result, 0),
        outcome_shuffle_control=shuffle, daily_screen_flag=shuffle["state"] == "positive",
        matched_p4_positive_control_power="not established; Phase 0 world recovery is not transferred to P4 residuals",
        reader_variant="exact P4 fitted augmented input design, reconstructed from hashed fitted models",
        conditional_extension=True, route="Extension CI state determines the next move; a null lacks matched P4 residual-power calibration")


def execute(output: Path, inputs: dict, config: dict) -> dict:
    output = Path(output); output.mkdir(parents=True, exist_ok=True); started = time.perf_counter()
    if config.get("permutations", 1000) != 1000:
        raise ValueError("1,000 frozen residual permutations required")
    rows, features, forecasts, pins, d34_report = saved_inputs(inputs)
    binding = dict(inputs=input_hashes(inputs), source_pins=pins, config=config, code_sha256=sha256(__file__))
    if (output / "BINDING.json").exists():
        assert_equal(read(output / "BINDING.json"), binding)
    else:
        write(output / "BINDING.json", binding)
    completed = 0; total = 2 * len({row["writer"] for row in rows if row["key"] in forecasts})
    def tick():
        nonlocal completed
        completed += 1
        if completed >= max(1, math.ceil(total / 10)) and not (output / "FIRST_TENTH.json").exists():
            write(output / "FIRST_TENTH.json", dict(completed_writer_units=completed, total_writer_units=total,
                  projected_seconds=(time.perf_counter() - started) * total / completed))
        return (output / "YIELD_REQUEST.json").exists()
    metrics = {}; exclusions = {}
    for name, shuffle in (("observed", False), ("shuffle", True)):
        if (output / "YIELD_REQUEST.json").exists():
            return dict(status="yielded", card="D34.extension", completed_writer_units=completed)
        value, support = primary.dataset_metrics(rows, features, forecasts, config, output / "units" / name,
            dict(run=binding, dataset=name), tick, shuffle)
        if value is None:
            return dict(status="yielded", card="D34.extension", completed_writer_units=completed)
        metrics[name] = value; exclusions[name] = support
    write(output / "WRITER_METRICS.json", metrics); write(output / "SUPPORT.json", exclusions)
    with (output / "FEATURES.npz").open("xb") as stream:
        np.savez_compressed(stream, **features)
    result = result_from_metrics(metrics, config)
    result.update(input_hashes=input_hashes(inputs), elapsed_seconds=time.perf_counter() - started,
        parent_state=d34_report["state"], parent_positive_control_detections=d34_report.get("positive_control_detections"),
        intermediate_hashes={name: sha256(output / name) for name in ("BINDING.json", "WRITER_METRICS.json", "SUPPORT.json", "FEATURES.npz")})
    write(output / "SUMMARY.json", result)
    return result


def verify(output: Path, inputs: dict, config: dict) -> dict:
    output = Path(output); result = read(output / "SUMMARY.json"); binding = read(output / "BINDING.json")
    assert_equal(input_hashes(inputs), result["input_hashes"])
    for path, digest in binding["source_pins"].items():
        if sha256(path) != digest:
            raise ValueError("D34 extension source changed")
    for name, digest in result["intermediate_hashes"].items():
        if sha256(output / name) != digest:
            raise ValueError("D34 extension intermediate changed")
    actual = result_from_metrics(read(output / "WRITER_METRICS.json"), config)
    assert_equal(actual, {key: result[key] for key in actual})
    return dict(verified=True, primary_recomputed=actual["primary"], state=actual["state"], verdict=actual["verdict"])
