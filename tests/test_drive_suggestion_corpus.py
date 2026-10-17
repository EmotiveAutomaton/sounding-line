import copy,tempfile,unittest
from pathlib import Path
from runners.drive.suggestion_corpus import menu_ranks,select_pilot,validate_rows,checkpoint,load_checkpoint,digest,main_bounds,ORDER,census

class CorpusTests(unittest.TestCase):
    def fixture(self):
        case=dict(key='k',brief='',document='',menu=['ab','cd','ef'])
        scores=[]
        for values in ([1.,2.],[1.,2.],[2.,2.]):
            total=sum(values);scores.append(dict(eligible=True,native_token_ids=[1,2],native_token_nll=values,codepoint_offsets=[[0,1],[1,2]],prefix_tokens=1,target_tokens=2,utf8_bytes=2,total_nll=total,mean_token_nll=total/2,nll_per_utf8_byte=total/2))
        rows=[dict(key='k',condition=c,scores=copy.deepcopy(scores),ranks=[1.5,1.5,3.]) for c in ('c0','c1','c2','c3')]
        return [case],rows
    def test_average_ties_and_exclusions(self):
        self.assertEqual(menu_ranks([dict(eligible=True,mean_token_nll=2),dict(eligible=False),dict(eligible=True,mean_token_nll=2),dict(eligible=True,mean_token_nll=1)]),[2.5,None,2.5,1.])
    def test_support_selection_order_invariant_and_overflow(self):
        xs=[('d',2048),('a',1),('c',500),('b',80),('z',2049)]
        self.assertEqual(select_pilot(xs),select_pilot(xs[::-1]));self.assertEqual(select_pilot(xs)[-1],'z')
        with self.assertRaises(ValueError):select_pilot([('z',2050)])
    def test_measured_main_gates_fail_closed(self):
        timing={name:dict(projected_seconds=100,projected_bytes=10000) for name in ORDER}
        self.assertEqual(main_bounds(timing)['max_compute_seconds'],36000)
        for key,value in [('projected_seconds',72*3600),('projected_bytes',32*1024**3),('projected_seconds',float('nan')),('projected_bytes',0)]:
            bad=copy.deepcopy(timing);bad[ORDER[0]][key]=value
            with self.assertRaises(ValueError):main_bounds(bad)
        del timing[ORDER[0]]
        with self.assertRaises(ValueError):main_bounds(timing)
    def test_input_census_preserves_overflow_without_truncation(self):
        from tests.test_drive_readers import Tokens
        groups=[dict(cases=[dict(key='short',brief='',document='',menu=['x','']),dict(key='long',brief='',document='x'*2100,menu=['a','b'])])]
        observed=[];counts,selection=census(Tokens(),groups,lambda *a:observed.append(a))
        self.assertEqual(counts['counts']['c3_excluded'],3)
        self.assertEqual(counts['counts']['c0_total'],4)
        self.assertIn('long',selection);self.assertTrue(observed)
        bad=dict(eligible=False,reason='whole context plus target exceeds common 2048-token window',prefix_tokens=1,target_tokens=2)
        cases,rows=self.fixture();rows[0]['scores'][0]=bad
        with self.assertRaises(ValueError):validate_rows(rows,cases)
    def test_complete_actual_checkpoint_handler_and_mutations(self):
        cases,rows=self.fixture();self.assertTrue(validate_rows(rows,cases))
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'chunk.json.gz';payload=dict(model='reader',plan_sha256='plan',input_sha256=digest(cases),rows=rows)
            record=checkpoint(p,payload,cases);self.assertEqual(load_checkpoint(p,record,cases,'plan','reader'),payload)
            with self.assertRaises(ValueError):load_checkpoint(p,record,cases,'other','reader')
            with self.assertRaises(ValueError):checkpoint(p,payload,cases)
            p.write_bytes(p.read_bytes()+b'x')
            with self.assertRaises(ValueError):load_checkpoint(p,record,cases,'plan','reader')
        for change in ('missing','order','loss','rank','offset','tokens'):
            bad=copy.deepcopy(rows)
            if change=='missing':bad.pop()
            elif change=='order':bad[0]['condition']='c3'
            elif change=='loss':bad[0]['scores'][0]['native_token_nll'][0]=float('nan')
            elif change=='rank':bad[0]['ranks']=[1,2,3]
            elif change=='offset':bad[0]['scores'][0]['codepoint_offsets'][0]=[0,3]
            else:bad[0]['scores'][0]['target_tokens']=1
            with self.assertRaises(ValueError):validate_rows(bad,cases)

if __name__=='__main__':unittest.main()
