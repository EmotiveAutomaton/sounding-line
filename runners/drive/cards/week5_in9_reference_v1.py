"""Independent IN9 replay: trust-region likelihood, pair-count AUC, raw sums.

Does not call the production optimizer, cross-validation or AUC formula.
"""
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit


def evaluate(x, y, folds, weight, secondary_indices):
    x, y, weight = np.asarray(x, float), np.asarray(y, float), np.asarray(weight, float)
    prediction = np.zeros(len(y))
    for fold in range(5):
        training = np.flatnonzero((folds != fold) & (weight > 0))
        testing = np.flatnonzero(folds == fold)
        if len(training) == 0 or len(testing) == 0:
            raise ValueError('empty fixed writer fold')
        w = weight[training]; target = y[training]; raw = x[training]
        positives = w@target
        if not 0 < positives < w.sum():
            raise ValueError('training fold has fewer than two weighted labels')
        center = (raw.T@w)/w.sum()
        scale = np.sqrt(np.einsum('ij,ij,i->j', raw-center, raw-center, w)/w.sum())
        scale[scale <= 1e-12] = 1.
        design = np.concatenate((np.ones((len(training), 1)), (raw-center)/scale), axis=1)
        penalty = np.eye(design.shape[1]); penalty[0, 0] = 0.
        def loss(b):
            linear = design@b
            return float(np.sum(w*(np.logaddexp(0., linear)-target*linear))+.5*b@penalty@b)
        def gradient(b):
            return (w*(expit(design@b)-target))@design+penalty@b
        def hessian(b):
            probability = expit(design@b)
            return np.einsum('ni,nj,n->ij', design, design, w*probability*(1-probability))+penalty
        initial = np.zeros(design.shape[1]); initial[0] = np.log(positives/(w.sum()-positives))
        fit = minimize(loss, initial, jac=gradient, hess=hessian, method='trust-exact',
                       options={'gtol': 1e-8, 'maxiter': 100})
        if np.max(np.abs(gradient(fit.x))) > 1e-6:
            raise ValueError('independent ridge gradient certificate not met')
        test_design = np.concatenate((np.ones((len(testing), 1)), (x[testing]-center)/scale), axis=1)
        prediction[testing] = expit(test_design@fit.x)
    p = np.flatnonzero(y==1); n = np.flatnonzero(y==0)
    if weight[p].sum() <= 0 or weight[n].sum() <= 0:
        raise ValueError('test AUC has fewer than two weighted labels')
    # Independent pair definition via binary searches in the negative class,
    # rather than the production joint-class rank-group reduction.
    negative_order = n[np.argsort(prediction[n], kind='stable')]
    negative_scores = prediction[negative_order]
    cumulative = np.r_[0., np.cumsum(weight[negative_order])]
    below = np.searchsorted(negative_scores, prediction[p], side='left')
    through = np.searchsorted(negative_scores, prediction[p], side='right')
    numerator = float(weight[p]@(cumulative[below]+.5*(cumulative[through]-cumulative[below])))
    area = numerator/(weight[p].sum()*weight[n].sum())
    effects = []
    for j in secondary_indices:
        effects.append(float(sum(x[i, j]*weight[i] for i in p)/sum(weight[p])-
                             sum(x[i, j]*weight[i] for i in n)/sum(weight[n])))
    return [float(area), *effects]


def interval_and_se(values):
    """Independent scalar order-statistic interpolation and sum-of-squares SE."""
    rows = list(map(float, values)); ordered = sorted(rows); n = len(rows)
    def percentile(p):
        location = p*(n-1); low = int(location); fraction = location-low
        return ordered[low]*(1-fraction)+ordered[min(low+1, n-1)]*fraction
    mean = sum(rows)/n
    se = (sum((r-mean)**2 for r in rows)/(n-1))**.5
    return [percentile(.025), percentile(.975)], se
