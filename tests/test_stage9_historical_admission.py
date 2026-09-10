"""Complete original-task conjunction has exhaustive failure directions."""
import itertools
import pytest
from runners.stage9 import historical_admission as subject
from runners.stage9.common import write


def fixture(scope='pilot'):
    return ({'scope': scope, 'assigned_units': 4 if scope == 'pilot' else 96,
             'historical_point_threshold': -.05, 'historical_score_floor': 1e-9, 'prediction_criterion_pass': True},
            {'scope': scope, 'expected_attempts': 2 if scope == 'pilot' else 40,
             'population': 'historical_replay', 'comparison': {'criterion_pass': True}})


@pytest.mark.parametrize('scope', ['pilot', 'scientific'])
@pytest.mark.parametrize('prediction,generation,calibrated', list(itertools.product([True, False], repeat=3)))
def test_conjunction_requires_every_component_without_admitting_science(scope, prediction, generation, calibrated):
    p, g = fixture(scope); p['prediction_criterion_pass'] = prediction; g['comparison']['criterion_pass'] = generation
    result = subject.combine(p, g, calibrated, scope)
    assert result['historical_criterion_pass'] == (prediction and generation and calibrated)
    assert result['instrument_accepted'] == calibrated
    assert not result['scientific_admission'] and not result['confirmation_eligible']
    assert not result['pilot_eligible_for_admission']


@pytest.mark.parametrize('mutation', ['prediction_count', 'generation_count', 'population', 'scope', 'threshold', 'floor',
                                     'truthy_prediction', 'truthy_generation', 'truthy_calibration'])
def test_changed_or_incomplete_criteria_cannot_pass(mutation):
    p, g = fixture(); calibrated = True
    if mutation == 'prediction_count': p['assigned_units'] = 3
    elif mutation == 'generation_count': g['expected_attempts'] = 1
    elif mutation == 'population': g['population'] = 'original'
    elif mutation == 'scope': g['scope'] = 'scientific'
    elif mutation == 'threshold': p['historical_point_threshold'] = -.1
    elif mutation == 'floor': p['historical_score_floor'] = 1e-6
    elif mutation == 'truthy_prediction': p['prediction_criterion_pass'] = 'true'
    elif mutation == 'truthy_generation': g['comparison']['criterion_pass'] = 1
    else: calibrated = 1
    with pytest.raises(ValueError): subject.combine(p, g, calibrated, 'pilot')


@pytest.mark.parametrize('field', ['family', 'package_kind', 'adapter_sha256', 'training_complete_sha256',
                                  'precision', 'operation', 'scope', 'package'])
def test_producer_package_substitution_refuses_before_case_or_calibration_access(tmp_path, monkeypatch, field):
    monkeypatch.setattr(subject, 'inside', lambda p: p.resolve())
    monkeypatch.setattr(subject, 'validate_complete', lambda *args: {'execution_complete': True})
    monkeypatch.setattr(subject, 'score_package', lambda p: p)
    def forbidden(*args): raise AssertionError('substituted package reached source or calibration access')
    monkeypatch.setattr(subject, 'prediction_inputs', forbidden)
    monkeypatch.setattr(subject, 'checked_calibration', forbidden)
    paths = [tmp_path/name for name in ('prediction', 'generation', 'calibration', 'pc', 'gc')]
    base = {'scope': 'pilot', 'family': 'qwen', 'package_kind': 'fitted', 'adapter_sha256': 'a'*64,
            'training_complete_sha256': 'b'*64, 'precision': 'float16'}
    for path, operation in zip(paths, ('historical_prediction', 'broad_historical')):
        identity = dict(base, operation=operation)
        if path == paths[1] and field != 'package': identity[field] = 'substituted'
        write(path/'IDENTITY.json', identity)
        write(path/'PACKAGE.json', {'model': 'wrong' if path == paths[1] and field == 'package' else 'same'})
    with pytest.raises(ValueError): subject.inputs(*paths, 'pilot')
