"""Constructed joined sources, including an analytically specified MI4 level and lift."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd
import pyreadstat

import aggregate_register_v1 as register
import mi_fixture_worlds_v1 as worlds
import mi_source_contract_v1 as source
from science_entry import run_joined
from week6_sealed_support_v1 import write_tables


def construct(folder, editions, wave="M2", repeats=12, extra_profile=False):
    # Repeat entire made-up profiles in blocks of 12 so that every registered
    # eligibility intersection and its complement are safe to count in this fixture.
    base_people = []
    for maker, seed in ((worlds.mi1_world, 303), (worlds.mi2_world, 304), (worlds.mi3_world, 305)):
        block, _ = maker(seed, n=12)
        base_people.extend(block[:4])
    if extra_profile:
        base_people.append(base_people[-1])
    people = []
    for person in base_people:
        for _ in range(repeats):
            other = deepcopy(person)
            other["id"] = len(people) + 1
            people.append(other)
    diary, survey = worlds.raw_dictionary_rows(people, wave)
    f = source.fields(wave)
    for row in survey:
        profile = (row["M2ID"] - 1) // repeats
        row[f["traits"]["extraversion"]] = float(2 + profile % 2)
    for row in diary:
        profile = (row["M2ID"] - 1) // repeats
        on = int(row[f["study_day"]] % 2 == 0)
        # Baseline level depends only on extraversion. Event lift is balanced
        # and independent of that trait; all five event-kind contrasts exist.
        level, lift = 1 + profile % 2, (profile // 2) % 2
        for column in f["positive"]:
            row[column] = level + on * lift
        for column in f["positive_events"]:
            row[column] = 1 if on else 2
    folder.mkdir()
    result = {}
    for role, records in (("diary", diary), ("survey", survey)):
        path = folder / editions[wave][role]["filename"]
        pyreadstat.write_sav(pd.DataFrame.from_records(records).astype(float), str(path))
        data = path.read_bytes()
        result[role] = {"filename": path.name, "bytes": len(data), "sha256": sha256(data).hexdigest()}
    return result, len(people)


def check_known(tables):
    branch = register.BRANCHES.index("MI4") + 1
    rows = sorted((r for r in tables["estimates"] if r["branch"] == branch),
                  key=lambda r: r["parameter"])
    if len(rows) < 3 or not np.allclose([r["estimate"] for r in rows[:3]], [1., 1., 0.],
                                          rtol=0., atol=1e-10):
        raise ValueError("constructed MI4 level/lift contrast differs")


def rehearsal_main(editions):
    # This executable creates its only inputs in its own temporary folder.
    # It cannot read a research mount and contains no participant records.
    with TemporaryDirectory(prefix="sm-made-up-") as tmp:
        here = Path(tmp)
        candidate, n = construct(here / "wave", editions)
        fixture_map = {"M2": candidate}
        (here / "aggregates").mkdir()
        result = run_joined({"M2": here / "wave"}, "M2", fixture_map, here / "aggregates")
        check_known(result)
        write_tables(Path("/out"), {"known_answer": [{"n": n, "matched": 1}]})
    return 0


def mounted_rehearsal(fixture_map):
    """The same read path as production, bound exclusively to the constructed file hashes."""
    from sealed_io_v1 import selected_columns
    from joined_source import resolve_wave
    if resolve_wave(Path("/data"), fixture_map) != "M2":
        raise ValueError("constructed mount does not match the frozen wave")
    with TemporaryDirectory(prefix="sm-rehearsal-") as tmp:
        result = run_joined({"M2": Path("/data")}, "M2", fixture_map, Path(tmp))
        check_known(result)
        branch = register.BRANCHES.index("MI4") + 1
        row = next(r for r in result["estimates"] if r["branch"] == branch)
        write_tables(Path("/out"), {"known_answer": [{"n": row["n"], "matched": 1}]})
    return 0
