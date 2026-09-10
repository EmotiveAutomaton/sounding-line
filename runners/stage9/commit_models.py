"""Fit numeric diff/description models on complete training menus only.

DESIGN CHECK: H06/X01/X03/X06; LESSONS 3--5. NULL: a repeated repository's
extra rows cannot increase its total fitting weight; no candidate-position feature
is available. ALTERNATIVE: source correspondence learned on complete paired menus
reproduces the fitted estimator. Failed convergence or changed exported forecasts
refuses. Selection and grouped source exclusion belong to the case consumer.
"""
from collections import Counter
from .commit_features import check,pair_features,project,predict,normalize


def expanded(rows):
    if not rows or len({r['key'] for r in rows})!=len(rows):raise ValueError('nonempty unique training menus required')
    counts=Counter(r['unit'] for r in rows);output=[]
    for row in rows:
        candidates=check(row['evidence'])
        if row['truth'] not in ('0','1','2','3'):raise ValueError('description truth outside menu')
        for i,candidate in enumerate(candidates):
            output.append({'features':pair_features(row['evidence']['diff'],candidate),'label':int(str(i)==row['truth']),
                'weight':len(rows)/len(counts)/counts[row['unit']],'unit':row['unit']})
    return output


def fit(rows,kind):
    from sklearn.feature_extraction import DictVectorizer
    from sklearn.linear_model import LogisticRegression
    pairs=expanded(rows);vec=DictVectorizer();x=vec.fit_transform([project(r['features'],kind) for r in pairs])
    model=LogisticRegression(C=1.,solver='lbfgs',class_weight='balanced',max_iter=1000,random_state=902109)
    model.fit(x,[r['label'] for r in pairs],sample_weight=[r['weight'] for r in pairs])
    if max(model.n_iter_)>=1000:raise ValueError('description fit did not converge')
    result={'method':'logistic_pair','features':kind,'intercept':float(model.intercept_[0]),
        'coefficients':{str(k):float(v) for k,v in zip(vec.get_feature_names_out(),model.coef_[0])},
        'training_menus':len(rows),'training_groups':len({r['unit'] for r in rows}),
        'forecast':'C1 balanced binary pair classifier; exp(logit) menu normalization and explicit .01 uniform mixture; equal repository training mass'}
    logits=model.decision_function(x)
    for i,row in enumerate(rows):
        expected=normalize(logits[4*i:4*i+4]);actual=predict(row['evidence'],result)
        if any(abs(actual[k]-expected[k])>1e-12 for k in actual):raise ValueError('exported description forecast differs')
    return result


def all_models(rows):
    return {**{kind:fit(rows,kind) for kind in ('all','surface','description_only')},
        **{name:{'method':name} for name in ('uniform','lexical_overlap','filename_overlap')}}
