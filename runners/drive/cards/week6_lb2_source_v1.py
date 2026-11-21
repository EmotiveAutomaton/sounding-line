"""Interaction prompts in the three Mostajabi and Wright diary cohorts.

DESIGN CHECK (LESSONS 3–5). Make the person roster before applying masks.
Preserve genuine zeroes and the named feeling form for each member. An
unrecognised scale or changed source fails closed. Neither case supplies a
replacement outcome. A translation of the dominance scale preserves its sign.
"""
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .es_source_v1 import sha256
from .week6_lb1_source_v1 import numeric


@dataclass(frozen=True)
class Member:
    row: str
    seed: int
    size: int
    digest: str
    codebook: str
    suffix: str

    @property
    def pin(self):
        return {"bytes": self.size, "sha256": self.digest}

    @property
    def ratings(self):
        return tuple(word + self.suffix for word in ("happy", "angry", "nervous"))

    @property
    def columns(self):
        return ("id", "interaction", "dom_sub_you", *self.ratings)


MEMBERS = {
    "0042": Member("18", 202611190042, 3989396,
                   "9e33cfcd229d1c631f1b62d15a05dd4c5d5941ce118d7ae029e27ba74906f40b",
                   "1b834a87058f5486bb2cbed033dfdea02ab316cca73d7d37c1f0df1760bc10cc", "_interaction"),
    "0043": Member("19", 202611190043, 2646065,
                   "bb14a9f74aa98389c969f4b33b326ab9bd7876ec5b74ac687a1c8734e24a1d34",
                   "3fa7ae51fc08b482e0a0a6ac3d5f9a43edc77d87de78072c0268eb05c03bc5d5", "_interaction"),
    "0044": Member("20", 202611190044, 842212,
                   "1bf449b81c12056f9af9e7f279dccb686a22d4d26f62361bb0f81fa9f214b560",
                   "939923ecb839df9b69d02a7d15e181614b7a0e673c18713f565e63eef8be8498", ""),
}


@dataclass
class Source:
    people: int
    units: np.ndarray
    x: np.ndarray
    y: np.ndarray
    counts: dict


def prepare_frame(member, frame, missing):
    spec = MEMBERS[member]
    if not missing or set(spec.columns) - set(frame.columns):
        raise ValueError("Unknown missing convention or missing cohort fields")
    identified = ~frame.id.isin(missing)
    rows = frame.loc[identified]
    people, units = np.unique(rows.id.to_numpy(dtype=str), return_inverse=True)
    if len(people) < 2:
        raise ValueError("At least two source people are required")
    interaction = numeric(rows.interaction, missing, 0, 1)
    # The authors document a 101-point bipolar scale. All dictionaries agree
    # on the upper endpoint. Member 0042's secondary low label omits the minus
    # fifty given by its coding field and the original methods.
    dominance = numeric(rows.dom_sub_you, missing, -50, 50)
    happy, angry, nervous = (numeric(rows[field], missing, 0, 100) for field in spec.ratings)
    x = np.column_stack((100.0 - happy, dominance))
    y = np.column_stack((angry, nervous))
    observed = np.isfinite(x).all(axis=1) & np.isfinite(y).all(axis=1)
    keep = (interaction == 1) & observed
    counts = dict(source_rows=len(frame), source_people=len(people),
                  missing_identity=int((~identified).sum()), rows_with_identity=len(rows),
                  missing_interaction=int(np.isnan(interaction).sum()),
                  no_interaction=int((interaction == 0).sum()),
                  interaction_rows=int((interaction == 1).sum()),
                  people_reporting_interaction=int(np.unique(units[interaction == 1]).size),
                  incomplete_interactions=int(((interaction == 1) & ~observed).sum()),
                  people=int(np.unique(units[keep]).size), rows=int(keep.sum()),
                  dominance_range=[-50, 50], rating_fields=list(spec.ratings))
    return Source(len(people), units[keep], x[keep], y[keep], counts)


def load(member, path, pin, missing, guard):
    spec = MEMBERS[member]
    if pin != spec.pin or missing != ["", "NA"] or not callable(guard):
        raise ValueError("Unreviewed interaction-diary source or missing tokens")
    path = Path(path)

    def authenticate():
        guard()
        if path.stat().st_size != spec.size or sha256(path, guard) != spec.digest:
            raise ValueError("Interaction-diary source has changed")

    authenticate()
    parts = []
    with pd.read_csv(path, sep="\t", usecols=list(spec.columns), dtype=str,
                     keep_default_na=False, na_filter=False, chunksize=12000) as reader:
        for chunk in reader:
            guard()
            parts.append(chunk)
    authenticate()
    if not parts:
        raise ValueError("Empty interaction diary")
    return prepare_frame(member, pd.concat(parts, ignore_index=True), missing)
