"""Prospective global/local reports with an explicit source reliability assumption.

DESIGN CHECK: T04/X02/X05/X08; LESSONS 3--5, CONTROLS 6--7.
NULL: a report about an already visible mark adds no independent information; equal
operative futures remain equal under any reliability. ALTERNATIVE: true reports
improve prospective prediction while false reports can mislead the same reader.
Unknown fields, nonexistent sections/marks and unqualified likelihoods refuse.
Reports concern a future deadline or the maker's belief that one section is checked.
Historical likelihoods are unchanged. Each reported binary future state has a .5
pre-report prior, with the supplied symmetric source reliability as its likelihood.
This is a declared channel assumption, not measured human source calibration.
The fitted mark model remains approximate; reported availability earns no generation
legality credit and the program's explicit action noise is preserved.
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
    if set(bundle) != {'evidence','candidates','prior','shared_groups','population_types','cue'}:
        raise ValueError('undeclared context-cue input')
    evidence=validate(bundle['evidence'])
    if evidence['view'] != 'process_record':
        raise ValueError('cue reader requires qualified process-record likelihood')
    cue=bundle['cue']
    if not isinstance(cue,dict) or set(cue) != {'kind','value','section','reliability'}:
        raise ValueError('incomplete source-identified cue')
    reliability=cue['reliability']
    if type(reliability) not in (int,float) or not math.isfinite(reliability) or not 0<=reliability<=1:
        raise ValueError('invalid symmetric source reliability')
    if cue['kind']=='deadline':
        if cue['value'] not in ('loose','tight') or cue['section'] is not None:
            raise ValueError('invalid reported deadline')
        states=('loose','tight')
    elif cue['kind']=='section_checked':
        if type(cue['value']) is not bool or cue['section'] not in {s['name'] for s in evidence['current']['context']['sections']}:
            raise ValueError('invalid reported checked section')
        states=(False,True)
    elif cue['kind']=='past_mark':
        if cue['section'] is not None or cue['value'] not in evidence['current']['marks']:
            raise ValueError('redundant cue must name a mark already visible in the same evidence')
        states=()
    else:
        raise ValueError('unsupported cue causal scope')
    candidates,prior=bundle['candidates'],bundle['prior'];distribution(prior,candidates)
    inferred=Table(candidates,budget).forecast(evidence,prior,shared_groups=bundle['shared_groups'])
    if inferred['exact_within_declared_model'] is not True:
        raise ValueError('unqualified historical likelihood for cue reader')
    future=copy.deepcopy(artifact_work(evidence['current']))
    forecasts={};state_weights={}
    if not states:
        budget.charge(len(candidates))
        forecasts={c:policy(p,future) for c,p in candidates.items()}
    else:
        state_weights={str(state):reliability if state==cue['value'] else 1-reliability for state in states}
        for key,program in candidates.items():
            alternatives={}
            for state in states:
                p=copy.deepcopy(program);work=copy.deepcopy(future);checked=()
                if cue['kind']=='deadline':
                    work['context']['deadline']=state;p['context']['deadline']=state
                elif state:
                    checked=(cue['section'],)
                budget.charge(1)
                alternatives[str(state)]=policy(p,work,believed_checked=checked)
            forecasts[key]=predictive_mixture(state_weights,alternatives)
    population=predictive_mixture(prior,forecasts)
    predictions={'inferred_cued':predictive_mixture(inferred['weights'],forecasts),
                 'population_cued':population,'inferred_uncued':inferred['prediction']}
    for strength in (8.,16.,32.):
        offsets=cheap_adaptation(evidence,bundle['population_types'],strength)
        weights={a:p*math.exp(offsets.get(a.split(':')[0],0.)) for a,p in population.items()}
        total=math.fsum(weights.values())
        predictions['cheap-'+str(strength)]=distribution({a:p/total for a,p in weights.items()})
    if any(set(p)!=set(evidence['support']) for p in predictions.values()):
        raise ValueError('context cue changed the offered support')
    return {'predictions':predictions,'posterior':inferred['weights'],
            'historical_likelihood_receipts':inferred['likelihood_receipts'],
            'historical_input_sha256':identity(evidence),'information_sha256':identity(bundle),
            'reported_state_weights':state_weights,'cue_kind':cue['kind'],
            'distinct_earlier_works':inferred['distinct_earlier_works'],
            'exact_within_declared_model':True,'evaluations_used':budget.used,
            'assistance':'source-reliability-weighted future cue, original past and fitted maker factors; '
                         'balanced binary pre-report state prior; past-mark reports are redundant',
            'scientific_admission':False}
