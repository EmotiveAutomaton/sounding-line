"""Matched within-person student diary contrasts for lattice rows 11 to 17.

DESIGN CHECK (LESSONS 3–5). Same-row, same-person differences cancel the
planted exact null. The alternative separates the two target slopes. A
missing predictor, constant outcome, singular design or separated occurrence
fit is recorded without substituting zero. A draw always resamples people.
"""
from dataclasses import dataclass

import numpy as np

from . import week6_lb1_source_v1 as source
from . import week6_ld12_common_v1 as core
from .week6_lattice_diary_v1 import InvalidFit


@dataclass
class Panel:
    name: str
    predictors: tuple
    outcomes: tuple
    forms: tuple
    units: np.ndarray
    x: np.ndarray
    y: np.ndarray
    interaction: bool = False


# Each contrast points to columns already fitted on the same complete rows.
# An earlier predictor is aligned before complete-case selection.
REGISTRY = {
    "11": ("thinking", "L", "intellect", "curious", "content", .05),
    "12": ("opportunity_lag", "O", "prior_proud", "mating", None, .10),
    "13": ("opportunity_lag", "O", "prior_bored_schoolwork", "mating", None, .10),
    "14": ("opportunity_lag", "O", "prior_low_purpose", "mating", None, .10),
    "15": ("opportunity_now", "O", "mating", "excited", "content", .10),
    "16": ("argument", "L", "argument", "angry", "afraid", .05),
    "17": ("status", "O", "argument_by_dominant", "angry", "afraid", .05),
}
FIT_ERRORS = (InvalidFit, np.linalg.LinAlgError)


def build(data):
    prepared = core.Prepared(people=data.people, metadata={"source":data.counts, "panels":{}})
    current = np.arange(len(data.units))
    designs = (
        ("thinking",("intellect","positivity"),("curious","content"),("L",)),
        ("competence",("efficient","inventive","sociality","dominant"),("curious","excited"),("L",)),
        ("opportunity_lag",("prior_proud","prior_bored_schoolwork","prior_low_purpose","prior_mating","sociality"),("mating",),("O","L")),
        ("opportunity_now",("mating","sociality"),("excited","content"),("O","L")),
        ("argument",("argument",),("angry","afraid"),("L",)),
        ("status",("argument","dominant"),("angry","afraid"),("O","L")),
    )
    for name,predictors,outcomes,forms in designs:
        rows = data.later if name=="opportunity_lag" else current
        x = np.column_stack([data.values[k[6:]][data.earlier] if k.startswith("prior_")
                             else data.values[k][rows] for k in predictors])
        y = np.column_stack([data.values[k][rows] for k in outcomes])
        keep = np.isfinite(x).all(axis=1) & np.isfinite(y).all(axis=1)
        ids = data.units[rows][keep]
        panel = Panel(name,predictors,outcomes,forms,ids,x[keep],y[keep],name=="status")
        prepared.panels[name] = panel
        counts = {"rows":len(ids),"people":len(np.unique(ids))}
        prepared.metadata["panels"][name] = {**counts,"eligible_before_complete_cases":len(rows),
                                             "excluded_incomplete":int((~keep).sum())}
        terms = (*predictors,"argument_by_dominant") if panel.interaction else predictors
        for form in forms:
            for outcome in outcomes:
                for term in terms:
                    key = f"{name}/{form}/{outcome}/{term}"
                    core.metric(prepared,key,term+" on "+outcome,counts,role="coefficient")
    for row,(name,form,term,first,other,bar) in REGISTRY.items():
        counts = prepared.metadata["panels"][name]
        label = first+(" minus "+other if other else "")+" on "+term
        core.metric(prepared,"row/"+row,label,counts,role="registered",bar=bar)
        if form=="O":
            core.metric(prepared,"linear_sensitivity/"+row,label,counts,role="sensitivity")
    return prepared


def prepare(member,path,pin,missing_tokens,guard):
    if member!="0060":
        raise ValueError("Unregistered student diary")
    return build(source.load(path,pin,missing_tokens,guard))


def evaluate(prepared, weights, guard, *, verify=False):
    mass = core.multiplicities(prepared.people,weights)
    if mass.sum()!=prepared.people:
        raise ValueError("The draw must conserve its entire source-person roster")
    within,logit,linear = core.arithmetic(verify)
    result = dict.fromkeys(prepared.specs)
    for panel in prepared.panels.values():
        guard()
        w = mass[panel.units]
        if not len(w) or w.sum()==0:
            continue
        try:
            standardized,means,_ = within(panel.x,panel.units,w)
        except FIT_ERRORS:
            continue
        columns = panel.predictors
        if panel.interaction:
            standardized = np.column_stack((standardized,standardized[:,0]*standardized[:,1]))
            columns = (*columns,"argument_by_dominant")
        occurrence = np.column_stack((np.ones(len(w)),standardized,means))
        for j,outcome in enumerate(panel.outcomes):
            y = panel.y[:,j]
            for form in panel.forms:
                guard()
                try:
                    if form=="L":
                        target,_,_ = within(y,panel.units,w)
                        coefs = linear(standardized,target[:,0],w)
                    else:
                        coefs = logit(occurrence,y>1,w)[1:1+len(columns)]
                except FIT_ERRORS:
                    continue
                for term,val in zip(columns,coefs):
                    result[f"{panel.name}/{form}/{outcome}/{term}"] = float(val)
    for row,(name,form,term,first,other,_) in REGISTRY.items():
        forms = [(form,"row")] if form=="L" else [(form,"row"),("L","linear_sensitivity")]
        for fitted,key in forms:
            one = result[f"{name}/{fitted}/{first}/{term}"]
            two = result[f"{name}/{fitted}/{other}/{term}"] if other else None
            result[key+"/"+row] = core.contrast(one,two) if other else one
    core.record_point_dispositions(prepared,result,weights)
    return result
