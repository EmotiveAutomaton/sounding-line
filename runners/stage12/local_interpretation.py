"""Passage-linked local-world reverse and forward reader consumer.

DESIGN CHECK: LESSONS 2-5. NULL: all-unknown has no useful yield; a goal
reported as observed without a goal record is unsupported. ALTERNATIVE:
correctly located witnessed operations can be useful while goals remain
ambiguous. Supplied-law probabilities are an oracle-family reference, not
information made available to learned readers. Repeated public inputs are
one content unit, even when different coefficient lineages generated them.
"""
import json
from collections import defaultdict
from pathlib import Path
from .common import read,freeze,filehash,digest,distribution
from . import local_api
from .ghost_bridge import load_source

CLAIM_FIELDS={'role','status','step','value','span_ids','evidence_refs'}


def validate_body(body):
    if set(body)!={'analysis','probabilities','claims','unknown','next_evidence'}:raise ValueError('interpretation schema')
    if not isinstance(body['analysis'],str) or type(body['unknown']) is not bool or not isinstance(body['next_evidence'],str):raise ValueError('interpretation field types')
    if not isinstance(body['claims'],list) or len(body['claims'])>12:raise ValueError('claim count')
    for c in body['claims']:
        if set(c)!=CLAIM_FIELDS or c['role'] not in ('G','g_t','C_ext','adoption','process','maker_value'):raise ValueError('claim role')
        if c['status'] not in ('observed','inferred','unobserved') or type(c['step']) is not int or c['step'] not in (0,1,2):raise ValueError('claim state')
        if not isinstance(c['value'],str) or not isinstance(c['span_ids'],list) or not isinstance(c['evidence_refs'],list):raise ValueError('claim shape')
        if not all(x in ('unit-0','unit-1','unit-2') for x in c['span_ids']):raise ValueError('absent passage')
        if not all(isinstance(x,str) for x in c['evidence_refs']):raise ValueError('evidence reference type')
    return body


def request(public,question,labels,method):
    req=local_api.request(json.dumps(dict(evidence=public,question=question,labels=labels),sort_keys=True),len(labels),
                          'forecast' if method=='direct' else 'account')
    schema=req['format'];schema['properties'].update(
        claims=dict(type='array',maxItems=12,items=dict(type='object',additionalProperties=False,
            properties=dict(role=dict(type='string',enum=['G','g_t','C_ext','adoption','process','maker_value']),
                status=dict(type='string',enum=['observed','inferred','unobserved']),step=dict(type='integer',minimum=0,maximum=2),
                value=dict(type='string'),span_ids=dict(type='array',items=dict(type='string',enum=['unit-0','unit-1','unit-2'])),
                evidence_refs=dict(type='array',items=dict(type='string'))),required=sorted(CLAIM_FIELDS))),
        unknown=dict(type='boolean'),next_evidence=dict(type='string'))
    schema['required']=list(schema['properties'])
    req['messages'][-1]['content']+='\nAlso return claims, unknown and next_evidence according to this final schema: '+json.dumps(schema,separators=(',',':'))
    req['messages'][-1]['content']+='\nG is governing purpose, g_t a selected local goal, C_ext an external request. Keep adoption and maker values unknown. Passage units are claim=unit-0, evidence=unit-1, presentation=unit-2. Witness refs are observation:STEP. Only witnessed operations may be called observed; latent goals are hypotheses.'
    if len(req['messages'][-1]['content'].encode())+2048>8192:raise ValueError('interpretation context cap')
    return req


def score_claims(body,public,reference):
    observations={e['step']:e for e in public['inputs'].get('observations',[])}
    support={tuple(p['operations']) for p in reference['process_support']}
    claims=body['claims'];covered=set();located=set();contradictions=0;unsupported=0;mental=0
    anchors={'edit-claim':['unit-0'],'repair-evidence':['unit-1'],'replace-presentation':['unit-2']}
    for c in claims:
        if c['status']=='unobserved':continue
        if c['role'] in ('G','g_t','adoption','maker_value') and c['status']=='observed':mental+=1
        if c['role']!='process':continue
        step=c['step'];possible=any(p[step]==c['value'] for p in support)
        if not possible:contradictions+=1
        if c['status']=='observed':
            e=observations.get(step)
            if e is None or c['value']!=e['operation'] or 'observation:'+str(step) not in c['evidence_refs']:unsupported+=1;continue
            covered.add(step)
            expected=anchors.get(c['value'])
            if expected is None and e['before']!=e['after']:
                expected=['unit-'+str(i) for i,(a,b) in enumerate(zip(e['before'],e['after'])) if a!=b]
            # Inspection has no observed attended passage. Do not invent one.
            if expected and sorted(set(c['span_ids']))==expected:located.add(step)
    goal_support={(g['step'],g['goal']) for g in reference.get('goal_support',[]) if g['support']>0}
    proposed={(c['step'],c['value']) for c in claims if c['role']=='g_t' and c['status']!='unobserved'}
    return dict(eligible_witnessed_events=len(observations),supported_witnessed_events=len(covered),
        correctly_located_useful_events=len(located),unsupported_observed_operations=unsupported,
        contradictions=contradictions,unsupported_mental_assertions=mental,
        unknown=body['unknown'],next_discriminator_supplied=bool(body['next_evidence'].strip()),
        next_discriminator_validity='unverified model proposal; not counted as correct evidence',
        inferred_claims=sum(c['status']=='inferred' for c in claims),
        compatible_goal_label_denominator=len(goal_support),compatible_goal_labels_covered=len(proposed&goal_support),
        incompatible_goal_labels=len(proposed-goal_support),
        goal_coverage_semantics='finite compatible labels, not recovered historical private goals')


def to_provider(identifier,public,method,body,correspondence):
    from .provider import packet
    labels=[('claim-off','claim-on'),('evidence-off','evidence-on'),('plain','display')]
    pieces=[labels[i][bit] for i,bit in enumerate(public['inputs']['artifact'])];text='\n'.join(pieces);anchors=[];offset=0
    for i,piece in enumerate(pieces):
        anchors.append(dict(id='unit-'+str(i),start=offset,end=offset+len(piece)));offset+=len(piece)+1
    observations={e['step']:e for e in public['inputs'].get('observations',[])};claims=[]
    for i,c in enumerate(body['claims'] if body else []):
        status='unobserved' if c['status']=='unobserved' else 'inferred'
        spans=c['span_ids'];location='inferred' if spans else 'unobserved';refs=c['evidence_refs']
        if c['role']=='process' and c['step'] in observations:
            e=observations[c['step']];status='observed' if c['value']==e['operation'] else 'contradicted'
            if status=='observed':
                refs=['observation:'+str(c['step'])]
                expected={'edit-claim':['unit-0'],'repair-evidence':['unit-1'],'replace-presentation':['unit-2']}.get(c['value'])
                if expected is None:expected=['unit-'+str(j) for j,(a,b) in enumerate(zip(e['before'],e['after'])) if a!=b]
                location='observed' if expected and sorted(set(spans))==expected else 'unobserved'
                if location=='unobserved':spans=[]
        claims.append(dict(c,id=str(i),slot='step-'+str(c['step']),status=status,asserted_status=c['status'],
            asserted_span_ids=c['span_ids'],asserted_evidence_refs=c['evidence_refs'],span_ids=spans,location_status=location,evidence_refs=refs,
            operation=c['value'] if c['role']=='process' else None,actor='constructed maker',relation='unobserved',
            span_state='located' if spans else 'unknown',support='source witnessed operation' if status=='observed' else 'uncalibrated model hypothesis'))
    result=packet(identifier,dict(endpoint=text,anchors=anchors,source_public=public),method,claims,
        tier=public['tier'],origin='constructed Ghost local world; model-generated claims audited separately')
    result['correspondence_audit']=correspondence
    result['maker_snapshot']=dict(id=digest(public),scope='contextual evidence snapshot, not an identified human or validated persistent values')
    result['next_discriminator']=body['next_evidence'] if body else 'A valid interpretation is unavailable; inspect raw failure before proposing evidence.'
    result['model_valid']=body is not None
    return result


def compile(out,card,pulse,raw):
    source=raw/'jobs'/card['reference_card'];evaluators=read(source/'EVALUATOR_ONLY.json')
    model=load_source(card['generator_source']);public=read(Path(card['export_root'])/'PUBLIC_PACKET.json')['cases']
    seen=set();selected=[]
    for c in sorted(public,key=lambda c:c['case_id']):
        h=digest(c['packet'])
        if h not in seen:selected.append(c);seen.add(h)
    requests=[];targets=[];worlds={};by={r['case_id']:r for r in evaluators}
    for index,c in enumerate(selected):
        original=by[c['case_id']];lineage=int(c['case_id'].split('-')[0])
        if lineage not in worlds:worlds[lineage]=model.enumerate_world(model.law(lineage))
        matches=[r for r in worlds[lineage] if model.project(r,c['packet']['tier'])==c['packet']]
        goal=model.GOALS[index%len(model.GOALS)]
        for direction in ('reverse-local-goal','reverse-process','forward-given-goal'):
            labels=list(model.GOALS) if direction=='reverse-local-goal' else list(model.OPERATIONS)
            subsets=matches if direction!='forward-given-goal' else [r for r in matches if r['steps'][0]['goal']==goal]
            if not subsets:raise ValueError('empty conditional forward support')
            target=[];cheap=[]
            for label in labels:
                field='goal' if direction=='reverse-local-goal' else 'operation'
                target.append(sum(r['probability'] for r in subsets if r['steps'][0][field]==label)/sum(r['probability'] for r in subsets))
                cheap.append(sum(r['steps'][0][field]==label for r in subsets)/len(subsets))
            question=('Infer the selected local goal at step 0; it is not observed.' if direction=='reverse-local-goal' else
                      'Infer the operation at step 0.' if direction=='reverse-process' else
                      'Given that the selected local goal at step 0 was '+goal+', predict its operation. This goal is supplied, not recovered.')
            for method in ('direct','coherent-account'):
                ident=digest([c['case_id'],direction,method]);req=request(c['packet'],question,labels,method)
                requests.append(dict(id=ident,source=index,public=c['packet'],direction=direction,method=method,labels=labels,request=req))
                targets.append(dict(id=ident,oracle_family_target=target,uniform_template_target=cheap,reference=original['exact'],
                    target_role='g_t' if direction=='reverse-local-goal' else 'process',source_case=c['case_id']))
        pulse(phase='local-reader-matrix',completed=index+1,total=len(selected))
    freeze(out/'REQUESTS.json',requests);freeze(out/'EVALUATOR_ONLY.json',targets)
    return dict(status='complete',kind='infrastructure',distinct_sources=len(selected),requests=len(requests),
        scope='all-inspect ambiguity diagnostic, no varied-world capability or human transfer claim',
        controls=dict(public_only=True,forward_reverse_separate=True,duplicate_public_inputs_collapsed=True,all_rivals=True),
        files={n:filehash(out/n) for n in ('REQUESTS.json','EVALUATOR_ONLY.json')})


def run(out,card,pulse,raw):
    source=raw/'jobs'/card['compile_card'];requests=[r for r in read(source/'REQUESTS.json') if r['source'] in card['sources']]
    targets={r['id']:r for r in read(source/'EVALUATOR_ONLY.json')};rows=[];packets=[]
    if len(requests)!=6*len(card['sources']):raise ValueError('unbalanced local source block')
    from .output_interface import rows_for_card,profile_for_card
    requests=rows_for_card(requests,card)
    gate=read(raw/'jobs'/card['canary_card']/'READER_READY.json')
    if gate.get('status')!='complete':raise ValueError('reader not admitted')
    from .context_battery import matched_timing_check
    baseline=read(raw/'jobs'/card['canary_card']/'ROWS.json');recorded=[]
    with local_api.service(out,profile_for_card(card,raw/'jobs'/card['canary_card'],card['profile']),raw) as state:
        for i,r in enumerate(requests):
            pulse(phase='local-interpretation',completed=i,total=len(requests))
            saved=local_api.call(r['request'],len(r['labels']),out/'calls'/r['id'],state,raw)
            recorded.append((r,saved))
            kind='forecast' if r['method']=='direct' else 'account'
            timing=matched_timing_check([saved],[b['call'] for b in baseline if b['call_class']==kind])
            freeze(out/('TIMING-'+r['id']+'.json'),timing)
            if timing['degraded']:raise RuntimeError('matched throughput degraded; preserve incomplete local unit')
            response=read(out/'calls'/r['id']/'RAW.json');body=None
            try:body=validate_body(json.loads(response['message']['content']))
            except (ValueError,KeyError,TypeError):pass
            t=targets[r['id']];p=saved['probabilities'] if body else None
            rows.append(dict(id=r['id'],source=r['source'],method=r['method'],direction=r['direction'],
                oracle_family_score=distribution(p,t['oracle_family_target']),template_score=distribution(p,t['uniform_template_target']),
                correspondence=score_claims(body,r['public'],t['reference']) if body else None,invalid=body is None or p is None))
            packets.append(to_provider(r['id'],r['public'],r['method'],body,rows[-1]['correspondence']))
    for r,saved in recorded:
        if local_api.call(r['request'],len(r['labels']),out/'calls'/r['id'],{'uncertain':False},raw)!=saved:
            raise ValueError('local raw semantic replay differs')
    freeze(out/'ROWS.json',rows);freeze(out/'PACKETS.json',packets)
    return dict(status='complete',kind='scientific',sources=len(card['sources']),rows=len(rows),
        scope='finite alias diagnostic; forward supplied-goal construction separate from reverse goal inference; no human claim',
        controls=dict(all_rivals=True,raw_reparsed=True,invalids_retained=True,goals_not_observations=True),
        files={n:filehash(out/n) for n in ('ROWS.json','PACKETS.json')})
