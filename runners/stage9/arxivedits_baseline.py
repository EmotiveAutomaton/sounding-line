"""Leave-paper-out canonical-span development baseline, explicit license subset.

DESIGN CHECK: LESSONS 2-5; H02. NULL: priors and the explicit difference rival
remain scored; duplicating a label-bearing edit cannot create an independent paper.
ALTERNATIVE: actual before/after features learn annotated span purposes. Seven fixed
labels, C1 logistic, equal paper training weight, .01 uniform forecast mixture.
All three papers tested once with whole-paper holdout. Bands: descriptive only;
invalid inputs fail, no reserve, no population inference from this small selection.
"""
from collections import Counter
import time
from runners.stage9.common import ROOT,REPO,closure,digest,freeze,read,file_hash
from runners.stage9.arxivedits import LABELS,visible
from runners.stage9.argrewrite_baseline import features
from runners.stage9.scoring import log_score,paired_interval


def prior(rows):
    groups=Counter(r['independent_unit'] for r in rows);counts=Counter()
    for r in rows:
        if r['label'] not in LABELS:raise ValueError('unknown label')
        counts[r['label']]+=1/groups[r['independent_unit']]
    # One pseudo-observation per class, actual paper-equivalent total mass.
    return {k:(counts[k]+1)/(len(groups)+len(LABELS)) for k in LABELS}


def vector(row,view):
    evidence=visible(row,view)
    return features(evidence if view=='artifact' else {'before':evidence['before'],'after':evidence['text']})


def fit_predict(training,testing,view):
    from sklearn.feature_extraction import DictVectorizer
    from sklearn.linear_model import LogisticRegression
    if not training or not testing:raise ValueError('empty paper split')
    if {r['independent_unit'] for r in training}&{r['independent_unit'] for r in testing}:
        raise ValueError('paper overlap')
    labels=[r['label'] for r in training]
    if len(set(labels))<2:return [prior(training) for _ in testing]
    vec=DictVectorizer();x=vec.fit_transform([vector(r,view) for r in training])
    groups=Counter(r['independent_unit'] for r in training)
    weights=[len(training)/len(groups)/groups[r['independent_unit']] for r in training]
    model=LogisticRegression(C=1.,solver='lbfgs',max_iter=1000,random_state=902108)
    model.fit(x,labels,sample_weight=weights)
    probs=model.predict_proba(vec.transform([vector(r,view) for r in testing]))
    return [{k:.99*dict(zip(model.classes_,p)).get(k,0.)+.01/len(LABELS) for k in LABELS} for p in probs]


def run():
    started=time.time();prepared=ROOT/'private/prepared/arxivedits-v1';out=ROOT/'private/pilot-baseline/arxivedits-v1'
    complete=read(prepared/'COMPLETE.json');source=read(prepared/'IDENTITY.json')
    if complete['identity_sha256']!=digest(source) or complete['source_counts_match'] is not True:raise ValueError('preparation invalid')
    for name,sha in complete['output_hashes'].items():
        if file_hash(prepared/name)!=sha:raise ValueError('prepared source changed')
    rows=read(prepared/'RECORDS.json');groups=sorted({r['independent_unit'] for r in rows})
    identity={'prepared':digest(source),'records':file_hash(prepared/'RECORDS.json'),
              'sources':closure([REPO/'runners/stage9'/n for n in ('common.py','arxivedits.py','arxivedits_baseline.py','argrewrite.py','argrewrite_baseline.py','scoring.py')]+[REPO/'runners/run_arg_replication.py']),
              'classes':LABELS,'folds':groups,'scope':'all selected lineages development-only; qualitative annotated-span task',
              'forecast':'C1 logistic, equal-paper training, .01 uniform mixture; equal-paper smoothed prior',
              'features':'first1024 words and whole span length; pair adds explicit19 change features'}
    freeze(out/'IDENTITY.json',identity)
    if (out/'COMPLETE.json').exists():return read(out/'COMPLETE.json')
    predictions=[];folds=[]
    for held in groups:
        test=[r for r in rows if r['independent_unit']==held];train=[r for r in rows if r['independent_unit']!=held]
        # Remove exact nonempty before/after pairs crossing lineages; empty deletion
        # artifacts alone are common outcomes and cannot erase all deletion training.
        pairs={(r['before'],r['artifact']) for r in test};attempts=len(train)
        train=[r for r in train if (r['before'],r['artifact']) not in pairs]
        models={v:fit_predict(train,test,v) for v in ('artifact','pair')};rates=prior(train)
        folds.append({'held':held,'fit_attempts':attempts,'fit_rows':len(train),'test_rows':len(test)})
        for i,row in enumerate(test):
            predictions.append({'key':row['key'],'unit':held,'probabilities':{v:models[v][i] for v in models}|
                                {'class_prior':rates,'uniform':{k:1/len(LABELS) for k in LABELS}}})
    freeze(out/'PREDICTIONS.json',predictions);truth={r['key']:r['label'] for r in rows};freeze(out/'TRUTH.json',truth)
    scored=[{'key':r['key'],'unit':r['unit'],'scores':{v:log_score(p,truth[r['key']]) for v,p in r['probabilities'].items()}} for r in predictions]
    freeze(out/'SCORES.json',scored);freeze(out/'FOLDS.json',folds)
    contrasts={a+'_over_'+b:paired_interval([r|{'difference':r['scores'][a]-r['scores'][b]} for r in scored])
               for a,b in [('artifact','class_prior'),('pair','class_prior'),('pair','artifact')]}
    result={'identity_sha256':digest(identity),'elapsed_seconds':time.time()-started,'completed_at':time.time(),
            'targets':len(rows),'paper_lineages':len(groups),'classes':dict(Counter(truth.values())),
            'folds':folds,'contrasts':contrasts,'disposition':'DESCRIPTIVE','reserve_groups':0,
            'output_hashes':{n:file_hash(out/n) for n in ('PREDICTIONS.json','TRUTH.json','SCORES.json','FOLDS.json')},
            'limits':['three-paper qualitative selection','annotated boundaries supplied; no whole-artifact localization',
                      'no source-paper classifier reproduction','cross-source closure and scoped H02 remain owed']}
    freeze(out/'COMPLETE.json',result);freeze(ROOT/'intake/ARXIVEDITS_BASELINE.json',result)
    return result


if __name__=='__main__':print(run())
