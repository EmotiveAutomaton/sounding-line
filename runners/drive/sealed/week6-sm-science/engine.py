"""Two fresh joined-source decodes with frozen point and draw-level replay."""
import numpy as np

import aggregate_register_v1 as register
import analysis_v1 as analysis
import family_draws
from panels import ids, plan
from week6_sealed_support_v1 import SealedFailure


DRAW_COUNT = 2000


def equal_values(a, b):
    if a is None or b is None:
        return a is b
    return bool(np.allclose(a, b, rtol=1e-8, atol=1e-10))


def study(primary_tables, replay_tables, target, families=None, replay_families=None,
          branches=register.BRANCHES, measured=None, protected_groups=(), disclosure_groups=None):
    if families != replay_families:
        raise SealedFailure(14, "Independent family linkage differs")
    panels, counts = plan(primary_tables, target, False, branches, measured)
    reference, other_counts = plan(replay_tables, target, True, branches, measured)
    if counts != other_counts:
        raise SealedFailure(14, "Independent source or aggregate comparison differs")
    results = {}
    all_groups = [*counts.values(), *protected_groups]
    if target == "M3":
        # Previous primary returns and repeat counts can be read together.
        # Include the full primary register in the same membership-cell check.
        from table_support import supported_columns
        primary_branches = register.BRANCHES if measured is None else tuple(
            branch for branch in supported_columns({"M2": measured["M2"]}, "M2")
            if branch in register.BRANCHES)
        primary_panels, primary_counts = plan({"M2": primary_tables["M2"]}, "M2", False, primary_branches, measured)
        other_primary, independent_counts = plan({"M2": replay_tables["M2"]}, "M2", True, primary_branches, measured)
        if primary_counts != independent_counts:
            raise SealedFailure(14, "Independent primary eligibility differs")
        all_groups.extend(primary_counts.values())
        for name, people in primary_panels.items():
            groups = analysis.groups_for(people, name)
            if groups != analysis.groups_for(other_primary[name], name):
                raise SealedFailure(14, "Independent primary contributing groups differ")
            all_groups.extend([groups[0], *groups[1]])
    for branch in branches:
        people, other = panels[branch], reference[branch]
        if [p["id"] for p in people] != [p["id"] for p in other]:
            raise SealedFailure(14, "Independent source or aggregate comparison differs")
        contributors, required = analysis.groups_for(people, branch)
        if (contributors, required) != analysis.groups_for(other, branch):
            raise SealedFailure(14, "Independent source or aggregate comparison differs")
        all_groups.append(contributors)
        all_groups.extend(required)
        results[branch] = (people, other, contributors, required)
    # The original registry withholds every exact n if the source/count sets
    # permit a small complementary count. The installed gate requires exact n.
    if not register.exact_counts_safe(all_groups):
        raise SealedFailure(12, "Unsafe complementary population count")
    if disclosure_groups is not None:
        # Private memberships for the one final complementary-count gate.
        disclosure_groups.extend(all_groups)
    estimates, unavailable, coverage = [], [], []
    for branch_index, branch in enumerate(register.BRANCHES, start=1):
        if branch not in results:
            continue
        people, other, contributors, required = results[branch]
        actual = contributors.intersection(*required)
        if len(actual) < 11:
            continue
        stats = analysis.prepare(people, branch)
        other_stats = analysis.prepare(other, branch, True)
        point = analysis.private_point(people, stats, branch)
        expected = analysis.private_point(other, other_stats, branch, True)
        if not equal_values(point, expected):
            raise SealedFailure(14, "Independent source or aggregate comparison differs")
        rows, replay = [], []
        groups = family_draws.roster(people, families) if families is not None else None
        other_groups = family_draws.roster(other, replay_families, reference=True) if families is not None else None
        if not np.array_equal(groups, other_groups):
            raise SealedFailure(14, "Independent family ordering differs")
        # Missing individual links keep the observed point; its family interval is unavailable.
        if point is not None and (families is None or groups is not None):
            for index in range(DRAW_COUNT):
                seed = register.SEEDS[branch]
                if families is None:
                    row = analysis.draw_record(people, stats, branch, seed, index)
                    ref = analysis.draw_record(other, other_stats, branch, seed, index, True)
                else:
                    row = family_draws.draw_record(people, stats, groups, branch, seed, index)
                    ref = family_draws.draw_record(other, other_stats, other_groups, branch, seed, index, True)
                analysis.same_record(row, ref)
                rows.append(row)
                replay.append(ref)
        result = analysis.summarize(point, rows, contributors, required)
        verified = analysis.summarize(expected, replay, contributors, required)
        if not all(equal_values(result[k], verified[k]) for k in ("point", "interval", "se")):
            raise SealedFailure(14, "Independent source or aggregate comparison differs")
        invalid = sum(r["status"] != "VALID" for r in rows)
        for param in range(len(register.columns(branch))):
            mode = 1 if families is None else (2 if groups is not None else 3)
            identity = {"branch": branch_index, "parameter": param + 1, "n": len(actual), "resampling": mode,
                        "descriptive": int(len(actual) < 20)}
            if result["interval"] is not None:
                low, high = result["interval"][param]
                estimates.append(dict(identity, estimate=point[param], lower=low, upper=high,
                                      standard_error=result["se"][param]))
            elif point is None:
                unavailable.append(identity)
            else:
                coverage.append(dict(identity, estimate=point[param], draws=len(rows),
                                     invalid_draws=invalid))
    counts_table = [
        {"count_group": index, "n": len(counts[name])}
        for index, name in enumerate(register.count_names(), start=1) if name in counts and len(counts[name]) >= 11
    ]
    return {name: rows for name, rows in (
        ("estimates", estimates), ("unidentified", unavailable),
        ("interval_unavailable", coverage), ("counts", counts_table),
    ) if rows}
