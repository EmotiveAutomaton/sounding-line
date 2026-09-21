"""Finite Stage 12 preparation and source-bound consumers.

DESIGN CHECK: LESSONS 2-5; CONTROLS 6-7. NULL: lack of independent support
stays descriptive, and baseline equality or unknown goals cannot become neural
evidence. ALTERNATIVE: complete paired source records support the declared
comparison only. Every handler retains denominators and source/evaluator scope.
"""
from __future__ import annotations
from collections import Counter,defaultdict
from pathlib import Path
import math
from .common import REPO, read, freeze, filehash, digest, SEED, distribution
from .audit import S11

def packet_zero(out,card,pulse,raw):
    from runners.stage11_1.cheap import fit,predict
    from runners.stage11_1.preflight import source_rows
    from runners.stage11_1.targets import project,public
    from runners.stage11_1.score import episode
    from .provider import packet,claims_from_facts,metrics
    cohort=read(S11/'COHORT-v3.json');model=fit(cohort['train'])
    by={r['key']:r for r in cohort['discovery']};sources=source_rows(S11)
    if len(card['candidate_ids'])!=8:raise ValueError('packet-zero frozen eight-case roster')
    packets=[];evaluator=[];scored=[]
    for key in card['candidate_ids']:
        row=by[key];lines,events=sources[row['session']];event=events[row['ordinal']]
        if project(event,lines)!=row['target']:raise ValueError('source-operation replay differs')
        if any(public(event,v)!=row['views'][v] for v in row['views']):raise ValueError('public projection changed')
        for tier,view in [('E0','artifact'),('E1','alternatives'),('E2','alternatives'),('O','alternatives')]:
            e=dict(row['views'][view]);observed=tier in ('E2','O')
            if observed:
                # This condition receives the witnessed source operations. The
                # oracle is separately labelled; neither is a blind inference.
                e['witnessed_operations']=row['target']['facts']
                claims=claims_from_facts(row['target']['facts'],observed=True);alternatives=[]
            else:
                forecast,detail=predict(e,model);claims=claims_from_facts(forecast['facts'])
                alternatives=detail.get('compatible_histories',[])
                if not isinstance(alternatives,list):alternatives=[]
            method='witnessed-process projection' if tier=='E2' else 'oracle control' if tier=='O' else 'mechanical alignment with training prior'
            packets.append(packet(key,e,method,claims,alternatives,tier=tier))
            scored.append(dict(case_id=key,tier=tier,method=method,**metrics(claims,row['target']['facts'])))
        evaluator.append(dict(case_id=key,source_ordinal=row['ordinal'],target=row['target'],writer=row['writer'],session=row['session']))
        pulse(completed_cases=len(evaluator),total=8)
    # A deliberately fabricated claim at the wrong location must fail; all
    # unknown gets zero useful yield. These controls do not stand for people.
    truth=[dict(slot='insert',operation='insert',actor='human_writer',relation='none',span_state='located',span_ids=['p0'])]
    good=dict(slot='insert',role='process',status='inferred',operation='insert',actor='human_writer',relation='none',span_state='located',span_ids=['p0'])
    bad=dict(good,span_ids=['p1'])
    null=dict(schema='soundingline.provider.control.1',origin='synthetic',truth=truth,wrong_location=bad,
              unknown_metrics=metrics([],truth),wrong_location_metrics=metrics([bad],truth),correct_metrics=metrics([good],truth))
    freeze(out/'PACKETS.json',packets);freeze(out/'EVALUATOR_ONLY.json',evaluator)
    freeze(out/'METRICS.json',scored);freeze(out/'CONSTRUCTED_NULL.json',null)
    return dict(status='complete',kind='infrastructure',source_cases=8,packets=len(packets),
        case_selection='frozen hash order with writer coverage, no method-outcome predicates',
        targets='recorded source operations; governing/local goals, adoption and stable values unobserved',
        comparison_scope='source-bound provider and metric validation; new reader comparisons remain separate cards',
        controls=dict(all_source_replays=True,all_unknown_zero_yield=metrics([],truth)['supported_useful_events']==0,
            mislocated_not_useful=metrics([bad],truth)['correctly_located_useful_events']==0,
            correct_location_counted=metrics([good],truth)['correctly_located_useful_events']==1),
        files={p.name:filehash(p) for p in out.glob('*.json') if p.name in ('PACKETS.json','EVALUATOR_ONLY.json','METRICS.json','CONSTRUCTED_NULL.json')})

def human_freeze(out,card,pulse,raw):
    from .population import previous,matched_donor
    root=raw/'jobs'/card.get('census_card','S12-00');population=read(root/'POPULATION.json');census=read(root/'CENSUS.json')
    labels=read(root/'SOURCE_METADATA.json')['classes']['coauthor']
    # Allocation is inherited from verified writer/prompt components; selection
    # is hash order and session breadth, never current label or reader success.
    selected={}
    for lane,rows in population.items():
        grouped=defaultdict(list)
        for r in sorted(rows,key=lambda r:digest([SEED,lane,r['key']])):
            if lane=='evaluation' and not previous(r,rows):continue
            grouped[r['unit']].append(r)
        selected[lane]=[r for w in sorted(grouped) for r in grouped[w][:card['per_writer_cap']]]
    train=selected['train'];dev=selected['development'];test=selected['evaluation']
    for a,b in [(train,dev),(train,test),(dev,test)]:
        for k in ('unit','stimulus'):
            if {r[k] for r in a}&{r[k] for r in b}:raise ValueError('writer/prompt component crossing')
    counts=[1. for _ in labels]
    writers={r['unit'] for r in train}
    for r in train:counts[labels.index(r['truth'])]+=1/sum(s['unit']==r['unit'] for s in train)
    prior=[v/sum(counts) for v in counts]
    def public_history(rows):
        return [dict(key=r['key'],ordinal=r['ordinal'],evidence=r['views']['artifact'],recorded_handling=r['truth']) for r in rows]
    donors=sorted(population['train'],key=lambda r:digest([SEED,'donor',r['key']]))
    reader=[];evaluation=[]
    for i,r in enumerate(test):
        own=previous(r,population['evaluation']);donor,donor_rows=matched_donor(r,own,donors,population['train'])
        prior_rows=public_history(own)
        if donor['unit']==r['unit'] or donor['stimulus']==r['stimulus']:raise ValueError('donor test component leakage')
        persistent=[float(label==prior_rows[-1]['recorded_handling']) for label in labels] if prior_rows else prior
        # This freezes all predictions for cheap controls before any capable
        # reader evaluation. Donor history comes only from training components.
        reader.append(dict(id=r['key'],evidence=r['views']['artifact'],own_history=prior_rows,
            donor_history=public_history(donor_rows),
            donor_id=donor['key'],labels=labels,prior=prior,persistence=persistent))
        evaluation.append(dict(id=r['key'],truth=r['truth'],writer_component=r['unit'],prompt_component=r['stimulus'],session=r['session']))
    freeze(out/'READER_INPUTS.json',reader);freeze(out/'EVALUATOR_ONLY.json',evaluation)
    freeze(out/'DEVELOPMENT.json',dev);freeze(out/'TRAINING.json',train)
    # Conservative sensitivity, explicitly not the old account/direct variance.
    n=len({r['unit'] for r in test});sensitivity=[dict(assumed_sd=s,n=n,detectable_difference_approx=2.8*s/math.sqrt(n)) for s in (.15,.2301,.35,.5)]
    protocol=dict(id='S-P1',seed=SEED,primary='mean paired half-Brier loss: no history minus own history',
        arms=['own_history','no_history','matched_training_donor','training_prior','persistence'],
        candidate_ids=[r['id'] for r in reader],population='source-defined historically exposed human records',
        status='descriptive; no untouched component established',meaningful_margin=.05,
        uncertainty='writer and prompt dependencies; contrast-specific variance unknown until a completed development comparison',
        sensitivity=sensitivity,model='retained 27B package if admitted; separately named API conceptual replication requires approval',
        complete_microblock=4,maximum_new_interface_repairs=1,per_writer_cap=card['per_writer_cap'],
        zero_support_log_loss='infinite; never retrospectively clipped',secondary=['accuracy','calibration','coverage','cost'],
        constraints=['finish frozen population before outcome-selected expansion','donor training only','no value/endorsement inference'],
        history_eligibility='at least one completed earlier same-session opportunity; exact donor history count matched',
        donor_matching='training components only; same domain preferred, nearest text length, identity hash tie break; no outcome matching')
    freeze(out/'S-P1.json',protocol);pulse(phase='source-freeze-complete')
    return dict(status='complete',kind='infrastructure',eligible_opportunities=len(reader),writer_components=n,
        prompt_components=len({r['stimulus'] for r in test}),unexposed_components=0,
        paired_precision_sensitivity=sensitivity,capable_reader_status='waiting for admitted package and specific permitted allocation',
        controls=dict(writer_prompt_disjoint=True,donors_training_only=True,selection_outcome_blind=True,zero_support_preserved=True),
        files={p.name:filehash(p) for p in out.glob('*.json') if p.name in ('READER_INPUTS.json','EVALUATOR_ONLY.json','DEVELOPMENT.json','TRAINING.json','S-P1.json')})

def process_context(out,card,pulse,raw):
    from runners.stage11_1 import run_v3b as runner
    from runners.stage11_1.cheap import fit,predict
    from runners.stage11_1.score import episode,summarize
    from runners.stage11_1.preflight import source_rows
    from runners.stage11_1.targets import project
    cohort=read(S11/'COHORT-v3.json');by={r['key']:r for r in cohort['discovery']}
    sources=source_rows(S11);model=fit(cohort['train']);rows=[];forecasts=[]
    def forbidden(*a,**k):raise AssertionError('retained comparison cannot dispatch a call')
    runner.api=forbidden
    for key in card['candidate_ids']:
        row=by[key];lines,events=sources[row['session']]
        if project(events[row['ordinal']],lines)!=row['target']:raise ValueError('retained target replay')
        for view in ('artifact','alternatives'):
            arms={'alignment':predict(row['views'][view],model)[0],
                  'marginal_prior':predict(row['views'][view],model,aligned=False)[0]}
            for method in ('direct','review','account'):
                job=read(S11/'jobs'/f'S1-{method}-{row["tranche"]}-v3b'/'JOB.json')
                terminal,parts=runner.execute_block(S11,job,row,view,method)
                if terminal!='COMPLETE':raise ValueError('retained comparison incomplete')
                arms[method]=parts[-1]['forecast']
            for method,forecast in arms.items():
                rows.append(dict(view=view,method=method,**episode(row,forecast)))
                forecasts.append(dict(id=key,view=view,method=method,forecast=forecast))
        pulse(completed_units=len(rows)//10,total=len(card['candidate_ids']))
    if len(rows)!=len(card['candidate_ids'])*10:raise ValueError('incomplete balanced source block')
    summaries={view+':'+method:summarize([r for r in rows if r['view']==view and r['method']==method])
               for view in ('artifact','alternatives') for method in ('alignment','marginal_prior','direct','review','account')}
    freeze(out/'ROWS.json',rows);freeze(out/'FORECASTS.json',forecasts);freeze(out/'COMPARISONS.json',summaries)
    return dict(status='complete',kind='scientific',units=len(card['candidate_ids']),arms=5,evidence_conditions=2,
        scope='descriptive outcome-blind subset of previously landed human comparisons; no independent replication',
        semantic_replay='native source projection and full retained request/response chain, inference disabled',
        controls=dict(all_arms_all_units=True,raw_response_replay=True,source_projection_replay=True,training_only_prior=True),
        files={n:filehash(out/n) for n in ('ROWS.json','FORECASTS.json','COMPARISONS.json')})

def cloud_packet(out,card,pulse,raw):
    apparatus=read(REPO/'results/gear3/G3-S10-READER-1/APPARATUS.json')
    primary_root=raw/'jobs'/card.get('primary_card','S12-03')
    primary=read(primary_root/'S-P1.json')
    inputs=read(primary_root/'READER_INPUTS.json')
    profile=apparatus['profiles']['27b']
    planned=[]
    for r in inputs:
        for condition in ('own_history','no_history','matched_training_donor'):
            history=r['own_history'] if condition=='own_history' else r['donor_history'] if condition=='matched_training_donor' else []
            planned.append(dict(id=digest([r['id'],condition]),source_id=r['id'],condition=condition,
                public=dict(task='Recover the recorded handling of the displayed suggestion menu.',
                    evidence=r['evidence'],earlier_completed_handling=history,labels=r['labels']),
                model_profile=profile,maximum_output_tokens=512))
    blocks=[planned[i:i+12] for i in range(0,len(planned),12)]
    request=dict(schema='s12.cloud-review.1',dispatch_authorized=False,dispatched_dollars=0,
        task='S-P1 correct earlier human session history versus no history, with training-only donor and cheap controls',
        exact_replication=dict(profile=profile,image=apparatus['image'],source_package_receipt_sha256=filehash(REPO/'results/gear3/G3-S10-READER-1/APPARATUS.json')),
        population=primary['population'],candidate_ids=primary['candidate_ids'],calls=len(planned),
        blocks=len(blocks),maximum_calls_per_block=12,all_three_reader_conditions_per_source=True,
        source_permission='existing retained CoAuthor projection for prior approved Modal route; confirm current source grant before a new dispatch',
        new_provider_permission='not granted; no API upload',
        proposal=dict(pilot_gross_cap_dollars=20,optional_week_cap_dollars=50,
            allocation=dict(admission=3,primary=17,source_extension=15,conditional_causal=5,reserve=10)),
        billing='gross charges including startup/loading/failure/storage; credits unknown and do not increase cap',
        pricing='brief reference only; verify current provider quote and exact pilot cost before approval',
        account_limits='inspect read-only existing ledger and current provider limits before a concrete spend request',
        deadline=read(raw/'CONTRACT.json')['reporting'],
        uncertain_call='retain request and full reservation; retrieve by request identity before any retry',
        cancellation='between complete four-source blocks; stop/checkpoint child at deadline; no detached unowned worker',
        retrieval='full raw request/response, model/context/residency, timing, source hashes and immutable complete-block receipt',
        acceptance='independent offline semantic replay, full finite distributions and complete roster; no success-by-exit',
        current_blockers=['new specific allocation absent','current provider quote/credit inspection pending',
                          'original cloud launcher absent from current tree; recover and verify pinned implementation before dispatch'])
    freeze(out/'REQUESTS.json',planned);freeze(out/'MICROBLOCKS.json',blocks);freeze(out/'REVIEW_PACKET.json',request)
    pulse(phase='cloud-preparation-only')
    return dict(status='complete',kind='infrastructure',prepared_calls=len(planned),blocks=len(blocks),dispatch_dollars=0,
        exact_model_digest=profile['model_digest'],source_support=primary['status'],
        preparation_status='bounded request and comparison packet; funding and exact launcher verification remain admission prerequisites',
        controls=dict(no_dispatch=True,all_reader_conditions=True,private_evaluators_excluded=True,prior_approval_not_reused=True),
        files={n:filehash(out/n) for n in ('REQUESTS.json','MICROBLOCKS.json','REVIEW_PACKET.json')})

def cloud_result(out,card,pulse,raw):
    """Offline consumer only; a submitted receipt is not an implicit dispatch."""
    cloud=raw/'jobs'/card.get('cloud_card','S12-07');primary=raw/'jobs'/card.get('primary_card','S12-03')
    expected=read(cloud/'REQUESTS.json');truth=read(primary/'EVALUATOR_ONLY.json')
    incoming=read(raw/'inputs/CAPABLE_READER_RESULTS.json')
    if incoming.get('source_request_sha256')!=filehash(cloud/'REQUESTS.json'):
        raise ValueError('capable reader request population differs')
    forecasts={r['id']:r for r in incoming['rows']}
    if len(forecasts)!=len(expected) or set(forecasts)!={r['id'] for r in expected}:raise ValueError('incomplete capable-reader population')
    by={r['id']:r for r in truth};rows=[]
    for r in expected:
        saved=forecasts[r['id']];response=saved['raw_response']
        # The provider-specific raw response adapter must be explicitly named.
        # This canonical retrieval interface accepts only the finite probabilities
        # actually returned, never a post hoc reinterpretation of free prose.
        if saved['request']!=r or response.get('schema')!='s12.reader-response.1':raise ValueError('unreplayed provider request/response')
        labels=r['public']['labels'];target=[float(x==by[r['source_id']]['truth']) for x in labels]
        rows.append(dict(id=r['source_id'],condition=r['condition'],writer_component=by[r['source_id']]['writer_component'],
            prompt_component=by[r['source_id']]['prompt_component'],score=distribution(response.get('probabilities'),target)))
        if len(rows)%12==0:pulse(completed=len(rows),total=len(expected))
    freeze(out/'REPLAYED_ROWS.json',rows)
    return dict(status='complete',kind='scientific',rows=len(rows),scope='frozen descriptive S-P1, provider-specific package declared by retrieval',
        controls=dict(complete_request_population=True,raw_request_response_replay=True,zero_support_preserved=True),
        files={'REPLAYED_ROWS.json':filehash(out/'REPLAYED_ROWS.json')})
