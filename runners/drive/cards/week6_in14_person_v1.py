"""Unqualified covariance-aware person candidate; constructed admission first.

DESIGN CHECK: IN14_PERSON_CALIBRATION_V1.md; no human handler calls this module
until the frozen dependence calibration and complete replay integration pass.
"""
import numpy as np
from .week6_in14_math_v1 import FEELINGS, TERMS


def _fit(x, y, independent=False):
    if np.linalg.matrix_rank(x, tol=1e-10) != x.shape[1]:
        raise ValueError('rank deficient person fit')
    inverse = np.linalg.pinv(x, rcond=1e-11) if independent else np.linalg.solve(x.T @ x, x.T)
    beta = inverse @ y
    return beta, y - x @ beta, inverse


def prepare(frame, independent=False):
    people = []
    if frame.empty:
        return people
    for writer, part in frame.loc[frame.gap_minutes < 10].groupby('prolific_id', sort=True):
        part = part.copy()
        part['_feeling'] = part.feeling.map(dict(zip(FEELINGS, range(11))))
        part = part.sort_values(['raw_pair_ordinal', '_feeling'])
        ordinals = part.raw_pair_ordinal.drop_duplicates().to_numpy(int)
        if len(ordinals) < 4:
            continue
        record = {'writer': writer, 'pairs': len(ordinals), 'ordinals': ordinals, 'failure': None}
        try:
            if len(part) != 11 * len(ordinals) or part.groupby('raw_pair_ordinal')._feeling.nunique().ne(11).any():
                raise ValueError('eleven unique feelings required per pair')
            x = np.column_stack([np.ones(len(part)), part[list(TERMS)].to_numpy(float)])
            y = part.outcome.to_numpy(float)
            if not np.isfinite(x).all() or not np.isfinite(y).all():
                raise ValueError('nonfinite person observations')
            beta, residual, inverse = _fit(x, y, independent)
            cut = 11 * (len(ordinals) // 2)
            coefficients = [beta[2]]; maps = [inverse[2]]
            for sl in (slice(0, cut), slice(cut, len(y))):
                b, _, inv = _fit(x[sl], y[sl], independent)
                embedded = np.zeros(len(y)); embedded[sl] = inv[2]
                coefficients.append(b[2]); maps.append(embedded)
            inventory = part.N.dropna().unique()
            if len(inventory) > 1:
                raise ValueError('conflicting inventory composite')
            record.update(x=x, residual=residual.reshape(-1, 11), inverse=inverse,
                          coefficients=np.asarray(coefficients), maps=np.asarray(maps),
                          N=float(inventory[0]) if len(inventory) else np.nan)
        except (ValueError, np.linalg.LinAlgError) as error:
            record['failure'] = str(error)
        people.append(record)
    return people


def nuisance(people, counts):
    cross = np.zeros((11, 11)); numerator = denominator = 0.0
    for record in people:
        weight = counts.get(record['writer'], 0)
        if not weight:
            continue
        if record['failure']:
            raise ValueError(record['failure'])
        r = record['residual']; use = np.diff(record['ordinals']) == 1
        cross += weight * (r.T @ r)
        numerator += weight * np.sum(r[:-1][use] * r[1:][use])
        denominator += weight * np.sum(r[:-1][use] ** 2)
    if denominator <= 0 or np.any(np.diag(cross) <= 0):
        raise ValueError('unsupported pooled residual dependence')
    raw = float(numerator / denominator)
    scale = np.sqrt(np.diag(cross))
    return {'phi_raw': raw, 'phi': float(np.clip(raw, -.95, .95)),
            'phi_truncated': abs(raw) > .95, 'feeling_correlation': cross / np.outer(scale, scale)}


def covariance(record, noise, independent=False):
    x = record['x']; n = len(x); c = noise['feeling_correlation']
    d = np.abs(record['ordinals'][:, None] - record['ordinals'][None, :])
    temporal = noise['phi'] ** d
    if independent:
        correlation = np.kron(temporal, c)
        projection = x @ np.linalg.pinv(x, rcond=1e-11)
        degrees = np.trace((np.eye(n) - projection) @ correlation)
        joint = record['maps'] @ correlation @ record['maps'].T
    else:
        # R times X without constructing R, preserving actual pair distances.
        rx = np.einsum('ab,ij,bjk->aik', temporal, c, x.reshape(-1, 11, 5), optimize=True).reshape(n, 5)
        degrees = n - np.trace(record['inverse'] @ rx)
        maps = record['maps'].reshape(3, -1, 11)
        joint = np.einsum('kai,ab,ij,lbj->kl', maps, temporal, c, maps, optimize=True)
    if degrees <= 0:
        raise ValueError('nonpositive projected residual degrees of freedom')
    sigma2 = np.sum(record['residual'] ** 2) / degrees
    return sigma2 * joint


def corrected_moments(observed, sampling, raw_trait=None):
    observed = np.asarray(observed, float); sampling = np.asarray(sampling, float)
    true = observed - sampling
    answer = {'observed_covariance': observed.tolist(), 'mean_sampling_covariance': sampling.tolist(),
              'corrected_covariance': true.tolist(), 'full_reliability': None,
              'half_diagnostic': None, 'adjusted_trait_relation': None, 'status': 'ok'}
    if not np.isfinite(true).all() or np.any(np.diag(observed) <= 0) or np.any(np.diag(true) <= 0):
        return {**answer, 'status': 'nonpositive_variance', 'reason': 'observed and corrected variances must be positive'}
    reliability = true[0, 0] / observed[0, 0]
    answer.update(full_reliability=float(reliability),
                  half_diagnostic=float(true[1, 2] / np.sqrt(true[1, 1] * true[2, 2])))
    if raw_trait is not None:
        answer['adjusted_trait_relation'] = float(raw_trait / np.sqrt(reliability))
    return answer


def _moments(values, weights):
    mean = np.average(values, axis=0, weights=weights)
    centered = values - mean
    return (centered.T * weights) @ centered / (weights.sum() - 1)


def evaluate(people, counts=None, independent=False):
    counts = dict.fromkeys([p['writer'] for p in people], 1) if counts is None else counts
    selected = [p for p in people if counts.get(p['writer'], 0) > 0]
    if len(selected) < 2:
        return {'status': 'unsupported', 'reason': 'fewer than two independent writers'}
    if any(p['failure'] for p in selected):
        return {'status': 'unsupported', 'reason': 'person fit failure',
                'failed_writers': [p['writer'] for p in selected if p['failure']]}
    try:
        noise = nuisance(selected, counts)
        sampling = np.asarray([covariance(p, noise, independent) for p in selected])
        values = np.asarray([p['coefficients'] for p in selected])
        weights = np.asarray([counts[p['writer']] for p in selected], float)
        answer = corrected_moments(_moments(values, weights), np.average(sampling, axis=0, weights=weights))
        n = np.asarray([p['N'] for p in selected]); use = np.isfinite(n)
        answer.update(writers=len(selected), inventory_writers=int(use.sum()),
                      noise={k: v.tolist() if isinstance(v, np.ndarray) else v for k, v in noise.items()})
        if use.sum() >= 2:
            joint = _moments(np.column_stack([values[use, 0], n[use]]), weights[use])
            raw = joint[0, 1] / np.sqrt(joint[0, 0] * joint[1, 1]) if np.all(np.diag(joint) > 0) else None
            trait = corrected_moments(_moments(values[use], weights[use]),
                                      np.average(sampling[use], axis=0, weights=weights[use]), raw)
            answer['trait'] = {'status': trait['status'], 'raw_correlation': None if raw is None else float(raw),
                              'coefficient_reliability': trait['full_reliability'],
                              'adjusted_relation': trait['adjusted_trait_relation']}
        else:
            answer['trait'] = {'status': 'unsupported', 'adjusted_relation': None}
        return answer
    except (ValueError, np.linalg.LinAlgError) as error:
        return {'status': 'unsupported', 'reason': str(error)}
