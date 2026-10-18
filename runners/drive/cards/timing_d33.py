"""D33: chronological personal surprise and logged word-onset pauses.

Own caches use strictly earlier completed sessions. Mixture weight is selected
only on the chronological calibration fifth, then fixed for the final fifth.

DESIGN CHECK: LESSONS 3-5 reread 2026-10-17. NULL: personal surprise adds
no positive pause coefficient beyond the frozen population/nuisance terms.
ALTERNATIVE: a positive coefficient survives donor and shuffled controls.
Opposite, null and marginal intervals retain their signed states; insufficient
support or undefined fits are invalid. Source mutation fails closed. Saved
boundary yield is operational, never a scientific result. No future session
enters a cache or tunes the mixture. Verification rebuilds from source records.
"""
from __future__ import annotations

import math
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from runners.drive.cards.timing_census import read, write, filehash
from runners.drive.cards.timing_p6 import gzread, write_equal, gzip_equal
from runners.drive.cards.timing_stats import bind, check_binding
from runners.drive.cards.timing_checkpoint import regression


WEIGHTS = (0., .1, .25, .5, .75, .9)


def cache(sessions, before):
    uni, bi, contexts = Counter(), Counter(), Counter()
    for session in sessions:
        if not session["end_at"] < before:
            continue
        for sequence in session["training_sequences"]:
            previous = "<s>"
            for word in sequence:
                uni[word] += 1
                bi[(previous, word)] += 1
                contexts[previous] += 1
                previous = word
    return uni, bi, contexts, sum(uni.values())


def cache_probability(word, counts, population):
    uni, bi, contexts, total = counts
    previous = word["context"][-1] if word["context"] else "<s>"
    # One population-distributed pseudo-observation prevents zero cache
    # probabilities without inventing an arbitrary log-loss floor.
    return .5 * (uni[word["token"]] + population) / (total + 1) + .5 * (bi[(previous, word["token"])] + population) / (contexts[previous] + 1)


def population(word, session, extension, p7):
    if not extension:
        return word["population_probability"]
    value = p7.get((session, word["index"]))
    return math.exp(-value) if value is not None else None


def make_rows(records, timing_mode, extension=False, p7=None):
    p7 = p7 or {}
    by_writer = defaultdict(list)
    for record in records:
        by_writer[record["writer"]].append(record)
    writers = sorted(by_writer)
    rows, tuning, exclusions = [], [], []
    if len(writers) < 2:
        return rows, tuning, [dict(writer=w, reason="no independent donor writer") for w in writers]
    for wi, writer in enumerate(writers):
        sessions = sorted(by_writer[writer], key=lambda s: (s["timestamp"], s["session"]))
        a, b = int(.6 * len(sessions)), int(.8 * len(sessions))
        if a < 3 or b - a < 1 or len(sessions) - b < 1:
            exclusions.append(dict(writer=writer, reason="fewer than 3/1/1 chronological sessions"))
            continue
        losses = {alpha: [] for alpha in WEIGHTS}
        for session in sessions[a:b]:
            history = cache(sessions, session["timestamp"])
            for word in session["words"]:
                if not word["is_word"]:
                    continue
                p = population(word, session["session"], extension, p7)
                if p is None or p <= 0:
                    continue
                own = cache_probability(word, history, p)
                for alpha in WEIGHTS:
                    losses[alpha].append(-math.log((1 - alpha) * p + alpha * own))
        if not losses[0.]:
            exclusions.append(dict(writer=writer, reason="no supported calibration words"))
            continue
        alpha = min(WEIGHTS, key=lambda weight: (np.mean(losses[weight]), weight))
        donor = writers[(wi + 1) % len(writers)]
        tuning.append(dict(writer=writer, alpha=alpha, donor=donor, calibration_words=len(losses[0.]),
                           calibration_losses={str(weight): float(np.mean(losses[weight])) for weight in WEIGHTS}))
        for session in sessions[b:]:
            own_cache = cache(sessions, session["timestamp"])
            donor_cache = cache(by_writer[donor], session["timestamp"])
            for word in session["words"]:
                p = population(word, session["session"], extension, p7)
                if not word["is_word"] or p is None or p <= 0 or word["pause_seconds"] is None or word["pause_seconds"] <= 0:
                    continue
                if timing_mode == "per_character" and word["first_delta_characters"] != 1:
                    continue
                own = (1 - alpha) * p + alpha * cache_probability(word, own_cache, p)
                donor_p = (1 - alpha) * p + alpha * cache_probability(word, donor_cache, p)
                rows.append(dict(writer=writer, session=session["session"], index=word["index"],
                                 personal_surprise=math.log(p / own), donor_surprise=math.log(p / donor_p),
                                 population_surprisal=-math.log(p), log_pause=math.log(word["pause_seconds"]),
                                 length=word["length"], log_frequency=word["population_log_frequency"],
                                 sentence_start=int(word["sentence_start"]), after_punctuation=int(word["after_punctuation"])))
    return rows, tuning, exclusions


def analyze(rows, config, controls=True, on_tenth=None, checkpoint_dir=None):
    if len({r["writer"] for r in rows}) < 3:
        return dict(card="D33", state="invalid", reason="fewer than three writers with evaluation words")
    writers = [r["writer"] for r in rows]
    y = [r["log_pause"] for r in rows]
    nuisance = [[1., r["population_surprisal"], r["length"], r["log_frequency"], r["sentence_start"], r["after_punctuation"]] for r in rows]
    primary_x = [[r["personal_surprise"]] + n for r, n in zip(rows, nuisance)]
    donor_x = [[r["donor_surprise"]] + n for r, n in zip(rows, nuisance)]
    kwargs = dict(random_intercept=True, draws=config["bootstrap_draws"], seed=config["seed"])
    def run(x, name, callback=None):
        root = Path(checkpoint_dir) if checkpoint_dir is not None else None
        return regression(x, y, writers, on_tenth=callback,
                          checkpoint=root / name if root is not None else None,
                          yield_requested=(lambda: (root / "YIELD_REQUEST.json").exists()) if root is not None else None,
                          **kwargs)
    result = run(primary_x, "primary" if controls else "writer-shuffle", on_tenth)
    if result.get("status") == "yielded":
        return result
    donor = run(donor_x, "donor") if controls else None
    if donor is not None and donor.get("status") == "yielded":
        return donor
    rng = np.random.default_rng(config["seed"])
    # A separate writer-identity shuffle is rebuilt from sessions in execute.
    shuffled = np.array(primary_x, float)
    for writer in sorted(set(writers)):
        ix = np.flatnonzero(np.array(writers) == writer)
        shuffled[ix, 0] = rng.permutation(shuffled[ix, 0])
    null = run(shuffled, "within-writer-shuffle") if controls else None
    if null is not None and null.get("status") == "yielded":
        return null
    result.update(card="D33", descriptive=True, extension=config["extension"],
                  contrast="coefficient of own-minus-population surprisal on log pause", controls=dict(donor=donor, within_writer_surprise_shuffle=null),
                  route="Positive supports a personal deviation map; null leaves the population model sufficient for these pauses.")
    return result


def validate_inputs(inputs, config):
    if config.get("bootstrap_draws") != 2000 or config.get("seed") != 20261017 or type(config.get("extension")) is not bool:
        raise ValueError("D33 frozen configuration required")
    dependencies = [("p6_index", "p6_completion"), ("tc_primary", "tc_completion")]
    if config["extension"]:
        dependencies.append(("p7_index", "p7_completion"))
    for source, terminal in dependencies:
        complete = Path(inputs[terminal])
        record = read(complete)
        if record.get("status") != "COMPLETE" or not record.get("fresh_process_verified"):
            raise ValueError("D33 dependency is not verified complete")
        path = Path(inputs[source]).resolve()
        relative = path.relative_to(complete.parent.resolve()).as_posix()
        if record["outputs"].get(relative) != filehash(path):
            raise ValueError("D33 dependency completion binding changed")
    if read(inputs["tc_primary"])["timing_mode"] not in {"invalid", "per_character", "first_character_delta"}:
        raise ValueError("D33 unknown timing mode")


def source_data(inputs, config):
    mode = read(inputs["tc_primary"])["timing_mode"]
    index_path = Path(inputs["p6_index"])
    records = []
    for row in read(index_path):
        path = index_path.parent / row["file"]
        path.resolve().relative_to(index_path.parent.resolve())
        if filehash(path) != row["sha256"]:
            raise ValueError("P6 source changed")
        records.append(gzread(path))
    p7 = {}
    if config["extension"]:
        p7_path = Path(inputs["p7_index"])
        for row in read(p7_path):
            if row["domain"] != "typed":
                continue
            path = p7_path.parent / row["file"]
            path.resolve().relative_to(p7_path.parent.resolve())
            if filehash(path) != row["sha256"]:
                raise ValueError("P7 source changed")
            for word in gzread(path)["words"]:
                p7[(row["session"], word["index"])] = word["surprisal_nats"]
    rows, tuning, exclusions = make_rows(records, mode, config["extension"], p7)
    rng = np.random.default_rng(config["seed"])
    identities = rng.permutation([r["writer"] for r in records]).tolist()
    shuffled_records = [dict(record, writer=writer) for record, writer in zip(records, identities)]
    shuffle_rows, _, _ = make_rows(shuffled_records, mode, config["extension"], p7)
    return dict(rows=rows, tuning=tuning, exclusions=exclusions, shuffle_rows=shuffle_rows,
                config=config, timing_mode=mode)


def execute(output: Path, inputs: dict, config: dict) -> dict:
    started = time.monotonic()
    output = Path(output)
    validate_inputs(inputs, config)
    write_equal(output / "D33_RUN_BINDINGS.json", dict(inputs={k: filehash(v) for k, v in inputs.items()}, config=config))
    if (output / "D33_PRIMARY.json").exists():
        return verify(output, inputs, config)["primary"]
    mode = read(inputs["tc_primary"])["timing_mode"]
    if mode == "invalid":
        result = dict(card="D33", state="blocked", reason="TC invalidates pause outcomes", descriptive=True)
        write(output / "D33_PRIMARY.json", result)
        bind(output, inputs, config, ["D33_PRIMARY.json", "D33_RUN_BINDINGS.json"])
        return result
    data = source_data(inputs, config)
    gzip_equal(output / "D33_INTERMEDIATES.json.gz", data)
    def first_tenth(receipt):
        if (output / "FIRST_TENTH.json").exists():
            return
        elapsed = time.monotonic() - started
        projection = elapsed - receipt["primary_seconds"] + receipt["primary_seconds"] * 40
        write(Path(output) / "FIRST_TENTH.json", dict(card="D33", active_seconds=elapsed, **receipt,
              projected_cpu_seconds=projection, forecast_cpu_seconds=3600, projection_exceeds_twice_forecast=projection > 7200,
              method="all preparation observed plus first tenth primary bootstrap projected over four fitted contrasts"))
    result = analyze(data["rows"], config, on_tenth=first_tenth, checkpoint_dir=output)
    if result.get("status") == "yielded":
        return dict(result, card="D33", scientific_admission=False)
    shuffled = analyze(data["shuffle_rows"], config, controls=False, checkpoint_dir=output)
    if shuffled.get("status") == "yielded":
        return dict(shuffled, card="D33", scientific_admission=False)
    result["writer_shuffle"] = shuffled
    result.update(tuning_writers=len(data["tuning"]), excluded_writers=len(data["exclusions"]), timing_mode=mode)
    write(Path(output) / "D33_PRIMARY.json", result)
    write(Path(output) / "D33_TIMING.json", dict(wall_seconds=time.monotonic() - started, observations=len(data["rows"]), forecast_cpu_seconds=3600))
    bind(output, inputs, config, ["D33_PRIMARY.json", "D33_INTERMEDIATES.json.gz", "D33_RUN_BINDINGS.json"])
    return result


def verify(output: Path, inputs: dict, config: dict) -> dict:
    validate_inputs(inputs, config)
    check_binding(output, inputs, config)
    saved = read(Path(output) / "D33_PRIMARY.json")
    mode = read(inputs["tc_primary"])["timing_mode"]
    if saved["state"] == "blocked":
        if mode != "invalid":
            raise ValueError("D33 false timing block")
        return dict(verified=True, primary=saved)
    data = gzread(Path(output) / "D33_INTERMEDIATES.json.gz")
    if data != source_data(inputs, config):
        raise ValueError("D33 source-derived intermediates changed")
    result = analyze(data["rows"], config)
    result["writer_shuffle"] = analyze(data["shuffle_rows"], config, controls=False)
    result.update(tuning_writers=len(data["tuning"]), excluded_writers=len(data["exclusions"]), timing_mode=mode)
    if result != saved:
        raise ValueError("D33 primary does not recompute")
    return dict(verified=True, primary=result)
