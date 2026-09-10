"""Joint fitted-program/history inference on an explicitly offered finite support.

DESIGN CHECK: M05/X02/X05/X08; LESSONS 3--5, CONTROLS 6--7.
NULL: equal path likelihoods retain history ambiguity; an identical future across
programs cannot become a predictive gain from choosing a history. ALTERNATIVE:
likelihood-weighted histories support calibrated narrowing and future prediction.
Missing/duplicate histories, hidden truth, unsupported observations or numerical
failure refuse. The six three-successful-event histories are supplied candidates;
this is conditional offered-support inference, not unrestricted historical recovery.
All fitted parameters come from independent training. A supplied later observation
updates history only; it never generates a prediction scored on that observation.
"""
import copy
import itertools
import math
from .artifact_view import validate,validate_work,action_id
from .erased_inference import artifact_work,process_likelihood
from .mark_program import policy,success_probabilities
from .program_inference import distribution,identity,log_probability,normalize_logs,predictive_mixture


def forecast(bundle,budget):
    if set(bundle)!={'evidence','candidates','prior','histories','observed_future'}:
        raise ValueError('undeclared offered-history input')
    evidence=validate(bundle['evidence'])
    if evidence['view'] not in ('artifact','process_record') or evidence['earlier'] or len(evidence['current']['marks'])!=3:
        raise ValueError('offered-history operation requires the declared three-mark work without earlier works')
    histories=bundle['histories'];marks=evidence['current']['marks']
    if not isinstance(histories,dict) or len(histories)!=6:
        raise ValueError('complete six-history support required')
    orders=[];works={}
    for h,events in histories.items():
        if not isinstance(h,str) or not h or len(events)!=3 or any(e['outcome']!='done' for e in events):
            raise ValueError('invalid offered completed history')
        work={**copy.deepcopy(evidence['current']),'events':events,'observed_stop':None}
        validate_work(work,'process_record');orders.append(tuple(action_id(e) for e in events));works[h]=work
    if len(set(orders))!=6 or set(orders)!=set(itertools.permutations(marks)):
        raise ValueError('duplicate or omitted offered history')
    recorded=None
    if evidence['view']=='process_record':
        matches=[h for h,events in histories.items() if events==evidence['current']['events']]
        if len(matches)!=1 or evidence['current']['observed_stop'] is not None:
            raise ValueError('supplied process diagnostic must identify one offered censored history')
        recorded=matches[0]
    candidates,prior=bundle['candidates'],bundle['prior'];distribution(prior,candidates)
    old=artifact_work(evidence['current']);changed=copy.deepcopy(old);changed['context']['tools']['library']=True
    futures={'old':{},'changed':{}};success={}
    for c,p in candidates.items():
        new=copy.deepcopy(p);new['context']['library']='available';budget.charge(2)
        futures['old'][c]=policy(p,old);futures['changed'][c]=policy(new,changed)
        success[c]=success_probabilities(new,changed)
    observed=bundle['observed_future']
    if observed is not None:
        if (not isinstance(observed,dict) or set(observed)!={'action','outcome'}
                or observed['action'] not in evidence['support']
                or observed['outcome']!=('stop' if observed['action']=='stop' else 'done')):
            raise ValueError('invalid supplied later observation')
    pairs=[];logs={}
    for c in sorted(candidates):
        for h in sorted(histories):
            mass=process_likelihood(candidates[c],works[h],budget)['log_mass']+log_probability(prior[c])
            if recorded is not None and h!=recorded:mass=-math.inf
            if observed is not None:
                mass+=log_probability(futures['changed'][c][observed['action']])
                if observed['action']!='stop':mass+=log_probability(success[c][observed['action']])
            key=str(len(pairs));pairs.append((c,h));logs[key]=mass
    weights,_=normalize_logs(logs)
    hp={h:math.fsum(weights[str(i)] for i,(_,hh) in enumerate(pairs) if hh==h) for h in histories}
    cp={c:math.fsum(weights[str(i)] for i,(cc,_) in enumerate(pairs) if cc==c) for c in candidates}
    # Marginal summation of exponentiated log weights can retain a few ulps of
    # total-mass error. Normalize before using either marginal as a forecast.
    ht,ct=math.fsum(hp.values()),math.fsum(cp.values())
    hp={h:p/ht for h,p in hp.items()};cp={c:p/ct for c,p in cp.items()}
    distribution(hp,histories);distribution(cp,candidates)
    best=max(hp.values());tied=[h for h,p in hp.items() if p==best]
    histories_out={'inferred':hp,'uniform':{h:1/len(histories) for h in histories},
                   'committed':{h:float(h in tied)/len(tied) for h in histories}}
    predictions={}
    if observed is None:
        restricted={c:math.fsum(weights[str(i)] for i,(cc,h) in enumerate(pairs) if cc==c and h in tied) for c in candidates}
        total=math.fsum(restricted.values());restricted=distribution({c:p/total for c,p in restricted.items()})
        for condition,forecasts in futures.items():
            predictions[condition]={'inferred':predictive_mixture(cp,forecasts),
                                    'committed':predictive_mixture(restricted,forecasts),
                                    'population':predictive_mixture(prior,forecasts)}
    return {'history_predictions':histories_out,'future_predictions':predictions,'program_posterior':cp,
            'selected_histories':tied,'information_sha256':identity(bundle),'evaluations_used':budget.used,
            'exact_within_offered_model':True,'later_observation_supplied':observed is not None,'view':evidence['view'],
            'assistance':'complete six-history candidate support; independently fitted mark-program likelihoods; '
                         'ties average committed histories; true source law and selected historical event are absent',
            'scientific_admission':False}
