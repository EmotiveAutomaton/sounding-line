"""Known-answer measure and real native-queue rehearsal for Stage 12."""
import json
from pathlib import Path
import tempfile
import unittest
from datetime import datetime,timezone,timedelta
from runners.stage12.common import REPO,read,freeze,filehash,distribution,digest
from runners.stage12.provider import packet,metrics,validate

class Rulers(unittest.TestCase):
    def test_tiny_interface_without_consuming_a_training_setting(self):
        import torch
        from runners.stage12.tiny import create,RECIPE,batch,tokens,capability
        public={'schema':'v19.local.public.1','tier':'E0','inputs':{'artifact':[0,1,0]}}
        model=create(RECIPE);model.eval()
        with torch.no_grad():
            x,n=batch([{'public':public}]);h=model.encode(x,n)
            a=model.decode(h);b=model.decode(h.clone())
            self.assertTrue(all(torch.equal(a[k],b[k]) for k in a))
        with self.assertRaises(ValueError):tokens(dict(public,hidden_goal='meaning'))
        self.assertFalse(capability([])['admitted'])
    def test_primary_cluster_weighting_and_zero_support(self):
        from runners.stage12.primary_analysis import aggregate,dependency_groups
        rows=[]
        for writer,n in [('w0',4),('w1',1)]:
            for i in range(n):
                for condition,p in [('own_history',[1.,0.]),('no_history',[0.,1.])]:
                    rows.append(dict(id=writer+str(i),writer_component=writer,prompt_component='shared',session=writer,
                        condition=condition,probabilities=p,score=distribution(p,[1.,0.])))
        r=aggregate(rows)
        self.assertEqual(r['primary']['mean'],1)
        self.assertEqual(r['dependency_components'],1)
        self.assertIsNone(r['primary']['population_interval'])
        self.assertEqual(r['conditions']['no_history']['infinite_log_losses'],5)
    def test_week_checkpoints_and_full_unit_deadline(self):
        from runners.stage12.checkpoints import due
        from runners.stage12.common import admit
        t=datetime.now(timezone.utc);contract={k:(t+timedelta(hours=h)).isoformat() for k,h in [('interim',96),('reporting',156),('deadline',168)]}
        self.assertEqual(due(contract,t),[])
        self.assertEqual([x[0] for x in due(contract,t+timedelta(hours=157))],['interim-96h','reporting-start'])
        with tempfile.TemporaryDirectory(dir=REPO/'results/phase_2_4_stage_12/raw') as d:
            contract.update(cpu_process_seconds=100000,gpu_service_seconds=100000,diagnostic_gpu_seconds=3600,reporting=(t+timedelta(seconds=50)).isoformat())
            with self.assertRaises(RuntimeError):admit({'wall_seconds':60},contract,Path(d))
        from runners.stage12.checkpoints import run
        with tempfile.TemporaryDirectory(dir=REPO/'results/phase_2_4_stage_12/raw') as d:
            raw=Path(d);freeze(raw/'CONTRACT.json',{k:(t-timedelta(hours=h)).isoformat() for k,h in [('interim',72),('reporting',12),('deadline',1)]})
            run(raw);first=filehash(raw/'checkpoints/final-checkpoint.json')
            run(raw)
            self.assertEqual(filehash(raw/'checkpoints/final-checkpoint.json'),first)
            self.assertEqual(len(list((raw/'checkpoints').glob('EXIT-*.json'))),2)

    def test_context_matrices_have_sensitive_and_invariant_controls(self):
        from runners.stage12.context_battery import compile_rows,matched_timing_check
        from runners.stage11_2.world import make_unit
        units=[make_unit('dev',i)[0] for i in range(4)]
        for family,count in [('C1',32),('C2',16),('C3',24)]:
            rows,targets=compile_rows(units,family);self.assertEqual(len(rows),count)
            self.assertEqual({r['id'] for r in rows},{r['id'] for r in targets})
            if family=='C1':
                own=[r for r in rows if r['unit']==units[0]['unit']]
                self.assertEqual(own[0]['request'],own[-1]['request'])
        reference=[dict(wall_seconds=10,prompt_tokens=100,output_tokens=100)]*3
        self.assertTrue(matched_timing_check([dict(wall_seconds=25,prompt_tokens=100,output_tokens=100)],reference)['degraded'])
        self.assertFalse(matched_timing_check([dict(wall_seconds=25,prompt_tokens=1000,output_tokens=100)],reference)['matched'])
    def test_current_canary_balanced_and_repeated(self):
        from runners.stage12.canary import compile_inputs
        rows=compile_inputs()
        for name in ('forecast','account'):
            own=[r for r in rows if r['call_class']==name]
            self.assertEqual({max(range(4),key=r['truth'].__getitem__) for r in own[:4]},set(range(4)))
            self.assertEqual(own[0]['request'],own[-1]['request'])
            self.assertTrue(all(r['request']['options']['num_thread']==2 for r in own))

    def test_unknown_current_call_retains_reservation_and_refuses_retry(self):
        from unittest.mock import patch
        from runners.stage12.local_api import call,request
        with tempfile.TemporaryDirectory(dir=REPO/'results/phase_2_4_stage_12/raw') as d:
            raw=Path(d);freeze(raw/'CONTRACT.json',dict(reporting=(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat(),
                cpu_process_seconds=100000,gpu_service_seconds=100000,diagnostic_gpu_seconds=3600))
            state={'uncertain':False};req=request('A is correct. Labels A, B.',2)
            with patch('runners.stage12.local_api.snapshot',return_value={'fixture':True}),patch('runners.stage12.local_api.api',side_effect=TimeoutError('fixture')) as transport:
                with self.assertRaises(TimeoutError):call(req,2,raw/'call',state,raw,True)
                with self.assertRaises(RuntimeError):call(req,2,raw/'call',state,raw,True)
                self.assertEqual(transport.call_count,1)
            self.assertTrue(state['uncertain'])
            self.assertEqual(read(next((raw/'charges').glob('*.json')))['gpu_seconds'],330)

    def test_gpu_lock_retained_only_for_unknown_service(self):
        from unittest.mock import patch
        from runners.stage12.local_api import service
        with tempfile.TemporaryDirectory(dir=REPO/'results/phase_2_4_stage_12/raw') as d:
            root=Path(d);(root/'results').mkdir();out=root/'first';out.mkdir()
            freeze(root/'CONTRACT.json',dict(reporting=(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat(),cpu_process_seconds=100000,gpu_service_seconds=100000,diagnostic_gpu_seconds=3600))
            with patch('runners.stage12.local_api.REPO',root),patch('runners.stage12.local_api.readiness',return_value={'ready':True}):
                with service(out,{},root):self.assertTrue((root/'results/.gpu.lock').exists())
                self.assertFalse((root/'results/.gpu.lock').exists())
                out=root/'second';out.mkdir()
                with service(out,{},root) as state:state['uncertain']=True
                self.assertTrue((root/'results/.gpu.lock').exists())
                with self.assertRaises(FileExistsError):
                    with service(root/'third',{},root):pass

    def test_known_response_survives_failed_post_response_telemetry(self):
        from unittest.mock import patch
        from runners.stage12.local_api import call,request
        with tempfile.TemporaryDirectory(dir=REPO/'results/phase_2_4_stage_12/raw') as d:
            root=Path(d);req=request('A is correct. Labels A, B.',2)
            freeze(root/'CONTRACT.json',dict(reporting=(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat(),
                cpu_process_seconds=100000,gpu_service_seconds=100000,diagnostic_gpu_seconds=3600))
            response=dict(done=True,done_reason='stop',message=dict(content=json.dumps(dict(analysis='fixture',probabilities=[1.,0.]))))
            state={'uncertain':False}
            with patch('runners.stage12.local_api.snapshot',side_effect=[{'fixture':True},TimeoutError('device stalled')]),patch('runners.stage12.local_api.api',return_value=response) as api:
                with self.assertRaises(TimeoutError):call(req,2,root/'call',state,root,True,300)
                with self.assertRaises(RuntimeError):call(req,2,root/'call',state,root,True,300)
                self.assertEqual(api.call_count,1)
            self.assertEqual(read(root/'call/RAW.json'),response)
            receipt=read(root/'call/RESPONSE_RECEIVED.json')
            self.assertEqual(receipt['raw_sha256'],digest(response))
            self.assertGreaterEqual(receipt['wall_seconds'],0)
            self.assertEqual(read(root/'call/FAILED.json')['response_receipt_sha256'],digest(receipt))
            self.assertFalse((root/'call/COMPLETE.json').exists())
            self.assertFalse(state['uncertain'])
            self.assertEqual(read(next((root/'charges').glob('*.json')))['gpu_seconds'],300)

    def test_shorter_canary_budget_preserves_entire_balanced_unit(self):
        from unittest.mock import patch
        from contextlib import contextmanager
        from runners.stage12.canary import run,compile_inputs
        rows=compile_inputs();requests={digest(r['request']):r['truth'] for r in rows}
        @contextmanager
        def service(*args,**kwargs):yield {}
        def call(req,n,path,state,raw,diagnostic,allowance):
            return dict(probabilities=requests.get(digest(req),[1.,0.,0.,0.]),wall_seconds=1,
                        prompt_tokens=100,output_tokens=100)
        with tempfile.TemporaryDirectory(dir=REPO/'results/phase_2_4_stage_12/raw') as d:
            root=Path(d);card=dict(requests_digest=digest(rows),call_allowance_seconds=300,
                gpu_seconds=3270,diagnostic_gpu_seconds=3270,wall_seconds=4000)
            with patch('runners.stage12.canary.service',service),patch('runners.stage12.canary.call',side_effect=call) as transport:
                result=run(root/'ok',card,lambda **k:None,root)
                self.assertTrue(result['reader_admitted'])
                self.assertEqual(transport.call_count,11)
                self.assertEqual([c.kwargs['allowance'] for c in transport.call_args_list],[150]+[300]*10)
                self.assertEqual({k:g['n'] for k,g in result['groups'].items()},{'forecast':5,'account':5})
                before=transport.call_count
                with self.assertRaises(ValueError):run(root/'bad',dict(card,diagnostic_gpu_seconds=3269),lambda **k:None,root)
                self.assertEqual(transport.call_count,before)
    def test_history_matching_never_uses_future_or_test_donor(self):
        from runners.stage12.population import previous,matched_donor,allocation
        def r(key,ordinal,session='s',unit='train',stimulus='p'):
            return dict(key=key,ordinal=ordinal,session=session,unit=unit,stimulus=stimulus,
                        domain='same',views={'artifact':{'text':'x'}},truth='accept')
        train=[r(str(i),i) for i in range(6)]
        target=r('t',2,'test','test','q');own=[r('h0',0,'test','test','q'),r('h1',1,'test','test','q')]
        self.assertEqual(len(previous(target,own+[target,r('future',3,'test','test','q')])),2)
        donor,hist=matched_donor(target,own,train,train)
        self.assertEqual(len(hist),2);self.assertTrue(all(x['ordinal']<donor['ordinal'] for x in hist))
        with self.assertRaises(ValueError):matched_donor(target,own,[target],train)
        a=allocation(list('abcdefgh'),2,2,'test');self.assertEqual(a,allocation(list('hgfedcba'),2,2,'test'))
        self.assertEqual(list(a.values()).count('evaluation'),4)
    def test_excluded_log_without_identity_is_not_an_extra_writer(self):
        from runners.stage12.audit import ledger_summary
        rows=[dict(writer='w',prompt='p',usable=True,usable_decisions=3),
              dict(key='excluded',usable=False,reason='not in released metadata')]
        r=ledger_summary(rows)
        self.assertEqual(r['writers'],1);self.assertEqual(r['metadata_linked_sessions'],1)
        self.assertEqual(r['metadata_unlinked_excluded_logs'],1)
        rows[1]['usable']=True
        with self.assertRaises(ValueError):ledger_summary(rows)
    def test_finite_distributions_and_infinite_log_loss(self):
        self.assertEqual(distribution([1.,0.],[1.,0.])['half_brier'],0.)
        self.assertEqual(distribution([.5,.5],[1.,0.])['half_brier'],.25)
        self.assertTrue(distribution([0.,1.],[1.,0.])['log_loss_infinite'])
        self.assertFalse(distribution([.2,.2],[1.,0.])['valid'])
        self.assertFalse(distribution([float('nan'),1.],[1.,0.])['valid'])

    def test_location_and_unknown_cannot_win(self):
        target=dict(slot='s',actor='human_writer',operation='insert',relation='none',span_ids=['p0'],span_state='located')
        c=dict(target,role='process',status='inferred')
        self.assertEqual(metrics([c],[target])['correctly_located_useful_events'],1)
        self.assertEqual(metrics([dict(c,span_ids=['p1'])],[target])['correctly_located_useful_events'],0)
        self.assertEqual(metrics([],[target])['supported_useful_events'],0)
        self.assertEqual(metrics([dict(c,operation='delete')],[target])['unsupported_operation_claims'],1)

    def test_observed_mental_goal_requires_separate_evidence(self):
        evidence=dict(endpoint='abc',anchors=[dict(id='p0',start=0,end=3)])
        p=packet('case',evidence,'fixture',[])
        p['claims']=[dict(role='g_t',status='observed',span_ids=['p0'],evidence_refs=['click'])]
        with self.assertRaises(ValueError):validate(p)
        p['claims'][0]['status']='inferred';self.assertTrue(validate(p))
        p['claims'][0]['span_ids']=['absent']
        with self.assertRaises(ValueError):validate(p)

    def test_nanosecond_audit_and_original_semantics(self):
        from runners.stage12.audit import timing_row,OLD
        p=next((OLD/'calls').glob('*/COMPLETE.json')).parent;r=timing_row(p)
        self.assertEqual(r['seconds']['eval_duration'],r['original_nanoseconds']['eval_duration']/1e9)
        self.assertAlmostEqual(r['wall_seconds']-r['seconds']['total_duration'],r['unaccounted_wait_seconds'])
        self.assertIsNone(r['gpu_snapshot'])
        self.assertEqual(len(r['model_revision']),64)

    def test_causal_rehearsal(self):
        from runners.stage12.controlled import tiny_rehearsal
        with tempfile.TemporaryDirectory(dir=REPO/'results') as d:
            r=tiny_rehearsal(Path(d),dict(seed=120921),lambda **kw:None,Path(d))
            self.assertTrue(all(r['controls'].values()))
            self.assertEqual(r['settings_trained'],0)

    def test_git_real_replay(self):
        from runners.stage12.git_context import fixture
        with tempfile.TemporaryDirectory(dir=REPO/'results') as d:
            r=fixture(Path(d)/'fixture')
            self.assertEqual(len(r['opportunities']),16)
            self.assertTrue(all(r['controls'].values()))

    def test_git_merge_and_actual_missing_history(self):
        from runners.stage12.git_context import merge_fixture
        with tempfile.TemporaryDirectory(dir=REPO/'results') as d:
            r=merge_fixture(Path(d)/'fixture')
            self.assertEqual(len(r['parents']),2)
            self.assertTrue(all(r['controls'].values()))

    def test_local_claims_do_not_invent_location_or_mental_observation(self):
        from runners.stage12.local_interpretation import score_claims,validate_body,request,to_provider
        from runners.stage12.local_api import parse
        public=dict(schema='v19.local.public.1',tier='E2-full',inputs=dict(artifact=[0,1,0],initial=[0,1,0],requested_purpose=0,
            observations=[dict(step=0,operation='inspect',before=[0,1,0],after=[0,1,0],tool_proposal=None)]))
        body=dict(analysis='fixture',probabilities=[1.,0.,0.],claims=[dict(role='process',status='observed',step=0,value='inspect',span_ids=['unit-0'],evidence_refs=['observation:0'])],unknown=True,next_evidence='record the attended unit')
        reference=dict(process_support=[dict(operations=['inspect']*3)])
        score=score_claims(validate_body(body),public,reference)
        self.assertEqual(score['supported_witnessed_events'],1);self.assertEqual(score['correctly_located_useful_events'],0)
        body['claims'].append(dict(body['claims'][0],role='g_t',value='meaning'))
        self.assertEqual(score_claims(body,public,reference)['unsupported_mental_assertions'],1)
        output=to_provider('fixture',public,'direct',body,score_claims(body,public,reference))
        self.assertEqual(output['claims'][0]['span_state'],'unknown')
        self.assertEqual(output['claims'][1]['status'],'inferred')
        self.assertEqual(output['claims'][1]['asserted_status'],'observed')
        req=request(public,'Infer local goal',['meaning','dependency','presentation'],'direct')
        raw=dict(done=True,done_reason='stop',message=dict(content=json.dumps(body)))
        self.assertEqual(parse(raw,3,req['format']),[1.,0.,0.])
        body['claims'][0]['span_ids']=['missing']
        with self.assertRaises(ValueError):validate_body(body)

    def test_aries_canonical_many_to_many_and_unlabelled(self):
        from runners.stage12.aries import paragraph_text,relation
        paper=dict(pdf_parse=dict(body_text=[dict(text='first'),dict(text='second')],back_matter=[dict(text='last')]))
        self.assertEqual(paragraph_text(paper,[0,2]),'first\nlast')
        with self.assertRaises(ValueError):paragraph_text(paper,[3])
        labels=dict(positive_edits=[1],negative_edits=[2])
        self.assertEqual(relation(labels,1),'linked');self.assertEqual(relation(labels,2),'not-linked')
        self.assertEqual(relation(labels,3),'unlabelled')

    def test_cloud_authority_and_full_remote_retrieval_without_inference(self):
        import io,time
        from unittest.mock import patch,MagicMock
        from runners.stage12.cloud import validate,cost,remote_run,restore,verify_return,verified_pilot,CAMPAIGN
        now=time.time();plan=dict(original_reporting_epoch=now+10000)
        approval=dict(campaign=CAMPAIGN,plan_sha256=digest(plan),curator_words='synthetic test fixture, not authorization',
            over_ten_dollar_words='synthetic fixture only',gross_cap_cents=2000,provider='Modal',private_source_upload='retained CoAuthor projection on existing Modal route')
        account=dict(source='provider-api',status='VERIFIED',observed_at=now,cycle_start_at=now-100,cycle_end_at=now+20000,
            usage_limit_cents=2000,metered_at_check_cents=0,storage_allowance_cents=0,net_spend_limit_cents=2000,
            other_workloads='none',payment_method_present=True,workspace='fixture',environment='fixture')
        self.assertTrue(validate(plan,approval,account,now));self.assertLessEqual(cost(3900),300)
        with self.assertRaises(ValueError):validate(plan,dict(approval,curator_words=''),account,now)
        with self.assertRaises(ValueError):validate(plan,approval,dict(account,observed_at=now-90000),now)
        profile=dict(model='fixture',model_digest='f'*64,server_version='fixture',context_tokens=16384,quantization='fixture')
        original=dict(id='fixture',public=dict(labels=['no','yes'],task='fixture'),model_profile=profile,maximum_output_tokens=32)
        payload=dict(profile=profile,rows=[original],call_seconds=240)
        def response(request,timeout):
            path=request.full_url.split('11434')[1]
            result={'/api/version':dict(version='fixture'),'/api/tags':dict(models=[dict(name='fixture',digest='f'*64)]),
                '/api/generate':dict(done=True),'/api/ps':dict(models=[dict(digest='f'*64,context_length=16384,details=dict(quantization_level='fixture'))]),
                '/api/chat':dict(done=True,done_reason='stop',prompt_eval_count=10,message=dict(content=json.dumps(dict(analysis='fixture',probabilities=[0.,1.]))))}[path]
            return io.BytesIO(json.dumps(result).encode())
        with tempfile.TemporaryDirectory(dir=REPO/'results') as d:
            volume=MagicMock();opener=MagicMock();opener.open.side_effect=response;server=MagicMock();server.poll.return_value=None
            with patch('subprocess.Popen',return_value=server),patch('urllib.request.build_opener',return_value=opener):
                terminal=remote_run(volume,'fixture',payload,now+1000,d)
                self.assertEqual(terminal['status'],'COMPLETE');self.assertTrue(server.terminate.called)
                recovered=restore(Path(d)/terminal['archive_path'],Path(d)/'retrieved',terminal['archive_sha256'])
                self.assertEqual(recovered['rows'][0]['raw_response']['prompt_eval_count'],10)
                self.assertTrue(verify_return(recovered,payload,Path(d)/'retrieved'))
                import shutil
                folder=Path(d)/'pilot';folder.mkdir()
                shutil.copyfile(Path(d)/terminal['archive_path'],folder/'OUTPUT.zip')
                freeze(folder/'RESERVATION.json',dict(plan_sha256=digest(plan),payload_sha256=digest(payload)))
                freeze(folder/'COMPLETE.json',dict(terminal,valid_calls=1))
                self.assertEqual(verified_pilot(plan,[original],dict(request_ids=['fixture']),folder)['valid_calls'],1)
                broken=read(folder/'COMPLETE.json');broken['rows'][0]['wall_seconds']+=1
                from runners.stage12.common import atomic
                atomic(folder/'COMPLETE.json',broken)
                with self.assertRaises(ValueError):verified_pilot(plan,[original],dict(request_ids=['fixture']),folder)
                recovered['rows'][0]['raw_response']['prompt_eval_count']=20
                with self.assertRaises(ValueError):verify_return(recovered,payload,Path(d)/'retrieved')
                with self.assertRaises(RuntimeError):remote_run(volume,'fixture',payload,now+1000,d)

    def test_shared_causal_and_practice_consumers_with_untrained_fixture(self):
        import torch
        from runners.stage12.tiny import create,RECIPE,causal,HEADS
        from runners.stage12.shared_extensions import expertise,reference_composition
        torch.set_num_threads(1);torch.manual_seed(123)
        model=create(RECIPE);public=dict(schema='v19.local.public.1',tier='E0',inputs=dict(artifact=[0,1,0]))
        targets={k:[1./n]*n for k,n in HEADS.items()}
        equal=dict(composition='independent-static',reference=dict(ab=targets,ba=targets))
        self.assertEqual(reference_composition(equal),0.)
        with self.assertRaises(ValueError):reference_composition(dict(equal,composition='ordered-dependent'))
        with tempfile.TemporaryDirectory(dir=REPO/'results') as d:
            raw=Path(d);source=raw/'jobs/import';source.mkdir(parents=True);out=raw/'causal';out.mkdir()
            checkpoint=source/'MODEL.pt';torch.save(dict(model=model.state_dict()),checkpoint)
            record=dict(recipe=RECIPE,checkpoint=str(checkpoint),checkpoint_sha256=filehash(checkpoint))
            freeze(source/'MODEL.json',record);freeze(source/'CAPABILITY.json',dict(admitted=True,scope='UNTRAINED TEST FIXTURE ONLY'))
            pair=dict(id='fixture',lineage='dev',base=public,donor=public,wrong_variable=public,ordinary=targets,counterfactual=targets)
            pairs=raw/'pairs.json';freeze(pairs,dict(development=[pair],test=[dict(pair,lineage='test')]))
            result=causal(out,dict(fit_card='import',pairs=str(pairs)),lambda **kw:None,raw)
            self.assertEqual(result['rows'],12)
            self.assertEqual({r['arm'] for r in read(out/'ROWS.json')},{'correct','random','shuffled','wrong_variable','noop','full_state'})
            cross=[(a,b,'on-policy') for a in ('technical','presentation') for b in ('intact','degraded')]
            examples=[]
            for objective,quality,shift in cross:
                for arm in ('declarative','observational','practice','exact-replay'):
                    examples.append(dict(unit='fixture',objective=objective,quality=quality,distribution=shift,arm=arm,model_id='fixture',
                        public=public,targets=targets,feedback_count=1,sample_count=1,tool_access='same',rng_sha256='fixture',
                        initial_weights_sha256='fixture',optimizer_recipe_sha256='fixture',persistent_state_sha256='fixture',update_rule='frozen'))
            path=raw/'practice.json';freeze(path,dict(schema='ghost.practice-replay.1',training_owner='Ghost',production_capability_admitted=True,
                charge_receipt_sha256='UNTRAINED TEST FIXTURE ONLY',models=[dict(record,id='fixture')],pairs=examples))
            receipt=raw/'review.json';freeze(receipt,dict(path=str(path),sha256=filehash(path),native_reference_replay=True))
            practice_out=raw/'practice';practice_out.mkdir();card=dict(reviewed_receipt=str(receipt),cross=cross)
            result=expertise(practice_out,card,lambda **kw:None,raw);self.assertEqual(result['matched_cells'],4)
            records=read(practice_out/'ROWS.json');self.assertEqual(len(records),32)
            means={arm:sum(r['half_brier'] for r in records if r['arm']==arm) for arm in ('practice','exact-replay')}
            self.assertEqual(means['practice'],means['exact-replay'])

    def test_primary_full_retrieval_and_runtime_drift(self):
        from runners.stage12.primary_analysis import consume
        with tempfile.TemporaryDirectory(dir=REPO/'results') as d:
            raw=Path(d);primary=raw/'jobs/primary';cloud=raw/'jobs/cloud';analysis=raw/'jobs/analysis';out=raw/'output'
            for p in (primary,cloud,analysis,out):p.mkdir(parents=True)
            truth=[dict(id='a',truth='yes',writer_component='w',prompt_component='p',session='s')]
            freeze(primary/'EVALUATOR_ONLY.json',truth)
            freeze(primary/'READER_INPUTS.json',[dict(id='a',labels=['no','yes'],prior=[.5,.5],persistence=[0.,1.])])
            freeze(analysis/'ANALYSIS_PLAN.json',dict(full_training_prior=[.5,.5]))
            profile=dict(model_digest='f'*64,server_version='fixture',context_tokens=4096,quantization='fixture')
            req=[dict(id=str(i),source_id='a',condition=c,public=dict(labels=['no','yes']),model_profile=profile) for i,c in enumerate(('own_history','no_history','matched_training_donor'))]
            freeze(cloud/'REQUESTS.json',req)
            rows=[dict(id=r['id'],request=r,model_profile=profile,runtime_identity=profile,cost_receipt={'fixture':True},
                       raw_response=dict(done=True,done_reason='stop',prompt_eval_count=10,message=dict(content=json.dumps(dict(probabilities=[0.,1.]))))) for r in req]
            incoming=raw/'incoming.json';freeze(incoming,dict(source_request_sha256=filehash(cloud/'REQUESTS.json'),rows=rows))
            card=dict(primary_card='primary',cloud_card='cloud',analysis_card='analysis',retrieval=str(incoming))
            result=consume(out,card,lambda **kw:None,raw);self.assertEqual(result['rows'],6)
            self.assertEqual(result['comparisons']['primary']['mean'],0.)
            self.assertEqual(result['comparisons']['conditions']['own_history']['valid'],1)
            rows[0]['runtime_identity']=dict(profile,context_tokens=200)
            incoming.write_text(json.dumps(dict(source_request_sha256=filehash(cloud/'REQUESTS.json'),rows=rows)),encoding='utf-8')
            with self.assertRaises(ValueError):consume(out,card,lambda **kw:None,raw)

class NativeQueue(unittest.TestCase):
    def test_failure_continuation_missing_inputs_and_reentry(self):
        from runners.stage12.queue import run
        from runners.stage12.prepare import source_files
        from runners.stage12.common import pin
        # Raw outputs are ignored, and the actual CLI worker is exercised.
        with tempfile.TemporaryDirectory(dir=REPO/'results/phase_2_4_stage_12/raw') as d:
            raw=Path(d);pins=pin(source_files())
            start=datetime.now(timezone.utc)
            freeze(raw/'CONTRACT.json',dict(reporting=(start+timedelta(hours=1)).isoformat(),
                cpu_process_seconds=100000,gpu_service_seconds=100000,diagnostic_gpu_seconds=3600))
            ids=['fixture-fails','fixture-ready','fixture-deferred'];hashes={}
            for identifier in ids:
                cp=raw/'manifests'/(identifier+'.json')
                freeze(cp,dict(id=identifier,handler='fixture',rehearsal=True,resource='cpu',question='Native runner rehearsal',
                    cpu_seconds=60,wall_seconds=60,seed=120921,source_pins=pins,inputs={},
                    needs=[str((raw/'missing.json').relative_to(REPO))] if identifier=='fixture-deferred' else []))
                hashes[identifier]=filehash(cp)
            plan=raw/'PLAN.json';freeze(plan,dict(cards=ids,source_pins=pins,manifest_hashes=hashes,contract_sha256=filehash(raw/'CONTRACT.json')))
            run(plan,raw)
            self.assertTrue(list((raw/'queue').glob('EXIT-*.json')))
            self.assertTrue((raw/'jobs/fixture-fails/FAILED.json').exists())
            self.assertTrue((raw/'jobs/fixture-ready/COMPLETE.json').exists())
            self.assertFalse((raw/'jobs/fixture-deferred/START.json').exists())
            before=filehash(raw/'jobs/fixture-ready/COMPLETE.json')
            run(plan,raw)
            self.assertEqual(filehash(raw/'jobs/fixture-ready/COMPLETE.json'),before)
            self.assertFalse((raw/'jobs/fixture-fails/COMPLETE.json').exists())
            self.assertEqual(read(raw/'charges/fixture-fails.json')['state'],'failed')
            (raw/'CONTRACT.json').write_text('{}',encoding='utf-8')
            with self.assertRaises(ValueError):run(plan,raw)

if __name__=='__main__':unittest.main()
