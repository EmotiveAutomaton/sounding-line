"""CA5.m: distinguish recurring overall severity from centered topic patterns.

DESIGN CHECK: LESSONS 3-5, CONTROLS 1-7. Stable rater offsets alone give
severity recurrence but exact-zero centered topic recurrence; zero-mean stable
topic patterns give the reverse. Both may coexist. Reverse signs must reverse
the matching endpoint. Every itemwise within-group null rebuilds all features.
Endpoints use different units: no subtraction or causal mediation inference.
"""
from pathlib import Path
import numpy as np
from . import week3_dices as base
from . import week3_dices_followup as shared
from .batch_runtime import atomic
from .menus_io import assert_equal, input_hashes, read, write


def correlation(pairs):
    """Pearson across the penultimate (rater) axis; constants are exactly zero."""
    pairs = np.asarray(pairs, float)
    centered = pairs - pairs.mean(axis=-2, keepdims=True)
    numerator = np.sum(centered[..., 0] * centered[..., 1], axis=-1)
    denominator = np.sqrt(np.sum(centered[..., 0] ** 2, axis=-1) * np.sum(centered[..., 1] ** 2, axis=-1))
    return np.divide(numerator, denominator, out=np.zeros_like(numerator), where=denominator > 1e-14)


def severity_report(real, null, draws):
    observed, null_means = float(correlation(real)), correlation(null)
    indices = np.random.default_rng(shared.SEED + 10001).integers(0, len(real), size=(draws, len(real)))
    boot = []
    # Each bootstrap uses the same rater sample for real and every reference.
    # Chunking bounds memory, without reducing the reference or bootstrap bank.
    for start in range(0, draws, 8):
        ix = indices[start:start + 8]
        reference = correlation(null[:, ix, :]).mean(axis=0)
        boot.extend(shared.clean(correlation(real[ix]) - reference))
    effect = float(shared.clean(observed - float(null_means.mean())))
    return shared.report(observed, null_means, np.asarray(boot), effect, draws)


def calculate(output, inputs, config, verify_only=False):
    data, count, draws = shared.admit(inputs, config)
    cells = []
    for population, values, groups, items, topics in shared.populations(data):
        profiles, severity, census = shared.features(values, groups, items, topics, "odd_even")
        cell = {"population": population, **census}
        if profiles is None:
            cell.update(state="unsupported", reason="full fixed population lacks peer or topic support")
        else:
            real, zero = base.profile_correlations(profiles)
            topic_null, severity_null = [], []
            for j in range(count):
                fake = base.permutation(values, groups, shared.SEED + j)
                fp, fs, changed = shared.features(fake, groups, items, topics, "odd_even")
                if changed != census or fp is None:
                    raise ValueError("permutation changed frozen support")
                topic_null.append(base.profile_correlations(fp)[0]); severity_null.append(fs)
                if not verify_only and j % 50 == 0:
                    atomic(Path(output) / "PROGRESS.json", {"phase": "mechanism_references", "population": population, "completed": j + 1, "total": count})
            cell.update(state="complete", topic_centered=shared.topic_report(real, np.asarray(topic_null), draws),
                        overall_severity=severity_report(severity, np.asarray(severity_null), draws),
                        zero_topic_profile_raters=int(zero.sum()),
                        severity_variance_by_half=np.var(severity, axis=0).tolist())
        cells.append(cell)
    endpoints = [c[k] for c in cells if c["state"] == "complete" for k in ("topic_centered", "overall_severity")]
    # Four frozen endpoint/population tests; unsupported endpoints consume p=1.
    adjusted = shared.holm([e["permutation_p_one_sided"] for e in endpoints] + [1.] * (4 - len(endpoints)))
    for endpoint, p in zip(endpoints, adjusted):
        endpoint["holm_adjusted_p_4_endpoints"] = p
        endpoint["supported_after_family_adjustment"] = endpoint["state"] == "positive" and p < .05
    for cell in cells:
        if cell["state"] == "complete":
            t = cell["topic_centered"]["supported_after_family_adjustment"]
            s = cell["overall_severity"]["supported_after_family_adjustment"]
            cell["descriptive_pattern"] = "both_recur" if t and s else "topic_recurrence_only_detected" if t else "severity_recurrence_only_detected" if s else "neither_recurrence_detected"
    return {**shared.contract("CA5.m"), "input_hashes": input_hashes(inputs), "populations": cells,
            "response_encoding": "No=0; Unsure=0.5; Yes=1; all judgments retained",
            "split": "fixed odd/even numeric item IDs",
            "topic_endpoint": "mean within-rater Pearson correlation across centered harm-topic profiles",
            "severity_endpoint": "Pearson correlation across all raters of mean leave-one-rater-out group/item deviation in each half",
            "interval_scope": "paired rater bootstrap conditional on the observed group/item adjustment; severity correlation recomputed for real and every null under each same resample",
            "mechanism_limit": "The endpoints have different statistical units; they are not subtracted. Coexistence or isolated detection is descriptive, not causal attribution, absence evidence or a variance share."}


def execute(output, inputs, config):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    result = calculate(output, inputs, config)
    write(output / "SUMMARY.json", result)
    return result


def verify(output, inputs, config):
    assert_equal(calculate(output, inputs, config, True), read(Path(output) / "SUMMARY.json"))
    return {"verified": True, "fresh_both_endpoints_populations_and_all_references": True}
