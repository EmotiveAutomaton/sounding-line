"""Training-only fitting of executable mark-program libraries.

DESIGN CHECK: M01/M02/X01/X02/X11; LESSONS 3--5. NULL: held-out units,
empty cohorts and unsuccessful optimization cannot produce a library. ALTERNATIVE:
the analytic gradient matches numerical differences and a fitted planted policy
predicts through the actual portable executor. Equal independent-unit weights.

Cohort labels are constructor training metadata, never query evidence. Learned
coefficients remain approximations, not supplied true operative laws. Separating
training cohorts does not prove the corresponding factors identifiable at test.
"""
from collections import Counter, defaultdict
import copy
import math

import numpy as np
from scipy.optimize import minimize
from scipy.sparse import csr_matrix
from scipy.special import expit, logsumexp

from .artifact_view import TYPES, all_header_actions, type_counts, validate as validate_evidence
from .common import digest
from .mark_program import neutral_program, requirements, validate as validate_program

PROGRESS_KEYS = tuple(a+'>'+b for a in TYPES for b in TYPES)
STOP_KEYS = ('intercept', 'progress', 'deadline', 'self')
ACTION_DIM = len(TYPES)+len(PROGRESS_KEYS)+1


def encode(program):
    validate_program(program)
    return np.array([*[program['purpose'][t] for t in TYPES],
                     *[program['expertise']['progress'][t] for t in PROGRESS_KEYS], program['section_bias'],
                     *[program['stop'][t] for t in STOP_KEYS]], dtype=float)


def decode(weights, template):
    if len(weights) != ACTION_DIM+len(STOP_KEYS) or not np.isfinite(weights).all():
        raise ValueError('invalid fitted program vector')
    result = copy.deepcopy(template)
    result['purpose'] = dict(zip(TYPES, map(float, weights[:len(TYPES)])))
    result['expertise']['progress'] = dict(zip(PROGRESS_KEYS, map(float, weights[len(TYPES):ACTION_DIM-1])))
    result['section_bias'] = float(weights[ACTION_DIM-1])
    result['stop'] = dict(zip(STOP_KEYS, map(float, weights[ACTION_DIM:])))
    return validate_program(result)


def design(records, template):
    validate_program(template)
    if not records:
        raise ValueError('empty program training cohort')
    groups = Counter(r['unit'] for r in records)
    rows, offsets, starts, targets, stops, widths, weights = [], [], [0], [], [], [], []
    for record in records:
        if set(record) != {'unit', 'evidence', 'target'} or not isinstance(record['unit'], str) or not record['unit']:
            raise ValueError('invalid program training record')
        evidence = validate_evidence(record['evidence'])
        if record['target'] not in evidence['support']:
            raise ValueError('training target outside declared support')
        work = evidence['current']
        context = work['context']
        actions = all_header_actions(context)
        counts = type_counts(work)
        names = [s['name'] for s in context['sections']]
        fluency = template['expertise']['fluency']
        tools = {k: context['tools'][k] if template['context'][k] == 'follow' else template['context'][k] == 'available'
                 for k in context['tools']}
        deadline = context['deadline'] if template['context']['deadline'] == 'follow' else template['context']['deadline']
        active = []
        for aid in evidence['support'][1:]:
            action = actions[aid]
            kind = action['type']
            if kind not in template['available_types'] or any(not tools[t] for t in requirements(kind)):
                continue
            features = np.zeros(ACTION_DIM)
            features[TYPES.index(kind)] = 1/fluency
            for old in TYPES:
                features[len(TYPES)+PROGRESS_KEYS.index(old+'>'+kind)] = counts[old]/len(actions)/fluency
            features[-1] = (1-names.index(action['section'])/len(names))/fluency
            rows.append(features)
            offsets.append((-template['expertise']['cost'][kind]+template['history'][kind])/fluency)
            active.append(aid)
        target = record['target']
        # -1 is an explicit stop, -2 an offered action unavailable in this candidate.
        targets.append(-1 if target == 'stop' else starts[-1]+active.index(target) if target in active else -2)
        starts.append(len(rows))
        stops.append([1., len(work['marks'])/len(actions), float(deadline == 'tight'), float(context['audience'] == 'self')])
        widths.append(len(evidence['support']))
        weights.append(1/(len(groups)*groups[record['unit']]))
    matrix = csr_matrix(np.array(rows).reshape((-1, ACTION_DIM)))
    return {'matrix': matrix, 'offsets': np.array(offsets), 'starts': np.array(starts), 'targets': np.array(targets),
            'stops': np.array(stops), 'widths': np.array(widths), 'weights': np.array(weights),
            'noise': template['action_noise']}


def objective(coefficients, data, l2):
    if not math.isfinite(l2) or l2 < 0:
        raise ValueError('invalid program regularization')
    logits = data['matrix']@coefficients[:ACTION_DIM] + data['offsets']
    hazards = expit(data['stops']@coefficients[ACTION_DIM:])
    residual = np.zeros(len(logits))
    stop_residual = np.zeros(len(hazards))
    loss = .5*l2*float(coefficients@coefficients)
    eps = data['noise']
    for i, (start, end) in enumerate(zip(data['starts'][:-1], data['starts'][1:])):
        target = data['targets'][i]
        hazard = hazards[i] if start != end else 1.
        categorical = np.exp(logits[start:end]-logsumexp(logits[start:end])) if start != end else np.array([])
        raw = hazard if target == -1 else (1-hazard)*categorical[target-start] if target >= 0 else 0.
        probability = eps/data['widths'][i] + (1-eps)*raw
        if probability <= 0:
            raise ValueError('training evidence impossible under declared candidate support/noise')
        weight = data['weights'][i]
        loss -= weight*math.log(probability)
        influence = weight*(1-eps)*raw/probability
        if start != end and target == -1:
            stop_residual[i] = -influence*(1-hazard)
        elif target >= 0:
            residual[start:end] += influence*categorical
            residual[target] -= influence
            stop_residual[i] = influence*hazard
    gradient = np.concatenate([np.asarray(data['matrix'].T@residual).ravel(), data['stops'].T@stop_residual])
    gradient += l2*coefficients
    if not math.isfinite(loss) or not np.isfinite(gradient).all():
        raise ValueError('nonfinite program training objective')
    return loss, gradient


def fit(records, *, template=None, l2=.01, max_iterations=300):
    if type(max_iterations) is not int or max_iterations < 1:
        raise ValueError('invalid program optimizer budget')
    template = copy.deepcopy(template or neutral_program())
    data = design(records, template)
    result = minimize(objective, encode(template), args=(data, l2), method='L-BFGS-B', jac=True,
                      options={'maxiter': max_iterations, 'ftol': 1e-11, 'gtol': 1e-7})
    if not result.success or not np.isfinite(result.x).all():
        raise ValueError('program optimization failed: '+str(result.message))
    program = decode(result.x, template)
    return program, {'training_records_sha256': digest(records), 'program_sha256': digest(program),
                     'records': len(records), 'units': len({r['unit'] for r in records}),
                     'l2': l2, 'iterations': int(result.nit), 'converged': bool(result.success),
                     'objective': float(result.fun), 'max_abs_gradient': float(np.max(np.abs(result.jac))),
                     'model': 'equal-unit likelihood of actual noisy portable policy; fixed remaining template parameters'}


def fit_library(records, training_units, *, minimum_units=8, l2=.01, max_iterations=300):
    """Fit declared training cohorts; return anonymous model keys and private audit.

    Each record adds maker_group and purpose_group to the ordinary training fields.
    These name factor cohorts, never individual identities. The caller verifies the
    source allocation before supplying training_units. Missing cohorts are failures,
    not generated evidence or replacements selected from held-out outcomes.
    """
    if not training_units or type(minimum_units) is not int or minimum_units < 2:
        raise ValueError('explicit training allocation and minimum cohort size required')
    cohorts = defaultdict(list)
    for record in records:
        if set(record) != {'unit', 'evidence', 'target', 'maker_group', 'purpose_group'}:
            raise ValueError('invalid library training record')
        if record['unit'] not in training_units:
            raise ValueError('library record outside permitted training allocation')
        if any(not isinstance(record[k], str) or not record[k] for k in ('maker_group', 'purpose_group')):
            raise ValueError('invalid training cohort label')
        cohorts[(record['maker_group'], record['purpose_group'])].append(
            {k: record[k] for k in ('unit', 'evidence', 'target')})
    if not cohorts or len(cohorts) > 64:
        raise ValueError('library outside finite catalogue envelope')
    groups = {g: f'maker{i}' for i, g in enumerate(sorted({g for g, _ in cohorts}))}
    candidates, shared, audit = {}, {}, {}
    for i, ((maker, purpose), selected) in enumerate(sorted(cohorts.items())):
        if len({r['unit'] for r in selected}) < minimum_units:
            raise ValueError('insufficient independent training units in declared cohort')
        candidate, receipt = fit(selected, l2=l2, max_iterations=max_iterations)
        key = f'program{i}'
        candidates[key] = candidate
        shared[key] = groups[maker]
        audit[key] = {'maker_training_cohort': maker, 'purpose_training_cohort': purpose, **receipt}
    # Equal group mass and equal conditional purpose mass; record rather than
    # borrowing the count of convenient training records as a target-population prior.
    sizes = Counter(shared.values())
    prior = {key: 1/(len(sizes)*sizes[shared[key]]) for key in candidates}
    return {'candidates': candidates, 'shared_groups': shared, 'prior': prior}, {
        'training_units_sha256': digest(sorted(training_units)), 'training_records_sha256': digest(records),
        'cohorts': audit, 'units': len({r['unit'] for r in records}),
        'training_labels_in_reader_input': False,
        'meaning': 'program coefficients fitted from permitted training targets; query factors remain inferred'}
