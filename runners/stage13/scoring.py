"""Consumers defined before inference; no combined reading score.

DESIGN CHECK: LESSONS 3-5. NULL: random ranking, wrong locations and missing
attempts cannot earn oracle performance. ALTERNATIVE: known labels and exact
locations score perfectly. Invalid probability vectors count at worst loss;
human calibration fixes thresholds before reserve and ties cannot inflate TPR.
"""
from __future__ import annotations
import json
import math
import numpy as np
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import roc_auc_score,average_precision_score,roc_curve
from .common import SEED


def probabilities(value, count):
    if isinstance(value, str):
        try: value = json.loads(value)
        except (ValueError, TypeError): return None
    if not isinstance(value, list) or len(value) != count: return None
    if any(type(x) not in (int, float) or not math.isfinite(x) or x < 0 or x > 1 for x in value): return None
    # Literal schema probabilities only. Do not repair or normalize a model reply.
    if abs(sum(value)-1) > 1e-6: return None
    return value


def proper_loss(value, truth, count):
    p = probabilities(value, count)
    if not 0 <= truth < count: raise ValueError('truth outside candidate set')
    if p is None: return dict(valid=False, correct=0, brier=2., log_loss=-math.log(1e-12), confidence=None)
    return dict(valid=True, correct=int(np.argmax(p)==truth),
                brier=sum((x-int(i==truth))**2 for i,x in enumerate(p)),
                log_loss=-math.log(max(p[truth],1e-12)), confidence=max(p))


def validate_spans(spans, text_length):
    if not isinstance(spans,list): raise ValueError('spans must be a list')
    previous = 0
    for s in spans:
        if not isinstance(s,(list,tuple)) or len(s)!=2 or any(type(x)!=int for x in s): raise ValueError('bad span')
        a,b=s
        if not 0<=a<b<=text_length or a<previous: raise ValueError('overlapping or out-of-bounds span')
        previous=b
    return [list(s) for s in spans]


def span_scores(predicted, truth, text_length):
    predicted=validate_spans(predicted,text_length);truth=validate_spans(truth,text_length)
    def iou(a,b):
        overlap=max(0,min(a[1],b[1])-max(a[0],b[0]))
        return overlap/(a[1]-a[0]+b[1]-b[0]-overlap)
    out={}
    for name,threshold in [('strict',1),('relaxed',.5)]:
        matches=0
        if predicted and truth:
            matrix=np.array([[iou(a,b)>=threshold for b in truth] for a in predicted],dtype=int)
            rr,cc=linear_sum_assignment(-matrix);matches=int(matrix[rr,cc].sum())
        precision=matches/len(predicted) if predicted else float(not truth)
        recall=matches/len(truth) if truth else float(not predicted)
        out[name]=dict(precision=precision,recall=recall,f1=2*precision*recall/(precision+recall) if precision+recall else 0.)
    return out


def group_mean(values,units):
    if len(values)!=len(units) or not values: raise ValueError('empty or unmatched units')
    groups={k:[] for k in sorted(set(units))}
    for v,u in zip(values,units):
        if not math.isfinite(v): raise ValueError('nonfinite value')
        groups[u].append(v)
    return np.array([np.mean(groups[k]) for k in sorted(groups)],dtype=float)


def interval(values,units,draws=1000):
    v=group_mean(values,units)
    if len(v)<2:return dict(mean=float(v.mean()),low=None,high=None,units=len(v),method='insufficient independent components for an interval')
    rng=np.random.default_rng(SEED)
    boot=np.mean(v[rng.integers(0,len(v),(draws,len(v)))],axis=1)
    return dict(mean=float(v.mean()),low=float(np.quantile(boot,.025)),high=float(np.quantile(boot,.975)),units=len(v),method='ordered source-cluster bootstrap; equal cluster weight')


def threshold(human_scores,rate):
    if not human_scores or not 0<rate<1: raise ValueError('invalid calibration')
    s=sorted(float(v) for v in human_scores)
    if not all(math.isfinite(v) for v in s): raise ValueError('invalid score')
    allowed=math.floor(rate*len(s))
    # Flag score > threshold; all tied scores receive the same decision.
    return s[max(0,len(s)-allowed-1)]


def confusion(labels,scores,cut):
    if len(labels)!=len(scores) or not labels: raise ValueError('empty/mismatched detection rows')
    if not all(y in (0,1) for y in labels) or not all(math.isfinite(x) for x in scores): raise ValueError('invalid detection rows')
    tp=sum(y==1 and s>cut for y,s in zip(labels,scores));fp=sum(y==0 and s>cut for y,s in zip(labels,scores))
    pos=sum(labels);neg=len(labels)-pos
    tpr=tp/pos if pos else None;fpr=fp/neg if neg else None
    return dict(tp=tp,fp=fp,positive=pos,negative=neg,tpr=tpr,fpr=fpr,
        precision=tp/(tp+fp) if tp+fp else None,recall=tpr,f1=2*tp/(2*tp+fp+pos-tp) if 2*tp+fp+pos-tp else None,
        zero_fp_95_upper=1-.05**(1/neg) if neg and fp==0 else None,
        precision_at_hypothetical_prevalence={str(p):p*tpr/(p*tpr+(1-p)*fpr) if tpr is not None and fpr is not None and p*tpr+(1-p)*fpr else None for p in (.01,.1,.5)})


def detection_report(rows,score_name,cuts):
    labels=[r['label'] for r in rows];scores=[r[score_name] for r in rows]
    report=dict(rows=len(rows),independent_sources=len({r['unit'] for r in rows}),
                auc=float(roc_auc_score(labels,scores)) if len(set(labels))==2 else None,thresholds={})
    report['precision_recall_area']=float(average_precision_score(labels,scores)) if len(set(labels))==2 else None
    if len(set(labels))==2:
        fpr,tpr,_=roc_curve(labels,scores);report['test_roc_tpr_at_fpr']={str(q):float(max(tpr[fpr<=q])) for q in (.01,.05)}
    losses=[proper_loss([1-s,s],y,2) for s,y in zip(scores,labels)]
    report['probability_loss']={k:interval([v[k] for v in losses],[r['unit'] for r in rows]) for k in ('brier','log_loss')}
    report['selective_risk']={}
    for confidence in (.5,.7,.9):
        selected=[(r,v) for r,v in zip(rows,losses) if v['confidence'] is not None and v['confidence']>=confidence]
        report['selective_risk'][str(confidence)]=dict(coverage=len(selected)/len(rows),risk=interval([1-v['correct'] for r,v in selected],[r['unit'] for r,v in selected]) if selected else None)
    for name,cut in cuts.items():
        c=confusion(labels,scores,cut)
        for label,key in ((0,'fpr_interval'),(1,'tpr_interval')):
            selected=[r for r in rows if r['label']==label]
            c[key]=interval([float(r[score_name]>cut) for r in selected],[r['unit'] for r in selected]) if selected else None
        report['thresholds'][name]=dict(cut=cut,**c)
    return report
