"""Registered interaction-diary products for rows 18, 19 and 20.

DESIGN CHECK (LESSONS 3–5). Symmetric outcomes give zero contrast. A planted
unpleasantness by dominance effect on anger must recover a positive contrast.
Occurrence uses the registered slider floor of five. Both outcomes use the
same complete interaction rows, bootstrap draws and predictor scaling.
"""
import numpy as np

from . import week6_lb2_source_v1 as source
from . import week6_ld12_common_v1 as core
from .week6_lattice_diary_v1 import InvalidFit


SLIDER_FLOOR = 5
TERMS = ("unpleasantness", "own_dominance", "unpleasantness_by_own_dominance")
OUTCOMES = ("angry", "nervous")
ERRORS = (InvalidFit, np.linalg.LinAlgError)


def build(member, data):
    row = source.MEMBERS[member].row
    counts = data.counts
    meta = dict(member=member, row=row, source=counts, floor=SLIDER_FLOOR,
                above_floor={k: int((data.y[:, i] > SLIDER_FLOOR).sum())
                             for i, k in enumerate(OUTCOMES)},
                conditional_sensitivity="No qualified within-person binary conditional logit in the diary core")
    result = core.Prepared(data.people, meta, panels={"interactions": data})
    for form in ("O", "L"):
        for outcome in OUTCOMES:
            for term in TERMS:
                core.metric(result, f"{form}/{outcome}/{term}", f"{term} on {outcome}",
                            counts, role="coefficient")
    label = "Unpleasantness by own dominance on anger minus nervousness"
    disposition = "below_support_floor" if counts["people"] < 20 else None
    core.metric(result, "row/" + row, label, counts, role="registered",
                bar=.05, disposition=disposition)
    core.metric(result, "linear_sensitivity/" + row, label, counts, role="sensitivity")
    core.metric(result, "occurrence_description/" + row, label, counts, role="descriptive")
    return result


def prepare(member, path, pin, missing_tokens, guard):
    return build(member, source.load(member, path, pin, missing_tokens, guard))


def evaluate(prepared, weights, guard, *, verify=False):
    row = prepared.metadata["row"]
    panel = prepared.panels["interactions"]
    mass = core.multiplicities(prepared.people, weights)
    if mass.sum() != prepared.people:
        raise ValueError("The draw must conserve the complete source-person roster")
    w = mass[panel.units]
    within, logit, linear = core.arithmetic(verify)
    result = dict.fromkeys(prepared.specs)
    guard()
    if w.sum() > 0:
        try:
            x, means, _ = within(panel.x, panel.units, w)
        except ERRORS:
            x = None
        if x is not None:
            terms = np.column_stack((x, x[:, 0] * x[:, 1]))
            design = np.column_stack((np.ones(len(w)), terms, means))
            for i, outcome in enumerate(OUTCOMES):
                y = panel.y[:, i]
                guard()
                try:
                    slopes = logit(design, y > SLIDER_FLOOR, w)[1:4]
                except ERRORS:
                    pass
                else:
                    result.update({f"O/{outcome}/{k}": float(s) for k, s in zip(TERMS, slopes)})
                guard()
                try:
                    centered, _, _ = within(y, panel.units, w)
                    slopes = linear(terms, centered[:, 0], w)
                except ERRORS:
                    pass
                else:
                    result.update({f"L/{outcome}/{k}": float(s) for k, s in zip(TERMS, slopes)})
    for form, name in (("O", "occurrence_description"), ("L", "linear_sensitivity")):
        left, right = (result[f"{form}/{outcome}/{TERMS[-1]}"] for outcome in OUTCOMES)
        result[f"{name}/{row}"] = core.contrast(left, right)
    if prepared.metadata["source"]["people"] >= 20:
        result["row/" + row] = result["occurrence_description/" + row]
    core.record_point_dispositions(prepared, result, weights)
    return result
