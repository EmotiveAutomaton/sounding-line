"""D17: normalized pause mixtures and writer stability across sessions.

The location-specific component count minimizes BIC over 1..5 Gaussian
components on log(interval / session median within-word interval). Component
distributions are pooled; only session mixture weights vary. No component is
treated as an observed psychological state.

DESIGN CHECK: LESSONS sections 3-5 reread 2026-10-17. Under the NULL,
session weights without stable writer differences must not pass the positive
ICC rule; under the ALTERNATIVE, planted writer weights must be recovered by
the serialized raw-log pipeline. Positive means percentile CI lower > 0;
other valid bands follow states_v2, undefined support is invalid, never null.
Reject incomplete/changed TC, foundation or raw sources before estimation.
Drop whole observed intervals crossing request-to-open system waits; never
subtract a guessed waiting time. Bootstrap uncertainty conditions on the
selected pooled mixture, whose BIC is descriptive, not a cognitive-state test.
"""
from __future__ import annotations

import json
import hashlib
import math
import re
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.mixture import GaussianMixture
from scipy.special import logsumexp

from runners.drive.cards import states_v2 as states
from runners.drive.cards.timing_census import read, write, filehash, session_paths
from runners.drive.cards.timing_p6 import gzwrite, gzread, write_equal, gzip_equal, progress
from runners.drive.cards.timing_stats import bind, check_binding
from runners.stage9.coauthor import units, text_of, delta_ops, apply_delta


def intervals(events, mode):
    if mode not in ("per_character", "first_character_delta") or not events:
        raise ValueError("unsupported timing mode or empty raw session")
    doc = units(events[0]["currentDoc"])
    previous, last_clock = None, -math.inf
    pending_wait = crossed_wait = False
    out = dict(within_word=[], between_words=[], between_sentences=[], excluded_zero_pre_delta=0,
               excluded_multicharacter=0, excluded_system_wait=0)
    for event in events:
        clock = float(event["eventTimestamp"]) / 1000
        if not math.isfinite(clock) or clock < last_clock:
            raise ValueError("invalid interval chronology")
        last_clock = clock
        if event.get("eventName") == "suggestion-get":
            pending_wait = crossed_wait = True
        elif event.get("eventName") == "suggestion-open":
            pending_wait = False
        ops = delta_ops(event.get("textDelta"))
        if not ops:
            continue
        insertion = sum(len(op["insert"]) for op in ops if "insert" in op)
        if event.get("eventSource") == "user" and insertion and previous is not None:
            out["excluded_zero_pre_delta"] += int(clock == previous)
            out["excluded_multicharacter"] += int(mode == "per_character" and insertion != 1)
            out["excluded_system_wait"] += int(crossed_wait or pending_wait)
        if event.get("eventSource") == "user" and insertion and previous is not None and clock > previous and not (crossed_wait or pending_wait):
            position = 0
            for op in ops:
                if "insert" not in op:
                    position += op.get("retain", op.get("delete", 0))
                    continue
                text = op["insert"]
                if text and text[0].isalnum() and (mode != "per_character" or insertion == 1):
                    before = text_of(doc[:position])
                    value = clock - previous
                    if before and before[-1].isalnum():
                        out["within_word"].append(value)
                    elif not before.strip() or re.search(r"[.!?]\s*$", before):
                        out["between_sentences"].append(value)
                    else:
                        out["between_words"].append(value)
                break  # Only the first character has a measured pre-delta interval.
        doc, _, _ = apply_delta(doc, [None] * len(doc), event.get("textDelta"))
        previous = clock
        crossed_wait = pending_wait
    return out


def session_weights(values, means, variances, initial):
    logs = -.5 * (np.log(2 * np.pi * variances)[None, :] + (np.asarray(values)[:, None] - means[None, :]) ** 2 / variances[None, :])
    weights = initial.copy()
    for _ in range(2000):
        joint = logs + np.log(np.maximum(weights, 1e-300))[None, :]
        updated = np.exp(joint - logsumexp(joint, axis=1)[:, None]).mean(0)
        if np.max(abs(updated - weights)) < 1e-8:
            return updated
        weights = updated
    raise ValueError("session mixture weights failed to converge")


class CooperativeYield(Exception):
    pass


def mixture(sessions, location, seed, checkpoint_root=None, started=None, prior_seconds=0.):
    supported = [r for r in sessions if r["intervals"]["within_word"] and r["intervals"][location]]
    values, groups = [], []
    for row in supported:
        baseline = float(np.median(row["intervals"]["within_word"]))
        a = np.log(np.asarray(row["intervals"][location]) / baseline)
        values.extend(a.tolist())
        groups.append((row, a, baseline))
    if len(values) < 20:
        return [], dict(reason="fewer than 20 valid normalized intervals")
    x = np.array(values)[:, None]
    data_hash = hashlib.sha256(x.tobytes()).hexdigest()
    candidates = []
    for k in range(1, 6):
        if len(x) < k * 3 or len(np.unique(x)) < k:
            continue
        path = Path(checkpoint_root) / f"D17_MIXTURE_K{k}.json" if checkpoint_root else None
        if path is not None and path.exists():
            if read(path.with_suffix(".receipt.json"))["sha256"] != filehash(path):
                raise ValueError("D17 mixture checkpoint bytes changed")
            candidate = read(path)
            if candidate["data_sha256"] != data_hash or candidate["location"] != location or candidate["seed"] != seed:
                raise ValueError("D17 mixture checkpoint binding changed")
        else:
            fit_started = time.monotonic()
            model = GaussianMixture(k, covariance_type="full", n_init=3, max_iter=300, random_state=seed, reg_covar=1e-6).fit(x)
            if not model.converged_:
                raise ValueError("pause mixture failed to converge")
            candidate = dict(bic=float(model.bic(x)), components=k, means=model.means_[:, 0].tolist(),
                             variances=model.covariances_[:, 0, 0].tolist(), weights=model.weights_.tolist(),
                             data_sha256=data_hash, location=location, seed=seed, fit_seconds=time.monotonic() - fit_started)
            if path is not None:
                write(path, candidate)
                write(path.with_suffix(".receipt.json"), dict(sha256=filehash(path)))
        candidates.append(candidate)
        if checkpoint_root:
            elapsed = prior_seconds + time.monotonic() - started
            progress(Path(checkpoint_root) / "D17_PROGRESS.json", dict(phase="mixture", components_completed=k, active_seconds=elapsed))
            if k == 1 and not (Path(checkpoint_root) / "FIRST_TENTH.json").exists():
                projection = elapsed + candidate["fit_seconds"] * 14
                write(Path(checkpoint_root) / "FIRST_TENTH.json", dict(card="D17", phase="first of five component-count fits (1+2+3+4+5 complexity)",
                      active_seconds_from_first_start=elapsed, projected_cpu_seconds=projection, forecast_cpu_seconds=3600,
                      projection_exceeds_twice_forecast=projection > 7200,
                      method="all observed extraction/preparation plus first component fit extrapolated by total component count"))
            if (Path(checkpoint_root) / "YIELD_REQUEST.json").exists():
                raise CooperativeYield("saved mixture component checkpoint")
    model = min(candidates, key=lambda item: (item["bic"], item["components"]))
    k = model["components"]
    order = np.argsort(model["means"])
    means = np.array(model["means"])[order]
    variances = np.array(model["variances"])[order]
    initial = np.array(model["weights"])[order]
    weights = []
    for row, a, baseline in groups:
        fitted = session_weights(a, means, variances, initial)
        weights.append(dict(writer=row["writer"], session=row["session"], slowest_weight=float(fitted[-1]),
                            component_weights=fitted.tolist(), intervals=len(a), within_word_median_seconds=baseline))
    return weights, dict(components=k, bic=[dict(components=c["components"], bic=c["bic"]) for c in candidates],
                         log_scale_means=means.tolist(), log_scale_variances=variances.tolist(), pooled_weights=initial.tolist())


def icc(groups):
    if len(groups) < 3 or any(len(g) < 2 for g in groups):
        raise ValueError("ICC needs three writers with repeated sessions")
    sizes = np.array([len(g) for g in groups], float)
    means = np.array([np.mean(g) for g in groups])
    n = sizes.sum()
    grand = float(means @ sizes / n)
    between = float((sizes * (means - grand) ** 2).sum() / (len(groups) - 1))
    within = sum(float(((np.array(g) - np.mean(g)) ** 2).sum()) for g in groups) / (n - len(groups))
    effective = (n - float(sizes @ sizes) / n) / (len(groups) - 1)
    variance = (between - within) / effective
    denominator = variance + within
    if denominator <= 0:
        return None
    return variance / denominator


def analyze(weights, config):
    by_writer = defaultdict(list)
    for row in weights:
        by_writer[row["writer"]].append(row["slowest_weight"])
    groups = [by_writer[w] for w in sorted(by_writer) if len(by_writer[w]) >= 2]
    if len(groups) < 3:
        return dict(state="invalid", reason="fewer than three writers with repeated supported sessions")
    point = icc(groups)
    if point is None:
        return dict(state="invalid", reason="constant slowest-component weights, ICC undefined")
    rng = np.random.default_rng(config["seed"])
    samples = [icc([groups[i] for i in rng.integers(0, len(groups), len(groups))]) for _ in range(config["bootstrap_draws"])]
    if any(v is None for v in samples):
        return dict(state="invalid", reason="undefined writer-bootstrap ICC")
    low, high = np.quantile(samples, [.025, .975]).tolist()
    se = float(np.std(samples, ddof=1))
    z = point / se if se > 0 else None
    pool = np.concatenate(groups)
    rng.shuffle(pool)
    shuffled, start = [], 0
    for g in groups:
        shuffled.append(pool[start:start + len(g)].tolist())
        start += len(g)
    return dict(effect=point, ci_low=low, ci_high=high, state=states.contrast_state(point, low, high),
                bootstrap_se=se, z=z, wald_p_two_sided=math.erfc(abs(z) / math.sqrt(2)) if z is not None else None,
                p_reference="approximate two-sided normal Wald test; descriptive; state remains percentile-CI based",
                writers=len(groups), sessions=sum(map(len, groups)), writer_shuffle_icc=icc(shuffled),
                bootstrap_draws=config["bootstrap_draws"], seed=config["seed"])


def validate_inputs(inputs, config):
    if config.get("bootstrap_draws") != 2000 or config.get("seed") != 20261017 or type(config.get("extension")) is not bool:
        raise ValueError("D17 frozen configuration required")
    complete = Path(inputs["tc_completion"]).resolve()
    primary = Path(inputs["tc_primary"]).resolve()
    receipt = read(complete)
    if receipt.get("status") != "COMPLETE" or receipt.get("fresh_process_verified") is not True:
        raise ValueError("D17 requires verified TC completion")
    if receipt["outputs"].get(primary.relative_to(complete.parent).as_posix()) != filehash(primary):
        raise ValueError("D17 TC completion binding changed")
    mode = read(primary)["timing_mode"]
    if mode not in ("invalid", "per_character", "first_character_delta"):
        raise ValueError("unsupported timing mode")
    return mode


def sources(inputs):
    rows = read(inputs["raw_roster"])
    roster = {r["session"]: r for r in rows}
    if not rows or len(roster) != len(rows):
        raise ValueError("empty or duplicate raw roster")
    root = Path(inputs["repo_root"]).resolve()
    for row, path in session_paths(inputs):
        meta = roster[row["session"]]
        session = read(path)
        if session["session"] != row["session"] or session["writer"] != row["writer"] or meta["writer"] != row["writer"] or session["source_sha256"] != meta["source_sha256"]:
            raise ValueError("D17 foundation/raw identity mismatch")
        source = (root / meta["path"]).resolve()
        source.relative_to(root)
        if filehash(source) != meta["source_sha256"]:
            raise ValueError("D17 raw source changed")
        yield row, meta, source


def execute(output: Path, inputs: dict, config: dict) -> dict:
    mode = validate_inputs(inputs, config)
    output = Path(output)
    if (output / "D17_PRIMARY.json").exists():
        return verify(output, inputs, config)["primary"]
    write_equal(output / "D17_RUN_BINDINGS.json", dict(config=config, inputs={k: (str(Path(v).resolve()) if Path(v).is_dir() else filehash(v)) for k, v in inputs.items()}))
    previous = read(output / "D17_PROGRESS.json") if (output / "D17_PROGRESS.json").exists() else {}
    prior_seconds, started = previous.get("active_seconds", 0.), time.monotonic()
    if mode == "invalid":
        result = dict(card="D17", state="blocked", reason="TC invalidates pause outcomes", descriptive=True)
        write(output / "D17_PRIMARY.json", result)
        bind(output, inputs, config, ["D17_PRIMARY.json"])
        return result
    sessions = []
    for row, source_meta, source in sources(inputs):
        checkpoint = output / "intervals" / (hashlib.sha256(row["session"].encode()).hexdigest() + ".json")
        if checkpoint.exists():
            if read(checkpoint.with_suffix(".receipt.json"))["sha256"] != filehash(checkpoint):
                raise ValueError("D17 interval checkpoint bytes changed")
            saved = read(checkpoint)
            if saved["source_sha256"] != source_meta["source_sha256"] or saved["timing_mode"] != mode or saved["session"] != row["session"] or saved["writer"] != row["writer"]:
                raise ValueError("D17 interval checkpoint changed")
            values = saved["intervals"]
        else:
            with source.open(encoding="utf-8") as stream:
                values = intervals([json.loads(line) for line in stream], mode)
            write(checkpoint, dict(session=row["session"], writer=row["writer"], source_sha256=source_meta["source_sha256"], timing_mode=mode, intervals=values))
            write(checkpoint.with_suffix(".receipt.json"), dict(sha256=filehash(checkpoint)))
        sessions.append(dict(session=row["session"], writer=row["writer"], intervals=values))
        progress(output / "D17_PROGRESS.json", dict(phase="extraction", sessions=len(sessions), active_seconds=prior_seconds + time.monotonic() - started))
        if (output / "YIELD_REQUEST.json").exists():
            return dict(status="yielded", card="D17", reason="saved interval session checkpoint", completed_sessions=len(sessions))
    location = "between_sentences" if config["extension"] else "between_words"
    try:
        weights, model = mixture(sessions, location, config["seed"], output, started, prior_seconds)
    except CooperativeYield as exc:
        return dict(status="yielded", card="D17", reason=str(exc))
    result = analyze(weights, config)
    result.update(card="D17", descriptive=True, location=location, mixture=model, timing_mode=mode,
                  input_sessions=len(sessions), supported_sessions=len(weights),
                  zero_pre_delta_intervals_excluded=sum(row["intervals"]["excluded_zero_pre_delta"] for row in sessions),
                  multicharacter_deltas_excluded=sum(row["intervals"]["excluded_multicharacter"] for row in sessions),
                  system_wait_intervals_excluded=sum(row["intervals"]["excluded_system_wait"] for row in sessions),
                  interval="writer-cluster percentile bootstrap conditional on the selected pooled mixture",
                  contrast="writer intraclass correlation of slowest normalized pause mixture weight",
                  route="Stable normalized weights support writer process boxes; no psychological component identity is assumed.")
    gzip_equal(output / "D17_INTERVALS.json.gz", sessions)
    write_equal(output / "D17_WEIGHTS.json", weights)
    write_equal(output / "D17_PRIMARY.json", result)
    bind(output, inputs, config, ["D17_WEIGHTS.json", "D17_INTERVALS.json.gz", "D17_PRIMARY.json"])
    return result


def verify(output: Path, inputs: dict, config: dict) -> dict:
    mode = validate_inputs(inputs, config)
    check_binding(output, inputs, config)
    saved = read(Path(output) / "D17_PRIMARY.json")
    if saved["state"] == "blocked":
        if mode != "invalid":
            raise ValueError("D17 false timing block")
        return dict(verified=True, primary=saved)
    sessions = gzread(Path(output) / "D17_INTERVALS.json.gz")
    authenticated = [(r["session"], r["writer"]) for r, _, _ in sources(inputs)]
    if authenticated != [(r["session"], r["writer"]) for r in sessions]:
        raise ValueError("D17 saved session identities changed")
    weights = read(Path(output) / "D17_WEIGHTS.json")
    model = saved["mixture"]
    derived = []
    for row in sessions:
        timing = row["intervals"]
        if not timing["within_word"] or not timing[saved["location"]] or "components" not in model:
            continue
        baseline = float(np.median(timing["within_word"]))
        values = np.log(np.asarray(timing[saved["location"]]) / baseline)
        fitted = session_weights(values, np.array(model["log_scale_means"]), np.array(model["log_scale_variances"]), np.array(model["pooled_weights"]))
        derived.append(dict(writer=row["writer"], session=row["session"], slowest_weight=float(fitted[-1]),
                            component_weights=fitted.tolist(), intervals=len(values), within_word_median_seconds=baseline))
    if derived != weights:
        raise ValueError("D17 weights do not recompute from saved intervals")
    result = analyze(weights, config)
    for key, value in result.items():
        if saved.get(key) != value:
            raise ValueError("D17 primary does not recompute")
    return dict(verified=True, primary=saved)
