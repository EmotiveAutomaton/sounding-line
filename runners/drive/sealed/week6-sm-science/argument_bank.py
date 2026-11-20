"""Sealed whole-family comparisons of resolved and unresolved arguments (BF)."""
from math import fsum

import numpy as np

import argument_panel as panel
import family_draws
from week6_sealed_support_v1 import SealedFailure


SEED = 2026112025
DRAWS = 2000
WITHIN, ALL_REPORTS, SAME_DAY = 1, 2, 3


def contributors(data):
    resolved = {p for p,row in data.items() if row[1]}
    unresolved = {p for p,row in data.items() if row[3]}
    paired = resolved & unresolved
    same = {p for p in paired if data[p][5] and data[p][7]}
    return {WITHIN:paired, ALL_REPORTS:resolved | unresolved, SAME_DAY:same}, (resolved, unresolved)


def released_sets(plan, data):
    support_groups, _ = panel.support_summary(plan)
    groups, margins = contributors(data)
    return [s for s in (*support_groups, *groups.values(), *margins) if len(s) >= 11]


def _scores(matrix, weights, which, reference):
    if which == ALL_REPORTS:
        if reference:
            pooled = [fsum(w*x for w,x in zip(weights, matrix[:,i])) for i in range(4)]
        else:
            pooled = weights @ matrix[:,:4]
        return pooled[2]/pooled[3]-pooled[0]/pooled[1] if pooled[1] and pooled[3] else None
    start = 4 if which == SAME_DAY else 0
    if reference:
        contrast = fsum(w*(row[start+2]/row[start+3] - row[start]/row[start+1])
                        for row,w in zip(matrix,weights) if w)
        return contrast/fsum(weights)
    per_person = matrix[:,start+2]/matrix[:,start+3] - matrix[:,start]/matrix[:,start+1]
    return float(np.average(per_person, weights=weights))


def compare_branch(data, replica, people, which, families, replay_families):
    ids = sorted(people)
    roster = [{"id":p} for p in ids]
    x, y = (np.asarray([source[p] for p in ids], dtype=float) for source in (data, replica))
    if not np.array_equal(x,y):
        raise SealedFailure(14, "Argument panels differ")
    if families is None:
        groups = alt = np.arange(len(ids))
        mode = 1
    else:
        groups = family_draws.roster(roster, families)
        alt = family_draws.roster(roster, replay_families, reference=True)
        mode = 2 if groups is not None else 3
    if not np.array_equal(groups,alt):
        raise SealedFailure(14, "Argument family allocation differs")
    def checked(weights, independent):
        a = _scores(x,weights,which,False)
        b = _scores(y,independent,which,True)
        if (a is None)!=(b is None) or a is not None and not np.isclose(a,b,rtol=1e-9,atol=1e-10):
            raise SealedFailure(14, "Argument estimate differs on independent replay")
        return a
    ones = np.ones(len(ids))
    point = checked(ones, ones)
    values = []
    if groups is not None:
        for index in range(DRAWS):
            w = family_draws.multiplicities(groups, SEED, index)
            v = family_draws.multiplicities(alt, SEED, index, independent=True)
            if not np.array_equal(w,v):
                raise SealedFailure(14, "Argument family draw differs on replay")
            if np.count_nonzero(w)<11:
                continue
            if which==ALL_REPORTS and any(np.count_nonzero((w>0)&(x[:,j]>0))<11 for j in (1,3)):
                continue
            estimate = checked(w,v)
            if estimate is not None:
                values.append(estimate)
    identity = dict(comparison=which, n=len(ids), resampling=mode, valid_draws=len(values))
    if len(values) == DRAWS:
        lower, upper = np.quantile(values,[.025,.975])
        return dict(identity, estimate=point, lower=float(lower), upper=float(upper)), True
    return dict(identity, estimate=point), False


def run(exposure, data, replica, families, replay_families):
    if families != replay_families:
        raise SealedFailure(14, "Argument family linkage differs")
    support_groups, support_rows = panel.support_summary(exposure)
    groups, margins = contributors(data)
    result = {"argument_support":support_rows}
    stored = {}
    for which, ids in groups.items():
        if len(ids)<11 or which==ALL_REPORTS and any(len(arm)<11 for arm in margins):
            continue
        row, has_interval = compare_branch(data, replica, ids, which, families, replay_families)
        name = "argument_estimates" if has_interval else "argument_point_only"
        stored[which] = row
        result.setdefault(name, []).append(row)
    # Report the denominators for both actually analysed arms of the pooled comparison.
    if ALL_REPORTS in stored:
        result["argument_report_people"] = [dict(n=len(margin), resolution=i)
                                            for i,margin in enumerate(margins,1)]
    primary = stored.get(WITHIN)
    if primary is not None:
        descriptive = stored.get(ALL_REPORTS)
        disagreement = bool(descriptive and primary["estimate"]*descriptive["estimate"] < 0)
        if disagreement:
            verdict = 4
        elif len(support_groups[0])<100 or "lower" not in primary or descriptive is None:
            verdict = 3
        elif primary["lower"]>0:
            verdict = 1
        elif primary["upper"]<0:
            verdict = 5
        else:
            verdict = 2
        result["argument_reading"] = [dict(n=primary["n"], support_met=int(len(support_groups[0])>=100),
                                        sign_disagreement=int(disagreement), decision=verdict)]
    return result
