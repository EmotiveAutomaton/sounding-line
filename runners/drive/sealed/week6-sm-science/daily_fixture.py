"""Constructed joined MIDUS tables with exact affect, lag and family checks."""
from hashlib import sha256
from math import log
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat

import mi_source_contract_v1 as contract


# All eight answers belong to the same invented respondent. Different first
# and final days make the two person-level exposure means independently estimable.
HISTORIES = (
    "00101011", "11001010", "01100110", "10100101", "11100010", "01011001",
    "00110100", "11001101", "10111000", "01010010", "11100101", "10101110",
)
COPIES = 12


def known_daily_point():
    counts = np.array([[int(x) for x in s] for s in HISTORIES], dtype=float)
    current, prior = counts[:, 1:], counts[:, :-1]
    within_sd = [float(np.sqrt(np.mean((x - x.mean(axis=1)[:, None]) ** 2))) for x in (current, prior)]
    # At each exposure combination, one, two or three of four response types
    # experience negative affect. Hence each stressor adds exactly log(3) on
    # the raw log-odds scale. The trait has no main or product effect.
    return [log(3)*sd for sd in within_sd] + [0.0]*5


def records():
    fields = contract.fields("M2")
    diary, survey = [], []
    for pattern, history in enumerate(HISTORIES):
        for response in range(4):
            for _ in range(COPIES):
                person = len(survey) + 1
                survey.append({"M2ID": person, "M2FAMNUM": (person-1)//2 + 1,
                               fields["traits"]["neuroticism"]: 1.25 + .5*((2*pattern+1)%5),
                               fields["traits"]["agreeableness"]: 1.5 + .5*((pattern+2)%5),
                               fields["traits"]["extraversion"]: 2 + pattern % 2})
                for index, bit in enumerate(history):
                    day = index + 1
                    now = int(bit)
                    prior = int(history[index-1]) if index else 0
                    row = {"M2ID": person, fields["study_day"]: day, fields["weekday"]: 1+index%7}
                    for k, stress in enumerate(fields["stressors"]):
                        observed = bool(now) and (k == 0 or (pattern+day+k)%5 == 0)
                        row[stress["occurrence"]] = 1 if observed else 2
                        row[stress["severity"]] = (pattern+day+k)%4 if observed else 9
                        row[stress["control"]] = (pattern+2*day+k)%4 if observed else 9
                        for j, col in enumerate(stress["risks"].values()):
                            row[col] = (j*day+pattern+k+j)%4 if observed else 9
                    row["B2DF1WC6"] = 1 + (pattern+index)%2 if now else 9
                    bad = (response+index)%4 < 1 + now + prior
                    for j, col in enumerate(fields["negative"]):
                        row[col] = (1 + (j+pattern+response)%4 if bad and
                                    (j == 0 or (pattern+index+j)%3 != 0) else 0)
                    good = day%2 == 0
                    level, lift = 1 + pattern%2, (pattern//2)%2
                    row.update({col: level + int(good)*lift for col in fields["positive"]})
                    row.update({col: 1 if good else 2 for col in fields["positive_events"]})
                    diary.append(row)
    return {"survey": survey, "diary": diary}


def construct(directory, editions):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    sources = {}
    for role, rows in records().items():
        filename = editions["M2"][role]["filename"]
        if Path(filename).name != filename:
            raise ValueError("Expected a source basename")
        path = directory/filename
        pyreadstat.write_sav(pd.DataFrame.from_records(rows).astype(float), str(path))
        data = path.read_bytes()
        sources[role] = {"filename": filename, "bytes": len(data), "sha256": sha256(data).hexdigest()}
    return {"M2": sources}


def check_known(tables):
    from joined_fixture import check_known as check_original
    check_original(tables)
    n = len(HISTORIES)*4*COPIES
    exposure, = tables.get("daily_exposure", [])
    if exposure["n"] != n or exposure["support_met"] != 1:
        raise ValueError("Constructed complete daily roster differs")
    expected_pairs = 4 * COPIES * sum(h[:-1].count("1") for h in HISTORIES)
    if exposure["previous_stressor_pairs"] != expected_pairs:
        raise ValueError("Constructed prior-stressor support differs")
    series = sorted(tables.get("daily_estimates", []), key=lambda r:r["parameter"])
    if [r["parameter"] for r in series] != list(range(1, 8)):
        raise ValueError("Known daily fixture lacks a complete 2,000-draw coefficient bank")
    if any(r["n"] != n or r["resampling"] != 2 or r["descriptive"] for r in series):
        raise ValueError("Constructed contributing people or family clusters differ")
    if not np.allclose([r["estimate"] for r in series], known_daily_point(), rtol=1e-7, atol=1e-8):
        raise ValueError("Known stressor slopes, trait terms or their ratios differ")
    return n
