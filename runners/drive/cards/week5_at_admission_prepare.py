"""One-stage, non-launching preparation for the corrected AT2 reader bank.

DESIGN CHECK: LESSONS 3-5. Missing measured evidence refuses under every
scientific outcome. Qualification caps are not forecasts. No weight-size
estimate releases a model, no old failure disappears, and no partial bank
selects a reader. This module has no launch, lease, ACK or publication action.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import ast
import hashlib
import importlib.util
import json
import math
import subprocess

REPO = Path(__file__).resolve().parents[3]
PRIVATE = REPO/'.agent-state/drive-20261107'
BASE = REPO/'results/phase_2_4_stage_15/raw/drive-week5-20261107'
ROSTER = PRIVATE/'at-corrected-bank-proposals/ROSTER.json'
ROSTER_SHA = 'cdb90059a1439205dff7feba1517dc7fb990a57718e1e7996d431730f99a05fb'
PREPARED = PRIVATE/'at-guarded-bank-prepared.json'
PREPARED_SHA = '9b4d868a739497554801dd00d8de741564d717edde805c7c7304c995cd8a06f7'
GUARDED = 'runners.drive.cards.week5_at_scoring_guard_v1'
FIXTURE = 'runners.drive.cards.week5_at_guarded_bank_fixture'
MIGRATION = 'runners.drive.cards.week5_at_precision_migration'
CASE = 'runners.drive.cards.week5_at_precision_guard_v2'
RUNTIME = ['runners.drive.week5_launch_v7','runners.drive.cards.week5_runtime_v7',
           'runners.drive.cards.week5_policy_v2','runners.drive.cards.week5_child_v3']
NUMERIC = dict(version='AT-FP64-1',model_computation='float64_from_pinned_float32',
               log_softmax_and_entropy='float32',cache_fresh_tolerance_nats=1e-4,
               attention_backend='original_model_default')
NATIVE_LIMITS = dict(start_commit_bytes=26*2**30,start_ram_bytes=20*2**30,
                     request_commit_bytes=7*2**30,request_ram_bytes=7*2**30,
                     hard_commit_floor_bytes=6*2**30,hard_ram_floor_bytes=6*2**30,
                     cooperative_grace_seconds=60,poll_seconds=.25)
CASES = {'160m':'AT2-pilot-m02-b0007','410m':'AT2-pilot-m04-b0000'}
STAGES = {'guard_fixture','largest_verifier','case_control','first_chunk','pilot_chunk','pilot_envelope','resume'}


class Refusal(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise Refusal(reason)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(2**20),b''):
            h.update(block)
    return h.hexdigest()


def finite(value, positive=False):
    require(type(value) in (int,float) and math.isfinite(value) and
            (value>0 if positive else value>=0),'Finite measured quantity or explicit positive cap required')
    return float(value)


def path(value, within=None):
    p=Path(value)
    if not p.is_absolute():p=REPO/p
    p=p.resolve();p.relative_to(Path(REPO if within is None else within).resolve())
    return p


def pin_map(pins):
    require(isinstance(pins,dict) and pins,'Nonempty frozen pin map required')
    normalized={}
    for name,digest in pins.items():
        p=path(name);key=str(p).casefold()
        require(key not in normalized or normalized[key]==digest,'Conflicting pin aliases')
        require(sha(p)==digest,'Frozen dependency changed: '+str(p))
        normalized[key]=digest
    return normalized


def stopped_owner(root, plan_sha256):
    from runners.stage9.process_identity import is_same_live_process
    owner=read(Path(root)/'OWNER.json')
    require(owner.get('plan_sha256')==plan_sha256,'Native owner/plan binding differs')
    require(not is_same_live_process(owner['native']),'Prior native owner is still active')


def complete(root, module=None):
    root=path(root,BASE)
    require((root/'COMPLETE.json').is_file(),'Complete native receipt absent: '+str(root))
    require(not any((root/n).exists() for n in ['FAILED.json','PAUSED.json','MONITOR_FAILED.json']),
            'Ambiguous or failed native terminal')
    done=read(root/'COMPLETE.json');plan=read(root/'PLAN.json')
    require(done.get('status')=='COMPLETE' and done.get('fresh_process_verified') is True,
            'Independent complete native verification absent')
    require(plan.get('campaign')=='S15-WEEK5' and plan.get('family')=='AT','Wrong charged campaign/family')
    require(module is None or plan.get('module')==module,'Unexpected native dependency module')
    require(done['outputs'].get('PLAN.json')==sha(root/'PLAN.json'),'Native plan not sealed by completion')
    stopped_owner(root,sha(root/'PLAN.json'))
    for name,digest in done['outputs'].items():
        p=(root/name).resolve();p.relative_to(root)
        require(sha(p)==digest,'Completed output changed: '+name)
    normalized=pin_map(plan['pins'])
    if module is not None:
        require(all(normalized.get(str(path(p)).casefold())==s for p,s in closure([module]).items()),
                'Native dependency omitted or changed a required handler source pin')
    require(read(root/'VERIFIED.json').get('verified') is True,'Complete marker lacks actual verified=True')
    measured=0.
    for phase in ['EXECUTE','VERIFY']:
        usage=read(root/(phase+'_JOB_USAGE.json'))
        require(usage.get('includes_all_descendants_and_exited_processes') is True and usage.get('exit_code')==0,
                'Native descendant accounting or successful phase absent')
        measured+=finite(usage['cpu_seconds'])
    require(finite(done['cpu_seconds'])+1e-9>=measured,'Native terminal undercounts its phase receipts')
    return root,plan,done


def terminal_audit():
    """Keep every AT terminal charge; never turn a missing active receipt into zero."""
    rows=[]
    for directory in sorted(BASE.iterdir()):
        pp=directory/'PLAN.json'
        if not pp.is_file():continue
        plan=read(pp)
        if plan.get('campaign')!='S15-WEEK5' or plan.get('family')!='AT':continue
        terms=[directory/n for n in ['COMPLETE.json','FAILED.json','PAUSED.json'] if (directory/n).exists()]
        require(len(terms)<=1,'Ambiguous AT terminal accounting')
        claimed=(directory/'ATTEMPT.claim').exists()
        if claimed and not terms:
            # Other AT statistics may run independently; a reader-bank stage
            # already active prevents this driver preparing a concurrent stage.
            module=plan.get('module','')
            bank=any(tag in module for tag in ['at_scoring','at_precision','at_guarded_bank'])
            require(not bank,'A reader-bank qualification or scoring stage is already active')
        elif claimed and terms and any(tag in plan.get('module','') for tag in ['at_scoring','at_precision','at_guarded_bank']):
            stopped_owner(directory,sha(pp))
        rows.append(dict(root=str(directory),plan_sha256=sha(pp),
                         status=terms[0].stem.lower() if terms else ('active' if claimed else 'unstarted'),
                         terminal_sha256=sha(terms[0]) if terms else None,
                         cpu_seconds=finite(read(terms[0])['cpu_seconds']) if terms else (None if claimed else 0),
                         supervisor_envelope_cpu_seconds=30 if claimed else 0))
    return rows


def frozen_inputs():
    require(sha(ROSTER)==ROSTER_SHA and sha(PREPARED)==PREPARED_SHA,'Prepared roster or guarded build changed')
    roster=read(ROSTER);prepared=read(PREPARED)
    pin_map(prepared['files']);pin_map(prepared['source_closure']);pin_map(prepared['native_proof_dependencies'])
    refs=[roster[k] for k in ['models','sources','code_closure','proof_dependencies','retained_costs','resource_cost_gates']]
    refs+=roster['per_model_checkpointed_pilot_proposals']
    for ref in refs:require(sha(path(ref['path']))==ref['sha256'],'Prepared roster artifact changed')
    models=read(path(roster['models']['path']))['models']
    sources=read(path(roster['sources']['path']))
    for source_key in ['complete_full_source','complete_pilot_scope','complete_covariates']:
        src=sources[source_key];root=path(src['root'],BASE)
        require(sha(root/'COMPLETE.json')==src['complete_sha256'],'Frozen source completion changed')
        pin_map(src['metadata_pins'])
    require(sources['final_context']['pilot_word_share']>=.05,'Fixed pilot is below five-percent word coverage')
    proposals={m['model']:read(path(ref['path'])) for m,ref in zip(models,roster['per_model_checkpointed_pilot_proposals'])}
    require(len(proposals)==10 and all(proposals[m['model']]['model_revision']==m['revision'] for m in models),
            'Incomplete or reordered fixed reader bank')
    return roster,prepared,models,sources,proposals


def closure(modules):
    pending=list(modules);seen=set();files=set()
    while pending:
        module=pending.pop()
        if module in seen:continue
        seen.add(module);parts=module.split('.')
        p=REPO.joinpath(*parts).with_suffix('.py')
        if not p.exists():p=REPO.joinpath(*parts)/'__init__.py'
        if not p.exists():continue
        files.add(p);package=module if p.name=='__init__.py' else module.rpartition('.')[0]
        for i in range(1,len(parts)):
            q=REPO.joinpath(*parts[:i])/'__init__.py'
            if q.exists():files.add(q)
        for n in ast.walk(ast.parse(p.read_text(encoding='utf8'))):
            if isinstance(n,ast.Import):names=[a.name for a in n.names]
            elif isinstance(n,ast.ImportFrom):
                base=importlib.util.resolve_name('.'*n.level+(n.module or ''),package) if n.level else n.module
                names=[base]+[base+'.'+a.name for a in n.names] if base else []
            else:continue
            pending.extend(s for s in names if s and s.split('.')[0] in {'runners','soundingline','corpora','tools'})
    return {str(p):sha(p) for p in sorted(files)}


def guard_fixture(root):
    root,plan,done=complete(root,FIXTURE)
    value=read(root/'output/FIXTURE.json')
    for key in ['fixture_only','actual_guarded_v5_and_unguarded_v5_numeric_bytes_equal',
                'complete_ten_reader_360_row_bank','original_2000_draw_AT2_equal',
                'exact_reader_binding','unknown_guard_missing_pin_changed_limits_refused',
                'original_collection_refusals_retained','completed_guard_provenance_stable_under_later_replay']:
        require(value.get(key) is True,'Guarded fixture is incomplete: '+key)
    require(value.get('native_human_model_admission') is False,'Constructed fixture misstates human admission')
    return root


def guard_measurement(root, score_subdir='output'):
    done=read(root/'COMPLETE.json');records=[]
    for name in sorted(done['outputs']):
        if Path(name).parent.as_posix()!=score_subdir or not Path(name).name.startswith('GUARD_'):continue
        d=read(root/name)
        if d.get('status')!='returned':continue
        require(d.get('phase') in ['execute','verify'],'Invalid guard phase')
        require(d['limits']==NATIVE_LIMITS,'Original native memory thresholds or grace changed')
        require(d['initial']['commit_headroom_bytes']>=26*2**30 and d['initial']['ram_available_bytes']>=20*2**30,
                'Model entered below original resource gate')
        records.append(dict(phase=d['phase'],peak_bytes=finite(d['peak_working_set_bytes'],True),
                            receipt=name,sha256=sha(root/name)))
    require({r['phase'] for r in records}=={'execute','verify'},'Both actual native guarded phases required')
    return dict(peak_working_set_GiB=max(r['peak_bytes'] for r in records)/2**30,guard_receipts=records)


def largest_verification(root):
    root,plan,done=complete(root,MIGRATION)
    require(path(plan['inputs']['predecessor_root'])==BASE/'AT2-precision-m01-native','Wrong original largest-reader predecessor')
    require(path(plan['inputs']['failed_root'])==BASE/'AT2-pilot-m01-b0000','Wrong retained largest-reader failure')
    value=read(root/'output/FIXTURE.json')
    require(value.get('entire_original_chunk') and value.get('original_failure_preserved') and
            value.get('numerical_spec')==NUMERIC,'Largest-reader full numerical control absent')
    require(read(root/'output/scores/SUMMARY.json')['words']==164,'Largest retained full chunk changed')
    return root,guard_measurement(root)


def failed_case(root, name):
    root,plan,done=complete(root,CASE)
    require(path(plan['inputs']['failed_root'])==BASE/CASES[name],'Different actual failing case')
    value=read(root/'output/FIXTURE.json')
    require(value.get('engineering_replay_only') and value.get('entire_original_chunk') and
            value.get('unchanged_seeded_fresh_sample') and value.get('original_failure_preserved') and
            value.get('numerical_spec')==NUMERIC,'Actual full failed-case control missing')
    return root


def chain(root):
    """Authenticate exact same-module pauses and retain every native charge."""
    result=[];seen=set();root=path(root,BASE)
    while True:
        require(root not in seen,'Cyclic checkpoint chain');seen.add(root)
        plan=read(root/'PLAN.json');terms=[root/n for n in ['COMPLETE.json','PAUSED.json','FAILED.json'] if (root/n).exists()]
        require(len(terms)==1 and terms[0].name!='FAILED.json','A measured completed chain cannot conceal a failed predecessor')
        terminal=read(terms[0]);result.append(dict(root=str(root),terminal_sha256=sha(terms[0]),
                                                cpu_seconds=finite(terminal['cpu_seconds']),supervisor_envelope_cpu_seconds=30))
        resume=plan.get('resume')
        if not resume:break
        old=path(resume['root'],BASE);prior=read(old/'PLAN.json')
        require(sha(old/'PLAN.json')==resume['plan_sha256'] and sha(old/'PAUSED.json')==resume['paused_sha256'],
                'Resume predecessor pin differs')
        require(all(plan[k]==prior[k] for k in ['module','inputs','family','campaign']),'Resume changed numerical/source identity')
        require({k:v for k,v in plan['config'].items() if k!='max_wall_seconds'}==
                {k:v for k,v in prior['config'].items() if k!='max_wall_seconds'},'Resume changed scientific configuration')
        require(all(plan['pins'].get(p)==s for p,s in prior['pins'].items()),'Resume dropped prior pins')
        paused=read(old/'PAUSED.json')
        stopped_owner(old,sha(old/'PLAN.json'))
        for n,s in paused['checkpoint_outputs'].items():
            p=(old/'output'/n).resolve();p.relative_to(old/'output')
            require(sha(p)==s,'Paused checkpoint bytes changed')
        root=old
    return result


def measured_chunk(root, proposal):
    root,plan,done=complete(root,GUARDED)
    require(sha(path(plan['inputs']['model_manifest']))==proposal['model_manifest_sha256'],'Wrong model/tokenizer revision')
    cfg=plan['config']
    require(cfg.get('context','final')=='final' and cfg.get('context_length',1024)==1024,'Wrong complete pilot context')
    rows=path(plan['inputs']['rows']);digest=sha(rows)
    normalized={str(path(p)).casefold():s for p,s in plan['pins'].items()}
    require(normalized.get(str(rows).casefold())==digest and
            normalized.get(str(path(plan['inputs']['model_manifest'])).casefold())==proposal['model_manifest_sha256'],
            'Measured scorer did not pin its exact rows and model/tokenizer manifest')
    candidates=[b for b in proposal['pilot_batches'] if b['input_sha256']==digest and path(b['input_rows'])==rows]
    require(len(candidates)==1,'Completed source chunk is not the exact frozen pilot')
    batch=candidates[0];summary=read(root/'output/SUMMARY.json')
    require(summary.get('numerical_spec')==NUMERIC and summary.get('model')==proposal['model'] and
            summary.get('model_revision')==proposal['model_revision'] and summary.get('words')==batch['words'],
            'Complete measured pilot binding differs')
    traces=chain(root);measure=guard_measurement(root)
    return dict(root=str(root),complete_sha256=sha(root/'COMPLETE.json'),batch_ordinal=batch['batch_ordinal'],
                words=batch['words'],source_sha256=digest,model=proposal['model'],
                model_manifest_sha256=proposal['model_manifest_sha256'],
                chain=traces,native_cpu_seconds=sum(t['cpu_seconds'] for t in traces),
                **measure)


def pilot_envelope(roots, proposal):
    require(len(roots)==165,'Complete measured pilot requires all165 fixed chunks')
    chunks=[measured_chunk(r,proposal) for r in roots]
    require(sorted(c['batch_ordinal'] for c in chunks)==list(range(165)),'Duplicate/missing pilot chunks')
    require(sum(c['words'] for c in chunks)==27007,'Pilot work coverage changed')
    attempts={}
    for c in chunks:
        for entry in c['chain']:
            require(entry['root'] not in attempts,'One native attempt cannot measure two chunks')
            attempts[entry['root']]=entry
    return dict(schema='AT2-measured-corrected-pilot-envelope-1',model=proposal['model'],
                model_manifest_sha256=proposal['model_manifest_sha256'],numerical_spec=NUMERIC,
                source_roster_sha256=ROSTER_SHA,words=27007,batches=165,
                native_cpu_seconds=sum(t['cpu_seconds'] for t in attempts.values()),
                supervisor_envelope_cpu_seconds=sum(t['supervisor_envelope_cpu_seconds'] for t in attempts.values()),
                measured_peak_working_set_GiB=max(c['peak_working_set_GiB'] for c in chunks),
                chunks=chunks,weight_size_used_as_measurement=False,whole_bank_ready=False,
                whole_bank_forecast_cpu_seconds=None,
                cost_scope='Completed exact chunk chains; failed attempts remain separately charged in retained_AT_attempts, never hidden or used as zero-cost throughput',
                forecast_pending='All ten envelopes, retained charges and measured downstream allowance are required')


def design_review(review, stage, expected_design):
    require(review.get('owner_reviewed') is True and review.get('stage')==stage,'Explicit owner stage review required')
    require(review.get('prepared_manifest_sha256')==PREPARED_SHA,'Owner review addresses another prepared build')
    p=path(expected_design);commit=review.get('design_commit')
    require(isinstance(commit,str) and commit,'Reviewed committed design absent')
    data=subprocess.run(['git','show',commit+':'+p.relative_to(REPO).as_posix()],cwd=REPO,capture_output=True,check=True).stdout
    require(data==p.read_bytes(),'Design differs from the reviewed local commit')
    return p,commit


def resumable(root):
    root=path(root,BASE)
    require((root/'PAUSED.json').is_file() and not any((root/n).exists() for n in ['COMPLETE.json','FAILED.json','MONITOR_FAILED.json']),
            'Only an authenticated unambiguous pause may continue')
    prior=read(root/'PLAN.json');paused=read(root/'PAUSED.json')
    require(prior.get('module') in {FIXTURE,MIGRATION,CASE,GUARDED} and
            prior.get('campaign')=='S15-WEEK5' and prior.get('family')=='AT','Unreviewed resume module or charged campaign')
    require(paused.get('checkpoint_validation_required') is True,'Pause is not a checkpoint continuation')
    stopped_owner(root,sha(root/'PLAN.json'));pin_map(prior['pins'])
    from .week5_resume import output_manifest
    require(output_manifest(root/'output')==paused['checkpoint_outputs'],'Original paused checkpoint manifest changed')
    return root,prior,dict(root=str(root),plan_sha256=sha(root/'PLAN.json'),paused_sha256=sha(root/'PAUSED.json'))


def prepare(request):
    require(set(request)<={'stage','review','dependencies','model','case','completed_chunks','target_root','predecessor_root'},'Unknown driver request field')
    stage=request.get('stage');require(stage in STAGES,'Unknown explicit preparation stage')
    roster,build,models,sources,proposals=frozen_inputs();audit=terminal_audit()
    deps=request.get('dependencies',{});review=request.get('review',{})
    proofs=[path(p) for p in build['native_proof_dependencies']]
    pins={};measurement=None;resume_spec=None;prior=None;effective=stage;model=request.get('model')
    if stage=='resume':
        old,prior,resume_spec=resumable(request.get('predecessor_root','__absent__'))
        effective={FIXTURE:'guard_fixture',MIGRATION:'largest_verifier',CASE:'case_control',GUARDED:'pilot_chunk'}[prior['module']]
        if prior['module']==GUARDED:
            model=read(path(prior['inputs']['model_manifest']))['model']
            require(model in proposals,'Resume reader is outside the frozen ten-model bank')
            proposal=proposals[model]
            require(sha(path(prior['inputs']['model_manifest']))==proposal['model_manifest_sha256'],
                    'Resume model/tokenizer manifest differs')
            require(any(path(b['input_rows'])==path(prior['inputs']['rows']) and
                        b['input_sha256']==sha(path(prior['inputs']['rows'])) for b in proposal['pilot_batches']),
                    'Resume source is outside the fixed pilot')
            require(prior['config'].get('context','final')=='final' and prior['config'].get('context_length',1024)==1024,
                    'Resume changes pilot context')
        elif prior['module']==CASE:
            require(path(prior['inputs']['failed_root']) in {BASE/n for n in CASES.values()},'Resume failed case is outside the fixed controls')
        elif prior['module']==MIGRATION:
            require(path(prior['inputs']['predecessor_root'])==BASE/'AT2-precision-m01-native' and
                    path(prior['inputs']['failed_root'])==BASE/'AT2-pilot-m01-b0000','Resume largest-reader source differs')
        else:
            require(prior['inputs']=={} and prior['config']=={},'Constructed guard fixture has no external inputs')
        for name in ['PLAN.json','PAUSED.json']:pins[str(old/name)]=sha(old/name)
        pins.update(prior['pins'])
    if effective!='guard_fixture':
        fixture=guard_fixture(deps.get('guarded_fixture','__absent__'));proofs.append(fixture/'COMPLETE.json')
    if effective in {'case_control','first_chunk','pilot_chunk','pilot_envelope'}:
        largest,largest_measurement=largest_verification(deps.get('largest_verifier','__absent__'))
        proofs.append(largest/'COMPLETE.json')
    if effective in {'first_chunk','pilot_chunk','pilot_envelope'}:
        for name in CASES:proofs.append(failed_case(deps.get('case_'+name,'__absent__'),name)/'COMPLETE.json')
    if stage=='pilot_envelope':
        require(request.get('model') in proposals,'Exact commissioned model required')
        result=pilot_envelope(request.get('completed_chunks',[]),proposals[request['model']])
        return dict(result,retained_AT_attempts=audit,scientific_admission=False,launch_authority=False)
    if stage=='resume':
        module=prior['module'];inputs=prior['inputs'];config=prior['config'];design=prior['design']
        proofs += [path(p) for p in prior['validation_receipts']]
    elif stage=='guard_fixture':
        module=FIXTURE;inputs={};config={};design=build['design']
    elif stage=='largest_verifier':
        module=MIGRATION;old=BASE/'AT2-precision-m01-native';prior=read(old/'PLAN.json')
        require((old/'PAUSED.json').is_file() and not any((old/n).exists() for n in ['COMPLETE.json','FAILED.json']),
                'Original largest-reader paused predecessor unavailable')
        require(read(old/'VERIFIED.json').get('status')=='yielded','Original largest verify was not a resource pause')
        stopped_owner(old,sha(old/'PLAN.json'))
        pin_map(prior['pins']);pins.update(prior['pins'])
        for name in ['PLAN.json','PAUSED.json']:pins[str(old/name)]=sha(old/name)
        inputs=dict(failed_root=prior['inputs']['failed_root'],predecessor_root=str(old));config={}
        design='docs/design/stage-15/week5/AT_PRECISION_MIGRATION.md'
        proofs.append(PRIVATE/'at-precision-migration-fixture/FIXTURE.json')
    elif stage=='case_control':
        require(request.get('case') in CASES,'Exact registered failing case required')
        failed=BASE/CASES[request['case']]
        require((failed/'FAILED.json').is_file(),'Original failed evidence absent')
        original=read(failed/'PLAN.json');pin_map(original['pins']);pins.update(original['pins'])
        for name in ['PLAN.json','FAILED.json']:pins[str(failed/name)]=sha(failed/name)
        inputs=dict(failed_root=str(failed));module=CASE;config={}
        design='docs/design/stage-15/week5/AT_PRECISION_GUARD.md'
    else:
        require(request.get('model') in proposals,'Exact commissioned model required')
        proposal=proposals[request['model']];completed=[measured_chunk(r,proposal) for r in request.get('completed_chunks',[])]
        indices=sorted(c['batch_ordinal'] for c in completed)
        require(indices==list(range(len(completed))) and len(completed)<165,'Pilot work must advance in its frozen prefix order')
        if stage=='first_chunk':require(not completed,'First cost cannot replace a measured chunk')
        else:
            require(completed,'Measured per-model envelope absent; no weight-size substitute')
            measurement=dict(reference_chunks=completed,reference_native_cpu_seconds=sum(c['native_cpu_seconds'] for c in completed),
                             measured_words=sum(c['words'] for c in completed),
                             measured_peak_working_set_GiB=max(c['peak_working_set_GiB'] for c in completed),
                             provisional_chunk_envelope=True,complete_pilot=False,whole_bank_forecast_cpu_seconds=None)
        batch=proposal['pilot_batches'][len(completed)]
        require(sha(path(batch['input_rows']))==batch['input_sha256'],'Frozen pilot chunk changed')
        inputs=dict(rows=batch['input_rows'],model_manifest=proposal['model_manifest']);config=proposal['config']
        module=GUARDED;design=build['design']
        for p in inputs.values():pins[str(path(p))]=sha(path(p))
        for item in completed:proofs.append(Path(item['root'])/'COMPLETE.json')
    design,commit=design_review(review,stage,design)
    caps=review.get('caps',{})
    require(set(caps)=={'max_cpu_seconds','max_wall_seconds','projected_peak_ram_GiB'},'Explicit finite stage caps required')
    for value in caps.values():finite(value,True)
    require(caps['max_wall_seconds']<=1700 and caps['max_cpu_seconds']<=7200,'Stage must remain a bounded in-slot qualification/chunk')
    if effective=='guard_fixture':
        require(caps['max_cpu_seconds']<=600 and caps['max_wall_seconds']<=900 and caps['projected_peak_ram_GiB']>=3,
                'Constructed fixture envelope differs')
    else:
        require(caps['projected_peak_ram_GiB']>=20,'Initial conservative guarded qualification envelope is at least20GiB; no unmeasured lower-memory exception')
    if prior is not None:
        require(caps['projected_peak_ram_GiB']>=prior['projected_peak_ram_GiB'],'Resume cannot silently reduce the admitted memory envelope')
    if measurement:
        require(caps['projected_peak_ram_GiB']>=measurement['measured_peak_working_set_GiB'],'Declared peak below measured native peak')
        per_chunk=max(c['native_cpu_seconds'] for c in measurement['reference_chunks'])
        require(caps['max_cpu_seconds']>=per_chunk,'Stage cap below already measured complete chunk; obtain explicit continuation review')
    else:
        require(review.get('qualification_cap_not_forecast') is True,'Unmeasured first qualification must be labelled as a cap, never a forecast')
    target=path(request.get('target_root','__absent__'),BASE)
    require(target.parent==BASE and target.name.startswith('AT2-'),'A single direct AT2 attempt root is required')
    require(not target.exists(),'Never overwrite or readmit an existing attempt')
    pins.update(closure([module,*RUNTIME]));pins[str(design)]=sha(design)
    pins[str(ROSTER)]=ROSTER_SHA;pins[str(PREPARED)]=PREPARED_SHA
    pins[str(Path(__file__).resolve())]=sha(__file__)
    scaffold=REPO/'docs/design/stage-15/week5/AT_BANK_ADMISSION_SCAFFOLD.md'
    pins[str(scaffold)]=sha(scaffold)
    for p in proofs:pins[str(p)]=sha(p)
    plan=dict(campaign='S15-WEEK5',family='AT',card=target.name,module=module,inputs=inputs,config=config,
              **caps,numerical_threads=2,gpu=False,paid=False,ollama=False,owner_reviewed=False,
              design=str(design),reviewed_design_commit=commit,fixture_passed=True,
              validation_receipts=[str(p) for p in proofs],pins=pins,pilot_fraction=.05,
              forecast_state='unmeasured' if measurement is None else 'provisional_measured_chunk_envelope',
              premortem=dict(case_and_check='Only the exact bounded qualification or measured pilot prefix; every original numerical/source guard remains.',
                             smaller_route='Pause with sealed checkpoints; owner evaluates measured whole-writer sample/family continuation, never a favorable reader subset.'))
    if resume_spec is not None:plan['resume']=resume_spec
    plan['at2_preparation_stage']=stage
    plan['fixture_scope']='Existing native platform/core proofs; guard_fixture stage qualifies the new target and does not claim it has already passed'
    # Read-only actual admission assessment. No claim, lease or process start.
    from . import week5_policy_v2 as policy
    admission=policy.admission(plan)
    resources=admission['resources']
    if effective!='guard_fixture':
        commit_min=28 if effective=='largest_verifier' or model=='EleutherAI/pythia-1.4b-deduped' else 26
        require(resources['commit_headroom_GiB']>=commit_min and resources['ram_available_GiB']>=20,
                'Fresh largest/generic guard memory gate unavailable; do not start or duplicate model loads')
    diagnostics=read(PRIVATE/'at-precision-review.json')
    overhead=finite(review.get('diagnostic_startup_charge_cpu_seconds'))
    extra=finite(diagnostics['measured_diagnostic_subtotal'])+overhead
    require(caps['max_cpu_seconds']<=admission['remaining_cpu_seconds']-extra,
            'Actual family room after retained diagnostic charges is insufficient')
    return dict(schema='AT2-private-stage-proposal-1',stage=stage,at=datetime.now(timezone.utc).isoformat(),
                proposed_attempt_root=str(target),nonlaunchable=True,launch_authority=False,
                scientific_admission=False,bank_ready=False,plan_template=plan,
                measured_envelope=measurement,whole_bank_forecast_cpu_seconds=None,
                semantic_request_sha256=hashlib.sha256(json.dumps(request,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
                owner_stage_review=review,target_guard_fixture_already_passed=effective!='guard_fixture',
                actual_readonly_policy_snapshot=admission,retained_AT_attempts=audit,
                retained_diagnostic_accounting_cpu_seconds=extra,
                measured_diagnostic_process_cpu_seconds=diagnostics['measured_diagnostic_subtotal'],
                owner_declared_diagnostic_startup_charge_cpu_seconds=overhead,
                accounting_note='Conservatively retain separately receipted diagnosis plus explicit owner overhead; do not subtract these as already charged without a separately reviewed accounting successor',
                owner_final_review_required=True)


def main():
    parser=argparse.ArgumentParser(description='Prepare one private AT2 proposal; never launches')
    parser.add_argument('request',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();destination=path(args.output,PRIVATE/'at-admission-work')
    require(destination.name!='PLAN.json','Never write a runnable PLAN.json')
    try:result=prepare(read(args.request));code=0
    except (Refusal,KeyError,OSError,ValueError,RuntimeError,subprocess.CalledProcessError) as exc:
        result=dict(status='refused',reason=str(exc),launch_authority=False,bank_ready=False);code=2
    destination.parent.mkdir(parents=True,exist_ok=True)
    with destination.open('x',encoding='utf8') as stream:json.dump(result,stream,indent=2,sort_keys=True);stream.write('\n')
    print(json.dumps(dict(status=result.get('status','prepared'),private_output=str(destination),launch_authority=False)))
    raise SystemExit(code)


if __name__=='__main__':main()
