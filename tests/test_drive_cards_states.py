import unittest
from runners.drive.cards.states import contrast_state, family_progress


class StateContract(unittest.TestCase):
    def test_direction_and_boundaries(self):
        for effect, lo, hi, result in [(1,.1,2,'positive'),(-1,-2,-.1,'negative'),
                                      (1,0,2,'marginal'),(-1,-2,0,'null'),(0,0,0,'null')]:
            self.assertEqual(contrast_state(effect,lo,hi), result)
            self.assertEqual(contrast_state(-effect,-hi,-lo,-1), result)
        self.assertEqual(contrast_state(1,2,3),'invalid')
        self.assertEqual(contrast_state(float('nan'),0,2),'invalid')

    def test_ladder_gaps_cannot_stop_early(self):
        ladder = list('abcdefgh')
        results = {x: {'state':'null'} for x in ladder[1:]}
        self.assertFalse(family_progress(ladder,results)['stopped'])
        results['a'] = {'state':'invalid'}
        self.assertTrue(family_progress(ladder,results)['stopped'])
        results['d'] = {'state':'negative'}
        self.assertFalse(family_progress(ladder,results)['stopped'])

    def test_marginal_extension_policy(self):
        rows = {x: {'state':'marginal','extension_state':'negative'} for x in 'abcdef'}
        self.assertTrue(family_progress(list('abcdef'), rows)['stopped'])
        rows['c']['extension_pending'] = True
        self.assertEqual(family_progress(list('abcdef'),rows)['consecutive_nulls'],2)


if __name__ == '__main__':
    unittest.main()
