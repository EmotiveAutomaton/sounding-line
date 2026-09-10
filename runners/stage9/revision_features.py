"""Standard-library revision features and exported fitted distributions.

DESIGN CHECK: H01/H02/X02/X06; LESSONS 3--5, especially the explicit delta rival.
NULL: identical permitted text yields identical predictions despite private labels;
empty or unseen features cannot delete a class. ALTERNATIVE: trained lexical/delta
associations change a complete distribution. Unknown fields, malformed parameters
or nonfinite outputs refuse. These are label-agreement tools, not intent truth.
The nineteen delta features reproduce run_arg_replication.change_features exactly.
"""
from collections import Counter
from difflib import SequenceMatcher
import math,re


def change_features(old,new):
    ot,nt=old.split(),new.split();so,sn=set(ot),set(nt)
    union=len(so|sn) or 1;inter=len(so&sn)
    char_ratio=SequenceMatcher(None,old,new).ratio() if (old or new) else 1.
    sm=SequenceMatcher(None,ot,nt);tok_ratio=sm.ratio() if (ot or nt) else 1.
    ins=dele=rep=eq=0
    for tag,i1,i2,j1,j2 in sm.get_opcodes():
        if tag=='insert':ins+=j2-j1
        elif tag=='delete':dele+=i2-i1
        elif tag=='replace':rep+=max(i2-i1,j2-j1)
        else:eq+=i2-i1
    return [inter/union,char_ratio,tok_ratio,float(ins),float(dele),float(rep),float(eq),
        float(len(ot)),float(len(nt)),float(len(nt)-len(ot)),float(abs(len(nt)-len(ot))),
        float(len(new)-len(old)),float(abs(len(new)-len(old))),float(len(sn-so)),
        float(len(so-sn)),float(inter),float(not ot),float(not nt),len(nt)/len(ot) if ot else 0.]


def check_evidence(evidence,classes):
    if set(evidence) not in ({'text'},{'before','after'},{'before','after','earlier_labels'}):
        raise ValueError('unregistered revision evidence; private fields forbidden')
    if any(not isinstance(v,str) for k,v in evidence.items() if k!='earlier_labels'):
        raise ValueError('revision text must be strings')
    if 'earlier_labels' in evidence and (not isinstance(evidence['earlier_labels'],list) or
        any(k not in classes for k in evidence['earlier_labels'])):raise ValueError('unknown prior-cycle annotation')


def features(evidence,classes,kind='lexical_delta'):
    check_evidence(evidence,classes)
    if kind not in ('lexical_delta','surface_delta'):raise ValueError('undeclared revision feature family')
    result={}
    for side in ('text','before','after'):
        if side not in evidence:continue
        words=re.findall(r'\w+',evidence[side].casefold())
        result[side+':log_words']=math.log1p(len(words))
        if kind=='lexical_delta':
            counts=Counter(words[:1024]);total=max(1,sum(counts.values()))
            result.update({side+':word:'+w:n/total for w,n in counts.items()})
    if 'before' in evidence:
        result.update({'change:'+str(i):math.copysign(math.log1p(abs(v)),v)
            for i,v in enumerate(change_features(evidence['before'],evidence['after']))})
    if 'earlier_labels' in evidence:
        counts=Counter(evidence['earlier_labels']);total=len(evidence['earlier_labels'])+len(classes)
        result.update({'earlier:'+k:(counts[k]+1)/total for k in classes})
    return result


def probabilities(values,classes):
    if set(values)!=set(classes) or any(type(v) not in (int,float) or not math.isfinite(v) or v<0 for v in values.values()):
        raise ValueError('invalid complete revision forecast')
    if abs(math.fsum(values.values())-1)>1e-10:raise ValueError('revision forecast not normalized')
    return values


def predict(evidence,model):
    classes=model['classes'];check_evidence(evidence,classes)
    if not classes or len(set(classes))!=len(classes):raise ValueError('full fixed unique class support required')
    prior=probabilities(model['prior'],classes);method=model['method']
    if method=='prior':return prior
    if method=='majority':
        selected=min(classes,key=lambda k:(-prior[k],k))
        return {k:.99*(k==selected)+.01/len(classes) for k in classes}
    if method=='previous_cycle':
        if 'earlier_labels' not in evidence:raise ValueError('prior-cycle rival needs explicit earlier annotations')
        labels=evidence['earlier_labels'];counts=Counter(labels)
        return {k:(counts[k]+1)/(len(labels)+len(classes)) for k in classes} if labels else prior
    if method!='logistic':raise ValueError('unknown revision model')
    x=features(evidence,classes,model['features']);fitted=model['fitted_classes']
    if not fitted or not set(fitted)<=set(classes) or len(set(fitted))!=len(fitted):raise ValueError('invalid fitted class subset')
    coefficients=model['coefficients'];intercept=model['intercept']
    if set(coefficients)!=set(fitted) or set(intercept)!=set(fitted):raise ValueError('missing class coefficients')
    logits={}
    for k in fitted:
        weights=coefficients[k]
        if type(intercept[k]) not in (int,float) or not math.isfinite(intercept[k]) or any(type(v) not in (int,float) or not math.isfinite(v) for v in weights.values()):
            raise ValueError('nonfinite revision coefficients')
        logits[k]=intercept[k]+math.fsum(v*x.get(w,0.) for w,v in weights.items())
    if any(not math.isfinite(v) for v in logits.values()):raise ValueError('nonfinite revision logit')
    maximum=max(logits.values());weights={k:math.exp(v-maximum) for k,v in logits.items()};total=math.fsum(weights.values())
    return probabilities({k:.99*weights.get(k,0.)/total+.01/len(classes) for k in classes},classes)
