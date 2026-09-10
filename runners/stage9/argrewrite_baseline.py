"""Grouped retrospective and genuine whole-cycle prospective ArgRewrite baselines.

DESIGN CHECK: LESSONS sections 2-5; H01, L79/L81/L85 corrections read.
NULL: prior-label prediction and future-blind features work without text signal;
future labels cannot select a current excerpt or change an input feature.
ALTERNATIVE: an explicit actual revision delta carries learnable class information.
All essays/student lineages stay together. Nine fixed classes, explicit .01 uniform
forecast mixture, equal essay training and scoring weights; no new reserve.
Bands: descriptive estimates only; preparation failure blocks fitting, no silent skip.
"""
from collections import Counter
import math
import re
import time

from runners.stage9.common import REPO, ROOT, closure, digest, freeze, read, file_hash
from runners.stage9.argrewrite import CLASSES, visible, future_visible
from runners.run_arg_replication import change_features
from runners.stage9.scoring import paired_interval


def features(evidence):
    if set(evidence) not in ({'text'}, {'before','after'}, {'before','after','earlier_labels'}):
        raise ValueError('unregistered revision evidence')
    result = {}
    for side in ('text','before','after'):
        if side not in evidence: continue
        words = re.findall(r'\w+', evidence[side].casefold())
        result[side+':log_words'] = math.log1p(len(words))
        # Fixed first1024 word budget never depends on the later target location.
        counts = Counter(words[:1024]); total = max(1,sum(counts.values()))
        result.update({side+':word:'+w:n/total for w,n in counts.items()})
    if 'before' in evidence:
        delta = change_features(evidence['before'],evidence['after'])
        result.update({'change:'+str(i): math.copysign(math.log1p(abs(v)),v) for i,v in enumerate(delta)})
    if 'earlier_labels' in evidence:
        if any(label not in CLASSES for label in evidence['earlier_labels']): raise ValueError('unknown earlier label')
        result.update({'earlier:'+k:v for k,v in prior(evidence['earlier_labels']).items()})
    return result


def prior(labels):
    counts = Counter(labels)
    if set(counts)-set(CLASSES):raise ValueError('unknown label')
    return {k:(counts[k]+1)/(len(labels)+len(CLASSES)) for k in CLASSES}


def fit_predict(training, testing, view):
    from sklearn.feature_extraction import DictVectorizer
    from sklearn.linear_model import LogisticRegression
    vectorizer = DictVectorizer()
    train = vectorizer.fit_transform([features(r[view]) for r in training])
    labels = [r['truth'] for r in training]
    if len(set(labels)) < 2:return [prior(labels) for _ in testing]
    groups = Counter(r['unit'] for r in training)
    weights = [len(training)/len(groups)/groups[r['unit']] for r in training]
    model = LogisticRegression(C=1., max_iter=1000, solver='lbfgs', random_state=902106)
    model.fit(train, labels, sample_weight=weights)
    probabilities = model.predict_proba(vectorizer.transform([features(r[view]) for r in testing]))
    return [{k:.99*dict(zip(model.classes_,p)).get(k,0.)+.01/len(CLASSES) for k in CLASSES} for p in probabilities]


def run():
    started=time.time(); prepared=ROOT/'private/prepared/argrewrite-v3'; output=ROOT/'private/pilot-baseline/argrewrite-v1'
    source=read(prepared/'IDENTITY.json'); complete=read(prepared/'COMPLETE.json')
    if complete['identity_sha256']!=digest(source) or not complete['historical_v4_exact']:
        raise ValueError('canonical preparation not accepted')
    paths=sorted((prepared/'essays').glob('*.json'))
    essays=[read(p) for p in paths]
    groups=sorted([e['group'] for e in essays],key=lambda g:digest({'arg-fit':g}))
    fit_groups=set(groups[:3*len(groups)//4]);test_groups=set(groups)-fit_groups
    identity={'prepared_identity':digest(source),'prepared_records':closure(paths),
              'sources':closure([REPO/'runners/stage9'/n for n in ('argrewrite.py','argrewrite_baseline.py','common.py','scoring.py')]+[REPO/'runners/run_arg_replication.py']),
              'fit_groups':sorted(fit_groups),'test_groups':sorted(test_groups),'reserve_groups':0,
              'scope':'historically exposed development-only, no published-model reproduction or H01 claim',
              'features':'first1024words and wholetext length; pair adds the explicit19 change features; record adds only earlier cycle labels',
              'forecast':'nine fixed classes, C1 logistic, .01 uniform mixture; equal essay train mass',
              'future_target':'each actually annotated canonical draft2->3 unit under ONE forecast from the whole earlier draft; essay mean score'}
    freeze(output/'IDENTITY.json',identity)
    if (output/'COMPLETE.json').exists():return read(output/'COMPLETE.json')
    retrospective={'fit':[],'test':[]};future={'fit':[],'test':[]};counts=Counter()
    for essay in essays:
        lane='fit' if essay['group'] in fit_groups else 'test'
        previous=[u['fine'] for u in essay['units'] if u['cycle']=='12' and u['usable']]
        for unit in essay['units']:
            counts['retrospective_'+lane+'_attempts']+=1
            if not unit['usable']:continue
            retrospective[lane].append({'key':unit['key'],'unit':unit['group'],'cycle':unit['cycle'],
                                        'truth':unit['fine'],'artifact':visible(unit,'artifact'),'pair':visible(unit,'pair'),
                                        'previous':previous if unit['cycle']=='23' else []})
        counts['future_'+lane+'_attempted_essays']+=1
        if not essay['future_usable']:
            counts['future_'+lane+'_excluded_essays']+=1;continue
        later=[u for u in essay['units'] if u['cycle']=='23' and u['usable']]
        if not later:
            counts['future_'+lane+'_empty_cycles']+=1;continue
        for unit in later:
            future[lane].append({'key':unit['key'],'unit':unit['group'],'truth':unit['fine'],
                                'artifact':future_visible(essay,'artifact'),'record':future_visible(essay,'record'),
                                'previous':previous})
    scores={}; summaries={}
    for task, data, views in [('retrospective',retrospective,('artifact','pair')),('future',future,('artifact','record'))]:
        training, testing=data['fit'],data['test']
        if not training or not testing:raise ValueError('empty development task')
        if {r['unit'] for r in training}&{r['unit'] for r in testing}:raise ValueError('group leakage')
        predictions={view:fit_predict(training,testing,view) for view in views}
        rates=prior([r['truth'] for r in training]); rows=[]
        for i,row in enumerate(testing):
            previous=prior(row['previous']) if row['previous'] else rates
            rows.append({'key':row['key'],'unit':row['unit'],
                         'probabilities':{**{v:predictions[v][i] for v in views},'class_prior':rates,
                                          'previous_cycle':previous,'uniform':{k:1/len(CLASSES) for k in CLASSES}}})
        freeze(output/(task+'_PREDICTIONS.json'),rows)
        truths={r['key']:r['truth'] for r in testing};freeze(output/(task+'_TRUTH.json'),truths)
        scored=[{'key':r['key'],'unit':r['unit'],
                 'scores':{arm:math.log(p[truths[r['key']]]) for arm,p in r['probabilities'].items()}} for r in rows]
        freeze(output/(task+'_SCORES.json'),scored);scores[task]=scored
        contrasts={}
        for left,right in [(v,'class_prior') for v in views]+[(views[1],views[0]),(views[1],'previous_cycle')]:
            contrasts[left+'_over_'+right]=paired_interval([r|{'difference':r['scores'][left]-r['scores'][right]} for r in scored])
        summaries[task]={'fit_events':len(training),'test_events':len(testing),
                         'fit_essays':len({r['unit'] for r in training}),'test_essays':len({r['unit'] for r in testing}),
                         'test_class_counts':dict(Counter(r['truth'] for r in testing)),
                         'contrasts':contrasts,'disposition':'DESCRIPTIVE'}
    result={'identity_sha256':digest(identity),'completed_at':time.time(),'elapsed_seconds':time.time()-started,
            'counts':dict(counts),'tasks':summaries,'reserve_groups':0,
            'limit':'single student-essay topic, previous project exposure, no independent H01 claim; prior-cycle labels explicit-record only'}
    freeze(output/'COMPLETE.json',result);freeze(ROOT/'intake/ARGREWRITE_BASELINE.json',result)
    return result


if __name__=='__main__':
    print(run())
