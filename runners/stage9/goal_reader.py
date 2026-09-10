"""Use an announced new commission without rewriting the recorded old purpose.

DESIGN CHECK: T03/X02/X05/X08; LESSONS 3--5, CONTROLS 6--7.
NULL: identical purpose vectors and an unchanged deadline leave forecasts unchanged.
ALTERNATIVE: inferred maker knowledge can transfer when the future purpose changes,
with a separate unchanged-goal deadline control. Hidden truth, incomplete matched
purpose support or unqualified likelihoods refuse the entire operation.
Only each candidate's purpose vector is replaced by its same-maker, training-fitted
new-purpose vector. Expertise, habit and all other fitted fields remain fixed. These
fitted vectors are an approximate representation, not identified true causal factors.
Cheap frequency rivals receive the same announcement and original earlier works.
"""
import copy
import math

from .artifact_view import validate
from .choice_features import cheap_adaptation
from .erased_inference import artifact_work
from .likelihood_table import Table
from .mark_program import policy
from .program_inference import distribution, identity, predictive_mixture


def forecast(bundle, budget):
    fields = {'evidence', 'candidates', 'prior', 'shared_groups', 'purpose_groups',
              'announced_purpose', 'deadline', 'population_types'}
    if set(bundle) != fields or bundle['deadline'] not in ('unchanged', 'tight'):
        raise ValueError('undeclared goal-transfer input')
    evidence = validate(bundle['evidence'])
    if evidence['view'] != 'process_record':
        raise ValueError('goal transfer requires qualified process-record likelihood')
    candidates, prior = bundle['candidates'], bundle['prior']
    groups, purposes = bundle['shared_groups'], bundle['purpose_groups']
    distribution(prior, candidates)
    if set(groups) != set(candidates) or set(purposes) != set(candidates):
        raise ValueError('incomplete maker-purpose catalogue')
    if any(not isinstance(v, str) or not v for v in [*groups.values(), *purposes.values()]):
        raise ValueError('invalid maker-purpose label')
    labels = set(purposes.values())
    lookup = {(groups[c], purposes[c]): c for c in candidates}
    if (len(lookup) != len(candidates) or len(lookup) != len(set(groups.values()))*len(labels)
            or bundle['announced_purpose'] is not None and bundle['announced_purpose'] not in labels):
        raise ValueError('missing or ambiguous same-maker destination purpose')
    inferred = Table(candidates, budget).forecast(evidence, prior, shared_groups=groups)
    if inferred['exact_within_declared_model'] is not True:
        raise ValueError('unqualified goal-transfer historical likelihood')
    future = copy.deepcopy(artifact_work(evidence['current']))
    programs = copy.deepcopy(candidates)
    for key, program in programs.items():
        if bundle['announced_purpose'] is not None:
            destination = lookup[groups[key], bundle['announced_purpose']]
            program['purpose'] = copy.deepcopy(candidates[destination]['purpose'])
        if bundle['deadline'] == 'tight':
            program['context']['deadline'] = 'tight'
    if bundle['deadline'] == 'tight':
        future['context']['deadline'] = 'tight'
    budget.charge(len(candidates))
    forecasts = {c: policy(p, future) for c,p in programs.items()}
    population = predictive_mixture(prior, forecasts)
    predictions = {'inferred_changed': predictive_mixture(inferred['weights'], forecasts),
                   'population_changed': population, 'inferred_stale': inferred['prediction']}
    for strength in (8., 16., 32.):
        offsets = cheap_adaptation(evidence, bundle['population_types'], strength)
        weights = {a: p*math.exp(offsets.get(a.split(':')[0], 0.)) for a,p in population.items()}
        total = math.fsum(weights.values())
        predictions['cheap-'+str(strength)] = distribution({a: p/total for a,p in weights.items()})
    if any(set(p) != set(evidence['support']) for p in predictions.values()):
        raise ValueError('goal-transfer forecast changed support')
    return {'predictions': predictions, 'posterior': inferred['weights'],
            'historical_likelihood_receipts': inferred['likelihood_receipts'],
            'historical_input_sha256': identity(evidence), 'future_input_sha256': identity(future),
            'future_programs_sha256': identity(programs), 'information_sha256': identity(bundle),
            'announced_purpose': bundle['announced_purpose'], 'deadline': bundle['deadline'],
            'exact_within_declared_model': True, 'evaluations_used': budget.used,
            'assistance': 'announced future commission or deadline; learned purpose-vector substitution '
                          'with original fitted expertise/habit and historical likelihood fixed',
            'scientific_admission': False}
