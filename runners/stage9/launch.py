"""Fail-closed launch acceptance for the manually reviewed scientific workload.

DESIGN CHECK: LESSONS sections 3/5; I01-I06/X01/X02/X06/X07/X12.
NULL: a bare accepted flag, empty evidence, missing real runs, changed source,
absent failed-seed coverage or invented idle delivery cannot start science.
ALTERNATIVE: the full concrete reviewed workload, independently gated evidence,
actual matching scheduler dress rehearsal and measured forecast all reconcile.
Bands: all structural/evidence checks pass, or refusal with the missing condition.
The operator still reviews study meaning; a schema cannot certify that judgment.
"""
from datetime import datetime,timezone
import math
from pathlib import Path

from runners.stage9.common import REPO,ROOT,read,freeze,digest,file_hash,closure

REQUIRED = {'manual_review','fixtures','sources','packages','splits','forecast','wake','interruption','dress_rehearsal'}
CORPORA = {'argrewrite','coauthor','scholawrite','iterater','arxivedits','shelley_godwin',
           'woolf','broll','drawings_things','commitbench','newsedits2','genius'}
CARDS = {f'{prefix}{i:02d}' for prefix,count in (('I',6),('C',8),('M',6),('T',6),('H',8),('S',4),('B',4))
         for i in range(1,count+1)}


def require(condition,message):
    if not condition:raise ValueError(message)


def checked(pointer):
    require(isinstance(pointer,dict) and set(pointer)=={'path','sha256'},'explicit evidence path and content hash required')
    path=(REPO/pointer['path']).resolve()
    require(path.is_relative_to(REPO) and path.is_file() and not path.is_symlink(),'launch evidence must be a real repository file')
    require(file_hash(path)==pointer['sha256'],'launch evidence changed: '+pointer['path'])
    return read(path)


def handler_operation(job):
    """Match executed operations within dispatchers, not just their module names."""
    module=job['module'];args=job['arguments'];operation=None;family=None;package_kind=None
    if module=='runners.stage9.closure_probe':
        from .closure_probe import RUNTIMES
        require(args.count('--runtime')==1,'isolation rehearsal must name one runtime')
        index=args.index('--runtime')
        require(index+1<len(args) and args[index+1] in RUNTIMES,'unknown isolation runtime')
        operation='probe-'+args[index+1]
    if module=='runners.stage9.disposition_jobs':
        require(args.count('--card')==1,'not-run rehearsal must name one card')
        index=args.index('--card')
        require(index+1<len(args) and args[index+1] in CARDS,'unknown not-run card')
        operation='not-run-'+args[index+1]
    if module=='runners.stage9.training_jobs':
        require(bool(args) and args[0] in ('fit','collect','pack'),'training dispatcher operation missing')
        operation=args[0]
    if module in ('runners.stage9.repair_jobs','runners.stage9.repair_admission'):
        choices=('fit','predict','select') if module.endswith('repair_jobs') else ('calibrate','evaluate')
        require(bool(args) and args[0] in choices,'repair dispatcher operation missing')
        operation=args[0]
    human_operations={'runners.stage9.revision_predictions':('fit','predict'),
        'runners.stage9.revision_analysis':('select','evaluate'),
        'runners.stage9.broll_jobs':('prepare','fit','predict','select','evaluate'),
        'runners.stage9.commit_jobs':('prepare','fit','predict','select','evaluate'),
        'runners.stage9.record_jobs':('prepare','fit','predict','select','evaluate','collect'),
        'runners.stage9.genetic_jobs':('prepare','controls','neural','evaluate')}
    if module in human_operations:
        require(bool(args) and args[0] in human_operations[module],'human dispatcher operation missing')
        operation=args[0]
    for flag in ('--operation','--family','--package-kind'):
        require(args.count(flag)<=1,'duplicate dispatcher identity option')
        if flag in args:
            index=args.index(flag)
            require(index+1<len(args) and not args[index+1].startswith('--'),'missing dispatcher identity value')
            if flag=='--operation':
                require(operation is None or operation==args[index+1],'conflicting dispatcher operation')
                operation=args[index+1]
            elif flag=='--family':family=args[index+1]
            else:package_kind=args[index+1]
    if module=='runners.stage9.training_jobs':
        require(family in ('qwen','smollm'),'training rehearsal must name its actual family')
    if module=='runners.stage9.artifact_comparisons':
        from .artifact_comparisons import selected_views, VIEWS
        require(args.count('--views')<=1,'duplicate comparator evidence views')
        views=VIEWS
        if '--views' in args:
            index=args.index('--views')+1;end=index
            while end<len(args) and not args[end].startswith('--'):end+=1
            views=selected_views(args[index:end])
        require(operation is None,'artifact comparison has no separate operation flag')
        operation='predict-views-'+'+'.join(views)
    if module=='runners.stage9.purpose_jobs':
        require(args.count('--consumer')<=1,'duplicate maker consumer')
        consumer='purpose'
        if '--consumer' in args:
            index=args.index('--consumer')
            require(index+1<len(args) and args[index+1] in ('purpose','proposal','transfer','goal','cue','ambiguity','constraint','familiarity','selection','familiarity-entry'),'unknown maker consumer')
            consumer=args[index+1]
        require(operation is None,'maker consumer has no separate operation flag')
        operation='predict-'+consumer
    if module=='runners.stage9.genetic_jobs' and operation=='neural':
        require(family in ('qwen','smollm'),'genetic rehearsal must name its actual family')
        package_kind=package_kind or 'fitted'
        require(package_kind in ('base','archive','fitted'),'unknown genetic reader package kind')
    if module in ('runners.stage9.artifact_analysis','runners.stage9.ambiguity_analysis','runners.stage9.familiarity_analysis','runners.stage9.familiarity_entry_analysis'):
        require(operation in ('select','evaluate'),'analysis rehearsal must name its actual operation')
    if module=='runners.stage9.paired_artifact_analysis':
        require(operation is None,'paired analysis has no separate operation flag')
        operation='paired-analysis'
    if module=='runners.stage9.rival_plan':
        require(operation is None and args.count('--declaration')==1,'plan binding requires one explicit declaration')
        index=args.index('--declaration')
        require(index+1<len(args),'plan binding declaration path missing')
        path=(REPO/args[index+1]).resolve()
        require(path.is_relative_to(REPO) and path.is_file() and not path.is_symlink(),'plan declaration must be a real repository file')
        declaration=read(path)
        kinds={'queries':'selection','template':'evaluation','paired_template':'paired','analysis_template':'consumer'}
        present=[key for key in kinds if key in declaration]
        require(len(present)==1,'plan binding must have one explicit operation')
        operation='bind-'+kinds[present[0]]
        if present==['analysis_template']:
            from .analysis_plan_contracts import validate
            template=declaration[present[0]]
            validate(template,declaration.get('analysis_contract'),declaration.get('role'))
            operation+='-'+declaration['analysis_contract']+'-'+template['operation']
        if 'query_contract' in declaration:
            from .rival_plan import QUERY_CONTRACTS
            require(present==['queries'] and declaration['query_contract'] in QUERY_CONTRACTS,'unknown or misplaced binding task contract')
            operation+='-'+declaration['query_contract']
        if present!=['queries'] or 'query_contract' in declaration:
            require(args.count('--declaration-sha256')==1,'typed binding requires its original declaration checksum')
            index=args.index('--declaration-sha256')
            require(index+1<len(args) and args[index+1]==file_hash(path),'binding declaration checksum changed')
    if module=='runners.stage9.generation_cases':
        require(args.count('--population')==1,'generation preparation must name its population')
        index=args.index('--population')
        require(index+1<len(args) and args[index+1] in ('original','expanded'),'unknown generation population')
        operation='prepare-'+args[index+1]
    if module=='runners.stage9.neural_operations':
        package_kind=package_kind or 'fitted'
        require(package_kind in ('fitted','base','archive'),'unknown reader package kind')
    if module in human_operations and operation=='predict':
        require(args.count('--lane')==1,'human prediction rehearsal must name its partition')
        index=args.index('--lane')
        require(index+1<len(args) and args[index+1] in ('development','evaluation'),'unknown human prediction partition')
        operation+='-'+args[index+1]
    if module=='runners.stage9.record_jobs' and operation=='prepare':
        require(args.count('--dataset')==1,'prospective preparation must name its dataset')
        index=args.index('--dataset')
        require(index+1<len(args) and args[index+1] in ('coauthor','scholawrite'),'unsupported prospective dataset')
        dataset=args[index+1];operation+='-'+dataset
        if dataset=='scholawrite':
            require(args.count('--fold')==1,'ScholaWrite preparation requires a project fold')
            index=args.index('--fold')
            require(index+1<len(args) and args[index+1] in tuple(map(str,range(5))),'unknown ScholaWrite outer fold')
            operation+='-fold-'+args[index+1]
        else:require('--fold' not in args,'CoAuthor has no project rotation')
    if module=='runners.stage9.iterater_cases':
        require(args.count('--study')<=1,'duplicate HUMAN study')
        study='legacy-execution-pilot'
        if '--study' in args:
            index=args.index('--study')
            require(index+1<len(args) and args[index+1] in ('within','leave-arxiv','leave-news','leave-wiki'),'unknown HUMAN study')
            study=args[index+1]
        operation='prepare-'+study
    return module,operation,family,package_kind


def verify_forecast(forecast,plan):
    jobs={j['id']:j for j in plan['jobs']}
    require(set(forecast['jobs'])==set(jobs),'forecast must enumerate every actual job')
    gpu=cpu=0.
    for key,row in forecast['jobs'].items():
        for field in ('measured_seconds','measured_units','planned_units','overhead_seconds','multiplier','forecast_seconds'):
            require(type(row.get(field)) in (int,float) and math.isfinite(row[field]) and row[field]>=0,'invalid measured forecast component')
        require(row['measured_units']>0 and row['planned_units']>0 and 1<=row['multiplier']<=3,
                'positive actual pilot units and explicit bounded planning multiplier required')
        measured=checked(row['pilot'])
        value=measured
        for field in row['measured_field']:
            require(isinstance(value,dict) and field in value,'pilot measurement path is absent')
            value=value[field]
        require(type(value) in (int,float) and value==row['measured_seconds'],'forecast differs from actual pilot measurement')
        expected=row['measured_seconds']/row['measured_units']*row['planned_units']*row['multiplier']+row['overhead_seconds']
        require(math.isclose(expected,row['forecast_seconds'],rel_tol=1e-9,abs_tol=1e-6),'forecast arithmetic does not reconcile')
        if jobs[key]['resource']=='gpu':gpu+=expected
        else:cpu+=expected
        require(math.isclose(jobs[key]['estimated_gpu_seconds'],expected if jobs[key]['resource']=='gpu' else 0.,abs_tol=1e-6),
                'manifest GPU forecast differs from measured ledger')
    prior=forecast['preparation_gpu_reserved_seconds']
    require(type(prior) in (int,float) and math.isfinite(prior) and prior>=0,'preparation GPU cost is required')
    require(prior+gpu<=92*3600,'preparation plus planned GPU reservation exceeds the stage envelope')
    # The present scheduler is serial. Do not subtract imagined CPU/GPU overlap.
    require(forecast['scheduling']=='serial' and forecast['remaining_wall_seconds']>=gpu+cpu,
            'forecast claims concurrency the current scheduler does not implement')
    remaining=plan['horizon_epoch']-forecast['forecast_at']
    require(forecast['remaining_wall_seconds']<=remaining,'finite forecast exceeds remaining campaign horizon')
    if plan.get('execution_scope'):
        import time
        require(forecast['forecast_at']<=time.time() and time.time()+gpu+cpu<=plan['horizon_epoch'],
                'tranche forecast is stale or cannot fit the original live horizon')
    require(forecast['initial_queue_seconds']>=18*3600 or bool(forecast.get('underfill_reason')),
            'roughly one-day initial depth or a concrete underfill explanation is required')


def validate(plan,evidence):
    if 'overnight_continuation' in plan:
        from .overnight import validate as validate_overnight
        return validate_overnight(plan, evidence)
    from runners.stage9.queue import validate_manifest,verify_sources,verify_committed
    from runners.stage9.training_jobs import FITS
    require(plan['kind']=='science','launch acceptance is only for scientific manifests')
    validate_manifest(plan);verify_sources(plan['sources'])
    from .tranche import scope as tranche_scope
    tranche=tranche_scope(plan)
    from runners.stage9.closure_raw import validate_scientific_reviews
    validate_scientific_reviews(plan,{j['id']:j for j in plan['jobs']})
    require(set(evidence)==REQUIRED,'launch evidence set is empty, incomplete or unregistered')
    objects={key:checked(value) for key,value in evidence.items()}
    review=objects['manual_review'];jobs={j['id']:j for j in plan['jobs']}
    require(review['manifest_sha256']==digest(plan) and set(review['jobs'])==set(jobs),'manual review is not tied to every concrete cell')
    require(set(review['cards'])==CARDS,'manual review omits a commissioned card')
    from runners.stage9.closure_coverage import validate_mapping
    coverage=validate_mapping(plan)
    require(coverage['cards']==review['cards'],'final card coverage differs from the manual launch review')
    for key,row in review['jobs'].items():
        require(row.get('read_source_sha256')==plan['sources']['files'][jobs[key]['module'].replace('.','/')+'.py'],
                'reviewed entrypoint source differs from the scheduled source')
        require(all(isinstance(row.get(k),str) and row[k].strip() for k in
                    ('hypothesis','method','null_expectation','alternative_expectation','failure_direction',
                     'independent_unit','evidence_view','strongest_rival','exhaustive_bands')),
                'manual cell design is missing a load-bearing field')
    if tranche is None:
        require({tuple(row) for row in review['training_fits']}==set(FITS) and len(review['training_fits'])==24,
                'all recipes/families/seeds must be explicitly scheduled')
    else:
        require(review['training_fits']==[], 'tranche cannot claim deferred factorial fits')
    fit_jobs=[j for j in plan['jobs'] if j['module']=='runners.stage9.training_jobs' and j['arguments'][0]=='fit']
    actual_fits=[]
    for job in fit_jobs:
        args=job['arguments'];actual_fits.append((args[args.index('--family')+1],args[args.index('--recipe')+1],int(args[args.index('--seed')+1])))
    require((not actual_fits) if tranche else (len(actual_fits)==24 and set(actual_fits)==set(FITS)),
            'reviewed factorial differs from actual fit invocations')
    for card,keys in review['cards'].items():
        require(isinstance(keys,list) and (keys or card in coverage.get('preparations', {})
                or tranche and tranche['cards'][card]['status']=='deferred')
                and set(keys)<=set(jobs),'card has no scheduled cells or checked preparation evidence: '+card)
    require(set(objects['sources']['corpora'])==(set(tranche['source_corpora']) if tranche else CORPORA)
            and len(objects['sources']['inherited_checkouts'])==17,
            'source readiness inventory is incomplete')
    from runners.stage9.packet_review import policy as packet_policy
    require(set(packet_policy(plan)['inherited_checkouts'])==set(objects['sources']['inherited_checkouts']),
            'final packet checkout roster differs from the reviewed launch sources')
    for name,row in objects['sources']['corpora'].items():
        require(row.get('status') in ('usable','blocked','unready') and bool(row.get('basis')),'source readiness has no scoped disposition')
        if tranche:
            require(row['status']=='usable','selected corpus is blocked or unready')
        if row['status']=='usable':
            loader=checked(row['loader']);baseline=checked(row['baseline'])
            require(loader and baseline and row.get('grouping') and row.get('rights_basis'),'usable corpus lacks real loader/baseline/grouping/rights evidence')
    fixtures=objects['fixtures']
    require(fixtures.get('positive_cases') and fixtures.get('negative_cases') and fixtures.get('all_expected_answers') is True,
            'both actual positive and negative instrument fixtures are required')
    require(set(fixtures['attacks'])=={f'X{i:02d}' for i in range(1,13)},'shared attacks are not fully enumerated')
    for name,row in fixtures['attacks'].items():
        if tranche and row.get('status')=='inapplicable':
            shared={'X01','X02','X05','X06','X11','X12'} | ({'X07'} if tranche['package_kinds'] else set())
            require(name not in shared,'selected-task leakage, support, grouping or recovery control cannot be deferred')
            require(not coverage['attacks'][name]['jobs'] and row.get('reason')==coverage['attacks'][name]['not_applicable_reason'],
                    'an applicable shared attack cannot be deferred')
            continue
        require(row.get('null_expected') and row.get('alternative_expected') and row.get('executed_receipts'),
                'attack lacks known-response execution: '+name)
        for pointer in row['executed_receipts']:checked(pointer)
    packages=objects['packages']
    require(set(packages['families'])==(set(tranche['package_kinds']) if tranche else {'qwen','smollm'}),
            'all selected pinned reader families are required')
    for family,row in packages['families'].items():
        from runners.stage9.train import BASES
        require(row.get('base')==BASES[family],'reader base revision differs from the commissioned package')
        require(row.get('tokenizer_sha256') and row.get('renderer_sha256') and row.get('scorer_sha256') and row.get('operation_profiles'),
                'reader identity/profile contract incomplete')
        require(row.get('precision')=='float16' and row.get('maximum_context')==4096 and row.get('maximum_support')==128,
                'reader exceeds the actual calibrated pilot envelope')
        calibration=checked(row['calibration'])
        require(calibration and row.get('historical_adapter') and
                (row.get('package_kinds')==tranche['package_kinds'][family] if tranche else row.get('proposed_fit_jobs')),
                'reader lacks calibrated and historical/proposed package identities')
    split=objects['splits'];seen={};counts={}
    require(split.get('assignments') and split.get('cross_source_checks') and split.get('reserve_truth_opened') is False,
            'actual split and cross-source closure evidence required')
    for row in split['assignments']:
        role=row['role'];require(role in ('training','pilot','development','discovery','reserve'),'unknown split role')
        for key in (('lineage',row['group']),('content',row['content_sha256'])):
            require(key not in seen or seen[key]==role,'source lineage/content crosses split roles')
            seen[key]=role
        counts[role]=counts.get(role,0)+1
    require(all(counts.get(role,0)>0 for role in (tranche['required_split_roles'] if tranche else
                                                ('training','pilot','development','discovery','reserve'))),
            'required construction partitions are empty')
    wake=objects['wake']
    require(wake.get('probe_id')=='S9-WAKE-20260906-01' and wake.get('delivered') is True
            and wake.get('recorded_at') and wake.get('owner_session_id')==review['owner_session_id'],
            'queued or wrong-owner wake is not actual delivery')
    interruption=objects['interruption']
    required_checks={'all_actual_loaded_sources_match','all_prior_unit_bytes_unchanged','campaign_clock_unchanged',
                     'competing_writer_refused','complete_192_units','native_kill_observed','same_cell_identity',
                     'same_manifest','source_omission_rejected'}
    require(required_checks<=set(interruption.get('checks',{})) and
            all(interruption['checks'][k] is True for k in required_checks) and interruption['preserved_completed_units']>0,
            'actual interruption/restart evidence is incomplete')
    if tranche:
        from .tranche import compatibility
        compatibility(checked(interruption['source']),plan['sources'],interruption['compatibility'])
    if tranche:
        from .tranche import rehearsal as verify_tranche_rehearsal
        verify_tranche_rehearsal(plan,objects['dress_rehearsal'])
    else:
        verify_rehearsal(plan,objects['dress_rehearsal'])
    campaign=read(ROOT/'CAMPAIGN.json')
    require(plan['campaign_start']==campaign['started_epoch'] and plan['horizon_epoch']==campaign['horizon_epoch'],
            'scientific lock resets the preparation clock')
    verify_forecast(objects['forecast'],plan)
    result={'manifest_sha256':digest(plan),'checked_evidence':evidence,'jobs':len(jobs),'cards':42,
            'scientific_claim':'none from launch mechanics'}
    if tranche:
        result.update(acceptance_scope='tranche',execution_scope_sha256=digest(tranche),
                      permitted_claims=tranche['permitted_claims'],full_stage_accepted=False)
    return result


def verify_rehearsal(plan,rehearsal):
    from .queue import verify_committed
    jobs={j['id']:j for j in plan['jobs']}
    rehearsal_plan=checked(rehearsal['plan'])
    require(rehearsal_plan['kind']=='prelaunch_rehearsal' and rehearsal_plan['sources']==plan['sources'],
            'dress rehearsal did not execute final scientific source closure')
    require(set(rehearsal['job_mapping'])==set(jobs),'dress rehearsal omits scheduled cells')
    rehearsal_jobs={j['id']:j for j in rehearsal_plan['jobs']}
    queue_root=(REPO/rehearsal['queue_root']).resolve()
    require(queue_root.is_relative_to(ROOT),'dress rehearsal is outside this stage')
    terminal=read(queue_root/'COMPLETE.json')
    for key,other in rehearsal['job_mapping'].items():
        require(other in rehearsal_jobs and handler_operation(jobs[key])==handler_operation(rehearsal_jobs[other]),
                'dress rehearsal substituted a different handler operation or model family')
        require(terminal['jobs'][other]['status']=='COMPLETE','actual handler did not complete its dress rehearsal')
        verify_committed(queue_root,rehearsal_jobs[other],rehearsal_plan,digest(rehearsal_plan))


def certify(manifest,evidence):
    manifest=Path(manifest).resolve();plan=read(manifest);result=validate(plan,evidence)
    certificate=result|{'accepted':True,'version':2,'accepted_at':datetime.now(timezone.utc).isoformat()}
    freeze(manifest.parent/'LAUNCH_ACCEPTANCE.json',certificate)
    return certificate


def verify_certificate(plan,certificate):
    require(certificate.get('version')==2 and certificate.get('accepted') is True
            and certificate.get('manifest_sha256')==digest(plan),'nonvacuous launch certificate missing or mismatched')
    result=validate(plan,certificate.get('checked_evidence',{}))
    require(result['jobs']==certificate.get('jobs') and certificate.get('cards')==42,'launch workload changed')
    for key in ('acceptance_scope','execution_scope_sha256','permitted_claims','full_stage_accepted'):
        require(result.get(key)==certificate.get(key),'launch acceptance scope or claims changed')
    return True
