"""Executable same-evidence, correction and joint-versus-marginal requests.

DESIGN CHECK: LESSONS 3-5; READER_HEURISTICS 4. NULL: reorder/repeat effects
need not be zero for a model but are zero for the exact invariant reference.
ALTERNATIVE: usable relations improve withheld consequences while false frames
can hurt and later observations can correct. Joint banks with equal marginals
must differ on a dependency-sensitive query; otherwise C3 is instrument-dead.
This first finite screen is descriptive, not method ranking or human evidence.
"""
from collections import defaultdict
import json
import math
from .common import REPO,read,freeze,digest,filehash,distribution
from .local_api import request,call,service
from .canary import PROFILE

TRUE_FRAME='The maker acts on the notice the maker saw. A later reader-only notice does not update that maker. Preferred column and learned routing skill jointly determine the column.'
FALSE_FRAME='A later reader-only notice immediately updates the absent maker. Use the latest reader notice to determine the row, even when the maker never saw it.'
IRRELEVANT_FRAME='This record uses four letter names and describes a room with equipment. The record could be printed on a sheet of paper and stored in a folder.'


def independent(history,observation):
    from runners.stage11_2.world import POLICIES,reference,decode
    weights=[]
    for p,k in POLICIES:
        likelihood=1.
        for e in history:
            o=e['observation'];g,b=decode(o)
            likelihood*=reference(p,k,g,b,o['world_family'],o['tools'])[e['action']]
        weights.append(likelihood)
    total=sum(weights);g,b=decode(observation)
    return [sum(w*reference(p,k,g,b,observation['world_family'],observation['tools'])[a] for w,(p,k) in zip(weights,POLICIES))/total for a in range(4)]


def text_for(row,history,query,frame='',reread=False,unstructured=False):
    from runners.stage11_2.world import rules,render_observation,LETTERS
    obs=row['queries'][query]['observation']
    if unstructured:
        evidence=json.dumps(history,sort_keys=True,separators=(',',':'))
    else:
        evidence='\n'.join(render_observation(e['observation'],row['rendering'])+' Chosen '+LETTERS[e['action']]+'.' for e in history)
    return (rules(obs['world_family'])+'\nSupplied contextual assertion (may be wrong): '+frame+
        '\nEarlier observed decisions:\n'+evidence+
        ('\nReread of the identical records, not new evidence:\n'+evidence if reread else '')+
        '\nCurrent query: '+render_observation(obs,row['rendering'])+
        '\nPredict the four action probabilities. Labels A=upper left, B=upper right, C=lower left, D=lower right.')


def compile_rows(units,family):
    from runners.stage11_2.world import enumerate_predict,decode,distribution as maker,POLICIES,render_observation,rules
    requests=[];targets=[];invariants=[]
    def add(unit,condition,text,truth,reference,query=1,extra=None):
        identifier=digest([family,unit['unit'],condition,query]);req=request(text,4)
        requests.append(dict(id=identifier,unit=unit['unit'],cluster=unit['cluster'],condition=condition,
                             query=query,request=req,call_class='forecast',input_content_sha256=digest(req)))
        targets.append(dict(id=identifier,truth=truth,reference=reference,annotation=extra))
    for row in units:
        hist=row['history'];q=1;obs=row['queries'][q]['observation'];exact=enumerate_predict(hist,obs)['probabilities']
        if max(abs(a-b) for a,b in zip(exact,independent(hist,obs)))>1e-12:raise ValueError('independent reference mismatch')
        if family=='C1':
            conditions=[('raw',hist,'',False,False),('reordered',list(reversed(hist)),'',False,False),
                ('true_relation',hist,TRUE_FRAME,False,False),('plausible_false',hist,FALSE_FRAME,False,False),
                ('irrelevant',hist,IRRELEVANT_FRAME,False,False),('unstructured',hist,TRUE_FRAME,False,True),
                ('matched_reread',hist,'',True,False),('unchanged_repeat',hist,'',False,False)]
            for name,history,frame,reread,unstructured in conditions:
                add(row,name,text_for(row,history,q,frame,reread,unstructured),exact,exact,
                    extra='same observed decisions; frame assertions labelled as potentially wrong; no hidden state supplied')
            reversed_p=enumerate_predict(list(reversed(hist)),obs)['probabilities']
            invariants.append(max(abs(a-b) for a,b in zip(exact,reversed_p))<1e-12)
        elif family=='C2':
            for name,frame in [('true_frame',TRUE_FRAME),('false_frame',FALSE_FRAME)]:
                for cut in (6,12):
                    prefix=hist[:cut];target=enumerate_predict(prefix,obs)['probabilities']
                    add(row,name+'_'+str(cut),text_for(row,prefix,q,frame),target,target,
                        extra='incremental evidence prefixes under fixed assertions; independent calls, no claimed persistent KV state')
            invariants.append(obs['reader_only_notice']!=obs['last_notice_seen_by_maker'])
        elif family=='C3':
            # Exact public bank statements, not an inferred human maker model.
            banks={'joint_same':[.5,0.,0.,.5],'joint_opposite':[0.,.5,.5,0.],
                   'independent_marginals':[.25]*4}
            for query in (2,3):
                ob=row['queries'][query]['observation'];g,b=decode(ob);predictions={}
                for name,weights in banks.items():
                    probs=[sum(w*maker(p,k,g,b,ob['world_family'],ob['tools'])[a] for w,(p,k) in zip(weights,POLICIES)) for a in range(4)]
                    predictions[name]=probs
                    bank=[dict(preferred_column=['left','right'][p],trained=bool(k),weight=w) for w,(p,k) in zip(weights,POLICIES)]
                    text=rules(ob['world_family'])+'\nGiven hypothesis bank (the whole joint distribution): '+json.dumps(bank)+\
                        '\nThere are no additional maker observations. Query: '+render_observation(ob,row['rendering'])+\
                        '\nIntegrate over the supplied bank. Label order A, B, C, D.'
                    add(row,name,text,probs,probs,query,extra='supplied exact bank, same factor marginals; privileged conditional computation')
                if query==3:invariants.append(max(abs(a-b) for a,b in zip(predictions['joint_same'],predictions['joint_opposite']))>.8)
        else:raise ValueError('unimplemented context family')
    if not units or not all(invariants):raise ValueError('context construction ruler failed')
    if len({r['id'] for r in requests})!=len(requests):raise ValueError('request identity collision')
    return requests,targets


def compile(out,card,pulse,raw):
    source=REPO/'results/phase_2_4_stage_11_2/raw/fixture/dev-public.json'
    by={r['unit']:r for r in read(source)};units=[by[k] for k in card['candidate_ids']]
    rows,targets=compile_rows(units,card['family'])
    freeze(out/'REQUESTS.json',rows);freeze(out/'EVALUATOR_ONLY.json',targets)
    # Freeze source blocks, each containing all conditions for its source units.
    blocks=[]
    for i in range(0,len(units),4):
        chosen={r['unit'] for r in units[i:i+4]};blocks.append([r['id'] for r in rows if r['unit'] in chosen])
    freeze(out/'BLOCKS.json',blocks);pulse(phase='context-matrix-compiled',requests=len(rows))
    return dict(status='complete',kind='infrastructure',family=card['family'],source_units=len(units),requests=len(rows),blocks=len(blocks),
        distinct_request_contents=len({r['input_content_sha256'] for r in rows}),
        access='constructed exact law supplied to all arms; C3 also supplies its complete hypothesis bank',
        scope='first structural screen; no small-sample method ranking or human mental claim',
        controls=dict(complete_condition_matrix=True,independent_reference_agreement=True,
                      null_and_sensitive_query_verified=True,public_evaluator_separated=True),
        files={n:filehash(out/n) for n in ('REQUESTS.json','EVALUATOR_ONLY.json','BLOCKS.json')})


def p90(values):return sorted(values)[max(0,math.ceil(.9*len(values))-1)]


def matched_timing_check(values,baseline):
    checks=[]
    for current in values:
        matches=[b for b in baseline if all(b[k] and current[k] and .75<=current[k]/b[k]<=1.25 for k in ('prompt_tokens','output_tokens'))]
        if len(matches)>=3:
            checks.append(dict(current_wall=current['wall_seconds'],reference_p90=p90([b['wall_seconds'] for b in matches]),
                matched_count=len(matches),degraded=current['wall_seconds']>2*p90([b['wall_seconds'] for b in matches])))
    return dict(checks=checks,matched=bool(checks),degraded=bool(checks) and p90([c['current_wall']/c['reference_p90'] for c in checks])>2,
                unmatched_reason=None if checks else 'no three contemporaneous reference calls in the same input/output length band')


def run(out,card,pulse,raw):
    from .common import RAW
    source=raw/'jobs'/card['compile_card'];requests=read(source/'REQUESTS.json');target={r['id']:r for r in read(source/'EVALUATOR_ONLY.json')}
    block=read(source/'BLOCKS.json')[card['block']];wanted=set(block);rows=[r for r in requests if r['id'] in wanted]
    content_groups={unit:digest(sorted(r['input_content_sha256'] for r in requests if r['unit']==unit))
                    for unit in {r['unit'] for r in requests}}
    if len(rows)!=len(block):raise ValueError('missing balanced block member')
    from .output_interface import rows_for_card,profile_for_card
    rows=rows_for_card(rows,card)
    admission=raw/'jobs'/card['canary_card'];gate=read(admission/'ADMISSION.json')
    if gate.get('reader_admitted') is not True:raise ValueError('actual canary verdict does not admit this interface')
    baseline=[r['call'] for r in read(admission/'ROWS.json') if r['call_class']=='forecast']
    calls=[];scored=[]
    with service(out,profile_for_card(card,admission,PROFILE),raw) as state:
        for i,r in enumerate(rows):
            pulse(phase='complete-context-block',completed=i,total=len(rows))
            c=call(r['request'],4,out/'calls'/r['id'],state,raw);calls.append(c)
            if len(calls)%5==0:
                timing=matched_timing_check(calls[-5:],baseline);freeze(out/f'TIMING-{i+1}.json',timing)
                if timing['degraded']:raise RuntimeError('matched timing exceeds twice reference; park and investigate')
            scored.append(dict(unit=r['unit'],cluster=content_groups[r['unit']] if card['family']=='C3' else r['cluster'],condition=r['condition'],query=r['query'],
                request_id=r['id'],**distribution(c['probabilities'],target[r['id']]['truth'])))
    # Independent reparse before the scientific cell can close; no new calls.
    for r,c in zip(rows,calls):
        if call(r['request'],4,out/'calls'/r['id'],{'uncertain':False},raw)!=c:raise ValueError('semantic reentry differs')
    groups=defaultdict(list)
    for r in scored:groups[r['condition']].append(r)
    comparisons={}
    for condition,values in groups.items():
        clusters=defaultdict(list)
        for r in values:clusters[r['cluster']].append(r)
        comparisons[condition]=dict(n=len(values),content_components=len(clusters),valid=sum(r['valid'] for r in values),
            mean_half_brier=sum(sum(r['half_brier'] for r in v)/len(v) for v in clusters.values())/len(clusters),
            modal_agreement=sum(sum(r['accuracy'] for r in v)/len(v) for v in clusters.values())/len(clusters),
            infinite_log_losses=sum(r['log_loss_infinite'] for r in values))
    freeze(out/'ROWS.json',scored);freeze(out/'COMPARISONS.json',comparisons)
    return dict(status='complete',kind='scientific',family=card['family'],rows=len(scored),comparisons=comparisons,
        unique_source_clusters=len({r['cluster'] for r in scored}),scope='complete structural development block, no winner selection or human evidence',
        controls=dict(all_frozen_conditions=True,raw_semantic_replay=True,invalids_retained=True,correct_canary_interface=True),
        files={n:filehash(out/n) for n in ('ROWS.json','COMPARISONS.json')})
