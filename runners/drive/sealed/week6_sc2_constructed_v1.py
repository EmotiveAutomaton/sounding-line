"""Construct Parquet files for the SC2 sealed-image known answer."""
import csv
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory

from runners.drive.cards.week6_sealed_support_v1 import write_tables
from runners.drive.sealed.week6_sc2_job_v1 import compare
from runners.drive.sealed.week6_sc2_source_v1 import COLUMNS, PINS


def make_files(root, conversations=26, *, identical=False):
    import numpy as np
    import pyarrow as pa
    import pyarrow.parquet as pq

    rng = np.random.default_rng(200044)
    rows = {name: [] for name in COLUMNS}
    for i in range(conversations):
        conversation = "fixture-" + str(i)
        a, b = "repeat-speaker", "invented-" + str(i)
        end = float(rng.uniform(600, 2400))
        fraction = float(rng.uniform(.12, .88))
        rows["clock"].append((conversation, end))
        for respondent, partner in ((a, b), (b, a)):
            funny = float(rng.normal())
            rows["survey"].append((conversation, respondent, partner, funny, 2.*funny+4., 2.*funny+4. if identical else -3.*funny+12.))
        rows["speech"].extend([(conversation, 0, a, 0., 1.), (conversation, 1, a, 1., end*fraction),
                               (conversation, 2, b, end*fraction, end-1.), (conversation, 3, b, end-1., end)])
    pins = {}
    for name, records in rows.items():
        file = root / PINS[name][0]
        file.parent.mkdir(parents=True, exist_ok=True)
        fields = dict(zip(COLUMNS[name], zip(*records), strict=True))
        pq.write_table(pa.table(fields), file, row_group_size=7)
        pins[name] = (PINS[name][0], file.stat().st_size, hashlib.sha256(file.read_bytes()).hexdigest())
    return pins


def known_answer():
    import resource
    import signal

    resource.setrlimit(resource.RLIMIT_CPU, (600, 600))
    signal.alarm(1100)
    with TemporaryDirectory(prefix="sc2-constructed-") as temp:
        root = Path(temp)
        out = root / "aggregate"
        out.mkdir()
        compare(root, out, pins=make_files(root))
        with (out / "estimates.csv").open() as stream:
            rows = sorted(csv.DictReader(stream), key=lambda r: int(r["metric"]))
        if len(rows) != 3:
            return 14
        for row, expected in zip(rows, (1., -1., 2.), strict=True):
            if int(row["n"]) != 27 or int(row["conversations"]) != 26 or int(row["valid_draws"]) != 2000:
                return 14
            if any(abs(float(row[key]) - expected) > 1.e-8 for key in ("estimate", "lower", "upper")):
                return 14
        write_tables(Path("/out"), {"known_answer": [dict(n=27, conversations=26, metrics=3,
                                                          paired_draws=2000, agreed=1, constructed=1)]})
    return 0
