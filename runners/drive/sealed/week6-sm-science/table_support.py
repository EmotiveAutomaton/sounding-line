"""Frozen field dependencies for the MIDUS joined tables (amendment AX)."""
import aggregate_register_v1 as register
from mi_source_contract_v1 import fields


EXTRAS = ("NT1.s", "D5.s")
TABLE_IDS = {name: i for i, name in enumerate((*register.BRANCHES, *EXTRAS), start=1)}


def required_columns(wave, name):
    """Return exactly the measurements that define this branch in this wave."""
    spec = fields(wave)
    daily = {spec["person"], spec["study_day"]}
    survey = set()
    stressors = spec["stressors"]
    effects = set(spec["negative"])
    occurrence = {s["occurrence"] for s in stressors}
    controls = {s["control"] for s in stressors}
    if name == "MI1":
        daily.update(effects, occurrence, controls, (s["severity"] for s in stressors))
        for s in stressors:
            daily.update(s["risks"].values())
    elif name in ("MI2", "MI2-reliability", "MI2-traits"):
        indices = (12, 9, 13, 7, 1, 8)
        daily.update(occurrence, (spec["negative"][i] for i in indices))
        if name == "MI2-traits":
            survey.update((spec["person"], spec["traits"]["neuroticism"], spec["traits"]["agreeableness"]))
    elif name in ("MI3", "MI3-direction"):
        daily.update(effects, occurrence, controls, (spec["weekday"],))
    elif name in register.MI4_BRANCHES:
        daily.update(spec["positive"], spec["positive_events"])
        survey.update((spec["person"], spec["traits"]["extraversion"]))
    elif wave == "M2" and name in EXTRAS:
        daily.update(effects, (spec["weekday"],))
        if name == "NT1.s":
            daily.update(occurrence)
            survey.update((spec["person"], spec["traits"]["neuroticism"]))
        else:
            daily.update(("B2DF1", "B2DF1WC6"))
    else:
        raise ValueError("Unregistered study or wave")
    return {"diary": daily, "survey": survey}


def table_names(target):
    return (*register.BRANCHES, *EXTRAS) if target == "M2" else register.BRANCHES


def supported_columns(measured, target):
    """A repeat requires each of its fields in both waves. Added studies use M2 only."""
    return tuple(name for name in table_names(target)
                 if all(required.issubset(measured[wave][role])
                        for wave in measured
                        for role, required in required_columns(wave, name).items()))


def source_status(measured, people, target):
    """Every status count is the actual roster of the specified input table."""
    enabled = set(supported_columns(measured, target))
    rows = []
    for wave in sorted(measured):
        for name in table_names(target):
            for role, required in required_columns(wave, name).items():
                keys = people[wave][role]
                if not required or len(keys) < 11:
                    continue
                rows.append(dict(branch=TABLE_IDS[name], wave=int(wave[1]), table_role=1 if role == "survey" else 2,
                                 n=len(keys), fields_required=len(required),
                                 fields_present=len(required & measured[wave][role]),
                                 fields_supported=int(name in enabled)))
    return rows
