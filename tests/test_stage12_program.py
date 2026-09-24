"""Known targets, causal visibility, complete handlers and no-dispatch replay."""
from contextlib import contextmanager
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from runners.stage12 import program as P,program_world as W,program_queries as Q,program_sources as S,program_prepare as B,local_api as API
from runners.stage12.common import REPO,RAW,read,freeze,digest,distribution

@contextmanager
def service(*args,**kwargs):yield {'uncertain':False,'call_charged_seconds':0.}


class ProgramTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.units=W.roster(21000,4);cls.donors=W.roster(51000,4)

    def test_source_counterfactuals_and_exact_rulers(self):
        for u in self.units:
            rows=W.static_rows('LP04',[u]);self.assertEqual(len(rows),42)
            for method in W.METHODS:
                for frame in ('true','false','neutral'):
                    by={(r['update'],r['mode']):r for r in rows if r['method']==method and r['frame']==frame}
                    self.assertEqual(by['unchanged','fresh']['target'],by['irrelevant','fresh']['target'])
                    self.assertGreaterEqual(W.tv(by['diagnostic','fresh']['target'],by['unchanged','fresh']['target']),.05)
                    self.assertEqual(len(by['diagnostic','fresh']['text'].encode()),len(by['irrelevant','fresh']['text'].encode()))
            rows=W.static_rows('LP06',[u]);by={r['condition']:r for r in rows if r['method']=='direct'}
            for name in ('duplicate','restatement','irrelevant'):self.assertEqual(by['single']['target'],by[name]['target'])
            self.assertEqual(len(by['independent']['text']),len(by['irrelevant']['text']))
        p=[.1,.2,.3,.4];order=[2,0,3,1]
        self.assertEqual(P.canonical([p[i] for i in order],order),p)
        with self.assertRaises(ValueError):P.canonical(p,[0,0,1,2])
        self.assertEqual(distribution(None,p)['half_brier'],1)
        self.assertTrue(distribution([1,0,0,0],p)['log_loss_infinite'])
        self.assertAlmostEqual(distribution(p,p)['half_brier'],(1-sum(v*v for v in p))/2)

    def test_query_unrevealed_outcomes_and_repeated_identity(self):
        u=self.units[0];slots=Q.slots('LP07',[u]);finished=[]
        for s in slots:
            r=Q.materialize(s,finished)
            if r['role']=='selection':
                self.assertNotIn('actual_target',r['text']);p=[float(i==0) for i in r['label_order']]
            else:p=r['target']
            finished.append(P.score(r,dict(probabilities=p,wall_seconds=0)))
        for policy in ('neutral','counterexample'):
            last=next(r for r in finished if r['policy']==policy and r['step']==3 and r['role']=='forecast')
            self.assertEqual([r['repeated'] for r in last['realized_selections']],[False,True,True])
            self.assertEqual(last['realized_selections'][-1]['information'],0)
        bad=[dict(r,probabilities=None) if r['role']=='selection' else r for r in finished]
        with self.assertRaisesRegex(ValueError,'selection'):Q.materialize(slots[2],bad)
        self.assertEqual(len(slots),22)
        stop=Q.stopping(self.units);self.assertEqual(len(stop),48)
        self.assertEqual({r['optimal_buy'] for r in stop},{False,True})
        for r in stop:
            result=P.score(r,dict(probabilities=r['target'],wall_seconds=0));self.assertEqual(result['decision_regret'],0)
            self.assertEqual(result['current_forecast'],r['forecast_target'])

    def test_known_wrong_copy_and_missing_family(self):
        rows=W.static_rows('LP02',self.units)
        for r in rows:
            if r['condition']=='wrong':
                result=P.score(r,dict(probabilities=r['supplied_answer'],wall_seconds=0))
                self.assertEqual(result['copy_max_error'],0);self.assertGreater(result['excess_half_brier'],.01)
        rows=W.static_rows('LP12',self.units)
        self.assertTrue(all(r['target'][-1]>0 for r in rows if r['candidate_condition']=='omit'))
        self.assertTrue(all(r['target'][-1]==0 for r in rows if r['candidate_condition']=='complete'))
        for r in W.static_rows('LP10',self.units):
            if r['role']=='acquisition':self.assertNotIn('Current query:',r['text'])

    def test_actual_handlers_no_dispatch_on_second_entry(self):
        families=['LP01','LP02','LP04','LP05','LP06','LP09','LP10','LP11','LP12','LP07','LP08']
        for family in families:
            with self.subTest(family=family),tempfile.TemporaryDirectory(dir=REPO/'results') as tmp:
                root=Path(tmp);u=self.units[:1]
                rows=Q.slots(family,u) if family=='LP07' else Q.stopping(self.units) if family=='LP08' else W.static_rows(family,u,donors=self.donors)
                freeze(root/'input.json',rows);freeze(root/'gate.json',dict(reader_admitted=True))
                freeze(root/'CONTRACT.json',dict(reporting='2099-01-01T00:00:00+00:00',cpu_process_seconds=10**8,gpu_service_seconds=10**8,diagnostic_gpu_seconds=10**8))
                card=dict(family=family,calls=len(rows),rows_path=str(root/'input.json'),rows_digest=digest(rows),admission_path=str(root/'gate.json'),profile={})
                seen=[]
                def api(path,payload=None,timeout=300):
                    seen.append(payload);n=payload['format']['properties']['probabilities']['minItems']
                    return dict(done=True,done_reason='stop',message=dict(content=json.dumps(dict(analysis='FAKE TRANSPORT ONLY',probabilities=[1/n]*n))),prompt_eval_count=10,eval_count=10)
                with patch.object(API,'service',service),patch.object(API,'snapshot',return_value={'fake':True}),patch.object(API,'api',side_effect=api):
                    first=P.run(root/'out',card,lambda **kw:None,root)
                    self.assertEqual(first,P.run(root/'out',card,lambda **kw:None,root))
                self.assertEqual(len(seen),len(rows))
                raw=root/'out/calls'/rows[0]['id']/'RAW.json';changed=read(raw);changed['message']['content']='changed';raw.write_text(json.dumps(changed))
                with self.assertRaisesRegex(ValueError,'binding'):P.run(root/'out',card,lambda **kw:None,root)

    def test_native_forward_does_not_see_future_steps(self):
        rows,meta=S.native(RAW/'inputs/ghost-source-v1')
        self.assertEqual(len(rows),256);self.assertEqual(meta['LP19']['status'],'BLOCKED')
        for r in rows:
            if r['task']=='next_given_goal':
                self.assertNotIn('final',r['public_projection'])
                self.assertTrue(all(e['step']==0 for e in r['public_projection'].get('observations',[])))

    def test_intervals_and_all_attempt_pairing(self):
        self.assertEqual(P.disposition(P.interval([-.1]*8)),'BENEFIT')
        self.assertEqual(P.disposition(P.interval([.1]*8)),'HARM')
        self.assertEqual(P.disposition(P.interval([0]*8)),'EQUIVALENT')
        self.assertEqual(P.disposition(P.interval([-.1,.1]*4)),'UNRESOLVED')
        with self.assertRaises(ValueError):P.paired([],lambda r:True,lambda r:False,lambda r:0)

    def test_narrow_admission_has_literal_and_capability_failure_directions(self):
        rows=[dict(view='witness',score=dict(valid=True,accuracy=float(i%4==0))) for i in range(32)]
        self.assertFalse(P.admission(rows,'LP16')['reader_admitted'])
        for r in rows:r['score']['accuracy']=1.
        self.assertTrue(P.admission(rows,'LP16')['reader_admitted'])
        rows.append(dict(view='current',score=dict(valid=False,accuracy=0.)))
        self.assertFalse(P.admission(rows,'LP16')['reader_admitted'])
        self.assertFalse(P.admission([],'LP20-Qwen')['reader_admitted'])
        hf=[dict(score=dict(valid=True,accuracy=float(i<42))) for i in range(48)]
        self.assertTrue(P.admission(hf,'LP20-Qwen')['reader_admitted'])
        hf[0]['score']['accuracy']=0.
        self.assertFalse(P.admission(hf,'LP20-Qwen')['reader_admitted'])

    def test_hf_raw_replay_checks_model_identity_without_loading(self):
        from runners.stage12 import program_hf as H
        with tempfile.TemporaryDirectory(dir=REPO/'results') as tmp:
            root=Path(tmp);req=API.request('Known answer B. Label order A,B.',2)
            card=dict(hf_model='fixture-only',model_files={'frozen':'a'*64})
            binding=digest(dict(request=req,model=card['hf_model'],files=card['model_files'],output_tokens=1024,context_tokens=4096,temperature=0))
            raw=dict(done=True,done_reason='stop',message=dict(content=json.dumps(dict(analysis='fixture',probabilities=[0.,1.]))),output_ids=[1,2])
            freeze(root/'REQUEST.json',req);freeze(root/'RAW.json',raw)
            saved=dict(binding=binding,raw_sha256=digest(raw),probabilities=[0.,1.],wall_seconds=1.)
            freeze(root/'COMPLETE.json',saved)
            self.assertEqual(H.call(req,2,root,{},root,card),saved)
            with self.assertRaises(ValueError):H.call(req,2,root,{},root,dict(card,hf_model='other'))
            with self.assertRaises(ValueError):H.call(req,3,root,{},root,card)
            with self.assertRaises(ValueError):H.call(req,2,root,{},root,dict(card,model_files={'frozen':'b'*64}))

    def test_admission_handler_writes_verdict_and_replays_for_both_backends(self):
        from runners.stage12 import program_hf as H
        for family in ('LP16','LP17','LP20-Qwen','LP20-Smol'):
            for probabilities,expected in (([1.,0.],True),([0.,1.],False),(None,False)):
                with self.subTest(family=family,probabilities=probabilities),tempfile.TemporaryDirectory(dir=REPO/'results') as tmp:
                    root=Path(tmp)
                    rows=[dict(id='fixture',family=family,text='FAKE admission fixture only',n=2,
                        call_class='direct',label_order=[0,1],target=[1.,0.],view='witness')]
                    freeze(root/'input.json',rows);freeze(root/'gate.json',dict(reader_admitted=True))
                    card=dict(family=family,calls=1,rows_path=str(root/'input.json'),rows_digest=digest(rows),
                        admission_path=str(root/'gate.json'),profile={},admission=True)
                    if family.startswith('LP20'):card['hf_model']='fixture-only'
                    calls=[]
                    def fake_call(req,n,path,*args,**kwargs):
                        path=Path(path)
                        if (path/'COMPLETE.json').exists():return read(path/'COMPLETE.json')
                        calls.append(req)
                        freeze(path/'RAW.json',dict(message=dict(content='FAKE transport fixture')))
                        return freeze(path/'COMPLETE.json',dict(probabilities=probabilities,wall_seconds=0.))
                    with patch.object(API,'service',service),patch.object(API,'call',fake_call),patch.object(H,'service',service),patch.object(H,'call',fake_call):
                        first=P.run(root/'out',card,lambda **kw:None,root)
                        self.assertEqual(first['reader_admitted'],expected)
                        self.assertEqual(read(root/'out/ADMISSION.json')['reader_admitted'],expected)
                        self.assertEqual((root/'out/READY.json').exists(),expected)
                        self.assertEqual(first,P.run(root/'out',card,lambda **kw:None,root))
                    self.assertEqual(len(calls),1)

    def test_calibration_bins_partition_exact_boundary_confidences(self):
        rows=[]
        for confidence in (.2,.4,.6,.8,1.):
            probabilities=[confidence]+[(1-confidence)/4]*4
            target=[.2]*5
            rows.append(dict(method='direct',n=5,probabilities=probabilities,target=target,
                score=distribution(probabilities,target)))
        group=P.calibration(rows)['groups'][0]
        self.assertEqual(sum(b['count'] for b in group['bins']),len(rows))
        self.assertEqual([(b['lower'],b['count']) for b in group['bins']],[(.2,1),(.4,1),(.6,1),(.8,2)])
        components=group['score_components']
        self.assertAlmostEqual(components['valid_only_loss'],components['uncertainty']+components['binned_reliability']-components['binned_resolution']+components['within_bin_remainder'])


if __name__=='__main__':unittest.main()
