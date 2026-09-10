"""Prospective, development-only CoAuthor handling baselines.

DESIGN CHECK: LESSONS sections 2, 3, 4 and 5; H07/I02/X02/X03/X11.
NULL: changing future selection/edit labels cannot change current features; a
constant history gives no extra information over its action-rate rival.
ALTERNATIVE: known document features or an actually preceding handling label can
predict a new outcome. Train and test writers AND prompts are disjoint. Historical
project exposure is retained; this split never creates an untouched reserve.
Scores average within writer/prompt first; small writer/stimulus counts descriptive.
"""
from collections import Counter, defaultdict
import math
import re
import time

from runners.stage9.common import REPO, ROOT, closure, digest, freeze, read
from runners.stage9.coauthor import DECISIONS, project
from runners.stage9.scoring import paired_interval


def features(evidence):
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


def prior(labels):
    counts=Counter(labels);return {k:(counts[k]+1)/(len(labels)+len(DECISIONS)) for k in DECISIONS}


def model_fit(rows, view):
    from sklearn.feature_extraction import DictVectorizer
    from sklearn.linear_model import LogisticRegression
    vectorizer=DictVectorizer()
    matrix=vectorizer.fit_transform([features(r[view]) for r in rows])
    target=[r['truth'] for r in rows]
    if len(set(target))<2:
        return vectorizer,None,prior(target)
    model=LogisticRegression(C=1.,max_iter=1000,solver='lbfgs',random_state=902103)
    model.fit(matrix,target)
    return vectorizer,model,None


def predict(fitted, rows, view):
    vectorizer,model,fallback=fitted
    if model is None:return [dict(fallback) for _ in rows]
    matrix=vectorizer.transform([features(r[view]) for r in rows])
    probabilities=model.predict_proba(matrix)
    # Explicit common mixture yields a normalized forecast with positive support.
    return [{k:.99*dict(zip(model.classes_,p)).get(k,0.)+.01/len(DECISIONS) for k in DECISIONS}
            for p in probabilities]


def run():
    started=time.time();root=ROOT/'private/prepared/coauthor-v2'
    output=ROOT/'private/pilot-baseline/coauthor-v2'
    if (output/'COMPLETE.json').exists():return read(output/'COMPLETE.json')
    source=read(root/'IDENTITY.json');complete=read(root/'COMPLETE.json');ledger=read(root/'LEDGER.json')
    if complete['identity_sha256']!=digest(source):raise ValueError('CoAuthor source identity changed')
    dev=[r for r in ledger if r.get('split')=='development']
    people=sorted({r['writer'] for r in dev},key=lambda k:digest({'coauthor-fit-writer':k}))
    fit_people=set(people[:2*len(people)//3]);test_people=set(people)-fit_people
    prompts=sorted({r['prompt'] for r in dev},key=lambda k:digest({'coauthor-test-prompt':k}))
    test_prompts=set(prompts[:max(2,len(prompts)//4)]);fit_prompts=set(prompts)-test_prompts
    assert not fit_people&test_people and not fit_prompts&test_prompts
    training=[];testing=[];attempts=Counter();exclusions=Counter()
    for record in dev:
        lane=('fit' if record['writer'] in fit_people and record['prompt'] in fit_prompts else
              'test' if record['writer'] in test_people and record['prompt'] in test_prompts else None)
        if lane is None:continue
        session=read(root/'sessions'/(record['key']+'.json'));history=[]
        for event in session['events']:
            attempts[lane]+=1
            if not event['usable']:
                exclusions[lane+': unsupported replay or handling']+=1;continue
            row={'key':digest({'session':record['key'],'event':event['ordinal']}),
                 'unit':record['writer'],'prompt':record['prompt'],'session':record['key'],'domain':record['domain'],
                 'artifact':project(event,'artifact'),'record':project(event,'record',history),
                 'truth':event['decision']}
            (training if lane=='fit' else testing).append(row)
            history.append(event)
    if not training or not testing:raise ValueError('empty development baseline population')
    plan={'source_identity':digest(source),'sources':closure([REPO/'runners/stage9'/n for n in
          ('coauthor_baseline.py','coauthor.py','scoring.py','common.py')]),
          'split':{'fit_writers':sorted(fit_people),'test_writers':sorted(test_people),
                   'fit_prompts':sorted(fit_prompts),'test_prompts':sorted(test_prompts)},
          'scope':'development-only baseline; no new reserve and no scientific admission',
          'features':'current document last512word lexical frequencies and whole-document length; currently displayed candidate lengths/overlap; record adds only completed prior handling',
          'classification':'four named classes, C1 logistic regression, normalized .01 uniform mixture',
          'history':'earlier completed opportunities in the same session, never current handling'}
    freeze(output/'IDENTITY.json',plan)
    probabilities={view:predict(model_fit(training,view),testing,view) for view in ('artifact','record')}
    rates=prior([r['truth'] for r in training]);transitions=defaultdict(list)
    for row in training:
        history=row['record']['earlier_handling'];transitions[history[-1] if history else 'none'].append(row['truth'])
    predictions=[]
    for i,row in enumerate(testing):
        history=row['record']['earlier_handling'];previous=history[-1] if history else 'none'
        markov=prior(transitions[previous]) if transitions[previous] else rates
        arms={'uniform':{k:1/4 for k in DECISIONS},'action_rate':rates,'previous_decision':markov,
              'artifact':probabilities['artifact'][i],'record':probabilities['record'][i]}
        predictions.append({k:row[k] for k in ('key','unit','prompt','session','domain')}|{'probabilities':arms})
    # Writer IDs are opaque hashes and remain evaluator bookkeeping, never features.
    freeze(output/'PREDICTIONS.json',predictions)
    truths={row['key']:row['truth'] for row in testing};freeze(output/'TRUTH.json',truths)
    scored=[{k:r[k] for k in ('key','unit','prompt','session','domain')}|
            {'scores':{arm:math.log(p[truths[r['key']]]) for arm,p in r['probabilities'].items()}}
            for r in predictions]
    contrasts={}
    for left,right in (('artifact','action_rate'),('record','action_rate'),('record','previous_decision'),('record','artifact')):
        contrasts[left+'_over_'+right]=paired_interval([
            r|{'difference':r['scores'][left]-r['scores'][right]} for r in scored],second_cluster='prompt')
    result={'identity_sha256':digest(plan),'attempts':dict(attempts),'exclusions':dict(exclusions),
            'training_events':len(training),'test_events':len(testing),'test_writers':len({r['unit'] for r in testing}),
            'test_sessions':len({r['session'] for r in testing}),'test_prompts':len({r['prompt'] for r in testing}),
            'training_classes':dict(Counter(r['truth'] for r in training)),
            'test_classes':dict(Counter(r['truth'] for r in testing)),
            'test_domains':dict(Counter(r['domain'] for r in testing)),
            'contrasts':contrasts,'disposition':'DESCRIPTIVE','reserve_groups':0,
            'elapsed_seconds':time.time()-started,'completed_at':time.time(),
            'limit':'few held development writers/prompts; internal reconstruction only; previous project exposure; no historical intention or authorship share claim'}
    freeze(output/'SCORES.json',scored);freeze(output/'COMPLETE.json',result)
    freeze(ROOT/'intake/COAUTHOR_BASELINE.json',result)
    return result


if __name__=='__main__':
    print(run())
