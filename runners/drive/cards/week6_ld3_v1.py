"""LD3. The solitary activity table, claims T6 and T2.

DESIGN CHECK: LESSONS 3–5. In a known linear panel the full joint table must
recover the planted slopes. Under the null the registered differences tend to
zero. Missing secondary ratings cannot change either primary's sample. Whole
people are resampled and within-person scales are recomputed on every draw.
"""
from dataclasses import dataclass

import numpy as np

from .week6_lattice_bindings_v1 import ACTIVITY, form_l
from .week6_lattice_diary_v1 import InvalidFit
from .week6_lattice_source_v1 import (
    complete_panel, feeling_names,
)


CONTRASTS = {
    "intellectual_enthusiastic_minus_relaxed": ("intellectual", "enthusiastic", "relaxed"),
    "overwhelmed_anxious_minus_angry": ("overwhelmed", "anxious", "angry"),
}


@dataclass
class Panel:
    outcomes: tuple
    counts: dict
    unit: np.ndarray
    x: np.ndarray
    y: np.ndarray
    clusters: np.ndarray
    crossproducts: np.ndarray


@dataclass
class Prepared:
    people: int
    metadata: dict
    specs: dict
    panels: dict


def _make_panel(people, outcomes):
    ids, values, counts = complete_panel(people, (*ACTIVITY, *outcomes))
    x = np.column_stack([values[k] for k in ACTIVITY])
    y = np.column_stack([values[k] for k in outcomes])
    # The source adapter groups by person. Each copy of a resampled person
    # therefore has the same within-person mean as their original rows.
    clusters, starts, sizes = np.unique(ids, return_index=True, return_counts=True)
    joined = np.column_stack((x, y))
    products = np.empty((len(clusters), joined.shape[1], joined.shape[1]))
    for i, (start, size) in enumerate(zip(starts, sizes)):
        block = joined[start:start + size]
        centered = block - block.mean(axis=0)
        products[i] = centered.T @ centered
    return Panel(tuple(outcomes), counts, ids, x, y, clusters, products)


def prepare_from_people(member, people, counts, guard):
    panels, specs, coverage = {}, {}, {}
    for name in feeling_names(member):
        guard()
        panel = _make_panel(people, (name,))
        panels[name] = panel
        coverage[name] = panel.counts
        for event in ACTIVITY:
            specs[f"table/{name}/{event}"] = {
                "role": "table", "label": f"{name} on {event}",
                "people": panel.counts["retained_people"], "rows": panel.counts["retained_rows"],
            }
    for key, (event, first, second) in CONTRASTS.items():
        guard()
        panel = _make_panel(people, (first, second))
        panels[key] = panel
        coverage[key] = panel.counts
        specs[f"contrast/{key}"] = {
            "role": "primary", "bar": .05, "direction": "positive",
            "label": f"{event} slope for {first} minus {second}",
            "people": panel.counts["retained_people"], "rows": panel.counts["retained_rows"],
        }
    return Prepared(len(people), dict(source=counts, coverage=coverage,
                    predictors=list(ACTIVITY), feelings=list(feeling_names(member))),
                    specs, panels)


def prepare(member, path, pin, missing_tokens, guard, *, include_description=True):
    from .week6_ld12_common_v1 import next_prompt_frames, source_projection
    from .week6_ld3_follow_v1 import describe
    projection = source_projection(member, path, pin, missing_tokens, guard, "LD3")
    people = []
    names = (*ACTIVITY, *feeling_names(member))
    for unit in range(projection.people):
        mask = projection.units == unit
        people.append(dict(source_ordinals=projection.ordinals[mask],
                           ratings={name: projection.values.get(name, np.empty(0))[mask] for name in names}))
    prepared = prepare_from_people(member, people, projection.counts, guard)
    if not include_description:
        return prepared
    frames = next_prompt_frames(member, path, pin, missing_tokens, guard)
    rows = (r for frame in frames for r in frame.to_dict("records"))
    prepared.metadata["next_answered_prompt"] = describe(rows, missing_tokens, guard)
    return prepared


def _coefficients(panel, masses, verify):
    if not len(panel.clusters) or not np.any(masses[panel.clusters]):
        raise InvalidFit("no complete sampled people")
    if verify:
        # An independent fit from the fresh original rows uses the installed
        # within-person projection and least-squares solver for every draw.
        keep = masses[panel.unit] > 0
        table = form_l(panel.unit[keep], panel.x[keep],
                       {k: panel.y[keep, j] for j, k in enumerate(panel.outcomes)},
                       masses[panel.unit[keep]])
        return np.column_stack([table[k] for k in panel.outcomes])
    joint = np.einsum("i,ijk->jk", masses[panel.clusters], panel.crossproducts)
    p = len(ACTIVITY)
    scales = np.sqrt(np.maximum(np.diag(joint), 0))
    if np.any(scales <= 0):
        raise InvalidFit("zero within-person scale")
    # Normalizing to a correlation matrix gives the same units as Form L.
    corr = joint / scales[:, None] / scales[None, :]
    xx = corr[:p, :p]
    if np.linalg.cond(xx) > 1e12:
        # The Gram matrix squares the condition number. Consult the raw-row
        # least-squares ruler before deciding a borderline draw lost rank.
        return _coefficients(panel, masses, verify=True)
    return np.linalg.solve(xx, corr[:p, p:])


def evaluate(prepared, weights, guard, *, verify=False):
    if weights is None:
        weights = np.ones(prepared.people, dtype=int)
    masses = np.asarray(weights)
    if (masses.shape != (prepared.people,) or not np.issubdtype(masses.dtype, np.integer)
            or np.any(masses < 0) or masses.sum() != prepared.people):
        raise ValueError("one whole-person multiplicity per source cluster required")
    values = dict.fromkeys(prepared.specs)
    for name, panel in prepared.panels.items():
        guard()
        try:
            beta = _coefficients(panel, masses, verify)
        except (InvalidFit, np.linalg.LinAlgError):
            continue
        if name in CONTRASTS:
            row = ACTIVITY.index(CONTRASTS[name][0])
            values[f"contrast/{name}"] = float(beta[row, 0] - beta[row, 1])
        else:
            for index, event in enumerate(ACTIVITY):
                values[f"table/{name}/{event}"] = float(beta[index, 0])
    return values
