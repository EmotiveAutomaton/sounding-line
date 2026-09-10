"""Bounded leave-project-out next-category/location development baselines.

DESIGN CHECK: LESSONS sections 2-5; H08/I02/X03, L173 persistence control.
NULL: outcome mutation leaves all current features unchanged; prior/persistence
remain strong rivals without lexical insight. ALTERNATIVE: planted present-state
features support forecast gain. Four hundred source-order-independent hash-selected
eligible boundaries per project, five complete held-project folds, no new reserve.
Current visible text and previous completed difference are distinct evidence views.
All forecasts have fixed support and .01 uniform mixture before outcome access.
Bands: descriptive only with five projects; invalid inputs fail, no hidden fallback.
"""
from collections import Counter,defaultdict
import math
import re
import time

from runners.stage9.common import REPO,ROOT,closure,digest,freeze,read,file_hash
from runners.stage9.scholawrite import CATEGORIES,LOCATIONS,visible
from runners.stage9.scoring import paired_interval


def features(evidence):
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


def prior(labels,classes):
    counts=Counter(labels)
    if set(counts)-set(classes):raise ValueError('unknown target')
    return {k:(counts[k]+1)/(len(labels)+len(classes)) for k in classes}


def fit_predict(training,testing,view,target,classes):
    from sklearn.feature_extraction import DictVectorizer
    from sklearn.linear_model import LogisticRegression
    if {r['unit'] for r in training}&{r['unit'] for r in testing}:raise ValueError('project overlap')
    if {r['content'] for r in training}&{r['content'] for r in testing}:raise ValueError('current text duplicate across split')
    vectorizer=DictVectorizer();matrix=vectorizer.fit_transform([r[view] for r in training])
    labels=[r[target] for r in training]
    if len(set(labels))<2:return [prior(labels,classes) for _ in testing]
    counts=Counter(r['unit'] for r in training)
    weights=[len(training)/len(counts)/counts[r['unit']] for r in training]
    model=LogisticRegression(C=1.,max_iter=1000,solver='lbfgs',random_state=902107)
    model.fit(matrix,labels,sample_weight=weights)
    predictions=model.predict_proba(vectorizer.transform([r[view] for r in testing]))
    return [{k:.99*dict(zip(model.classes_,p)).get(k,0.)+.01/len(classes) for k in classes} for p in predictions]


def run():
    started=time.time();prepared=ROOT/'private/prepared/scholawrite-v2';output=ROOT/'private/pilot-baseline/scholawrite-v1'
    source=read(prepared/'IDENTITY.json');complete=read(prepared/'COMPLETE.json');ledger=read(prepared/'LEDGER.json')
    if complete['identity_sha256']!=digest(source) or not complete['source_counts_match']:raise ValueError('preparation invalid')
    rows=[];selection=[]
    for item in ledger:
        path=prepared/item['path']
        if file_hash(path)!=item['sha256']:raise ValueError('prepared project changed')
        project=read(path);eligible=[r for r in project['records'] if r['usable']]
        selected=sorted(eligible,key=lambda r:digest({'schola-baseline-sample':r['key']}))[:400]
        selection.append({'project':item['unit'],'eligible':len(eligible),'selected':[r['key'] for r in selected]})
        for record in selected:
            rows.append({'key':record['key'],'unit':record['unit'],'author':record['author'],'session':record['session'],
                         'content':record['after'],'category':record['next_category'],'location':record['next_location'],
                         'previous_category':record['category'],'previous_location':record['location'],
                         'artifact':features(visible(record,project['texts'],'artifact')),
                         'record':features(visible(record,project['texts'],'record'))})
    identity={'prepared_identity':digest(source),'prepared_ledger':digest(ledger),'selection':selection,
              'sources':closure([REPO/'runners/stage9'/n for n in ('scholawrite.py','scholawrite_baseline.py','common.py','scoring.py')]),
              'classification':'C1 logistic, fixed three/five classes, explicit .01 uniform mixture; equal project train mass',
              'features':'fixed first256+last256 current words and whole visible-fragment counts; record adds previous difference and completed category/location',
              'sampling':'400 hash-selected eligible boundaries per project before label access',
              'splits':'all five leave-project-out; exact current-text duplicates removed from each training fold',
              'scope':'historically exposed development baseline, no new reserve, not paper reproduction or H08 admission'}
    freeze(output/'IDENTITY.json',identity)
    if (output/'COMPLETE.json').exists():return read(output/'COMPLETE.json')
    fold_receipts=[];predictions=[]
    for held in sorted({r['unit'] for r in rows}):
        testing=[r for r in rows if r['unit']==held];test_texts={r['content'] for r in testing}
        attempted=[r for r in rows if r['unit']!=held]
        training=[r for r in attempted if r['content'] not in test_texts]
        if not training or not testing:raise ValueError('empty held-project fold')
        fold={'held_project':held,'fit_attempts':len(attempted),'fit_rows':len(training),
              'excluded_current_text_duplicates':len(attempted)-len(training),'test_rows':len(testing),
              'fit_projects':sorted({r['unit'] for r in training})}
        fold_receipts.append(fold)
        for target,classes in [('category',CATEGORIES),('location',LOCATIONS)]:
            model={v:fit_predict(training,testing,v,target,classes) for v in ('artifact','record')}
            rates=prior([r[target] for r in training],classes);transitions=defaultdict(list)
            for r in training:transitions[r['previous_'+target]].append(r[target])
            for i,row in enumerate(testing):
                previous=row['previous_'+target]
                probs={v:model[v][i] for v in model}
                probs.update({'class_prior':rates,'previous_transition':prior(transitions[previous],classes) if transitions[previous] else rates,
                              'persistence':{k:.99*int(k==previous)+.01/len(classes) for k in classes},
                              'uniform':{k:1/len(classes) for k in classes}})
                predictions.append({'key':row['key'],'unit':held,'target':target,'probabilities':probs})
    freeze(output/'FOLDS.json',fold_receipts);freeze(output/'PREDICTIONS.json',predictions)
    truths={r['key']:{k:r[k] for k in ('category','location')} for r in rows};freeze(output/'TRUTH.json',truths)
    scored=[{'key':r['key'],'unit':r['unit'],'target':r['target'],
             'scores':{a:math.log(p[truths[r['key']][r['target']]]) for a,p in r['probabilities'].items()}} for r in predictions]
    freeze(output/'SCORES.json',scored);tasks={}
    for target in ('category','location'):
        selected=[r for r in scored if r['target']==target];contrasts={}
        for left,right in [('artifact','class_prior'),('record','class_prior'),('record','artifact'),
                           ('record','previous_transition'),('record','persistence')]:
            contrasts[left+'_over_'+right]=paired_interval([r|{'difference':r['scores'][left]-r['scores'][right]} for r in selected])
        tasks[target]={'contrasts':contrasts,'classes':dict(Counter(r[target] for r in rows)),
                       'unchanged_from_previous':sum(r[target]==r['previous_'+target] for r in rows),
                       'targets':len(rows),'disposition':'DESCRIPTIVE'}
    result={'identity_sha256':digest(identity),'completed_at':time.time(),'elapsed_seconds':time.time()-started,
            'attempted_eligible_boundaries':sum(r['eligible'] for r in selection),'sampled_boundaries':len(rows),
            'projects':len(selection),'project_scoped_authors':len({r['author'] for r in rows}),
            'sessions':len({r['session'] for r in rows}),'folds':fold_receipts,'tasks':tasks,'reserve_groups':0,
            'limits':['five projects; descriptive only','annotator spans create persistence',
                      'next released edit not next physical keystroke','location relative to visible fragment','project-scoped identity only']}
    freeze(output/'COMPLETE.json',result);freeze(ROOT/'intake/SCHOLAWRITE_BASELINE.json',result)
    return result


if __name__=='__main__':
    print(run())
