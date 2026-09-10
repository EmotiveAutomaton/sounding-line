"""Purpose uncertainty versus commitment in a declared executable model.

DESIGN CHECK: M03/X02/X05/X06; LESSONS 3--5. NULL: identical purpose
policies give identical forecasts under every intervention. ALTERNATIVE: true
purpose can help and false commitment can hurt; a mixture need not pick a unique
purpose. Missing support, private fields and non-normalized weights refuse.
Purpose conditioning changes the current work only. Training-cohort names are
representation metadata, never evidence of the query's true purpose. Supplied
purpose is a separate invocation with explicitly privileged input.

The purpose-agnostic ablation retains the inferred persistent-maker marginal but
replaces current-purpose posterior weights with their training prior. Thus it
removes purpose-specific predictive use, not all incidental purpose information
in maker inference. This is not a purpose-free cognitive architecture.
"""
import math

from .artifact_view import validate
from .erased_inference import artifact_work
from .likelihood_table import Table
from .mark_program import policy
from .program_inference import distribution, identity, predictive_mixture


def forecast(bundle, budget):
    fields = {'evidence', 'candidates', 'prior', 'shared_groups', 'purpose_groups', 'mode'}
    if bundle.get('mode') == 'supplied':
        fields.add('supplied_purpose')
    if set(bundle) != fields or bundle['mode'] not in ('ordinary', 'supplied'):
        raise ValueError('undeclared purpose input or mode')
    evidence = validate(bundle['evidence'])
    # The full artifact estimator failed its measured envelope. This consumer
    # uses the independently exact process-record likelihood only.
    if evidence['view'] != 'process_record':
        raise ValueError('purpose consumer requires the qualified process-record view')
    candidates, prior = bundle['candidates'], bundle['prior']
    groups, purposes = bundle['shared_groups'], bundle['purpose_groups']
    distribution(prior, candidates)
    if (set(groups) != set(candidates) or set(purposes) != set(candidates) or
            any(not isinstance(x, str) or not x for x in [*groups.values(), *purposes.values()])):
        raise ValueError('incomplete maker or purpose representation')
    labels = sorted(set(purposes.values()))
    if len(labels) < 2:
        raise ValueError('purpose comparison needs distinct represented alternatives')
    members = {g: [c for c in candidates if groups[c] == g] for g in sorted(set(groups.values()))}
    if any(len(cs) != len(labels) or {purposes[c] for c in cs} != set(labels) for cs in members.values()):
        raise ValueError('each maker requires the same complete purpose support')
    table = Table(candidates, budget)

    def conditioned(weights):
        distribution(weights, labels)
        return table.forecast(evidence, prior, shared_groups=groups,
                              current_purpose_weights={c: weights[purposes[c]] for c in candidates})

    if bundle['mode'] == 'supplied':
        result = conditioned(bundle['supplied_purpose'])
        predictions = {'supplied': result}
        marginal = None
    else:
        inferred = table.forecast(evidence, prior, shared_groups=groups)
        marginal = {p: math.fsum(inferred['weights'][c] for c in candidates if purposes[c] == p) for p in labels}
        distribution(marginal, labels)
        # Average all tied maximum purposes. Arbitrary candidate names must not
        # decide which future is predicted when evidence leaves an exact tie.
        maximum = max(marginal.values())
        tied = [p for p in labels if marginal[p] == maximum]
        commitments = [conditioned({p: float(p == chosen) for p in labels}) for chosen in tied]
        single = predictive_mixture({str(i): 1/len(tied) for i in range(len(tied))},
                                    {str(i): r['prediction'] for i, r in enumerate(commitments)})
        masses = {g: math.fsum(prior[c] for c in cs) for g, cs in members.items()}
        weights = {c: inferred['persistent_weights'][groups[c]] * prior[c]/masses[groups[c]] for c in candidates}
        distribution(weights, candidates)
        budget.charge(len(candidates))
        forecasts = {c: policy(program, artifact_work(evidence['current'])) for c, program in candidates.items()}
        predictions = {
            'inferred_distribution': inferred,
            'single_purpose': {'prediction': single, 'selected_purposes': tied,
                               'tie_policy': 'average the individually committed forecasts at exact ties',
                               'components': commitments, 'exact_within_declared_model': True},
            'purpose_agnostic': {'prediction': predictive_mixture(weights, forecasts), 'weights': weights,
                                'exact_within_declared_model': True,
                                'meaning': 'retain maker marginal; restore training conditional-purpose prior'}}
    if any(not r['exact_within_declared_model'] for r in predictions.values()):
        raise ValueError('unqualified approximation cannot enter this consumer')
    return {'predictions': predictions, 'purpose_posterior': marginal,
            'evaluations_used': budget.used, 'information_sha256': identity(bundle),
            'assistance': 'executable fitted model; supplied current-purpose weights' if bundle['mode'] == 'supplied'
                          else 'executable fitted model; no supplied query purpose',
            'view': evidence['view'], 'scientific_admission': False}
