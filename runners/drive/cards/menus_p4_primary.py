"""P4 primary-only full route; immutable recipient checkpoints permit yielding.

The separate extension route computes writer offsets only after this primary
lands positive or marginal. The frozen P4 pilot is preserved. Primary model
recipes, recipient chronology and the shuffled-outcome control match that pilot.
"""
from __future__ import annotations

import copy
import math
import time
from pathlib import Path
import joblib
import numpy as np
from scipy.special import softmax
from scipy.stats import norm
from sklearn.decomposition import PCA
from sklearn.ensemble import HistGradientBoostingClassifier

from . import menus_p4 as pilot
from . import states
from .menus_io import assert_equal, canonical, input_hashes, read, sha256, write


def fit_recipient(split, rows, base, scalars, embeddings, index, config):
    def indices(group):
        return np.asarray([index[row["key"]] for session in group for row in session["rows"]], int)
    train, own, cal, test = [indices(split[name]) for name in ("train", "own_train", "calibration", "test")]
    y = np.asarray([pilot.ACTIONS.index(row["handling"]) for row in rows]); cal_rows = [rows[i] for i in cal]
    dimensions = min(int(config.get("pca_dimensions", 16)), len(train) - 1, embeddings.shape[1])
    projection = PCA(n_components=dimensions, svd_solver="randomized", random_state=int(config.get("seed", 20261017)))
    projection.fit(embeddings[train])
    content = np.c_[scalars, projection.transform(embeddings)]
    mean, sd = pilot.standardize_fit(content[train]); augmented = np.c_[base, (content - mean) / sd]
    baseline_weights = pilot.global_fit(base[train], y[train])
    _, baseline_penalty, baseline_offset = pilot.select_offset(base[own] @ baseline_weights, y[own], base[cal] @ baseline_weights, y[cal], cal_rows)
    baseline = softmax(base[test] @ baseline_weights + baseline_offset, axis=1)
    logistic_weights = pilot.global_fit(augmented[train], y[train])
    candidates = [(pilot.session_mean(pilot.brier(softmax(augmented[cal] @ logistic_weights, axis=1), y[cal]), cal_rows), "logistic", None)]
    for leaves in (7, 15):
        model = HistGradientBoostingClassifier(max_iter=100, learning_rate=.1, max_leaf_nodes=leaves,
                    l2_regularization=1., early_stopping=False, random_state=int(config.get("seed", 20261017)))
        model.fit(augmented[train], y[train])
        score = pilot.session_mean(pilot.brier(pilot.forest_probabilities(model, augmented[cal]), y[cal]), cal_rows)
        candidates.append((score, "boosted_" + str(leaves), model))
    _, selected, model = min(candidates, key=lambda item: (item[0], item[1]))
    logits = augmented @ logistic_weights if model is None else np.log(np.maximum(pilot.forest_probabilities(model, augmented), 1e-15))
    probability = softmax(logits[test], axis=1)
    predictions = [dict(key=rows[i]["key"], writer=rows[i]["writer"], session=rows[i]["session"], prompt=rows[i]["prompt"],
        truth=rows[i]["handling"], probabilities={"backbone": baseline[j].tolist(), "content": probability[j].tolist()}) for j, i in enumerate(test)]
    receipt = dict(writer=split["writer"], cutoff=split["cutoff"], test_cutoff=split["test_cutoff"],
        train_sessions=[s["session"] for s in split["train"]], calibration_sessions=[s["session"] for s in split["calibration"]],
        test_sessions=[s["session"] for s in split["test"]],
        train_keys=[rows[i]["key"] for i in train], own_train_keys=[rows[i]["key"] for i in own],
        calibration_keys=[rows[i]["key"] for i in cal], test_keys=[rows[i]["key"] for i in test],
        excluded_future_training=split["excluded_future_training"], excluded_overlapping_calibration=split["excluded_overlapping_calibration"],
        pca_fit_keys=[rows[i]["key"] for i in train], pca_dimensions=dimensions, selected=selected,
        calibration_scores={name: score for score, name, _ in candidates}, baseline_penalty=baseline_penalty,
        refit_on_calibration=False, writer_extension_computed=False)
    model = dict(selected=selected, selected_booster=model, baseline_weights=baseline_weights, baseline_offset=baseline_offset,
                 logistic_weights=logistic_weights, scalar_mean=mean, scalar_sd=sd, projection=projection)
    return predictions, receipt, model


def summarize(predictions, config, comparator="backbone", forecast="content"):
    groups = {}
    for row in predictions:
        target = [pilot.ACTIONS.index(row["truth"])]
        baseline = pilot.brier([row["probabilities"][comparator]], target)[0]
        fitted = pilot.brier([row["probabilities"][forecast]], target)[0]
        groups.setdefault((row["writer"], row["session"]), []).append([baseline - fitted, baseline, fitted])
    keys = sorted(groups); writers = sorted({writer for writer, _ in keys})
    if len(writers) < 2:
        return dict(state="invalid", primary=None, reason="fewer than two scored writers", writers=len(writers), decisions=len(predictions))
    values = np.asarray([np.mean(groups[key], axis=0) for key in keys])
    units = [values[[key[0] == writer for key in keys]] for writer in writers]
    rng = np.random.default_rng(int(config.get("seed", 20261017))); draws = []
    for _ in range(int(config.get("bootstrap_draws", 2000))):
        sample = rng.integers(len(units), size=len(units))
        draws.append(np.concatenate([units[i] for i in sample]).mean(0)[0])
    effect = float(values[:, 0].mean()); interval = np.quantile(draws, [.025, .975]).tolist(); se = float(np.std(draws, ddof=1))
    pvalue = float(2 * norm.sf(abs(effect / se))) if se > 0 else 1. if effect == 0 else None
    return dict(state=states.classify(effect, *interval), primary=dict(estimate=effect, interval95=interval,
                standard_error=se, p_value_approx=pvalue, p_value_method="two-sided Wald approximation from writer-bootstrap standard error; descriptive",
                direction="positive", useful_margin=.01, reaches_useful_margin=effect >= .01),
                decisions=len(predictions), sessions=len(keys), writers=len(writers),
                mean_half_brier={comparator: float(values[:, 1].mean()), forecast: float(values[:, 2].mean())},
                weighting="equal session weights; writer-cluster bootstrap; conditional on fitted forecasts")


def load_features(inputs):
    if "p8" in inputs:
        raise ValueError("P8 producer score remains uncalibrated")
    sessions = read(inputs["sessions"])
    for session in sessions:
        for row in session["rows"]:
            row["session_end"] = session["end_at"]
    vectors = np.load(inputs["vectors"], mmap_mode="r", allow_pickle=False)
    records = read(inputs["records"])
    rows, base, scalar, embedding = pilot.prefix_features(sessions, records, vectors)
    shuffled = copy.deepcopy(sessions); rng = np.random.default_rng(int(inputs.get("_seed", 20261017)) + 701)
    for session in sorted(shuffled, key=lambda row: row["session"]):
        labels = rng.permutation([row["handling"] for row in session["rows"]])
        for row, label in zip(session["rows"], labels):
            row["handling"] = str(label)
    changed_rows, changed_base, changed_scalar, _ = pilot.prefix_features(shuffled, records, vectors)
    return sessions, rows, base, scalar, embedding, shuffled, changed_rows, changed_base, changed_scalar


def execute(output: Path, inputs: dict, config: dict) -> dict:
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter(); hashes = input_hashes(inputs)
    binding = dict(inputs=hashes, config=config, code_sha256=sha256(__file__))
    if (output / "BINDING.json").exists():
        assert_equal(read(output / "BINDING.json"), binding)
    else:
        write(output / "BINDING.json", binding)
    if not {"pilot_summary", "pilot_plan"} <= inputs.keys():
        raise ValueError("P4 full requires the measured one-recipient pilot summary and frozen plan")
    receipt = read(inputs["pilot_summary"])
    if not receipt.get("execution_only") or receipt.get("computed_recipients") != 1:
        raise ValueError("P4 pilot did not complete its fixed recipient")
    for key in ("sessions", "records", "vectors"):
        if receipt["input_hashes"].get(key) != hashes[key]:
            raise ValueError("P4 pilot/full sources differ")
    pilot_config = read(inputs["pilot_plan"])["config"]
    for key, default in (("seed", 20261017), ("pca_dimensions", 16)):
        if config.get(key, default) != pilot_config.get(key, default):
            raise ValueError("P4 pilot/full model configuration differs")
    sessions, rows, base, scalars, embeddings, shuffled, changed_rows, changed_base, changed_scalar = load_features(dict(inputs, _seed=int(config.get("seed", 20261017))))
    row_index = {row["key"]: i for i, row in enumerate(rows)}
    splits, excluded = pilot.chronological_partitions(sessions); changed_splits, _ = pilot.chronological_partitions(shuffled)
    eligible = []
    for writer in sorted(splits):
        split = pilot.recipient_split(writer, splits)
        if split["reason"] is None and sum(len(session["rows"]) for session in split["train"]) >= 8:
            eligible.append(writer)
        else:
            excluded.append(dict(writer=writer, reason=split["reason"] or "fewer than 8 pooled fitting decisions"))
    feature_names = ("FEATURES.npz", "FEATURE_ROWS.json", "ELIGIBILITY.json")
    if (output / "FEATURE_MANIFEST.json").exists():
        for name, digest in read(output / "FEATURE_MANIFEST.json").items():
            if sha256(output / name) != digest:
                raise ValueError("P4 saved feature checkpoint changed")
    else:
        if any((output / name).exists() for name in feature_names):
            raise ValueError("incomplete feature checkpoint retained; owner review required")
        with (output / "FEATURES.npz").open("xb") as stream:
            np.savez_compressed(stream, backbone=base, scalars=scalars, embeddings=embeddings)
        write(output / "FEATURE_ROWS.json", [{key: row[key] for key in ("key", "writer", "session", "open_at", "resolved_at")} for row in rows])
        write(output / "ELIGIBILITY.json", dict(eligible_writers=eligible, exclusions=excluded))
        write(output / "FEATURE_MANIFEST.json", {name: sha256(output / name) for name in feature_names})
    predictions, control, fits, control_fits = [], [], [], []
    completed = 0
    for writer in eligible:
        if (output / "YIELD_REQUEST.json").exists():
            return dict(status="yielded", card="P4", completed_recipients=completed)
        for arm, current_splits, current_rows, current_base, current_scalar, destination, fit_destination in (
            ("primary", splits, rows, base, scalars, predictions, fits),
            ("shuffle", changed_splits, changed_rows, changed_base, changed_scalar, control, control_fits)):
            folder = output / arm; checkpoint = folder / (writer + ".json"); model_path = folder / (writer + ".joblib")
            if checkpoint.exists():
                if sha256(checkpoint) != read(folder / (writer + ".seal.json"))["sha256"]:
                    raise ValueError("P4 saved recipient checkpoint changed")
                saved = read(checkpoint); assert_equal(saved["binding"], binding)
                if sha256(model_path) != saved["fit"]["model_sha256"]:
                    raise ValueError("P4 saved recipient model changed")
            else:
                if model_path.exists():
                    raise ValueError("uncommitted recipient model retained; owner review required")
                split = pilot.recipient_split(writer, current_splits)
                predicted, fit, model = fit_recipient(split, current_rows, current_base, current_scalar, embeddings, row_index, config)
                folder.mkdir(parents=True, exist_ok=True); joblib.dump(model, model_path, compress=3)
                fit["model_sha256"] = sha256(model_path)
                saved = dict(binding=binding, predictions=predicted, fit=fit)
                write(checkpoint, saved)
                write(folder / (writer + ".seal.json"), dict(sha256=sha256(checkpoint)))
            destination.extend(saved["predictions"]); fit_destination.append(saved["fit"])
        completed += 1
        if completed >= max(1, math.ceil(.1 * len(eligible))) and not (output / "FIRST_TENTH.json").exists():
            elapsed = time.perf_counter() - started
            write(output / "FIRST_TENTH.json", dict(completed_recipients=completed, total_recipients=len(eligible),
                  elapsed_seconds=elapsed, projected_seconds=elapsed * len(eligible) / completed))
    if (output / "YIELD_REQUEST.json").exists():
        return dict(status="yielded", card="P4", completed_recipients=completed)
    write(output / "PREDICTIONS.json", predictions); write(output / "FITS.json", fits)
    write(output / "SHUFFLE_PREDICTIONS.json", control); write(output / "SHUFFLE_FITS.json", control_fits)
    report = dict(card="P4", descriptive=True, **summarize(predictions, config), shuffle_control=summarize(control, config),
        extension_computed=False, input_hashes=hashes, excluded_recipients=len(excluded), wall_seconds=time.perf_counter() - started,
        intermediate_hashes={name: sha256(output / name) for name in ("PREDICTIONS.json", "FITS.json", "SHUFFLE_PREDICTIONS.json", "SHUFFLE_FITS.json", "FEATURES.npz", "FEATURE_ROWS.json", "ELIGIBILITY.json", "FEATURE_MANIFEST.json", "BINDING.json")})
    write(output / "SUMMARY.json", report)
    return report


def verify(output: Path, inputs: dict, config: dict) -> dict:
    output = Path(output); report = read(output / "SUMMARY.json")
    assert_equal(report["input_hashes"], input_hashes(inputs))
    for name, expected in report["intermediate_hashes"].items():
        if sha256(output / name) != expected:
            raise ValueError("P4 primary intermediate changed")
    for arm, filename in (("primary", "FITS.json"), ("shuffle", "SHUFFLE_FITS.json")):
        for fit in read(output / filename):
            if sha256(output / arm / (fit["writer"] + ".joblib")) != fit["model_sha256"]:
                raise ValueError("P4 primary model changed")
    actual = summarize(read(output / "PREDICTIONS.json"), config)
    assert_equal(actual, {key: report[key] for key in actual})
    assert_equal(summarize(read(output / "SHUFFLE_PREDICTIONS.json"), config), report["shuffle_control"])
    return dict(verified=True, primary_recomputed=actual["primary"], state=actual["state"])
