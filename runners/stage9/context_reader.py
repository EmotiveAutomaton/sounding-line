"""Infer the recorded past, then apply an explicitly observed future constraint.

DESIGN CHECK: T01/X02/X05/X08; LESSONS 3--5, CONTROLS 6.
NULL: an irrelevant announcement leaves forecasts unchanged; altered announcements
cannot alter historical likelihoods or posterior weights. ALTERNATIVE: an observed
tool withdrawal changes the future policy under unchanged learned goal, expertise
and habit. It does not rewrite earlier contexts or assert a new purpose.
Unsupported interventions, hidden truth, changed support or approximate likelihoods
refuse. The fitted mark program remains approximate to the actual maker, although
its process-record likelihood is exact. No generation or causal-history admission.
"""
import copy

from .artifact_view import validate
from .erased_inference import artifact_work
from .likelihood_table import Table
from .mark_program import policy
from .program_inference import distribution, identity, predictive_mixture


def forecast(bundle, budget):
    if (set(bundle) != {'evidence', 'candidates', 'prior', 'shared_groups', 'announcement'}
            or bundle['announcement'] not in ('none', 'library_withdrawn')):
        raise ValueError('undeclared announced-context input or intervention')
    evidence = validate(bundle['evidence'])
    if evidence['view'] != 'process_record':
        raise ValueError('context consumer requires qualified process-record likelihood')
    candidates, prior = bundle['candidates'], bundle['prior']
    distribution(prior, candidates)
    table = Table(candidates, budget)
    inferred = table.forecast(evidence, prior, shared_groups=bundle['shared_groups'])
    if inferred['exact_within_declared_model'] is not True:
        raise ValueError('unqualified historical likelihood in context consumer')
    future = artifact_work(evidence['current'])
    programs = copy.deepcopy(candidates)
    # artifact_work keeps the context reference; detach it before changing anything.
    future = copy.deepcopy(future)
    if bundle['announcement'] == 'library_withdrawn':
        future['context']['tools']['library'] = False
        for program in programs.values():
            # The specified withdrawal is observed by the maker. It supersedes
            # earlier beliefs about this tool, not any other program parameter.
            program['context']['library'] = 'unavailable'
    budget.charge(len(candidates))
    forecasts = {key: policy(program, future) for key, program in programs.items()}
    predictions = {'inferred_announced': predictive_mixture(inferred['weights'], forecasts),
                   'population_announced': predictive_mixture(prior, forecasts),
                   'inferred_stale': inferred['prediction']}
    if any(set(p) != set(evidence['support']) for p in predictions.values()):
        raise ValueError('announced-context future support differs')
    return {'predictions': predictions, 'posterior': inferred['weights'],
            'historical_likelihood_receipts': inferred['likelihood_receipts'],
            'historical_input_sha256': identity(evidence), 'future_input_sha256': identity(future),
            'information_sha256': identity(bundle), 'announcement': bundle['announcement'],
            'distinct_earlier_works': inferred['distinct_earlier_works'],
            'evaluations_used': budget.used, 'exact_within_declared_model': True,
            'assistance': 'announced library removal observed by maker; executable fitted model; '
                          'same historical evidence, purpose, expertise and habitual parameters',
            'scientific_admission': False}
