"""Full local Gear 3 consumer on constructed answers and original raw archives."""
from copy import deepcopy
from dataclasses import asdict,replace
import hashlib,json,os,shutil
from pathlib import Path
import pytest
from runners import gear3_campaign as cost,gear3_plan
from runners.stage10 import gear3_batch as batch,gear3_bundle as bundle,gear3_consumer as consumer
from runners.stage10 import gear3_readouts as readouts,gear3_freeze as freeze,human_baselines
from runners.stage10 import gear3_io as storage,human_memory_checks as fixtures,human_programs
from runners.stage10.contracts import digest,canonical
from tests.test_gear3_round1 import manifest,transport,profile,SPEC
from tests.test_gear3_controller import account


def test_direct_label_secondary_projection_and_conditional_collapse():
    task=fixtures.task(100,2);m=manifest();answers={task.task_id:{'truth':task.choices[0][0],'group':'fixture','event':'one','session':'session','dependencies':['prompt:fixture']}}
    train=m['training']['coauthor-handling'];analysis={'targets':{task.task_id:{'record':asdict(task),'metadata':answers[task.task_id]}},'selection':{},'cheap_controls':{'fitted':human_baselines.fit(train['public'],train['answers'])}}
    units=[]
    for u in m['units']:
        p=.8 if u['arm']=='R2' and u['model']=='27b' else .25
        forecast={'choice':task.choices[0][0],'probabilities':{k:p if i==0 else (1-p)/3 for i,(k,_) in enumerate(task.choices)},'insufficient_evidence':False,'explanation':'constructed'}
        units.append({'unit':u,'result':{'status':'VALID','forecast':forecast}})
    r=consumer.summarize([{'manifest':m,'condition':'ordinary','units':units}],analysis,answers,[],{})
    contrast=next(iter(r['contrasts'].values()))
    assert contrast['direct_model_package_difference']['brier']['estimate']==0
    assert contrast['deliberative_model_package_difference']['brier']['estimate']!=0
    original=deepcopy(units[0]['result']['forecast']);projected=readouts.same_confidence(task,'VALID',original)
    assert original==units[0]['result']['forecast'] and sorted(projected['probabilities'].values())==[.05,.05,.05,.85]
    assert readouts.same_confidence(task,'INVALID',None) is None
    candidate={'goal_hypothesis':'fixture','program':{'feature':'draft_words','threshold':6.5,'below':'accept','otherwise':'edit'}}
    d=readouts.human_diagnostic(task,[candidate],original)
    assert d['constant_collapse_identical'] and d['constant_rule_share']==0 and d['vote_concentration']==1
    swapped=deepcopy(units);u=next(x for x in swapped if x['unit']['model']=='27b' and x['unit']['arm']=='R0')
    u['result']['forecast']=projected
    changed=next(iter(consumer.summarize([{'manifest':m,'condition':'ordinary','units':swapped}],analysis,answers,[],{})['contrasts'].values()))
    assert changed['direct_model_package_difference']['brier']['estimate']!=0
    assert changed['brier']==contrast['brier']
    assert changed['deliberative_model_package_difference']==contrast['deliberative_model_package_difference']


def test_whole_plan_cost_and_fabricated_pilot_refuse(tmp_path):
    # No provider access; account headroom remains lower than campaign authority.
    a=account(tmp_path/'account.json')
    data={'runs':[]}
    jobs=[{'invocation':'a'+str(i),'node':'A','seconds':14000,'overhead_cents':25,'bundle_sha256':'f'*64} for i in range(2)]
    gear3_plan.affordable_jobs(jobs[:1],data,a)
    with pytest.raises(ValueError,match='aggregate'):gear3_plan.affordable_jobs(jobs,data,a)
    p=tmp_path/'pilot.json';p.write_text(json.dumps({'status':'PASS'}))
    with pytest.raises(ValueError,match='source-bound'):gear3_plan.validate_pilot(tmp_path,p,{'runs':[]},tmp_path)


def test_full_archive_answer_join_all_branches_and_refusals(tmp_path,monkeypatch):
    source=Path.cwd();repo=tmp_path/'repo';repo.mkdir();native=Path(os.environ['G3_GHOST_ROOT'])
    closure=bundle.source_closure(source)
    for name in closure:
        target=repo/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((source/name).read_bytes())
    ledger_path=repo/'results/GPU_SPEND.json';monkeypatch.setattr(cost,'authoritative_ledger',lambda _:ledger_path)
    ledger=cost.CampaignLedger(ledger_path);ledger.enroll('constructed only',SPEC)
    transport(monkeypatch)
    original=fixtures.task(110,2,'process-record');donor=replace(original,task_id=digest('donor')[:32],evidence={**original.evidence,'earlier_handling':['accept']})
    d=fixtures.task(111,2,'process-record');targets={};answer_rows=[]
    for t,g in [(original,'test-writer'),(d,'other-test-writer')]:
        answer_rows.append({'task_id':t.task_id,'writer_component':g,'prompt_component':'p-'+g,'source_event':'e-'+g,'session':'s-'+g,'correct_choice':t.choices[0][0]})
        targets[t.task_id]={'record':asdict(t),'metadata':{'group':g,'event':'e-'+g,'session':'s-'+g,'dependencies':['prompt:p-'+g]}}
    eval_path=repo/'answers.json';eval_path.write_text(canonical({'targets':answer_rows}))
    for t in targets.values():t['evaluator']={'path':'answers.json','sha256':hashlib.sha256(eval_path.read_bytes()).hexdigest()}
    blocks=[];jobs=[];states=[];controls=None
    scenarios=[('a','A',[('ordinary',original)]),('b','B',[('other-writer',replace(original,evidence={**original.evidence,'earlier_handling':['accept']})),('artifact-only',replace(original,evidence_view='artifact',evidence={k:v for k,v in original.evidence.items() if k!='earlier_handling'}))]),('c','C',[('ordinary',original)]),('d','D',[('ordinary',d)])]
    ghost_destination=repo/'results/phase_2_4_stage_10/raw/interface-v3/ghost-public'
    for invocation,node,variants in scenarios:
        manifests=[]
        for condition,task in variants:
            m=manifest(node)
            pool=m['training']['coauthor-handling']
            for record,answer in list(zip(pool['public'],pool['answers'])):
                extra=deepcopy(record);extra['task_id']=digest(['process',record['task_id']])[:32];extra['evidence_view']='process-record';extra['evidence']['earlier_handling']=['edit']
                pool['public'].append(extra);pool['answers'].append({**answer,'task_id':extra['task_id']})
            m['block_id']=invocation+'-'+condition;m['source_hashes']=closure
            m['tasks']=[{'record':asdict(task),'envelope':None,'group':targets[task.task_id]['metadata']['group']}]
            m['units']=[{'task_id':task.task_id,**{k:v for k,v in u.items() if k!='task_id'}} for u in m['units']]
            m['scope']='constructed only; '+condition;manifests.append(m)
            train=m['training']['coauthor-handling'];fitted=human_baselines.fit(train['public'],train['answers'])
            controls={'sources':human_baselines.identity(),'training':train,'fitted':fitted,'fit_sha256':digest(fitted)}
            cell=digest([node,condition,task.family,task.evidence_view,task.question,task.contributor_role,task.exposure])
            blocks.append({'invocation':invocation,'block_id':m['block_id'],'manifest_sha256':digest(m),'task_ids':[task.task_id],'node':node,'condition':condition,'cell':cell})
        folder=repo/'bundles'/invocation;proof=bundle.build(repo,manifests,native,folder,mode='science',profiles=manifests[0]['profiles'],server_version='0.32.14')
        if not ghost_destination.exists():shutil.copytree(folder/'contents/ghost-public',ghost_destination)
        payload=json.loads((folder/'contents/JOB.json').read_text());reservation=ledger.reserve(invocation,node,['runners/gear3.py','round1',proof['archive_sha256']],{'job_sha256':digest(payload)},60,0,approval='constructed only')
        ledger.transition(invocation,'SUBMITTED',call_id='fc-'+invocation,evidence={'app_id':'ap-'+invocation})
        local=repo/'private/gear3/G3-S10-READER-1/invocations'/invocation;raw=local/'raw';raw.mkdir(parents=True)
        for m in manifests:batch.run_block(m,raw/'blocks'/m['block_id'])
        terminal={'status':'COMPLETE','reservation_sha256':digest(reservation),'source_archive_sha256':proof['archive_sha256'],'owner_ended':True}
        (raw/'TERMINAL.json').write_text(canonical(terminal));archive=storage.make_archive(raw,local/'OUTPUT.zip')
        for name,value in [('RESERVATION.json',reservation),('RETRIEVAL.json',archive),('REMOTE_TERMINAL.json',terminal)]: (local/name).write_text(canonical(value))
        ledger.transition(invocation,'COMPLETE',owner_ended=True,evidence={'full_archive_sha256':archive['archive_sha256']})
        jobs.append({'invocation':invocation,'node':node,'bundle':(folder/'INPUT.zip').relative_to(repo).as_posix(),'bundle_sha256':proof['archive_sha256'],'seconds':60,'startup_seconds':30,'overhead_cents':0,'dependencies':[] if node in {'A','D'} else ['a'],'failure_domain':node})
        states.append({'invocation':invocation,'status':'COMPLETE'})
    analysis={'schema':'gear3.analysis.1','readout':readouts.DEFINITION,'targets':targets,'history_donors':{original.task_id:{'group':'donor-writer','dependencies':['prompt:donor-prompt'],'public':donor.public(),'source_record':asdict(donor),'source_record_sha256':digest(asdict(donor))}},
              'selection':{'constructed_only':True,'excluded':[{'reason':'fixture unstarted tail'}]},'blocks':blocks,'cheap_controls':controls,
              'consumer_sources':freeze.consumer_sources(source),'local_source_root_sha256':digest(str(repo.resolve()))}
    (repo/'analysis.json').write_text(canonical(analysis));(repo/'pilot.json').write_text(canonical({'execution_sources':closure,'scope':'consumer fixture, never admission'}))
    plan={'schema':'gear3.execution_plan.2','approval':'constructed only','pilot':'pilot.json','pilot_sha256':'fixture','allowed_bundle_sha256':[j['bundle_sha256'] for j in jobs],'jobs':jobs,'analysis':'analysis.json','analysis_sha256':digest(analysis),'affordability':{}}
    path=repo/'PLAN.json';path.write_text(canonical(plan));seq=repo/'private/gear3/G3-S10-READER-1/sequences'/digest(plan);seq.mkdir(parents=True);(seq/'COMPLETE.json').write_text(canonical({'plan_sha256':digest(plan),'jobs':states}))
    before={j['invocation']:hashlib.sha256((repo/'private/gear3/G3-S10-READER-1/invocations'/j['invocation']/'OUTPUT.zip').read_bytes()).hexdigest() for j in jobs}
    monkeypatch.setattr(consumer.ollama if hasattr(consumer,'ollama') else __import__('runners.stage10.ollama',fromlist=['ollama']),'api',lambda *a,**k:pytest.fail('offline consumer called model'))
    public=consumer.consume(repo,path,repo,repo/'packet')
    assert {c['node'] for c in public['cells'].values()}==set('ABCD')
    assert len(public['cells'])==5 and (repo/'packet/WORKED_EXAMPLES.json').exists()
    assert 'word word' not in canonical(public) and 'earlier_handling' not in canonical(public)
    assert all(hashlib.sha256((repo/'private/gear3/G3-S10-READER-1/invocations'/k/'OUTPUT.zip').read_bytes()).hexdigest()==v for k,v in before.items())
    raw=eval_path.read_bytes();eval_path.write_bytes(raw+b' ')
    with pytest.raises(ValueError,match='evaluator bytes'):consumer.consume(repo,path,repo,repo/'bad-answers')
    eval_path.write_bytes(raw)
    bad=deepcopy(analysis);bad['targets'].pop(original.task_id)
    with pytest.raises(ValueError,match='roster'):consumer.validate_analysis(bad,plan)
    with pytest.raises(ValueError,match='source-bound'):gear3_plan.validate_pilot(repo,repo/'pilot.json',{'runs':[]},native)

def test_actual_source_affordable_freeze_and_naming_preflight(tmp_path,monkeypatch):
    import time
    from runners.stage10 import gear3_prepare,gear3_inputs,gear3_memory,reading_memory,ollama
    native=Path(os.environ['G3_GHOST_ROOT']);local=native.parents[4];repo=Path.cwd()
    prepared=tmp_path/'prepared';gear3_prepare.prepare(local,prepared)
    src=bundle.source_closure(repo);profiles={k:asdict(profile(k)) for k in batch.PINS}
    pilot={'schema':'gear3.pilot_admission.2','status':'PASS','execution_sources':src,'profiles':profiles,
        'route_timings':[{'family':family,'model':model,'arm':arm,'seconds':8} for family in ('coauthor-handling','ghost-reading','ghost-opportunity') for model in profiles for arm in batch.METHODS['P'] if family!='ghost-opportunity' or arm in batch.METHODS['A']],
        'service_duration_seconds':400,'valid_routes':[[family,model,arm] for family in ('coauthor-handling','ghost-reading','ghost-opportunity') for model in profiles for arm in batch.METHODS['P'] if family!='ghost-opportunity' or arm in batch.METHODS['A']]}
    pilot_path=tmp_path/'constructed-timing.json';pilot_path.write_text(canonical(pilot))
    # Literal-provider admission is tested separately. This isolates the entire
    # real, outcome-blind roster/cost/dependency/naming freeze behind that boundary.
    monkeypatch.setattr(freeze,'validate_pilot',lambda *a:deepcopy(pilot))
    monkeypatch.setattr(gear3_plan,'validate_pilot',lambda *a:deepcopy(pilot))
    ledger=tmp_path/'ledger.json';ledger.write_text(canonical({'runs':[]}));monkeypatch.setattr(freeze,'authoritative_ledger',lambda _:ledger)
    account_path=tmp_path/'account.json';account(account_path)
    plan=freeze.freeze(repo,local,prepared,pilot_path,account_path,tmp_path/'frozen')
    analysis=json.loads((repo/plan['analysis']).read_text())
    assert set(j['node'] for j in plan['jobs'])==set('ABCD')
    assert analysis['selection']['C_preflight']
    assert all(r['identical_except_descriptions'] for r in analysis['selection']['C_preflight'])
    assert len({tid for b in analysis['blocks'] for tid in b['task_ids']})==len(analysis['targets'])
    bad=deepcopy(plan);bad['jobs'][0]['seconds']=100000
    with pytest.raises(ValueError):gear3_plan.validate_plan(repo,bad,account(account_path),{'runs':[]},native)
    c=json.loads((prepared/'sources/CENSUS.json').read_text());row=next(r for r in gear3_inputs.roster(c)['C'] if r['record']['family']=='ghost-reading')
    task=__import__('runners.stage10.reader',fromlist=['from_record']).from_record(row['record']);pool=c['ghost']['reading']['training']
    lib=reading_memory.induce(native,pool['public'],pool['answers'],prior_observations=task.evidence['permitted_prior_artifacts'],prior_group=row['group'])
    for kind in ('empty','supported','near-cap'):
        library=deepcopy(lib)
        if kind=='empty':library['procedures']=[]
        elif not library['procedures']:
            library['procedures']=[{'id':'fragment0','definition':[0,1],'description':'Cells zero then one.','training_observations':3,'training_groups':2}]
        if kind=='near-cap':library['procedures'][0]['description']='Known complete description. '*130
        reps={};selections={}
        for name in ('grounded','opaque'):reps[name],selections[name]=gear3_memory.paired_representation(task,row['envelope'],pool['public'],pool['answers'],library,profile(),name)
        stripped=deepcopy(reps['grounded'])
        for p in stripped['procedures']:p.pop('description')
        assert stripped==reps['opaque']
        assert selections['grounded']['selected_ids']==selections['opaque']['selected_ids']
        assert len(canonical(reps['grounded']).encode())<=6000

def test_original_native_answer_joins_known_executed_future(tmp_path):
    from runners.stage10 import ghost,reading_source
    root=Path(os.environ['G3_GHOST_ROOT']);local=root.parents[4]
    all_rows,_=ghost.envelopes(root);targets={}
    for operation in ('opportunity','reading'):
        row=next(r for r in all_rows if r['envelope']['declared_context']['operation']==operation)
        task=ghost.task_from(row['envelope']);case=row['case_id'];actual={'case_id':case,'task_ids':[task.task_id]}
        if operation=='opportunity':actual['hidden_continuations']={'artifact':0,'legal':True,'attempted_option':0};correct='0'
        else:
            requested=task.evidence['target_request'];feasible=requested.get('feasible',list(range(8)))
            program=[];execution=reading_source.native_world(root).execute(program,feasible=tuple(feasible),budget=3)
            actual['true_production_record']={'hidden_continuations':{'artifact':execution.artifact,'target':requested['future_target'],'feasible':feasible,'program':program}};correct=str(execution.artifact)
        p=tmp_path/(case+'.json');p.write_text(canonical(actual))
        targets[task.task_id]={'record':asdict(task),'metadata':{'group':case,'event':task.task_id,'session':None,'dependencies':['constructor:fixture']},
             'evaluator':{'root':'campaign','kind':'ghost-native','path':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'case_id':case,'case_task_ids':[task.task_id]}}
        answers=consumer.joined_targets({'readout':readouts.DEFINITION,'targets':{task.task_id:targets[task.task_id]}},local,tmp_path)
        assert answers[task.task_id]['truth']==next(k for k,v in task.choices if v==correct)
        changed=deepcopy(actual);changed['case_id']='wrong';p.write_text(canonical(changed))
        with pytest.raises(ValueError,match='bytes changed'):consumer.joined_targets({'readout':readouts.DEFINITION,'targets':{task.task_id:targets[task.task_id]}},local,tmp_path)
