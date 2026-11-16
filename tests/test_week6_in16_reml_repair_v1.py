"""Constructed-only precision controls. Owner executes in one counted slot.

DESIGN CHECK: exact balanced REML, zero, weighted copies, shifted responses,
independent covariance score and unchanged comparator; no participant source.
"""
import copy
from types import SimpleNamespace
import numpy as np
import pandas as pd
import pytest
from runners.drive.cards import week6_in16_reml_repair_v1 as repaired
from runners.drive.cards import week6_in14_in16_fixture_v1 as fixture
from runners.drive.cards import week6_in14_in16_run_v1 as oldrun
from runners.drive.cards import week5_in12_v1 as common


def balanced(plant=True, offset=0.):
    means = np.array([-3., -2., -1., 0., 0., 1., 2., 3.]) if plant else np.zeros(8)
    residual = np.array([-2., -1., 0., 1., 2.])*.5
    table = pd.DataFrame([{'prolific_id': f'w{i}', 'emotion': 'one',
                          'intensity': offset+mean+error}
                         for i, mean in enumerate(means) for error in residual])
    return repaired.matrix(table, [], 'intensity')


def closed_form(panel, counts):
    """Balanced intercept-only REML from between/within mean squares.

    Independent replicated groups give G=sum multiplicities, not unique keys.
    """
    selected = [(b, counts.get(b['key'], 0)) for b in panel['blocks'] if counts.get(b['key'], 0)]
    groups = sum(w for _, w in selected); m = selected[0][0]['n']
    grand = sum(w*float(b['y'].mean()) for b, w in selected)/groups
    within = sum(w*float(((b['y']-b['y'].mean())**2).sum()) for b, w in selected)
    between = sum(w*m*(float(b['y'].mean())-grand)**2 for b, w in selected)
    sigma = within/(groups*(m-1)); tau = max(0., (between/(groups-1)-sigma)/m)
    return tau/(tau+sigma)


@pytest.mark.parametrize('plant', [False, True])
@pytest.mark.parametrize('offset', [0., 5., 1000.])
def test_exact_balanced_reml_and_response_offset(plant, offset):
    panel = balanced(plant, offset); counts = dict.fromkeys(panel['keys'], 1)
    expected = closed_form(panel, counts)
    left, reason = repaired.writer_share(panel, counts)
    right, other = repaired.writer_share(panel, counts, True)
    assert reason is None and other is None
    assert abs(left-expected)<1e-8 and abs(right-expected)<1e-8
    common.compare(left, right)


def test_multiplicity_is_independent_writer_copies():
    panel = balanced(); counts = dict(zip(panel['keys'], [2, 0, 1, 3, 0, 1, 2, 1]))
    expected = closed_form(panel, counts)
    for independent in (False, True):
        value, reason = repaired.writer_share(panel, counts, independent)
        assert reason is None and abs(value-expected)<1e-8


@pytest.mark.parametrize('log_ratio', [0., .2, 1.5])
def test_analytic_score_has_independent_and_finite_difference_checks(log_ratio):
    panel = balanced(); blocks = [(b, 1) for b in panel['blocks']]
    f, score = repaired.profile(blocks, 1, log_ratio)
    g, direct = repaired.profile(blocks, 1, log_ratio, True)
    assert abs(f-g)<1e-9 and abs(score-direct)<1e-9
    # This is an engineering derivative check away from a minimum, not an
    # estimator or scientific tolerance. The production comparison stays 1e-7.
    h = 1e-5
    finite = (repaired.profile(blocks, 1, log_ratio+h, True)[0]
              -repaired.profile(blocks, 1, log_ratio-h, True)[0])/(2*h)
    assert abs(score-finite)<1e-6


def test_ragged_multicolumn_fixed_bootstrap_bank():
    frame = fixture.share_frame(.2, writers=60, reports=8, seed=1616)
    keep = [i for i in range(len(frame)) if i%8 < 3+(i//8)%6]
    frame = frame.iloc[keep].copy()
    frame['intensity'] += 5.
    panel = repaired.matrix(frame, list(repaired.frozen.original.APPRAISALS), 'intensity')
    for draw in range(8):
        counts = oldrun.resample(panel['keys'], 'IN16', draw, 2)
        left, reason = repaired.writer_share(panel, counts)
        right, other = repaired.writer_share(panel, counts, True)
        assert reason is None and other is None
        common.compare(left, right)


def test_declared_clearing_and_preparation_are_unchanged():
    assert repaired.prepare is repaired.frozen.prepare
    assert repaired.clearing is repaired.frozen.clearing
    prepared = repaired.prepare(fixture.clearing_frame(.2, writers=40))
    counts = dict.fromkeys(prepared['keys'], 1)
    value, reason = repaired.clearing(prepared['clearing'], counts)
    reference, other = repaired.clearing(prepared['clearing'], counts, True)
    assert reason is None and other is None and abs(value-.2)<1e-10
    common.compare(value, reference)


def test_invalid_support_rank_and_zero_residual_are_not_repaired():
    panel = balanced(); one = {panel['keys'][0]:80}
    assert repaired.writer_share(None, {}) == (None, 'no writer-share support')
    assert 'two independent' in repaired.writer_share(panel, one)[1]
    singular = copy.deepcopy(panel); singular['p'] = 2
    for b in singular['blocks']:
        b['x'] = np.ones((b['n'], 2)); b['xx'] = b['x'].T@b['x']
        b['xy'] = b['x'].T@b['y']; b['sx'] = b['x'].sum(0)
    assert repaired.writer_share(singular, dict.fromkeys(panel['keys'], 1))[0] is None
    zeros = balanced(False)
    for b in zeros['blocks']:
        b['y'][:] = 0.; b['xy'][:] = 0.; b['yy'] = b['sy'] = 0.
    assert repaired.writer_share(zeros, dict.fromkeys(zeros['keys'], 1))[0] is None


def test_bracket_failure_upper_boundary_and_nonfinite_are_explicit():
    assert repaired.polish(lambda t:(t*t, float('nan')), .2)[0] is None
    assert repaired.polish(lambda t:(t, 1.), .5)[1].startswith('REML derivative minimum unbracketed')
    assert 'upper bracket' in repaired.polish(lambda t:(-t, -1.), 12.-1e-7)[1]
    root, reason = repaired.polish(lambda t:((t-.6)**2, 2*(t-.6)), .600001)
    assert reason is None and abs(root-.6)<1e-12
    assert repaired.polish(lambda t:(t, 1.), float('nan'))[0] is None


def test_original_minimizer_failure_is_not_bypassed(monkeypatch):
    monkeypatch.setattr(repaired, 'minimize_scalar', lambda *a, **k:SimpleNamespace(success=False, fun=0., x=.1))
    panel = balanced()
    assert repaired.writer_share(panel, dict.fromkeys(panel['keys'], 1)) == (None, 'REML failed or rank deficient')


def test_original_comparison_tolerance_remains_strict():
    common.compare({'value':.5}, {'value':.5+0.99e-7})
    with pytest.raises(ValueError, match='Independent numerical formula differs'):
        common.compare({'value':.5}, {'value':.5+1.01e-7})


def test_new_runner_pins_frozen_dependency_and_rejects_old_binding(tmp_path):
    from runners.drive.cards import week6_in16_run_repair_v1 as run
    from runners.drive.cards import week5_engine_export_io as seal
    pins = run.dependencies()
    assert str(__import__('pathlib').Path(repaired.frozen.__file__).resolve()) in pins
    assert run.in16 is repaired and run.common.compare is common.compare
    assert run.settings('IN16', {'source_scope':'real-event-primary'})['seed'] == 20261107
    with pytest.raises(ValueError):run.settings('IN14', {'source_scope':'real-event-primary'})
    target = tmp_path/'DRAWS.json'
    saved = seal.state(target, 'old-dependency-binding', {'point':None, 'draws':[]})
    seal.checkpoint(target, saved)
    with pytest.raises(ValueError):seal.state(target, 'new-dependency-binding', {'point':None, 'draws':[]})
