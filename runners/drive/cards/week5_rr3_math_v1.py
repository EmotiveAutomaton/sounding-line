"""RR3's new strictly lagged error and absolute-coefficient formulas.

DESIGN CHECK: the grouped logistic estimator is the unchanged qualified MD3
primitive. The new feature and contrast have separately implemented references.
"""
import numpy as np
from . import week5_md3_bounded as fitted


def recent(plays):
    p = np.asarray(plays, float)
    if p.ndim != 3 or p.shape[1:] != (30, 15):
        raise ValueError('Thirty-trial qualified numeric plays required')
    if not np.isin(p[:, :, 6], [0, 1]).all() or not np.isfinite(p[:, :, [2, 3, 4, 7]]).all():
        raise ValueError('Choice, offered values and actual outcomes must be valid')
    expected = np.where(p[:, :, 6] == 1, (p[:, :, 3]+p[:, :, 4])/2, p[:, :, 2])
    errors = p[:, :, 7]-expected
    cumulative = np.column_stack((np.zeros(len(p)), np.cumsum(errors, axis=1)))
    value = np.full((len(p), 30), np.nan)
    for trial in range(1, 30):
        start = max(0, trial-3)
        value[:, trial] = (cumulative[:, trial]-cumulative[:, start])/(trial-start)
    return value


def reference_recent(plays):
    p = np.asarray(plays, float)
    value = np.full((len(p), 30), np.nan)
    for person, play in enumerate(p):
        previous = []
        for trial, row in enumerate(play):
            if previous:
                value[person, trial] = sum(previous[-3:])/len(previous[-3:])
            expectation = (float(row[3])+float(row[4]))*.5 if row[6] else float(row[2])
            previous.append(float(row[7])-expectation)
    return value


def contrast(beta):
    beta = np.asarray(beta, float)
    if beta.shape != (9,) or not np.isfinite(beta).all():
        raise ValueError('All nine finite logistic coefficients required')
    return [float(beta[8]), float(beta[3]), float(beta[4]),
            float(abs(beta[8])-max(abs(beta[3]), abs(beta[4])))]


def reference_contrast(beta):
    coefficients = list(map(float, beta))
    a, below, above = coefficients[8], coefficients[3], coefficients[4]
    magnitude = lambda x: x if x >= 0 else -x
    distance = sorted([magnitude(below), magnitude(above)])[-1]
    return [a, below, above, magnitude(a)-distance]


def evaluate(x, y, people, weights=None, independent=False):
    fit = fitted.grouped_logit(x, y, people, weights)
    if fit['status'] != 'ok':
        return {'failure': fit['status'], 'informative_participants': fit['informative_participants']}
    values = reference_contrast(fit['beta']) if independent else contrast(fit['beta'])
    return {'value': values, 'informative_participants': fit['informative_participants'],
            'gradient': fit['gradient']}


def interval_and_se(values, independent=False):
    if not independent:
        x = np.asarray(values, float)
        return np.quantile(x, [.025, .975]).tolist(), float(x.std(ddof=1))
    ordered = sorted(map(float, values)); n = len(ordered)
    answer = []
    for q in (.025, .975):
        location = (n-1)*q; left = int(location); fraction = location-left
        answer.append(ordered[left]*(1-fraction)+ordered[min(left+1, n-1)]*fraction)
    mean = sum(ordered)/n
    return answer, (sum((v-mean)**2 for v in ordered)/(n-1))**.5


def correlation(x, y, independent=False):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 2 or np.std(x) == 0 or np.std(y) == 0:
        return None
    if not independent:
        return float(np.corrcoef(x, y)[0, 1])
    a = x-sum(x)/len(x); b = y-sum(y)/len(y)
    return float(sum(a*b)/(sum(a*a)*sum(b*b))**.5)
