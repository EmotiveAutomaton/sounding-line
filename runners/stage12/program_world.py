"""Approved local-program projections of the unchanged Stage 11.2 maker law.

DESIGN CHECK: LESSONS 3-5; CONTROLS 5-7. NULL: identities and duplicate
observations preserve the exact target; wrong assistance separates fidelity
from correctness. ALTERNATIVE: independently observed choices change support.
Source duplicates, absent dynamic range, future-query acquisition or an invalid
inverse fail compilation. No changed maker mechanism or additional model fit.
"""
from collections import defaultdict
from copy import deepcopy
import itertools
import json
import math
import random

from .common import digest, distribution
from .context_battery import independent, text_for, TRUE_FRAME, FALSE_FRAME
from .execution_access import rounded_answer
from runners.stage11_2 import world as W

METHODS = ('direct', 'account')
PERM = [2, 0, 3, 1]


def target(unit, history=None, query=1):
    history = unit['history'] if history is None else history
    obs = unit['queries'][query]['observation']
    a = W.enumerate_predict(history, obs)['probabilities']
    b = independent(history, obs)
    if max(abs(x-y) for x,y in zip(a,b)) > 1e-12:
        raise ValueError('independent reference differs')
    return a


def tv(a, b):
    return sum(abs(x-y) for x,y in zip(a,b))/2


def actual_target(unit, query=1):
    # Exact truth stays evaluator-only. Never infer a label from an output.
    index = int(unit['unit'].split('-')[-1])
    p,k = W.POLICIES[index % 4]
    o = unit['queries'][query]['observation']; g,b = W.decode(o)
    return W.reference(p,k,g,b,o['world_family'],o['tools'])


def eligible(unit):
    before = target(unit, unit['history'][:1]); after = target(unit, unit['history'][:8])
    bank = [rounded_answer(target(unit, query=q)) for q in (1,3)]
    return tv(before,after) >= .05 and bank[0] != bank[1]


def roster(start, n, excluded=()):
    """Source-only selection, balanced persistent policy index, no reader outputs."""
    seen = set(excluded); pools = {i:[] for i in range(4)}
    for index in range(start, start+20000):
        u = W.make_unit('dev', index)[0]
        if u['cluster'] in seen or not eligible(u):
            continue
        pools[index % 4].append(u); seen.add(u['cluster'])
        if all(len(v) >= (n+3)//4 for v in pools.values()):
            return [pools[i%4][i//4] for i in range(n)]
    raise ValueError('insufficient distinct diagnostic histories')


def evidence(history, rendering='narrative'):
    return '\n'.join('Event '+str(e['sequence'])+': '+W.render_observation(e['observation'],rendering)+
                     ' Chosen '+W.LETTERS[e['action']]+'.' for e in history)


def question(unit, query=1):
    o=unit['queries'][query]['observation']
    return W.rules(o['world_family'])+'\nCurrent query: '+W.render_observation(o,unit['rendering'])+'\nForecast in A,B,C,D order.'


def row(family, unit, condition, text, truth, method='direct', query=1, **extra):
    if not truth or not distribution(truth,truth)['valid']:
        raise ValueError('invalid reference distribution')
    result=dict(id=digest([family,unit['unit'],condition,method,query])[:24],
        family=family,unit=unit['unit'],cluster=unit['cluster'],condition=condition,
        method=method,query=query,text=text,n=len(truth),target=list(truth),
        reference=list(truth),call_class='account' if method=='account' else 'forecast',
        label_order=list(range(len(truth))),role='forecast')
    result.update(extra)
    return result


def pad_irrelevant(base, longer):
    size=len(longer.encode())-len(base.encode()); marker='\nIrrelevant margin, not maker evidence: '
    if size < len(marker): raise ValueError('no room for matched irrelevant update')
    filler=('Decorative margin only. '*((size//23)+2))[:size-len(marker)]
    answer=base+marker+filler
    if len(answer.encode()) != len(longer.encode()): raise ValueError('length matching failed')
    return answer


def static_rows(family, units, *, donors=None):
    rows=[]
    for ordinal,u in enumerate(units):
        hist=u['history']; short=hist[:1]; long=hist[:8]
        before=target(u,short); after=target(u,long); full=target(u)
        add=lambda c,t,q=full,method='direct',query=1,**kw: rows.append(row(family,u,c,t,q,method,query,**kw))
        if family=='LP01':
            body=evidence(long); ask=question(u)
            base=ask+'\nObserved history:\n'+body
            for c in ('canonical','repeat','reversed_options','permuted_labels','evidence_first','evidence_last'):
                order=list(reversed(range(4))) if c=='reversed_options' else PERM if c=='permuted_labels' else list(range(4))
                text=base
                if c in ('evidence_first','evidence_last'):
                    filler='Irrelevant page margin. '*16
                    text=ask+'\n'+(body+'\n'+filler if c=='evidence_first' else filler+'\n'+body)
                if c in ('reversed_options','permuted_labels'):
                    text+='\nReturn probabilities in this presentation order: '+','.join(W.LETTERS[i] for i in order)+'.'
                add(c,text,after,label_order=order)
        elif family=='LP02':
            bank={str(q):rounded_answer(target(u,query=q)) for q in (1,3)}
            for q in (1,3):
                truth=target(u,query=q)
                for c in ('unaided','single','bank','labels','distractor','wrong'):
                    order=PERM if c=='labels' else list(range(4))
                    answer=bank[str(4-q)] if c=='wrong' else bank[str(q)]
                    shown={str(k):[v[i] for i in order] for k,v in bank.items()}
                    if c=='distractor': shown['99']=[.25]*4
                    if c in ('single','wrong'): shown={str(q):answer}
                    text=text_for(u,hist,q) if c=='unaided' else question(u,q)+'\nSupplied fallible answer bank (assistance): '+json.dumps(shown)+'\nCopy entry '+str(q)+' exactly; do not infer or correct it. Output order '+','.join(W.LETTERS[i] for i in order)+'.'
                    add(c,text,truth,query=q,label_order=order,
                        supplied_answer=None if c=='unaided' else shown[str(q)])
        elif family in ('LP04','LP21-revision'):
            if tv(before,after)<.05: raise ValueError('diagnostic reference lacks movement')
            for frame_name,frame in [('true',TRUE_FRAME),('false',FALSE_FRAME),('neutral','No additional assertion is supplied.')]:
                old=text_for(u,short,1,frame); new=text_for(u,long,1,frame)
                texts={'unchanged':old,'diagnostic':new,'irrelevant':pad_irrelevant(old,new)}
                for method in METHODS:
                    add(frame_name+'-initial',old,before,method,frame=frame_name,update='initial',mode='initial')
                    initial=rows[-1]['id']
                    for update in texts:
                        modes=('saved','fresh') if ordinal%2 else ('fresh','saved')
                        for mode in modes:
                            add(frame_name+'-'+update+'-'+mode,texts[update],after if update=='diagnostic' else before,method,
                                frame=frame_name,update=update,mode=mode,saved_reply=initial if mode=='saved' else None)
        elif family=='LP05':
            winner=max(range(4),key=before.__getitem__)
            for method in METHODS:
                for update,h in [('diagnostic',long),('irrelevant',short)]:
                    base=text_for(u,h,1); truth=after if update=='diagnostic' else before
                    if update=='irrelevant':base=pad_irrelevant(base,text_for(u,long,1))
                    add(update+'-fresh',base,truth,method,update=update,mode='fresh')
                    for correct,confidence,owner in itertools.product((False,True),('low','high'),('self','other')):
                        index=winner if correct else (winner+2)%4
                        vector=[.1]*4;vector[index]=.7
                        prior='An attributed earlier prediction, possibly inaccurate; this attribution is supplied, not proof of an actual prior conversation. Claimed source: '+owner+'. Claimed confidence: '+confidence+'. Vector: '+json.dumps(vector)
                        add(f'{update}-{correct}-{confidence}-{owner}',base+'\n'+prior,truth,method,
                            update=update,correct_prior=correct,stated_confidence=confidence,claimed_owner=owner)
        elif family=='LP06':
            one=evidence(short); two=evidence(hist[:2]); ask=question(u)
            variants={'single':one,'duplicate':one+'\nDuplicate report of the SAME event:\n'+one,
                'restatement':one+'\nSame event restated, not another observation:\n'+evidence(short,'cards'),
                'independent':two,'irrelevant':pad_irrelevant(one,two)}
            for method in METHODS:
                for c,t in variants.items():
                    add(c,ask+'\nObserved evidence:\n'+t,target(u,hist[:2]) if c=='independent' else before,method)
        elif family=='LP09':
            o=u['queries'][1]['observation']; weights=W.enumerate_predict(short,o)['weights']
            bit=int(sum(w for w,pk in zip(weights,W.POLICIES) if pk[0]==1)>.5)
            for method,reliability,cue in itertools.product(METHODS,(.5,.75,.9),('support','oppose','absent')):
                claim=bit if cue=='support' else 1-bit
                adjusted=list(weights) if cue=='absent' else [w*(reliability if pk[0]==claim else 1-reliability) for w,pk in zip(weights,W.POLICIES)]
                adjusted=[w/sum(adjusted) for w in adjusted]
                truth=W.enumerate_predict([],o,adjusted)['probabilities']
                text=text_for(u,short,1)+'\nIndependent binary source: a symmetric channel with declared accuracy '+str(reliability)+'. Calibration illustration: '+str(round(reliability*20))+' correct reports among 20; the declared channel, not this sample, defines reliability.'
                text+='\nNo report supplied.' if cue=='absent' else '\nThis source reports the persistent preferred column is '+('right' if claim else 'left')+'.'
                add(f'{reliability}-{cue}',text,truth,method,reliability=reliability,cue=cue)
        elif family=='LP10':
            acquisition=W.rules(u['world_family'])+'\nEarlier history:\n'+evidence(hist)+'\nNo future question is disclosed. Preserve the observations and useful relations in a bounded memory. Return uniform probabilities as an unused placeholder.'
            ids={}
            for style in ('summary','structured'):
                add('acquire-'+style,acquisition+('\nWrite a concise free summary.' if style=='summary' else '\nOrganize the account by observations, constraints, hypotheses and uncertainty.'),[.25]*4,'account' if style=='structured' else 'direct',query=-1,role='acquisition')
                ids[style]=rows[-1]['id']
            weights=W.enumerate_predict(hist,u['queries'][0]['observation'])['weights']
            # The table is a deterministic representation of observed facts, not answers.
            table=[dict(observation=e['observation'],action=W.LETTERS[e['action']]) for e in hist]
            for q in range(4):
                ask=question(u,q); truth=target(u,query=q)
                views={'raw':evidence(hist),'indexed':evidence(sorted(hist,key=lambda e:(e['observation']['tools']!=u['queries'][q]['observation']['tools'],e['sequence']))),
                       'summary':'','structured':'','exact_state':'Privileged exact posterior weights over (left,untrained),(left,trained),(right,untrained),(right,trained): '+json.dumps(weights),
                       'fact_table':json.dumps(dict(observed_facts=table,unobserved_query_answers='unknown; this table does not supply inferred answers'),separators=(',',':'))}
                for c,t in views.items():
                    add(c,ask+'\nRetained evidence:\n'+t,truth,query=q,memory_reply=ids.get(c))
        elif family=='LP11':
            if donors is None:raise ValueError('donor source missing')
            d=donors[ordinal%len(donors)]
            if d['cluster']==u['cluster']:raise ValueError('self donor')
            current=hist[-2:]; truth=actual_target(u)
            for method,dose,c in itertools.product(METHODS,(1,2,4),('own','donor','domain','irrelevant')):
                previous=hist[:dose] if c=='own' else d['history'][:dose]
                if c=='domain': previous=[donors[(ordinal+j)%len(donors)]['history'][0] for j in range(dose)]
                prior=evidence(previous)
                if c=='irrelevant':prior=('Irrelevant record, unrelated to this maker. '*100)[:len(prior)]
                identity={'own':'same maker','donor':'one different maker','domain':'different makers, one per record','irrelevant':'not maker observations'}[c]
                text=question(u)+'\nPrior experience source: '+identity+'.\n'+prior+'\nCurrent maker observations:\n'+evidence(current)
                add(f'{c}-{dose}',text,truth,method,dose=dose,source_condition=c,
                    reference=target(u,current+(hist[:dose] if c=='own' else [])),target_kind='actual executed maker policy')
        elif family=='LP12':
            generating=int(u['unit'].split('-')[-1])%4
            for method,cut,condition in itertools.product(METHODS,(1,8),('complete','omit','extra')):
                weights=W.enumerate_predict(hist[:cut],u['queries'][1]['observation'])['weights']
                indices=[i for i in range(4) if condition!='omit' or i!=generating]
                labels=[str(W.POLICIES[i]) for i in indices]+['outside listed family']
                probs=[weights[i] for i in indices]+[sum(w for i,w in enumerate(weights) if i not in indices)]
                if condition=='extra':labels.insert(-1,'maker that always stays still (not a listed source-law policy)');probs.insert(-1,0.)
                text=W.rules(u['world_family'])+'\nHistory:\n'+evidence(hist[:cut])+'\nInfer persistent (preferred column bit, training bit), not the next action. Candidate order: '+json.dumps(labels)+'. Keep outside-family support when the listed candidates cannot explain evidence.'
                add(f'{condition}-{cut}',text,probs,method,query=cut,candidate_condition=condition,labels=labels)
        else:
            raise ValueError('unimplemented static family '+family)
    if family in ('LP05','LP06','LP09','LP11'):
        paired=defaultdict(list)
        for r in rows:paired[(r['unit'],r['method'],r.get('dose'))].append(r)
        for group in paired.values():
            width=max(len(r['text'].encode()) for r in group)
            for r in group:
                # ASCII-space padding changes no evidence or treatment assertion.
                r['text']+=' '*(width-len(r['text'].encode()))
                r['matched_input_bytes']=width
    validate_rows(rows)
    return rows


def validate_rows(rows):
    if not rows or len({r['id'] for r in rows})!=len(rows):raise ValueError('empty or duplicate request IDs')
    for r in rows:
        if sorted(r['label_order'])!=list(range(r['n'])):raise ValueError('label inverse not bijective')
        if not distribution(r['target'],r['target'])['valid']:raise ValueError('invalid evaluator target')
    return True


def twin_rows(pairs):
    rows=[]
    for a,b in pairs:
        artifact=[e['action'] for e in a['history'][-4:]]
        if artifact != [e['action'] for e in b['history'][-4:]]:raise ValueError('not an artifact twin')
        cluster=digest(['LP13-artifact',artifact])
        candidates=[evidence(u['history'][-4:]) for u in (a,b)]
        base='The artifact records only four resulting choices: '+json.dumps(artifact)+'. Candidate routes have equal prior probability within this selected pair. Exactly these two routes are possible here.\nRoute 0:\n'+candidates[0]+'\nRoute 1:\n'+candidates[1]+'\nInfer the historical route. Output order: route 0, route 1. A claimed context alone is not verified evidence.'
        for member,method,view in itertools.product(range(2),METHODS,('artifact','witness','misleading')):
            unit=dict(unit=a['unit']+'-pair-'+str(member),cluster=cluster)
            text=base
            if view=='witness':text+='\nVerified route observation:\n'+candidates[member]
            if view=='misleading':text+='\nAn unverified, experimentally assigned frame claims route '+str(1-member)+'. Assignment is independent of actual route.'
            truth=[float(i==member) for i in range(2)] if view=='witness' else [.5,.5]
            rows.append(row('LP13',unit,view,text,truth,method,member,member=member))
    validate_rows(rows);return rows


def twins(start=90000,n=64):
    groups=defaultdict(list)
    for i in range(start,start+20000):
        u=W.make_unit('dev',i)[0];key=tuple(e['action'] for e in u['history'][-4:])
        if len(groups[key])<2 and all(evidence(v['history'][-4:])!=evidence(u['history'][-4:]) for v in groups[key]):groups[key].append(u)
        ready=[v for k,v in sorted(groups.items()) if len(v)==2]
        if len(ready)>=n:return ready[:n]
    raise ValueError('insufficient unique observable artifact pairs')
