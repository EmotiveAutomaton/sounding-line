"""Fit conditional action models on training-only projected inputs and targets.

DESIGN CHECK: M01/X01/X03/X11; LESSONS 3--5. NULL: target-independent
features cannot yield systematic independent gain; incomplete targets and failed
optimization do not become valid parameters. ALTERNATIVE: a planted context/action
association is learned on a finite fixture with its gradient checked independently.
Each declared independent unit receives equal total weight. Private unit IDs and
target records remain evaluator-side; only numerical feature weights enter readers.
"""
from collections import Counter
import math

import numpy as np
from scipy.optimize import minimize
from scipy.sparse import csr_matrix
from scipy.special import logsumexp

from runners.stage9.artifact_view import validate
from runners.stage9.choice_features import action_features
from runners.stage9.common import digest


def design(records, individual=False):
    if not records:
        raise ValueError('empty conditional-choice training data')
    groups = Counter(row['unit'] for row in records)
    rows, starts, targets, sample_weights, columns = [], [0], [], [], set()
    for record in records:
        if set(record) != {'unit', 'evidence', 'target'} or not isinstance(record['unit'], str) or not record['unit']:
            raise ValueError('invalid training record boundary')
        evidence = validate(record['evidence'])
        support = evidence['support']
        if record['target'] not in support:
            raise ValueError('training target outside visible query support')
        targets.append(starts[-1]+support.index(record['target']))
        for action in support:
            features = action_features(evidence, action, individual)
            rows.append(features)
            columns.update(features)
        starts.append(len(rows))
        sample_weights.append(1/(len(groups)*groups[record['unit']]))
    columns = sorted(columns)
    index = {key: i for i, key in enumerate(columns)}
    data, ix, offsets = [], [], [0]
    for row in rows:
        for key, value in sorted(row.items()):
            if value:
                data.append(value)
                ix.append(index[key])
        offsets.append(len(data))
    matrix = csr_matrix((np.array(data, dtype=float), np.array(ix, dtype=np.int32),
                         np.array(offsets, dtype=np.int32)), shape=(len(rows), len(columns)))
    return matrix, np.array(starts), np.array(targets), np.array(sample_weights), columns


def objective(weights, matrix, starts, targets, sample_weights, l2):
    if not math.isfinite(l2) or l2 < 0:
        raise ValueError('invalid regularization')
    logits = matrix @ weights
    residual = np.zeros_like(logits)
    loss = .5*l2*float(weights @ weights)
    for i, (start, end) in enumerate(zip(starts[:-1], starts[1:])):
        normalizer = logsumexp(logits[start:end])
        loss += sample_weights[i]*(normalizer-logits[targets[i]])
        residual[start:end] = sample_weights[i]*np.exp(logits[start:end]-normalizer)
        residual[targets[i]] -= sample_weights[i]
    gradient = np.asarray(matrix.T @ residual).ravel() + l2*weights
    if not math.isfinite(loss) or not np.isfinite(gradient).all():
        raise ValueError('nonfinite conditional-choice objective')
    return loss, gradient


def fit(records, *, individual=False, l2=.01, max_iterations=250, uniform_mixture=.01):
    if type(max_iterations) is not int or max_iterations < 1:
        raise ValueError('positive optimization budget required')
    if not 0 <= uniform_mixture < 1:
        raise ValueError('invalid forecast mixture')
    matrix, starts, targets, sample_weights, columns = design(records, individual)
    result = minimize(objective, np.zeros(len(columns)), args=(matrix, starts, targets, sample_weights, l2),
                      jac=True, method='L-BFGS-B', options={'maxiter': max_iterations, 'ftol': 1e-11, 'gtol': 1e-7})
    if not result.success or not np.isfinite(result.x).all():
        raise ValueError('conditional-choice optimization failed: '+str(result.message))
    parameters = {'version': 's9-conditional-choice-v1', 'individual': individual,
                  'uniform_mixture': uniform_mixture, 'weights': dict(zip(columns, result.x.tolist()))}
    receipt = {'method': 'equal-unit regularized conditional multinomial logistic regression',
               'records': len(records), 'units': len({r['unit'] for r in records}),
               'action_rows': matrix.shape[0], 'features': matrix.shape[1], 'l2': l2,
               'optimizer_iterations': int(result.nit), 'objective': float(result.fun),
               'max_abs_gradient': float(np.max(np.abs(result.jac))),
               'converged': bool(result.success), 'message': str(result.message),
               'training_records_sha256': digest(records), 'parameters_sha256': digest(parameters)}
    return parameters, receipt
