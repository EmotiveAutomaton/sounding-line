"""Wave-two daily trait panel and its fixed whole-cluster return.

DESIGN CHECK (LESSONS 3–5). Support is counted on exposures before the
outcome projection is opened. Family identifiers never leave the sealed
job. Each parameter needs its own complete bank, and both decoders and
solvers must agree on availability as well as every retained number.
"""
import numpy as np

import family_draws
import mi_source_contract_v1 as contract
import nt1_daily as daily
from joined_source import read_roles
from table_support import required_columns
from week6_sealed_support_v1 import SealedFailure


DRAWS = 2000
BRANCH_RESULTS = ("slower_decay", "unread_lower_baseline", "stronger_first",
                  "saturation", "proportional_strength", "no_placement", "could_not_say")


def plan(paths):
    """Read only the identifiers, clocks, stressors and trait until support is known."""
    spec = contract.fields("M2")
    fields = required_columns("M2", "NT1.s")
    fields["diary"] -= set(spec["negative"])
    projection = {role: sorted(columns) for role, columns in fields.items()}
    first = daily.support(read_roles(paths, projection))
    second = daily.support(read_roles(paths, projection), replay=True)
    if first != second:
        raise SealedFailure(14, "Daily exposure roster differs on replay")
    pairs, exposed, pair_count = first
    ready = pair_count >= 300 and len(exposed) >= 150
    panel = replay = None
    if ready:
        columns = ["M2ID", spec["study_day"], *spec["negative"]]
        source = {"diary": paths["diary"]}
        panel = daily.panel(read_roles(source, {"diary": columns}), pairs)
        replay = daily.panel(read_roles(source, {"diary": columns}), second[0], replay=True)
        if (panel is None) != (replay is None) or (panel is not None and
                any(not np.array_equal(panel[key], replay[key]) for key in panel)):
            raise SealedFailure(14, "Daily contributing records differ on replay")
    return {"exposed": exposed, "pairs": pair_count, "support": ready, "panel": panel, "replay": replay}


def released_sets(design):
    """Person memberships whose exact counts can appear alongside other sealed results."""
    groups = []
    if len(design["exposed"]) >= 11:
        groups.append(design["exposed"])
    panel = design["panel"]
    if panel is not None and len(panel["ids"]) >= 11:
        groups.append(set(int(v) for v in panel["ids"]))
    return groups


def checked_values(point, replay):
    if (point is None) != (replay is None):
        raise SealedFailure(14, "Daily coefficient availability differs")
    if point is None:
        return [None] * len(daily.PARAMETERS)
    if len(point) != len(daily.PARAMETERS) or len(replay) != len(point):
        raise SealedFailure(14, "Daily coefficient register differs")
    for a, b in zip(point, replay):
        if (a is None) != (b is None) or (a is not None and
                not np.isclose(a, b, rtol=1e-7, atol=1e-8)):
            raise SealedFailure(14, "Daily independent coefficient differs")
    return point


def run(design, families, independent_families):
    if families != independent_families:
        raise SealedFailure(14, "Family linkage differs")
    exposed = len(design["exposed"])
    result = {}
    if exposed >= 11:
        result["daily_exposure"] = [dict(n=exposed, previous_stressor_pairs=design["pairs"],
                                         support_met=int(design["support"]))]
    panel, replay = design["panel"], design["replay"]
    if panel is None or len(panel["ids"]) < 11:
        return result
    people = [{"id": int(v)} for v in panel["ids"]]
    n = len(people)
    if families is None:
        groups = independent_groups = np.arange(n)
        mode = 1
    else:
        groups = family_draws.roster(people, families)
        independent_groups = family_draws.roster(people, independent_families, reference=True)
        mode = 3 if groups is None else 2
    if not np.array_equal(groups, independent_groups):
        raise SealedFailure(14, "Daily family assignments differ")
    point = checked_values(daily.score(panel, np.ones(n)), daily.score(replay, np.ones(n), True))
    bank = []
    if groups is not None and any(value is not None for value in point):
        for ordinal in range(DRAWS):
            w = family_draws.multiplicities(groups, daily.SEED, ordinal)
            w2 = family_draws.multiplicities(independent_groups, daily.SEED, ordinal, independent=True)
            if not np.array_equal(w, w2):
                raise SealedFailure(14, "Daily whole-cluster allocation differs")
            if np.count_nonzero(w) < 11:
                bank.append([None] * len(point))
                continue
            bank.append(checked_values(daily.score(panel, w), daily.score(replay, w2, True)))
    intervals = [None] * len(point)
    for index, value in enumerate(point):
        identity = dict(parameter=index+1, n=n, resampling=mode, descriptive=int(n < 20))
        values = [row[index] for row in bank if row[index] is not None]
        if value is None:
            result.setdefault("daily_unidentified", []).append(identity)
        elif len(values) != DRAWS:
            result.setdefault("daily_point_only", []).append(dict(identity, estimate=value,
                draws=len(bank), valid_draws=len(values)))
        else:
            low, high = np.quantile(values, [.025, .975])
            intervals[index] = [float(low), float(high)]
            result.setdefault("daily_estimates", []).append(dict(identity, estimate=value,
                lower=float(low), upper=float(high), standard_error=float(np.std(values, ddof=1))))
    fate = daily.interpretation(intervals[6], point[2], intervals[3])
    result["daily_reading"] = [dict(n=n, resampling=mode, decision=BRANCH_RESULTS.index(fate)+1)]
    return result
