"""Actual goal-reversal or unchanged-goal difficulty forecasts on the same sources.

DESIGN CHECK: T03/X02/X06/X08; LESSONS 3--5, CONTROLS 6--7.
NULL: altered future, incomplete calls or changed support invalidates the unit;
source shortfall blocks its entire prediction cell. ALTERNATIVE: maker inference
supports prospective changed-goal prediction beyond announcement-aware population
and cheap frequency rivals. Conditions have separate cell identities and produce
paths, with their original independent source unit retained for paired analysis.
The future goal announcement is supplied context, never a recovered historical goal.
"""
from pathlib import Path
from . import comparison_runtime
from .artifact_comparisons import checkpoint_call
from .common import digest, distribution
from .series_cases import dose_view
from .goal_cases import counterfactual


def forecast_unit(case, package, purpose_groups, directory, *, resume_only=False):
    declared = case['goal_transfer']
    truth = counterfactual(case, declared['condition'])
    if truth != declared:
        raise ValueError('goal-transfer source future changed')
    evidence = dose_view(case, 7, 'process_record')
    bundle = {'evidence': evidence, **package['library'], 'purpose_groups': purpose_groups,
              'announced_purpose': truth['announced_purpose'], 'deadline': truth['deadline'],
              'population_types': package['types']['process_record']}
    result = checkpoint_call(Path(directory)/'goal.json', bundle,
        lambda: comparison_runtime.execute(bundle, operation='goal_transfer', budget=800000,
                                           root=Path(directory)/'caps-goal'), resume_only=resume_only)
    names = ('inferred_changed', 'population_changed', 'inferred_stale', 'cheap-8.0', 'cheap-16.0', 'cheap-32.0')
    predictions = result['prediction']['predictions'] if result['accepted'] else {}
    for prediction in predictions.values():
        distribution(prediction)
        if set(prediction) != set(evidence['support']):
            raise ValueError('goal-transfer prediction changed the offered support')
    return {'unit': case['unit'], 'role': case['role'], 'truth': truth['target'],
            'domain': case['private_factors']['domain'], 'purpose': case['private_factors']['purpose'],
            'rows': {'process_record|'+truth['condition']: {'predictions': predictions,
                     'validity': {n: result['accepted'] for n in names},
                     'model_input_sha256': {n: digest(bundle) for n in names},
                     'evidence_sha256': digest(evidence), 'support': evidence['support'],
                     'unique_prior_works': len({digest(w) for w in evidence['earlier']})}},
            'costs': [{'operation': 'goal_transfer', 'accepted': result['accepted'],
                       'wall_seconds': result['wall_s'], 'capsule': result['capsule']}],
            'counterfactual_sha256': digest(truth), 'condition': truth['condition'],
            'assistance': 'announced new commission or deadline, original historical contexts and fitted expertise retained'}
