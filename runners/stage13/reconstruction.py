"""Retrospective process candidates, cheap rivals and shared contribution consumer.

DESIGN CHECK: LESSONS 2-5. NULL: identical endpoints cannot distinguish hidden
histories; candidate omission lowers coverage, not silently renormalized truth.
ALTERNATIVE: declared transforms reconstruct known endpoints and exact locations.
Human edits outside the transform family remain missing support. Goal hypotheses
are unscored without independent goal truth; process success is not goal recovery.
"""
from __future__ import annotations
from copy import deepcopy
from collections import defaultdict
from difflib import SequenceMatcher
import math
import numpy as np
from .common import digest,freeze
from .scoring import probabilities,proper_loss,span_scores,interval
from runners.stage11_1 import cheap
from runners.stage11_1.targets import ACTORS,OPERATIONS,RELATIONS,SLOTS
from runners.stage11_1.models import ACTIONS

FIELDS={'actor':ACTORS,'operation':OPERATIONS,'relation':RELATIONS}
_RETRIEVAL={}


def candidates(e):
    if 'before' not in e:return []
    before=e['before'];prefix=before[:-1] if before.endswith('\n') else before
    end='\n' if before.endswith('\n') else ''
    result=[]
    for i,offer in enumerate(e['alternatives']):
        offer=offer.replace('\r\n','\n').replace('\r','\n')
        result.append(dict(id='accept-'+str(i),handling='accept',offer=offer,executed=prefix+offer+end,operation='insert',goal_hypothesis='incorporate offered material'))
        # All transformations are declared data, never executable generated code.
        for tag,replacement in [('trim',offer.strip()),('delete',''),('first-sentence',offer.split('.')[0]+'.')]:
            result.append(dict(id='edit-'+str(i)+'-'+tag,handling='edit',offer=offer,executed=prefix+replacement+end,operation='content_edit',goal_hypothesis='modify offered material'))
    for action in ('dismiss','ignore'):
        result.append(dict(id=action,handling=action,offer='',executed=before,operation='absent',goal_hypothesis='continue without using offered material'))
    return result


def exact_locations(e,handling):
    if 'before' not in e:return {s:[] for s in SLOTS}
    before=e['before'];after=e['endpoint'];out={s:[] for s in SLOTS}
    retained=[]
    for offer in e['alternatives']:
        offer=offer.replace('\r\n','\n').replace('\r','\n')
        if not offer:continue
        start=after.find(offer,max(0,len(before)-2))
        if start>=0:retained.append([start,start+len(offer)])
    if retained and handling in ('accept','edit'):
        span=max(retained,key=lambda s:s[1]-s[0]);out['selection']=[span];out['entry']=[span]
        tail=span[1]
        if tail<len(after.rstrip('\n')):out['continuation']=[[tail,len(after.rstrip('\n'))]]
    changes=[[k,l] for tag,i,j,k,l in SequenceMatcher(None,before,after,autojunk=False).get_opcodes() if tag!='equal' and l>k]
    if handling=='edit':out['change']=changes
    if not retained:out['surrounding']=changes
    return out


def model_fit(rows):
    from sklearn.feature_extraction.text import TfidfVectorizer
    model=cheap.fit(rows)
    # Store source IDs and declarative training targets; fit vectorizer in-memory on
    # each complete block, never persist an untrusted pickle.
    return dict(prior=model,training=[dict(key=r['key'],unit=r['unit'],text=r['views']['A']['endpoint'],target=r['target']) for r in rows])


def retrieval(e,model):
    from sklearn.feature_extraction.text import TfidfVectorizer
    train=model['training'];cache_key=digest([r['key'] for r in train])
    if cache_key not in _RETRIEVAL:
        vector=TfidfVectorizer(analyzer='char',ngram_range=(3,5),max_features=12000,min_df=1)
        matrix=vector.fit_transform([r['text'] for r in train]);_RETRIEVAL[cache_key]=(vector,matrix)
    vector,matrix=_RETRIEVAL[cache_key];query=vector.transform([e['endpoint']]);similarity=(matrix@query.T).toarray().ravel()
    order=sorted(range(len(train)),key=lambda i:(-float(similarity[i]),train[i]['key']))
    selected=[];units=set()
    for i in order:
        if train[i]['unit'] in units:continue
        selected.append(train[i]);units.add(train[i]['unit'])
        if len(selected)==3:break
    records=[dict(writer=r['unit'],target=r['target']) for r in selected]
    prediction,_=cheap.predict(e,cheap.fit(records),False)
    return prediction,[r['key'] for r in selected]


def predict(e,model,arm,goal_support=None):
    if arm=='prior':pred,_=cheap.predict(e,model['prior'],False);meta={}
    elif arm=='retrieval':pred,neighbors=retrieval(e,model);meta={'neighbors':neighbors}
    elif arm=='alignment':pred,meta=cheap.predict(e,model['prior'],True)
    elif arm in ('joint-execution','without-execution','without-goal-coupling','shuffled-goal-coupling'):
        pred,_=cheap.predict(e,model['prior'],False);cs=candidates(e);prior=model['prior']['handling'];weights=[]
        support=goal_support or [1.]*4
        if arm=='shuffled-goal-coupling':support=support[1:]+support[:1]
        if arm=='without-goal-coupling':support=[1.]*4
        for c in cs:
            i=ACTIONS.index(c['handling']);similarity=SequenceMatcher(None,c['executed'],e['endpoint'],autojunk=False).ratio()
            execution=1. if arm=='without-execution' else math.exp(8*(similarity-1))
            weights.append(prior[i]*execution*max(.01,support[i]))
        masses=[.05*p for p in prior]  # unidentified histories remain supported.
        for c,w in zip(cs,weights):masses[ACTIONS.index(c['handling'])]+=w/max(1,sum(x['handling']==c['handling'] for x in cs))
        pred['handling']=[x/sum(masses) for x in masses]
        best=cs[int(np.argmax(weights))] if cs else None
        if best:
            facts=cheap.prototype(e,best['handling'],best['offer'])
            for f in pred['facts']:
                for k,labels in FIELDS.items():f[k]=[.2*p+.8*int(facts[f['slot']][k]==lab) for p,lab in zip(f[k],labels)]
        meta=dict(candidate_count=len(cs),executions=[dict(id=c['id'],handling=c['handling'],endpoint_matches=c['executed']==e['endpoint']) for c in cs],
            scoring='fixed similarity likelihood, source prior and optional reader goal compatibility; heuristic until independent calibration',
            unknown_history_floor=.05,goal_support_available=goal_support is not None)
    elif arm=='observed-extraction':
        if 'observed_operations' not in e:raise ValueError('record upper bound requires explicit process view')
        pred=dict(handling=[float(a==e.get('observed_handling')) for a in ACTIONS] if e.get('observed_handling') in ACTIONS else None,facts=[],attributes=dict(reviewed='unknown',endorsed='unknown',understood='unknown'))
        for f in e['observed_operations']:
            pred['facts'].append(dict(slot=f['slot'],**{k:[float(f[k]==lab) for lab in labels] for k,labels in FIELDS.items()},exact_spans=f['exact_spans']))
        return pred,dict(scope='process-record extraction upper bound; not inference')
    else:raise ValueError('unknown reconstruction arm')
    action=ACTIONS[int(np.argmax(pred['handling']))]
    locations=exact_locations(e,action)
    for f in pred['facts']:f['exact_spans']=locations[f['slot']] if arm not in ('prior','retrieval') else []
    return pred,meta


def score_prediction(row,pred,meta):
    truth=row['target'];out={};facts={f['slot']:f for f in pred.get('facts',[])}
    if set(facts)!=set(SLOTS):raise ValueError('missing or repeated fact slot')
    out['handling']=proper_loss(pred.get('handling'),ACTIONS.index(truth['handling']),len(ACTIONS))
    for k,labels in FIELDS.items():
        losses=[proper_loss(facts[t['slot']].get(k),labels.index(t[k]),len(labels)) for t in truth['facts']]
        out[k]=dict(brier=sum(x['brier'] for x in losses)/len(losses),correct=sum(x['correct'] for x in losses)/len(losses),valid=all(x['valid'] for x in losses))
    location=[]
    for t in truth['facts']:
        try:location.append(span_scores(facts[t['slot']].get('exact_spans',[]),t['exact_spans'],len(row['views']['A']['endpoint'])))
        except ValueError:location.append({k:dict(f1=0,precision=0,recall=0) for k in ('strict','relaxed')})
    out['location']={k:(0. if pred.get('invalid') else sum(x[k]['f1'] for x in location)/len(location)) for k in ('strict','relaxed')}
    out['unsupported_mental_assertions']=sum(v!='unknown' for v in pred.get('attributes',{}).values())
    ex=meta.get('executions')
    out['candidate_coverage']=any(c['handling']==truth['handling'] and c['endpoint_matches'] for c in ex) if ex is not None else None
    out['goal_recovery']=None
    return out


def run_batch(rows,model,out,arms=('prior','alignment','retrieval','joint-execution','without-execution','without-goal-coupling','shuffled-goal-coupling'),views=('A','B','C','D'),tick=None):
    records=[]
    for row in rows:
        for view in views:
            e=row['views'][view]
            for arm in arms+(('observed-extraction',) if view=='D' else ()):
                if tick:tick()
                pred,meta=predict(e,model,arm)
                record=dict(key=row['key'],unit=row['unit'],partition=row.get('partition','fixture'),view=view,arm=arm,prediction=pred,metadata=meta,scores=score_prediction(row,pred,meta))
                # JSON round-trip and pure re-scoring, before completion.
                import json
                replay=json.loads(json.dumps(record))
                if score_prediction(row,replay['prediction'],replay['metadata'])!=record['scores']:raise ValueError('consumer semantic replay differs')
                records.append(record)
    result=dict(rows=records,goal_truth='unavailable in CoAuthor; goal coupling arms require independent reader output',
        warning='without available goal support, joint and severed goal arms intentionally coincide; do not claim a coupling comparison')
    freeze(out/'PREDICTIONS.json',result);return result


def summarize(records):
    grouped=defaultdict(list)
    for r in records:grouped[(r.get('partition','unknown'),r['view'],r['arm'])].append(r)
    result={}
    for (partition,view,arm),rs in sorted(grouped.items()):
        units=[r['unit'] for r in rs];entry={}
        for field in ('handling','actor','operation','relation'):
            entry[field]={metric:interval([r['scores'][field][metric] for r in rs],units) for metric in ('brier','correct')}
        entry['locations']={k:interval([r['scores']['location'][k] for r in rs],units) for k in ('strict','relaxed')}
        coverage=[r for r in rs if r['scores']['candidate_coverage'] is not None]
        entry['candidate_coverage']=interval([float(r['scores']['candidate_coverage']) for r in coverage],[r['unit'] for r in coverage]) if coverage else None
        result[partition+'/'+view+'/'+arm]=entry
    return dict(status='complete',comparisons=result,scope='retrospective recorded handling and located contributions; historically exposed human corpus; no goal or value truth',
        missing=['matched primary Qwen direct and joint inference until GPU admission','human local-goal accuracy unavailable without independent goal labels'])


def admission_fixture():
    facts=[]
    for slot in SLOTS:
        f=dict(slot=slot,actor='unknown',operation='absent',relation='none',exact_spans=[])
        if slot=='entry':f.update(actor='model',operation='insert',relation='selected_by',exact_spans=[[4,8]])
        if slot=='selection':f.update(actor='human_writer',operation='select',relation='selects',exact_spans=[[4,8]])
        facts.append(f)
    e=dict(endpoint='Old new.\n',before='Old \n',alternatives=['new.'],anchors=[dict(id='a000',start=0,end=9)])
    return dict(key='s13-known-adoption-fixture',unit='known-fixture',partition='admission-fixture',control='observed-adoption',target=dict(handling='accept',facts=facts),views={'D':dict(e,observed_operations=facts,observed_handling='accept')})
