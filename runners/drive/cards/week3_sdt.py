"""WD1: population-relative acceptance slope and criterion, with honest LOO.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-7. A planted writer-specific slope
must recur across disjoint prompt halves; a criterion-only change must not be
called sensitivity learning. Every reference fit excludes all sessions of its
recipient, including under session-label permutations. P4 previous-action and
recent-acceptance features are structurally removed. Construction validates the
ruler only: conformity with population acceptance does not identify competence.
"""
from __future__ import annotations

from collections import defaultdict
import copy
from pathlib import Path
import time

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit, ndtr
from sklearn.decomposition import PCA

from . import menus_p4
from .menus_io import assert_equal, input_hashes, read, write, sha256
from .batch_runtime import atomic
from .timing_pmap_stats import split_sessions

SEED = 20261026
SCOPE = "Population-relative sensitivity and criterion; independent quality, competence, causal learning and payoffs are unidentified."


def population_features(sessions, records, vectors):
    sessions = copy.deepcopy(sessions)
    for session in sessions:
        for row in session["rows"]:
            row["session_end"] = session["end_at"]
    rows, base, scalar, embedding = menus_p4.prefix_features(sessions, records, vectors)
    if base.shape[1] != 9 or scalar.shape[1] != 60:
        raise ValueError("P4 feature layout changed: re-audit forbidden history columns")
    # Base 5:9 is previous action. Scalar 52 is last-five acceptance rate.
    # P8 scores are deliberately absent, as in the admitted P4 primary.
    kept = np.c_[base[:, :5], scalar[:, [i for i in range(60) if i != 52]]]
    return sessions, rows, kept, embedding


def logistic_fit(x, y, penalty=1.):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if x.ndim != 2 or y.shape != (len(x),) or not len(x) or not np.isfinite(x).all():
        raise ValueError("invalid reference design")
    if not np.isin(y, (0, 1)).all():
        raise ValueError("binary decisions required")
    regularizer = np.full(x.shape[1], float(penalty)); regularizer[0] = 0.
    def objective(beta):
        z = x @ beta
        value = float(np.sum(np.logaddexp(0, z) - y * z) + .5 * np.dot(regularizer * beta, beta))
        gradient = x.T @ (expit(z) - y) + regularizer * beta
        return value, gradient
    initial = np.zeros(x.shape[1]); initial[0] = np.log((y.sum() + .5) / (len(y) - y.sum() + .5))
    result = minimize(objective, initial, jac=True, method="L-BFGS-B",
                      options={"maxiter": 600, "gtol": 1e-6, "ftol": 1e-12, "maxls": 40})
    gradient = objective(result.x)[1]
    if not np.isfinite(result.x).all() or np.max(np.abs(gradient)) > 1e-3:
        raise ValueError("population logistic fit failed original gradient certificate")
    return result.x


def probit_fit(score, truth, penalty=.5):
    score, truth = np.asarray(score, float), np.asarray(truth, float)
    if len(score) < 4 or not np.isfinite(score).all():
        raise ValueError("insufficient finite decisions for sensitivity")
    # Unit: one population log-odds. Intercept is acceptance at population p=.5.
    # Fixed weak ridge prevents separated low-count halves from diverging.
    def objective(beta):
        z = beta[0] + beta[1] * score
        p = np.clip(ndtr(z), 1e-10, 1 - 1e-10)
        pdf = np.exp(-.5 * z * z) / np.sqrt(2 * np.pi)
        value = -np.sum(truth * np.log(p) + (1 - truth) * np.log1p(-p)) + .5 * penalty * np.dot(beta, beta)
        dz = (p - truth) * pdf / (p * (1 - p))
        return float(value), np.array([dz.sum(), np.dot(dz, score)]) + penalty * beta
    result = minimize(objective, np.zeros(2), jac=True, method="BFGS", options={"gtol": 1e-7, "maxiter": 300})
    if not np.isfinite(result.x).all() or np.max(np.abs(objective(result.x)[1])) > 1e-4:
        raise ValueError("sensitivity fit failed original gradient certificate")
    return {"criterion": float(-result.x[0]), "sensitivity": float(result.x[1]), "decisions": len(score)}


def reference_scores(sessions, rows, scalar, embeddings, assignment, seed=SEED, dimensions=16):
    owners = np.array([assignment.get(r["session"], r["writer"]) for r in rows])
    truth = np.array([r["handling"] in ("accept", "edit") for r in rows], dtype=float)
    scores = np.empty(len(rows)); provenance = {}
    for writer in sorted(set(owners)):
        own = owners == writer; train = ~own
        if train.sum() < 8 or len(np.unique(truth[train])) != 2:
            raise ValueError("population complement has insufficient binary support")
        # All fitted preprocessing is recipient-complement only, never transductive.
        k = min(dimensions, int(train.sum()) - 1, embeddings.shape[1])
        projection = PCA(n_components=k, svd_solver="randomized", random_state=seed)
        projection.fit(embeddings[train])
        content = np.c_[scalar[:, 1:], projection.transform(embeddings)]
        mean, sd = content[train].mean(0), content[train].std(0)
        sd[sd < 1e-10] = 1.
        x = np.c_[np.ones(len(rows)), (content - mean) / sd]
        beta = logistic_fit(x[train], truth[train])
        scores[own] = x[own] @ beta
        provenance[writer] = {"train_decisions": int(train.sum()), "excluded_decisions": int(own.sum()),
                              "own_decisions_in_fit": 0, "pca_dimensions": k}
    return scores, truth, provenance


def profiles(sessions, rows, scores, truth, assignment=None):
    assignment = assignment or {}
    halves, excluded = split_sessions(sessions, assignment)
    indices = defaultdict(list)
    for i, r in enumerate(rows): indices[r["session"]].append(i)
    fitted = {}; groups = defaultdict(list)
    for s in sessions: groups[assignment.get(s["session"], s["writer"])].append(s)
    for writer, pair in sorted(halves.items()):
        ids = [[i for s in part for i in indices[s["session"]]] for part in pair]
        if min(map(len, ids)) < 4:
            excluded[writer] = {"reason": "fewer than four decisions in a prompt half"}; continue
        fitted[writer] = {"halves": [probit_fit(scores[ix], truth[ix]) for ix in ids]}
        ordered = sorted(groups[writer], key=lambda s: (s["timestamp"], s["session"]))
        third = len(ordered) // 3
        early = [i for s in ordered[:third] for i in indices[s["session"]]]
        late = [i for s in ordered[-third:] for i in indices[s["session"]]] if third else []
        if min(len(early), len(late)) >= 4:
            fitted[writer]["thirds"] = [probit_fit(scores[early], truth[early]), probit_fit(scores[late], truth[late])]
    return fitted, excluded


def correlation(values):
    values = np.asarray(values, float)
    centered = values - values.mean(axis=0)
    denominator = np.sqrt(np.sum(centered[:, 0] ** 2) * np.sum(centered[:, 1] ** 2))
    return None if denominator < 1e-14 else float(np.sum(centered[:, 0] * centered[:, 1]) / denominator)


def permute_sessions(sessions, seed):
    rng = np.random.default_rng(seed); groups = defaultdict(list); assignment = {}
    for session in sorted(sessions, key=lambda s: s["session"]): groups[session["prompt"]].append(session)
    for _, group in sorted(groups.items()):
        shuffled = rng.permutation([s["writer"] for s in group])
        assignment.update({s["session"]: str(w) for s, w in zip(group, shuffled)})
    return assignment


def evaluate(sessions, rows, scalar, embeddings, assignment, config):
    scores, truth, provenance = reference_scores(sessions, rows, scalar, embeddings, assignment,
                                               int(config.get("seed", SEED)), int(config.get("pca_dimensions", 16)))
    fit, excluded = profiles(sessions, rows, scores, truth, assignment)
    return {"profiles": fit, "excluded": excluded, "reference_fit": provenance}


def summarize(real, controls, draws, seed):
    writers = sorted(real["profiles"])
    if len(writers) < 4:
        return {"state": "unsupported", "reason": "fewer than four supported writers", "writers": len(writers)}
    if any(sorted(c["profiles"]) != writers for c in controls):
        return {"state": "invalid", "reason": "permutation changed supported writer population", "writers": len(writers)}
    def matrix(record, field):
        return np.array([[part[field] for part in record["profiles"][w]["halves"]] for w in writers])
    values = matrix(real, "sensitivity"); fake = np.array([matrix(c, "sensitivity") for c in controls])
    actual = correlation(values); null = [correlation(c) for c in fake]
    if actual is None or any(r is None for r in null):
        return {"state": "invalid", "reason": "constant sensitivity makes reliability undefined", "writers": len(writers)}
    null = np.asarray(null); rng = np.random.default_rng(seed + 101)
    deltas = []; raw_boot = []
    for _ in range(draws):
        ix = rng.integers(0, len(writers), len(writers))
        r = correlation(values[ix]); refs = [correlation(f[ix]) for f in fake]
        if r is None or any(x is None for x in refs):
            # Undefined draws are retained as nulls and force invalidity rather than redrawn.
            return {"state": "invalid", "reason": "undefined paired bootstrap draw", "writers": len(writers)}
        raw_boot.append(r); deltas.append(r - float(np.mean(refs)))
    estimate = actual - float(null.mean()); low, high = map(float, np.quantile(deltas, [.025, .975]))
    p = float((1 + np.sum(null >= actual - 1e-14)) / (len(null) + 1))
    state = "positive" if low > 0 and p < .05 else "negative" if high < 0 else "marginal" if estimate > 0 else "null"
    if low > 0 and p >= .05: state = "unresolved"
    changes = {}
    for field in ("criterion", "sensitivity"):
        third_deltas = [v["thirds"][1][field] - v["thirds"][0][field]
                        for v in real["profiles"].values() if "thirds" in v]
        changes[field] = {"writers": len(third_deltas),
                          "mean_last_minus_first": float(np.mean(third_deltas)) if third_deltas else None}
    return {"state": state, "writers": len(writers), "sensitivity_reliability": actual,
            "permutation_mean": float(null.mean()), "permutation_95_interval": np.quantile(null, [.025, .975]).tolist(),
            "permutation_p_one_sided": p, "real_minus_permutation_mean": estimate,
            "paired_writer_95_interval": [low, high], "bootstrap_draws": draws,
            "permutation_draws": len(null), "criterion_reliability_secondary": correlation(matrix(real, "criterion")),
            "session_thirds_secondary": changes,
            "null_wording": "not detected; sensitivity untested" if state == "null" else None}


def run(output, inputs, config, verify_only=False):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    if "p8" in inputs: raise ValueError("uncalibrated P8 inputs are not admitted")
    config = dict(config); seed = int(config.get("seed", SEED))
    mode = config.get("mode", "full")
    permutations = int(config.get("permutation_draws", 1000))
    if mode == "full" and permutations < 1000: raise ValueError("full WD1 requires at least 1000 permutations")
    if mode not in ("full", "pilot", "fixture"): raise ValueError("unknown WD1 mode")
    binding = {"input_hashes": input_hashes(inputs), "config": config,
               "source_sha256": sha256(__file__)}
    if (output / "BINDINGS.json").exists(): assert_equal(binding, read(output / "BINDINGS.json"))
    elif verify_only: raise ValueError("missing source binding")
    else: write(output / "BINDINGS.json", binding)
    raw = read(inputs["sessions"]); vectors = np.load(inputs["vectors"], mmap_mode="r", allow_pickle=False)
    sessions, rows, scalar, embeddings = population_features(raw, read(inputs["records"]), vectors)
    real = evaluate(sessions, rows, scalar, embeddings, {}, config)
    if (output / "REAL.json").exists(): assert_equal(real, read(output / "REAL.json"))
    elif verify_only: raise ValueError("missing real calculation")
    else: write(output / "REAL.json", real)
    controls = []; timings = []
    for number in range(permutations):
        started = time.process_time()
        path = output / "permutations" / f"{number:04}.json"
        receipt_path = path.with_suffix(".receipt.json")
        if path.exists() and receipt_path.exists() and not verify_only:
            receipt = read(receipt_path)
            if receipt["sha256"] != sha256(path) or receipt["number"] != number:
                raise ValueError("changed permutation checkpoint")
            result = read(path); charged = receipt["cpu_seconds"]
        else:
            result = evaluate(sessions, rows, scalar, embeddings, permute_sessions(sessions, seed + number), config)
            if path.exists(): assert_equal(result, read(path))
            elif verify_only: raise ValueError("missing permutation calculation")
            else: write(path, result)
            charged = time.process_time() - started
            if not verify_only:
                write(receipt_path, {"number": number, "sha256": sha256(path), "cpu_seconds": charged})
        controls.append(result); timings.append(charged)
        if not verify_only:
            atomic(output / "PROGRESS.json", {"phase": "permutations", "completed": number + 1,
                    "total": permutations, "partial_scores_public": False})
            if (output / "YIELD_REQUEST.json").exists():
                return {"status": "yielded", "card": "WD1", "completed_permutations": number + 1}
    report = {"card": "WD1", "mode": mode, "input_hashes": input_hashes(inputs), "scope": SCOPE,
              "reference": "recipient-excluded P4 population features, binary accept-or-edit logistic ridge; no previous action or recent acceptance",
              "sensitivity": "probit slope per population log-odds; criterion is negative intercept at population acceptance probability .5",
              "permutation": "whole-session writer labels within prompt, refitting every complement reference and split profile",
              "known_answer_required_before_dispatch": True,
              "primary": summarize(real, controls, int(config.get("bootstrap_draws", 2000)), seed) if mode != "pilot"
              else {"state": "timing_only", "scientific_inference": False},
              "future_own_history_used": False, "real_decisions": len(rows), "real_sessions": len(sessions)}
    if verify_only: assert_equal(report, read(output / "SUMMARY.json"))
    elif (output / "SUMMARY.json").exists(): assert_equal(report, read(output / "SUMMARY.json"))
    else:
        write(output / "SUMMARY.json", report)
        write(output / "TIMING.json", {"permutation_cpu_seconds": timings,
                                      "full_1000_permutations_cpu_projection": float(np.mean(timings) * 1000)})
    return report


def execute(output, inputs, config):
    return run(output, inputs, config)


def verify(output, inputs, config):
    run(output, inputs, config, verify_only=True)
    return {"verified": True, "fresh_population_and_permutation_refit": True}
