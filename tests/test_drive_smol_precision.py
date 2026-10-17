import copy,unittest
from runners.drive.smol_precision import compare
from tests import test_drive_suggestion_corpus as fixtures

class PairedPrecisionTests(unittest.TestCase):
    def test_identical_and_unchanged_tolerance(self):
        _,rows=fixtures.CorpusTests().fixture();a=rows[0]['scores'];b=copy.deepcopy(a)
        self.assertTrue(compare(a,b,.02)['pass_all'])
        b[0]['native_token_nll'][0]+=.021
        self.assertFalse(compare(a,b,.02)['pass_all'])
    def test_alignment_finite_and_complete_support(self):
        _,rows=fixtures.CorpusTests().fixture();a=rows[0]['scores']
        for mutation in ('missing','nan','ids','length'):
            b=copy.deepcopy(a)
            if mutation=='missing':b.pop()
            elif mutation=='nan':b[0]['native_token_nll'][0]=float('nan')
            elif mutation=='ids':b[0]['native_token_ids']=[2,1]
            else:b[0]['native_token_nll'].pop()
            with self.assertRaises(ValueError):compare(a,b,.02)
    def test_whole_context_exclusions_remain_excluded(self):
        a=[dict(eligible=False,reason='whole context plus target exceeds common 2048-token window',prefix_tokens=2048,target_tokens=1)]
        self.assertEqual(compare(a,copy.deepcopy(a),.02)['eligible'],0)
        b=copy.deepcopy(a);b[0]['prefix_tokens']=2047
        with self.assertRaises(ValueError):compare(a,b,.02)

if __name__=='__main__':unittest.main()
