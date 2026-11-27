"""Constructed membership, interval and fallback checks for amendment DN."""
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'runners/drive/cards'),str(ROOT/'runners/drive/sealed/week6-sm-science'),str(ROOT)]
from independent_release import Entry
from runners.drive.sealed.r48_forms import choose, SealedFailure


class ReleaseForms(unittest.TestCase):
    universe=frozenset(range(100))

    def form(self, people):
        return [(1,'effect',[Entry({'estimate':0.5,'lower':0.1,'upper':0.9,'n':len(people)},frozenset(people))])]

    def select(self, fine, coarse, pooled):
        forms=dict(zip(('fine','coarse','summary'),map(self.form,(fine,coarse,pooled))))
        return choose(forms,self.universe,[])['effect'][0]['n']

    def test_finest_safe(self):
        self.assertEqual(self.select(range(60),range(70),range(100)),60)

    def test_small_complement_uses_coarse(self):
        self.assertEqual(self.select(range(96),range(70),range(100)),70)

    def test_summary_is_one_distinct_union(self):
        self.assertEqual(self.select(range(10),range(93),range(100)),100)

    def test_no_form(self):
        with self.assertRaises(SealedFailure) as result:
            self.select(range(3),range(4),range(5))
        self.assertEqual(result.exception.code,12)

    def test_count_must_match(self):
        bad=self.form(range(60))
        bad[0][2][0].fields['n']=100
        with self.assertRaises(SealedFailure):
            choose(dict(fine=bad,coarse=[],summary=[]),self.universe,[])

    def test_partial_fine_is_never_returned(self):
        rows=self.form(range(50))[0][2]+self.form(range(53))[0][2]
        forms=dict(fine=[(1,'effect',rows)],coarse=self.form(range(60)),summary=self.form(range(100)))
        self.assertEqual(choose(forms,self.universe,[])['effect'][0]['n'],60)


if __name__=='__main__':
    unittest.main()
