"""Original student-diary source projection for the seven LB1 study rows.

DESIGN CHECK (LESSONS 2–5). The complete person roster precedes all masks.
A missing rating may remove one pair but never create an earlier neighbour.
No ordering is inferred from file order, blank prompt numbers or tied times.
Source integrity and complete-case denominators apply under every sign.
"""
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .es_source_v1 import sha256


FIVE_POINT = ("curious", "content", "excited", "efficient", "inventive", "dominant",
              "proud", "purposeful", "angry", "afraid")
THREE_POINT = ("intellect", "positivity", "sociality", "mating")
BINARY = ("bored_schoolwork", "argument_family", "argument_friend")
CLOCK = ("day", "hour", "minute")
COLUMNS = ("id", *CLOCK, *FIVE_POINT, *THREE_POINT, *BINARY)
SOURCE_SEED = 202611190060
SOURCE_SHA256 = "14cc03a8b6886d20b68ee2bff8bdc8aa6baaaccfda307c883a24f121c2f6ca3c"
CODEBOOK_SHA256 = "f727d31c958524abad63a5ec01dbab79bdb6cb139ffe7948ce339f76a6ddd175"


@dataclass
class Source:
    people: int
    units: np.ndarray
    values: dict
    earlier: np.ndarray
    later: np.ndarray
    counts: dict


def ordered_pairs(units, days, hours, minutes):
    """Return only unambiguous immediate neighbours in the same reported day."""
    if not (len(units) == len(days) == len(hours) == len(minutes)):
        raise ValueError("Clock vectors differ in length")
    visits = pd.DataFrame(dict(unit=units, day=days, time=hours*60+minutes,
                               ordinal=np.arange(len(units))))
    unknown_day = set(visits.loc[visits.day.isna(), "unit"])
    dated = visits.loc[~visits.unit.isin(unknown_day)]
    earlier, later = [], []
    counts = dict(people_excluded_unknown_day=len(unknown_day),
                  rows_excluded_unknown_day=len(visits)-len(dated), days_with_missing_clock=0,
                  rows_on_missing_clock_days=0, first_rows_of_orderable_days=0,
                  transitions_touching_ties=0)
    for _, group in dated.groupby(["unit","day"], sort=False):
        if group.time.isna().any():
            counts["days_with_missing_clock"] += 1
            counts["rows_on_missing_clock_days"] += len(group)
            continue
        ordered = group.sort_values("time",kind="stable")
        ambiguous = ordered.time.duplicated(keep=False).to_numpy()
        ordinals = ordered.ordinal.to_numpy()
        keep = ~(ambiguous[1:] | ambiguous[:-1])
        counts["first_rows_of_orderable_days"] += 1
        counts["transitions_touching_ties"] += int((~keep).sum())
        earlier.extend(ordinals[:-1][keep])
        later.extend(ordinals[1:][keep])
    counts["adjacent_same_day_pairs"] = len(earlier)
    assert (len(visits) == counts["rows_excluded_unknown_day"] + counts["rows_on_missing_clock_days"]
            + counts["first_rows_of_orderable_days"] + counts["transitions_touching_ties"] + len(earlier))
    return np.asarray(earlier,dtype=int), np.asarray(later,dtype=int), counts


def numeric(series, missing, low, high):
    present = ~series.isin(missing)
    values = pd.to_numeric(series.where(present), errors="coerce").to_numpy(dtype=float)
    valid = values[present.to_numpy()]
    if (not np.isfinite(valid).all() or np.any(valid != np.floor(valid))
            or np.any(valid < low) or np.any(valid > high)):
        raise ValueError("Unexpected documented value in "+str(series.name))
    return values


def prepare_frame(frame, missing):
    if set(COLUMNS) - set(frame.columns) or not missing:
        raise ValueError("Missing source fields or unknown missing-value convention")
    has_id = ~frame["id"].isin(missing)
    selected = frame.loc[has_id]
    roster, units = np.unique(selected["id"].to_numpy(dtype=str), return_inverse=True)
    if len(roster) < 2:
        raise ValueError("At least two source people required")
    values = {}
    for fields, low, high in ((FIVE_POINT,1,5), (THREE_POINT,1,3), (BINARY,0,1)):
        for field in fields:
            values[field] = numeric(selected[field],missing,low,high)
    days = numeric(selected["day"],missing,0,np.inf)
    hours = numeric(selected["hour"],missing,0,23)
    minutes = numeric(selected["minute"],missing,0,59)
    earlier, later, counts = ordered_pairs(units,days,hours,minutes)
    family, friend = values["argument_family"], values["argument_friend"]
    # One positive answer establishes an event even when the other is missing.
    values["argument"] = np.where((family == 1) | (friend == 1), 1.,
                                  np.where((family == 0) & (friend == 0), 0., np.nan))
    values["low_purpose"] = 6.-values["purposeful"]
    counts.update(source_rows=len(frame), rows_with_identity=len(selected),
                  missing_identity=int((~has_id).sum()), source_people=len(roster))
    return Source(len(roster),units,values,earlier,later,counts)


def load(path, source_pin, missing, guard):
    if not callable(guard) or not missing or not all(isinstance(token,str) for token in missing):
        raise ValueError("A native source guard and reviewed missing tokens are required")
    path = Path(path)
    def authenticate():
        guard()
        if path.stat().st_size != source_pin["bytes"] or sha256(path,guard) != source_pin["sha256"]:
            raise ValueError("Student diary source pin differs")
    authenticate()
    with pd.read_csv(path,sep="\t",usecols=list(COLUMNS),dtype=str,keep_default_na=False,
                     na_filter=False,chunksize=12000) as reader:
        parts = []
        for frame in reader:
            guard()
            parts.append(frame)
    authenticate()
    if not parts:
        raise ValueError("Empty student diary source")
    return prepare_frame(pd.concat(parts,ignore_index=True),missing)
