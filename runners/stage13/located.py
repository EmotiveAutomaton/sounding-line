"""Source-cross-fitted located contribution model and matched direct feature rival.

DESIGN CHECK: LESSONS 3-5. NULL: wrong locations and shuffled source labels fail
location controls; source siblings never cross folds. ALTERNATIVE: located-label
features improve independently calibrated detection over equally costly document
labels. Coarse character windows are explicit, not exact recovered edit histories.
"""
from collections import Counter
import math
import numpy as np
from .common import digest,freeze,SEED
from .scoring import span_scores,interval

NAMES=['located_mean','located_max','located_entropy','located_transitions','located_fraction','direct_mean','direct_max','direct_entropy','direct_transitions','direct_fraction']
DIM=16384


def windows(text):
    return [(i,min(i+160,len(text)),text[i:i+160]) for i in range(0,len(text),160)] or [(0,0,'')]


def vector(texts):
    from sklearn.feature_extraction.text import HashingVectorizer
    return HashingVectorizer(analyzer='char',ngram_range=(3,5),n_features=DIM,alternate_sign=False,norm='l2',dtype=np.float64).transform(texts)


def overlap(span,truth):
    a,b=span;return sum(max(0,min(b,d)-max(a,c)) for c,d in truth)/max(1,b-a)


def fit(rows,direct=False):
    from sklearn.linear_model import SGDClassifier
    texts=[];labels=[];weights=[];counts=Counter(r['unit'] for r in rows)
    for r in rows:
        if not direct and not r['location_truth_valid']:continue
        ws=windows(r['text'])
        for a,b,text in ws:
            texts.append(text);labels.append(r['label'] if direct else int(overlap((a,b),r['spans'])>=.5));weights.append(1/(counts[r['unit']]*len(ws)))
    if len(set(labels))!=2:raise ValueError('located training lacks both classes')
    weights=np.asarray(weights);weights*=len(weights)/weights.sum()
    clf=SGDClassifier(loss='log_loss',alpha=.0001,max_iter=30,tol=1e-4,random_state=SEED,shuffle=True).fit(vector(texts),labels,sample_weight=weights)
    return dict(coef=clf.coef_[0].tolist(),intercept=float(clf.intercept_[0]),method='char 3-5 hash features, 160-codepoint windows, SGD log loss',direct=direct)


def predict(model,text):
    ws=windows(text);z=vector([s for a,b,s in ws])@np.array(model['coef'])+model['intercept'];p=1/(1+np.exp(-np.clip(z,-60,60)))
    spans=[]
    for (a,b,_),v in zip(ws,p):
        if v>=.5 and b>a:
            if spans and spans[-1][1]==a:spans[-1][1]=b
            else:spans.append([a,b])
    entropy=-np.mean(p*np.log(np.maximum(p,1e-12))+(1-p)*np.log(np.maximum(1-p,1e-12)))
    features=[float(p.mean()),float(p.max()),float(entropy),float(np.mean(np.abs(np.diff(p)))) if len(p)>1 else 0.,sum(b-a for a,b in spans)/max(1,len(text))]
    return features,spans


def train_crossfit(rows,out,tick=None):
    folds={u:int(digest(['source-fold',u])[:8],16)%5 for u in sorted({r['unit'] for r in rows})};oof={}
    for fold in range(5):
        if tick:tick()
        train=[r for r in rows if folds[r['unit']]!=fold];test=[r for r in rows if folds[r['unit']]==fold]
        models=[fit(train,direct=x) for x in (False,True)]
        for r in test:oof[r['key']]=sum((predict(m,r['text'])[0] for m in models),[])
    result=dict(models=[fit(rows,direct=x) for x in (False,True)],oof=oof,folds=folds,feature_names=NAMES,
        fixed_span_threshold=.5,scope='AI involvement in source-annotated character windows; not sole authorship, mental goals or a complete process graph')
    freeze(out/'MODEL.json',result);return result


def features(rows,model,training=False):
    result=[]
    for r in rows:
        v=model['oof'][r['key']] if training else sum((predict(m,r['text'])[0] for m in model['models']),[])
        result.append(dict(r,**dict(zip(NAMES,v))))
    return result


def evaluate(rows,model):
    records=[]
    for r in rows:
        if not r['location_truth_valid']:continue
        _,spans=predict(model['models'][0],r['text'])
        score=span_scores(spans,r['spans'],len(r['text']));records.append(dict(key=r['key'],unit=r['unit'],score=score))
    return dict(strict=interval([r['score']['strict']['f1'] for r in records],[r['unit'] for r in records]),relaxed=interval([r['score']['relaxed']['f1'] for r in records],[r['unit'] for r in records]),
        invalid_annotation_exclusions=len(rows)-len(records),resolution='fixed 160 Unicode-codepoint windows; exact and relaxed matching remain separate',dependency_truth='unavailable in OpAI, human recorded-dependency fields scored in branch B')
