"""Registered whole-family bootstrap for sealed MIDUS tables (amendment AW).

DESIGN CHECK. When all families are singletons, each draw matches the original
person bootstrap at the same seed and index. In a constructed family, selecting
one member must select every eligible relative with exactly the same weight.
Invalid linkage cannot silently turn a family analysis into a person analysis.
All person and family keys stay inside the sealed process.
"""
from collections import Counter
from math import isfinite

import numpy as np
import pyreadstat

import analysis_v1 as analysis
from week6_sealed_support_v1 import SealedFailure


def positive_integer(value):
    if isinstance(value, (int, float)) and isfinite(value) and value > 0 and value == int(value):
        return int(value)
    return None


def family_index(survey_path):
    """Use the wave-two family key for both waves. SPSS user missings become NaN."""
    _, metadata = pyreadstat.read_sav(str(survey_path), metadataonly=True)
    if "M2FAMNUM" not in metadata.column_names:
        return None
    frame, _ = pyreadstat.read_sav(
        str(survey_path), usecols=["M2ID", "M2FAMNUM"], user_missing=False,
        apply_value_formats=False, disable_datetime_conversion=True,
    )
    groups = {}
    for person, family in frame[["M2ID", "M2FAMNUM"]].itertuples(index=False, name=None):
        person_id = positive_integer(person)
        if person_id is None:
            continue
        if person_id in groups:
            raise SealedFailure(11, "Family linkage contains a duplicate person")
        groups[person_id] = positive_integer(family)
    return groups


def roster(people, index, reference=False):
    """Return a compact family ordering aligned exactly with the fitted people."""
    labels = [index.get(person["id"]) for person in people]
    if any(label is None for label in labels):
        return None
    if reference:
        first = {}
        for position in reversed(range(len(labels))):
            first[labels[position]] = position
        ordered = sorted(first, key=first.get)
    else:
        ordered = list(dict.fromkeys(labels))
    numbers = {family: i for i, family in enumerate(ordered)}
    return np.asarray([numbers[label] for label in labels], dtype=int)


def multiplicities(groups, seed, index, independent=False):
    n_groups = int(np.max(groups)) + 1
    rng = np.random.default_rng(np.random.SeedSequence([seed, index]))
    selected = rng.integers(n_groups, size=n_groups)
    if independent:
        counts = Counter(int(group) for group in selected)
        return np.asarray([counts[int(group)] for group in groups], dtype=int)
    return np.bincount(selected, minlength=n_groups)[groups]


def draw_record(people, stats, groups, branch, seed, index, reference=False):
    weights = multiplicities(groups, seed, index, reference)
    selected = [person for person, weight in zip(people, weights) if weight]
    contributors, required = analysis.groups_for(selected, branch)
    if len(contributors) <= 10 or any(len(subset) <= 10 for subset in required):
        return {"draw": index, "status": "INVALID", "reason": "PRIVACY_SUPPORT"}
    value = analysis.evaluate(stats, branch, weights, reference)
    if value is None:
        return {"draw": index, "status": "INVALID", "reason": "UNIDENTIFIED"}
    return {"draw": index, "status": "VALID", "value": value}
