import unittest
from runners.drive.reader_precision import discrepancy

class PrecisionTests(unittest.TestCase):
    def test_complete_known_vectors(self):
        self.assertEqual(discrepancy([1.,2.],[1.,2.]),0.)
        self.assertGreater(discrepancy([1.,2.],[1.,2.1]),.02)
    def test_no_silent_zip_or_nonfinite(self):
        for a,b in [([],[]),([1,2],[1]),([1],[float('nan')]),([float('inf')],[1])]:
            with self.assertRaises(ValueError):discrepancy(a,b)

if __name__=='__main__':unittest.main()
