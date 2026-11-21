"""Frozen projections for four November diary cohorts. See LB456_DIARIES_20261120.md."""
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .es_source_v1 import sha256
from .week6_lb1_source_v1 import numeric


FEAR = ("afraid", "scared", "frightened", "nervous", "jittery", "shaky")
ANGER = ("angry", "hostile", "irritable")
SCORN = ("scornful", "disgusted", "loathing")


@dataclass(frozen=True)
class Member:
    card: str
    rows: tuple
    ratings: tuple
    low: int
    high: int
    size: int
    digest: str
    codebook: str
    seed: int

    @property
    def pin(self):
        return {"bytes": self.size, "sha256": self.digest}

    @property
    def columns(self):
        return ("id", *self.ratings)


MEMBERS = {
    "0063": Member("LB6", ("32", "33"),
                   ("inspired", "good_at_this", "appreciated", "chose_doing", "doubt", "cheerful"), 1, 7,
                   782643, "45e3d3379fb9f8d959918120786ca7e965ba9fa0a3613cf9cebbc4922041fcfd",
                   "d4d238bad953d920c3dc713c3b430970addbae06bbbf9261a101ee9cecad9586", 202611190063),
    "0064": Member("LB5", ("30", "31"),
                   (*FEAR, *ANGER, *SCORN, "distressed", "upset"), 1, 5,
                   2712663, "29f115f54e25f9de2f2447bc2f67ff6a63c5f79475aa822951041533296163d7",
                   "fa1695dbaf29722e55f3fb7023bc8694d9eca252bdfd531f185b8ab174ed4041", 202611190064),
    "0070": Member("LB4", ("26", "27", "28"),
                   ("silly", "expected", "important", "pleasant", "fearful", "sad"), 0, 100,
                   1518936, "a50365d98627d11cc706e489647b2a223822a23d82609109354daa4c63fd80aa",
                   "8878cf6f211026a5b096283eccca78b619f51b4aacfdce7f0797864402f6721f", 202611190070),
    "0076": Member("LB4", ("29",),
                   ("interaction_playful", "stressed", "interaction_pleasant", "interaction_meaningful", "interaction_frequency"), 1, 5,
                   6743927, "5923ffffa062b749dd1b0ec84b624d6c7c242b31627b07ed5b9a1efad98ae4e4",
                   "b611651862599e5ffa6d1720f422fb4f16bb511826b7d0d605222b2f9016fc6a", 202611190076),
}


def project(member, frame, missing):
    spec = MEMBERS[member]
    if not missing or set(spec.columns) - set(frame):
        raise ValueError("Incomplete diary input schema or missing-value dictionary")
    keep = ~frame.id.isin(missing)
    frame = frame.loc[keep]
    roster, units = np.unique(frame.id.to_numpy(dtype=str), return_inverse=True)
    if len(roster) < 2:
        raise ValueError("Insufficient diary roster")
    ratings = {}
    for name in spec.ratings:
        low, high = (0, 4) if name == "interaction_frequency" else (spec.low, spec.high)
        ratings[name] = numeric(frame[name], missing, low, high)
    counts = dict(source_rows=len(keep), source_people=len(roster), missing_identity=int((~keep).sum()),
                  missing_ratings={name: int(np.isnan(value).sum()) for name, value in ratings.items()})
    return units, len(roster), ratings, counts


def load(member, path, pin, missing, guard):
    path = Path(path)
    spec = MEMBERS[member]
    def authenticate():
        guard()
        if pin != spec.pin or path.stat().st_size != spec.size or sha256(path, guard) != spec.digest:
            raise ValueError("Diary source outside its reviewed binding")
    authenticate()
    parts = []
    with pd.read_csv(path, sep="\t", usecols=list(spec.columns), dtype=str, na_filter=False,
                     keep_default_na=False, chunksize=10000) as reader:
        for part in reader:
            guard()
            parts.append(part)
    authenticate()
    if not parts:
        raise ValueError("Empty diary source")
    return project(member, pd.concat(parts, ignore_index=True), missing)
