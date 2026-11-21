"""Exercise the production SC2 reader on tiny Parquet copies of invented tables."""
import hashlib
import tempfile
import unittest
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from runners.drive.sealed import week6_sc2_reader_v1 as reader
from runners.drive.sealed import week6_sc2_source_v1 as source


def fixture(root, *, omit=None, remove_column=None, processed=False):
    base = root / "processed" if processed else root
    rows = {
        "survey": [("q", "writer", "actor", 2, 3, 4), ("q", "actor", "writer", 8, 7, 6)],
        "clock": [("q", 120)],
        "speech": [("q", 0, "writer", 0, 8), ("q", 1, "actor", 20, 30),
                   ("q", 2, "writer", 40, 60), ("q", 3, "actor", 110, 120)],
    }
    pins = {}
    for key, records in rows.items():
        path = base / source.PINS[key][0]
        path.parent.mkdir(parents=True, exist_ok=True)
        cols = dict(zip(source.COLUMNS[key], zip(*records), strict=True))
        if remove_column in cols:
            del cols[remove_column]
        cols["unused_synthetic_column"] = ["unselected"] * len(records)
        pq.write_table(pa.table(dict(reversed(cols.items()))), path, row_group_size=1)
        payload = path.read_bytes()
        pins[key] = (source.PINS[key][0], len(payload), hashlib.sha256(payload).hexdigest())
        if key == omit:
            path.unlink()
    return pins


class TestSealedReader(unittest.TestCase):
    def test_nested_layout_batching_and_projection(self):
        with tempfile.TemporaryDirectory() as local:
            root = Path(local)
            pins = fixture(root, processed=True)
            one, counts = reader.load_dyads(root, pins=pins, batch_size=1)
            self.assertEqual((one, counts), reader.load_dyads(root, pins=pins, batch_size=20))
            self.assertEqual((counts["retained_people"], counts["retained_conversations"]), (2, 1))
            by_target = {row[0]: row for row in one[0][1]}
            self.assertEqual(by_target["writer"][1:5], ("actor", 8., 7., 6.))
            self.assertAlmostEqual(by_target["writer"][-1], 2 / 3)

    def test_single_layout_required(self):
        with tempfile.TemporaryDirectory() as local:
            root = Path(local)
            fixture(root)
            pins = fixture(root, processed=True)
            with self.assertRaises(reader.Unavailable) as error:
                reader.load_dyads(root, pins=pins)
            self.assertEqual(error.exception.args, (21,))

    def test_missing_clock_refuses(self):
        with tempfile.TemporaryDirectory() as local:
            root = Path(local)
            pins = fixture(root, omit="clock")
            with self.assertRaises(reader.Unavailable) as error:
                reader.load_dyads(root, pins=pins)
            self.assertEqual(error.exception.args, (21,))

    def test_changed_bytes_and_over_budget_refuse(self):
        with tempfile.TemporaryDirectory() as local:
            root = Path(local)
            pins = fixture(root)
            path, size, digest = pins["clock"]
            for broken, code in (((path, size, "f" * 64), 23),
                                 ((path, 2_000_000_001, digest), 22)):
                with self.subTest(code=code), self.assertRaises(reader.Unavailable) as error:
                    reader.load_dyads(root, pins=dict(pins, clock=broken))
                self.assertEqual(error.exception.args, (code,))

    def test_missing_field_refuses(self):
        with tempfile.TemporaryDirectory() as local:
            root = Path(local)
            pins = fixture(root, remove_column="speaker")
            with self.assertRaises(reader.Unavailable) as error:
                reader.load_dyads(root, pins=pins)
            self.assertEqual(error.exception.args, (24,))

    def test_no_transcript_text_projected(self):
        class Probe:
            def iter_batches(self, **options):
                self.options = options
                return ()
        p = Probe()
        self.assertEqual(list(reader._projected_rows(p, source.COLUMNS["speech"], 3)), [])
        self.assertEqual(p.options, dict(batch_size=3, columns=list(source.COLUMNS["speech"]), use_threads=False))
        self.assertNotIn("utterance", p.options["columns"])


if __name__ == "__main__":
    unittest.main()
