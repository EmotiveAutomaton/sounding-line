"""Registered diary rows 26–33. Each panel fixes its support before resampling.

DESIGN CHECK (LESSONS 2–5). The original uses within-person sums of products.
Replay centers individual reports again and fits weighted least squares. Both
use the same full-roster multiplicities, including persons outside the panel.
"""
from dataclasses import dataclass
import numpy as np
from . import week6_lb456_source_v1 as source
from . import week6_ld12_common_v1 as core


FIELDS = {
    "0070": ("silly", "expected", "important", "pleasant", "fearful", "sad"),
    "0076": ("interaction_playful", "stressed", "interaction_pleasant"),
    "0063": ("inspired", "good_at_this", "appreciated", "chose_doing", "doubt", "cheerful"),
    "0064": ("anger", "fear", "scorn", "distressed", "upset"),
}
ROWS = {
    "0070": {"26": ("expected",), "27": ("important",), "28": ("fearful", "sad")},
    "0076": {"29": ("stressed",)},
    "0063": {"32": ("good_at_this",), "33": ("appreciated",)},
    "0064": {"30": ("anger_fear",), "31": ("scorn_fear", "anger_fear")},
}


@dataclass
class Panel:
    member: str
    units: np.ndarray
    observed: np.ndarray
    products: np.ndarray
    frequency: dict


def build(member, projection):
    units, people, values, counts = projection
    values = dict(values)
    if member == "0064":
        for name, items in (("anger", source.ANGER), ("fear", source.FEAR), ("scorn", source.SCORN)):
            values[name] = np.column_stack([values[item] for item in items]).mean(axis=1)
    fields = FIELDS[member]
    data = np.column_stack([values[name] for name in fields])
    keep = np.isfinite(data).all(axis=1)
    ids, data = units[keep], data[keep]
    support = {"rows":len(ids), "people":len(np.unique(ids))}
    prepared = core.Prepared(people=people, metadata={"source":counts, "matched":support,
                            "excluded_incomplete":int((~keep).sum())})
    products = np.zeros((people, len(fields), len(fields)))
    for person in np.unique(ids):
        observations = data[ids == person]
        centered = observations - observations.mean(axis=0)
        products[person] = centered.T @ centered
    names = ("anger_fear", "scorn_fear") if member == "0064" else fields[1:]
    for name in names:
        core.metric(prepared, name, name, support, role="coefficient")
    for row, terms in ROWS[member].items():
        key = "row/"+row
        core.metric(prepared, key, " minus ".join(terms), support, role="registered", bar=.05)
        prepared.specs[key]["direction"] = "negative" if row in ("26","27","28","29","31") else "positive"
    frequency = {}
    if member == "0076":
        for name in ("interaction_playful", "interaction_meaningful"):
            for category in range(5):
                valid = (values["interaction_frequency"] == category) & np.isfinite(values[name])
                key = f"frequency/{category}/{name}"
                group = units[valid]
                frequency[key] = (np.bincount(group, weights=values[name][valid], minlength=people),
                                  np.bincount(group, minlength=people))
                core.metric(prepared, key, name+" by partner frequency", dict(rows=valid.sum(), people=len(np.unique(group))))
    prepared.panels[member] = Panel(member, ids, data, products, frequency)
    return prepared


def prepare(member, path, pin, missing_tokens, guard):
    return build(member, source.load(member, path, pin, missing_tokens, guard))


def fits(panel, mass, verify):
    partial = panel.member == "0064"
    split = 3 if partial else 1
    if verify:
        weights = mass[panel.units]
        if not len(weights) or not weights.sum():
            return {}
        z, _, _ = core.reference_within(panel.observed, panel.units, weights)
        x, y = z[:, split:], z[:, :split]
        coefficient = np.column_stack([core.reference_linear(x, col, weights) for col in y.T])
        if partial:
            residual = y - x @ coefficient
            matrix = residual.T @ (weights[:, None] * residual)
    else:
        matrix = np.tensordot(mass, panel.products, axes=(0,0))
        scale = np.sqrt(np.diag(matrix))
        if np.any(scale <= np.finfo(float).eps):
            return {}
        corr = matrix / np.outer(scale,scale)
        xx, xy = corr[split:,split:], corr[split:,:split]
        if np.linalg.matrix_rank(xx) != len(xx):
            return {}
        coefficient = np.linalg.solve(xx, xy)
        if partial:
            matrix = corr[:split,:split] - xy.T @ coefficient
    if not partial:
        return dict(zip(FIELDS[panel.member][1:], map(float,coefficient[:,0])))
    variances = np.diag(matrix)
    result = {}
    for key, idx in (("anger_fear",0), ("scorn_fear",2)):
        if min(variances[idx],variances[1]) > 1e-12*max(1., float(variances.max())):
            result[key] = float(matrix[idx,1]/np.sqrt(variances[idx]*variances[1]))
    return result


def evaluate(prepared, weights, guard, *, verify=False):
    guard()
    mass = core.multiplicities(prepared.people, weights)
    if mass.sum() != prepared.people:
        raise ValueError("Incomplete person resample")
    panel, = prepared.panels.values()
    result = dict.fromkeys(prepared.specs)
    try:
        result.update(fits(panel, mass, verify))
    except (np.linalg.LinAlgError, core.fits.InvalidFit):
        pass
    for row, terms in ROWS[panel.member].items():
        result["row/"+row] = result[terms[0]] if len(terms)==1 else core.contrast(result[terms[0]], result[terms[1]])
    for key, (sums, counts) in panel.frequency.items():
        n = counts @ mass
        if n:
            result[key] = float((sums @ mass)/n)
    core.record_point_dispositions(prepared, result, weights)
    return result
