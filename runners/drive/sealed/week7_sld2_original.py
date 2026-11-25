"""SLD2 original-survey adapter. All frames, keys and membership sets stay sealed.

DESIGN CHECK: a constructed loss only qualifies strictly between interview months.
No change at wave three recovers inside the registered equivalence margin. Changed
membership and differing midpoint labels must remain visible in the two readings.
"""
from collections import Counter
from hashlib import file_digest
from pathlib import Path

import numpy as np
import pandas as pd

from runners.drive.cards.week6_sealed_support_v1 import ReadBudget, SealedFailure, write_tables
from runners.drive.sealed.week7_sld2 import projected, trajectory


PURPOSE = [
    ("A1SF1C", "A1SF1G", "A1SF1J"),
    ("B1SE1OO", "B1SE1E", "B1SE1QQ"),
    ("C1SE1OO", "C1SE1E", "C1SE1QQ"),
]
ITEMS = ("aim", "future", "done")
DEATH_FIRST, DIVORCE_FIRST = "B1PB23", "B1PB25"
DEATH_RECENT, DIVORCE_RECENT = "B1PB29", "B1PB28"


def field_list(wave):
    names = ["M2ID", "M2FAMNUM", *PURPOSE[wave-1]]
    if wave == 1:
        names.extend(["A1PI_MO", "A1PI_YR"])
    if wave == 2:
        names.extend(["B1PIDATE_MO", "B1PIDATE_YR", "B1PB19", "B1PB22"])
        for kind in (DEATH_FIRST, DIVORCE_FIRST, DEATH_RECENT, DIVORCE_RECENT):
            names.extend([kind+"M", kind+"Y"])
    return names


def load_sources(root, manifest):
    import pyreadstat
    if len(manifest) != 3:
        raise SealedFailure(13, "Three pinned source files required")
    budget = ReadBudget(root)
    frames = []
    for wave, (name, length, digest) in enumerate(manifest, 1):
        if Path(name).name != name:
            raise SealedFailure(13, "Invalid source basename")
        path = budget.reserve(Path(root)/name, passes=2)
        with path.open("rb") as stream:
            if path.stat().st_size != length or file_digest(stream,"sha256").hexdigest() != digest:
                raise SealedFailure(13, "Source pin mismatch")
        columns = field_list(wave)
        frame, _ = pyreadstat.read_sav(str(path), usecols=columns, user_missing=False, apply_value_formats=False)
        if set(frame) != set(columns):
            raise SealedFailure(13, "Incomplete source binding")
        if frame.M2ID.isna().any() or frame.M2ID.duplicated().any():
            raise SealedFailure(12, "Nonunique person key")
        frames.append(frame.set_index("M2ID"))
    return frames


def month_index(year, month):
    valid = year.between(1900, 2100) & month.between(1, 12) & year.mod(1).eq(0) & month.mod(1).eq(0)
    return (year*12 + month).where(valid)


def loss_flags(first, second):
    lo = month_index(first.A1PI_YR, first.A1PI_MO).reindex(second.index)
    hi = month_index(second.B1PIDATE_YR, second.B1PIDATE_MO)
    def inside(prefix):
        date = month_index(second[prefix+"Y"], second[prefix+"M"])
        return date.gt(lo) & date.lt(hi)
    death = (second.B1PB22.eq(1) & inside(DEATH_FIRST)) | (second.B1PB19.eq(4) & inside(DEATH_RECENT))
    divorce = (second.B1PB22.eq(2) & inside(DIVORCE_FIRST)) | (second.B1PB19.eq(3) & inside(DIVORCE_RECENT))
    return death, divorce


def scored(frames, remove_neutral):
    result = []
    for wave, source in enumerate(frames,1):
        values = source[list(PURPOSE[wave-1])].copy()
        values.columns = ITEMS
        values = values.where(values.isin(range(1,8)))
        if wave == 1 or remove_neutral:
            values = values.mask(values.eq(4))
        values["aim"] = 8 - values["aim"]
        values["person"] = source.index
        values["family"] = source.M2FAMNUM
        result.append(values.reset_index(drop=True))
    return result


def analyze(frames, draws=2000):
    death, divorce = loss_flags(*frames[:2])
    emitted = []
    catalogue = []
    # Both pooled readings precede descriptions so suppression prioritizes the primary.
    for group, flag in enumerate([death | divorce, death, divorce],1):
        for reading, remove_neutral in enumerate([False, True],1):
            waves = scored(frames,remove_neutral)
            waves[1]["role_loss"] = flag.reindex(waves[1].person).to_numpy(dtype=int)
            cohort = projected(waves,ITEMS)
            members = frozenset(cohort.index)
            if len(members)<11:
                continue
            for frame in frames:
                families = frame.loc[cohort.index, "M2FAMNUM"]
                conflicts = families.notna() & cohort.family.notna() & families.ne(cohort.family)
                if conflicts.any():
                    raise SealedFailure(12, "Conflicting family link")
            if cohort.family.isna().any():
                continue
            candidates = [*emitted, members]
            cells = Counter(tuple(p in roster for roster in candidates) for p in set.union(set(),*candidates))
            if min(cells.values())<11:
                continue
            rows = trajectory(waves,ITEMS,draws=draws)
            if rows:
                emitted.append(members)
                catalogue.extend(dict(group=group,reading=reading,**row) for row in rows)
    if not catalogue:
        raise SealedFailure(12,"No disclosable cohort")
    return catalogue


def run_original(root, out, manifest):
    frames = load_sources(root,manifest)
    result = analyze(frames)
    # A fresh projection and fresh whole-family bootstrap must reproduce every output row.
    if result != analyze(load_sources(root,manifest)):
        raise SealedFailure(14,"Independent reread and replay differed")
    write_tables(out, {"purpose":result})

