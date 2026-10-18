"""D14 single schema-repair retry; original failed module remains immutable.

DESIGN CHECK: LESSONS 3-5. Pilot selection never reads outcomes; source/config
mutation and incomplete pilot verification refuse main. Known null/positive/
reverse worlds validate the adjusted probability slope. Numerical failure is
invalid, not null. Pilot population statistics are never admission gates.
"""
import json
import math
import time
from collections import Counter
from pathlib import Path
import numpy as np
from .events_p5 import read, write, freeze_or_equal, filehash, model_identity
from . import events_d14_recovery_features as features
from . import events_d14_reuse as reuse
from . import events_d14_stats as stats

BASE_INPUTS = {"sessions", "content_records", "content_vectors", "content_model", "content_complete",
               "p8_rows", "p8_summary", "p8_verified", "spacy_model"}
FORECAST = 10800
PILOT_FORECAST = 1080


def save(path, value):
    path = Path(path)
    receipt = path.with_name(path.name + ".sha256")
    if path.exists() and receipt.exists():
        if load(path) != value:
            raise ValueError("immutable checkpoint differs")
        return
    if path.exists():
        retained = path.with_name(path.name + ".incomplete")
        if retained.exists():
            raise ValueError("second incomplete checkpoint not retried")
        path.rename(retained)
    write(path, value)
    with receipt.open("x", encoding="ascii", newline="\n") as f:
        f.write(filehash(path) + "\n")


def load(path):
    path = Path(path)
    receipt = path.with_name(path.name + ".sha256")
    if not receipt.exists() or receipt.read_text(encoding="ascii").strip() != filehash(path):
        raise ValueError("checkpoint hash differs")
    return read(path)


def complete(path):
    path = Path(path)
    return path.exists() and path.with_name(path.name + ".sha256").exists()


def input_pins(inputs):
    pins = {str(Path(value)): filehash(value) for key, value in inputs.items() if key != "spacy_model"}
    linguistic_pins = features.spacy_pins(inputs["spacy_model"])
    pins.update(linguistic_pins)
    if not linguistic_pins:
        raise ValueError("empty spaCy model")
    identity = read(inputs["content_model"])
    model_identity(inputs["content_model"])
    pins.update({str(Path(identity["path"]) / rel): expected for rel, expected in identity["files"].items()})
    return pins


def source(inputs):
    if read(inputs["content_complete"])["status"] != "COMPLETE":
        raise ValueError("CONTENT_V2 incomplete")
    completed = read(inputs["content_complete"])["outputs"]
    for key in ("content_records", "content_vectors", "content_model"):
        path = Path(inputs[key])
        candidates = [digest for name, digest in completed.items() if Path(name).name == path.name]
        if len(candidates) != 1 or candidates[0] != filehash(path):
            raise ValueError("CONTENT_V2 completion binding differs")
    p8 = read(inputs["p8_summary"])
    if p8.get("status") != "complete" or p8["table_sha256"] != filehash(inputs["p8_rows"]) or not read(inputs["p8_verified"]).get("verified"):
        raise ValueError("P8 completion/verification differs")
    sessions = read(inputs["sessions"])
    records = read(inputs["content_records"])
    vectors = np.load(inputs["content_vectors"], mmap_mode="r", allow_pickle=False)
    with Path(inputs["p8_rows"]).open(encoding="utf8") as f:
        p8_rows = [json.loads(line) for line in f]
    menus = {r["key"]: r for s in sessions for r in s["rows"]}
    if len(menus) != sum(len(s["rows"]) for s in sessions) or set(menus) != {r["key"] for r in records} or len(records) != len(menus):
        raise ValueError("source decision coverage differs")
    p8_keys = [(r["key"], r["position"]) for r in p8_rows]
    if len(set(p8_keys)) != len(p8_keys) or set(p8_keys) != {(k, i) for k, r in menus.items() for i in range(len(r["menu"]))}:
        raise ValueError("P8 option coverage differs")
    return sessions, records, vectors, p8_rows


def bootstrap_arm(output, moments, config, name):
    folder = Path(output) / name
    folder.mkdir(parents=True, exist_ok=True)
    try:
        point, certificate = stats.fit_draw(moments)
    except ValueError as exc:
        return dict(effect=None, state="invalid", ci95=None, reason=str(exc)), 0.
    rng = np.random.default_rng(config["seed"])
    choices = rng.integers(len(moments), size=(config["bootstrap"], len(moments)))
    grams = np.asarray([r["gram"] for r in moments], float)
    right_sides = np.asarray([r["rhs"] for r in moments], float)
    draws, failures, elapsed = [], [], 0.
    for first in range(0, config["bootstrap"], 100):
        path = folder / f"BOOTSTRAP_{first:04d}.json"
        if complete(path):
            block = load(path)
        else:
            start = time.monotonic()
            values, errors = [], []
            for draw in range(first, min(first + 100, config["bootstrap"])):
                multiplicity = np.bincount(choices[draw], minlength=len(moments))
                try:
                    values.append(stats.fit_moments(np.einsum("i,ijk->jk", multiplicity, grams), multiplicity @ right_sides)[0])
                except ValueError as exc:
                    values.append(None)
                    errors.append(dict(draw=draw, reason=str(exc)))
            block = dict(first=first, estimates=values, failures=errors, elapsed_seconds=time.monotonic() - start)
            save(path, block)
        if block["first"] != first or len(block["estimates"]) != min(100, config["bootstrap"] - first):
            raise ValueError("bootstrap checkpoint coverage differs")
        if [f["draw"] for f in block["failures"]] != [first + i for i, v in enumerate(block["estimates"]) if v is None]:
            raise ValueError("bootstrap failure ledger differs")
        draws.extend(v for v in block["estimates"] if v is not None)
        failures.extend(block["failures"])
        elapsed += block["elapsed_seconds"]
        if (Path(output) / "YIELD_REQUEST.json").exists():
            return dict(status="yielded", arm=name, draws_saved=first + len(block["estimates"])), elapsed
    result = stats.summarize(point, draws, len(failures))
    result.update(certificate=certificate, writers=len(moments))
    return result, elapsed


def execute(output: Path, inputs: dict, config: dict) -> dict:
    phase = config.get("phase")
    forecast = PILOT_FORECAST if phase == "pilot" else FORECAST
    expected = dict(phase=phase, threads=2, batch_size=16, bootstrap=2000, seed=20261017, pca_dimensions=16)
    if phase not in ("pilot", "main") or config != expected:
        raise ValueError("frozen D14 configuration differs")
    if set(inputs) != BASE_INPUTS | reuse.EXTRA_INPUTS | ({"pilot_summary", "pilot_verified"} if phase == "main" else set()):
        raise ValueError("explicit D14 input set differs")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    pins = input_pins(inputs)
    binding = dict(paths=inputs, config=config, pins=pins)
    if (output / "INPUTS.json").exists():
        if read(output / "INPUTS.json") != binding:
            raise ValueError("resume source/config changed")
        if (output / "SUMMARY.json").exists():
            raise ValueError("completed output is verified, never rerun")
    elif any(output.iterdir()):
        raise ValueError("unbound existing output")
    else:
        write(output / "INPUTS.json", binding)
    sessions, records, vectors, p8_rows = source(inputs)
    writers = sorted({s["writer"] for s in sessions})
    recovery_receipt, reusable = reuse.authenticate(inputs, config, writers, pins)
    freeze_or_equal(output / "RECOVERY.json", recovery_receipt)
    selected = features.pilot_writers(writers, config["seed"]) if phase == "pilot" else writers
    pilot_index = {}
    if phase == "main":
        pilot_path = Path(inputs["pilot_summary"])
        pilot = read(pilot_path)
        verified = read(inputs["pilot_verified"])
        pilot_binding = read(pilot_path.parent / "INPUTS.json")
        if (pilot.get("phase") != "pilot" or not verified.get("verified")
                or verified.get("summary_sha256") != filehash(pilot_path)
                or pilot["selected_writers"] != features.pilot_writers(writers, config["seed"])
                or any(pilot_binding["paths"][k] != inputs[k] for k in BASE_INPUTS)
                or any(pins.get(k) != v for k, v in pilot_binding["pins"].items())):
            raise ValueError("pilot identity/verification differs")
        for relative, expected_hash in read(pilot_path.parent / "OUTPUT_HASHES.json").items():
            if filehash(pilot_path.parent / relative) != expected_hash:
                raise ValueError("pilot output changed")
        pilot_index = {r["writer"]: (pilot_path.parent / r["file"], r["sha256"]) for r in read(pilot_path.parent / "WRITER_INDEX.json")}
    freeze_or_equal(output / "SELECTION.json", dict(full_writers=writers, selected_writers=selected,
        selection="ceil(10 percent), lowest SHA256(seed:writer), no outcome access" if phase == "pilot" else "all frozen writers"))
    encoder = nlp = None
    writer_index, all_rows, extraction_elapsed = [], [], 0.
    audit = Counter()
    for writer in selected:
        filename = f"writers/{writer}.json"
        path = output / filename
        if complete(path):
            saved = load(path)
        elif phase == "pilot" and writer in reusable:
            prior = Path(reusable[writer]["path"])
            if filehash(prior) != reusable[writer]["sha256"]:
                raise ValueError("reused failed-pilot checkpoint changed")
            saved = load(prior)
            save(path, saved)
        elif writer in pilot_index:
            old_path, expected_hash = pilot_index[writer]
            if filehash(old_path) != expected_hash:
                raise ValueError("pilot writer checkpoint changed")
            saved = load(old_path)
            save(path, saved)
        else:
            clock = time.monotonic()
            if encoder is None:
                import spacy
                encoder = features.ParagraphEncoder(inputs["content_model"], config["threads"], config["batch_size"])
                nlp = spacy.load(inputs["spacy_model"])
            own = [s for s in sessions if s["writer"] == writer]
            saved = features.extract_writer(own, records, vectors, encoder, nlp)
            saved["elapsed_seconds"] = time.monotonic() - clock
            save(path, saved)
        all_rows.extend(saved["rows"])
        audit.update(saved["audit"])
        extraction_elapsed += saved["elapsed_seconds"]
        writer_index.append(dict(writer=writer, file=filename, sha256=filehash(path)))
        if len(writer_index) == max(1, math.ceil(.1 * len(selected))) and not (output / "FIRST_TENTH.json").exists():
            write(output / "FIRST_TENTH.json", dict(writers=len(writer_index), full_writers=len(writers),
                selected_writers=len(selected), elapsed_seconds=extraction_elapsed,
                projected_cpu_seconds=extraction_elapsed * len(selected) / len(writer_index),
                projected_main_extraction_seconds=extraction_elapsed * len(writers) / len(writer_index),
                forecast_cpu_seconds=forecast, projection_scope="selected execution workload, extraction only; final pilot adds both bootstrap arms and verification allowance"))
        if (output / "YIELD_REQUEST.json").exists():
            return dict(status="yielded", writers_saved=len(writer_index), writers_total=len(selected))
    # Canonical order makes saved bootstrap inputs stable across process/hash seeds.
    all_rows.sort(key=lambda r: (r["writer"], r["session"], r["key"], r["position"]))
    chosen_sessions = [s for s in sessions if s["writer"] in set(selected)]
    preprocess_clock = time.monotonic()
    nuisance, projection = features.nuisance_matrix(all_rows, chosen_sessions, records, vectors, p8_rows,
                                                   config["seed"], config["pca_dimensions"])
    save(output / "ROWS.json", all_rows)
    save(output / "NUISANCE.json", nuisance.tolist())
    save(output / "PROJECTION.json", projection)
    preprocess_elapsed = time.monotonic() - preprocess_clock
    results, bootstrap_elapsed = {}, 0.
    for name, shuffle in (("primary", None), ("drift_shuffle", config["seed"] + 1)):
        moments = stats.sufficient(all_rows, nuisance, shuffle_seed=shuffle)
        save(output / f"MOMENTS_{name}.json", moments)
        result, elapsed = bootstrap_arm(output, moments, config, name)
        bootstrap_elapsed += elapsed
        if result.get("status") == "yielded":
            return result
        results[name] = result
    save(output / "WRITER_INDEX.json", writer_index)
    summary = dict(card="D14", phase=phase, selected_writers=selected, total_writers=len(writers),
        primary=results["primary"], controls=dict(within_writer_drift_shuffle=results["drift_shuffle"]),
        rows=len(all_rows), extraction_seconds=extraction_elapsed, bootstrap_seconds=bootstrap_elapsed,
        extraction_audit=dict(audit),
        preprocessing_seconds=preprocess_elapsed, elapsed_seconds_this_invocation=time.monotonic() - started,
        projected_cpu_seconds=2 * (extraction_elapsed + bootstrap_elapsed + preprocess_elapsed) * len(writers) / len(selected),
        projection_scope="Full main extraction, preprocessing and bootstrap, doubled conservatively to include fresh verification",
        verification_allowance_multiplier=2,
        forecast_cpu_seconds=forecast, main_forecast_cpu_seconds=FORECAST,
        execution_only=phase == "pilot", scientific_admission=False,
        extension_run=False, extension="Restoration: accept-then-edit moves topic drift toward the preceding paragraph; positive",
        weighting="Equal writers, sessions within writers, menus within sessions; dismissed menu offers split its weight",
        primary_scope="Descriptive linear probability slope with writer intercepts, exact D1/P8 features and content PCA; no causal set-point claim",
        not_measured=["sentiment change", "formality change"],
        outcome_support="Dismissed menus: all offers; accept/edit menus: unique selected offer; ignore and other offers excluded")
    write(output / "SUMMARY.json", summary)
    write(output / "OUTPUT_HASHES.json", {p.relative_to(output).as_posix(): filehash(p) for p in output.rglob("*")
        if p.is_file() and p.name not in ("OUTPUT_HASHES.json", "YIELD_REQUEST.json")})
    return summary


def verify(output: Path, inputs: dict, config: dict) -> dict:
    output = Path(output)
    binding = read(output / "INPUTS.json")
    if binding["paths"] != inputs or binding["config"] != config:
        raise ValueError("verification binding differs")
    for path, expected in binding["pins"].items():
        if filehash(path) != expected:
            raise ValueError("input changed")
    for relative, expected in read(output / "OUTPUT_HASHES.json").items():
        if filehash(output / relative) != expected:
            raise ValueError("output changed")
    receipt, _ = reuse.authenticate(inputs, config, verified_pins=binding["pins"])
    if read(output / "RECOVERY.json") != receipt:
        raise ValueError("recovery source snapshot differs")
    rows, nuisance = load(output / "ROWS.json"), load(output / "NUISANCE.json")
    summary = read(output / "SUMMARY.json")
    for name, shuffle in (("primary", None), ("drift_shuffle", config["seed"] + 1)):
        moments = stats.sufficient(rows, nuisance, shuffle_seed=shuffle)
        if moments != load(output / f"MOMENTS_{name}.json"):
            raise ValueError("saved moments differ")
        try:
            point, certificate = stats.fit_draw(moments)
        except ValueError as exc:
            rebuilt = dict(effect=None, state="invalid", ci95=None, reason=str(exc))
        else:
            draws, invalid = [], 0
            for first in range(0, config["bootstrap"], 100):
                block = load(output / name / f"BOOTSTRAP_{first:04d}.json")
                draws.extend(v for v in block["estimates"] if v is not None)
                invalid += len(block["failures"])
            rebuilt = stats.summarize(point, draws, invalid)
            rebuilt.update(certificate=certificate, writers=len(moments))
        saved = summary["primary"] if name == "primary" else summary["controls"]["within_writer_drift_shuffle"]
        if rebuilt != saved:
            raise ValueError("primary/control does not reproduce")
    return dict(verified=True, phase=config["phase"], summary_sha256=filehash(output / "SUMMARY.json"),
                primary_recomputed=summary["primary"], scientific_admission=False)
