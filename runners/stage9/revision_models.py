"""Preparation-only fitted revision rivals; export pure numeric parameters.

DESIGN CHECK: H01/H02/X01/X06; LESSONS 3--5. NULL: equal text and balanced
labels cannot invent a feature advantage, and test labels never enter fitting.
ALTERNATIVE: learned lexical/delta associations reproduce the fitted estimator.
Whole source lineages share equal training mass, annotation votes stay fractional,
and all fixed classes survive even when absent from training. Nonconvergence or
empty training refuses. Split enforcement belongs to the verified source consumer.
"""
from collections import Counter
import math
from .revision_features import features,predict


def training_rows(rows,classes):
    if not rows or not classes or len(classes)!=len(set(classes)):raise ValueError('nonempty training and unique classes required')
    if len({r['key'] for r in rows})!=len(rows):raise ValueError('duplicate training records')
    groups=Counter(r['unit'] for r in rows);expanded=[]
    for row in rows:
        labels=row['labels']
        if not labels or any(k not in classes for k in labels):raise ValueError('missing or unknown training annotation')
        for label,n in Counter(labels).items():
            expanded.append({'unit':row['unit'],'evidence':row['evidence'],'label':label,
                'weight':n/len(labels)/groups[row['unit']]})
    counts=Counter()
    for row in expanded:counts[row['label']]+=row['weight']
    prior={k:(counts[k]+1)/(len(groups)+len(classes)) for k in classes}
    return expanded,prior


def fit(rows,classes,kind='lexical_delta'):
    from sklearn.feature_extraction import DictVectorizer
    from sklearn.linear_model import LogisticRegression
    expanded,prior=training_rows(rows,classes)
    base={'classes':list(classes),'prior':prior,'training_records':len(rows),
        'training_groups':len({r['unit'] for r in rows}),'features':kind,
        'forecast':'C1 logistic; fixed .01 uniform mixture; equal source-lineage mass; fractional released annotations'}
    labels=[r['label'] for r in expanded]
    if len(set(labels))<2:return {**base,'method':'prior','fit_limit':'only one observed training class'}
    vec=DictVectorizer();x=vec.fit_transform([features(r['evidence'],classes,kind) for r in expanded])
    # Normalize total fit weight to the number of original records, matching the
    # existing equal-lineage development estimator's regularization convention.
    scale=len(rows)/len({r['unit'] for r in rows})
    model=LogisticRegression(C=1.,solver='lbfgs',max_iter=1000,random_state=902106)
    model.fit(x,labels,sample_weight=[r['weight']*scale for r in expanded])
    if max(model.n_iter_)>=1000:raise ValueError('revision logistic fit did not converge')
    names=list(vec.get_feature_names_out());fitted=list(model.classes_)
    coefficients=model.coef_;intercept=model.intercept_
    if len(fitted)==2:
        # sklearn's binary probability uses sigmoid(z); softmax(-z/2,z/2) is exact.
        coefficients=[-coefficients[0]/2,coefficients[0]/2];intercept=[-intercept[0]/2,intercept[0]/2]
    exported={**base,'method':'logistic','fitted_classes':fitted,
        'coefficients':{k:{name:float(v) for name,v in zip(names,weights)} for k,weights in zip(fitted,coefficients)},
        'intercept':{k:float(v) for k,v in zip(fitted,intercept)}}
    reference=model.predict_proba(x)
    for row,p in zip(expanded,reference):
        actual=predict(row['evidence'],exported)
        expected={k:.99*dict(zip(fitted,p)).get(k,0.)+.01/len(classes) for k in classes}
        if any(abs(actual[k]-expected[k])>1e-12 for k in classes):raise ValueError('exported estimator differs from fitted probabilities')
    return exported


def all_models(rows,classes,*,earlier_labels=False):
    lexical=fit(rows,classes,'lexical_delta');surface=fit(rows,classes,'surface_delta')
    base={'classes':list(classes),'prior':lexical['prior']}
    result={'lexical_delta':lexical,'surface_delta':surface,
        'class_prior':{**base,'method':'prior'},'majority':{**base,'method':'majority'}}
    if earlier_labels:result['previous_cycle']={**base,'method':'previous_cycle'}
    return result
