import unittest
from runners.drive.v2 import analyze

class DecompositionTests(unittest.TestCase):
    def test_perfect_and_invalid_system_denominator(self):
        p=[[1,0,0,0],[0,1,0,0]];base=[[.25]*4]*2;y=[0,1];groups=['a','b']
        good=analyze(p,y,groups,base);self.assertEqual(good['system_half_brier'],0)
        self.assertEqual(good['merged_deciles']['half_brier'],0)
        bad=analyze(p,y,groups,base,[True,False]);self.assertEqual(bad['system_half_brier'],.5)
        self.assertEqual(bad['rows'],2);self.assertEqual(bad['invalid'],1)
        self.assertIsNone(bad['exact_vectors']['correction_iid'])
    def test_constant_resolution(self):
        p=[[.25]*4]*4;r=analyze(p,[0,1,2,3],['a','a','b','b'],p)
        self.assertEqual(r['merged_deciles']['resolution'],0)
        self.assertEqual(r['gain_over_reference']['estimate'],0)

if __name__=='__main__':unittest.main()
