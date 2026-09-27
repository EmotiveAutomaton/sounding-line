"""Retrospective annotated revision purpose and observed operation coupling.

DESIGN CHECK: LESSONS 3-5. NULL: independent marginals and shuffled training
associations must remain real rivals; project copies cannot cross partitions.
ALTERNATIVE: goal/process coupling improves both targets with fixed support.
ScholaWrite purpose is annotator-supplied, never maker-stated mental truth.
"""
from difflib import SequenceMatcher
from collections import Counter
import numpy as np
from .common import RAW,REPO,read,freeze,filehash,digest,SEED
from .scoring import proper_loss,interval
OPS=['unchanged','insert','delete','replace','mixed']


def operation(before,after):
    changes={t for t,*_ in SequenceMatcher(None,before,after,autojunk=False).get_opcodes() if t!='equal'}
    return 'unchanged' if not changes else next(iter(changes)) if len(changes)==1 else 'mixed'


def prepare(raw=RAW):
    from runners.stage9.common import ROOT,digest as old_digest
    from runners.stage9.scholawrite import LABEL_MAP
    from .splits import normalized
    base=ROOT/'private/prepared/scholawrite-v2';ledger=read(base/'LEDGER.json');projects=sorted(ledger,key=lambda x:digest(['stage13-schola',x['unit']]))
    rows=[];pins={};exclusions=[];order=['train','train','development','calibration','reserve']
    for item,part in zip(projects,order):
        p=base/item['path']
        if filehash(p)!=item['sha256']:raise ValueError('ScholaWrite prepared source changed')
        pins[str(p.relative_to(REPO))]=filehash(p);data=read(p)
        selected=sorted(data['records'],key=lambda r:digest(['retrospective-purpose',r['key']]))[:100]
        for r in selected:
            before=data['texts'][r['before']];after=data['texts'][r['after']]
            if old_digest(before)!=r['before'] or old_digest(after)!=r['after']:raise ValueError('source text digest differs')
            if r['fine_label'] not in LABEL_MAP or LABEL_MAP[r['fine_label']]!=r['category']:raise ValueError('annotated purpose labels disagree')
            rows.append(dict(key=r['key'],unit=r['unit'],partition=part,before=before,after=after,goal=r['fine_label'],goal_type='annotator revision purpose',operation=operation(before,after),endpoint_sha=digest(normalized(after))))
    # Remove exact normalized endpoint copies across projects; near copies remain a stated limitation.
    seen={}
    for r in rows:seen.setdefault(r['endpoint_sha'],set()).add(r['unit'])
    kept=[r for r in rows if len(seen[r['endpoint_sha']])==1]
    freeze(raw/'sources/schola-retrospective.json',kept)
    result=dict(status='complete',source_pins=pins,outputs={'sources/schola-retrospective.json':filehash(raw/'sources/schola-retrospective.json')},goals=sorted(LABEL_MAP),operations=OPS,
        counts={p:dict(rows=sum(r['partition']==p for r in kept),projects=len({r['unit'] for r in kept if r['partition']==p})) for p in sorted(set(order))},exact_copy_exclusions=len(rows)-len(kept),
        scope='five historically exposed projects; retrospective current edit, not previous next-edit task; annotator purpose; project-scoped author IDs, near-duplicate and cross-project author identity unresolved')
    freeze(raw/'sources/SCHOLA_COMPLETE.json',result);return result


def text(row,view):
    # Same fixed view-specific evidence for all learned rivals.
    after=row['after'];bound=after[:2000]+'\n'+after[-2000:]
    return bound if view=='A' else row['before'][:2000]+'\n'+row['before'][-2000:]+'\nAFTER\n'+bound


def classifier(training,testing,view,field,labels):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    vector=TfidfVectorizer(ngram_range=(1,2),max_features=6000,sublinear_tf=True)
    x=vector.fit_transform([text(r,view) for r in training]);target=[labels.index(r[field]) for r in training]
    counts=Counter(r['unit'] for r in training);weights=[len(training)/(len(counts)*counts[r['unit']]) for r in training]
    if len(set(target))<2:
        p=np.ones(len(labels))
        for y in target:p[y]+=1
        return np.tile(p/p.sum(),(len(testing),1))
    model=LogisticRegression(C=1,max_iter=1000,random_state=SEED).fit(x,target,sample_weight=weights)
    pred=model.predict_proba(vector.transform([text(r,view) for r in testing]));result=np.full((len(testing),len(labels)),.01/len(labels))
    for j,label in enumerate(model.classes_):result[:,label]+=.99*pred[:,j]
    return result


def coupling(training,goals,shuffle=False):
    table=np.ones((len(goals),len(OPS)))
    order=sorted(training,key=lambda r:r['key']);g=[r['goal'] for r in order]
    if shuffle:g=g[1:]+g[:1]
    counts=Counter(r['unit'] for r in training)
    for r,goal in zip(order,g):table[goals.index(goal),OPS.index(r['operation'])]+=len(training)/(len(counts)*counts[r['unit']])
    table/=table.sum();return table/(table.sum(1)[:,None]*table.sum(0)[None,:])


def joint(pg,pp,link):
    table=np.asarray(pg)[:,None]*np.asarray(pp)[None,:]*link;table/=table.sum();return table.sum(1).tolist(),table.sum(0).tolist()


def run(rows,out,tick):
    from runners.stage9.scholawrite import LABEL_MAP
    from .calibration import fit,evaluate
    goals=sorted(LABEL_MAP);train=[r for r in rows if r['partition']=='train'];test=[r for r in rows if r['partition']!='train'];records=[]
    assert not {r['unit'] for r in train}&{r['unit'] for r in test}
    links={'joint':coupling(train,goals),'severed':np.ones((len(goals),len(OPS))),'shuffled':coupling(train,goals,True)}
    for view in ('A','C'):
        tick();pg=classifier(train,test,view,'goal',goals);pp=classifier(train,test,view,'operation',OPS)
        for r,g,p in zip(test,pg,pp):
            exact=np.array([.01/len(OPS)+.99*(o==r['operation']) for o in OPS]) if view=='C' else p
            predictions={'direct':(g.tolist(),p.tolist()),'without-execution':joint(g,p,links['joint'])}
            for method,link in links.items():predictions[method]=joint(g,exact,link)
            predictions['without-goal-coupling']=joint(np.ones(len(goals))/len(goals),exact,links['joint'])
            for method,(gp,op) in predictions.items():
                for field,v,labels in [('goal',gp,goals),('operation',op,OPS)]:
                    records.append(dict(key=r['key'],unit=r['unit'],partition=r['partition'],view=view,method=method,target=field,truth=labels.index(r[field]),n=len(labels),probabilities=v,scores=proper_loss(v,labels.index(r[field]),len(labels))))
    freeze(out/'PREDICTIONS.json',dict(rows=records,scope='annotator-purpose and observed edit-operation coupling; joint compatibility learned on training projects only'))
    result={}
    for view,method,field in sorted({(r['view'],r['method'],r['target']) for r in records}):
        cal=[r for r in records if r['view']==view and r['method']==method and r['target']==field and r['partition']=='calibration'];held=[r for r in records if r['view']==view and r['method']==method and r['target']==field and r['partition']=='reserve'];model=fit(cal)
        result[view+'/'+method+'/'+field]=dict(calibration=model,evaluation=evaluate(held,model))
    analysis=dict(status='complete',comparisons=result,scope='descriptive previously exposed human projects; single reserve project; annotation is not mental-goal truth; process is exact text-edit class, not complete decision history',unknowns=['cross-project author and near-copy independence','temporal dependency truth','strong Qwen counterpart remains held'])
    freeze(out/'ANALYSIS.json',analysis);return analysis
