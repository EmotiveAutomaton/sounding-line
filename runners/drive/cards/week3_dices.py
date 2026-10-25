"""CA5: DICES topic-profile recurrence beyond demographic group and leniency.

DESIGN CHECK: LESSONS 3-5, CONTROLS 1-7. Group/item effects and constant
individual leniency alone must give exact zero centered profiles. Constructed
stable topic directions must recur; opposite directions must reverse sign.
Every permutation reassigns whole judgment vectors within demographic group
independently per item and rebuilds all means/centering. Quality exclusions are
the published list, frozen before ratings, never selected for favorable results.
"""
from __future__ import annotations

import ast
from collections import Counter, defaultdict
import csv
from pathlib import Path
import re
import time

import numpy as np

from .menus_io import assert_equal, input_hashes, read, write, sha256
from .batch_runtime import atomic

SOURCE_HASH = "63cb8620eb04e64957f9e45b1f7cb3d079c4eed8e8b28909f46e0b7038ce4301"
CODEBOOK_HASH = "0e9d5b8fa1ae3d102a77ca4f773a2551b9c0a56f88f5cf825e5db2d405ebd5f3"
SCORES = {"No": 0., "Unsure": .5, "Yes": 1.}
SEED = 20261026


def excluded_raters(codebook):
    text = Path(codebook).read_text(encoding="utf8")
    match = re.search(r"removed_raters_350\s*=\s*(\[[^\]]+\])", text)
    if match is None: raise ValueError("official quality exclusion list absent")
    result = ast.literal_eval(match.group(1))
    if not isinstance(result, list) or any(not isinstance(x, str) for x in result) or len(set(result)) != len(result):
        raise ValueError("malformed official quality exclusion list")
    return set(result)


def load(inputs, config):
    if not config.get("fixture", False):
        if sha256(inputs["source"]) != SOURCE_HASH or sha256(inputs["codebook"]) != CODEBOOK_HASH:
            raise ValueError("pinned DICES source/codebook changed")
    excluded = excluded_raters(inputs["codebook"])
    records = {}; raters = {}; items = {}
    with Path(inputs["source"]).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        for row in reader:
            rater = row["rater_id"]; item = int(row["item_id"])
            if (rater, item) in records: raise ValueError("duplicate rater/item judgment")
            if row["Q_overall"] not in SCORES: raise ValueError("unrecognized overall rating; no silent imputation")
            group = (row["rater_gender"].strip(), row["rater_race"].strip())
            if not all(group): raise ValueError("missing demographic group")
            if rater in raters and raters[rater] != group: raise ValueError("rater group changed within release")
            raters[rater] = group
            topic = row["harm_type"].strip()
            if not topic: raise ValueError("missing expert harm topic")
            if item in items and items[item] != topic: raise ValueError("expert harm topic differs between raters")
            items[item] = topic; records[rater, item] = SCORES[row["Q_overall"]]
    writer_ids, item_ids = sorted(raters), sorted(items)
    if len(records) != len(writer_ids) * len(item_ids): raise ValueError("release is not fully crossed")
    if not excluded <= set(writer_ids): raise ValueError("quality list contains absent raters")
    if not config.get("fixture", False) and (len(writer_ids), len(item_ids), len(excluded)) != (123, 350, 19):
        raise ValueError("frozen 123/104-rater, 350-item denominators changed")
    values = np.array([[records[w, item] for item in item_ids] for w in writer_ids])
    groups = [raters[w] for w in writer_ids]; topics = [items[item] for item in item_ids]
    quality = np.array([w not in excluded for w in writer_ids])
    return values, groups, item_ids, topics, quality


def adjusted_profiles(values, groups, item_ids, topics):
    values = np.asarray(values, float); count, items = values.shape
    if count != len(groups) or items != len(item_ids) or items != len(topics): raise ValueError("profile dimensions differ")
    memberships = defaultdict(list)
    for i, group in enumerate(groups): memberships[tuple(group)].append(i)
    adjusted = np.zeros_like(values); supported = np.ones(count, dtype=bool)
    for group, indices in sorted(memberships.items()):
        ix = np.array(indices)
        if len(ix) < 2:
            supported[ix] = False; continue
        # Leave-one-rater-out group/item mean; no self contribution to baseline.
        adjusted[ix] = values[ix] - (values[ix].sum(axis=0) - values[ix]) / (len(ix) - 1)
    parities = np.array(item_ids) % 2
    categories = sorted(set(topics)); category_mask = np.array(topics)
    retained = [t for t in categories if all(np.any((category_mask == t) & (parities == h)) for h in (0, 1))]
    if len(retained) < 2: raise ValueError("fewer than two topics represented in both item halves")
    profiles = np.empty((count, 2, len(retained)))
    for half in (0, 1):
        ix = parities == half
        centered = adjusted - adjusted[:, ix].mean(axis=1, keepdims=True)
        # Exact construction cancellations cannot become tiny signed findings.
        centered[np.abs(centered) < 1e-12] = 0.
        for k, topic in enumerate(retained):
            profiles[:, half, k] = centered[:, ix & (category_mask == topic)].mean(axis=1)
    return profiles, supported, retained, len(categories) - len(retained)


def profile_correlations(profiles):
    centered = profiles - profiles.mean(axis=2, keepdims=True)
    numerator = np.sum(centered[:, 0] * centered[:, 1], axis=1)
    denominator = np.sqrt(np.sum(centered[:, 0] ** 2, axis=1) * np.sum(centered[:, 1] ** 2, axis=1))
    return np.divide(numerator, denominator, out=np.zeros(len(profiles)), where=denominator > 1e-14), denominator <= 1e-14


def permutation(values, groups, seed):
    rng = np.random.default_rng(seed); output = np.array(values, copy=True)
    members = defaultdict(list)
    for i, group in enumerate(groups): members[tuple(group)].append(i)
    for group, indices in sorted(members.items()):
        ix = np.array(indices)
        for item in range(values.shape[1]): output[ix, item] = values[rng.permutation(ix), item]
    return output


def decomposition(values, groups):
    """Balanced fixed-effects sums of squares; residual is not isolated mechanism."""
    values = np.asarray(values, float); grand = values.mean(); item = values.mean(axis=0) - grand
    group = np.zeros_like(values); group_item = np.zeros_like(values); rater = np.zeros_like(values)
    members = defaultdict(list)
    for i, label in enumerate(groups): members[tuple(label)].append(i)
    for indices in members.values():
        ix = np.array(indices); overall = values[ix].mean(); by_item = values[ix].mean(axis=0)
        group[ix] = overall - grand
        group_item[ix] = by_item - overall - item
        rater[ix] = values[ix].mean(axis=1, keepdims=True) - overall
    error = values - grand - item - group - group_item - rater
    pieces = {"demographic_group": group, "item": np.broadcast_to(item, values.shape),
              "rater_within_group": rater, "item_by_group": group_item,
              "item_by_rater_plus_unreplicated_error": error}
    ss = {k: float(np.sum(v * v)) for k, v in pieces.items()}
    total = float(np.sum((values - grand) ** 2))
    if not np.isclose(sum(ss.values()), total, rtol=1e-9, atol=1e-10): raise ValueError("balanced decomposition did not close")
    return {"sum_squares": ss, "total_sum_squares": total,
            "limitation": "One rating per rater/item: item-by-rater interaction cannot be separated from observation error."}


def compute(values, groups, item_ids, topics, config, output=None, verify_only=False):
    count = int(config.get("permutation_draws", 1000)); draws = int(config.get("bootstrap_draws", 2000)); seed = int(config.get("seed", SEED))
    profiles, supported, categories, missing_topics = adjusted_profiles(values, groups, item_ids, topics)
    real, zero = profile_correlations(profiles); real = real[supported]
    if len(real) < 4:
        return {"state": "unsupported", "reason": "fewer than four raters with group peers", "supported_raters": len(real)}
    null = []
    for i in range(count):
        changed = permutation(values, groups, seed + i)
        fake, mask, _, _ = adjusted_profiles(changed, groups, item_ids, topics)
        if not np.array_equal(mask, supported): raise ValueError("permutation changed supported rater population")
        null.append(profile_correlations(fake)[0][supported])
        if output is not None and not verify_only and i % 50 == 0:
            atomic(Path(output) / "PROGRESS.json", {"phase": "permutations", "completed": i + 1, "total": count})
    null = np.asarray(null); delta = real - null.mean(axis=0)
    # If all worlds are numerically identical, the contrast is exactly zero.
    delta[np.abs(delta) < 1e-14] = 0.
    rng = np.random.default_rng(seed + 10001)
    boot = delta[rng.integers(0, len(real), size=(draws, len(real)))].mean(axis=1)
    low, high = map(float, np.quantile(boot, [.025, .975])); effect = float(delta.mean())
    observed = float(real.mean()); null_means = null.mean(axis=1)
    p = float((1 + np.sum(null_means >= observed - 1e-14)) / (count + 1))
    state = "positive" if low > 0 and p < .05 else "negative" if high < 0 else "marginal" if effect > 0 else "null"
    if low > 0 and p >= .05: state = "unresolved"
    return {"state": state, "raters": len(values), "items": len(item_ids), "supported_raters": len(real),
            "singleton_group_raters": int((~supported).sum()), "topics_in_both_halves": len(categories),
            "topics_missing_from_one_half": missing_topics, "zero_profile_raters": int(zero[supported].sum()),
            "mean_within_rater_profile_correlation": observed, "permutation_mean": float(null_means.mean()),
            "permutation_95_interval": np.quantile(null_means, [.025, .975]).tolist(),
            "permutation_p_one_sided": p, "real_minus_permutation_mean": effect, "paired_rater_95_interval": [low, high],
            "permutation_draws": count, "bootstrap_draws": draws,
            "null_wording": "not detected; sensitivity untested" if state == "null" else None,
            "decomposition": decomposition(values, groups)}


def calculate(output, inputs, config, verify_only=False):
    if not config.get("fixture", False) and int(config.get("permutation_draws", 1000)) < 1000:
        raise ValueError("full CA5 requires at least 1000 permutations")
    values, groups, item_ids, topics, quality = load(inputs, config)
    full = compute(values, groups, item_ids, topics, config, output, verify_only)
    subset = compute(values[quality], [g for g, keep in zip(groups, quality) if keep], item_ids, topics, config, output, verify_only)
    return {"card": "CA5", "input_hashes": input_hashes(inputs), "primary_all_released_raters": full,
            "sensitivity_published_quality_subset": subset,
            "response_encoding": "No=0; Unsure=0.5; Yes=1 in per-rater Q_overall",
            "demographic_group": "gender by race recruitment strata; no identity or demographic class inference",
            "profile": "expert harm_type topics; leave-one-rater-out group/item mean; separately centered within each odd/even half",
            "reliability": "mean within-rater Pearson correlation across topics; constant profiles contribute zero and are counted",
            "scope": "Recurrence of perceived harm topic judgments; not independent personal values, objective safety or competence."}


def execute(output, inputs, config):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    report = calculate(output, inputs, config)
    write(output / "SUMMARY.json", report)
    return report


def verify(output, inputs, config):
    assert_equal(calculate(output, inputs, config, True), read(Path(output) / "SUMMARY.json"))
    return {"verified": True, "fresh_both_denominators_and_all_permutations": True}
