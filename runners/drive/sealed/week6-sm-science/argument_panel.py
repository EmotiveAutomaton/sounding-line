"""MIDUS D5.s, amendment BF. Keep argument routing separate from feeling data."""
from collections import defaultdict
from math import fsum

import mi_source_contract_v1 as contract
from joined_source import read_roles
from nt1_daily import identity
from week6_sealed_support_v1 import SealedFailure


def _day(row, fields):
    person = identity(row["M2ID"])
    day = contract.valid_code(row[fields["study_day"]], range(1, 9), missing=())
    return person, None if day is None else int(day)


def exposure(rows):
    """Inspect only occurrence, resolution and dates. Pair true adjacent study days."""
    fields = contract.fields("M2")
    calendars = defaultdict(dict)
    for row in rows:
        person, day = _day(row, fields)
        if day is None:
            continue
        if day in calendars[person]:
            raise SealedFailure(11, "Duplicate argument-source person-day")
        weekday = contract.valid_code(row[fields["weekday"]], range(1, 8), missing=())
        events = [contract.valid_code(row[item["occurrence"]], (1, 2)) for item in fields["stressors"]]
        clear = all(value == 2 for value in events)
        argument = contract.valid_code(row["B2DF1"], (1, 2))
        resolution = contract.valid_code(row["B2DF1WC6"], (1, 2)) if argument == 1 else None
        calendars[person][day] = (weekday, clear, resolution)
    baseline, arguments = {}, {}
    for person, days in sorted(calendars.items()):
        baseline[person] = tuple(day for day in sorted(days) if days[day][1])
        for day, (weekday, _, resolution) in sorted(days.items()):
            if resolution is None or day+1 not in days:
                continue
            next_weekday = days[day+1][0]
            if contract.adjacent_days(day, day+1, weekday, next_weekday, "M2"):
                arguments[(person, day)] = int(resolution)
    return baseline, arguments


def support_plan(paths):
    fields = contract.fields("M2")
    names = {"M2ID", fields["study_day"], fields["weekday"], "B2DF1", "B2DF1WC6"}
    names.update(item["occurrence"] for item in fields["stressors"])
    def projection():
        return read_roles({"diary":paths["diary"]}, {"diary":sorted(names)})["diary"]
    original = exposure(projection())
    repeat = exposure(reversed(projection()))
    if original != repeat:
        raise SealedFailure(14, "Argument exposure roster differs on reconstruction")
    return original


def support_summary(plan):
    _, arguments = plan
    people = {kind: {p for (p,_), v in arguments.items() if v == kind} for kind in (1, 2)}
    both = people[1] & people[2]
    groups = [both, people[1], people[2]]
    status = []
    for code, group in enumerate(groups, 1):
        kinds = (1, 2) if code==1 else (code-1,)
        counts = {kind: sum(p in group and v==kind for (p,_),v in arguments.items()) for kind in kinds}
        status.append(dict(group=code, n=len(group), resolved_days=counts.get(1,0),
                           unresolved_days=counts.get(2,0), primary_support_met=int(len(both)>=100) if code==1 else -1))
    return groups, status


def daily_scores(rows, replay=False):
    fields = contract.fields("M2")
    result = {}
    for row in rows:
        person, day = _day(row, fields)
        if day is None:
            continue
        if (person, day) in result:
            raise SealedFailure(11, "Duplicate argument outcome on a study day")
        values = [contract.valid_code(row[name], range(5)) for name in fields["negative"]]
        if any(value is None for value in values):
            score = None
        else:
            score = (fsum(reversed(values)) if replay else sum(values)) / len(values)
        result[person, day] = score
    return result


def person_totals(plan, outcomes):
    """Sufficient statistics per person; held only in the seal.

    Columns are sums and counts for resolved and unresolved next-day reports,
    then for the corresponding same-day reports. Both use the person's
    complete stressor-free day scores as their baseline.
    """
    baseline_days, arguments = plan
    baseline = {}
    for person, days in baseline_days.items():
        valid = [outcomes[person, day] for day in days if outcomes[person, day] is not None]
        if valid:
            baseline[person] = fsum(valid)/len(valid)
    grouped = defaultdict(lambda: [[] for _ in range(4)])
    for (person, day), resolution in sorted(arguments.items()):
        if person not in baseline:
            continue
        following = outcomes[person, day+1]
        if following is None:
            continue
        index = resolution-1
        grouped[person][index].append(following-baseline[person])
        on_day = outcomes[person, day]
        if on_day is not None:
            grouped[person][2+index].append(on_day-baseline[person])
    return {p:tuple(item for values in sides for item in (fsum(values), len(values)))
            for p,sides in sorted(grouped.items())}


def outcome_plan(paths, plan):
    fields = contract.fields("M2")
    names = ["M2ID", fields["study_day"], *fields["negative"]]
    def decode(replay):
        rows = read_roles({"diary":paths["diary"]}, {"diary":names})["diary"]
        return person_totals(plan, daily_scores(reversed(rows) if replay else rows, replay))
    first, second = decode(False), decode(True)
    if first != second:
        raise SealedFailure(14, "Independent argument-day decoding differs")
    return first, second
