"""IN9 reference optimizer repair: unchanged trust-exact with centered restarts.

The original v1 solve runs first, with its exact options and certificate.
Only an uncertified finite candidate receives at most two recentered solves.
No production optimizer, AUC routine, source rows or bootstrap results are used.
"""
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit

GTOL = 1e-8
CERTIFICATE = 1e-6
MAXITER = 100
MAX_RECENTERS = 2


def relative_loss(design, target, weight, penalty, anchor, displacement):
    """Exactly L(anchor+displacement)-L(anchor), without a large baseline.

    log(1+p*(exp(d)-1)) is the softplus difference. Near d=0, expm1
    and log1p retain the decrement discarded by subtracting two full losses.
    Outside that neighborhood direct stable softplus subtraction avoids exp
    overflow. The linear label and ridge cross terms are unchanged.
    """
    linear = design @ anchor
    delta = design @ displacement
    change = np.empty_like(delta)
    near = np.abs(delta) <= .5
    change[near] = np.log1p(expit(linear[near])*np.expm1(delta[near]))
    change[~near] = np.logaddexp(0., linear[~near]+delta[~near])-np.logaddexp(0., linear[~near])
    return float(np.sum(weight*(change-target*delta)) + anchor@penalty@displacement
                 + .5*displacement@penalty@displacement)


def fit_weighted(design, target, weight, diagnostics=None):
    """Retain the independent optimizer and the absolute 1e-6 certificate."""
    positives = weight@target
    if not 0 < positives < weight.sum():
        raise ValueError('training fold has fewer than two weighted labels')
    penalty = np.eye(design.shape[1]); penalty[0, 0] = 0.
    def loss(b):
        linear = design@b
        return float(np.sum(weight*(np.logaddexp(0., linear)-target*linear))+.5*b@penalty@b)
    def gradient(b):
        return (weight*(expit(design@b)-target))@design+penalty@b
    def hessian(b):
        probability = expit(design@b)
        return np.einsum('ni,nj,n->ij', design, design, weight*probability*(1-probability))+penalty
    initial = np.zeros(design.shape[1]); initial[0] = np.log(positives/(weight.sum()-positives))
    fit = minimize(loss, initial, jac=gradient, hess=hessian, method='trust-exact',
                   options={'gtol': GTOL, 'maxiter': MAXITER})
    candidate = fit.x
    for stage in range(MAX_RECENTERS+1):
        gap = float(np.max(np.abs(gradient(candidate))))
        finite = bool(np.isfinite(candidate).all() and np.isfinite(gap))
        if diagnostics is not None:
            diagnostics.append({'stage': stage, 'status': int(fit.status),
                'iterations': int(fit.nit), 'gradient_inf': gap if np.isfinite(gap) else None,
                'certified': bool(finite and gap <= CERTIFICATE)})
        if finite and gap <= CERTIFICATE:
            return candidate
        if not finite or stage == MAX_RECENTERS:
            raise ValueError('independent ridge gradient certificate not met')
        anchor = candidate.copy()
        fit = minimize(lambda d: relative_loss(design, target, weight, penalty, anchor, d),
            np.zeros_like(anchor), jac=lambda d: gradient(anchor+d),
            hess=lambda d: hessian(anchor+d), method='trust-exact',
            options={'gtol': GTOL, 'maxiter': MAXITER})
        candidate = anchor+fit.x


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
        beta = fit_weighted(design, target, w)
        test_design = np.concatenate((np.ones((len(testing), 1)), (x[testing]-center)/scale), axis=1)
        prediction[testing] = expit(test_design@beta)
    p = np.flatnonzero(y==1); n = np.flatnonzero(y==0)
    if weight[p].sum() <= 0 or weight[n].sum() <= 0:
        raise ValueError('test AUC has fewer than two weighted labels')
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
    """Unchanged independent scalar interpolation and sum-of-squares SE."""
    rows = list(map(float, values)); ordered = sorted(rows); n = len(rows)
    def percentile(p):
        location = p*(n-1); low = int(location); fraction = location-low
        return ordered[low]*(1-fraction)+ordered[min(low+1, n-1)]*fraction
    mean = sum(rows)/n
    se = (sum((r-mean)**2 for r in rows)/(n-1))**.5
    return [percentile(.025), percentile(.975)], se
