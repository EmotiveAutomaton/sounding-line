import unittest
from runners.next_round.native_profile_audit import chronology,compare

class NativeTests(unittest.TestCase):
    def test_wrong_label_missing_row_and_time_fail(self):
        row=dict(key='a',ordinal=3,handling='accept',menu=['x'],document='d',prompt='p',open_at=1.,resolved_at=2.)
        self.assertEqual(compare([row],[row]),[])
        for patch in (dict(handling='dismiss'),dict(menu=['y']),dict(document='wrong'),dict(prompt='other'),dict(open_at=3),dict(resolved_at=3)):
            self.assertEqual(len(compare([row],[dict(row,**patch)])),1)
        self.assertEqual(len(compare([row],[])),1)
        with self.assertRaises(ValueError):compare([row],[row,row])
    def test_target_future_and_source_mutation_refuse(self):
        r=dict(key='past',writer='w',prompt='p',open_at=1,resolved_at=2,handling='accept',menu=['x'],document='d',ordinal=3,session='s')
        target=dict(key='target',writer='w',open_at=4)
        training={'w':dict(cutoff=3,h2=[r],h3=[r])};source={'past':r}
        chronology([target],training,source)
        for changed in (dict(r,resolved_at=3),dict(r,handling='dismiss')):
            with self.assertRaises(ValueError):chronology([target],training,{'past':changed})
        with self.assertRaises(ValueError):chronology([dict(target,key='past')],training,source)

if __name__=='__main__':unittest.main()
