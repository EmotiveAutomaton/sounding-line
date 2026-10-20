"""DR1 metadata-only acquisition component; no profile estimator or verdict.

DESIGN CHECK (2026-10-20): LESSONS sections 3-5.
NULL: hidden outcomes cannot change a selection because they are not accepted.
ALTERNATIVE: metadata coverage can change expected variance reduction.
Invalid identities, nonfinite inputs or unknown fields refuse. The deterministic
policy has zero support off its selected candidate. Conditional probabilities
never masquerade as marginal inclusion probabilities or population weights.
"""
import math
import numpy as np

FIELDS = {"session", "writer", "prompt", "timestamp", "typed_words"}
POLICIES = {"chronological", "random", "directed", "directed_random20"}


def metadata_matrix(records):
    if not records or any(set(r) != FIELDS for r in records):
        raise ValueError("Only exact pre-read metadata fields are permitted")
    records = sorted(records, key=lambda r: r["session"])
    if (len({r["session"] for r in records}) != len(records)
            or len({r["writer"] for r in records}) != 1
            or any(not isinstance(r[k], str) or not r[k] for r in records
                   for k in ("session", "writer", "prompt"))):
        raise ValueError("Unique sessions for one named writer are required")
    if any(type(r["typed_words"]) is not int or r["typed_words"] < 0
           or not isinstance(r["timestamp"], (int, float))
           or not math.isfinite(r["timestamp"]) for r in records):
        raise ValueError("Finite dates and nonnegative integer word counts required")
    prompts = sorted({r["prompt"] for r in records})
    continuous = np.array([[math.log1p(r["typed_words"]), r["timestamp"]] for r in records], dtype=float)
    scale = continuous.std(axis=0)
    continuous = (continuous - continuous.mean(axis=0)) / np.where(scale > 0, scale, 1)
    matrix = np.column_stack((np.ones(len(records)),
                              [[float(r["prompt"] == p) for p in prompts] for r in records],
                              continuous))
    return records, matrix


def variance_gain(covariance, target, candidate):
    """Unit-noise linear-Gaussian mean-profile variance drop, no outcomes."""
    projection = covariance @ candidate
    return float((target @ projection)**2 / (1 + candidate @ projection))


def make_order(records, policy, seed):
    if policy not in POLICIES or type(seed) is not int or seed < 0:
        raise ValueError("Frozen policy and nonnegative integer seed required")
    records, matrix = metadata_matrix(records)
    target = matrix.mean(axis=0)
    covariance = np.eye(matrix.shape[1])
    remaining = list(range(len(records)))
    rng = np.random.default_rng(seed)
    steps = []
    while remaining:
        gains = np.array([variance_gain(covariance, target, matrix[i]) for i in remaining])
        if policy == "chronological":
            chosen = min(range(len(remaining)), key=lambda j: (records[remaining[j]]["timestamp"], records[remaining[j]]["session"]))
            probabilities = np.zeros(len(remaining)); probabilities[chosen] = 1
        elif policy == "random":
            probabilities = np.full(len(remaining), 1/len(remaining))
        else:
            # Inputs are session-sorted, so exact gain ties break by session ID.
            best = int(np.argmax(gains))
            epsilon = .2 if policy == "directed_random20" else 0.
            probabilities = np.full(len(remaining), epsilon/len(remaining))
            probabilities[best] += 1-epsilon
        chosen = int(rng.choice(len(remaining), p=probabilities))
        index = remaining[chosen]
        steps.append(dict(step=len(steps)+1, session=records[index]["session"],
                          conditional_pick_probability=float(probabilities[chosen]),
                          candidate_probabilities={records[i]["session"]: float(p) for i, p in zip(remaining, probabilities)},
                          expected_reference_variance_drop=float(gains[chosen]),
                          predictive_variance_before=float(target @ covariance @ target)))
        x = matrix[index]; projection = covariance @ x
        covariance -= np.outer(projection, projection)/(1+x @ projection)
        covariance = (covariance + covariance.T)/2
        remaining.pop(chosen)
    return dict(policy=policy, seed=seed, steps=steps,
                metadata_only=True, population_weights_available=False,
                scientific_admission=False,
                model="Unit-noise Bayesian linear model; identity prior covariance; intercept, prompt indicators, standardized log1p words and date; acquisition minimizes variance of the full-metadata mean",
                caveat="A coverage heuristic, not measured information gain. Conditional probabilities are not marginal inclusion probabilities. Full-cohort policy evaluation and its inference remain separate.")
