"""Apply the two frozen MIDUS decoders and branch-specific eligibility in the seal."""
import numpy as np

import aggregate_register_v1 as register
import analysis_v1 as analysis
import independent_v1 as independent
import mi4_source_bridge_v1 as positive
import mi4_stats_v1 as mi4
import mi_source_bridge_v1 as negative


def decode(tables, wave, reference):
    daily, survey = tables["diary"], tables["survey"]
    if reference:
        people = independent.decode(daily, survey, wave)
        positive_people = independent.decode_positive(daily, survey, wave)
    else:
        people = negative.decode_rows(daily, survey, wave)[0]
        positive_people = positive.decode_rows(daily, survey, wave)[0]
    if [p["id"] for p in people] != [p["id"] for p in positive_people]:
        raise ValueError("positive and negative person rosters disagree")
    for person, other in zip(people, positive_people):
        if not np.array_equal(person["days"], other["days"]):
            raise ValueError("positive and negative diary days disagree")
        person.update({k: other[k] for k in ("positive", "pleasant_kinds", "extraversion")})
    return people


def ids(people):
    return {person["id"] for person in people}


def plan(tables, target, reference, branches=register.BRANCHES, measured=None):
    people_by_wave = {wave: decode(rows, wave, reference) for wave, rows in tables.items()}
    primary = people_by_wave["M2"]
    population = people_by_wave[target]
    diary_ids = {int(r["M2ID"]) for r in tables[target]["diary"]}
    survey_ids = {int(r["M2ID"]) for r in tables[target]["survey"]}
    counts = dict(zip(register.count_names()[:5], (
        diary_ids, survey_ids, diary_ids - survey_ids, survey_ids - diary_ids,
        diary_ids - ids(population),
    )))
    panels = {}
    if measured is not None and "M2ID" not in measured[target]["survey"]:
        for key in ("source.survey_people", "source.diary_without_survey", "source.survey_without_diary"):
            counts.pop(key)
    for branch in branches:
        initial = analysis.eligible_people(primary, branch, reference)
        primary_ids = ids(initial)
        available = population if target == "M2" else [p for p in population if p["id"] in primary_ids]
        eligible = initial if target == "M2" else analysis.eligible_people(available, branch, reference)
        available_ids, eligible_ids = ids(available), ids(eligible)
        panels[branch] = eligible
        trait = "extraversion" if branch in register.MI4_BRANCHES else "traits"
        groups = {
            "primary_roster": primary_ids, "available_for_wave": available_ids,
            "eligible": eligible_ids, "excluded_in_wave": available_ids - eligible_ids,
            "absent_repeat": set() if target == "M2" else primary_ids - available_ids,
            "complete_traits": {p["id"] for p in eligible if np.isfinite(p[trait]).all()},
        }
        if measured is not None:
            from mi_source_contract_v1 import fields
            roster_fields = fields(target)["traits"]
            required_traits = {roster_fields["extraversion"]} if branch in register.MI4_BRANCHES else {
                roster_fields["neuroticism"], roster_fields["agreeableness"]}
            if not required_traits.issubset(measured[target]["survey"]):
                groups.pop("complete_traits")
        counts.update({branch + "." + name: group for name, group in groups.items()})
        if branch == "MI3":
            excluded = independent.mi3_exclusions(available)
        elif branch in register.MI4_BRANCHES:
            excluded = (independent.mi4_exclusions(available, branch) if reference else
                        mi4.prepare(available, branch)["exclusions"])
        else:
            continue
        groups = {branch + ".exclusion." + name: set(keys) for name, keys in excluded.items()}
        if set().union(*groups.values()) != available_ids - eligible_ids:
            raise ValueError("exclusion partition differs")
        counts.update(groups)
    if (set(counts) - set(register.count_names()) or
            (measured is None and tuple(branches) == register.BRANCHES and set(counts) != set(register.count_names()))):
        raise ValueError("incomplete frozen count register")
    return panels, counts
