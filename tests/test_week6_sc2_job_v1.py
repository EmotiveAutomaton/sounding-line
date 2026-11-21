"""Exercise the SC2 entry, genuine-person suppression, and deterministic packaging."""
import ast
import base64
import csv
import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from runners.drive.cards.week6_sealed_support_v1 import SealedFailure
from runners.drive.sealed import week6_sc2_build_v1 as build
from runners.drive.sealed import week6_sc2_model_v1 as model
from runners.drive.sealed.week6_sc2_constructed_v1 import make_files
from runners.drive.sealed.week6_sc2_job_v1 import compare


class TestMatchedEntry(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.out = self.root / "out"
        self.out.mkdir()

    def test_full_parquet_job_known_answer(self):
        compare(self.root, self.out, pins=make_files(self.root))
        with (self.out/"estimates.csv").open() as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 3)
        for row, expected in zip(rows, [1., -1., 2.], strict=True):
            self.assertEqual((row["n"], row["conversations"], row["valid_draws"]), ("27", "26", "2000"))
            for name in ("estimate", "lower", "upper"):
                self.assertAlmostEqual(float(row[name]), expected, places=8)
        support = (self.out/"support.csv").read_text()
        self.assertFalse(any(key in support for key in ("repeat-speaker", "fixture-", "invented-")))

    def test_duplicated_outcomes_have_zero_paired_difference(self):
        with patch.object(model, "DRAWS", 20):
            # The public entry declares its production draw count once.
            with patch("runners.drive.sealed.week6_sc2_job_v1.DRAWS", 20):
                compare(self.root, self.out, pins=make_files(self.root, identical=True))
        with (self.out/"estimates.csv").open() as stream:
            rows = list(csv.DictReader(stream))
        self.assertAlmostEqual(float(rows[2]["estimate"]), 0)
        self.assertAlmostEqual(float(rows[2]["upper"]), 0)

    def test_ten_people_are_suppressed_even_with_eighteen_directed_reports(self):
        with self.assertRaises(SealedFailure) as error:
            compare(self.root,self.out,pins=make_files(self.root,conversations=9))
        self.assertEqual(error.exception.code,12)
        self.assertEqual(list(self.out.iterdir()), [])

    def test_entry_rebuilds_exactly_and_science_contains_no_constructed_module(self):
        p = self.root/"job"
        self.assertEqual(build.build(p), build.build(p))
        payload=(p/"matched/run.py").read_text("utf8")
        tree=ast.parse(payload)
        packed, = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant)
                   and isinstance(n.value,str) and len(n.value)>3000]
        with zipfile.ZipFile(io.BytesIO(base64.b85decode(packed))) as z:
            self.assertFalse(any("constructed" in n for n in z.namelist()))
            for source in build.MODULES:
                self.assertEqual(z.read(source.as_posix()), (build.ROOT/source).read_bytes())
        (p/"matched/run.py").write_text("changed")
        with self.assertRaises(ValueError):
            build.build(p)


if __name__ == "__main__":
    unittest.main()
