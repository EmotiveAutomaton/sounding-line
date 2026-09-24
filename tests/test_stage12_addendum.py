"""Known references, full actual-handler replay and aggregate spending refusal."""
from contextlib import contextmanager
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from runners.stage12 import addendum as A, cloud as C, local_api as API, aries
from runners.stage12.common import REPO, RAW, read, freeze, filehash, digest, distribution
from runners.stage12.output_interface import VERSION


@contextmanager
def service(*args,**kwargs):
    yield dict(uncertain=False,call_charged_seconds=0.)


def revision_units():
    from runners.stage11_2.world import make_unit, enumerate_predict
    units=[]
    for i in range(36,164):
        r=make_unit('dev',i)[0];o=r['queries'][1]['observation']
        before=enumerate_predict(r['history'][:1],o)['probabilities'];after=enumerate_predict(r['history'][:8],o)['probabilities']
        if sum(abs(x-y) for x,y in zip(before,after))/2>=.05:units.append(r)
    return units[:8]


class AddendumTests(unittest.TestCase):
    def test_actual_revision_and_binding_handlers_replay_every_call(self):
        from runners.stage11_2.world import make_unit
        units=revision_units()
        self.assertEqual(len(units),8)
        for family,chosen,total in [('revision',units,112),('binding',[make_unit('dev',i)[0] for i in (16,17,18,19)],48)]:
            with self.subTest(family=family), tempfile.TemporaryDirectory(dir=REPO/'results') as tmp:
                root=Path(tmp);source=root/'jobs/source';public=root/'public.json';freeze(public,chosen)
                card=dict(family=family,candidate_ids=[r['unit'] for r in chosen],public_source=str(public),output_interface=VERSION)
                result=A.compile(source,card,lambda **kw:None,root)
                self.assertEqual(result,A.compile(source,card,lambda **kw:None,root))
                descriptors=read(source/'REQUESTS.json');self.assertEqual(len(descriptors),total)
                if family=='revision':
                    refs=read(source/'REFERENCES.json')
                    self.assertEqual({r['frame'] for r in refs},{'true','false'})
                    self.assertTrue(all(r['before']!=r['after'] and r['before']==r['irrelevant_target'] for r in refs))
                    for unit in chosen:
                        rows=[r for r in descriptors if r['unit']==unit['unit'] and r['method']=='direct' and r.get('mode')=='fresh']
                        d={r['update']:r for r in rows}
                        self.assertEqual(len(d['diagnostic']['text'].encode()),len(d['irrelevant']['text'].encode()))
                profile=dict(output=2048);gate=root/'jobs/gate'
                freeze(gate/'ADMISSION.json',dict(reader_admitted=True))
                freeze(gate/'READER_READY.json',dict(profile=profile,output_interface=VERSION))
                freeze(gate/'ROWS.json',[dict(call_class=c,call=dict(wall_seconds=10,prompt_tokens=100,output_tokens=20)) for c in ('forecast','account')])
                freeze(root/'CONTRACT.json',dict(reporting='2099-01-01T00:00:00+00:00',cpu_process_seconds=10**8,gpu_service_seconds=10**8,diagnostic_gpu_seconds=10**8))
                card.update(compile_card='source',canary_card='gate',profile=profile,effective_requests_digest=digest(descriptors))
                supplied={digest(r['request']):r.get('supplied_answer') for r in descriptors if 'request' in r}
                seen=[]
                def api(path,payload=None,timeout=300):
                    self.assertEqual(path,'/api/chat');seen.append(deepcopy(payload))
                    probabilities=supplied.get(digest(payload)) or [.25]*4
                    invalid=family=='revision' and len(seen)==1
                    return dict(done=True,done_reason='length' if invalid else 'stop',prompt_eval_count=100,eval_count=20,
                        message=dict(content=json.dumps(dict(analysis='FAKE TRANSPORT ONLY',probabilities=probabilities))),
                        total_duration=1000000,load_duration=0,prompt_eval_duration=500000,eval_duration=500000)
                with patch.object(API,'service',service),patch.object(API,'snapshot',return_value={'fake':True}),patch.object(API,'api',side_effect=api):
                    first=A.run(root/'out',card,lambda **kw:None,root)
                    self.assertEqual(first,A.run(root/'out',card,lambda **kw:None,root))
                self.assertEqual(len(seen),total)
                rows=read(root/'out/ROWS.json')
                if family=='revision':
                    self.assertEqual(sum(r['score']['invalid'] for r in rows),1)
                    self.assertEqual(len(A.summarize_pairs(rows)),48)
                    saved=[r for r in descriptors if r.get('saved_reply')]
                    raw=read(root/'out/calls'/saved[0]['saved_reply']/'RAW.json')
                    actual=read(root/'out/actual-requests'/(saved[0]['id']+'.json'))
                    self.assertEqual(actual['saved_reply_sha256'],digest(raw))
                    self.assertIn('FAKE TRANSPORT ONLY',actual['request']['messages'][-1]['content'])
                    with self.assertRaises(ValueError):A.summarize_pairs([r for r in rows if r['mode']!='fresh'])
                else:
                    self.assertTrue(all(r['fidelity']['copied_exactly'] for r in rows))
                    self.assertTrue(all(r['excess_half_brier']>.01 for r in rows if r['condition']=='wrong_vector'))
                changed=deepcopy(card);changed['effective_requests_digest']='changed'
                with self.assertRaisesRegex(ValueError,'roster'):A.run(root/'other',changed,lambda **kw:None,root)
                # Mutating the saved raw initial output cannot silently alter a descendant.
                first_path=root/'out/calls'/descriptors[0]['id']/'RAW.json'
                old=read(first_path);old['message']['content']='changed';first_path.write_text(json.dumps(old),encoding='utf-8')
                with patch.object(API,'service',service),self.assertRaisesRegex(ValueError,'binding'):
                    A.run(root/'out',card,lambda **kw:None,root)

    def test_label_inverse_and_failed_reference(self):
        self.assertEqual(A.rank_concordance(1,0),1.)
        self.assertEqual(A.rank_concordance(0,1),0.)
        self.assertEqual(A.rank_concordance(.5,.5),.5)
        self.assertIsNone(A.rank_concordance(None,.5))
        self.assertEqual(aries.lexical('', ''),0.)
        self.assertEqual(aries.lexical('same word','same word'),1.)
        self.assertEqual(aries.lexical('a','b'),0.)
        p=[.1,.2,.3,.4];order=list(A.PERMUTATION)
        self.assertEqual(A.inverse_labels([p[i] for i in order],order),p)
        self.assertIsNone(A.inverse_labels(None,order))
        with self.assertRaises(ValueError):A.inverse_labels(p,[0,0,2,3])
        row=dict(saved_reply='initial',text='evidence',call_class='forecast')
        with self.assertRaisesRegex(ValueError,'context'):
            A.effective_request(row,{'initial':{'message':{'content':'x'*10000}}},VERSION)

    def test_aries_additional_roster_has_explicit_classes(self):
        source=RAW/'inputs/aries-v1'
        if not source.exists():self.skipTest('private pinned ARIES input absent')
        excluded=set()
        for p in (RAW/'jobs').glob('S12-ARIES-compile*/SOURCE_ROWS.json'):excluded.update(r['doc'] for r in read(p))
        selection=A.source_aries(source,excluded)
        self.assertEqual(len(selection['paper_ids']),16)
        self.assertFalse(set(selection['paper_ids'])&excluded)
        with tempfile.TemporaryDirectory(dir=REPO/'results') as tmp:
            root=Path(tmp);card=dict(selection,source_root=str(source))
            first=aries.compile(root,card,lambda **kw:None,RAW)
            self.assertEqual(first,aries.compile(root,card,lambda **kw:None,RAW))
            self.assertEqual(first['requests'],128)
            self.assertEqual(first['eligible_pairs'],32)
            self.assertEqual({tuple(r['target']) for r in read(root/'EVALUATOR_ONLY.json')},{(1.,0.),(0.,1.)})

    def test_cloud_cap_only_and_aggregate_reservation(self):
        with tempfile.TemporaryDirectory(dir=REPO/'results') as tmp:
            root=Path(tmp);old=[dict(id=str(i),maximum_output_tokens=512,public=dict(labels=['a','b'],evidence='source')) for i in range(171)]
            original=root/'original.json';freeze(original,old)
            rows=deepcopy(old)
            for r in rows:r['maximum_output_tokens']=2048
            plan=dict(revision=C.REVISION,original_requests=str(original),original_requests_sha256=filehash(original),main_cap_cents=1300,pilot_cap_cents=300,retained_original_pilot_cents=300)
            self.assertTrue(C.validate_revision(plan,rows))
            bad=deepcopy(rows);bad[0]['public']['evidence']='changed'
            with self.assertRaisesRegex(ValueError,'more than output cap'):C.validate_revision(plan,bad)
            bad=deepcopy(rows);bad[0]['maximum_output_tokens']=512
            with self.assertRaises(ValueError):C.validate_revision(plan,bad)
        prior=[dict(invocation='pilot',reserved_cents=300,status='COMPLETE')]
        self.assertTrue(C.reservation_guard(prior,C.REVISION+'-pilot',3900,True))
        prior.append(dict(invocation=C.REVISION+'-pilot',reserved_cents=300,status='COMPLETE'))
        seconds,_=C.main_allowance([79.2]*12,True)
        self.assertEqual(C.cost(seconds),1300)
        self.assertTrue(C.reservation_guard(prior,C.REVISION+'-main',seconds,True))
        with self.assertRaises(ValueError):C.main_allowance([79.201]*12,True)
        with self.assertRaises(ValueError):C.reservation_guard(prior,C.REVISION+'-pilot',3900,True)
        with self.assertRaises(ValueError):C.reservation_guard(prior,C.REVISION+'-main',seconds+100,True)
        prior[0]['status']='UNKNOWN'
        with self.assertRaises(ValueError):C.reservation_guard(prior,C.REVISION+'-main',seconds,True)

    def test_revised_cloud_wire_archive_and_literal_refusals(self):
        import io,time,shutil
        from unittest.mock import MagicMock
        from runners.stage12.primary_analysis import parse_raw
        stamp=time.time();plan=dict(original_reporting_epoch=stamp+10000)
        approval=dict(campaign=C.CAMPAIGN,plan_sha256=digest(plan),curator_words='FAKE',over_ten_dollar_words='FAKE',gross_cap_cents=2000,provider='Modal',private_source_upload='retained CoAuthor projection on existing Modal route')
        account=dict(source='provider-api',status='VERIFIED',observed_at=stamp,cycle_start_at=stamp-100,cycle_end_at=stamp+20000,usage_limit_cents=4250,metered_at_check_cents=1270,storage_allowance_cents=500,net_spend_limit_cents=1250,other_workloads='none',payment_method_present=True,workspace='fixture',environment='main')
        self.assertTrue(C.validate(plan,approval,account,stamp))
        with self.assertRaisesRegex(ValueError,'headroom'):C.validate(plan,approval,dict(account,metered_at_check_cents=2000),stamp)
        with self.assertRaisesRegex(ValueError,'deadline'):C.validate(plan,approval,account,stamp+9990)
        profile=dict(model='fixture',model_digest='f'*64,server_version='fixture',context_tokens=16384,quantization='fixture')
        rows=[dict(id=str(i),public=dict(labels=['no','yes'],task='FAKE'),model_profile=profile,maximum_output_tokens=2048) for i in range(12)]
        payload=dict(profile=profile,rows=rows,call_seconds=240)
        valid=dict(done=True,done_reason='stop',prompt_eval_count=10,message=dict(content=json.dumps(dict(analysis='fixture',probabilities=[0.,1.]))))
        self.assertIsNone(parse_raw(dict(valid,done_reason='length'),2,16384))
        self.assertIsNone(parse_raw(dict(valid,message={'content':'{"probabilities": ['}),2,16384))
        def response(request,timeout):
            path=request.full_url.split('11434')[1]
            result={'/api/version':dict(version='fixture'),'/api/tags':dict(models=[dict(name='fixture',digest='f'*64)]),
                '/api/generate':dict(done=True),'/api/ps':dict(models=[dict(digest='f'*64,context_length=16384,details=dict(quantization_level='fixture'))]),'/api/chat':valid}[path]
            return io.BytesIO(json.dumps(result).encode())
        with tempfile.TemporaryDirectory(dir=REPO/'results') as tmp:
            root=Path(tmp);volume=MagicMock();opener=MagicMock();opener.open.side_effect=response;server=MagicMock();server.poll.return_value=None
            with patch('subprocess.Popen',return_value=server),patch('urllib.request.build_opener',return_value=opener):
                result=C.remote_run(volume,'revised-fixture',payload,time.time()+1000,tmp)
            restored=C.restore(root/result['archive_path'],root/'restored',result['archive_sha256'])
            self.assertTrue(C.verify_return(restored,payload,root/'restored',strict=True))
            plan=dict(revision=C.REVISION);folder=root/'pilot';folder.mkdir()
            shutil.copyfile(root/result['archive_path'],folder/'OUTPUT.zip')
            freeze(folder/'RESERVATION.json',dict(plan_sha256=digest(plan),payload_sha256=digest(payload)))
            freeze(folder/'COMPLETE.json',dict(result,valid_calls=12))
            self.assertEqual(C.verified_pilot(plan,rows,dict(request_ids=[r['id'] for r in rows]),folder)['valid_calls'],12)
            path=root/'restored/calls/0/REQUEST.json';changed=read(path);changed['wire']['think']=True;path.write_text(json.dumps(changed),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'revised wire'):C.verify_return(restored,payload,root/'restored',strict=True)
            with (folder/'OUTPUT.zip').open('ab') as f:f.write(b'changed')
            with self.assertRaisesRegex(ValueError,'archive changed'):C.verified_pilot(plan,rows,dict(request_ids=[r['id'] for r in rows]),folder)

    def test_worker_deadline_refuses_before_attempt(self):
        from runners.stage12.worker import run
        with tempfile.TemporaryDirectory(dir=REPO/'results') as tmp:
            root=Path(tmp);freeze(root/'CONTRACT.json',dict(reporting='2099-01-01T00:00:00+00:00',cpu_process_seconds=100000,gpu_service_seconds=100000,diagnostic_gpu_seconds=3600))
            path=root/'card.json';freeze(path,dict(id='deadline-fixture',handler='fixture',rehearsal=True,source_pins={},cpu_seconds=1,wall_seconds=60,execution_deadline='2000-01-01T00:00:00+00:00'))
            with self.assertRaisesRegex(TimeoutError,'execution window'):run(path,root)
            self.assertFalse((root/'jobs/deadline-fixture/START.json').exists())


if __name__=='__main__':unittest.main()
