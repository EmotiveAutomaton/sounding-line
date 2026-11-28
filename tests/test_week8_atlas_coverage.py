"""A cost stop may retain only independently replayed cells from the frozen order."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from tools.week8_atlas_coverage import checkpoint_receipt


class CoverageTest(unittest.TestCase):
    def setUp(self):
        scratch=TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.root=Path(scratch.name)
        self.folder=self.root/'verified_cells'
        self.folder.mkdir()
        self.keys=[('help','mood','internal'),('loss','mood','all'),('loss','mood','unread')]

    def cell(self, i, key):
        data=dict(zip(('event','feeling','scope'),key))
        (self.folder/f'{i:04}.json').write_text(json.dumps(data))

    def progress(self,n):
        (self.root/'ATLAS_PROGRESS.json').write_text(json.dumps(dict(verified=n,planned=3)))

    def test_completed_atomic_write_before_progress_and_separate_member(self):
        self.cell(0,self.keys[0])
        self.cell(1,self.keys[1])
        self.progress(1)
        a=checkpoint_receipt(self.root,self.keys)
        self.assertEqual(a['planned'],dict(internal=1,all=1,unread=1))
        self.assertEqual(a['reached'],dict(internal=1,all=1))
        self.assertEqual(list(a['checksums']),['0000.json','0001.json'])

    def test_wrong_identity_hole_and_uncommitted_progress_refuse(self):
        self.cell(0,self.keys[1])
        self.progress(1)
        with self.assertRaises(ValueError):
            checkpoint_receipt(self.root,self.keys)
        self.cell(0,self.keys[0])
        self.cell(2,self.keys[2])
        self.progress(2)
        with self.assertRaises(ValueError):
            checkpoint_receipt(self.root,self.keys)
        (self.folder/'0002.json').unlink()
        with self.assertRaises(ValueError):
            checkpoint_receipt(self.root,self.keys)

    def test_unmeasured_cells_do_not_enter_agreement_count(self):
        import sys
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
        from r48_week8_tables import atlas_tables
        self.cell(0,self.keys[0])
        path=self.folder/'0000.json'
        cell=json.loads(path.read_text())
        cell.update(splits=10,defined_both=10,same_clear=10,both_positive=10,both_negative=0,
                    paired_intervals=[[[1,0.1,2],[0.9,0.2,2]]]*10)
        path.write_text(json.dumps(cell))
        self.progress(1)
        audit=checkpoint_receipt(self.root,self.keys)
        failure={'reason':'Row allowance or campaign drain'}
        (self.root/'FAILED.json').write_text(json.dumps(failure))
        with patch('tools.week8_atlas_coverage.capture',return_value=audit):
            rows={r[0]:r for r in atlas_tables(self.root,failure)}
        self.assertEqual(rows['0049, replayed cells with at least eight agreements'][1],1)
        self.assertEqual(rows['all, unmeasured cells'][1],1)
        self.assertNotIn('all, replayed cells with at least eight agreements',rows)
