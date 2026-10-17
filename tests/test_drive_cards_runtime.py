import json
import tempfile
import unittest
from pathlib import Path
from runners.drive.cards.batch_runtime import claim_slot, release_slot, slot_count, check_files


class RuntimeChecks(unittest.TestCase):
    def test_counted_ownership_and_refusal(self):
        with tempfile.TemporaryDirectory(dir='.agent-state') as d:
            first=claim_slot(d, {'pid':1,'created_ticks':10}, 'A', slots=2)
            second=claim_slot(d, {'pid':2,'created_ticks':20}, 'B', slots=2)
            with self.assertRaises(RuntimeError):
                claim_slot(d, {'pid':3}, 'C', slots=2)
            with self.assertRaises(RuntimeError):
                release_slot(first[0],second[1])
            release_slot(*first)
            third=claim_slot(d, {'pid':3}, 'C',slots=2)
            self.assertEqual(first[0],third[0])
            release_slot(*third)
            release_slot(*second)

    def test_changed_pin_refuses(self):
        with tempfile.TemporaryDirectory(dir='.agent-state') as d:
            p=Path(d)/'input';p.write_bytes(b'changed')
            with self.assertRaises(ValueError):
                check_files({str(p):'0'*64})
        self.assertEqual([slot_count(i) for i in (4,8,11,12,32)], [2,3,3,4,4])


if __name__ == '__main__':
    unittest.main()
