"""Stage-one within-person carry after criticism, from Round 32, section 4.

The chronology and support projection opens no feeling or trait columns.
The primary and descriptive row reuse the qualified Form O arithmetic.
"""
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from . import week6_ld12_common_v1 as common
from .es_clock_v1 import utc_seconds
from .es_source_v1 import sha256
from .week6_lattice_diary_v1 import InvalidFit


EVENTS = ("criticised", "admired", "ignored", "respected", "upstaged", "sidelined")
FEELINGS = ("angry", "ashamed", "insecure", "anxious", "sad")
EXPOSURE_COLUMNS = ("id", "day", "created_esm", "ended_esm", "interaction",
                    *("status_" + name for name in EVENTS))
FEELING_COLUMNS = tuple(prefix + name for prefix in ("int_", "occup_") for name in FEELINGS)


@dataclass
class Selection:
    people: int
    current: np.ndarray
    units: np.ndarray
    context: np.ndarray
    hours: np.ndarray
    events: np.ndarray
    counts: dict

    def summary(self):
        cuts = np.quantile(self.hours, [1 / 3, 2 / 3]).tolist() if len(self.hours) else []
        return {"counts": self.counts, "gap_cuts_hours": cuts,
                "supported": self.counts["prior_criticised_prompts"] >= 300
                and self.counts["prior_criticised_people"] >= 150}


def project_source(path, pin, columns, guard):
    path = Path(path)
    if path.stat().st_size != pin["bytes"] or sha256(path, guard) != pin["sha256"]:
        raise ValueError("Diary source differs before projection")
    with pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False,
                     na_filter=False, usecols=list(columns), chunksize=20000) as reader:
        frames = []
        for frame in reader:
            guard()
            frames.append(frame.loc[:, list(columns)])
    if sha256(path, guard) != pin["sha256"]:
        raise ValueError("Diary source changed during projection")
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=columns)


def codes(series, missing, low, high):
    present = ~series.isin(missing)
    values = pd.to_numeric(series.where(present), errors="coerce")
    if (present & ~values.isin(range(low, high + 1))).any():
        raise ValueError("Undocumented nonmissing diary rating in " + str(series.name))
    return values.to_numpy(dtype=float, na_value=np.nan)


def select_lags(frame, missing, guard):
    if tuple(frame.columns) != EXPOSURE_COLUMNS:
        raise ValueError("Support requires the frozen exposure-only projection")
    frame = frame.reset_index(drop=True)
    identifiers = frame["id"]
    roster = {s: i for i, s in enumerate(sorted(set(identifiers) - set(missing)))}
    counts = Counter(source_rows=len(frame), source_people=len(roster),
                     missing_identity_rows=int(identifiers.isin(missing).sum()))
    contexts = codes(frame["interaction"], missing, 1, 2)
    event_columns = [codes(frame["status_" + name], missing, 1, 6) - 1 for name in EVENTS]
    all_events = np.column_stack(event_columns)
    current, units, context, gaps, event_vectors = [], [], [], [], []
    valid = frame.loc[~identifiers.isin(missing)]
    for who, rows in valid.groupby("id", sort=True):
        guard()
        indices = rows.index.to_numpy(dtype=int)
        clocks = ("day", "created_esm", "ended_esm")
        if rows.loc[:, list(clocks)].isin(missing).any().any():
            counts["unplaceable_clock_people"] += 1
            continue
        created = np.array([utc_seconds(value) for value in rows["created_esm"]])
        answered = np.array([utc_seconds(value) for value in rows["ended_esm"]])
        utc_days = np.floor_divide(created, 86400).astype(int)
        study_day = pd.to_numeric(rows["day"], errors="coerce").to_numpy()
        if (np.any(answered < created) or len(np.unique(answered)) != len(answered)
                or not np.array_equal(study_day, utc_days - utc_days.min() + 1)):
            counts["ambiguous_clock_or_study_day_people"] += 1
            continue
        order = np.argsort(answered)
        for left, right in zip(order[:-1], order[1:]):
            if utc_days[left] != utc_days[right]:
                counts["cross_day_pairs"] += 1
                continue
            gap = (answered[right] - answered[left]) / 3600
            if not 0 < gap <= 4:
                counts["over_four_hours"] += 1
                continue
            pre, now = indices[left], indices[right]
            if contexts[pre] != 1 or not np.isfinite(contexts[now]):
                counts["ineligible_context_pairs"] += 1
                continue
            # A solitary prompt has zero exposure to an interaction event.
            latest = all_events[now] if contexts[now] == 1 else np.zeros(len(EVENTS))
            predictors = np.r_[latest, all_events[pre]]
            if not np.isfinite(predictors).all():
                counts["incomplete_event_pairs"] += 1
                continue
            current.append(now)
            units.append(roster[who])
            context.append(int(contexts[now]))
            gaps.append(gap)
            event_vectors.append(predictors)
    unit = np.asarray(units, dtype=int)
    events = np.asarray(event_vectors, dtype=float).reshape((-1, 2 * len(EVENTS)))
    criticised = events[:, len(EVENTS)] > 0
    counts.update(eligible_prompts=len(unit), eligible_people=len(np.unique(unit)),
                  prior_criticised_prompts=int(criticised.sum()),
                  prior_criticised_people=len(np.unique(unit[criticised])))
    return Selection(len(roster), np.asarray(current, dtype=int), unit,
                     np.asarray(context, dtype=int), np.asarray(gaps), events, dict(counts))


def occurrence(frame, selection, missing):
    if tuple(frame.columns) != FEELING_COLUMNS:
        raise ValueError("Wrong current-prompt feeling projection")
    values = np.column_stack([codes(frame[col], missing, 1, 6) for col in FEELING_COLUMNS])
    rows = values[selection.current]
    chosen = np.where(selection.context[:, None] == 1, rows[:, :5], rows[:, 5:])
    return np.where(np.any(chosen > 1, axis=1), 1.,
                    np.where(np.all(chosen == 1, axis=1), 0., np.nan))


def coefficients(selection, outcome, mask, multiplicities, verify=False):
    valid = np.isfinite(outcome)
    section = mask[valid]
    units = selection.units[valid]
    predictors = np.column_stack((selection.events[valid], selection.hours[valid],
                                  (selection.context[valid] == 1).astype(float)))
    if not np.any(section):
        return None, None
    within, logit, _ = common.arithmetic(verify)
    weights = multiplicities[units]
    try:
        adjusted, means, _ = within(predictors, units, weights)
        matrix = np.column_stack((np.ones(len(units)), adjusted, means))
        beta = logit(matrix[section], outcome[valid][section], weights[section])
    except InvalidFit:
        return None, None
    return float(beta[1]), float(beta[1 + len(EVENTS)])


def gap_description(selection, outcome):
    cuts = selection.summary()["gap_cuts_hours"]
    if len(cuts) != 2:
        return {"gap_cuts_hours": cuts, "thirds": []}
    groups = np.searchsorted(cuts, selection.hours, side="left")
    weights = np.ones(selection.people)
    results = []
    for j in range(3):
        mask = groups == j
        _, b2 = coefficients(selection, outcome, mask, weights)
        valid = mask & np.isfinite(outcome)
        results.append({"third": j + 1, "rows": int(valid.sum()),
                        "people": int(np.unique(selection.units[valid]).size), "b2": b2})
    return {"gap_cuts_hours": cuts, "thirds": results}


def stage_two_gate(b1, b2, b2_interval):
    """Use only a fully verified stage-one return to call this decision."""
    if b1 is None or b2 is None or b2_interval is None:
        return False
    lo, hi = b2_interval
    if not np.isfinite([b1, b2, lo, hi]).all() or hi < lo:
        raise ValueError("Invalid stage-one interval")
    return bool(b1 > 0 and lo > 0 and b2 >= .30 * b1)


def bind_registration(review, panel):
    """Check this physical member and every literal name before opening the source."""
    from .week6_diary_rows_v1 import reviewed_file
    from .batch_runtime import read
    member = panel["member"]
    book, layout, table = [read(reviewed_file(review[key])) for key in ("codebook", "source_layout", "rows_table")]
    if (member != "0057" or book["dataset_id"] != member
            or review["codebook"]["sha256"] != common.CODEBOOK_HASHES[member]):
        raise ValueError("NT1 stage one requires the large diary's reviewed codebook")
    pin = panel["source_pin"]
    files = [item for item in layout["files"] if (item["sha256"], item["bytes"]) == (pin["sha256"], pin["bytes"])]
    if len(files) != 1:
        raise ValueError("Source digest does not identify a unique table")
    required = set(EXPOSURE_COLUMNS + FEELING_COLUMNS)
    if not required <= ({v["name"] for v in book["features"]} & {v["name"] for v in files[0]["columns"]}):
        raise ValueError("An NT1 item is absent from the registered member")
    if (table["member"] != member or table["operator"] != "NT1-stage-1"
            or table["rows"] != [{"id":"NT1.d", "metric":"B2", "bar":0.10, "draws":2000},
                                  {"id":"NT1.e", "metric":"B2_by_gap_third", "draws":0}]
            or table["support"] != {"prior_criticised_prompts":300, "prior_criticised_people":150}):
        raise ValueError("Unsupported stage-one registration")
    return {"member": member, "source_sha256": pin["sha256"], "items": sorted(required),
            "table_sha256": review["rows_table"]["sha256"], "codebook_sha256": review["codebook"]["sha256"]}


def assemble(review, panel, source, output, verify, guard):
    from .week6_diary_rows_v1 import one_pass
    binding = bind_registration(review, panel)
    pin, missing = panel["source_pin"], panel["missing_tokens"]
    exposures = project_source(source, pin, EXPOSURE_COLUMNS, guard)
    selection = select_lags(exposures, missing, guard)
    summary = selection.summary()
    support_sha, saved = one_pass(output, "ROW_SUPPORT", binding, lambda: summary, verify)
    if saved != summary:
        raise ValueError("Fresh exposure-only support differs from its receipt")
    metadata = {"support_sha256": support_sha, **summary}
    prepared = common.Prepared(selection.people, metadata)
    if not summary["supported"]:
        return prepared
    feelings = project_source(source, pin, FEELING_COLUMNS, guard)
    if len(exposures) != len(feelings):
        raise ValueError("Source projections have different lengths")
    y = occurrence(feelings, selection, missing)
    n = common.denominator(selection.units, np.isfinite(y))
    metadata["missing_composite"] = int(np.count_nonzero(~np.isfinite(y)))
    common.metric(prepared, "B1", "Current criticism", n)
    common.metric(prepared, "B2", "Previous criticism", n, role="primary", bar=.10)
    prepared.specs["B2"]["row_id"] = "NT1.d"
    description_sha, _ = one_pass(output, "NT1_E_DESCRIPTION", binding,
                                  lambda: gap_description(selection, y), verify)
    metadata["description_sha256"] = description_sha
    prepared.panels["overall"] = (selection, y)
    return prepared


def evaluate(prepared, weights, guard, *, verify=False):
    guard()
    selection, y = prepared.panels["overall"]
    counts = common.multiplicities(selection.people, weights)
    b1, b2 = coefficients(selection, y, np.ones(len(y), dtype=bool), counts, verify)
    values = {"B1": b1, "B2": b2}
    common.record_point_dispositions(prepared, values, weights)
    return values
