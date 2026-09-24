"""Sequential questions and utility-bounded stopping over the existing maker law.

DESIGN CHECK: LESSONS 3-5. NULL: duplicate questions have zero new information;
random or always-buy policies can fail. ALTERNATIVE: distinct observations
improve support and appropriate purchases depend on public cost. Choices never
receive unrevealed outcomes. Invalid choices leave dependent slots incomplete.
"""
from copy import deepcopy
import itertools
import json
import math
import random
from .common import digest
from .program_world import W, row, target, evidence, question, validate_rows


def entropy(p):
    return -sum(v*math.log2(v) for v in p if v)


def options(unit):
    # Existing observations, with one source event behind each persistent ID.
    return [deepcopy(q['observation']) for q in unit['queries']]


def loss(p, purpose='forecast'):
    return (1-sum(v*v for v in p))/2 if purpose=='forecast' else 1-max(p)


def values(unit, history, seen=(), purpose='forecast'):
    obs=unit['queries'][1]['observation']
    old=W.enumerate_predict(history,obs)
    current=loss(old['probabilities'],purpose); result=[]
    for index,o in enumerate(options(unit)):
        if index in seen:
            result.append(dict(gain=0.,information=0.));continue
        probabilities=W.enumerate_predict(history,o)['probabilities']
        after=0.; info=0.
        for action,probability in enumerate(probabilities):
            h=history+[dict(sequence=100+index,observation=o,action=action)]
            update=W.enumerate_predict(h,obs)
            after+=probability*loss(update['probabilities'],purpose)
            info+=probability*entropy(update['weights'])
        result.append(dict(gain=current-after,information=entropy(old['weights'])-info))
    return result


def reveal(unit,index):
    o=options(unit)[index];pref,skill=W.POLICIES[int(unit['unit'].split('-')[-1])%4]
    goal,belief=W.decode(o)
    p=W.reference(pref,skill,goal,belief,o['world_family'],o['tools'])
    rng=random.Random(int(digest(['LP07-observation',unit['unit'],index])[:16],16))
    action=rng.choices(range(4),weights=p)[0]
    return dict(sequence=100+index,observation=o,action=action)


def slots(family,units):
    rows=[]
    for u in units:
        for policy in ('neutral','counterexample','random','exact'):
            base=dict(dynamic='query',source=u,policy=policy)
            rows.append(row(family,u,policy+'-forecast-0','',[.25]*4,role='forecast',step=0,**base))
            for step in range(1,4):
                if policy in ('neutral','counterexample'):
                    rows.append(row(family,u,policy+'-choose-'+str(step),'',[.25]*4,role='selection',step=step,**base))
                rows.append(row(family,u,policy+'-forecast-'+str(step),'',[.25]*4,role='forecast',step=step,**base))
    validate_rows(rows);return rows


def materialize(slot,finished):
    """Rebuild the realized branch exclusively from retained earlier selections."""
    s=deepcopy(slot);u=s['source'];history=deepcopy(u['history'][:1]);seen=[];chosen=[]
    policy=s['policy'];step=s['step']
    relevant=[r for r in finished if r['unit']==s['unit'] and r.get('policy')==policy]
    for k in range(1,step+1):
        if s['role']=='selection' and k==step:break
        v=values(u,history,seen)
        if policy=='random':index=random.Random(int(digest([u['unit'],k,'random'])[:16],16)).randrange(4)
        elif policy=='exact':index=max(range(4),key=lambda i:(v[i]['information'],-i))
        else:
            prev=next((r for r in relevant if r['role']=='selection' and r['step']==k),None)
            if prev is None or prev['probabilities'] is None:
                raise ValueError('unavailable earlier question selection; no hidden fallback')
            index=max(range(4),key=prev['probabilities'].__getitem__)
        chosen.append(dict(index=index,**v[index],repeated=index in seen))
        if index not in seen:history.append(reveal(u,index));seen.append(index)
    s['realized_selections']=chosen;s['history_sha256']=digest(history)
    if s['role']=='selection':
        order=list(range(4));random.Random(int(digest([u['unit'],step,'option-order'])[:16],16)).shuffle(order)
        v=values(u,history,seen);best=max(x['information'] for x in v)
        winners=[i for i,x in enumerate(v) if abs(x['information']-best)<1e-12]
        s['target']=[float(i in winners)/len(winners) for i in range(4)];s['reference']=s['target'];s['label_order']=order
        instruction=('Choose a question whose possible answer could distinguish the remaining maker hypotheses.' if policy=='neutral' else
            'Seek a counterexample to the leading explanation: choose a question whose possible answer could most strongly challenge it. Do not merely negate it.')
        s['text']=question(u)+'\nObserved history:\n'+evidence(history)+'\n'+instruction+' Choose a persistent question ID; repeated IDs return the same event and add no evidence. Previously revealed IDs: '+str(seen)+'.\nOptions in response order: '+json.dumps([dict(id=i,observation=options(u)[i]) for i in order])
        s['information_values']=v
    else:
        s['target']=target(u,history);s['reference']=s['target']
        s['text']=question(u)+'\nObserved history, counting each event once:\n'+evidence(history)
    return s


def stopping(units):
    rows=[];decisions=set()
    for u,purpose,cost,reverse in itertools.product(units,('forecast','classification'),(.0,.2,.5),(False,True)):
        h=u['history'][:1];truth=target(u,h);v=values(u,h,purpose=purpose)
        offer=max(range(4),key=lambda i:(v[i]['gain'],-i));gain=v[offer]['gain'];buy=gain>cost+1e-12;decisions.add(buy)
        labels=[(d,a) for d in (('buy','stop') if reverse else ('stop','buy')) for a in W.LETTERS]
        # A joint distribution gives two coherent marginals in one model call.
        q=[truth[W.LETTERS.index(a)]*float((d=='buy')==buy) for d,a in labels]
        utility='expected half-Brier error (one half of squared probability error)' if purpose=='forecast' else 'probability of an incorrect highest-probability action'
        text=question(u)+'\nHistory:\n'+evidence(h)+'\nReader purpose: minimize '+utility+'. Stop now or purchase one new event, then make the same forecast. Purchase cost in those loss units: '+str(cost)+'. Offered observation: '+json.dumps(options(u)[offer])+'. Give a JOINT probability over decision and CURRENT action, not an unobserved future answer. Its decision marginal selects stop/buy; action marginal is your current forecast. Label order: '+json.dumps(labels)
        rows.append(row('LP08',u,f'{purpose}-{cost}-{reverse}',text,q,purpose=purpose,cost=cost,offer=offer,offer_gain=gain,decision_labels=[d for d,a in labels],forecast_target=truth,optimal_buy=buy))
    if decisions!={False,True}:raise ValueError('stopping has no buy/stop dynamic range')
    validate_rows(rows);return rows
