"""Training-only exported current-draft and earlier-record predictive baselines.

DESIGN CHECK: H07/H08/X01/X02/X06; LESSONS 3--5. NULL: repeated source events
cannot increase that group's total fitted mass; missing classes survive as fixed
support. ALTERNATIVE: learned current-text features reproduce the fitted estimator.
Every prior/persistence/transition rival is explicit, fitted only on its partition.
Nonconvergence and export disagreement fail. Source-level split checks are separate.
"""
from collections import Counter,defaultdict
from .record_features import SUPPORT,features,previous,predict


def weights_and_prior(rows,kind):
    if kind not in SUPPORT or not rows or len({r['key'] for r in rows})!=len(rows):raise ValueError('nonempty unique prospective training rows required')
    classes=SUPPORT[kind];groups=Counter(r['unit'] for r in rows);weights=[len(rows)/len(groups)/groups[r['unit']] for r in rows]
    counts=Counter()
    for r in rows:
        if r['truth'] not in classes:raise ValueError('training label outside source-native support')
        counts[r['truth']]+=1/groups[r['unit']]
    prior={k:(counts[k]+1)/(len(groups)+len(classes)) for k in classes}
    return weights,prior


def fit(rows,kind,feature_kind):
    from sklearn.feature_extraction import DictVectorizer
    from sklearn.linear_model import LogisticRegression
    weights,prior=weights_and_prior(rows,kind);classes=SUPPORT[kind]
    base={'kind':kind,'classes':list(classes),'prior':prior,'features':feature_kind,'training_rows':len(rows),
        'training_groups':len({r['unit'] for r in rows}),'forecast':'C1 logistic, equal group fitting mass, explicit .01 uniform mixture'}
    labels=[r['truth'] for r in rows]
    if len(set(labels))<2:return base|{'method':'prior','fit_limit':'only one observed training class'}
    vec=DictVectorizer();x=vec.fit_transform([features(r['evidence'],kind,feature_kind) for r in rows])
    model=LogisticRegression(C=1.,max_iter=1000,solver='lbfgs',random_state=902107)
    model.fit(x,labels,sample_weight=weights)
    if max(model.n_iter_)>=1000:raise ValueError('prospective estimator did not converge')
    fitted=list(model.classes_);coefficients=model.coef_;bias=model.intercept_
    if len(fitted)==2:coefficients=[-coefficients[0]/2,coefficients[0]/2];bias=[-bias[0]/2,bias[0]/2]
    exported=base|{'method':'logistic','fitted_classes':fitted,
        'coefficients':{k:{str(w):float(v) for w,v in zip(vec.get_feature_names_out(),values)} for k,values in zip(fitted,coefficients)},
        'intercept':{k:float(v) for k,v in zip(fitted,bias)}}
    for row,p in zip(rows,model.predict_proba(x)):
        actual=predict(row['evidence'],exported);expected={k:.99*dict(zip(fitted,p)).get(k,0.)+.01/len(classes) for k in classes}
        if any(abs(actual[k]-expected[k])>1e-12 for k in classes):raise ValueError('exported prospective estimator differs')
    return exported


def all_models(rows,kind,record):
    weights,prior=weights_and_prior(rows,kind);base={'kind':kind,'classes':list(SUPPORT[kind]),'prior':prior}
    result={'lexical':fit(rows,kind,'lexical'),'surface':fit(rows,kind,'surface'),
        'class_prior':base|{'method':'prior'},'majority':base|{'method':'majority'}}
    if record:
        counts=defaultdict(Counter);total=Counter();scale=len({r['unit'] for r in rows})/len(rows)
        for row,w in zip(rows,weights):
            key=previous(row['evidence'],kind);counts[key][row['truth']]+=w*scale;total[key]+=w*scale
        transitions={p:{k:(values[k]+1)/(total[p]+len(SUPPORT[kind])) for k in SUPPORT[kind]} for p,values in counts.items()}
        result.update(previous_transition=base|{'method':'previous_transition','transitions':transitions},persistence=base|{'method':'persistence'})
    return result
