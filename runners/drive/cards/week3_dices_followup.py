"""Frozen shared mechanics for the one-generation CA5.s and CA5.m follow-ups.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-7. Pure group/item effects and
constant personal severity have zero topic recurrence; stable topic deviations
recur and reversed deviations reverse. Severity can recur with zero topic
recurrence. Every null rebuilds group/item adjustment from itemwise assignments
within demographic group. Unsupported cells retain their full population and
cannot pass by dropping a rater. Constant correlations contribute exact zero.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import numpy as np

from . import week3_dices as original
from .menus_io import read, sha256

SEED = 20261026
SPLITS = ("odd_even", "first_last")
UNSURE = (0., .5, 1.)


def admit(inputs, config):
    if set(inputs) != {"source", "codebook", "parent_summary", "parent_complete"}:
        raise ValueError("follow-up requires exactly source, codebook and authenticated parent")
    if set(config) - {"fixture", "permutation_draws", "bootstrap_draws", "seed"}:
        raise ValueError("unfrozen follow-up configuration")
    count = int(config.get("permutation_draws", 1000))
    draws = int(config.get("bootstrap_draws", 2000))
    seed = int(config.get("seed", SEED))
    if count < 1 or draws < 2 or seed != SEED:
        raise ValueError("invalid frozen reference bank")
    if not config.get("fixture", False) and (count != 1000 or draws != 2000):
        raise ValueError("full follow-up requires exactly 1000 permutations and 2000 bootstraps")
    parent, complete = read(inputs["parent_summary"]), read(inputs["parent_complete"])
    if complete.get("status") != "COMPLETE" or complete.get("fresh_process_verified") is not True:
        raise ValueError("parent lacks complete fresh verification")
    if complete.get("outputs", {}).get("output/SUMMARY.json") != sha256(inputs["parent_summary"]):
        raise ValueError("parent summary not authenticated by completion")
    if parent.get("card") != "CA5" or parent.get("primary_all_released_raters", {}).get("state") != "positive":
        raise ValueError("registered follow-ups require the landed positive CA5 parent")
    for key in ("source", "codebook"):
        if parent.get("input_hashes", {}).get(key) != sha256(inputs[key]):
            raise ValueError("follow-up source differs from parent")
    return original.load(inputs, config), count, draws


def split_labels(item_ids, split):
    ids = np.asarray(item_ids, int)
    if len(ids) < 4 or len(np.unique(ids)) != len(ids) or np.any(np.diff(ids) <= 0):
        raise ValueError("item order must be unique ascending numeric IDs")
    if split == "odd_even":
        labels = ids % 2
    elif split == "first_last":
        labels = (np.arange(len(ids)) >= len(ids) // 2).astype(int)
    else:
        raise ValueError("split outside frozen two-specification set")
    if set(labels) != {0, 1}:
        raise ValueError("empty frozen half")
    return labels


def recode(values, unsure):
    if unsure not in UNSURE:
        raise ValueError("Unsure coding outside frozen set")
    values = np.asarray(values, float)
    if not np.isin(values, [0., .5, 1.]).all():
        raise ValueError("rating outside original three-category support")
    return np.where(values == .5, unsure, values)


def features(values, groups, item_ids, topics, split):
    values = np.asarray(values, float)
    if values.shape != (len(groups), len(item_ids)) or len(topics) != len(item_ids) or not np.isfinite(values).all():
        raise ValueError("invalid profile dimensions or nonfinite values")
    halves = split_labels(item_ids, split)
    members = defaultdict(list)
    for i, group in enumerate(groups):
        members[tuple(group)].append(i)
    counts = {"raters": len(groups), "items": len(item_ids),
              "half_item_counts": [int(np.sum(halves == h)) for h in (0, 1)],
              "singleton_group_raters": sum(len(ix) for ix in members.values() if len(ix) < 2)}
    topic_array = np.asarray(topics)
    retained = [t for t in sorted(set(topics)) if all(np.any((topic_array == t) & (halves == h)) for h in (0, 1))]
    counts.update(topics_in_both_halves=len(retained), topics_missing_from_one_half=len(set(topics)) - len(retained))
    if counts["singleton_group_raters"] or len(groups) < 4 or len(retained) < 2:
        return None, None, counts
    adjusted = np.zeros_like(values)
    for _, indices in sorted(members.items()):
        ix = np.array(indices)
        adjusted[ix] = values[ix] - (values[ix].sum(axis=0) - values[ix]) / (len(ix) - 1)
    severity = np.column_stack([adjusted[:, halves == h].mean(axis=1) for h in (0, 1)])
    severity[np.abs(severity) < 1e-12] = 0.
    profiles = np.empty((len(groups), 2, len(retained)))
    for h in (0, 1):
        centered = adjusted - adjusted[:, halves == h].mean(axis=1, keepdims=True)
        centered[np.abs(centered) < 1e-12] = 0.
        for k, topic in enumerate(retained):
            profiles[:, h, k] = centered[:, (halves == h) & (topic_array == topic)].mean(axis=1)
    return profiles, severity, counts


def clean(values):
    values = np.array(values, float, copy=True)
    values[np.abs(values) < 1e-14] = 0.
    return values


def classify(effect, interval, p):
    low, high = interval
    if low > 0:
        return "positive" if p < .05 else "unresolved"
    if high < 0:
        return "negative"
    return "marginal" if effect > 0 else "null"


def report(observed, null, boot, effect, draws):
    interval = np.quantile(clean(boot), [.025, .975]).tolist()
    p = float((1 + np.sum(null >= observed - 1e-14)) / (len(null) + 1))
    state = classify(float(effect), interval, p)
    return {"state": state, "observed": float(observed), "permutation_mean": float(np.mean(null)),
            "permutation_95_interval": np.quantile(null, [.025, .975]).tolist(),
            "permutation_p_one_sided": p, "real_minus_permutation_mean": float(effect),
            "paired_rater_95_interval": interval, "permutation_draws": len(null), "bootstrap_draws": draws,
            "null_wording": "not detected; sensitivity untested" if state == "null" else None}


def topic_report(real, null, draws):
    delta = clean(real - null.mean(axis=0))
    ix = np.random.default_rng(SEED + 10001).integers(0, len(real), size=(draws, len(real)))
    return report(float(real.mean()), null.mean(axis=1), delta[ix].mean(axis=1), float(delta.mean()), draws)


def holm(values):
    order = np.argsort(values, kind="stable")
    result = np.empty(len(values)); previous = 0.
    for rank, ix in enumerate(order):
        previous = max(previous, min(1., float(values[ix]) * (len(values) - rank)))
        result[ix] = previous
    return result.tolist()


def populations(data):
    values, groups, item_ids, topics, quality = data
    return [("all_released_raters", values, groups, item_ids, topics),
            ("published_quality_subset", values[quality], [g for g, keep in zip(groups, quality) if keep], item_ids, topics)]


def contract(card):
    return {"card": card, "followup_generation": 1, "followups_allowed": False,
            "original_cpu_cap_seconds": 1800, "seed": SEED,
            "permutation": "independent rater-label reassignment within demographic group for each item; all means and profiles rebuilt",
            "population": "all 123 raters and separately all published 104; no outcome exclusions",
            "constant_profile_policy": "zero contribution, counted; no deletion",
            "unsupported_policy": "whole cell unsupported if any rater lacks a demographic peer or fewer than two topics span both halves",
            "scope": "Recurring perceived harm judgments only; no objective safety, independent values, competence or causal mechanism claim."}
