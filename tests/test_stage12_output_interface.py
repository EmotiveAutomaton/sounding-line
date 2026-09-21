"""Output diagnosis keeps old inputs and strict failed-response accounting."""
import copy
import json
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from runners.stage12.output_interface import adapt, VERSION
from runners.stage12.local_api import parse, request
from runners.stage12.canary import compile_inputs


class OutputInterface(unittest.TestCase):
    def test_preserves_evidence_roster_and_original_requests(self):
        old=compile_inputs(); before=copy.deepcopy(old); new=compile_inputs(VERSION)
        self.assertEqual(old,before)
        for a,b in zip(old,new):
            self.assertEqual(a['truth'],b['truth'])
            self.assertEqual(a['source_id'],b['source_id'])
            self.assertTrue(b['request']['messages'][-1]['content'].startswith(a['request']['messages'][-1]['content']))
            self.assertEqual(b['request']['options']['num_predict'],2048)
        for kind in ('forecast','account'):
            group=[r for r in new if r['call_class']==kind]
            self.assertEqual(group[0]['request'],group[-1]['request'])
            self.assertEqual({max(range(4),key=r['truth'].__getitem__) for r in group[:4]},set(range(4)))
        self.assertEqual(adapt(old[0]['request']),old[0]['request'])
        with self.assertRaises(ValueError):adapt(old[0]['request'],'unreviewed')

    def test_invalid_responses_stay_invalid(self):
        req=adapt(request('Labels A, B, C, D.',4),VERSION)
        def raw(p,reason='stop'):
            return dict(done=True,done_reason=reason,message=dict(content=json.dumps(dict(analysis='fixture',probabilities=p))))
        for p,reason in [([.1,.89,0,0],'stop'),([1,0,0,0],'length'),([float('nan'),0,0,0],'stop')]:
            with self.assertRaises(ValueError):parse(raw(p,reason),4,req['format'])
        self.assertEqual(parse(raw([.925,.025,.025,.025]),4,req['format']),[.925,.025,.025,.025])

    def test_oversized_input_refuses_before_inference(self):
        req=request('Labels A, B.',2)
        req['messages'][-1]['content']='x'*8000
        with self.assertRaises(ValueError):adapt(req,VERSION)

    def test_changed_roster_and_wrong_profile_refuse(self):
        from runners.stage12.output_interface import rows_for_card,profile_for_card
        from runners.stage12.common import REPO,freeze,digest
        rows=[dict(request=request('Labels A, B.',2))]
        card=dict(output_interface=VERSION)
        card['effective_requests_digest']=digest(rows_for_card(rows,card))
        rows_for_card(rows,card)
        rows[0]['request']['messages'][-1]['content']+=' changed'
        with self.assertRaises(ValueError):rows_for_card(rows,card)
        with tempfile.TemporaryDirectory(dir=REPO/'results') as d:
            p=Path(d);freeze(p/'READER_READY.json',dict(profile={'output':512},output_interface=None))
            with self.assertRaises(ValueError):profile_for_card(card,p,{'output':2048})

    def test_capacity_wait_requires_two_ready_samples_and_honors_stop(self):
        from runners.stage12 import capacity_wait
        from runners.stage12.common import REPO,read
        with tempfile.TemporaryDirectory(dir=REPO/'results') as d:
            p=Path(d);(p/'results').mkdir()
            card=dict(profile={},poll_seconds=300)
            seq=[dict(ready=False,reason='occupied'),dict(ready=True,reason='ready'),dict(ready=True,reason='ready')]
            with patch.object(capacity_wait,'REPO',p),patch.object(capacity_wait,'readiness',side_effect=seq) as inspect,patch.object(capacity_wait.time,'sleep'):
                result=capacity_wait.run(p/'wait',card,lambda **kw:None,p)
            self.assertEqual(inspect.call_count,3)
            self.assertEqual(read(p/'wait/RESOURCE_READY.json')['checks'],3)
            self.assertTrue(result['controls']['no_inference'])
            def stop(**kw):raise TimeoutError('natural boundary cancellation')
            with self.assertRaises(TimeoutError):capacity_wait.run(p/'cancelled',card,stop,p)
            self.assertFalse((p/'cancelled/RESOURCE_READY.json').exists())

    def test_retention_handler_reentry_preserves_json_bank_without_new_calls(self):
        from contextlib import contextmanager
        from runners.stage12 import retention
        from runners.stage12.common import REPO,freeze,read,digest
        from runners.stage11_2.world import make_unit
        @contextmanager
        def service(*args,**kwargs):yield {}
        invoked={}
        def call(req,n,path,state,raw):
            key=str(path);binding=digest(req)
            if key in invoked:
                self.assertEqual(invoked[key][0],binding)
                return invoked[key][1]
            body=dict(analysis='TEST FIXTURE ONLY',probabilities=[.25]*4)
            freeze(path/'RAW.json',dict(message=dict(content=json.dumps(body))))
            result=dict(probabilities=body['probabilities'],wall_seconds=1,prompt_tokens=100,output_tokens=100)
            invoked[key]=(binding,result)
            return result
        with tempfile.TemporaryDirectory(dir=REPO/'results') as d:
            raw=Path(d);unit,_=make_unit('dev',0);src=raw/'jobs/source';gate=raw/'jobs/gate';out=raw/'out'
            freeze(src/'PUBLIC_UNITS.json',[unit])
            freeze(src/'EVALUATOR_ONLY.json',[dict(unit=unit['unit'],query=q,target=[.25]*4) for q in (1,3)])
            freeze(gate/'ADMISSION.json',dict(reader_admitted=True))
            profile=dict(output=2048)
            freeze(gate/'READER_READY.json',dict(profile=profile,output_interface=VERSION))
            freeze(gate/'ROWS.json',[dict(call_class=k,call=dict(wall_seconds=10,prompt_tokens=100,output_tokens=100)) for k in ('forecast','account')])
            card=dict(compile_card='source',canary_card='gate',profile=profile,output_interface=VERSION)
            with patch.object(retention,'service',service),patch.object(retention,'call',side_effect=call):
                first=retention.run(out,card,lambda **kw:None,raw)
                self.assertEqual(len(invoked),11)
                again=retention.run(out,card,lambda **kw:None,raw)
                self.assertEqual(len(invoked),11)
            self.assertEqual(first,again)
            self.assertEqual(set(read(out/(unit['unit']+'-FROZEN.json'))['bank']),{'1','3'})


if __name__=='__main__':unittest.main()
