import numpy as np
import pytest
from runners.drive.cards import week5_in11_v1 as study
from runners.drive.cards import week5_in11_fixture_v1 as fixture


def test_curator_fixed_order_no_elapsed_seconds_or_none_zero():
    assert study.math.RANKS == dict(seconds=1, minutes=2, hours=3, days=4, weeks=5)
    assert study.math.rank('I had none', True) is None
    with pytest.raises(ValueError):
        study.math.rank('I had none')
    with pytest.raises(ValueError):
        study.math.rank('3600')
    assert study.SOURCE_COLUMNS == ['text_id', 'prolific_id', 'event_duration', 'emotion_duration']


def test_source_categories_exclusions_and_independent_reentry(tmp_path):
    assert fixture.projection_chain(tmp_path/'source')['passed']


def test_six_style_items_exclude_both_indices():
    assert len(study.math.STYLE) == 6
    assert not set(study.math.STYLE) & set(study.math.JUMP+study.math.NO_REMEDY)


def test_both_outcomes_and_indices_standardized_within_prompt():
    frame = fixture.world(); prepared = study.math.prepare(frame)
    independent = study.math.prepare(frame, True)
    assert np.allclose(prepared['x'], independent['x']) and np.allclose(prepared['y'], independent['y'])
    cursor = 0
    for size in prepared['counts'].values():
        assert np.allclose(prepared['y'][cursor:cursor+size].mean(axis=0), 0)
        assert np.allclose(prepared['y'][cursor:cursor+size].std(axis=0, ddof=1), 1)
        cursor += size


def test_full_2000_crossover_and_zero_worlds(tmp_path):
    for name, contrast in [('positive', .3), ('null', 0.)]:
        assert fixture.chain(tmp_path/name, contrast)['passed']


def test_independent_rows_recover_weighted_design_and_component_order():
    prepared = study.math.prepare(fixture.world()); weights = study.math.draw(len(prepared['keys']), 39)
    a = study.math.evaluate(prepared, weights); b = study.math.evaluate(prepared, weights, True)
    study.compare(a, b)
    point = study.math.evaluate(prepared, np.ones(len(prepared['keys'])))['value']
    assert np.allclose(point, [.3, .15, 0., 0., .15], atol=1e-9)


def test_failed_draws_and_partial_banks_cannot_receive_intervals():
    point = {'value': [0., 0., 0., 0., 0.]}; draws = [point]*2000
    draws[51] = {'failure': 'rank deficient'}
    result = study.summarize(point, draws, 100)
    assert result['failed_draws'] == [51] and 'primary' not in result
    with pytest.raises(ValueError):
        study.summarize(point, draws[:10], 100)


def test_small_support_constant_scale_and_scope_refusals():
    point = {'value': [0., 0., 0., 0., 0.]}
    result = study.summarize(point, [point]*2000, 19)
    assert result['status'] == 'below floor, descriptive' and 'outcome' not in result['primary']
    with pytest.raises(ValueError):
        study.math.z([1., 1., 1.])
    with pytest.raises(ValueError):
        study.settings({'phase': 'IN11', 'draws': 200})
    with pytest.raises(ValueError):
        study.load_source({})


def test_changed_input_refuses_checkpoint_reentry(tmp_path):
    frame = fixture.world(); config = {'phase': 'IN11', 'max_new_draws': 1}
    with fixture.table_boundary(frame):
        assert study.execute(tmp_path, {}, config)['status'] == 'yielded'
    frame.loc[0, 'intensity'] += .01
    with fixture.table_boundary(frame), pytest.raises(ValueError, match='binding changed'):
        study.execute(tmp_path, {}, config)
