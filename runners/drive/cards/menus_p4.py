"""P4/D1 recipient-specific chronological free-feature forecasts.

The Phase 0 feature recipe is retained; models and preprocessing fit only on
declared training sessions ending before the recipient's first calibration.
Calibration chooses models/penalties, never supplies fitted outcomes. Scored
sessions retain fixed parameters while lawful resolved prefix covariates update.
Every alternative receives the same scoring rows and session weights.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import json
import copy
import joblib
import time
import numpy as np
from scipy.special import softmax
from sklearn.decomposition import PCA
from sklearn.ensemble import HistGradientBoostingClassifier

from runners.stage14_midweek.baselines import global_fit, intercept_fit
from . import states
from .menus_io import assert_equal, input_hashes, read, sha256, write

ACTIONS = ("accept", "edit", "dismiss", "ignore")
PENALTIES = (.01, .1, 1., 10.)


def chronological_partitions(sessions):
    grouped = defaultdict(list)
    for session in sessions:
        if session["end_at"] < session["timestamp"]:
            raise ValueError("negative session duration")
        grouped[session["writer"]].append(session)
    splits, excluded = {}, []
    for writer, group in sorted(grouped.items()):
        group.sort(key=lambda row: (row["timestamp"], row["session"]))
        a, b = int(.6 * len(group)), int(.8 * len(group))
        if a < 3 or b - a < 1 or len(group) - b < 1:
            excluded.append(dict(writer=writer, reason="fewer than 3/1/1 sessions"))
        else:
            splits[writer] = dict(train=group[:a], calibration=group[a:b], test=group[b:])
    return splits, excluded


def recipient_split(writer, splits):
    own = splits[writer]
    cutoff = min(session["timestamp"] for session in own["calibration"])
    test_cutoff = min(session["timestamp"] for session in own["test"])
    # This selection deliberately reads no row outcomes.
    declared = [session for group in splits.values() for session in group["train"]]
    allowed = [session for session in declared if session["end_at"] < cutoff]
    overlap = [session["session"] for session in declared if session["end_at"] >= cutoff]
    calibration = [session for session in own["calibration"] if session["end_at"] < test_cutoff]
    removed_calibration = [session["session"] for session in own["calibration"] if session["end_at"] >= test_cutoff]
    own_train = [session for session in allowed if session["writer"] == writer]
    reason = None
    if len(own_train) < 3 or len(calibration) < 1 or len(own["test"]) < 1:
        reason = "chronology leaves fewer than 3/1/1 sessions"
    elif any(not any(session["rows"] for session in group) for group in (allowed, own_train, calibration, own["test"])):
        reason = "empty usable train/own/calibration/test decision partition"
    return dict(writer=writer, cutoff=cutoff, test_cutoff=test_cutoff, train=allowed,
                own_train=own_train, calibration=calibration, test=own["test"],
                excluded_future_training=sorted(overlap), excluded_overlapping_calibration=sorted(removed_calibration),
                reason=reason)


def prefix_features(sessions, records, vectors, p8_rows=None):
    features = {row["key"]: row for row in records}
    probability = defaultdict(list)
    for row in p8_rows or []:
        probability[row["key"]].append(row)
    rows = sorted((row for session in sessions for row in session["rows"]), key=lambda row: (row["open_at"], row["key"]))
    if len({row["key"] for row in rows}) != len(rows) or set(features) != {row["key"] for row in rows}:
        raise ValueError("content/decision support mismatch")
    history = defaultdict(list); last_request = {}
    base, scalar, embedding = [], [], []
    for row in rows:
        prior = [p for p in history[row["writer"]] if p["resolved_at"] <= row["open_at"]
                 and (p["session"] == row["session"] or p["session_end"] < row["session_time"])]
        previous = prior[-1]["handling"] if prior else None
        context_words = set(row["document"][-1200:].lower().split())
        overlap = max((len(context_words & set(text.lower().split())) / max(1, len(set(text.lower().split()))) for text in row["menu"]), default=0)
        mean_length = np.mean([len(text) for text in row["menu"]])
        base.append([1., len(row["menu"]) / 10, np.log1p(mean_length) / 8, overlap,
                     np.log1p(row["decision_index"]) / 10] + [float(previous == action) for action in ACTIONS])
        feature = features[row["key"]]
        if feature["writer"] != row["writer"] or feature["session"] != row["session"] or len(feature["options"]) != len(row["menu"]):
            raise ValueError("feature identity differs")
        option_vectors = np.asarray(vectors[feature["options"]], float)
        embedding.append(np.r_[vectors[feature["context"]], option_vectors.mean(0)])
        cosine = np.asarray(feature["cosine"], float); sc = np.asarray(feature["scalars"], float)
        if sc.shape != (len(cosine), 4):
            raise ValueError("invalid scalar features")
        aggregate = np.r_[sc.mean(0), sc.std(0), sc.min(0), sc.max(0),
                          cosine.mean(), cosine.std(), cosine.min(), cosine.max()]
        # First five slots make position explicit without reading the selected slot.
        slots = np.zeros((5, 6))
        for i in range(min(5, len(cosine))):
            slots[i] = [1., cosine[i], *sc[i]]
        elapsed = max(0., (row["open_at"] - row["session_time"]) / 1000)
        elapsed_since_request = max(0., (row["open_at"] - last_request.get(row["session"], row["session_time"])) / 1000)
        recent = prior[-5:]
        accepts = np.mean([p["handling"] == "accept" for p in recent]) if recent else 0.
        logged = probability.get(row["key"], [])
        log_values = np.asarray([p["log_positive_score"] for p in logged if p["log_positive_score"] is not None], float)
        model_pref = [float(len(log_values) != len(row["menu"]))]
        model_pref += [float(log_values.mean()), float(log_values.std()), float(log_values.max())] if len(log_values) else [0., 0., 0.]
        scalar.append(np.r_[aggregate, slots.ravel(), np.log1p(elapsed), np.log1p(elapsed_since_request),
                            accepts, np.log1p(mean_length), max(0., 600 - elapsed) / 600,
                            float(elapsed >= 600), model_pref])
        last_request[row["session"]] = row["open_at"]
        history[row["writer"]].append(row)
    return rows, np.asarray(base), np.asarray(scalar), np.asarray(embedding)


def standardize_fit(values):
    mean, std = values.mean(0), values.std(0)
    return mean, np.where(std < 1e-10, 1., std)


def brier(probabilities, truth):
    p = np.asarray(probabilities, float); y = np.asarray(truth, int)
    if p.shape != (len(y), 4) or not np.isfinite(p).all() or np.any(p < 0) or not np.allclose(p.sum(1), 1, atol=1e-10):
        raise ValueError("invalid forecast")
    return .5 * np.sum((p - np.eye(4)[y]) ** 2, axis=1)


def session_mean(values, rows):
    grouped = defaultdict(list)
    for value, row in zip(values, rows):
        grouped[row["session"]].append(float(value))
    if not grouped:
        raise ValueError("empty scored sessions")
    return float(np.mean([np.mean(grouped[key]) for key in sorted(grouped)]))


def forest_probabilities(model, values):
    out = np.zeros((len(values), 4)); out[:, model.classes_.astype(int)] = model.predict_proba(values)
    return out


def select_offset(train_logits, train_truth, calibration_logits, calibration_truth, calibration_rows):
    candidates = []
    for penalty in PENALTIES:
        offset = intercept_fit(train_logits, train_truth, np.ones(len(train_truth)), penalty)
        score = session_mean(brier(softmax(calibration_logits + offset, axis=1), calibration_truth), calibration_rows)
        candidates.append((score, penalty, offset))
    return min(candidates, key=lambda item: (item[0], item[1]))


def fit_recipient(split, rows, base, scalars, embeddings, index, config):
    def indices(group):
        return np.asarray([index[row["key"]] for session in group for row in session["rows"]], int)
    train, own, cal, test = [indices(split[name]) for name in ("train", "own_train", "calibration", "test")]
    if len(train) < 8 or not all(len(ids) for ids in (own, cal, test)):
        raise ValueError("insufficient usable fitting decisions")
    y = np.asarray([ACTIONS.index(row["handling"]) for row in rows]); calibration_rows = [rows[i] for i in cal]
    # Fit preprocessing on recipient-eligible training rows, never all embeddings.
    dimensions = min(int(config.get("pca_dimensions", 16)), len(train) - 1, embeddings.shape[1])
    projection = PCA(n_components=dimensions, svd_solver="randomized", random_state=int(config.get("seed", 20261017)))
    projection.fit(embeddings[train])
    content = np.c_[scalars, projection.transform(embeddings)]
    mean, sd = standardize_fit(content[train]); content = (content - mean) / sd
    augmented = np.c_[base, content]
    # Existing fixed Phase0 ridge convention, now under recipient chronology.
    baseline_weights = global_fit(base[train], y[train])
    _, baseline_penalty, baseline_offset = select_offset(base[own] @ baseline_weights, y[own], base[cal] @ baseline_weights, y[cal], calibration_rows)
    baseline = softmax(base[test] @ baseline_weights + baseline_offset, axis=1)
    logistic_weights = global_fit(augmented[train], y[train])
    candidates = [(session_mean(brier(softmax(augmented[cal] @ logistic_weights, axis=1), y[cal]), calibration_rows), "logistic", None)]
    for leaves in (7, 15):
        model = HistGradientBoostingClassifier(max_iter=100, learning_rate=.1, max_leaf_nodes=leaves,
                l2_regularization=1., early_stopping=False, random_state=int(config.get("seed", 20261017)))
        model.fit(augmented[train], y[train])
        score = session_mean(brier(forest_probabilities(model, augmented[cal]), y[cal]), calibration_rows)
        candidates.append((score, "boosted_" + str(leaves), model))
    _, selected, model = min(candidates, key=lambda item: (item[0], item[1]))
    if model is None:
        logits = augmented @ logistic_weights
    else:
        logits = np.log(np.maximum(forest_probabilities(model, augmented), 1e-15))
    _, writer_penalty, writer_offset = select_offset(logits[own], y[own], logits[cal], y[cal], calibration_rows)
    predictions = []
    for j, i in enumerate(test):
        row = rows[i]
        predictions.append(dict(key=row["key"], writer=row["writer"], session=row["session"], prompt=row["prompt"], truth=row["handling"],
            probabilities={"backbone": baseline[j].tolist(), "content": softmax(logits[i]).tolist(),
                           "content_writer": softmax(logits[i] + writer_offset).tolist()}))
    receipt = dict(writer=split["writer"], cutoff=split["cutoff"], test_cutoff=split["test_cutoff"],
                   train_sessions=[s["session"] for s in split["train"]], calibration_sessions=[s["session"] for s in split["calibration"]],
                   test_sessions=[s["session"] for s in split["test"]],
                   train_keys=[rows[i]["key"] for i in train], own_train_keys=[rows[i]["key"] for i in own],
                   calibration_keys=[rows[i]["key"] for i in cal], test_keys=[rows[i]["key"] for i in test],
                   excluded_future_training=split["excluded_future_training"], excluded_overlapping_calibration=split["excluded_overlapping_calibration"],
                   pca_fit_keys=[rows[i]["key"] for i in train], pca_dimensions=dimensions,
                   selected=selected, calibration_scores={name: score for score, name, _ in candidates},
                   baseline_penalty=baseline_penalty, writer_penalty=writer_penalty,
                   baseline_weights=baseline_weights.tolist(), baseline_offset=baseline_offset.tolist(),
                   logistic_weights=logistic_weights.tolist(), writer_offset=writer_offset.tolist(),
                   scalar_mean=mean.tolist(), scalar_sd=sd.tolist(), pca_mean=projection.mean_.tolist(),
                   pca_components=projection.components_.tolist(), refit_on_calibration=False)
    saved_model = dict(selected=selected, selected_booster=model, baseline_weights=baseline_weights,
                       baseline_offset=baseline_offset, logistic_weights=logistic_weights,
                       writer_offset=writer_offset, scalar_mean=mean, scalar_sd=sd, projection=projection)
    return predictions, receipt, saved_model


def summarize(predictions, config):
    groups = defaultdict(list)
    for row in predictions:
        scores = {arm: float(brier([probability], [ACTIONS.index(row["truth"])])[0]) for arm, probability in row["probabilities"].items()}
        groups[(row["writer"], row["session"])].append([scores["backbone"] - scores["content"], scores["content"] - scores["content_writer"], *[scores[a] for a in ("backbone", "content", "content_writer")]])
    summaries = [(writer, session, np.asarray(values).mean(0)) for (writer, session), values in sorted(groups.items())]
    writers = sorted({row[0] for row in summaries})
    if len(writers) < 2:
        return dict(card="P4", state="invalid", reason="fewer than two scored writers", descriptive=True)
    values = np.asarray([row[2] for row in summaries]); writer_values = [values[[row[0] == writer for row in summaries]] for writer in writers]
    rng = np.random.default_rng(int(config.get("seed", 20261017))); draws = []
    for _ in range(int(config.get("bootstrap_draws", 2000))):
        selected = rng.integers(len(writers), size=len(writers))
        draws.append(np.concatenate([writer_values[i] for i in selected]).mean(0))
    intervals = np.quantile(draws, [.025, .975], axis=0).T; effects = values.mean(0)
    return dict(card="P4", descriptive=True, state=states.classify(effects[0], *intervals[0]),
                primary=dict(estimate=float(effects[0]), interval95=intervals[0].tolist(), direction="positive", useful_margin=.01,
                             reaches_useful_margin=bool(effects[0] >= .01)),
                extension=dict(estimate=float(effects[1]), interval95=intervals[1].tolist(), direction="positive",
                               state=states.classify(effects[1], *intervals[1]), expectation="less than .01"),
                mean_half_brier=dict(zip(("backbone", "content", "content_writer"), effects[2:].tolist())),
                decisions=len(predictions), sessions=len(summaries), writers=len(writers),
                weighting="equal session weight; writers resampled as clusters", bootstrap_draws=len(draws),
                interpretation="Exposed-data descriptive forecast; intervals condition on fitted predictions.")


def execute(output: Path, inputs: dict, config: dict) -> dict:
    started = time.perf_counter()
    mode = config.get("mode", "full")
    if mode not in ("full", "pilot"):
        raise ValueError("unknown P4 execution mode")
    if "p8" in inputs:
        raise ValueError("P8 producer-score semantics are uncalibrated; omit this optional feature input")
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    sessions = read(inputs["sessions"])
    # Add immutable end times for prefix provenance without mutating source bytes.
    for session in sessions:
        for row in session["rows"]:
            row["session_end"] = session["end_at"]
    p8_rows = None
    if "p8" in inputs:
        with Path(inputs["p8"]).open(encoding="utf8") as stream:
            p8_rows = [json.loads(line) for line in stream]
    vectors = np.load(inputs["vectors"], mmap_mode="r", allow_pickle=False)
    rows, base, scalars, embeddings = prefix_features(sessions, read(inputs["records"]), vectors, p8_rows)
    index = {row["key"]: i for i, row in enumerate(rows)}
    declared_splits, _ = chronological_partitions(sessions)
    eligible_writers = []
    for writer in sorted(declared_splits):
        split = recipient_split(writer, declared_splits)
        if split["reason"] is None and sum(len(s["rows"]) for s in split["train"]) >= 8:
            eligible_writers.append(writer)
    if not eligible_writers:
        raise ValueError("no eligible recipient for frozen chronology")
    selected_writers = eligible_writers[:1] if mode == "pilot" else eligible_writers
    write(output / "ELIGIBILITY.json", dict(mode=mode, eligible_writers=eligible_writers, selected_writers=selected_writers,
          rule="lexicographically first eligible recipient for pilot, metadata/count eligibility only; no outcome-based selection"))
    write(output / "FEATURE_ROWS.json", [{key: row[key] for key in ("key", "writer", "session", "open_at", "resolved_at")} for row in rows])
    with (output / "FEATURES.npz").open("xb") as stream:
        np.savez_compressed(stream, backbone=base, scalars=scalars, embeddings=embeddings)
    def fit_all(current_sessions, current_rows, current_base, current_scalars, folder):
        splits, exclusions = chronological_partitions(current_sessions); predictions, fits = [], []
        for writer in sorted(splits):
            if mode == "pilot" and writer not in selected_writers:
                continue
            split = recipient_split(writer, splits)
            if split["reason"] is not None:
                exclusions.append(dict(writer=writer, reason=split["reason"], excluded_future_training=split["excluded_future_training"],
                                       excluded_overlapping_calibration=split["excluded_overlapping_calibration"]))
                continue
            if sum(len(session["rows"]) for session in split["train"]) < 8:
                exclusions.append(dict(writer=writer, reason="fewer than 8 pooled fitting decisions")); continue
            predicted, receipt, model = fit_recipient(split, current_rows, current_base, current_scalars, embeddings, index, config)
            predictions.extend(predicted); fits.append(receipt)
            model_path = folder / "writers" / (writer + ".joblib")
            model_path.parent.mkdir(parents=True, exist_ok=True)
            if model_path.exists():
                raise ValueError("existing model checkpoint")
            joblib.dump(model, model_path, compress=3)
            receipt["model_sha256"] = sha256(model_path)
            write(folder / "writers" / (writer + ".json"), dict(predictions=predicted, fit=receipt))
        return predictions, fits, exclusions
    predictions, fits, exclusions = fit_all(sessions, rows, base, scalars, output)
    # Outcome shuffle preserves each writer/session's class composition. Prefix
    # lags are rebuilt from the shuffled world, so old labels cannot leak through.
    shuffled = copy.deepcopy(sessions); rng = np.random.default_rng(int(config.get("seed", 20261017)) + 701)
    for session in sorted(shuffled, key=lambda row: row["session"]):
        labels = rng.permutation([row["handling"] for row in session["rows"]])
        for row, label in zip(session["rows"], labels):
            row["handling"] = str(label)
    shuffled_rows, shuffled_base, shuffled_scalars, _ = prefix_features(shuffled, read(inputs["records"]), vectors, p8_rows)
    control, control_fits, control_exclusions = fit_all(shuffled, shuffled_rows, shuffled_base, shuffled_scalars, output / "shuffle")
    write(output / "SHUFFLE_PREDICTIONS.json", control)
    write(output / "SHUFFLE_FITS.json", control_fits)
    write(output / "PREDICTIONS.json", predictions); write(output / "FITS.json", fits); write(output / "EXCLUSIONS.json", exclusions)
    report = summarize(predictions, config)
    report["shuffle_control"] = summarize(control, config)
    report["shuffle_control"]["exclusions"] = len(control_exclusions)
    elapsed = time.perf_counter() - started
    report.update(mode=mode, eligible_recipients=len(eligible_writers), computed_recipients=len(selected_writers),
                  wall_seconds=elapsed, projected_full_seconds=elapsed * len(eligible_writers) if mode == "pilot" else elapsed)
    if mode == "pilot":
        report.update(state=states.instrument_state(True), execution_only=True, scientific_primary=None,
                      pilot_rule="first eligible recipient; original and shuffle fit included; no population inference")
    report.update(input_hashes=input_hashes(inputs), exclusions=len(exclusions), no_paid_features=True,
                  model_preference="log of positive logged GPT-3 producer scores; probability semantics unverified" if p8_rows is not None else "unavailable; fixed missing indicator",
                  intermediate_hashes={name: sha256(output / name) for name in ("PREDICTIONS.json", "FITS.json", "EXCLUSIONS.json", "SHUFFLE_PREDICTIONS.json", "SHUFFLE_FITS.json", "FEATURE_ROWS.json", "FEATURES.npz", "ELIGIBILITY.json")})
    write(output / "SUMMARY.json", report)
    return report


def verify(output: Path, inputs: dict, config: dict) -> dict:
    output = Path(output); report = read(output / "SUMMARY.json")
    assert_equal(report["input_hashes"], input_hashes(inputs))
    for name, identity in report["intermediate_hashes"].items():
        if sha256(output / name) != identity:
            raise ValueError("changed P4 intermediate")
    recomputed = summarize(read(output / "PREDICTIONS.json"), config)
    compared = {key: report[key] for key in recomputed}
    if report["mode"] == "pilot":
        compared["state"] = recomputed["state"]
    assert_equal(recomputed, compared)
    control = summarize(read(output / "SHUFFLE_PREDICTIONS.json"), config)
    assert_equal(control, {key: report["shuffle_control"][key] for key in control})
    for folder, name in ((output, "FITS.json"), (output / "shuffle", "SHUFFLE_FITS.json")):
        for fit in read(output / name):
            if sha256(folder / "writers" / (fit["writer"] + ".joblib")) != fit["model_sha256"]:
                raise ValueError("frozen fitted model changed")
    return dict(verified=True, primary_recomputed=recomputed.get("primary"), state=report["state"], execution_only=report["mode"] == "pilot")
