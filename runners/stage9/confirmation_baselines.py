"""B02: execute one frozen numerical-baseline claim on exactly its reserved units.

DESIGN CHECK: B02/X01/X02/X05/X06/X12; LESSONS 3--5, CONTROLS 6--7.
NULL: substituted source worlds, hidden inputs, changed fits, incomplete support or
failed calls cannot become a finite confirmation contrast. ALTERNATIVE: every
assigned source runs the exact frozen paired views/routes through the restricted
baseline capsule. Saved calls and full units reconstruct without new inference.
The fitted numerical baselines carry no neural training-seed claim. Every failed
forecast and every nonfinite contrast is retained; no finite-only subset is scored.
This executes predictions; full-family calculation and B03 admission remain separate.
"""
import argparse
import math
from pathlib import Path
import time

from . import baseline_matrix_runtime
from .artifact_comparisons import audit_execution, checkpoint_call, model_inputs, validate_cases
from .common import REPO, Units, digest, distribution, file_hash, freeze
from .confirmation_access import frozen_claim, reservation
from .revision_predictions import finish, reentry, sources
from .scoring import log_score, score_json
from .series_cases import dose_view
from .training_jobs import cell_identity


def forecast(case, models, contrast, call):
    """Only the frozen views/doses enter their respective reader capsules."""
    views = sorted({side['view'] for side in contrast.values()})
    output, costs = {}, []
    for view in views:
        selected = {name: side for name, side in contrast.items() if side['view'] == view}
        required = {side['model'].rsplit('|', 1)[0] for side in selected.values()}
        if not required <= set(models['models'][view]):
            raise ValueError('frozen baseline key is absent from the actual fitting package')
        evidences = {name: dose_view(case, side['dose'], view) for name, side in selected.items()}
        bundle = {'evidences': evidences, 'models': {k: models['models'][view][k] for k in sorted(required)},
                  'population_types': models['types'][view]}
        result = call(bundle, view)
        costs.append({'view': view, 'accepted': result['accepted'], 'wall_seconds': result['wall_s'],
                      'capsule': result['capsule']})
        for name, side in selected.items():
            probabilities = result['prediction']['predictions'][name].get(side['model']) if result['accepted'] else None
            if result['accepted']:
                distribution(probabilities)
                if set(probabilities) != set(evidences[name]['support']):
                    raise ValueError('frozen baseline forecast omits public support')
            output[name] = {'valid': result['accepted'], 'probabilities': probabilities,
                            'evidence_sha256': digest(evidences[name]), 'route': side}
    return {'unit': case['unit'], 'target': 'next_recorded_event', 'truth': case['target'],
            'role': case['role'], 'sides': output, 'costs': costs}


def calculation_input(rows, expected):
    if (len(rows) != len(expected) or len(expected) != len(set(expected))
            or {r['unit'] for r in rows} != set(expected)):
        raise ValueError('confirmation output does not retain the exact assigned source units')
    differences, limitations, scores = [], [], []
    for row in rows:
        if set(row['sides']) != {'left', 'right'}:
            raise ValueError('confirmation omits one paired side')
        if any(side['valid'] is not True for side in row['sides'].values()):
            limitations.append({'unit': row['unit'], 'reason': 'required forecast failed; no valid-only subset'})
            continue
        a, b = [row['sides'][side]['probabilities'] for side in ('left', 'right')]
        if set(a) != set(b):
            raise ValueError('paired confirmation supports differ')
        left, right = log_score(a, row['truth']), log_score(b, row['truth'])
        difference = None if left == right == -math.inf else left - right
        scores.append({'unit': row['unit'], 'left_log_score': left, 'right_log_score': right,
                       'difference': difference})
        if difference is None or not math.isfinite(difference):
            limitations.append({'unit': row['unit'], 'reason': 'nonfinite paired contrast; finite inference not defined'})
        else:
            differences.append({'unit': row['unit'], 'target': row['target'], 'seed': None, 'difference': difference})
    targets = {r['unit']: [r['target']] for r in rows}
    # Scores of all valid forecasts remain diagnostic data. They are never used
    # as a finite-only subset when any assigned target failed or was nonfinite.
    return score_json({'calculation_status': 'NOT_RUN' if limitations else 'READY',
        'assigned_units': len(expected), 'assigned_targets': targets, 'limitations': limitations,
        'paired_rows': None if limitations else differences, 'all_available_scores': scores,
        'excluded_units': 0, 'excluded_targets': 0, 'scientific_confirmation': False})


def run(directory, freeze_directory, manifest_path, queue_path, claim_id, scope):
    started, cpu = time.monotonic(), time.process_time()
    frozen = frozen_claim(freeze_directory, manifest_path, queue_path, claim_id, scope)
    with reservation(directory, frozen) as access:
        packet, contract = access['packet'], access['contract']
        role = 'pilot' if scope == 'pilot' else 'reserve'
        cases = [access['payloads'][unit] for unit in packet['reserve_units']]
        validate_cases(cases, role)
        for unit, case in zip(packet['reserve_units'], cases):
            if case['unit'] != unit or digest(case['sources']) != contract['reserve'][unit]['content_sha256']:
                raise ValueError('reserve source content differs from the actual reconstructed maker series')
        models = model_inputs((REPO / contract['reader']['path']).parent, role)
        if models['completion_sha256'] != contract['reader']['sha256']:
            raise ValueError('actual baseline fitting completion differs from the frozen reader')
        work = Path(directory) / 'work'
        identity = {'cell_identity': cell_identity(), 'operation': 'frozen-baseline-confirmation-v1',
            'scope': scope, 'role': role, 'source': sources(), 'claim_id': claim_id,
            'freeze_complete_sha256': frozen['freeze_complete_sha256'], 'claims_sha256': frozen['claims_sha256'],
            'execution_contract_sha256': digest(contract), 'selected_units': packet['reserve_units'],
            'access_identity_sha256': digest(access['identity']), 'access_opened_sha256': file_hash(Path(directory) / 'OPENED.json')}
        units = Units(work, identity)
        prior = reentry(work, identity)
        rows = []
        for case in cases:
            saved = units.get(case['unit'])
            def call(bundle, view):
                result = checkpoint_call(work / 'calls' / case['unit'][:16] / (view + '.json'), bundle,
                    lambda: baseline_matrix_runtime.execute(bundle, root=work / 'capsules'),
                    resume_only=saved is not None or prior is not None)
                audit_execution(result)
                return result
            row = forecast(case, models, contract['contrast'], call)
            if saved is not None and saved != row:
                raise ValueError('saved complete confirmation unit failed reconstruction')
            if prior is not None and saved is None:
                raise ValueError('completed confirmation lacks an assigned unit')
            units.put(case['unit'], row);rows.append(row)
        outcome = calculation_input(rows, packet['reserve_units'])
        freeze(work / 'PREDICTIONS.json', rows)
        freeze(work / 'OUTCOME.json', outcome)
        if prior is not None:
            return prior
        return finish(work, identity, started, cpu,
            ['PREDICTIONS.json', 'OUTCOME.json', 'units', 'calls', 'capsules', '../OPENED.json', '../IDENTITY.json'],
            assigned_units=len(cases), completed_units=len(rows), calculation_status=outcome['calculation_status'],
            scientific_confirmation=False, role=role)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for key in ('output', 'freeze', 'manifest', 'queue'):
        parser.add_argument('--' + key, type=Path, required=True)
    parser.add_argument('--claim', required=True)
    parser.add_argument('--scope', choices=('pilot', 'scientific'), required=True)
    args = parser.parse_args()
    run(args.output, args.freeze, args.manifest, args.queue, args.claim, args.scope)
