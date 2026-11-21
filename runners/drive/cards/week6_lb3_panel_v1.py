"""Matched parent-diary regressions and complete tables for rows 21 through 25.

DESIGN CHECK (LESSONS 3–5). All operands in a registered difference use
identical parent-days. The five contrasts retain their registered direction,
including the negative fear-minus-sadness contrast. A constant input or
unidentified model gives a missing estimate. Every draw resamples parents.
"""
from dataclasses import dataclass

import numpy as np

from . import week6_lb3_source_v1 as source
from . import week6_ld12_common_v1 as core
from .week6_lattice_diary_v1 import InvalidFit


EVENTS = (*source.STRESSORS, *source.NEED_ITEMS)
BLOCKED = ("blocked", *(key for key in EVENTS if key not in ("told_what_to_do", "against_own_will")))
THREAT = ("health_or_financial", *(key for key in EVENTS if key not in ("stressor_health", "stressor_financial")))
CARE = ("child_distress", "time_minutes")
PLAY = ("parent_afraid", "parent_sad", "parent_angry", "parent_exhausted",
        "parenting_disagreements", "time_minutes")
COMPARE = {
    "21": ("blocked", (("parent_angry","blocked",1.), ("parent_afraid","blocked",-1.))),
    "22": ("threat", (("parent_afraid","health_or_financial",.5),
                      ("parent_worried","health_or_financial",.5), ("parent_angry","health_or_financial",-1.))),
    "23": ("exclusion", (("parent_sad","excluded_ostracized",1.), ("parent_angry","excluded_ostracized",-1.))),
    "24": ("matched_care", (("parent_worried","child_distress",1.), ("parent_angry","child_distress",-1.))),
    "25": ("play", (("parenting_fun","parent_afraid",1.), ("parenting_fun","parent_sad",-1.))),
}
FIT_ERRORS = (InvalidFit, np.linalg.LinAlgError)


@dataclass
class Panel:
    predictors: tuple
    outcomes: tuple
    units: np.ndarray
    x: np.ndarray
    y: np.ndarray


def build(data):
    prepared = core.Prepared(people=data.people, metadata={"source": data.counts, "panels": {}})

    def add(name, predictors, outcomes):
        x = np.column_stack([data.values[k] for k in predictors])
        y = np.column_stack([data.values[k] for k in outcomes])
        complete = np.isfinite(x).all(axis=1) & np.isfinite(y).all(axis=1)
        ids = data.units[complete]
        panel = Panel(predictors, outcomes, ids, x[complete], y[complete])
        prepared.panels[name] = panel
        count = dict(rows=len(ids), people=len(np.unique(ids)), eligible_before_complete_cases=len(complete),
                     excluded_incomplete=int((~complete).sum()))
        prepared.metadata["panels"][name] = count
        for outcome in outcomes:
            for key in predictors:
                core.metric(prepared, f"{name}/{outcome}/{key}", key+" on "+outcome, count, role="coefficient")

    for outcome in ("parent_angry", "parent_afraid", "parent_worried", "parent_sad"):
        add("events_"+outcome, EVENTS, (outcome,))
    for outcome in (*source.PARENT_FEELINGS, "parenting_talked_worries"):
        add("care_"+outcome, CARE, (outcome,))
    add("blocked", BLOCKED, ("parent_angry","parent_afraid"))
    add("threat", THREAT, ("parent_afraid","parent_worried","parent_angry"))
    add("exclusion", EVENTS, ("parent_sad","parent_angry"))
    add("matched_care", CARE, ("parent_worried","parent_angry"))
    add("play", PLAY, ("parenting_fun",))
    for row, (name, terms) in COMPARE.items():
        key = "row/"+row
        count = prepared.metadata["panels"][name]
        core.metric(prepared, key, name.replace("_"," ")+" contrast", count, role="registered", bar=.05)
        prepared.specs[key]["direction"] = "negative" if row=="25" else "positive"
    return prepared


def prepare(member, path, pin, missing_tokens, guard):
    if member != "0072":
        raise ValueError("Unregistered parent-diary member")
    return build(source.load(path, pin, missing_tokens, guard))


def evaluate(prepared, weights, guard, *, verify=False):
    mass = core.multiplicities(prepared.people, weights)
    if mass.sum() != prepared.people:
        raise ValueError("Draw lost a parent")
    within, _, linear = core.arithmetic(verify)
    values = dict.fromkeys(prepared.specs)
    for name, panel in prepared.panels.items():
        guard()
        w = mass[panel.units]
        if not len(w) or w.sum() == 0:
            continue
        try:
            x, _, _ = within(panel.x, panel.units, w)
        except FIT_ERRORS:
            continue
        for j, outcome in enumerate(panel.outcomes):
            try:
                y, _, _ = within(panel.y[:,j], panel.units, w)
                slopes = linear(x, y[:,0], w)
            except FIT_ERRORS:
                continue
            for key, slope in zip(panel.predictors, slopes):
                values[f"{name}/{outcome}/{key}"] = float(slope)
    for row, (name, terms) in COMPARE.items():
        inputs = [(values[f"{name}/{outcome}/{key}"], weight) for outcome,key,weight in terms]
        if all(value is not None for value, _ in inputs):
            values["row/"+row] = float(sum(value*weight for value,weight in inputs))
    core.record_point_dispositions(prepared, values, weights)
    return values
