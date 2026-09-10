"""Training-only consequence baselines, with separate development selection.

DESIGN CHECK: C03/X01/X02/X09/X11; LESSONS 3--5, CONTROLS 6.
NULL: no feature-target relationship leaves held-out prediction at the class prior;
ALTERNATIVE: an independently planted visible relationship is learned. Equal total
weight per source unit prevents repeated views/boundaries inflating its influence.
Six models: Jeffreys-smoothed class prior, two calibrated visible-rule tables,
and multinomial logistic regression at three fixed penalties. Half a count per
class is a declared training prior, never a floor applied to a scored prediction.
Development selects one complete comparator, not a per-item oracle. Disjoint
whole sources are mandatory; no scientific truth reaches the inference capsule.
"""
from collections import Counter
import math
import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp
from .common import digest
from .repair_features import LABELS,VERSION,features,predict,rule,validate

PENALTIES=(.001,.01,.1)


def checked(records):
    if not records:raise ValueError('empty consequence training cohort')
    for row in records:
        if set(row)!={'unit','evidence','target'} or not isinstance(row['unit'],str) or not row['unit']:
            raise ValueError('invalid training record boundary')
        validate(row['evidence'])
        if row['target'] not in LABELS:raise ValueError('undeclared consequence label')
    groups=Counter(r['unit'] for r in records)
    return np.array([1/groups[r['unit']] for r in records]),len(groups)


def objective(weights,matrix,targets,sample_weights,l2):
    w=weights.reshape(4,matrix.shape[1]);logits=matrix@w.T
    normalizers=logsumexp(logits,axis=1)
    residual=np.exp(logits-normalizers[:,None]);residual[np.arange(len(targets)),targets]-=1
    # The matrix includes one zero-feature, bias-one observation per class,
    # each of weight .5: a symmetric proper training prior on the intercept.
    value=float(np.sum(sample_weights*(normalizers-logits[np.arange(len(targets)),targets]))+.5*l2*np.sum(w*w))
    gradient=(residual*sample_weights[:,None]).T@matrix+l2*w
    if not math.isfinite(value) or not np.isfinite(gradient).all():raise ValueError('nonfinite consequence objective')
    return value,gradient.ravel()


def fit(records):
    weights,n=checked(records);counts={k:.5 for k in LABELS}
    for row,weight in zip(records,weights):counts[row['target']]+=float(weight)
    prior={k:v/sum(counts.values()) for k,v in counts.items()}
    common={'version':VERSION,'labels':list(LABELS)}
    models={'class_prior':{**common,'method':'class_prior','prior':prior}}
    for observed,name in ((False,'initial_rule'),(True,'observed_rule')):
        table={label:{k:.5 for k in LABELS} for label in LABELS}
        for row,weight in zip(records,weights):table[rule(row['evidence'],observed)][row['target']]+=float(weight)
        models[name]={**common,'method':name,'rows':{k:{label:v/sum(c.values()) for label,v in c.items()} for k,c in table.items()}}
    encoded=[features(r['evidence']) for r in records]
    columns=sorted(set().union(*(v.keys() for v in encoded)))
    matrix=np.array([[r.get(c,0.) for c in columns] for r in encoded]);origin=np.zeros((4,len(columns)))
    origin[:,columns.index('bias')]=1.;matrix=np.vstack([matrix,origin])
    targets=np.array([LABELS.index(r['target']) for r in records]+list(range(4)))
    sample_weights=np.concatenate([weights,np.full(4,.5)])/(n+2)
    optimizers={}
    for penalty in PENALTIES:
        result=minimize(objective,np.zeros(4*len(columns)),args=(matrix,targets,sample_weights,penalty),jac=True,
            method='L-BFGS-B',options={'maxiter':400,'ftol':1e-12,'gtol':1e-7})
        if not result.success or not np.isfinite(result.x).all():raise ValueError('consequence fitting failed: '+str(result.message))
        key='logistic-'+str(penalty);w=result.x.reshape(4,-1)
        models[key]={**common,'method':'logistic','weights':{label:dict(zip(columns,w[i].tolist())) for i,label in enumerate(LABELS)}}
        optimizers[key]={'converged':bool(result.success),'iterations':int(result.nit),'objective':float(result.fun),
            'max_abs_gradient':float(np.max(np.abs(result.jac))),'l2':penalty}
    return models,{'source_units':n,'records':len(records),'weighted_label_counts_including_prior':counts,
        'training_records_sha256':digest(records),'parameters_sha256':digest(models),'optimizers':optimizers,
        'training_prior':'half a count per class; logistic zero-feature intercept observations; no scoring floor'}


def select(models,training,development):
    _,_=checked(training);weights,n=checked(development)
    if set(r['unit'] for r in training)&set(r['unit'] for r in development):raise ValueError('training/development source overlap')
    # Stronger projected-copy leakage is checked here in addition to source IDs.
    if {digest(r['evidence']) for r in training}&{digest(r['evidence']) for r in development}:
        raise ValueError('training/development exact public-task overlap')
    scores={}
    for name,parameters in models.items():
        values=[predict(r['evidence'],parameters)[r['target']] for r in development]
        scores[name]=math.fsum(float(w)*math.log(p) for p,w in zip(values,weights))/n if all(values) else -math.inf
    chosen=min(scores,key=lambda k:(-scores[k],k))
    if not math.isfinite(scores[chosen]):raise ValueError('no finite complete development comparator')
    return {'selected':chosen,'scores':scores,'development_records_sha256':digest(development),'units':n,
        'parameters_sha256':digest(models),'selection':'largest mean whole-source held-out log score; name tie-break'}
