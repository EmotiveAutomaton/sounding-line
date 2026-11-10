from pathlib import Path
import numpy as np
import pytest
from runners.drive.cards import week5_md3_followup as study
from runners.drive.cards import week5_md3_conditional as conditional
from runners.drive.cards.week5_md3_followup_fixture import enumerated_objective


def small_panel():
    rng = np.random.default_rng(157)
    x = rng.normal(size=(4, 5, 2))
    y = np.asarray([[1, 0, 0, 0, 0], [1, 1, 0, 0, 0],
                    [1, 1, 1, 0, 0], [1, 1, 1, 1, 0]], float)
    return x, y


def test_conditional_exact_enumeration():
    x, y = small_panel()
    beta = np.asarray([.3, -.4])
    weights = np.asarray([1., 2., 0., 3.])
    actual = conditional.objective(beta, x, y, weights)
    expected = enumerated_objective(beta, x, y, weights)
    for a, b in zip(actual[:3], expected):
        np.testing.assert_allclose(a, b, atol=1e-12, rtol=0)


def test_conditional_offsets_cancel():
    x, y = small_panel()
    beta = np.asarray([.3, -.4])
    offset = np.arange(len(x))[:, None, None] * np.asarray([10., -4.])
    original = conditional.objective(beta, x, y)
    shifted = conditional.objective(beta, x + offset, y)
    for a, b in zip(original[:3], shifted[:3]):
        np.testing.assert_allclose(a, b, atol=1e-12, rtol=0)


def test_conditional_all_zero_one_uninformative():
    x, y = small_panel()
    y[0] = 0
    y[1] = 1
    assert conditional.objective(np.zeros(2), x, y)[3].tolist() == [2, 3]


def test_conditional_negative_cluster_weight_refuses():
    x, y = small_panel()
    with pytest.raises(ValueError, match='weights'):
        conditional.objective(np.zeros(2), x, y, np.asarray([1., -1., 1., 1.]))


def test_conditional_callback_can_checkpoint():
    x, y = small_panel()
    def pause():
        raise study.YieldRequested({'status': 'yielded'})
    with pytest.raises(study.YieldRequested):
        conditional.objective(np.zeros(2), x, y, check=pause)


@pytest.mark.parametrize('interval,outcome', [([.2, .3], 'supports'), ([-.3, -.2], 'against'),
                                           ([-.05, .05], 'inconclusive'), ([0., 0.], 'inconclusive')])
def test_exhaustive_directional_gate(interval, outcome):
    assert study.classify(interval, .1, {'both_sides_participants': 10000, 'rescue_choices': 10000}) == outcome


def test_floor_overrides_signed_interval():
    assert study.classify([1, 2], .1, {'both_sides_participants': 9999, 'rescue_choices': 10000}) == 'below floor, descriptive'


def test_changed_checkpoint_refuses(tmp_path):
    path = tmp_path / 'draw-0000.json'
    study.save_record(path, 'frozen', {'status': 'ok', 'values': [1., 2.]})
    with pytest.raises(ValueError, match='binding changed'):
        study.load_record(path, 'different')
    path.write_text('{}', encoding='utf8')
    with pytest.raises(ValueError, match='hash changed'):
        study.load_record(path, 'frozen')


def test_failure_retained_without_zero_imputation():
    def fail():
        raise ValueError('constructed rank deficient')
    value = study.safe_fit(fail)
    assert value == {'status': 'fit_failure', 'reason': 'constructed rank deficient'}
    assert 'values' not in value


def test_null_and_draw_counts_cannot_shrink(tmp_path):
    with pytest.raises(ValueError, match='full uncertainty'):
        study.perform(tmp_path, np.zeros((2, 30, 15)), {'standing_sd': 1}, 'MD3.p',
                      {'draws': 200}, {'constructed': True}, constructed=True)


def test_resource_request_propagates(tmp_path):
    (tmp_path / 'YIELD_REQUEST.json').write_text('{}')
    clock = study.RunClock(tmp_path, {})
    with pytest.raises(study.YieldRequested):
        clock.check()
