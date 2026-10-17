"""D34.v1: cohesion of surprising, directly linked accepted-model corrections.

Curator authorization, 17 October: "Run the supported subset; retain the broader
question." Own-text, mixed, multiply linked and otherwise unsupported corrections
are counted, never assigned a nearby menu forecast. The broader question is OPEN.
Surprisal is the realized edit-class handling outcome under its original reader;
it is not a likelihood for the correction's text. Simulated categorical reader
outcomes give its 80th percentile. Matched corrections are sampled without
replacement within writer/session, with equal unexplained/explained counts.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
import time
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np

from . import states_v2 as states
from .menus_io import assert_equal, input_hashes, read, sha256, write
from .menus_d34_stats import interval
from .menus_d34 import bind_completed_artifact


def fixed_seed(seed, label):
    return int(seed) + int(hashlib.sha256(label.encode()).hexdigest()[:8], 16)


def unexplained(probabilities, key, seed=20261017, simulations=1000):
    p = np.asarray(probabilities, float)
    if p.shape != (4,) or not np.isfinite(p).all() or np.any(p < 0) or not np.isclose(p.sum(), 1, atol=1e-10, rtol=0):
        raise ValueError("invalid four-class forecast")
    rng = np.random.default_rng(fixed_seed(seed, key))
    simulated = rng.choice(4, size=simulations, p=p)
    surprise = -np.log(p[simulated]); threshold = float(np.quantile(surprise, .8, method="higher"))
    observed = float(-np.log(p[1])) if p[1] > 0 else None
    return dict(unexplained=observed is None or observed > threshold, surprisal=observed,
                impossible_under_reader=observed is None, threshold80=threshold, simulations=simulations)


def linked_corrections(session, vectors, decisions, forecasts, config):
    counts = Counter(); rows = []; cache = {}
    for edit in session["edits"]:
        counts["all_corrections"] += 1
        owners = edit["accepted_owners_touched"]
        if edit["origin"] != "model":
            counts["unsupported_own" if edit["origin"] == "own" else "unsupported_other"] += 1; continue
        if any(n > 0 for origin, n in edit["deleted_origin_counts"].items() if origin != "accepted"):
            counts["unsupported_mixed"] += 1; continue
        if len(owners) != 1:
            counts["unsupported_multiple_owners"] += 1; continue
        decision = decisions.get((session["session"], owners[0]))
        if decision is None or decision["key"] not in forecasts:
            counts["unsupported_missing_forecast_link"] += 1; continue
        forecast = forecasts[decision["key"]]
        if forecast["writer"] != session["writer"] or forecast["truth"] != decision["handling"]:
            raise ValueError("linked forecast identity/target mismatch")
        if forecast["truth"] != "edit":
            counts["unsupported_linked_handling_not_edit"] += 1; continue
        delta = np.asarray(vectors[edit["after_vector"]] - vectors[edit["before_vector"]], float)
        norm = float(np.linalg.norm(delta))
        if not np.isfinite(delta).all():
            raise ValueError("nonfinite correction vector")
        if norm <= 1e-12:
            counts["unsupported_zero_vector"] += 1; continue
        key = decision["key"]
        if key not in cache:
            cache[key] = unexplained(forecast["probabilities"]["B-mixlogit"], key, config.get("seed", 20261017), config.get("simulations", 1000))
        classification = cache[key]
        counts["supported_corrections"] += 1
        counts["unexplained" if classification["unexplained"] else "explained"] += 1
        rows.append(dict(session=session["session"], ordinal=edit["ordinal"], key=key, unit=delta / norm, **classification))
    return rows, dict(counts)


def matched_moments(rows, writer, seed):
    grouped = defaultdict(lambda: {True: [], False: []})
    for row in rows:
        grouped[row["session"]][row["unexplained"]].append(row)
    moments = {"unexplained": [], "explained": []}; selected = []
    for session, split in sorted(grouped.items()):
        count = min(len(split[True]), len(split[False]))
        if not count:
            continue
        rng = np.random.default_rng(fixed_seed(seed, writer + ":" + session))
        for flag, name in ((True, "unexplained"), (False, "explained")):
            candidates = sorted(split[flag], key=lambda row: row["ordinal"])
            chosen = [candidates[i] for i in rng.choice(len(candidates), count, replace=False)]
            moments[name].append(dict(session=session, count=count, unit_sum=np.sum([row["unit"] for row in chosen], axis=0).tolist()))
            selected.extend({key: row[key] for key in ("session", "ordinal", "key", "unexplained", "surprisal", "threshold80", "impossible_under_reader")} for row in chosen)
    return moments, selected


def cohesion(moments):
    if len(moments) < 2:
        return None
    counts = np.asarray([row["count"] for row in moments]); sums = np.asarray([row["unit_sum"] for row in moments])
    denominator = int(counts.sum() ** 2 - (counts ** 2).sum())
    if denominator <= 0:
        return None
    return float(((sums.sum(0) ** 2).sum() - (sums ** 2).sum()) / denominator)


def summarize(units, config):
    audit = Counter(); values = []; own = []; means = []; matched = 0; exclusions = []
    for writer, unit in sorted(units.items()):
        audit.update(unit["audit"])
        u, e = (cohesion(unit["moments"][name]) for name in ("unexplained", "explained"))
        if u is None or e is None:
            exclusions.append(dict(writer=writer, reason="fewer than two sessions with both classes and matched counts")); continue
        values.append(u - e); own.append(u)
        moments = unit["moments"]["unexplained"]
        count = sum(row["count"] for row in moments); matched += count
        means.append(np.sum([row["unit_sum"] for row in moments], axis=0) / count)
    primary = interval(values, config.get("seed", 20261017), config.get("bootstrap", 2000))
    donor = dict(state="invalid", estimate=None, reason="fewer than two eligible writers")
    if len(means) >= 2:
        gram = np.asarray(means) @ np.asarray(means).T; np.fill_diagonal(gram, 0.)
        n = len(means); between = float(gram.sum() / (n * (n - 1))); point = float(np.mean(own) - between)
        rng = np.random.default_rng(config.get("seed", 20261017)); draws = []; unsupported = 0
        for _ in range(config.get("bootstrap", 2000)):
            multiplicity = np.bincount(rng.integers(n, size=n), minlength=n)
            denominator = n*n - multiplicity @ multiplicity
            if denominator == 0:
                unsupported += 1; continue
            draws.append(float(np.asarray(own) @ multiplicity / n - multiplicity @ gram @ multiplicity / denominator))
        donor = dict(estimate=point, other_writer_cosine=between, bootstrap_invalid=unsupported,
                     method="writer node bootstrap, excluding pairs from the same original writer")
        if len(draws) >= .95 * config.get("bootstrap", 2000):
            bounds = np.quantile(draws, [.025, .975]).tolist()
            donor.update(state=states.classify(point, *bounds), interval95=bounds, standard_error=float(np.std(draws, ddof=1)))
        else:
            donor.update(state="invalid", interval95=None, reason="more than 5% donor bootstrap draws lack distinct writers")
    rate = audit["unexplained"] / audit["supported_corrections"] if audit["supported_corrections"] else None
    return dict(card="D34.v1", descriptive=True, state=primary["state"], primary=primary, donor_control=donor,
        audit=dict(audit), unexplained_correction_rate=rate, rate_denominator="supported directly linked accepted-model corrections only",
        matched_per_class=matched, excluded_writers=exclusions, broader_question="OPEN: own-text and mixed corrections lack an applicable edit-reader forecast",
        scope="directly linked single accepted-model origin; observed reader handling class edit; nonzero P5 edit vector",
        authorization="Curator, 2026-10-17: Run the supported subset; retain the broader question.",
        threshold="strictly above 80th percentile of 1,000 categorical outcomes simulated from the original four-class handling reader",
        weighting="all cross-session correction pairs within writer, equal writer weights; per-session count-matched explained corrections")


def execute(output: Path, inputs: dict, config: dict) -> dict:
    output = Path(output); output.mkdir(parents=True, exist_ok=True); started = time.perf_counter()
    if config.get("scope") != "linked_model_corrections" or config.get("simulations", 1000) != 1000:
        raise ValueError("frozen supported subset and 1,000 simulations required")
    bind_completed_artifact(inputs["prediction_completion"], inputs["predictions"])
    bind_completed_artifact(inputs["p5_completion"], inputs["p5_summary"])
    bind_completed_artifact(inputs["p5_completion"], inputs["p5_index"])
    summary = read(inputs["p5_summary"]); index = read(inputs["p5_index"])
    if summary["sessions"] != len(index) or len({item["session"] for item in index}) != len(index):
        raise ValueError("P5 is incomplete")
    sessions = {row["session"]: row for row in read(inputs["sessions"])}
    if set(sessions) != {item["session"] for item in index}:
        raise ValueError("P5/source session support differs")
    prediction_rows = read(inputs["predictions"])
    forecasts = {row["key"]: row for row in prediction_rows}
    if len(forecasts) != len(prediction_rows):
        raise ValueError("duplicate source forecast")
    decisions = {(session["session"], row["ordinal"]): row for session in sessions.values() for row in session["rows"]}
    if len(decisions) != sum(len(session["rows"]) for session in sessions.values()):
        raise ValueError("ambiguous source menu ordinal")
    binding = dict(inputs=input_hashes(inputs), config=config, code_sha256=sha256(__file__))
    if (output / "BINDING.json").exists():
        assert_equal(read(output / "BINDING.json"), binding)
    else:
        write(output / "BINDING.json", binding)
    grouped = defaultdict(list)
    for item in index:
        grouped[sessions[item["session"]]["writer"]].append(item)
    units = {}; pins = {}
    for number, writer in enumerate(sorted(grouped)):
        token = hashlib.sha256(writer.encode()).hexdigest()[:20]; path = output / "writers" / (token + ".json")
        if path.exists():
            if sha256(path) != read(path.with_suffix(".seal.json"))["sha256"]:
                raise ValueError("D34.v1 writer checkpoint changed")
            saved = read(path); assert_equal(saved["binding"], binding)
            for source, expected in saved["source_pins"].items():
                if sha256(source) != expected:
                    raise ValueError("D34.v1 source changed")
        else:
            rows = []; audit = Counter(); source_pins = {}
            for item in sorted(grouped[writer], key=lambda item: item["session"]):
                data_path = Path(inputs["p5_index"]).parent / item["file"]; vectors_path = Path(inputs["p5_index"]).parent / item["vectors"]
                for source, expected in ((data_path, item["sha256"]), (vectors_path, item["vectors_sha256"])):
                    if sha256(source) != expected:
                        raise ValueError("P5 unit changed")
                    source_pins[str(source)] = expected
                with gzip.open(data_path, "rt", encoding="utf8") as stream:
                    session = json.load(stream)
                if session["session"] != item["session"] or session["writer"] != writer:
                    raise ValueError("P5 unit identity differs")
                selected, counts = linked_corrections(session, np.load(vectors_path, allow_pickle=False), decisions, forecasts, config)
                rows.extend(selected); audit.update(counts)
            moments, selected = matched_moments(rows, writer, config.get("seed", 20261017))
            saved = dict(binding=binding, writer=writer, audit=dict(audit), moments=moments, selected=selected, source_pins=source_pins)
            write(path, saved); write(path.with_suffix(".seal.json"), dict(sha256=sha256(path)))
        units[writer] = {key: saved[key] for key in ("audit", "moments", "selected")}; pins.update(saved["source_pins"])
        if number + 1 >= max(1, math.ceil(len(grouped) / 10)) and not (output / "FIRST_TENTH.json").exists():
            write(output / "FIRST_TENTH.json", dict(completed_writers=number+1, total_writers=len(grouped),
                  projected_seconds=(time.perf_counter() - started) * len(grouped) / (number+1)))
        if (output / "YIELD_REQUEST.json").exists():
            return dict(status="yielded", card="D34.v1", completed_writers=number+1)
    write(output / "WRITER_MOMENTS.json", units); write(output / "SOURCE_PINS.json", pins)
    result = summarize(units, config)
    result.update(input_hashes=input_hashes(inputs), elapsed_seconds=time.perf_counter() - started,
        intermediate_hashes={name: sha256(output / name) for name in ("BINDING.json", "WRITER_MOMENTS.json", "SOURCE_PINS.json")})
    write(output / "SUMMARY.json", result)
    return result


def verify(output: Path, inputs: dict, config: dict) -> dict:
    output = Path(output); result = read(output / "SUMMARY.json")
    assert_equal(input_hashes(inputs), result["input_hashes"])
    for name, expected in result["intermediate_hashes"].items():
        if sha256(output / name) != expected:
            raise ValueError("D34.v1 intermediate changed")
    for source, expected in read(output / "SOURCE_PINS.json").items():
        if sha256(source) != expected:
            raise ValueError("D34.v1 source changed")
    actual = summarize(read(output / "WRITER_MOMENTS.json"), config)
    assert_equal(actual, {key: result[key] for key in actual})
    return dict(verified=True, primary_recomputed=actual["primary"], state=actual["state"])
