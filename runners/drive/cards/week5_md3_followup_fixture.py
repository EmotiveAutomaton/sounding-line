"""Fixed native proof worlds for the three prospective MD3 descendants.

DESIGN CHECK: exact enumerated conditional likelihood, derivative and curvature
certificates, original-IRLS parity, dynamic-history regeneration and signed/null
full handlers precede any source admission. This module is built, not executed.
"""
from itertools import combinations
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
from scipy.special import expit, logsumexp
from . import week5_md3_followup as study
from . import week5_md3_conditional as conditional
from .week5_md_analysis_fixture import constructed

CASES = {
    'MD3.s': ('positive', 'negative', 'null'),
    'MD3.m': ('positive', 'negative', 'smooth-positive', 'smooth-negative',
              'positive-curved', 'negative-curved'),
    'MD3.p': ('positive', 'negative', 'null'),
}


def enumerated_objective(beta, x, y, weights):
    loss = 0.
    gradient = np.zeros(len(beta))
    hessian = np.zeros((len(beta), len(beta)))
    for design, response, weight in zip(x, y, weights):
        count = int(response.sum())
        if not weight or count == 0 or count == len(response):
            continue
        sums = np.asarray([design[list(indices)].sum(axis=0)
                           for indices in combinations(range(len(response)), count)])
        logits = sums @ beta
        normalizer = logsumexp(logits)
        probability = np.exp(logits - normalizer)
        mean = probability @ sums
        delta = sums - mean
        observed = response @ design
        loss += weight * (normalizer - observed @ beta)
        gradient += weight * (mean - observed)
        hessian += weight * (delta.T @ (probability[:, None] * delta))
    return loss, gradient, hessian


def arithmetic():
    rng = np.random.default_rng(92314)
    x = rng.normal(size=(7, 6, 3))
    y = np.asarray([[float(t < count) for t in range(6)] for count in range(7)])
    weight = np.arange(7) % 3 + 1.
    beta = np.asarray([.5, -.2, .4])
    actual = conditional.objective(beta, x, y, weight)
    expected = enumerated_objective(beta, x, y, weight)
    for a, b in zip(actual[:3], expected):
        if not np.allclose(a, b, rtol=0, atol=1e-10):
            raise ValueError('Conditional enumeration differs')
    gradient = np.empty(3)
    hessian = np.empty((3, 3))
    epsilon = 1e-5
    for column in range(3):
        step = np.eye(3)[column] * epsilon
        plus = conditional.objective(beta + step, x, y, weight)
        minus = conditional.objective(beta - step, x, y, weight)
        gradient[column] = (plus[0] - minus[0]) / (2 * epsilon)
        hessian[:, column] = (plus[1] - minus[1]) / (2 * epsilon)
    if not np.allclose(gradient, actual[1], atol=1e-7, rtol=0) or not np.allclose(hessian, actual[2], atol=1e-7, rtol=0):
        raise ValueError('Conditional finite derivatives differ')
    # Repeat complete clusters exactly; no observation-level bootstrap shortcut.
    rows = np.repeat(np.arange(len(x)), weight.astype(int))
    repeated = conditional.objective(beta, x[rows], y[rows])
    if any(not np.allclose(a, b, atol=1e-10, rtol=0) for a, b in zip(actual[:3], repeated[:3])):
        raise ValueError('Whole-cluster multiplicities differ')
    panel = rng.normal(size=(160, 8, 3))
    coefficients = np.asarray([1., -.8, .5])
    response = (rng.random((160, 8)) < expit(panel @ coefficients)).astype(float)
    fitted = conditional.fit(panel, response)
    if np.sign(fitted['beta']).tolist() != np.sign(coefficients).tolist() or fitted['gradient'] >= 1e-6:
        raise ValueError('Signed conditional exogenous recovery failed')
    original = study.original.logistic_fixed(panel, response)
    bounded = study.fixed_fit(panel, response)
    if not np.array_equal(original['beta'], bounded['beta']) or not np.array_equal(original['alpha'], bounded['alpha'], equal_nan=True):
        raise ValueError('Parent fixed-intercept arithmetic changed')
    # Pair every pattern with its complement: exact exogenous zero coefficients.
    doubled = np.concatenate([panel, panel])
    complement = np.concatenate([response, 1 - response])
    null = conditional.fit(doubled, complement)
    if not np.allclose(null['beta'], 0, atol=1e-12, rtol=0):
        raise ValueError('Exact conditional null did not remain zero')
    plays = constructed(n=48)
    raw = study.original.dynamic_features(plays, .65)
    scale = raw.reshape(-1, 8).std(axis=0, ddof=1).clip(1e-10)
    scale[3:5] = np.std(raw[:, :, 3] + raw[:, :, 4], ddof=1)
    parent_fit = study.fixed_fit(raw / scale, plays[:, :, 6])
    for namespace in (33, 34):
        seed = np.random.SeedSequence([study.SEED, 0, namespace])
        left = study.trajectory(plays, .65, parent_fit, scale, seed, zero_standing=True)
        right = study.original.null_trajectory(plays, .65, parent_fit, scale, seed)
        if not np.array_equal(left, right, equal_nan=True):
            raise ValueError('Complete parent dynamic null differs')
        # Reconstruct standing and gamble history independently from saved choices.
        rebuilt = study.features(left, .65, scale)
        prior_score = np.c_[np.zeros(len(left)), np.cumsum(left[:, :-1, 7], axis=1)]
        prior_count = np.c_[np.zeros(len(left)), np.cumsum(left[:, :-1, 6], axis=1)]
        if not np.allclose(rebuilt[:, :, 3] + rebuilt[:, :, 4], prior_score / scale[3], rtol=0, atol=1e-12):
            raise ValueError('Dynamic score history not regenerated')
        if not np.allclose(rebuilt[:, :, 5], prior_count / scale[5], rtol=0, atol=1e-12):
            raise ValueError('Dynamic choice history not regenerated')
    curved = study.features(plays, .65, scale, True)
    if not np.array_equal(curved[:, :, :8], raw / scale):
        raise ValueError('Quadratic addition changed inherited predictors')
    for lower, upper, curvature in ((1.2, -.6, .1), (.1, .1, -.2)):
        def function(value):
            return lower * min(value, 0) + upper * max(value, 0) + curvature * value ** 2
        step = 1e-7
        left = (function(0) - function(-step)) / step
        right = (function(step) - function(0)) / step
        if abs((left - right) - (lower - upper)) > 1e-6:
            raise ValueError('Curvature/kink derivative identity failed')
    try:
        conditional.fit(np.repeat(panel[:, :, :1], 2, axis=2), response)
    except ValueError as error:
        if 'rank deficient' not in str(error):
            raise
    else:
        raise ValueError('Conditional duplicate predictor did not refuse')
    return dict(verified=True, exact_enumeration=True, finite_derivatives=True,
                cluster_weights_exact=True, signed_exogenous_recovery=True,
                exact_null=True, parent_fixed_intercept_parity=True,
                full_dynamic_parent_parity=True, curvature_derivative=True,
                rank_failure_reachable=True)


def world(card, case, n=96):
    if case not in CASES[card]:
        raise ValueError('Unregistered constructed case')
    plays = constructed(n=n)
    raw = study.original.dynamic_features(plays, .65)
    scale = raw.reshape(-1, 8).std(axis=0, ddof=1).clip(1e-10)
    scale[3:5] = np.std(raw[:, :, 3] + raw[:, :, 4], ddof=1)
    beta = np.asarray([.25, -.25, .15, 0., 0., -.25, .20, .1])
    curvature = 0.
    if case.startswith('positive'):
        beta[3:5] = [1.2, -.6]
    elif case.startswith('negative'):
        beta[3:5] = [-1.2, .6]
    elif case.startswith('smooth'):
        beta[3:5] = [.1, .1]
        curvature = .15 if case == 'smooth-positive' else -.15
    if case.endswith('curved'):
        curvature = .15 if case.startswith('positive') else -.15
    if card == 'MD3.m':
        beta = np.r_[beta, curvature]
    alpha = np.random.default_rng(8831).normal(0, .3, n)
    data = study.trajectory(plays, .65, dict(alpha=alpha, beta=beta), scale,
                            np.random.SeedSequence([study.SEED, 733]), curved=card == 'MD3.m')
    # Source scale is defined before the constructed trajectory, never tuned to
    # the fitted or recovered contrast. The same value binds all replay stages.
    expected = 'supports' if case.startswith('positive') else 'against' if case.startswith('negative') else 'inconclusive'
    return data, dict(standing_sd=float(scale[3]), gamma=.65), expected


def prepare(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    for card, cases in CASES.items():
        for case in cases:
            data, parent, expected = world(card, case)
            path = output / (card + '-' + case + '.npz')
            np.savez_compressed(path, first=data)
            study.core.save_json(path.with_suffix('.json'),
                dict(constructed_only=True, card=card, case=case, expected=expected,
                     parent_primary=parent, source_sha256=study.core.sha(path), participants=len(data)))


def execute(output, inputs, config):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    if set(inputs) != {'task', 'manifest'} or set(config) - {'phase', 'case', 'max_wall_seconds', 'max_new_draws', 'draws'}:
        raise ValueError('Exact constructed fixture inputs required')
    manifest = study.read(inputs['manifest'])
    card, case = config['phase'], config['case']
    if manifest.get('constructed_only') is not True or manifest['card'] != card or manifest['case'] != case or case not in CASES[card]:
        raise ValueError('Constructed case scope differs')
    if manifest['source_sha256'] != study.core.sha(inputs['task']):
        raise ValueError('Constructed task changed')
    proof = output / 'ARITHMETIC.json'
    if not proof.exists():
        study.core.save_json(proof, arithmetic())
    with np.load(inputs['task'], allow_pickle=False) as arrays:
        data = arrays['first']
    value = study.perform(output, data, manifest['parent_primary'], card, config,
                          dict(constructed_manifest_sha256=study.core.sha(inputs['manifest']),
                               task_sha256=study.core.sha(inputs['task'])), constructed=True)
    if value.get('status') != 'yielded':
        if value.get('status') != 'complete' or any(cell.get('status') != 'ok' for cell in value['cells']):
            raise ValueError('Complete known-world numerical fit failed')
        for cell in value['cells']:
            if cell['outcome'] != 'below floor, descriptive':
                raise ValueError('Constructed small fixture improperly bypassed source floor')
            if cell['diagnostic_direction'] != manifest['expected']:
                raise ValueError('Full calibrated signed/null fixture decision differs')
    return value


def verify(output, inputs, config):
    output = Path(output)
    value = execute(output / 'independent-replay', inputs, config)
    if value.get('status') == 'yielded':
        return value | dict(verified=False)
    study.compare_complete(output)
    if study.read(output / 'ARITHMETIC.json') != study.read(output / 'independent-replay/ARITHMETIC.json'):
        raise ValueError('Arithmetic fixture replay changed')
    return dict(verified=True, full_signed_or_null_case=True,
                all_2000_draws_and_20_nulls_independently_replayed=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    prepare(parser.parse_args().output)
