import unittest
import json,tempfile
from pathlib import Path
from unittest.mock import patch
from runners.drive import budget as b
from runners.drive.cloud import params,Replay,MODEL
from runners.stage14.common import digest


class BudgetTests(unittest.TestCase):
    approval={'campaign':b.CAMPAIGN,'first_paid_cents':1000}
    def guard(self,runs,node='A',cents=1):return b.guard(runs,node,'new',cents,self.approval,now_epoch=0)
    def test_tranche_node_and_duplicate(self):
        run=dict(campaign_id=b.CAMPAIGN,invocation='old',node='A',booked_cents=999)
        self.guard([run])
        with self.assertRaises(ValueError):self.guard([run],cents=2)
        with self.assertRaises(ValueError):self.guard([],node='A0',cents=101)
        with self.assertRaises(ValueError):self.guard([],node='Reserve')
        with self.assertRaises(ValueError):self.guard([dict(run,invocation='new')])
    def test_cross_campaign_pending_account(self):
        account=dict(usage_limit_cents=4250,metered_at_check_cents=0,storage_allowance_cents=100,
            spend_limit_cents=1500,billed_at_check_cents=0,observed_at=100)
        runs=[dict(campaign_id='old',invocation='modal-old',booked_cents=800,status='RESERVED',ts=1)]
        self.assertEqual(b.modal_headroom(account,runs),600)
    def test_no_truncation_or_failed_item_as_answer(self):
        schema=dict(type='object',properties={'answer':{'type':'string','enum':['yes','no']}},required=['answer'],additionalProperties=False)
        ident=digest(params('test',schema))
        msg=dict(model=MODEL,stop_reason='max_tokens',content=[dict(type='text',text='{"answer":"yes"}')])
        r=Replay({ident:dict(result=dict(type='succeeded',message=msg))})
        with self.assertRaises(ValueError):r.complete('test',schema)
    def test_counted_ceiling_integer(self):
        row={'custom_id':'x','params':{'max_tokens':32}}
        self.assertEqual(b.ceiling([row],{'x':500}),3)
        with self.assertRaises(ValueError):b.ceiling([row],{'x':0})


class WholeRouteTests(unittest.TestCase):
    def test_all_batteries_through_fake_provider(self):
        from runners.drive import cloud as c
        from runners.stage14.common import REPO,read,filehash,freeze
        with tempfile.TemporaryDirectory(dir=REPO/'.agent-state') as td:
            root=Path(td).resolve();self.assertTrue(root.is_relative_to(REPO))
            def fake(path,value=None):
                if path=='/v1/models/'+MODEL:return json.dumps({'id':MODEL}).encode()
                if path=='/v1/messages/count_tokens':return b'{"input_tokens":500}'
                if path=='/v1/messages/batches':return b'{"id":"fake_batch"}'
                if path=='/v1/messages/batches/fake_batch':return b'{"id":"fake_batch","processing_status":"ended"}'
                if path=='/v1/messages/batches/fake_batch/results':
                    rows=read(root/'REQUESTS.json');items=read(root/'ITEMS.json');offsets={q:0 for q in c.QUESTIONS};out=[]
                    for row in rows:
                        q=row['question'];item=items[q][offsets[q]];offsets[q]+=1
                        msg=dict(model=MODEL,stop_reason='end_turn',content=[dict(type='text',text=json.dumps({'answer':item['expected']}))],usage=dict(input_tokens=500,output_tokens=12))
                        out.append(json.dumps(dict(custom_id=row['custom_id'],result=dict(type='succeeded',message=msg))))
                    return ('\n'.join(out)+'\n').encode()
                raise AssertionError(path)
            with patch.object(c,'ROOT',root),patch.object(c,'request',fake),patch.object(c,'reserve',return_value={'fake':True}),patch.object(c,'reconcile') as reconciled:
                p=c.prepare();self.assertLessEqual(p['reserved_cents'],100)
                c.submit();self.assertEqual(c.retrieve()['status'],'COMPLETE')
                receipt=read(root/'COMPLETE.json')
                for rel,h in receipt['outputs'].items():self.assertEqual(filehash(root/rel),h)
                self.assertEqual(len(read(root/'SUMMARY.json')),9);reconciled.assert_called_once()
                # No dispatch retry is possible even when all responses were valid.
                with self.assertRaises(FileExistsError):c.submit()


if __name__=='__main__':unittest.main()
