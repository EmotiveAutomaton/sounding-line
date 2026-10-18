"""D24 timer discontinuity: accepted closure primary and packet secondaries.

DESIGN CHECK: pre-outcome 120-second uniform local-linear window, separate
time slopes, writer fixed effects and writer-cluster bootstrap. Planted jumps
must recover their sign; constant outcomes and shuffled outcomes can reject
the instrument. The equal-weight lexical/rescaled-cosine composite is frozen
with each component retained. Typed closure, request/accept rates and own-
median-length location are descriptive secondaries. No causal need inference.
Native CPU pilot is mandatory before primary execution; no download/fallback.
"""
from __future__ import annotations

import hashlib
import json
import math
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

from runners.drive.cards import timing_closure_measure as measure
from runners.drive.cards.timing_census import read, filehash
from runners.drive.cards.timing_events import source_sessions, session_words, CooperativeYield
from runners.drive.cards.timing_stats import regression, bind, check_binding
from runners.stage14.common import atomic, freeze

FORECAST_SECONDS = 900
FORECASTS = dict(pilot=60, primary=900, extension=120)
BASE_CONFIG = dict(card="D24", bootstrap_draws=2000, seed=20261017)
SOURCE_INPUTS = {"session_index", "foundation_complete", "foundation_plan", "repo_root", "raw_roster"}
MODEL_INPUTS = {"model_manifest", "content_complete"}


def config_for(phase):
    return dict(BASE_CONFIG, phase=phase)


def validate(inputs, config):
    phase = config.get("phase")
    expected = config_for(phase)
    if phase not in {"pilot", "primary", "extension"} or set(config) != set(expected) or any(type(config[k]) is not type(v) or config[k] != v for k, v in expected.items()):
        raise ValueError("exact D24 phase configuration required")
    keys = MODEL_INPUTS if phase == "pilot" else SOURCE_INPUTS | MODEL_INPUTS | {"pilot_complete"}
    if phase == "extension":
        keys |= {"primary_complete"}
    if set(inputs) != keys:
        raise ValueError("exact D24 input set required")


def completed_output(path, names):
    path = Path(path)
    complete = read(path)
    if complete.get("status") != "COMPLETE" or complete.get("fresh_process_verified") is not True:
        raise ValueError("D24 dependency requires fresh-verified completion")
    output = path.parent / "output"
    for name in names:
        if complete["outputs"].get("output/" + name) != filehash(output / name):
            raise ValueError("D24 dependency output hash differs")
    return output


def authorize_pilot(inputs):
    output = completed_output(inputs["pilot_complete"], ["CLOSURE_PRIMARY.json", "TIMING_BINDINGS.json"])
    model_inputs = {k: inputs[k] for k in MODEL_INPUTS}
    check_binding(output, model_inputs, config_for("pilot"))
    result = read(output / "CLOSURE_PRIMARY.json")
    if result["state"] != "positive" or not result["instrument_only"]:
        raise ValueError("D24 native closure pilot did not pass")
    measure.model_identity(inputs)


def primary_rows(inputs):
    output = completed_output(inputs["primary_complete"], ["CLOSURE_ROWS.json", "CLOSURE_PRIMARY.json", "TIMING_BINDINGS.json"])
    source = {k: v for k, v in inputs.items() if k != "primary_complete"}
    check_binding(output, source, config_for("primary"))
    if read(output / "CLOSURE_PRIMARY.json")["state"] not in {"positive", "marginal"}:
        raise ValueError("D24 primary does not permit conditional extension")
    return read(output / "CLOSURE_ROWS.json")


def score_rows(inputs, encoder, output=None, elapsed=None):
    by_writer = defaultdict(list)
    source = {k: inputs[k] for k in SOURCE_INPUTS}
    for index, timeline, _ in source_sessions(source, "raw_roster"):
        by_writer[index["writer"]].append(session_words(timeline))
    medians = {w: float(np.median(v)) for w, v in by_writer.items()}
    total = len(read(inputs["session_index"]))
    sessions = []
    for done, (index, timeline, metadata) in enumerate(source_sessions(source, "raw_roster"), 1):
        raw_path = (Path(inputs["repo_root"]) / metadata["path"]).resolve()
        with raw_path.open(encoding="utf-8") as stream:
            raw = [json.loads(line) for line in stream]
        replayed = measure.replay(raw, timeline)
        session = dict(session=index["session"], writer=index["writer"], final_words=session_words(timeline),
                       median_final_words=medians[index["writer"]], duration_seconds=replayed["duration_seconds"],
                       requests=replayed["requests"], accepted_times=[r["seconds"] for r in replayed["entries"] if r["kind"] == "accepted"], entries=[])
        checkpoint = output / "sessions" / (hashlib.sha256(index["session"].encode()).hexdigest() + ".json") if output else None
        source_binding = dict(p2=index["sha256"], raw=metadata["source_sha256"])
        saved = None
        if checkpoint is not None and checkpoint.exists():
            saved = read(checkpoint)
            if saved["sources"] != source_binding or read(checkpoint.with_suffix(".receipt.json"))["sha256"] != filehash(checkpoint):
                raise ValueError("D24 scored session checkpoint changed")
        for entry in replayed["entries"]:
            median = session["median_final_words"]
            location = (entry["words_at_event"] - median) / median if median > 0 else None
            # All accepted event times remain for rates, even when no closure
            # score is needed. Score the fixed union of all registered windows.
            eligible = session["duration_seconds"] > 600 and (abs(entry["seconds"] - 600) <= 180 or location is not None and abs(location) <= .2)
            if eligible:
                record = dict(entry, median_location=location)
                if saved is not None:
                    position = len(session["entries"])
                    stored = saved["session"]["entries"][position]
                    if {k: stored[k] for k in record} != record:
                        raise ValueError("D24 checkpoint text/identity differs from raw source")
                    record["score"] = stored["score"]
                else:
                    record["score"] = encoder.score(entry["text"])
                session["entries"].append(record)
        if saved is not None and saved["session"] != session:
            raise ValueError("D24 checkpoint source reconstruction differs")
        if checkpoint is not None:
            freeze(checkpoint, dict(sources=source_binding, session=session))
            freeze(checkpoint.with_suffix(".receipt.json"), dict(sha256=filehash(checkpoint)))
        sessions.append(session)
        if output is not None:
            active = elapsed()
            atomic(output / "CLOSURE_PROGRESS.json", dict(completed_scored_sessions=done, total_sessions=total, active_seconds=active))
            overshoot = False
            if done == math.ceil(total / 10) and not (output / "FIRST_TENTH.json").exists():
                projection = 2 * active * total / done + 120
                overshoot = projection > 2 * FORECAST_SECONDS
                freeze(output / "FIRST_TENTH.json", dict(completed_scored_sessions=done, total_sessions=total,
                       elapsed_seconds=active, projected_cpu_seconds=projection, forecast_cpu_seconds=FORECAST_SECONDS,
                       includes_fresh_source_and_encoder_verification=True, reserved_statistics_seconds=120))
            if active > 3 * FORECAST_SECONDS:
                raise RuntimeError("D24 threefold active-time ceiling")
            if overshoot or (output / "YIELD_REQUEST.json").exists():
                if overshoot and not (output / "YIELD_REQUEST.json").exists():
                    atomic(output / "YIELD_REQUEST.json", dict(reason="first_tenth_projection_exceeds_twice_forecast"))
                raise CooperativeYield("saved fully scored source-bound session")
    return sessions


def rd(records, config, shuffle=False):
    if not records:
        return dict(state="invalid", reason="no supported local observations")
    x = [[int(r["location"] >= 0), r["location"], int(r["location"] >= 0) * r["location"]] for r in records]
    y = np.array([r["outcome"] for r in records], float)
    writers = [r["writer"] for r in records]
    if shuffle:
        rng = np.random.default_rng(config["seed"])
        for writer in sorted(set(writers)):
            ix = np.flatnonzero(np.array(writers) == writer)
            y[ix] = rng.permutation(y[ix])
    return regression(x, y, writers, within=True, draws=config["bootstrap_draws"], seed=config["seed"])


def closure_records(sessions, kind, component="closure", window=120, location="timer"):
    rows = []
    for session in sessions:
        if session["duration_seconds"] <= 600:
            continue
        for entry in session["entries"]:
            distance = entry["seconds"] - 600 if location == "timer" else entry["median_location"]
            width = window if location == "timer" else .2
            if entry["kind"] == kind and distance is not None and abs(distance) <= width:
                rows.append(dict(writer=session["writer"], session=session["session"], location=distance,
                                 outcome=entry["score"][component]))
    return rows


def rate_records(sessions, name):
    rows = []
    for session in sessions:
        duration = session["duration_seconds"]
        if duration <= 600:
            continue
        for left in range(480, 720, 30):
            right = min(left + 30, duration)
            if right <= left:
                continue
            count = sum(left <= t < right for t in session[name])
            rows.append(dict(writer=session["writer"], session=session["session"], location=(left+right)/2 - 600,
                             outcome=count * 60 / (right-left)))
    return rows


def summarize(sessions, config):
    extension = config["phase"] == "extension"
    window = 60 if extension else 120
    observations = closure_records(sessions, "accepted", window=window)
    result = rd(observations, config)
    result.update(card="D24", extension=extension, descriptive=True, window_seconds=window,
                  contrast="jump at 600 logged session seconds in accepted-suggestion closure; writer fixed effects and separate linear slopes",
                  composite="equal weights for frozen lexical marker presence and (mean anchor cosine+1)/2",
                  controls=dict(within_writer_closure_shuffle=rd(observations, config, shuffle=True)),
                  sessions_continuing_past_timer=sum(s["duration_seconds"] > 600 for s in sessions),
                  excluded_sessions_at_or_before_timer=sum(s["duration_seconds"] <= 600 for s in sessions),
                  interpretation="Exploratory association among continuing sessions; no causal need, internal target or intention identification")
    secondaries = {}
    if extension:
        for width in (60, 120, 180):
            secondaries[f"accepted_closure_window_{width}"] = rd(closure_records(sessions, "accepted", window=width), config)
    else:
        for kind in ("accepted", "typed"):
            for component in ("closure", "lexical", "cosine"):
                secondaries[f"{kind}_{component}_timer"] = rd(closure_records(sessions, kind, component), config)
            secondaries[f"{kind}_closure_own_median_length"] = rd(closure_records(sessions, kind, location="length"), config)
        for name in ("requests", "accepted_times"):
            secondaries[name + "_per_minute_timer"] = rd(rate_records(sessions, name), config)
    detail = dict(secondaries=secondaries, primary_observations=observations,
                  typed_unit="wholly typed complete visible sentence whose terminal punctuation is inserted now; later-deleted sentences retained",
                  own_median_definition="within-writer median final nonprompt length across all recorded sessions; retrospective descriptive location, uniform +/-20% of median",
                  rate_definition="30-second bins, actual observed exposure through last logged event; suggestion-get requests and verified API accepted insertions",
                  anchors=list(measure.ANCHORS), lexicon=list(measure.LEXICON),
                  component_scope="lexical indicator uses full text; cosine uses first 254 native tokens with original BERT boundaries, truncation retained",
                  scored_entries=sum(len(s["entries"]) for s in sessions),
                  truncated_entries=sum(r["score"]["truncated"] for s in sessions for r in s["entries"]))
    return result, detail


def execute(output: Path, inputs: dict, config: dict) -> dict:
    validate(inputs, config)
    output = Path(output)
    started = time.monotonic()
    if (output / "TIMING_BINDINGS.json").exists():
        return verify(output, inputs, config)["primary"]
    freeze(output / "CLOSURE_RUN_BINDINGS.json", dict(config=config, source_sha256=filehash(__file__), measure_sha256=filehash(measure.__file__),
           inputs={k: str(Path(v).resolve()) if Path(v).is_dir() else filehash(v) for k, v in inputs.items()}))
    prior = read(output / "CLOSURE_PROGRESS.json")["active_seconds"] if (output / "CLOSURE_PROGRESS.json").exists() else 0.
    elapsed = lambda: prior + time.monotonic() - started
    if config["phase"] == "pilot":
        result, details, sessions = measure.pilot(measure.Encoder(inputs)), {}, []
    else:
        authorize_pilot(inputs)
        if config["phase"] == "extension":
            sessions = primary_rows(inputs)
        else:
            encoder = measure.Encoder(inputs)
            try:
                sessions = score_rows(inputs, encoder, output, elapsed)
            except CooperativeYield as exc:
                return dict(status="yielded", card="D24", reason=str(exc))
        result, details = summarize(sessions, config)
    if elapsed() > 3 * FORECASTS[config["phase"]]:
        raise RuntimeError("D24 threefold active-time ceiling")
    for name, value in (("CLOSURE_ROWS.json", sessions), ("CLOSURE_PRIMARY.json", result), ("CLOSURE_DETAILS.json", details)):
        freeze(output / name, value)
    freeze(output / "CLOSURE_TIMING.json", dict(wall_seconds=elapsed(), forecast_cpu_seconds=FORECASTS[config["phase"]]))
    bind(output, inputs, config, ["CLOSURE_ROWS.json", "CLOSURE_PRIMARY.json", "CLOSURE_DETAILS.json"])
    return result


def verify(output: Path, inputs: dict, config: dict) -> dict:
    validate(inputs, config)
    check_binding(output, inputs, config)
    if config["phase"] == "pilot":
        result, details, sessions = measure.pilot(measure.Encoder(inputs)), {}, []
    else:
        authorize_pilot(inputs)
        sessions = primary_rows(inputs) if config["phase"] == "extension" else score_rows(inputs, measure.Encoder(inputs))
        result, details = summarize(sessions, config)
    for name, value in (("CLOSURE_ROWS.json", sessions), ("CLOSURE_PRIMARY.json", result), ("CLOSURE_DETAILS.json", details)):
        if read(Path(output) / name) != value:
            raise ValueError("D24 outputs do not reconstruct from authenticated sources and encoder")
    return dict(verified=True, primary=result)
