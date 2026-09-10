"""Pure prospective writing features with present draft and prior record separate.

DESIGN CHECK: H07/H08/X02/X03/X06; LESSONS 2--5. NULL: future handling or
next-edit annotations cannot enter permitted features; constant history returns
the fitted base-rate rival. ALTERNATIVE: present visible text or an actually prior
record changes a complete forecast. Source-native class support remains explicit.
Private fields, missing support and nonfinite fitted parameters refuse.
"""
from collections import Counter
import math,re
DECISIONS=('accept','edit','dismiss','ignore')
CATEGORIES=('PLANNING','IMPLEMENTATION','REVISION')
LOCATIONS=('first_quarter','second_quarter','third_quarter','last_quarter','no_change')
SUPPORT={'coauthor':DECISIONS,'schola_category':CATEGORIES,'schola_location':LOCATIONS}


def coauthor_features(evidence):
    if set(evidence) not in ({'document','suggestions'}, {'document','suggestions','earlier_handling'}):
        raise ValueError('unregistered prospective handling evidence')
    document = evidence['document']
    tokens = re.findall(r'\w+',document.casefold())
    candidates = [re.findall(r'\w+',s.casefold()) for s in evidence['suggestions']]
    known = set(tokens)
    out = {'log_document_words': math.log1p(len(tokens)),
           'log_suggestion_count': math.log1p(len(candidates)),
           'mean_log_suggestion_words': sum(math.log1p(len(s)) for s in candidates)/len(candidates),
           'mean_context_overlap': sum(sum(w in known for w in s)/max(1,len(s)) for s in candidates)/len(candidates),
           'suggestion_length_spread': math.log1p(max(map(len,candidates))-min(map(len,candidates)))}
    # Declared lexical suffix budget; complete documents remain in private source.
    word_counts = Counter(tokens[-512:]); total = max(1,sum(word_counts.values()))
    out.update({'word:'+w:n/total for w,n in word_counts.items()})
    if 'earlier_handling' in evidence:
        history = evidence['earlier_handling']
        if any(k not in DECISIONS for k in history):
            raise ValueError('unknown earlier handling')
        out['log_previous_opportunities'] = math.log1p(len(history))
        for k in DECISIONS:
            out['previous_rate:'+k] = (history.count(k)+1)/(len(history)+4)
        out['previous_label:'+(history[-1] if history else 'none')] = 1.
    return out


def schola_features(evidence):
    if set(evidence) not in ({'document'}, {'document','previous_document','previous_category','previous_location'}):
        raise ValueError('unregistered prospective editor evidence')
    document=evidence['document'];tokens=re.findall(r'\w+',document.casefold())
    counts=Counter(tokens[:256]+(tokens[-256:] if len(tokens)>256 else []))
    total=max(1,sum(counts.values()))
    result={'word:'+word:n/total for word,n in counts.items()}
    result.update({'log_words':math.log1p(len(tokens)),'log_lines':math.log1p(document.count('\n')),
                   'log_backslashes':math.log1p(document.count('\\'))})
    if 'previous_document' in evidence:
        before=evidence['previous_document'];old=re.findall(r'\w+',before.casefold())
        before_counts=Counter(old);after_counts=Counter(tokens)
        added=sum((after_counts-before_counts).values());removed=sum((before_counts-after_counts).values())
        if evidence['previous_category'] not in CATEGORIES or evidence['previous_location'] not in LOCATIONS:
            raise ValueError('unregistered previous annotation/location')
        result.update({'past_added':math.log1p(added),'past_removed':math.log1p(removed),
                       'past_length_change':math.copysign(math.log1p(abs(len(document)-len(before))),len(document)-len(before)),
                       'previous_category:'+evidence['previous_category']:1.,
                       'previous_location:'+evidence['previous_location']:1.})
    return result

def features(evidence,kind,feature_kind):
    if kind not in SUPPORT or feature_kind not in ('lexical','surface'):raise ValueError('unregistered prospective feature family')
    result=coauthor_features(evidence) if kind=='coauthor' else schola_features(evidence)
    return result if feature_kind=='lexical' else {k:v for k,v in result.items() if not k.startswith('word:')}


def previous(evidence,kind):
    features(evidence,kind,'surface')
    if kind=='coauthor':
        if 'earlier_handling' not in evidence:raise ValueError('prior-decision model requires explicit record evidence')
        return evidence['earlier_handling'][-1] if evidence['earlier_handling'] else 'none'
    key='previous_category' if kind=='schola_category' else 'previous_location'
    if key not in evidence:raise ValueError('prior-label model requires explicit record evidence')
    return evidence[key]


def distribution(values,classes):
    if set(values)!=set(classes) or any(type(v) not in (int,float) or not math.isfinite(v) or v<0 for v in values.values()):raise ValueError('invalid complete prospective distribution')
    if abs(math.fsum(values.values())-1)>1e-10:raise ValueError('prospective probabilities not normalized')
    return values


def predict(evidence,model):
    kind=model['kind'];classes=SUPPORT[kind]
    if model['classes']!=list(classes):raise ValueError('source-native prospective support changed')
    x=features(evidence,kind,model.get('features','surface'))
    prior=distribution(model['prior'],classes);method=model['method']
    if method=='prior':return prior
    if method=='majority':
        winner=min(classes,key=lambda k:(-prior[k],k));return {k:.99*(k==winner)+.01/len(classes) for k in classes}
    if method=='persistence':
        prev=previous(evidence,kind)
        return prior if prev=='none' else {k:.99*(k==prev)+.01/len(classes) for k in classes}
    if method=='previous_transition':
        prev=previous(evidence,kind);table=model['transitions']
        if set(table)-set(classes)-{'none'}:raise ValueError('unknown previous-label transition')
        return distribution(table[prev],classes) if prev in table else prior
    if method!='logistic':raise ValueError('unknown prospective model')
    fitted=model['fitted_classes'];weights=model['coefficients'];bias=model['intercept']
    if not fitted or len(set(fitted))!=len(fitted) or not set(fitted)<=set(classes) or set(weights)!=set(fitted) or set(bias)!=set(fitted):
        raise ValueError('incomplete prospective estimator')
    if any(type(v) not in (int,float) or not math.isfinite(v) for k in fitted for v in [bias[k],*weights[k].values()]):
        raise ValueError('nonfinite prospective estimator')
    logits={k:bias[k]+math.fsum(v*x.get(w,0.) for w,v in weights[k].items()) for k in fitted}
    if any(not math.isfinite(v) for v in logits.values()):raise ValueError('nonfinite prospective logit')
    maximum=max(logits.values());p={k:math.exp(v-maximum) for k,v in logits.items()};total=math.fsum(p.values())
    return distribution({k:.99*p.get(k,0.)/total+.01/len(classes) for k in classes},classes)
