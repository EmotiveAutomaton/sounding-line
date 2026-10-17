import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from runners.drive import suggestion_resume_v1 as resume
from tests.test_drive_suggestion_corpus import CorpusTests


class ResumeTests(unittest.TestCase):
    def test_prefix_refuses_holes_duplicates_and_reordering(self):
        groups=[dict(session='a',cases=[1]),dict(session='b',cases=[1])]
        records=[dict(model='m1',session='a'),dict(model='m1',session='b'),dict(model='m2',session='a')]
        with patch.object(resume.base,'ORDER',('m1','m2')):
            self.assertEqual(len(resume.prefix_keys(records,groups)),3)
            for bad in (records[1:],records[::-1],records+[records[-1]]):
                with self.assertRaises(ValueError):resume.prefix_keys(bad,groups)

    def test_original_budget_not_reset(self):
        plan=dict(max_compute_seconds=155780)
        self.assertEqual(resume.remaining_budget(plan,'2026-10-17T08:00:00+00:00','2026-10-17T14:27:10.978+00:00'),(23231,132549))
        for end in ('2026-10-16T08:00:00+00:00','2026-10-20T08:00:00+00:00'):
            with self.assertRaises(ValueError):resume.remaining_budget(plan,'2026-10-17T08:00:00+00:00',end)

    def test_real_mixed_checkpoint_verification_and_mutation_refusal(self):
        cases,rows=CorpusTests().fixture()
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'run';pilot=Path(td)/'pilot';b=resume.base
            b.freeze(root/'PLAN.json',dict(pins={},predecessor_plan_sha256='old-plan'))
            b.freeze(pilot/'CASES.json',[dict(session='a',cases=cases)])
            census=dict(counts={**{c+'_total':3 for c in ('c0','c1','c2','c3')},'eligible':12},target_tokens=24,input_tokens=36)
            b.freeze(pilot/'CENSUS.json',{m:census for m in ('m1','m2')})
            records=[]
            for m,plan in [('m1','old-plan'),('m2',b.filehash(root/'PLAN.json'))]:
                payload=dict(model=m,session='a',input_sha256=b.digest(cases),plan_sha256=plan,rows=copy.deepcopy(rows))
                r=b.checkpoint(root/m/'a.json.gz',payload,cases);r.update(model=m,session='a');records.append(r)
            b.freeze(root/'REUSE.json',records[:1]);b.freeze(root/'PREPARED.json',dict(reuse_sha256=b.filehash(root/'REUSE.json')))
            b.freeze(root/'CHUNKS.json',records)
            with patch.object(resume,'ROOT',root),patch.object(b,'PILOT',pilot),patch.object(b,'ORDER',('m1','m2')):
                resume.verify();self.assertTrue(b.read(root/'VERIFIED.json')['verified'])
                bad=root/'m1/a.json.gz';bad.write_bytes(bad.read_bytes()+b'x')
                with self.assertRaises(ValueError):resume.verify()

    def test_census_refuses_missing_or_extra_tokens(self):
        _,rows=CorpusTests().fixture();actual=resume.totals(rows)
        census=dict(counts={**{c+'_total':3 for c in ('c0','c1','c2','c3')},'eligible':12},target_tokens=24,input_tokens=36)
        resume.check_census(actual,census)
        for field in actual:
            bad=dict(actual);bad[field]+=1
            with self.assertRaises(ValueError):resume.check_census(bad,census)

    def test_prepare_authenticates_actual_retained_checkpoint(self):
        cases,rows=CorpusTests().fixture();b=resume.base
        with tempfile.TemporaryDirectory(dir=resume.REPO/'.agent-state') as td:
            source=Path(td)/'old';root=Path(td)/'new';pilot=Path(td)/'pilot'
            b.freeze(source/'PLAN.json',dict(pins={},max_compute_seconds=1000))
            b.freeze(source/'OWNER.json',dict(at='2026-10-17T08:00:00+00:00',native=dict(pid=123)))
            b.freeze(source/'FAILED.json',dict(at='2026-10-17T08:01:00+00:00',reason='GPU safety floor'))
            b.freeze(pilot/'CASES.json',[dict(session='a',cases=cases)])
            payload=dict(model='m',session='a',input_sha256=b.digest(cases),plan_sha256=b.filehash(source/'PLAN.json'),rows=rows)
            chunk=source/'m/a.json.gz';record=b.checkpoint(chunk,payload,cases);record.update(model='m',session='a')
            b.freeze(source/'CHUNKS.json',[record])
            with patch.object(resume,'SOURCE',source),patch.object(resume,'ROOT',root),patch.object(b,'PILOT',pilot),patch.object(b,'ORDER',('m',)),patch.object(b,'native_identity',return_value=None):
                resume.prepare();self.assertEqual(b.read(root/'PLAN.json')['max_compute_seconds'],940)
                with self.assertRaises(ValueError):resume.prepare()
                with patch.object(resume,'ROOT',Path(td)/'corrupt'):
                    chunk.write_bytes(chunk.read_bytes()+b'x')
                    with self.assertRaises(ValueError):resume.prepare()


if __name__=='__main__':unittest.main()
