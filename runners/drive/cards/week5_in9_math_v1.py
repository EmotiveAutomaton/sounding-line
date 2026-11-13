"""Frozen IN9 ridge-logistic formulas; no source IO or scientific admission."""
import hashlib
import numpy as np
from scipy.special import expit

SEED = 20261113
RIDGE = 1.0
FOLDS = 5


def fold_codes(writers):
    keys, code = np.unique(np.asarray(writers, str), return_inverse=True)
    ordered = sorted(range(len(keys)), key=lambda i: hashlib.sha256(
        (str(SEED)+'|IN9|'+keys[i]).encode()).hexdigest())
    assignment = np.empty(len(keys), int)
    assignment[ordered] = np.arange(len(keys)) % FOLDS
    return assignment[code], code, keys


def ridge_fit(x, y, weight):
    """Sum weighted Bernoulli loss plus ||slopes||^2/2; intercept unpenalized."""
    x, y, weight = np.asarray(x, float), np.asarray(y, float), np.asarray(weight, float)
    positive = float(weight@y); total = float(weight.sum())
    if not 0 < positive < total:
        raise ValueError('training fold has fewer than two weighted labels')
    beta = np.zeros(x.shape[1]); beta[0] = np.log(positive/(total-positive))
    penalty = np.r_[0., np.full(x.shape[1]-1, RIDGE)]
    objective = lambda b: float(weight@(np.logaddexp(0, x@b)-y*(x@b)) + .5*np.sum(penalty*b*b))
    for _ in range(80):
        prob = expit(x@beta)
        gradient = x.T@(weight*(prob-y))+penalty*beta
        if np.max(np.abs(gradient)) <= 1e-8:
            return beta
        hessian = (x.T*(weight*prob*(1-prob)))@x+np.diag(penalty)
        step = np.linalg.solve(hessian, gradient)
        before = objective(beta); alpha = 1.
        while alpha > 2**-30:
            candidate = beta-alpha*step
            if objective(candidate) <= before+1e-12:
                beta = candidate; break
            alpha *= .5
        else:
            raise ValueError('ridge Newton line search failed')
    raise ValueError('ridge gradient certificate not met')


def auc(y, scores, weight):
    """Weighted positive-negative pair probability; exact ties receive half."""
    y, scores, weight = np.asarray(y), np.asarray(scores), np.asarray(weight, float)
    positive = float(weight[y==1].sum()); negative = float(weight[y==0].sum())
    if not positive > 0 or not negative > 0:
        raise ValueError('test AUC has fewer than two weighted labels')
    order = np.argsort(scores, kind='stable'); score = scores[order]
    yy, ww = y[order], weight[order]
    starts = np.flatnonzero(np.r_[True, score[1:] != score[:-1]])
    p = np.add.reduceat(ww*yy, starts)
    n = np.add.reduceat(ww*(1-yy), starts)
    lower = np.cumsum(n)-n
    return float(p@(lower+.5*n)/(positive*negative))


def oof(x, y, folds, weight):
    x, y, weight = np.asarray(x, float), np.asarray(y, float), np.asarray(weight, float)
    scores = np.empty(len(y))
    for fold in range(FOLDS):
        train = (folds != fold) & (weight > 0); test = folds == fold
        if not test.any() or not train.any():
            raise ValueError('empty fixed writer fold')
        w = weight[train]; mean = np.average(x[train], axis=0, weights=w)
        sd = np.sqrt(np.average((x[train]-mean)**2, axis=0, weights=w))
        sd = np.where(sd > 1e-12, sd, 1.)
        z = np.column_stack((np.ones(train.sum()), (x[train]-mean)/sd))
        beta = ridge_fit(z, y[train], w)
        scores[test] = expit(np.column_stack((np.ones(test.sum()), (x[test]-mean)/sd))@beta)
    return scores


def draw_weights(writer_code, draw):
    n = int(writer_code.max())+1
    rng = np.random.default_rng(np.random.SeedSequence([SEED, 9, draw]))
    return np.bincount(rng.integers(0, n, n), minlength=n)[writer_code]


def evaluate(x, y, folds, weight, secondary_indices):
    scores = oof(x, y, folds, weight)
    effects = [float(np.average(x[y==1, j], weights=weight[y==1])-
                     np.average(x[y==0, j], weights=weight[y==0])) for j in secondary_indices]
    return [auc(y, scores, weight), *effects]
