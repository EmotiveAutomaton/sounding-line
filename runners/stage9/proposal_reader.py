"""Cross a fixed candidate pool with two explicitly different evaluators.

DESIGN CHECK: M02/X02/X05/X06; LESSONS 3--5. NULL: equal candidates
or empty evidence retain prior odds; copies cannot add evidence. ALTERNATIVE:
event order/outcomes can distinguish candidates a bag-of-marks score conflates.
Both evaluators receive identical programs, observations, support and budget.
The bag score is a frozen ranking surrogate, never a history likelihood. The
stateful score is exact only inside the declared approximate mark-program model;
a data-dependent proposal pool does not become an exact global posterior.
"""
import math

from .artifact_view import validate
from .erased_inference import artifact_work
from .likelihood_table import Table
from .mark_program import policy
from .program_inference import distribution, identity, log_probability, normalize_logs, predictive_mixture


def forecast(bundle,budget):
    if set(bundle)!={'evidence','candidates','prior','evaluator'} or bundle['evaluator'] not in ('stateful','bag'):
        raise ValueError('undeclared proposal evaluation inputs')
    evidence=validate(bundle['evidence'])
    if evidence['view']!='process_record':raise ValueError('unqualified artifact estimator cannot enter proposal comparison')
    candidates,prior=bundle['candidates'],bundle['prior'];distribution(prior,candidates)
    table=Table(candidates,budget)
    if bundle['evaluator']=='stateful':
        result=table.forecast(evidence,prior)
        if not result['exact_within_declared_model']:raise ValueError('non-exact process evaluation')
    else:
        current_key=identity(evidence['current']);earlier={identity(w):w for w in evidence['earlier'] if identity(w)!=current_key}
        works=[*earlier.values(),evidence['current']];scores={};forecasts={}
        for key,program in candidates.items():
            score=0.
            for work in works:
                budget.charge();initial=policy(program,artifact_work(work,[]))
                if work['marks']:
                    score+=math.fsum(log_probability(initial[a]) for a in work['marks'])/len(work['marks'])
            scores[key]=log_probability(prior[key])+score
            budget.charge();forecasts[key]=policy(program,artifact_work(evidence['current']))
        weights,total=normalize_logs(scores)
        result={'prediction':predictive_mixture(weights,forecasts),'weights':weights,
                'log_normalizer':total,'distinct_earlier_works':len(earlier),
                'duplicate_earlier_works_removed':len(evidence['earlier'])-len(earlier),
                'meaning':'softmax of initial-state mark log scores averaged within each work; ignores order/outcomes/stopping'}
    return {'forecast':result,'evaluator':bundle['evaluator'],'pool_sha256':identity({'candidates':candidates,'prior':prior}),
            'evidence_sha256':identity(evidence),'evaluations_used':budget.used,
            'exact_global_posterior':False,'assistance':'numerical candidate-program evaluation','scientific_admission':False}
