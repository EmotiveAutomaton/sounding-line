"""Local whole-plan evaluator join and complete-cell Gear 3 packet.

DESIGN CHECK: LESSONS3-5, inference2 and reader4/10 reread. NULL/ALTERNATIVE
retain original probability, choice, invalids, costs and exact common population.
Only validated complete blocks enter whole frozen cells. Missing counterparts,
changed answers/donors, duplicate events or mixed targets refuse. No model APIs.
"""
from collections import defaultdict,Counter
from copy import deepcopy
import hashlib,json
from pathlib import Path
from . import comparison,gear3_comparison,gear3_readouts,gear3_batch,gear3_io
from .contracts import digest
from .reader import from_record
from .queue import read
from .reading_source import persist

CLAIM_LIMITS=[
 'Human handling, constructed opportunity and constructed reading are separate populations and targets.',
 'Human R3 is a single-task approximate rule mixture, not a persistent likelihood-updated writer model. The proposer may infer from the supplied text.',
 'History means within-session action history, not enduring personal values or historical intent.',
 'Procedure memory measures representation assistance; reconstructed routes need not be historical routes.',
 'Native proposed support, evidence fit, legal reconstruction, visible artifact match and future prediction are distinct. Reconstruction success is not a prediction-validity gate.',
 'All sources are previously exposed descriptive evaluations. Model size is not isolated from the model package.',
 'Fewer than ten dependency components warrant descriptive component contrasts and leave-one-component-out ranges only.',
 'A null cannot close the general theory; same-confidence choice and constant-collapse checks are secondary readout diagnostics, not reasoning ablations.']


def joined_targets(analysis,root,repo=None):
    if analysis['readout']!=gear3_readouts.DEFINITION:raise ValueError('pre-outcome readout definition differs')
    loaded={};answers={}
    for tid,target in analysis['targets'].items():
        source=target['evaluator'];owner=root if source.get('root','local')=='local' else repo
        if owner is None:raise ValueError('campaign evaluator owner unavailable')
        path=(owner/source['path']).resolve()
        if not path.is_relative_to(owner.resolve()):raise ValueError('evaluator path escapes original local repository')
        key=str(path)
        record=from_record(target['record'])
        if source.get('kind')=='ghost-native':
            from .reading_source import target_from_record,native_world
            raw=path.read_bytes()
            if hashlib.sha256(raw).hexdigest()!=source['sha256']:raise ValueError('frozen native evaluator bytes changed')
            actual=json.loads(raw);case=source['case_id']
            if target['metadata']['group']!=case or actual['case_id']!=case or set(actual['task_ids'])!=set(source['case_task_ids']) or tid not in actual['task_ids']:
                raise ValueError('native evaluator case membership differs')
            if record.family=='ghost-reading':
                world=native_world(root/'results/phase_2_4_stage_10/raw/interface-v3/ghost-public')
                truth=target_from_record(actual,case,record,set(source['case_task_ids']),world)
            elif record.family=='ghost-opportunity':
                future=actual['hidden_continuations']
                if type(future['artifact']) is not int or future['artifact'] not in (0,1) or type(future['legal']) is not bool or future['attempted_option'] not in (0,1):
                    raise ValueError('original enacted opportunity outcome malformed')
                truth=next(k for k,v in record.choices if v==str(future['artifact']))
            else:raise ValueError('native evaluator attached to wrong family')
            answers[tid]={**target['metadata'],'truth':truth};continue
        if key not in loaded:
            raw=path.read_bytes()
            if hashlib.sha256(raw).hexdigest()!=source['sha256']:raise ValueError('frozen evaluator bytes changed')
            rows=json.loads(raw)['targets'];lookup={r['task_id']:r for r in rows}
            if len(rows)!=len(lookup):raise ValueError('duplicate evaluator task')
            loaded[key]=lookup
        actual=loaded[key].get(tid)
        if actual is None:raise ValueError('missing original evaluator outcome')
        record=from_record(target['record'])
        if record.task_id!=tid:raise ValueError('target identity differs')
        meta=target['metadata'];human=record.family=='coauthor-handling'
        if actual['writer_component' if human else 'case_id']!=meta['group']:
            raise ValueError('evaluator source group differs')
        if human and (actual.get('session')!=meta.get('session') or actual['source_event']!=meta['event'] or 'prompt:'+actual['prompt_component'] not in meta['dependencies']):
            raise ValueError('evaluator event/prompt differs')
        answers[tid]={**meta,'truth':actual['correct_choice']}
    return answers


def subset(cell,ids):
    # Rebuild from retained original predictions; never slice a cached summary.
    return {k:v for k,v in cell.items() if k in ids}


def summarize(records,analysis,answers,dispositions,costs):
    """records are verified full block manifests + original immutable unit results."""
    buckets=defaultdict(list);diagnostics=[];seen=set()
    for item in records:
        m=item['manifest'];condition=item['condition']
        tasks,profiles=gear3_batch.validate(m)
        if len(item['units'])!=len(m['units']):raise ValueError('incomplete returned block')
        units={digest(r['unit']):r for r in item['units']}
        if len(units)!=len(item['units']) or set(units)!={digest(u) for u in m['units']}:
            raise ValueError('missing or duplicated unit counterpart')
        for u in m['units']:
            task,row=tasks[u['task_id']];key=(m['node'],condition,task.family,task.evidence_view,task.question,task.contributor_role,task.exposure)
            unique=key+(task.task_id,u['model'],u['arm'])
            if unique in seen:raise ValueError('duplicated task/event across blocks')
            seen.add(unique)
            target=analysis['targets'].get(task.task_id)
            if target is None or row['group']!=target['metadata']['group']:raise ValueError('task absent from frozen analysis population')
            original=from_record(target['record'])
            if condition=='ordinary' and original!=task:raise ValueError('frozen original public evidence differs')
            result=units[digest(u)]['result'];status=result['status']
            if status not in {'VALID','INVALID','MISMATCH','EXECUTOR_INVALID'}:raise ValueError('unknown forecast disposition')
            if status!='VALID' and result.get('forecast') is not None:raise ValueError('invalid row has substituted forecast')
            prediction={'task_public':task.public(),'status':'VALID' if status=='VALID' else 'INVALID','forecast':result.get('forecast')}
            buckets[key].append((task,u['model']+'-'+u['arm'],prediction))
    cells={};details={};contrasts={}
    def make(tasks,predictions,pop):
        return comparison.cell(tasks,{t.task_id:answers[t.task_id] for t in tasks},predictions,pop)
    for key,rows in sorted(buckets.items()):
        node,condition,family,view,question,role,exposure=key;pop=digest([family,question,role,exposure])
        tasks={t.task_id:t for t,_,_ in rows};methods=defaultdict(dict)
        for task,method,prediction in rows:methods[method][task.task_id]=prediction
        expected={model+'-'+arm for model in ('9b','27b') for arm in gear3_batch.METHODS[node]}
        if set(methods)!=expected or any(set(p)!=set(tasks) for p in methods.values()):raise ValueError('incomplete scientific comparison cell')
        label=digest(key)[:24];base={k:make(list(tasks.values()),v,pop) for k,v in methods.items()}
        extras={}
        if family=='coauthor-handling':
            for method,pred in methods.items():
                projected={tid:{**p,'forecast':gear3_readouts.same_confidence(tasks[tid],p['status'],p['forecast'])} for tid,p in pred.items()}
                extras[method+'-same-confidence']=make(list(tasks.values()),projected,pop)
        controls={}
        if family=='coauthor-handling':
            from . import human_baselines
            for arm in human_baselines.ARMS:
                preds={tid:{'task_public':task.public(),'status':'VALID','forecast':human_baselines.predict(task,analysis['cheap_controls']['fitted'],arm)} for tid,task in tasks.items()}
                controls[arm]=make(list(tasks.values()),preds,pop)
        else:
            for arm in ('uniform','first-option'):
                preds={}
                for tid,task in tasks.items():
                    choice=task.choices[0][0];probs={k:(1/len(task.choices) if arm=='uniform' else float(k==choice)) for k,_ in task.choices}
                    preds[tid]={'task_public':task.public(),'status':'VALID','forecast':{'choice':choice,'probabilities':probs,'insufficient_evidence':False,'explanation':'Fixed cheap reference, no model call.'}}
                controls[arm]=make(list(tasks.values()),preds,pop)
        cells[label]={'node':node,'condition':condition,'family':family,'view':view,'question':question,
                      'methods':base,'cheap_controls':controls,'secondary_same_confidence':extras,
                      'counts':{'events':len({answers[t]['event'] for t in tasks}),
                                'writers':len({answers[t]['group'] for t in tasks}) if family=='coauthor-handling' else 0,
                                'sessions':len({answers[t]['session'] for t in tasks if answers[t].get('session')}),
                                'prompts':len({d for t in tasks for d in answers[t]['dependencies'] if d.startswith('prompt:')}),
                                'ghost_cases':len({answers[t]['group'] for t in tasks}) if family.startswith('ghost-') else 0}}
        cells[label]['outcome_class_counts']=dict(Counter(dict(tasks[tid].choices)[answers[tid]['truth']] for tid in tasks))
        details[key]=(tasks,methods,pop)
        if node in {'A','D'}:
            result=gear3_comparison.interaction({k:base[k] for k in ('9b-R2','9b-R3','27b-R2','27b-R3')})
            result['direct_model_package_difference']=comparison.paired(base['27b-R0'],base['9b-R0'])
            result['structured_versus_direct']={model:comparison.paired(base[model+'-R3'],base[model+'-R0']) for model in ('9b','27b')}
            contrasts[label]=result
        if node=='C':
            contrasts[label]={model:{'grounded_vs_opaque':comparison.paired(base[model+'-R4-grounded'],base[model+'-R4-opaque']),
                       **{name+'_vs_examples':comparison.paired(base[model+'-R4-'+name],base[model+'-R1-memory']) for name in ('opaque','grounded')}} for model in ('9b','27b')}
    # C reuses the exact admitted A task/method forecasts on its frozen subset.
    for key,(tasks,methods,pop) in details.items():
        if key[0]!='C':continue
        akey=('A','ordinary',*key[2:])
        if akey not in details:raise ValueError('memory comparison lacks admitted A cell')
        original_tasks,original_methods,_=details[akey];ids=set(tasks)
        if not ids<=set(original_tasks):raise ValueError('memory comparison target absent from A')
        label=digest(key)[:24]
        for model in ('9b','27b'):
            for naming in ('opaque','grounded'):
                memory=make(list(tasks.values()),methods[model+'-R4-'+naming],pop)
                for base in ('R0','R3'):
                    contrasts[label][model][naming+'_vs_'+base]=comparison.paired(memory,make(list(tasks.values()),subset(original_methods[model+'-'+base],ids),pop))
    # Compare B against the exact A subset, under the narrow declared evidence delta.
    for key,(tasks,methods,pop) in details.items():
        if key[0]!='B':continue
        akey=('A','ordinary',key[2],'process-record',*key[4:])
        if akey not in details:raise ValueError('history intervention lacks admitted A cell')
        original_tasks,original_methods,_=details[akey];ids=set(tasks)
        if not ids<=set(original_tasks):raise ValueError('history targets absent from admitted A')
        donors={tid:analysis['history_donors'][tid] for tid in ids}
        cells[digest(key)[:24]]['matched_correct_history']={method:make([original_tasks[t] for t in sorted(ids)],subset(original_methods[method],ids),pop)['summary'] for method in methods}
        from . import human_baselines
        persistence={tid:{'task_public':original_tasks[tid].public(),'status':'VALID','forecast':human_baselines.predict(original_tasks[tid],analysis['cheap_controls']['fitted'],'previous-handling')} for tid in ids}
        cells[digest(key)[:24]]['matched_correct_history_persistence']=make([original_tasks[t] for t in sorted(ids)],persistence,pop)['summary']
        contrasts[digest(key)[:24]]={method:gear3_comparison.history_contrast(
            make([original_tasks[t] for t in sorted(ids)],subset(original_methods[method],ids),pop),
            make(list(tasks.values()),pred,pop),condition=key[1],donors=donors) for method,pred in methods.items()}
    return {'schema':'gear3.results.1','cells':cells,'contrasts':contrasts,'branch_dispositions':dispositions,
            'cost_account':costs,'claim_limits':CLAIM_LIMITS,'readout_definition':gear3_readouts.DEFINITION,
            'selection':analysis['selection'],'diagnostics':diagnostics,'public_claim':'descriptive package comparisons only; curator synthesis pending'}


def cost_projection(data):
    from runners.gear3_campaign import CAMPAIGN,CampaignLedger,NODE_CENTS
    rows=[r for r in data['runs'] if r.get('campaign_id')==CAMPAIGN]
    return {'booked_by_node':CampaignLedger.totals(data),'original_reserved_cents':sum(r['reserved_cents'] for r in rows),
            'booked_cents':sum(r['booked_cents'] for r in rows),
            'provider_confirmed_cents':sum(r['provider_charge_cents'] for r in rows if r['provider_charge_cents'] is not None),
            'service_estimated_cents':sum(r['service_estimate_cents'] for r in rows if r['service_estimate_cents'] is not None),
            'unresolved_booked_cents':sum(r['booked_cents'] for r in rows if r['provider_charge_cents'] is None),
            'unused_campaign_cents':5000-sum(r['booked_cents'] for r in rows),'branch_caps_cents':NODE_CENTS,
            'basis':'original reservations, service estimates and final provider charges are separate; credits do not raise the campaign cap'}


def validate_analysis(analysis,plan):
    required={'schema','readout','targets','history_donors','selection','blocks','cheap_controls','consumer_sources','local_source_root_sha256'}
    if set(analysis)!=required or analysis['schema']!='gear3.analysis.1' or analysis['readout']!=gear3_readouts.DEFINITION:
        raise ValueError('complete pre-outcome analysis freeze required')
    if not analysis['targets'] or not analysis['blocks']:raise ValueError('empty analysis population')
    from .gear3_freeze import consumer_sources
    if analysis['consumer_sources']!=consumer_sources(Path(__file__).resolve().parents[2]):raise ValueError('incomplete consumer source freeze')
    for name,expected in analysis['consumer_sources'].items():
        repo=Path(__file__).resolve().parents[2];path=(repo/name).resolve()
        if not path.is_relative_to(repo) or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
            raise ValueError('consumer differs from pre-outcome freeze')
    identifiers={j['invocation'] for j in plan['jobs']}
    if {b['invocation'] for b in analysis['blocks']}!=identifiers:raise ValueError('analysis misses planned jobs')
    keys=[(b['invocation'],b['block_id']) for b in analysis['blocks']]
    if len(keys)!=len(set(keys)):raise ValueError('duplicated analysis block')
    if set(analysis['targets'])!={tid for b in analysis['blocks'] for tid in b['task_ids']}:
        raise ValueError('analysis outcome roster differs from declared blocks')
    for target in analysis['targets'].values():
        if not {'group','event','session','dependencies'}<=set(target['metadata']):raise ValueError('missing analysis dependencies')
    from . import human_baselines
    controls=analysis['cheap_controls']
    if controls['sources']!=human_baselines.identity() or digest(controls['fitted'])!=controls['fit_sha256']:
        raise ValueError('cheap controls source or frozen fit differs')
    if controls['fitted']!=human_baselines.fit(controls['training']['public'],controls['training']['answers']):
        raise ValueError('cheap controls do not reproduce from permitted training')


def route_diagnostics(task,route):
    rows=[]
    for path in sorted(route.rglob('EXECUTION.json')):
        execution=read(path)
        if task.family=='coauthor-handling':
            attempt=path.parent/'proposal/ATTEMPT.json'
            if not attempt.exists():continue
            proposal=read(attempt).get('proposal')
            if proposal is None:continue
            rows.append({'round':path.relative_to(route).as_posix(),**gear3_readouts.human_diagnostic(task,proposal['candidates'],{'choice':proposal['choice']})})
        else:
            response=execution.get('response',execution)
            # Retain all distinct native diagnostics verbatim; no reconstruction
            # gate is invented and future truth is joined only by the scorer.
            rows.append({'round':path.relative_to(route).as_posix(),'native_execution':response,
                         'scope':'proposed support, observation fit and reconstruction remain distinct from outcome accuracy'})
    return rows


def consume(repo,plan_path,local_root,output):
    """Full transport -> semantic replay -> frozen local answers -> final packet."""
    from runners.gear3_campaign import CampaignLedger,authoritative_ledger
    from runners.gear3_plan import verify_invocation,owned
    import zipfile
    plan=read(plan_path);analysis=read(owned(repo,plan['analysis']))
    if digest(analysis)!=plan['analysis_sha256']:raise ValueError('analysis binding changed')
    validate_analysis(analysis,plan)
    if digest(str(local_root.resolve()))!=analysis['local_source_root_sha256']:raise ValueError('local evaluator owner differs')
    ledger=CampaignLedger(authoritative_ledger(repo))
    with ledger.transaction() as data:data=deepcopy(data)
    native=local_root/'results/phase_2_4_stage_10/raw/interface-v3/ghost-public'
    sequence=read(repo/'private/gear3/G3-S10-READER-1/sequences'/digest(plan)/'COMPLETE.json')
    if sequence['plan_sha256']!=digest(plan):raise ValueError('finite sequence differs')
    states={r['invocation']:r for r in sequence['jobs']}
    if len(states)!=len(sequence['jobs']) or set(states)!={j['invocation'] for j in plan['jobs']}:raise ValueError('sequence omitted job disposition')
    records=[];dispositions=[];diagnostics=[];expected={(b['invocation'],b['block_id']):b for b in analysis['blocks']}
    for job in plan['jobs']:
        status=states[job['invocation']]['status'];dispositions.append(states[job['invocation']])
        if status=='NOT_RUN':continue
        if status not in {'COMPLETE','FAILED'}:raise ValueError('unresolved job ownership')
        row,payload,terminal,receipt,restored=verify_invocation(repo,job['invocation'],owned(repo,job['bundle']),data,native)
        if row['status']!=status:raise ValueError('sequence terminal differs from ledger')
        with zipfile.ZipFile(owned(repo,job['bundle'])) as z:
            for name in payload['blocks']:
                manifest=json.loads(z.read(name));binding=expected[(job['invocation'],manifest['block_id'])]
                if digest(manifest)!=binding['manifest_sha256'] or [r['record']['task_id'] for r in manifest['tasks']]!=binding['task_ids']:
                    raise ValueError('returned population differs from analysis freeze')
                if status=='FAILED':continue  # no partial scientific score
                folder=restored/'blocks'/manifest['block_id'];units=[]
                for unit in manifest['units']:
                    base=folder/'units'/digest(unit)[:32];units.append(read(base/'UNIT.json'))
                    task=from_record(next(r['record'] for r in manifest['tasks'] if r['record']['task_id']==unit['task_id']))
                    diagnostics.append({'invocation':job['invocation'],'unit':unit,'rows':route_diagnostics(task,base/'route'),'costs':route_costs(base/'route'),
                                        'family':task.family,'node':manifest['node']})
                records.append({'manifest':manifest,'units':units,'condition':binding['condition'],'invocation':job['invocation']})
    # An interrupted cell is a disposition, not a reduced convenience sample.
    failed_cells={b['cell'] for b in analysis['blocks'] if states[b['invocation']]['status']!='COMPLETE'}
    if failed_cells:
        failed_a_families={analysis['targets'][tid]['record']['family'] for b in analysis['blocks'] if b['node']=='A' and b['cell'] in failed_cells for tid in b['task_ids']}
        failed_cells.update(b['cell'] for b in analysis['blocks'] if b['node'] in {'B','C'} and any(analysis['targets'][tid]['record']['family'] in failed_a_families for tid in b['task_ids']))
        records=[r for r in records if expected[(r['invocation'],r['manifest']['block_id'])]['cell'] not in failed_cells]
        dispositions.extend({'cell':c,'status':'INCOMPLETE_NOT_SCORED'} for c in sorted(failed_cells))
    answers=joined_targets(analysis,local_root,repo)
    packet=summarize(records,analysis,answers,dispositions,cost_projection(data))
    packet.update(plan_sha256=digest(plan),analysis_sha256=digest(analysis),diagnostics=diagnostics,
                  verifier_sources=analysis['consumer_sources'],producer_sources=read(owned(repo,plan['pilot']))['execution_sources'])
    persist(output/'RESULTS.json',packet)
    # Public projection removes all original task text, options, source IDs and raw
    # replies. Original evidence and worked examples are retained privately.
    public={k:packet[k] for k in ('schema','plan_sha256','analysis_sha256','claim_limits','readout_definition','cost_account','branch_dispositions')}
    public['cells']={k:{**{n:v for n,v in c.items() if n not in {'methods','cheap_controls','secondary_same_confidence'}},
        **{n:{m:x['summary'] for m,x in c[n].items()} for n in ('methods','cheap_controls','secondary_same_confidence')}} for k,c in packet['cells'].items()}
    public['observed_route_costs']={}
    for item in diagnostics:
        key=item['node']+'/'+item['family']+'/'+item['unit']['model']+'/'+item['unit']['arm']
        values=public['observed_route_costs'].setdefault(key,{k:0 for k in item['costs']})
        for name,value in item['costs'].items():values[name]+=value
    public['contrasts']={k:public_contrast(v) for k,v in packet['contrasts'].items()}
    persist(output/'PUBLIC_RESULTS.json',public)
    examples=[]
    for label,c in packet['cells'].items():
        first=next(iter(c['methods'].values()))['rows'][0]['task_id']
        examples.append({'cell':label,'task':analysis['targets'][first]['record'],'answer':answers[first],
                         'methods':{m:next(r for r in x['rows'] if r['task_id']==first) for m,x in c['methods'].items()}})
    persist(output/'WORKED_EXAMPLES.json',examples)
    report=['# Gear 3 Round 1 complete selected packet','',
            'Question: does the larger reader package change direct prediction, deliberate rule execution, use of session history or reusable representations?',
            'METHOD: complete frozen paired cells, semantically replayed original responses and native executions, joined locally to byte-frozen outcomes. Writer/case balanced descriptive scores; connected dependencies retained.','',
            'The machine-readable packet reports direct R0 differences, R2/R3 interactions, R3 versus R0, original and same-confidence human forecasts, session-history contrasts, naming/memory contrasts, cheap controls, separate native execution diagnostics and the complete cost account.',
            'RESULTS: PUBLIC_RESULTS.json contains complete aggregate contrasts; RESULTS.json and WORKED_EXAMPLES.json retain private evidence. Failed or unstarted cells have explicit dispositions and no invented predictions.','',
            'Interpretation remains scoped to these exposed sources and model packages. A next experiment requires curator synthesis of the finished contrasts; persistent maker hypotheses, human causal mechanism, isolated parameter-count effects and general-theory closure remain unmeasured.','',*['- '+x for x in CLAIM_LIMITS]]
    (output/'REPORT.md').write_text('\n'.join(report)+'\n',encoding='utf8',newline='\n')
    persist(output/'COMPLETE.json',{'status':'COMPLETE','plan_sha256':digest(plan),'files':gear3_io.inventory(output),
                                 'scope':'complete selected descriptive packet; internal write-through and curator synthesis follow'})
    return public


def public_contrast(value):
    if isinstance(value,list):return [public_contrast(x) for x in value]
    if not isinstance(value,dict):return value
    return {k:public_contrast(v) for k,v in value.items() if k not in {'component_contrasts','common_components','validated_delta_bindings'}}


def route_costs(route):
    totals={'model_calls':0,'input_tokens':0,'generated_tokens':0,'server_duration_seconds':0.0,'executor_wall_seconds':0.0}
    for p in route.rglob('ATTEMPT.json'):
        attempt=read(p);c=attempt['cost'];totals['model_calls']+=1
        totals['input_tokens']+=c['prompt_eval_count'];totals['generated_tokens']+=c['eval_count']
        totals['server_duration_seconds']+=c['total_duration']/1e9
    for p in route.rglob('EXECUTION.json'):
        execution=read(p);totals['executor_wall_seconds']+=execution.get('response',{}).get('wall_seconds',0)
    return totals
