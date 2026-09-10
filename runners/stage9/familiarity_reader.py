"""Recognition odds and prospective forecasts from bounded same/other exposure.

DESIGN CHECK: T02/X02/X05/X06/X08; LESSONS 3--5, CONTROLS 6--7.
NULL: identical maker likelihoods retain the same/different prior and identical
future forecasts. ALTERNATIVE: an expected signature can increase recognition
while raw predictive surprise stays low. Recognition alone is no recovery claim.
The current observation is one executed action, conditional on execution; failures
are summed when erased. Earlier works each have a finite action budget, retaining
early stops. Independent per-work purpose is marginalized within persistent-maker
groups. Same/independent maker are explicit fitted-model hypotheses, not supplied
truth. Their model-conditional odds need evaluation on the conditional stress
sample; this routine does not assert natural-sample calibration.
"""
import math

from .artifact_view import action_id, validate, validate_work
from .choice_features import cheap_adaptation
from .constraint_reader import artifact_observation_likelihood, record_observation_likelihood
from .erased_inference import artifact_work
from .mark_program import policy, success_probabilities, validate as validate_program
from .program_inference import (distribution, identity, log_probability, logsumexp,
                                normalize_logs, predictive_mixture)


def first_action_likelihood(program, work, view, budget):
    validate_work(work, view)
    if len(work['marks']) > 1 or (view == 'process_record' and
            (len(work['events']) != 1 or work['observed_stop'] is not None)):
        raise ValueError('current observation must contain exactly one executed action')
    initial = artifact_work(work, [])
    budget.charge(); p = policy(program, initial); success = success_probabilities(program, initial)
    execution = math.fsum(p[a] for a in success)
    if execution <= 0: raise ValueError('candidate cannot execute the conditioned observation')
    if view == 'process_record':
        e = work['events'][0]; a = action_id(e)
        mass = p[a] * (success[a] if e['outcome'] == 'done' else 1-success[a])
    elif work['marks']:
        a = work['marks'][0]; mass = p[a] * success[a]
    else:
        mass = math.fsum(p[a]*(1-success[a]) for a in success)
    return log_probability(min(1., mass/execution))


def forecast(bundle, budget):
    if set(bundle) != {'evidences','maximum_actions','candidates','prior','shared_groups','same_prior','population_types'}:
        raise ValueError('undeclared familiarity inputs')
    evidences, candidates, prior, groups = (bundle[k] for k in ('evidences','candidates','prior','shared_groups'))
    maximum, same_prior = bundle['maximum_actions'], bundle['same_prior']
    if type(maximum) is not int or not 1 <= maximum <= 3:
        raise ValueError('invalid bounded archive observation budget')
    if (isinstance(same_prior,bool) or not isinstance(same_prior,(int,float)) or
            not math.isfinite(same_prior) or not 0 < same_prior < 1):
        raise ValueError('same-maker prior must leave both hypotheses live')
    if not isinstance(evidences,dict) or not 1 <= len(evidences) <= 8 or not candidates or len(candidates) > 64:
        raise ValueError('invalid explicit familiarity matrix or candidate support')
    distribution(prior,candidates)
    for program in candidates.values(): validate_program(program)
    if set(groups) != set(candidates) or any(not isinstance(g,str) or not g for g in groups.values()):
        raise ValueError('incomplete persistent maker grouping')
    members = {g:[c for c in candidates if groups[c]==g] for g in sorted(set(groups.values()))}
    masses = {g:math.fsum(prior[c] for c in cs) for g,cs in members.items()}
    if any(m <= 0 for m in masses.values()): raise ValueError('zero-mass maker group')
    conditional = {c:log_probability(prior[c]/masses[groups[c]]) for c in candidates}
    cache, queries = {}, {}
    for name, evidence in evidences.items():
        validate(evidence)
        if not 1 <= len(evidence['earlier']) <= 7:
            raise ValueError('recognition requires bounded prior exposure')
        view = evidence['view']; archive = []
        for earlier in evidence['earlier']:
            likelihoods = {}
            for c,program in candidates.items():
                key = (c,view,identity(earlier),'earlier')
                if key not in cache:
                    function = record_observation_likelihood if view=='process_record' else artifact_observation_likelihood
                    cache[key] = function(program,earlier,budget,maximum)['log_mass']
                likelihoods[c] = cache[key]
            archive.append({g:logsumexp([conditional[c]+likelihoods[c] for c in cs]) for g,cs in members.items()})
        # Repeated observable content is not automatically an additional work.
        # The source owner establishes distinct works; exact duplicates are not
        # collapsed here because independently generated empty works may match.
        maker, _ = normalize_logs({g:log_probability(masses[g])+math.fsum(row[g] for row in archive) for g in members})
        current_likelihoods, predictions = {}, {}
        for c,program in candidates.items():
            key = (c,view,identity(evidence['current']),'current')
            if key not in cache:
                cache[key] = first_action_likelihood(program,evidence['current'],view,budget)
            current_likelihoods[c] = cache[key]
            budget.charge(); predictions[c] = policy(program,artifact_work(evidence['current']))
        same_weights, same_mass = normalize_logs({c:log_probability(maker[groups[c]])+conditional[c]+current_likelihoods[c] for c in candidates})
        different_weights, different_mass = normalize_logs({c:log_probability(prior[c])+current_likelihoods[c] for c in candidates})
        recognition, observation_mass = normalize_logs({'same':log_probability(same_prior)+same_mass,
            'different':log_probability(1-same_prior)+different_mass})
        weights = {c:recognition['same']*same_weights[c]+recognition['different']*different_weights[c] for c in candidates}
        before = {c:same_prior*maker[groups[c]]*prior[c]/masses[groups[c]]+(1-same_prior)*prior[c] for c in candidates}
        routes = {'recognition_mixture':weights, 'assume_same':same_weights,
                  'assume_different':different_weights, 'program_prior':prior}
        recognition_routes={'inferred':recognition,'prior':{'same':same_prior,'different':1-same_prior}}
        # Strong cheap comparison: the existing fitted type-frequency reference
        # and three development-selectable bag adaptations. These are heuristic
        # verification probabilities, not historical maker posteriors. Erased
        # failures reveal no type, so this deliberately type-only rival abstains.
        current=evidence['current']
        kind=(current['events'][0]['type'] if view=='process_record' else
              current['marks'][0].split(':')[0] if current['marks'] else None)
        for strength in (8.,16.,32.):
            offsets=cheap_adaptation(evidence,bundle['population_types'],strength)
            odds=math.exp(offsets[kind]) if kind is not None else 1.
            same=same_prior*odds/(same_prior*odds+1-same_prior)
            recognition_routes['surface-'+str(strength)]={'same':same,'different':1-same}
        queries[name] = {'recognition':recognition, 'recognition_prior':{'same':same_prior,'different':1-same_prior},
            'recognition_routes':recognition_routes,
            'predictions':{route:predictive_mixture(w,predictions) for route,w in routes.items()},
            'weights':routes, 'archive_maker_weights':maker, 'current_program_weights_before':before,
            'raw_observation_surprise_nats':-observation_mass,
            'same_archive_observation_surprise_nats':-same_mass,
            'population_observation_surprise_nats':-different_mass,
            'current_log_likelihoods':current_likelihoods, 'archive_work_count':len(archive),
            'exact_within_declared_model':True}
    return {'queries':queries, 'evaluations_used':budget.used, 'information_sha256':identity(bundle),
        'assistance':'independently fitted approximate mark model; explicit bounded observation design',
        'current_observation':'one action conditional on execution; future unobserved',
        'recognition_claim':'same versus independent persistent maker within fitted model; no process-recovery implication'}
