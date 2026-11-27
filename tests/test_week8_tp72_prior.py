"""The earlier standing row must bind to the same people after the reciprocal join."""
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

from tests.test_week8_lkg1 import sample
from runners.drive.sealed import week8_tp72_prior as prior
from runners.stage14.common import filehash


class PriorRosterTest(unittest.TestCase):
    def test_reciprocal_missing_values_and_count_check(self):
        frame,previous=sample()
        frame['you_think_my_status']=5.
        frame.loc[frame.user_id=='p001','you_think_my_status']=float('nan')
        frame['i_think_your_status']=6.
        frame.loc[frame.partner_id=='p003','i_think_your_status']=float('nan')
        with TemporaryDirectory() as tmp:
            mount=Path(tmp)
            table=mount/'surveys/survey.parquet'
            table.parent.mkdir()
            frame.to_parquet(table,index=False)
            config=dict(pin=[table.relative_to(mount).as_posix(),table.stat().st_size,filehash(table)],
                        previous=previous,trait_counts={},standing_people=158)
            universe,known=prior.conversation_rosters(mount,config)
            self.assertEqual(set(frame.user_id),universe)
            self.assertEqual(universe-{'p001','p003'},known[-1])
            with self.assertRaises(prior.SealedFailure):
                prior.conversation_rosters(mount,dict(config,standing_people=159))
