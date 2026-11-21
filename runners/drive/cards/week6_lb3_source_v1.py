"""Original parent-diary source projection for lattice rows 21 through 25.

DESIGN CHECK (LESSONS 2–5). Build the whole-parent roster before row masks.
A missing component cannot imply an absent event or zero time. Verify the
original time-series bytes before and after the read. Retain only aggregate
support in published outputs.
"""
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .es_source_v1 import sha256
from .week6_lb1_source_v1 import numeric


STRESSORS = tuple("stressor_" + key for key in (
    "argument", "friend_relative", "health", "work", "household", "leisure", "financial", "other"))
NEED_ITEMS = ("told_what_to_do", "against_own_will", "pressure", "excluded_ostracized",
              "failure", "did_stupid", "struggled", "unappreciated")
PARENT_FEELINGS = tuple("parent_" + key for key in (
    "happy", "afraid", "sad", "balanced", "exhausted", "cheerful", "worried", "lively", "angry", "relaxed"))
CHILD_DISTRESS = ("child_sad", "child_afraid", "child_worried")
PARENTING = ("parenting_talked_worries", "parenting_fun", "parenting_disagreements")
RATINGS = (*NEED_ITEMS, *PARENT_FEELINGS, *CHILD_DISTRESS, *PARENTING)
TIME = ("time_with_child_hours", "time_with_child_minutes")
COLUMNS = ("id", "day", *STRESSORS, *RATINGS, *TIME)
SOURCE_SEED = 202611190072
SOURCE_SHA256 = "767cc1edcdfdf48b799499f07f02a1d3e3978dc10148c20f530e3b126afc284e"
SOURCE_BYTES = 2793431
CODEBOOK_SHA256 = "0086a6bb082826acf4e5b14e7c20775059c2edb281a51854a0544cc259339dbb"


@dataclass
class ParentDiary:
    people: int
    units: np.ndarray
    values: dict
    counts: dict


def duration_minutes(hours, minutes, missing):
    components = []
    for series in (hours, minutes):
        absent = series.isin(missing)
        numbers = pd.to_numeric(series.where(~absent), errors="coerce").to_numpy(dtype=float)
        if not np.isfinite(numbers[~absent.to_numpy()]).all():
            raise ValueError("Undocumented time code in " + str(series.name))
        components.append(numbers)
    h, m = components
    total = 60 * h + m
    present = np.isfinite(total)
    # Both entries are stated in physical units. Count out-of-range responses separately.
    invalid = present & ((h < 0) | (m < 0) | (total > 24 * 60))
    total[invalid] = np.nan
    return total, int((~present).sum()), int(invalid.sum())


def prepare_frame(frame, missing):
    if len(set(frame.columns)) != len(frame.columns) or set(COLUMNS) - set(frame.columns) or not missing:
        raise ValueError("Incomplete parent-diary source contract")
    has_id = ~frame["id"].isin(missing)
    identified = frame.loc[has_id]
    people, units = np.unique(identified["id"].to_numpy(dtype=str), return_inverse=True)
    if len(people) < 2:
        raise ValueError("At least two source parents are required")
    day = numeric(identified["day"], missing, 0, np.inf)
    dated = np.isfinite(day)
    duplicated = pd.DataFrame({"person": units, "day": day}).duplicated(keep=False).to_numpy() & dated
    use = dated & ~duplicated
    selected = identified.loc[use]
    values = {name: numeric(selected[name], missing, 0, 1) for name in STRESSORS}
    values.update({name: numeric(selected[name], missing, 1, 7) for name in RATINGS})
    values["time_minutes"], missing_time, invalid_time = duration_minutes(
        selected[TIME[0]], selected[TIME[1]], missing)
    values["blocked"] = (values["told_what_to_do"] + values["against_own_will"]) / 2
    health, money = values["stressor_health"], values["stressor_financial"]
    values["health_or_financial"] = np.where((health == 1) | (money == 1), 1.,
                                             np.where((health == 0) & (money == 0), 0., np.nan))
    values["child_distress"] = np.mean([values[k] for k in CHILD_DISTRESS], axis=0)
    counts = dict(source_rows=len(frame), source_people=len(people), missing_identity=int((~has_id).sum()),
                  missing_day=int((~dated).sum()), duplicate_parent_day_rows=int(duplicated.sum()),
                  eligible_parent_days=int(use.sum()), eligible_parents=len(np.unique(units[use])),
                  incomplete_time_components=missing_time, invalid_time_duration=invalid_time)
    assert len(frame) == sum(counts[k] for k in ("missing_identity", "missing_day",
                                                "duplicate_parent_day_rows", "eligible_parent_days"))
    return ParentDiary(len(people), units[use], values, counts)


def load(path, source_pin, missing, guard):
    path = Path(path)
    if not callable(guard) or not missing or not all(isinstance(t,str) for t in missing):
        raise ValueError("Missing parent-diary admission")
    def authenticate():
        guard()
        if path.stat().st_size != source_pin["bytes"] or sha256(path,guard) != source_pin["sha256"]:
            raise ValueError("Parent-diary source pin differs")
    authenticate()
    parts = []
    with pd.read_csv(path, sep="\t", usecols=list(COLUMNS), dtype=str, keep_default_na=False,
                     na_filter=False, chunksize=12000) as chunks:
        for frame in chunks:
            guard()
            parts.append(frame)
    authenticate()
    if not parts:
        raise ValueError("Empty parent diary")
    return prepare_frame(pd.concat(parts, ignore_index=True), missing)
