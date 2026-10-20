"""D36: joke liking versus mismatched-control-adjusted resolution rate.

Rater-cluster uncertainty is conditional on the frozen Jester joke set. A
separate joke bootstrap describes stimulus sensitivity; neither is substituted
for the packet's primary. Ordinary GPT-2 word surprisal is not resolution gain.
"""
from __future__ import annotations

import math
import time
from pathlib import Path

import numpy as np

from runners.drive.cards import states_v2 as states
from runners.drive.cards.timing_census import read, write, filehash
from runners.drive.cards.timing_p6 import gzread, gzwrite, write_equal, progress
from runners.drive.cards.timing_p7 import CachedScorer
from runners.drive.cards.timing_text import TOKEN, WORD
from runners.drive.cards.timing_stats import bind, check_binding

RATING_POPULATION = "All 150 texts remain in P7; unrated jokes stay eligible as mismatch donors when they have a setup and punchline, but cannot enter the rating contrast."


def split_jokes(jokes):
    import spacy
    nlp = spacy.blank("en")
    nlp.add_pipe("sentencizer")
    eligible, excluded = [], []
    for row in jokes:
        sentences = [s for s in nlp(row["text"]).sents if s.text.strip()]
        if len(sentences) < 2:
            excluded.append(dict(joke_id=str(row["joke_id"]), reason="one sentence"))
            continue
        start = sentences[-1].start_char
        eligible.append(dict(joke_id=str(row["joke_id"]), setup=row["text"][:start], punchline=row["text"][start:], full_text=row["text"]))
    return eligible, excluded


def mismatches(jokes, seed):
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(jokes))
    # One seeded cycle, no same-joke donor; exact duplicate punchlines refuse
    # instead of turning a mismatched control into a repeated true condition.
    donors = {int(order[i]): int(order[(i + 1) % len(order)]) for i in range(len(order))}
    if len(jokes) < 2 or any(jokes[i]["punchline"] == jokes[j]["punchline"] for i, j in donors.items()):
        raise ValueError("mismatched punchline control contains an identical punchline")
    return donors


def reread_mean(scorer, prefix, setup):
    scores = []
    for match in TOKEN.finditer(setup):
        if not WORD.fullmatch(match.group()):
            continue
        scores.append(scorer.score(prefix + setup[:match.start()], match.group()))
    if not scores:
        raise ValueError("setup has no lexical words")
    return float(np.mean([s["surprisal_nats"] for s in scores])), scores


def residual(value, covariates):
    if covariates is None:
        return np.array(value, float) - np.mean(value)
    x = np.column_stack([np.ones(len(value)), covariates])
    if np.linalg.matrix_rank(x) != x.shape[1]:
        raise ValueError("D36 extension covariates not identifiable")
    return np.array(value, float) - x @ np.linalg.lstsq(x, value, rcond=None)[0]


def correlation(x, y, covariates=None):
    a, b = residual(x, covariates), residual(y, covariates)
    # Exact covariate fits leave roundoff, not a measurable residual signal.
    for raw, centered in ((x, a), (y, b)):
        if np.linalg.norm(centered) <= np.finfo(float).eps * len(centered) * max(1., np.linalg.norm(raw)):
            return None
    denominator = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denominator <= 0:
        return None
    return float(a @ b / denominator)


def analyze(features, ratings, config, on_tenth=None, resume=None, on_checkpoint=None):
    rates = np.array([r["rate"] for r in features])
    # Canonical layout keeps reductions identical after column filtering/NPZ replay.
    ratings = np.ascontiguousarray(ratings, dtype=float)
    if ratings.ndim != 2 or len(features) != ratings.shape[1] or len(features) < 4 or ratings.shape[0] < 3:
        return dict(card="D36", state="invalid", reason="insufficient rated jokes or independent raters")
    observed = np.isfinite(ratings)
    counts = observed.sum(0)
    if np.any(counts == 0) or not np.isfinite(rates).all() or np.isinf(ratings).any():
        return dict(card="D36", state="invalid", reason="insufficient rated jokes or independent raters")
    values = np.where(observed, ratings, 0.)
    means = values.sum(0) / counts
    covariates = np.array([[r["punchline_surprisal"], r["punchline_tokens"]] for r in features]) if config["extension"] else None
    try:
        point = correlation(rates, means, covariates)
    except ValueError as exc:
        return dict(card="D36", state="invalid", reason=str(exc))
    if point is None:
        return dict(card="D36", state="invalid", reason="constant resolution rate or rating")
    rng = np.random.default_rng(config["seed"])
    rater_samples, joke_samples, null = [], [], []
    if resume:
        rater_samples, joke_samples, null = resume["rater_samples"], resume["joke_samples"], resume["null"]
        if len({len(rater_samples), len(joke_samples), len(null)}) != 1 or len(rater_samples) > config["bootstrap_draws"]:
            raise ValueError("invalid D36 bootstrap checkpoint")
        rng.bit_generator.state = resume["rng_state"]
    centered_rating = residual(means, covariates)
    fitted_rating = means - centered_rating
    started = time.monotonic()
    observed_float = observed.astype(float)
    for draw in range(len(rater_samples), config["bootstrap_draws"]):
        # Whole raters, preserving every within-rater missingness pattern.
        selected = rng.integers(0, len(ratings), len(ratings))
        weights = np.bincount(selected, minlength=len(ratings)).astype(float)
        denominator = weights @ observed_float
        if np.any(denominator == 0):
            return dict(card="D36", state="invalid", reason="rater-bootstrap replicate has an unrated joke")
        rater_samples.append(correlation(rates, (weights @ values) / denominator, covariates))
        jj = rng.integers(0, len(features), len(features))
        try:
            joke_samples.append(correlation(rates[jj], means[jj], None if covariates is None else covariates[jj]))
        except ValueError:
            joke_samples.append(None)
        null.append(correlation(rates, fitted_rating + rng.permutation(centered_rating), covariates))
        if on_tenth is not None and draw + 1 == math.ceil(config["bootstrap_draws"] / 10):
            on_tenth(dict(bootstrap_seconds=time.monotonic() - started, completed_draws=draw + 1, total_draws=config["bootstrap_draws"]))
        if on_checkpoint is not None and (draw + 1) % math.ceil(config["bootstrap_draws"] / 10) == 0:
            on_checkpoint(dict(rater_samples=rater_samples, joke_samples=joke_samples, null=null, rng_state=rng.bit_generator.state))
    if any(value is None for value in rater_samples + null):
        return dict(card="D36", state="invalid", reason="undefined bootstrap/permutation correlation")
    joke_invalid = sum(value is None for value in joke_samples)
    sensitivity = dict(state="invalid", reason="undefined joke-bootstrap replicate", undefined_draws=joke_invalid) if joke_invalid else dict(
        state="descriptive", ci_low=float(np.quantile(joke_samples, .025)), ci_high=float(np.quantile(joke_samples, .975)))
    low, high = np.quantile(rater_samples, [.025, .975]).tolist()
    se = float(np.std(rater_samples, ddof=1))
    z = point / se if se > 0 else None
    return dict(card="D36", descriptive=True, effect=point, ci_low=low, ci_high=high, bootstrap_se=se, z=z,
                wald_p_two_sided=math.erfc(abs(z) / math.sqrt(2)) if z is not None else None,
                p_reference="descriptive normal Wald from rater-cluster SE; conditional on the frozen joke set",
                state=states.contrast_state(point, low, high), extension=config["extension"],
                jokes=len(features), raters=len(ratings), bootstrap_draws=config["bootstrap_draws"], seed=config["seed"],
                interval_population="rater-cluster bootstrap, conditional on these eligible jokes; not generalization across jokes",
                joke_bootstrap_sensitivity=sensitivity,
                joke_permutation_control=dict(mean_correlation=float(np.mean(null)),
                    two_sided_p=(1 + sum(abs(value) >= abs(point) for value in null)) / (1 + len(null)),
                    method="rating residual permutation under the covariate-only model; no outcome-selected donor"),
                route="A positive gives beauty-as-fast-resolution a first descriptive hook; null leaves the broader claim untested at this resolution.")


def native_mean(scores):
    if not scores:
        raise ValueError("empty D36 reread scores")
    for score in scores:
        native = score["native_token_nll"]
        if not native or len(native) != len(score["native_token_ids"]) or not all(math.isfinite(v) and v >= 0 for v in native):
            raise ValueError("invalid D36 native reread scores")
        if sum(native) != score["surprisal_nats"]:
            raise ValueError("D36 native losses do not sum to word surprisal")
    return float(np.mean([s["surprisal_nats"] for s in scores]))


def reduce_reread(record):
    true_mean, mismatch_mean = native_mean(record["true"]), native_mean(record["mismatch"])
    if len(record["true"]) != len(record["mismatch"]) or record["punchline_tokens"] <= 0:
        raise ValueError("D36 conditions do not score the same setup")
    gain = mismatch_mean - true_mean
    return dict(joke_id=record["joke_id"], mismatch_joke_id=record["mismatch_joke_id"],
                setup_alone_mean=record["setup_alone_mean"], true_reread_mean=true_mean,
                mismatch_reread_mean=mismatch_mean, resolution_gain=gain,
                punchline_tokens=record["punchline_tokens"], punchline_surprisal=record["punchline_surprisal"],
                rate=gain / record["punchline_tokens"])


def rated_population(features, ratings):
    """An undefined mean rating is a disclosed stimulus exclusion, not zero."""
    if ratings.ndim != 2 or ratings.shape[1] != len(features):
        raise ValueError("D36 rating-column alignment changed")
    keep = np.isfinite(ratings).any(0)
    excluded = [dict(joke_id=row["joke_id"], reason="no observed ratings") for row, ok in zip(features, keep) if not ok]
    return [row for row, ok in zip(features, keep) if ok], ratings[:, keep], excluded


class CooperativeYield(Exception):
    pass


def execute(output: Path, inputs: dict, config: dict) -> dict:
    if type(config.get("extension")) is not bool or config.get("bootstrap_draws") != 2000 or config.get("seed") != 20261017:
        raise ValueError("D36 frozen configuration required")
    output = Path(output)
    if (output / "TIMING_BINDINGS.json").exists():
        return verify(output, inputs, config)["primary"]
    write_equal(output / "D36_RUN_BINDINGS.json", dict(config=config, source_sha256=filehash(__file__),
                inputs={key: filehash(value) for key, value in inputs.items()}))
    previous = read(output / "D36_PROGRESS.json") if (output / "D36_PROGRESS.json").exists() else {}
    prior_seconds = previous.get("active_seconds", 0.)
    started = time.monotonic()
    p7_path = Path(inputs["p7_index"])
    if read(p7_path.parent / "P7_PRIMARY.json").get("pilot_only"):
        raise ValueError("D36 requires the whole P7 pass")
    p7 = {str(r["joke_id"]): r for r in read(p7_path) if r["domain"] == "jester"}
    p7_bindings = read(p7_path.parent / "TIMING_BINDINGS.json")
    if any(p7_bindings["inputs"][key] != filehash(inputs[key]) for key in ("jester_texts", "model_manifest")):
        raise ValueError("P7 used different frozen joke text or model manifest")
    if len(read(inputs["jester_texts"])) != 150:
        raise ValueError("D36 requires the frozen 150-joke Jester intake")
    jokes, excluded = split_jokes(read(inputs["jester_texts"]))
    jokes.sort(key=lambda row: row["joke_id"])
    if any(joke["joke_id"] not in p7 for joke in jokes):
        raise ValueError("P7 joke coverage incomplete")
    if len({j["joke_id"] for j in jokes}) != len(jokes) or any(not j["joke_id"].isalnum() for j in jokes):
        raise ValueError("D36 requires unique alphanumeric joke identities")
    donors = mismatches(jokes, config["seed"])
    manifest = read(inputs["model_manifest"])
    for path, expected in manifest["files"].items():
        if filehash(path) != expected:
            raise ValueError("D36 reader source changed")
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    torch.set_num_threads(2)
    tokenizer = AutoTokenizer.from_pretrained(manifest["tokenizer_path"], local_files_only=True, use_fast=True)
    model = AutoModelForCausalLM.from_pretrained(manifest["model_path"], local_files_only=True, torch_dtype=torch.float32).cpu().eval()
    if model.config.model_type != "gpt2" or model.config.n_layer != 24 or model.config.n_embd != 1024:
        raise ValueError("D36 reader is not GPT-2 medium")
    features, rereads = [], []
    for i, joke in enumerate(jokes):
        source = p7_path.parent / p7[joke["joke_id"]]["file"]
        source.resolve().relative_to(p7_path.parent.resolve())
        if filehash(source) != p7[joke["joke_id"]]["sha256"]:
            raise ValueError("P7 joke scores changed")
        dest = output / "rereads" / (joke["joke_id"] + ".json.gz")
        if dest.exists():
            if read(dest.with_suffix(".receipt.json"))["sha256"] != filehash(dest):
                raise ValueError("D36 reread checkpoint changed")
            record = gzread(dest)
            if record["joke_id"] != joke["joke_id"] or record["mismatch_joke_id"] != jokes[donors[i]]["joke_id"]:
                raise ValueError("D36 mismatch checkpoint changed")
            features.append(reduce_reread(record))
            rereads.append(dict(file=dest.relative_to(output).as_posix(), sha256=filehash(dest)))
            continue
        words = gzread(source)["words"]
        setup_scores = [w["surprisal_nats"] for w in words if w["is_word"] and w["end"] <= len(joke["setup"])]
        punchline_scores = [w["surprisal_nats"] for w in words if w["is_word"] and w["start"] >= len(joke["setup"])]
        if not setup_scores or not punchline_scores:
            raise ValueError("setup/punchline score alignment empty")
        scorer = CachedScorer(model, tokenizer, torch)
        true_mean, true_scores = reread_mean(scorer, joke["full_text"] + "\n\n", joke["setup"])
        donor = jokes[donors[i]]
        mismatch_mean, mismatch_scores = reread_mean(scorer, joke["setup"] + donor["punchline"] + "\n\n", joke["setup"])
        punchline_tokens = len(tokenizer(joke["punchline"], add_special_tokens=False)["input_ids"])
        if punchline_tokens == 0:
            raise ValueError("empty tokenized punchline")
        record = dict(joke_id=joke["joke_id"], mismatch_joke_id=donor["joke_id"], setup_alone_mean=float(np.mean(setup_scores)),
                      punchline_tokens=punchline_tokens, punchline_surprisal=float(np.mean(punchline_scores)),
                      true=true_scores, mismatch=mismatch_scores)
        features.append(reduce_reread(record))
        gzwrite(dest, record)
        write(dest.with_suffix(".receipt.json"), dict(sha256=filehash(dest)))
        rereads.append(dict(file=dest.relative_to(output).as_posix(), sha256=filehash(dest)))
        overshoot = False
        if i + 1 == math.ceil(len(jokes) / 10):
            elapsed = prior_seconds + time.monotonic() - started
            overshoot = elapsed * len(jokes) / (i + 1) > 7200
            write(output / "FIRST_TENTH.json", dict(completed_jokes=i + 1, total_jokes=len(jokes),
                  elapsed_seconds=elapsed, projected_scoring_seconds=elapsed * len(jokes) / (i + 1), forecast_cpu_seconds=3600,
                  bootstrap_projection_pending=True, includes_model_load=True, forecast_overshoot=overshoot))
        progress(output / "D36_PROGRESS.json", dict(phase="rereads", completed_jokes=i + 1,
                 active_seconds=prior_seconds + time.monotonic() - started))
        if overshoot or (output / "YIELD_REQUEST.json").exists():
            return dict(card="D36", status="yielded", reason="saved joke checkpoint; forecast overshoot" if overshoot else "saved joke checkpoint",
                        completed_jokes=i + 1)
    with np.load(inputs["jester_ratings"], allow_pickle=False) as archive:
        matrix = np.asarray(archive["ratings"], float)
        columns = [str(value) for value in archive["joke_ids"].tolist()]
    if matrix.ndim != 2 or len(set(columns)) != len(columns) or matrix.shape[1] != len(columns) or np.any(np.isinf(matrix)) or np.any(np.abs(matrix[np.isfinite(matrix)]) > 10):
        raise ValueError("invalid Jester rating matrix; missing values must be NaN, ratings within [-10,10]")
    if set(columns) != {str(row["joke_id"]) for row in read(inputs["jester_texts"])}:
        raise ValueError("D36 ratings do not retain all 150 frozen joke columns")
    support = [dict(joke_id=identity, observed_ratings=int(np.isfinite(matrix[:, i]).sum())) for i, identity in enumerate(columns)]
    ratings = matrix[:, [columns.index(row["joke_id"]) for row in features]]
    ratings = ratings[np.isfinite(ratings).any(1)]
    eligible_features, eligible_ratings, unrated = rated_population(features, ratings)
    before_bootstrap = prior_seconds + time.monotonic() - started
    bootstrap_overshoot = False
    def on_tenth(receipt):
        nonlocal bootstrap_overshoot
        projection = before_bootstrap + receipt["bootstrap_seconds"] * receipt["total_draws"] / receipt["completed_draws"]
        bootstrap_overshoot = projection > 7200
        write(output / "BOOTSTRAP_FIRST_TENTH.json", dict(receipt, elapsed_seconds=prior_seconds + time.monotonic() - started,
              projected_cpu_seconds=projection, forecast_cpu_seconds=3600, forecast_overshoot=projection > 7200))
    checkpoint_path = output / "D36_BOOTSTRAP_CHECKPOINT.json"
    def on_checkpoint(record):
        progress(checkpoint_path, record)
        progress(checkpoint_path.with_suffix(".receipt.json"), dict(sha256=filehash(checkpoint_path)))
        progress(output / "D36_PROGRESS.json", dict(phase="bootstrap", completed_draws=len(record["rater_samples"]),
                 active_seconds=prior_seconds + time.monotonic() - started))
        if bootstrap_overshoot or (output / "YIELD_REQUEST.json").exists():
            raise CooperativeYield("saved rater-bootstrap checkpoint")
    resume = None
    if checkpoint_path.exists():
        if filehash(checkpoint_path) != read(checkpoint_path.with_suffix(".receipt.json"))["sha256"]:
            raise ValueError("D36 bootstrap checkpoint changed")
        resume = read(checkpoint_path)
    try:
        result = analyze(eligible_features, eligible_ratings, config, on_tenth, resume, on_checkpoint)
    except CooperativeYield as exc:
        return dict(card="D36", status="yielded", reason=str(exc))
    result.update(excluded_one_sentence_jokes=len(excluded), excluded_unrated_eligible_jokes=len(unrated),
                  total_source_unrated_jokes=sum(row["observed_ratings"] == 0 for row in support),
                  rating_eligibility=RATING_POPULATION)
    write(output / "D36_FEATURES.json", features)
    write(output / "D36_EXCLUSIONS.json", excluded + unrated)
    write(output / "D36_RATING_SUPPORT.json", support)
    write(output / "D36_REREADS.json", rereads)
    np.savez_compressed(output / "D36_RATINGS.npz", ratings=ratings)
    write(output / "D36_PRIMARY.json", result)
    write(output / "D36_TIMING.json", dict(wall_seconds=prior_seconds + time.monotonic() - started, forecast_cpu_seconds=3600))
    bind(output, inputs, config, ["D36_FEATURES.json", "D36_RATINGS.npz", "D36_PRIMARY.json", "D36_EXCLUSIONS.json", "D36_REREADS.json", "D36_RATING_SUPPORT.json"])
    return result


def verify(output: Path, inputs: dict, config: dict) -> dict:
    check_binding(output, inputs, config)
    features = read(Path(output) / "D36_FEATURES.json")
    recomputed = []
    for row in read(Path(output) / "D36_REREADS.json"):
        path = Path(output) / row["file"]
        path.resolve().relative_to(Path(output).resolve())
        if filehash(path) != row["sha256"]:
            raise ValueError("D36 native reread changed")
        recomputed.append(reduce_reread(gzread(path)))
    if features != recomputed:
        raise ValueError("D36 resolution features do not recompute from native losses")
    with np.load(Path(output) / "D36_RATINGS.npz", allow_pickle=False) as archive:
        ratings = archive["ratings"]
    eligible_features, eligible_ratings, unrated = rated_population(features, ratings)
    result = analyze(eligible_features, eligible_ratings, config)
    exclusions = read(Path(output) / "D36_EXCLUSIONS.json")
    if [row for row in exclusions if row["reason"] == "no observed ratings"] != unrated:
        raise ValueError("D36 unrated-joke eligibility does not recompute")
    result.update(excluded_one_sentence_jokes=sum(row["reason"] == "one sentence" for row in exclusions),
                  excluded_unrated_eligible_jokes=len(unrated),
                  total_source_unrated_jokes=sum(row["observed_ratings"] == 0 for row in read(Path(output) / "D36_RATING_SUPPORT.json")),
                  rating_eligibility=RATING_POPULATION)
    if result != read(Path(output) / "D36_PRIMARY.json"):
        raise ValueError("D36 primary does not recompute")
    return dict(verified=True, primary=result)
