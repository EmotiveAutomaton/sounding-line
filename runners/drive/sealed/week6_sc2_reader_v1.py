"""Read the three authenticated SC2 tables inside one read-only CANDOR mount.

DESIGN CHECK (LESSONS 2–5). The join requires the release's reciprocal survey,
recording clock and speaker timings. A missing table, changed digest, ambiguous
layout or missing field stops the projection. The timing scan excludes words.
This module returns in-memory dyads and source coverage to the sealed runner.
"""
from pathlib import Path

from runners.drive.sealed.week6_sc1_counts_v1 import Unavailable, source_layout
from runners.drive.sealed.week6_sc2_source_v1 import COLUMNS, PINS, pair_rows


def _projected_rows(reader, names, batch_size):
    for batch in reader.iter_batches(batch_size=batch_size, columns=list(names), use_threads=False):
        yield from zip(*(batch.column(name).to_pylist() for name in names), strict=True)


def load_dyads(root, *, pins=PINS, batch_size=8192):
    import pyarrow.parquet as pq

    if set(pins) != set(COLUMNS) or batch_size < 1:
        raise ValueError("Invalid source contract")
    root = Path(root)
    base = source_layout(root, pins)
    readers = {}
    try:
        for key, (relative, _, _) in pins.items():
            path = base / relative
            if not path.is_file():
                raise Unavailable(21)
            reader = pq.ParquetFile(path)
            readers[key] = reader
            fields = reader.schema_arrow.names
            if any(fields.count(name) != 1 for name in COLUMNS[key]):
                raise Unavailable(24)
        streams = [_projected_rows(readers[key], COLUMNS[key], batch_size)
                   for key in ("survey", "clock", "speech")]
        return pair_rows(*streams)
    finally:
        for reader in readers.values():
            reader.close()
