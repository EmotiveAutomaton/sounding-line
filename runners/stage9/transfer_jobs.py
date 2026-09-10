"""Forecast the independently executed post-ban target from the permitted past.

DESIGN CHECK: T01/X01/X02/X06/X08; LESSONS 3--5, CONTROLS 6.
NULL: source ineligibility, changed future, failed calls or missing support refuses
acceptance. ALTERNATIVE: inferred maker knowledge predicts the same post-ban target
better than a declared development-selected cheap rival and unchanged predictions.
The process-likelihood reader sees original past contexts; cheap current-feature
rivals receive the announced tool fact alongside the same recorded events. They are
feature snapshots, not assertions that the old events happened under the new ban.
No outcome enters a reader and no score is computed before the complete cell.
"""
import copy
from pathlib import Path
from . import baseline_matrix_runtime, comparison_runtime
from .artifact_comparisons import checkpoint_call
from .common import digest, distribution
from .series_cases import dose_view
from .transfer_cases import counterfactual


def forecast_unit(case, package, purpose_groups, directory, *, resume_only=False):
    del purpose_groups  # No supplied true purpose in this operation.
    truth = counterfactual(case)
    if truth != case['transfer']:
        raise ValueError('tool-removal source future changed')
    directory = Path(directory)
    original = dose_view(case, 7, 'process_record')
    features = copy.deepcopy(original)
    features['current']['context']['tools']['library'] = False
    baseline_input = {'evidences': {'withdrawn': features}, 'models': package['models']['process_record'],
                      'population_types': package['types']['process_record']}
    base = checkpoint_call(directory/'baselines.json', baseline_input,
        lambda: baseline_matrix_runtime.execute(baseline_input, root=directory/'caps-baseline'), resume_only=resume_only)
    bundle = {'evidence': original, **package['library'], 'announcement': 'library_withdrawn'}
    result = checkpoint_call(directory/'context.json', bundle,
        lambda: comparison_runtime.execute(bundle, operation='context_transfer', budget=800000,
                                           root=directory/'caps-context'), resume_only=resume_only)
    predictions, validity, hashes = {}, {}, {}
    for model in package['models']['process_record']:
        for route in ('population', 'brief', 'cheap-8.0', 'cheap-16.0', 'cheap-32.0'):
            key = model+'|'+route
            validity[key] = base['accepted']; hashes[key] = digest(baseline_input)
            if base['accepted']:
                predictions[key] = base['prediction']['predictions']['withdrawn'][key]
    for name in ('inferred_announced', 'population_announced', 'inferred_stale'):
        validity[name] = result['accepted']; hashes[name] = digest(bundle)
        if result['accepted']:
            predictions[name] = result['prediction']['predictions'][name]
    for p in predictions.values():
        distribution(p)
        if set(p) != set(original['support']):
            raise ValueError('post-ban prediction changed the offered support')
    return {'unit': case['unit'], 'role': case['role'], 'truth': truth['target'],
            'domain': case['private_factors']['domain'], 'purpose': case['private_factors']['purpose'],
            'rows': {'process_record|withdrawn': {'predictions': predictions, 'validity': validity,
                     'model_input_sha256': hashes, 'evidence_sha256': digest(bundle), 'support': original['support'],
                     'unique_prior_works': len({digest(w) for w in original['earlier']})}},
            'costs': [{'operation': name, 'accepted': call['accepted'], 'wall_seconds': call['wall_s'], 'capsule': call['capsule']}
                      for name, call in (('baselines', base), ('context_transfer', result))],
            'counterfactual_sha256': digest(truth), 'assistance': 'observed library withdrawal; same inferred prior purpose and recorded past'}
