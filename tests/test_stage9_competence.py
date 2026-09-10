import pytest

from runners.stage9.competence import PACKAGE_FIELDS, repair_gate, require_capability


def package():
    return {**{k: 'fixed-fixture' for k in PACKAGE_FIELDS}, 'operation': 'local_repair', 'assistance': 'exact-execution'}


def rows():
    return [{'attempt_id': str(i), 'unit': str(i), 'fixable': True, 'legal': True,
             'goal_improving': True, 'collateral_damage': False, 'consequence_difference': .12,
             'valid': True, 'truth_verified': True} for i in range(100)]


INSTRUMENT = {'battery_identity': 'independent-fixture', 'exact_executor_pass': True,
              'blind_control_fail': True, 'story_control_fail': True}


def test_exact_pass_story_failure_and_collateral_failure_are_separate():
    exact = repair_gate(package(), rows(), 100, 'independent-fixture', INSTRUMENT)
    assert require_capability(exact, package(), 'independent-fixture')
    story = [{**r, 'goal_improving': False, 'consequence_difference': 0.0} for r in rows()]
    assert repair_gate(package(), story, 100, 'independent-fixture', INSTRUMENT)['status'] == 'FAIL'
    damaged = rows()
    for r in damaged[:6]:
        r['collateral_damage'] = True
    assert repair_gate(package(), damaged, 100, 'independent-fixture', INSTRUMENT)['status'] == 'FAIL'


def test_missing_or_invalid_attempt_cannot_disappear_from_denominator():
    with pytest.raises(ValueError):
        repair_gate(package(), rows()[:-1], 100, 'independent-fixture', INSTRUMENT)
    attempts = rows()
    attempts[0]['valid'] = False
    result = repair_gate(package(), attempts, 100, 'independent-fixture', INSTRUMENT)
    assert result['status'] == 'INVALID'
    assert result['legal']['attempts'] == 100
    assert result['legal']['successes'] == 99


def test_assistance_operation_and_battery_cannot_borrow_another_pass():
    result = repair_gate(package(), rows(), 100, 'independent-fixture', INSTRUMENT)
    for changed in ({'assistance': 'unaided'}, {'operation': 'self_rollout'}, {'domain': 'another-domain'}):
        with pytest.raises(ValueError):
            require_capability(result, {**package(), **changed}, 'independent-fixture')
    with pytest.raises(ValueError):
        require_capability(result, package(), 'another-distribution')


def test_nonfinite_gain_cannot_admit_or_discard_a_repair_attempt():
    import math
    from runners.stage9.common import canonical
    for value in (math.inf,-math.inf,None):
        attempts = rows()
        attempts[0]['consequence_difference'] = value
        result = repair_gate(package(),attempts,100,'independent-fixture',INSTRUMENT)
        assert result['status'] == 'FAIL'
        assert result['consequence_contrast']['n_targets'] == 100
        assert result['consequence_contrast']['excluded_targets'] == 0
        assert not result['checks']['prospective_gain_at_least_0_05_nats']
        canonical(result)
