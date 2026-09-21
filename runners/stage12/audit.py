"""Offline retained-call telemetry and source-exposure inventory.

DESIGN CHECK: LESSONS 2-5. NULL: identical raw timings replay exactly and a
missing telemetry field stays unknown. ALTERNATIVE: load, decoding and wall
waiting are distinguished only where measured. Prior source exposure cannot
become fresh confirmation merely because an event or view is new. No scores
from the incomplete Stage 11.2 comparison are computed.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from .common import REPO, read, freeze, filehash, digest, SEED

OLD = REPO/'results/phase_2_4_stage_11_2/raw/repair-v1/M0-ollama-dev'
S11 = REPO/'results/phase_2_4_stage_11_1/raw'

def ledger_summary(ledger):
    linked=[r for r in ledger if 'writer' in r and 'prompt' in r]
    unlinked=[r for r in ledger if r not in linked]
    if any(r.get('usable') for r in unlinked):raise ValueError('usable source lacks writer/prompt identity')
    return dict(entries=len(ledger),metadata_linked_sessions=len(linked),
        metadata_unlinked_excluded_logs=len(unlinked),writers=len({r['writer'] for r in linked}),
        prompts=len({r['prompt'] for r in linked}),usable_sessions=sum(r.get('usable',False) for r in linked),
        source_defined_opportunities=sum(r.get('usable_decisions',0) for r in linked),
        unlinked_reasons=dict(Counter(r.get('reason','not recorded') for r in unlinked)))

def quantiles(values):
    import numpy as np
    v=[x for x in values if x is not None]
    return None if not v else dict(n=len(v), median=float(np.median(v)),
                                    p90=float(np.quantile(v,.9)), minimum=min(v), maximum=max(v))

def timing_row(path):
    attempt=read(path/'COMPLETE.json'); raw=read(path/'RAW.json'); request=read(path/'REQUEST.json')
    from runners.stage11_2.common import digest as original_digest
    # Preserve the historical serializer; Stage 12's compact record digest is
    # deliberately not substituted for the old indented raw-response binding.
    if original_digest(raw)!=attempt['raw_sha256']:
        raise ValueError('retained response digest changed')
    n=request['format']['properties']['probabilities']['maxItems']
    from runners.stage11_2.repair import parse
    try: parsed=parse(raw,n)
    except (ValueError,KeyError,TypeError): parsed=None
    if parsed!=attempt['probabilities']:
        raise ValueError('retained semantic replay differs')
    end=datetime.fromisoformat(raw['created_at'].replace('Z','+00:00'))
    secs=attempt['seconds']
    original={k:raw.get(k) for k in ('total_duration','load_duration','prompt_eval_duration','eval_duration')}
    seconds={k:v/1e9 if type(v) in (int,float) else None for k,v in original.items()}
    prompt=raw.get('prompt_eval_count'); output=raw.get('eval_count')
    tokens_per_second=lambda count,duration: count/duration if count is not None and duration else None
    parts=path.name.split('-'); arm='-'.join(parts[2:-1]); question=parts[-1]
    return dict(id=path.name, request_sha256=filehash(path/'REQUEST.json'),
        raw_sha256=filehash(path/'RAW.json'),attempt_sha256=filehash(path/'COMPLETE.json'),
        model=request['model'], model_binding=attempt['binding'],
        model_revision=read(OLD/'MODEL.json')['digest'], revision_basis='retained native model identity',
        request_class=('account-assisted forecast' if arm in ('persistent','other_model') else 'direct forecast'),
        arm=arm,question=question, input_tokens=prompt,output_tokens=output,
        input_bytes=len(str(request).encode()),context_cap=request['options']['num_ctx'],
        output_cap=request['options']['num_predict'], original_nanoseconds=original,
        seconds=seconds, wall_seconds=secs,
        end=end.isoformat(), start_estimate=(end-timedelta(seconds=secs)).isoformat(),
        start_basis='server response timestamp minus measured client interval; not original client-start telemetry',
        prompt_tokens_per_second=tokens_per_second(prompt,seconds['prompt_eval_duration']),
        output_tokens_per_second=tokens_per_second(output,seconds['eval_duration']),
        unaccounted_wait_seconds=None if seconds['total_duration'] is None else secs-seconds['total_duration'],
        completion=dict(done=raw.get('done'),reason=raw.get('done_reason')),
        time_window=end.strftime('%Y-%m-%dT%H'), gpu_snapshot=None,
        gpu_snapshot_status='no per-call native snapshot in retained attempt',
        missing=[k for k,v in original.items() if v is None])

def runtime(out, pulse=lambda **k:None):
    paths=sorted(p.parent for p in (OLD/'calls').glob('*/COMPLETE.json'))
    if len(paths)!=943: raise ValueError('retained-call population changed')
    rows=[]
    for p in paths:
        rows.append(timing_row(p))
        if len(rows)%50==0:pulse(completed=len(rows),total=len(paths))
    groups=defaultdict(list)
    for r in rows:
        key=(r['request_class'],r['model'],r['context_cap'],r['input_tokens']//256,
             r['output_tokens']//128,r['time_window'])
        groups[key].append(r)
    summaries=[]
    for key,group in sorted(groups.items()):
        summaries.append(dict(group=list(key),n=len(group),
            wall=quantiles([r['wall_seconds'] for r in group]),
            server=quantiles([r['seconds']['total_duration'] for r in group]),
            load=quantiles([r['seconds']['load_duration'] for r in group]),
            decoding_tokens_per_second=quantiles([r['output_tokens_per_second'] for r in group]),
            prompt_tokens_per_second=quantiles([r['prompt_tokens_per_second'] for r in group]),
            unaccounted_wait=quantiles([r['unaccounted_wait_seconds'] for r in group]),
            missing_telemetry=sum(bool(r['missing']) for r in group),
            reference_status='historical measured regime; not a current healthy target'))
    freeze(out/'TIMINGS.json',rows);freeze(out/'GROUPS.json',summaries)
    unknown=[p for p in (OLD/'calls').glob('*/REQUEST.json') if not p.with_name('RAW.json').exists()]
    return dict(status='complete', kind='infrastructure', retained_calls=len(rows),
        all_raw_semantically_replayed=True, timing_groups=len(groups), unknown_requests=len(unknown),
        missing_native_snapshots=len(rows), scores_computed=False,
        healthy_reference='pending current matched warmup and canaries',
        cause='unidentified; historical server/wall telemetry alone cannot attribute interference',
        controls=dict(nanoseconds_to_seconds=True, original943=True, missing_fields_explicit=True),
        files={'TIMINGS.json':filehash(out/'TIMINGS.json'),'GROUPS.json':filehash(out/'GROUPS.json')})

def inventory(out,pulse=lambda **k:None):
    from runners.stage9.coauthor_cases import inputs
    ledger_path=REPO/'results/phase_2_4_stage_9/private/prepared/coauthor-v2/LEDGER.json'
    ledger=read(ledger_path); cohort=read(S11/'COHORT-v3.json')
    population,metadata=inputs('scientific')
    exposure=defaultdict(list)
    # Record explicit role evidence without treating absence from these files as
    # proof of an untouched writer. Earlier loader/selection history stays unknown.
    for lane,rows in cohort.items():
        for r in rows:exposure[r['key']].append(dict(stage='11.1',purpose=lane,kind='evaluated/fit roster'))
    for path in sorted((REPO/'results/phase_2_4_stage_10/raw').rglob('*-public.json')):
        if path.stat().st_size>20_000_000:continue
        d=read(path)
        if not isinstance(d,dict):continue
        for r in d.get('tasks',[]):
            if r.get('task_id'):exposure[r['task_id']].append(dict(stage='10',purpose=path.stem,source=str(path.relative_to(REPO))))
    entries=[]
    for lane,rows in population.items():
        for r in rows:
            entries.append(dict(key=r['key'],writer=r['writer'],project='coauthor',session=r['session'],
                prompt=r['prompt'],writer_component=r['unit'],prompt_component=r['stimulus'],
                lane=lane,prior_stage_roles=exposure.get(r['key'],[]),
                outcome_exposure='parsed in source preparation; explicit stage roles listed; earlier selection not proven absent',
                outcome_based_selection='unknown before audited source reconstruction',
                new_component_unexposed_to_outcome_selection=False,
                category='new view of exposed event' if r['key'] in exposure else 'new event from known writer',
                training_eligible=lane=='train',confirmatory_eligible=False))
    pulse(phase='freeze-source-census',opportunities=len(entries))
    current_sessions=Counter(r['session'] for r in entries)
    roles_by_session=defaultdict(set)
    for lane,rows in cohort.items():
        for r in rows:roles_by_session[r['session']].add('11.1:'+lane)
    source_census=[]
    for r in ledger:
        source_census.append(dict(project='coauthor',session=r['key'],writer=r.get('writer'),prompt=r.get('prompt'),
            source_usable=r.get('usable',False),recorded_opportunities=r.get('usable_decisions',0),
            current_separated_opportunities=current_sessions[r['key']],prior_explicit_roles=sorted(roles_by_session[r['key']]),
            prior_source_preparation='released outcomes parsed in historical preparation' if r.get('usable') else 'excluded',
            prior_outcome_selection='not established absent by this inventory',
            training_use='explicit roles listed; other historical role evidence needs source-stage audit',
            exclusion=r.get('reason'),confirmatory_freshness='not established'))
    freeze(out/'CENSUS.json',entries);freeze(out/'SOURCE_CENSUS.json',source_census)
    freeze(out/'POPULATION.json',population);freeze(out/'SOURCE_METADATA.json',metadata)
    full=ledger_summary(ledger)
    return dict(status='complete',kind='infrastructure',prepared_source=full,eligible_partitions=metadata['counts'],
        categories=dict(Counter(r['category'] for r in entries)),
        source_ledger_sha256=filehash(ledger_path),unexposed_confirmatory_components=0,
        fresh_support_status='none established; absence from Stage11.1 is not evidence of untouched outcomes',
        exclusions=dict(Counter(r['reason'] for r in metadata['exclusions'])),
        discrepancy='published metadata-linked sessions and extra excluded local logs are separate counts; neither creates another writer',
        controls=dict(no_freshness_from_absence=True,writer_prompt_separation=True,source_identity_verified=True),
        files={p.name:filehash(p) for p in out.glob('*.json') if p.name in ('CENSUS.json','SOURCE_CENSUS.json','POPULATION.json','SOURCE_METADATA.json')})
