"""Bounded execution and whole-roster consumers for the approved local program.

DESIGN CHECK: LESSONS 3-5. NULL: repeats replay without dispatch and invalids
keep maximum error; an incomplete roster never becomes a null finding.
ALTERNATIVE: paired source-cluster contrasts survive known-answer controls.
Unknown outcomes, altered targets, missing dependent replies and budget expiry
stop execution; independent cards remain eligible. No fit or cloud transport.
"""
from collections import defaultdict
from contextlib import nullcontext
from copy import deepcopy
import json
import math
from pathlib import Path
import random
import statistics
from .common import read,freeze,filehash,digest,distribution
from . import local_api
from .output_interface import adapt,VERSION
from .program_world import validate_rows
from .program_queries import materialize


def canonical(p,order):
    if p is None:return None
    if sorted(order)!=list(range(len(p))):raise ValueError('invalid label inverse')
    answer=[0.]*len(p)
    for i,j in enumerate(order):answer[j]=p[i]
    return answer


def effective(spec,finished,bodies):
    r=materialize(spec,finished) if spec.get('dynamic')=='query' else deepcopy(spec)
    text=r['text']
    if r.get('saved_reply'):
        text+='\nActual earlier reply, retained verbatim even if invalid; it is fallible, not additional evidence:\n'+bodies[r['saved_reply']]['message']['content']
    if r.get('memory_reply'):
        key=r['memory_reply'];previous=next(x for x in finished if x['id']==key)
        if previous['probabilities'] is None:raise ValueError('failed memory acquisition, no substitute')
        body=json.loads(bodies[key]['message']['content'])
        text+='\nAcquired memory (future questions were not supplied):\n'+body['analysis']
    return r,adapt(local_api.request(text,r['n'],r['call_class']),VERSION)


def score(r,value):
    p=canonical(value['probabilities'],r['label_order']);q=r['target'];measure=distribution(p,q)
    # Retain factor labels but do not duplicate the private source passage.
    result={k:v for k,v in r.items() if k not in ('text','source')}
    result.update(probabilities=p,score=measure,exact_reference=distribution(q,q),
        excess_half_brier=measure['half_brier']-distribution(q,q)['half_brier'],
        uniform_reference=distribution([1/r['n']]*r['n'],q),wall_seconds=value['wall_seconds'])
    if r.get('supplied_answer') is not None:
        result['copy_max_error']=None if value['probabilities'] is None else max(abs(a-b) for a,b in zip(value['probabilities'],r['supplied_answer']))
    if r['family']=='LP08':
        buy=None if p is None else sum(x for x,label in zip(p,r['decision_labels']) if label=='buy')
        result['buy_probability']=buy
        result['decision_regret']=1. if buy is None else abs(r['offer_gain']-r['cost'])*float((buy>.5)!=r['optimal_buy'])
        result['current_forecast']=None if p is None else [p[i]+p[i+4] for i in range(4)]
        result['current_forecast_score']=distribution(result['current_forecast'],r['forecast_target'])
    if r.get('information_values'):
        result['selected_information']=None if p is None else r['information_values'][max(range(len(p)),key=p.__getitem__)]['information']
    cheap=dict(r.get('cheap_references',{}))
    for field in ('cheap_reference','prior','persistence'):
        if r.get(field) is not None:cheap[field]=r[field]
    result['cheap_scores']={name:distribution(v,q) for name,v in cheap.items()}
    return result


def run(out,card,pulse,raw):
    raw=Path(raw);specs=read(card['rows_path']);validate_rows(specs)
    if digest(specs)!=card['rows_digest'] or len(specs)!=card['calls']:raise ValueError('frozen program roster differs')
    is_hf=bool(card.get('hf_model'));replay=all((out/'calls'/r['id']/'COMPLETE.json').exists() for r in specs)
    if is_hf:
        from .program_hf import service,call
        manager=nullcontext({}) if replay else service(out,card,raw)
    else:
        reader_gate=read(card['admission_path'])
        if reader_gate.get('reader_admitted') is not True:raise ValueError('constructed reader admission unavailable')
        call=local_api.call;manager=nullcontext({'uncertain':False}) if replay else local_api.service(out,card['profile'],raw)
    rows=[];bodies={};receipts=[]
    with manager as state:
        for i,spec in enumerate(specs):
            pulse(phase='program-'+card['family'],completed=i,total=len(specs))
            r,req=effective(spec,rows,bodies);path=out/'calls'/r['id']
            freeze(out/'actual-requests'/(r['id']+'.json'),dict(request=req,materialized_row_sha256=digest(r)))
            if is_hf:value=call(req,r['n'],path,state,raw,card)
            else:value=call(req,r['n'],path,state,raw,diagnostic=card.get('diagnostic',False))
            bodies[r['id']]=read(path/'RAW.json');receipts.append((req,r,path,value));result=score(r,value)
            freeze(out/'scored'/(r['id']+'.json'),result);rows.append(result)
    # Actual parser/request reentry, not just a metadata checksum.
    for req,r,path,value in receipts:
        again=call(req,r['n'],path,{},raw,card) if is_hf else call(req,r['n'],path,{'uncertain':False},raw)
        if again!=value:raise ValueError('raw semantic replay differs')
    freeze(out/'ROWS.json',rows)
    report=dict(status='complete',kind='scientific',family=card['family'],calls=len(rows),
        controls=dict(full_frozen_roster=True,raw_semantic_replay=True,invalids_retained=True,no_hidden_target_in_requests=True),
        files={'ROWS.json':filehash(out/'ROWS.json')})
    if card.get('admission'):
        # Known-answer assistance is explicit and excluded from later science.
        a=admission(rows,card['family']);admitted=a['reader_admitted']
        freeze(out/'ADMISSION.json',a);report.update(kind='infrastructure',reader_admitted=admitted)
        if admitted:freeze(out/'READY.json',dict(status='complete',admission_sha256=digest(a)))
        report['files']['ADMISSION.json']=filehash(out/'ADMISSION.json')
    return report


def admission(rows,family):
    tested=[r for r in rows if r.get('view')=='witness'] if family=='LP16' else rows
    valid=bool(rows) and all(r['score']['valid'] for r in rows)
    correct=sum(r['score']['accuracy'] for r in tested)
    admitted=valid and correct>=math.ceil(.875*len(tested)) and bool(tested)
    return dict(reader_admitted=admitted,rows=len(rows),known_answer_rows=len(tested),literal_valid=valid,correct=correct,scope=family+' narrow assisted interface only; no broad human-history admission')


def interval(values,seed=120923,alpha=.05):
    if not values:raise ValueError('empty independent-unit contrast')
    rng=random.Random(seed);n=len(values);draws=sorted(sum(rng.choices(values,k=n))/n for _ in range(4000))
    return dict(n_clusters=n,mean=statistics.mean(values),low=draws[int(alpha/2*len(draws))],high=draws[min(len(draws)-1,int((1-alpha/2)*len(draws)))],level=1-alpha)


def disposition(ci,margin=.02):
    if ci['high'] < -margin:return 'BENEFIT'
    if ci['low'] > margin:return 'HARM'
    if ci['low']>=-margin and ci['high']<=margin:return 'EQUIVALENT'
    return 'UNRESOLVED'


def paired(rows,left,right,key,field='excess_half_brier',alpha=.05):
    a={key(r):r for r in rows if left(r)};b={key(r):r for r in rows if right(r)}
    if not a or a.keys()!=b.keys():raise ValueError('unpaired primary contrast')
    groups=defaultdict(list)
    for k in a:groups[a[k]['cluster']].append(a[k][field]-b[k][field])
    ci=interval([statistics.mean(v) for v in groups.values()],alpha=alpha)
    return dict(**ci,margin=.02,disposition=disposition(ci),direction='left loss minus right loss; negative favors left')


def consume(out,card,pulse,raw):
    rows=[]
    for job in card['source_jobs']:
        p=Path(raw)/'jobs'/job;terminal=read(p/'COMPLETE.json')
        for name,h in terminal['output_files'].items():
            if filehash(p/name)!=h:raise ValueError('source result changed')
        rows.extend(read(p/'ROWS.json'))
    if len(rows)!=card['calls'] or len({r['id'] for r in rows})!=len(rows):raise ValueError('whole-family roster incomplete')
    main=[r for r in rows if not r.get('development') and r['role'] not in ('acquisition','selection')]
    groups=defaultdict(list)
    for r in main:groups[(r['method'],r['condition'])].append(r)
    aggregates=[]
    for (method,condition),values in sorted(groups.items()):
        units=defaultdict(list)
        for r in values:units[r['cluster']].append(r['excess_half_brier'])
        aggregates.append(dict(method=method,condition=condition,attempts=len(values),clusters=len(units),
            invalid=sum(not r['score']['valid'] for r in values),infinite=sum(r['score']['log_loss_infinite'] for r in values),
            cluster_weighted_excess=statistics.mean(statistics.mean(v) for v in units.values()),
            attempt_weighted_loss=statistics.mean(r['score']['half_brier'] for r in values),
            cluster_interval=interval([statistics.mean(v) for v in units.values()])))
    contrasts={};f=card['family'];alpha=.025 if f.startswith('LP21') else .05
    if f in ('LP04','LP21-revision'):
        for frame in ('true','false','neutral'):
            v=[r for r in main if r.get('frame')==frame and r.get('update')=='diagnostic']
            contrasts[frame+'_saved_minus_fresh']=paired(v,lambda r:r['mode']=='saved',lambda r:r['mode']=='fresh',lambda r:(r['unit'],r['method']),alpha=alpha)
        by={(r['unit'],r['method'],r.get('frame'),r.get('mode')):r for r in main if r.get('update')=='diagnostic'}
        interactions=defaultdict(list)
        for unit,method in {(r['unit'],r['method']) for r in main}:
            diff=lambda frame:by[unit,method,frame,'saved']['excess_half_brier']-by[unit,method,frame,'fresh']['excess_half_brier']
            interactions[by[unit,method,'true','fresh']['cluster']].append(diff('false')-diff('true'))
        ci=interval([statistics.mean(v) for v in interactions.values()],alpha=alpha)
        contrasts['primary_false_minus_true_saved_penalty']=dict(**ci,margin=.02,disposition=disposition(ci))
    elif f in ('LP07','LP21-query'):
        v=[r for r in main if r.get('step')==3]
        contrasts['primary_counterexample_minus_neutral']=paired(v,lambda r:r['policy']=='counterexample',lambda r:r['policy']=='neutral',lambda r:r['unit'],alpha=alpha)
    elif any(r['method']=='account' for r in main) and any(r['method']=='direct' for r in main):
        contrasts['account_minus_direct']=paired(main,lambda r:r['method']=='account',lambda r:r['method']=='direct',lambda r:(r['unit'],r['condition'],r['query']))
    def conditions(a,b):
        contrasts[a+'_minus_'+b]=paired(main,lambda r:r['condition']==a,lambda r:r['condition']==b,lambda r:(r['unit'],r['method'],r['query']))
    if f=='LP01':
        for a,b in [('repeat','canonical'),('reversed_options','canonical'),('permuted_labels','canonical'),('evidence_last','evidence_first')]:conditions(a,b)
    elif f=='LP02':
        for a,b in [('bank','single'),('labels','bank'),('distractor','bank'),('wrong','single'),('single','unaided')]:conditions(a,b)
    elif f=='LP06':
        for a in ('duplicate','restatement','independent','irrelevant'):conditions(a,'single')
    elif f=='LP10':
        for a in ('indexed','summary','structured','exact_state','fact_table'):conditions(a,'raw')
    elif f=='LP11':
        for dose in (1,2,4):
            for source in ('donor','domain','irrelevant'):conditions('own-'+str(dose),source+'-'+str(dose))
    elif f=='LP12':
        for cut in (1,8):
            for a in ('omit','extra'):conditions(a+'-'+str(cut),'complete-'+str(cut))
    elif f in ('LP13','LP16','LP17','LP18'):
        baseline={'LP13':'artifact','LP16':'current','LP17':'current','LP18':'artifact'}[f]
        for a in sorted({r['condition'] for r in main}-{baseline}):conditions(a,baseline)
    if f=='LP05':
        v=[r for r in main if 'correct_prior' in r]
        contrasts['incorrect_minus_correct_prior']=paired(v,lambda r:not r['correct_prior'],lambda r:r['correct_prior'],lambda r:(r['unit'],r['method'],r['update'],r['stated_confidence'],r['claimed_owner']))
        contrasts['self_minus_other_attribution']=paired(v,lambda r:r['claimed_owner']=='self',lambda r:r['claimed_owner']=='other',lambda r:(r['unit'],r['method'],r['update'],r['stated_confidence'],r['correct_prior']))
        contrasts['high_minus_low_claimed_confidence']=paired(v,lambda r:r['stated_confidence']=='high',lambda r:r['stated_confidence']=='low',lambda r:(r['unit'],r['method'],r['update'],r['claimed_owner'],r['correct_prior']))
    if f=='LP09':
        for reliability in (.5,.75,.9):
            for cue in ('support','oppose'):conditions(str(reliability)+'-'+cue,str(reliability)+'-absent')
    decision=[]
    if f=='LP08':
        for purpose,cost in sorted({(r['purpose'],r['cost']) for r in main}):
            v=[r for r in main if r['purpose']==purpose and r['cost']==cost]
            decision.append(dict(purpose=purpose,cost=cost,attempts=len(v),invalid=sum(r['probabilities'] is None for r in v),mean_selection_regret=statistics.mean(r['decision_regret'] for r in v),
                always_stop_regret=statistics.mean(max(0.,r['offer_gain']-r['cost']) for r in v),always_buy_regret=statistics.mean(max(0.,r['cost']-r['offer_gain']) for r in v),margin_utility_units=.01))
    coverage=[]
    for threshold in (0.,.25,.5,.6,.7,.8,.9,1.):
        kept=[r for r in main if r['probabilities'] is not None and max(r['probabilities'])>=threshold]
        coverage.append(dict(threshold=threshold,attempts=len(main),retained=len(kept),coverage=len(kept)/len(main) if main else 0,mean_loss=statistics.mean(r['score']['half_brier'] for r in kept) if kept else None,invalid=sum(r['probabilities'] is None for r in main)))
    diagnostic=calibration(main)
    report=dict(status='complete',kind='scientific',family=f,calls=len(rows),main_calls=len(main),aggregates=aggregates,contrasts=contrasts,coverage=coverage,calibration=diagnostic,decision_regret=decision,
        multiplicity='LP21 uses 97.5% intervals for its two primary contrasts; no p-values',
        scope='Frozen source-cluster descriptive comparisons; supplied targets, restricted human exposure and native mechanism limits retained',
        controls=dict(whole_family=True,all_attempts=True,cluster_weighting=True,fixed_coverage_grid=True),files={})
    freeze(out/'ANALYSIS.json',report);report['files']={'ANALYSIS.json':filehash(out/'ANALYSIS.json')};return report


def calibration(rows):
    """Fixed bins and paired ranks, no fitted calibrator or chosen threshold."""
    edges=(0.,.2,.4,.6,.8,1.)
    def members(values,lower,upper):
        return [r for r in values if lower<=max(r['probabilities']) and
                (max(r['probabilities'])<upper or upper==1.)]
    groups=defaultdict(list)
    for r in rows:groups[(r['method'],r['n'])].append(r)
    result=[]
    for (method,n),attempts in sorted(groups.items()):
        valid=[r for r in attempts if r['probabilities'] is not None];bins=[]
        for lower,upper in zip(edges,edges[1:]):
            chosen=members(valid,lower,upper)
            if not chosen:continue
            confidence=statistics.mean(max(r['probabilities']) for r in chosen)
            support=statistics.mean(r['target'][max(range(n),key=r['probabilities'].__getitem__)] for r in chosen)
            bins.append(dict(lower=lower,upper=upper,count=len(chosen),confidence=confidence,expected_correct_support=support,gap=confidence-support))
        if sum(b['count'] for b in bins)!=len(valid):raise ValueError('calibration bins do not partition valid attempts')
        if valid:
            # Exact vector-score decomposition; the remainder is retained because
            # finite bins do not make all forecasts within a bin identical.
            qbar=[statistics.mean(r['target'][i] for r in valid) for i in range(n)]
            uncertainty=(1-sum(x*x for x in qbar))/2;reliability=resolution=0.
            for lower,upper in zip(edges,edges[1:]):
                chosen=members(valid,lower,upper)
                if not chosen:continue
                pmean=[statistics.mean(r['probabilities'][i] for r in chosen) for i in range(n)];qmean=[statistics.mean(r['target'][i] for r in chosen) for i in range(n)]
                weight=len(chosen)/len(valid);reliability+=weight*sum((p-q)**2 for p,q in zip(pmean,qmean))/2;resolution+=weight*sum((q-q0)**2 for q,q0 in zip(qmean,qbar))/2
            mean=statistics.mean(r['score']['half_brier'] for r in valid)
            components=dict(valid_only_loss=mean,uncertainty=uncertainty,binned_reliability=reliability,binned_resolution=resolution,within_bin_remainder=mean-(uncertainty+reliability-resolution))
        else:components=None
        result.append(dict(method=method,label_count=n,attempts=len(attempts),invalid=len(attempts)-len(valid),bins=bins,score_components=components))
    pairs=defaultdict(dict)
    for r in rows:
        if r.get('family')=='LP15':pairs[(r['cluster'],r['pair'],r['method'],r['direction'],r['view'])][r['annotation']]=r
    ranks=[]
    for key,pair in pairs.items():
        if set(pair)!={0,1}:raise ValueError('ARIES ranking pair incomplete')
        a,b=pair[1],pair[0];good=a['probabilities'] is not None and b['probabilities'] is not None
        ranks.append(dict(paper=key[0],method=key[2],direction=key[3],view=key[4],valid_pair=good,
            concordance=(float(a['probabilities'][1]>b['probabilities'][1])+.5*float(a['probabilities'][1]==b['probabilities'][1])) if good else None,
            lexical_concordance=float(a['lexical']>b['lexical'])+.5*float(a['lexical']==b['lexical'])))
    return dict(groups=result,paired_ranking=ranks,scope='LP03 zero-call analysis; invalid denominator retained, valid-only decomposition explicitly marked; no calibration fit')
