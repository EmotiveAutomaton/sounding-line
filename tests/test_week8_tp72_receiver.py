"""Check membership, form selection and source-exclusion handover without study data."""
import csv
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'runners/drive/cards'), str(ROOT/'runners/drive/sealed/week6-sm-science')]
from runners.drive.sealed import week8_tp72_receiver as receiver


class ReceiverTest(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.people = frozenset(range(32))
        self.core = frozenset(range(16))
        self.contract = {name: (['reading','outcome','n','value','lo','hi'],
                                [('lo','hi')], {'reading':['worry','fear'], 'outcome':['affect']})
                         for name in receiver.CONVERSATION}

    def write(self, filename, labels, size):
        path = self.root/filename
        exists = path.exists()
        with path.open('a', encoding='utf8', newline='') as stream:
            writer = csv.writer(stream)
            if not exists:
                writer.writerow(self.contract[filename][0])
            writer.writerow([*labels,size,0,-1,1])

    def select(self, memberships):
        return receiver.select_tables('conversation', self.root, self.contract, memberships, self.people, [])

    def test_actual_membership_and_known_complements(self):
        filename = 'conversation_affect.csv'
        memberships = {}
        for name, group in [('worry', self.core), ('fear', frozenset(range(17)))]:
            self.write(filename,(name,'affect'),len(group))
            memberships[filename,(name,'affect')] = group
        table = self.select(memberships)
        self.assertEqual([r['reading'] for r in table[filename]], ['worry'])
        self.assertEqual(table[filename][0]['n'],'16')

    def test_mismatch_refuses(self):
        key = 'conversation_affect.csv',('worry','affect')
        self.write(*key, 16)
        for memberships in ({}, {key:self.people}, {key:self.core, ('conversation_traits.csv',('worry','affect')):self.core}):
            with self.subTest(memberships=tuple(memberships)), self.assertRaises(receiver.SealedFailure):
                self.select(memberships)

    def test_duplicate_label_refuses(self):
        key = 'conversation_affect.csv',('worry','affect')
        self.write(*key,16)
        self.write(*key,16)
        with self.assertRaises(receiver.SealedFailure):
            self.select({key:self.core})

    def test_distinct_groups_and_dropped_comments(self):
        from contextlib import nullcontext
        (self.root/'excluded_communities.json').write_text(json.dumps(['named']), 'utf8')
        rows=[('NAMED','1','personality test'),('other','2','my personality test'),('other','3','ordinary')]
        with patch.object(receiver.original,'selected',side_effect=lambda *args: nullcontext(iter(rows))):
            self.assertEqual(receiver.measured_exclusions(None,{},self.root,[None]*4+[(1,None)]),({'named'},{'2'}))
            with self.assertRaises(receiver.SealedFailure):
                receiver.measured_exclusions(None,{},self.root,[None]*4+[(2,None)])

    def test_empty_output(self):
        with self.assertRaises(receiver.SealedFailure) as failure:
            self.select({})
        self.assertEqual(failure.exception.code,12)

    def test_history_observation_reaches_the_selected_table(self):
        contract = {name: (['stat','n','value','lo','hi'], [('lo','hi')],
                           {'stat':['diagonalMinusOther']}) for name in receiver.HISTORY}
        def produce(dest, observe):
            dest.mkdir()
            observe('contrast.csv',('diagonalMinusOther',),self.core)
            with (dest/'contrast.csv').open('w',encoding='utf8',newline='') as stream:
                writer = csv.writer(stream)
                writer.writerow(contract['contrast.csv'][0])
                writer.writerow(['diagonalMinusOther',16,0,-1,1])
        selected = receiver.receive('history',self.root/'out',contract,self.people,[],produce)
        self.assertEqual(selected['contrast.csv'][0]['n'],'16')


if __name__=='__main__':
    unittest.main()
