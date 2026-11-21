"""Known denominators, partial layouts and suppression for the SC2 status return."""
import csv
import hashlib
import tempfile
import unittest
from pathlib import Path

import pyarrow.parquet as pq

from runners.drive.sealed.week6_sc2_constructed_v1 import make_files
from runners.drive.sealed.week6_sc2_job_v1 import compare
from runners.drive.sealed.week6_sc2_source_v1 import COLUMNS
from runners.drive.sealed.week6_sc2_status_v1 import field_status


class TestStatus(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.pins = make_files(self.root)
        self.out = self.root/"out"
        self.out.mkdir()

    def omit(self, role, column):
        relative = self.pins[role][0]
        path = self.root/relative
        table = pq.read_table(path).drop_columns([column])
        pq.write_table(table,path)
        self.pins[role] = (relative, path.stat().st_size, hashlib.sha256(path.read_bytes()).hexdigest())

    def test_fixed_field_codes_true_person_counts(self):
        rows, complete = field_status(self.root, self.pins)
        self.assertTrue(complete)
        self.assertEqual(len(rows), sum(map(len, COLUMNS.values())))
        self.assertTrue(all(r["n"] == 27 and r["present"] == 1 for r in rows))

    def test_missing_rating_returns_field_status_without_model(self):
        self.omit("survey","i_like_you")
        compare(self.root,self.out,pins=self.pins)
        self.assertEqual([f.name for f in self.out.iterdir()], ["field_status.csv"])
        with (self.out/"field_status.csv").open() as stream:
            rows = list(csv.DictReader(stream))
        missing, = [r for r in rows if r["present"]=="0"]
        self.assertEqual(missing,dict(n="27",table_role="1",field="5",present="0"))

    def test_missing_survey_cannot_supply_clock_people(self):
        (self.root/self.pins["survey"][0]).unlink()
        compare(self.root,self.out,pins=self.pins)
        with (self.out/"field_status.csv").open() as stream:
            rows = list(csv.DictReader(stream))
        self.assertTrue(rows and all(r["table_role"]=="3" and r["n"]=="27" for r in rows))

    def test_absent_clock_join_key_does_not_borrow_survey_count(self):
        self.omit("clock","conversation_id")
        compare(self.root,self.out,pins=self.pins)
        with (self.out/"field_status.csv").open() as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual({r["table_role"] for r in rows}, {"1","3"})


if __name__ == "__main__":
    unittest.main()
