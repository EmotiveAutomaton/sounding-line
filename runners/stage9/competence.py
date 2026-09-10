"""Operation-specific evaluator gates; no global reader-admitted shortcut.

DESIGN CHECK: Stage 9 section 5.1/C03. All attempts stay in the denominators.
NULL: blind/story-only or invalid-output packages fail despite fluent explanations.
ALTERNATIVE: an exact constructive executor passes the independent fixable-case battery.
Capability cannot transfer across domain, assistance, operation or package identity.
"""
from collections import Counter
import math

from runners.stage9.common import digest
from runners.stage9.scoring import paired_extended, score_json

PACKAGE_FIELDS = {'domain', 'operation', 'assistance', 'model', 'revision', 'adapter_sha256',
                  'tokenizer_sha256', 'renderer_sha256', 'scorer_sha256', 'execution_interface_sha256'}
OPERATIONS = {'offered_choice', 'altered_prefix', 'local_repair', 'self_rollout', 'stopping', 'rule_transfer', 'historical_broad'}


def package_identity(package):
    if set(package) != PACKAGE_FIELDS or any(not isinstance(v, str) or not v for v in package.values()):
        raise ValueError('complete explicit capability package required')
    if package['operation'] not in OPERATIONS:
        raise ValueError('unregistered capability')
    return digest(package)


def rate(successes, total):
    if type(successes) is not int or type(total) is not int or not 0 <= successes <= total or total < 1:
        raise ValueError('nonempty complete attempt denominator required')
    value = successes / total
    z = 1.959963984540054
    denominator = 1 + z*z / total
    center = (value + z*z / (2*total)) / denominator
    half = z * math.sqrt(value*(1-value)/total + z*z/(4*total*total)) / denominator
    return {'successes': successes, 'attempts': total, 'rate': value,
            'interval': [max(0., center-half), min(1., center+half)], 'method': 'Wilson 95 percent interval'}


def repair_gate(package, rows, expected_attempts, battery_identity, instrument):
    package_sha = package_identity(package)
    if package['operation'] != 'local_repair':
        raise ValueError('repair passage cannot admit another operation')
    rows = list(rows)
    required = {'attempt_id', 'unit', 'fixable', 'legal', 'goal_improving', 'collateral_damage',
                'consequence_difference', 'valid', 'truth_verified'}
    if not rows or len(rows) != expected_attempts or len({r['attempt_id'] for r in rows}) != len(rows):
        raise ValueError('incomplete or duplicated repair attempts')
    for row in rows:
        if not required <= row.keys():
            raise ValueError('repair attempt missing its independently scored fields')
        for key in ('fixable', 'legal', 'goal_improving', 'collateral_damage', 'valid', 'truth_verified'):
            if type(row[key]) is not bool:
                raise ValueError('explicit boolean attempt outcome required')
    fixed = [r for r in rows if r['fixable']]
    if not fixed:
        raise ValueError('battery has no independently fixable case')
    # Invalid predictions remain failed attempts and cannot enter a selected valid subset.
    valid = all(r['valid'] and r['truth_verified'] for r in rows)
    legal = rate(sum(r['legal'] and r['valid'] for r in rows), len(rows))
    improved = rate(sum(r['goal_improving'] and r['legal'] and r['valid'] for r in fixed), len(fixed))
    damage = rate(sum(r['collateral_damage'] for r in rows), len(rows))
    contrast = paired_extended(rows, value='consequence_difference') if valid else None
    instrument_valid = (instrument.get('battery_identity') == battery_identity
                        and instrument.get('exact_executor_pass') is True
                        and instrument.get('blind_control_fail') is True
                        and instrument.get('story_control_fail') is True)
    checks = {'all_outputs_and_truth_valid': valid, 'instrument_known_answers': instrument_valid,
              'legal_at_least_95_percent': legal['rate'] >= .95,
              'correct_improvement_at_least_80_percent': improved['rate'] >= .80,
              'collateral_at_most_5_percent': damage['rate'] <= .05,
              'prospective_gain_at_least_0_05_nats': contrast is not None and contrast['finite_estimate'] and contrast['mean'] >= .05,
              'paired_interval_above_zero': contrast is not None and contrast['ci'] is not None and contrast['ci'][0] > 0}
    return {'kind': 'stage9_capability_v1', 'package': package, 'package_sha256': package_sha,
            'battery_identity': battery_identity, 'expected_attempts': expected_attempts,
            'status': 'PASS' if all(checks.values()) else ('FAIL' if valid and instrument_valid else 'INVALID'),
            'checks': checks, 'legal': legal, 'improvement': improved, 'collateral_damage': damage,
            'consequence_contrast': contrast, 'attempts_sha256': digest(score_json(rows)),
            'scope': 'finite constructed local-repair battery; no whole-generator or human repair admission'}


def require_capability(receipt, package, battery_identity):
    expected = package_identity(package)
    if receipt.get('kind') != 'stage9_capability_v1' or receipt.get('package_sha256') != expected or receipt.get('package') != package:
        raise ValueError('capability belongs to another package or assistance level')
    if receipt.get('battery_identity') != battery_identity:
        raise ValueError('capability belongs to another task distribution')
    if receipt.get('status') != 'PASS' or not receipt.get('checks') or not all(receipt['checks'].values()):
        raise ValueError('required capability has not passed its measured gate')
    return True
