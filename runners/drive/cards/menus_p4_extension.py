"""P4's conditional writer-offset extension, reusing the frozen primary models."""
from __future__ import annotations

import math
import time
from pathlib import Path
import joblib
import numpy as np
from scipy.special import softmax

from . import menus_p4_primary as primary
from . import states
from .menus_io import assert_equal, input_hashes, read, sha256, write


def extend_writer(fit, model, rows, base, scalars, embeddings, config):
    index = {row["key"]: i for i, row in enumerate(rows)}
    own, cal, test = [np.asarray([index[key] for key in fit[name]], int)
                      for name in ("own_train_keys", "calibration_keys", "test_keys")]
    content = np.c_[scalars, model["projection"].transform(embeddings)]
    augmented = np.c_[base, (content - model["scalar_mean"]) / model["scalar_sd"]]
    logits = (augmented @ model["logistic_weights"] if model["selected_booster"] is None else
              np.log(np.maximum(primary.pilot.forest_probabilities(model["selected_booster"], augmented), 1e-15)))
    y = np.asarray([primary.pilot.ACTIONS.index(row["handling"]) for row in rows])
    _, penalty, offset = primary.pilot.select_offset(logits[own], y[own], logits[cal], y[cal], [rows[i] for i in cal])
    predictions = [dict(key=rows[i]["key"], writer=rows[i]["writer"], session=rows[i]["session"], prompt=rows[i]["prompt"],
                        truth=rows[i]["handling"], probabilities={"content": softmax(logits[i]).tolist(),
                        "content_writer": softmax(logits[i] + offset).tolist()}) for i in test]
    return predictions, dict(writer=fit["writer"], writer_penalty=penalty, writer_offset=offset.tolist(),
                             own_train_keys=fit["own_train_keys"], calibration_keys=fit["calibration_keys"],
                             test_keys=fit["test_keys"], primary_model_sha256=fit["model_sha256"])


def execute(output: Path, inputs: dict, config: dict) -> dict:
    output = Path(output); output.mkdir(parents=True, exist_ok=True); started = time.perf_counter()
    hashes = input_hashes(inputs); primary_report = read(inputs["primary_summary"])
    if primary_report["state"] not in ("positive", "marginal"):
        raise ValueError("P4 writer-offset extension requires a positive or marginal primary")
    primary_root = Path(inputs["primary_summary"]).parent; plan = read(inputs["primary_plan"])
    if plan["module"] != "runners.drive.cards.menus_p4_primary":
        raise ValueError("P4 extension requires the primary-only route")
    for key in ("sessions", "records", "vectors"):
        if hashes[key] != primary_report["input_hashes"][key]:
            raise ValueError("P4 extension sources differ from primary")
    for key, default in (("seed", 20261017), ("pca_dimensions", 16)):
        if config.get(key, default) != plan["config"].get(key, default):
            raise ValueError("P4 extension model configuration differs from primary")
    primary.verify(primary_root, plan["inputs"], plan["config"])
    binding = dict(inputs=hashes, config=config, code_sha256=sha256(__file__))
    if (output / "BINDING.json").exists():
        assert_equal(read(output / "BINDING.json"), binding)
    else:
        write(output / "BINDING.json", binding)
    _, rows, base, scalars, embeddings, _, changed_rows, changed_base, changed_scalars = primary.load_features(dict(inputs, _seed=int(config.get("seed", 20261017))))
    primary_fits = read(primary_root / "FITS.json"); shuffled_fits = read(primary_root / "SHUFFLE_FITS.json")
    by_writer = {arm: {fit["writer"]: fit for fit in fits} for arm, fits in (("primary", primary_fits), ("shuffle", shuffled_fits))}
    saved_primary = {arm: {row["key"]: row for row in read(primary_root / name)} for arm, name in
                     (("primary", "PREDICTIONS.json"), ("shuffle", "SHUFFLE_PREDICTIONS.json"))}
    predictions, control, fits, control_fits = [], [], [], []; writers = sorted(by_writer["primary"])
    for number, writer in enumerate(writers):
        if (output / "YIELD_REQUEST.json").exists():
            return dict(status="yielded", card="P4.extension", completed_recipients=number)
        for arm, current_rows, current_base, current_scalars, destination, fit_destination in (
            ("primary", rows, base, scalars, predictions, fits), ("shuffle", changed_rows, changed_base, changed_scalars, control, control_fits)):
            path = output / arm / (writer + ".json"); seal = path.with_suffix(".seal.json")
            if path.exists():
                if sha256(path) != read(seal)["sha256"]:
                    raise ValueError("P4 extension checkpoint changed")
                saved = read(path); assert_equal(saved["binding"], binding)
            else:
                fit = by_writer[arm][writer]; model_path = primary_root / arm / (writer + ".joblib")
                if sha256(model_path) != fit["model_sha256"]:
                    raise ValueError("P4 primary fitted model changed")
                model = joblib.load(model_path)
                predicted, receipt = extend_writer(fit, model, current_rows, current_base, current_scalars, embeddings, config)
                for row in predicted:
                    if not np.allclose(row["probabilities"]["content"], saved_primary[arm][row["key"]]["probabilities"]["content"], rtol=0, atol=1e-12):
                        raise ValueError("P4 extension primary forecast replay differs")
                saved = dict(binding=binding, predictions=predicted, fit=receipt)
                write(path, saved); write(seal, dict(sha256=sha256(path)))
            destination.extend(saved["predictions"]); fit_destination.append(saved["fit"])
        if number + 1 >= max(1, math.ceil(.1 * len(writers))) and not (output / "FIRST_TENTH.json").exists():
            elapsed = time.perf_counter() - started
            write(output / "FIRST_TENTH.json", dict(completed_recipients=number + 1, total_recipients=len(writers),
                  elapsed_seconds=elapsed, projected_seconds=elapsed * len(writers) / (number + 1)))
    if (output / "YIELD_REQUEST.json").exists():
        return dict(status="yielded", card="P4.extension", completed_recipients=len(writers))
    for name, value in (("PREDICTIONS.json", predictions), ("FITS.json", fits), ("SHUFFLE_PREDICTIONS.json", control), ("SHUFFLE_FITS.json", control_fits)):
        write(output / name, value)
    report = dict(card="P4.extension", descriptive=True, **primary.summarize(predictions, config, "content", "content_writer"),
                  primary_state=primary_report["state"], expectation="increment below .01", conditional_extension=True,
                  shuffle_control=primary.summarize(control, config, "content", "content_writer"), input_hashes=hashes,
                  wall_seconds=time.perf_counter() - started,
                  intermediate_hashes={name: sha256(output / name) for name in ("PREDICTIONS.json", "FITS.json", "SHUFFLE_PREDICTIONS.json", "SHUFFLE_FITS.json", "BINDING.json")})
    write(output / "SUMMARY.json", report)
    return report


def verify(output: Path, inputs: dict, config: dict) -> dict:
    output = Path(output); report = read(output / "SUMMARY.json")
    assert_equal(input_hashes(inputs), report["input_hashes"])
    for name, expected in report["intermediate_hashes"].items():
        if sha256(output / name) != expected:
            raise ValueError("P4 extension intermediate changed")
    actual = primary.summarize(read(output / "PREDICTIONS.json"), config, "content", "content_writer")
    assert_equal(actual, {key: report[key] for key in actual})
    assert_equal(primary.summarize(read(output / "SHUFFLE_PREDICTIONS.json"), config, "content", "content_writer"), report["shuffle_control"])
    return dict(verified=True, primary_recomputed=actual["primary"], state=actual["state"])
