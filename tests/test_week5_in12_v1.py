import numpy as np
import pandas as pd
import pytest
from runners.drive.cards import week5_in12_v1 as study
from runners.drive.cards import week5_in12_fixture_v1 as fixture


def test_two_exact_permitted_item_polarities_and_ranges():
    assert study.SOURCE_COLUMNS == ['text_id', 'prolific_id', 'anxious', 'calm']
    assert study.math.item_score(1, 7) == 1
    assert study.math.item_score(7, 1) == 7
    assert study.math.item_score(4, 4) == 4
    with pytest.raises(ValueError):
        study.math.item_score(8, 1)


def test_source_writer_conflicts_missingness_and_complete_replay(tmp_path):
    assert fixture.projection_chain(tmp_path/'source')['passed']


def test_packet_common_mixed_and_zero_planted_coefficients():
    worlds = fixture.analytic_worlds()
    assert abs(worlds['common']['value']['pooled']-.2) < 1e-9
    assert abs(worlds['mixed']['value']['pooled']-2*.4/6) < .01
    assert worlds['mixed']['value']['spread'] > .18
    assert abs(worlds['null']['value']['pooled']) < 1e-9


def test_complete_2000_common_and_mixed_worlds(tmp_path):
    for name, slopes in [('common', (.2,)*6), ('mixed', (.4, .4, 0., 0., 0., 0.))]:
        assert fixture.chain(tmp_path/name, slopes)['passed']


def test_complete_2000_zero_world_and_independent_pauses(tmp_path):
    assert fixture.chain(tmp_path/'null', (0.,)*6, people=304)['passed']


def test_equal_writer_pair_weights_and_optional_support():
    frame, _ = study.math.fixed_table(fixture.world(people=320))
    negative, cross, eligible = study.math.pair_rows(frame)
    assert eligible == 320
    for rows in (negative, cross):
        weights = pd.DataFrame(rows, columns=['person', 'x', 'y', 'weight']).groupby('person').weight.sum()
        assert np.allclose(weights, 1)
    counts = dict.fromkeys(sorted(frame.prolific_id.unique()), 1)
    for rows in (negative, cross):
        assert abs(study.math.correlation(rows, counts)-study.math.correlation(rows, counts, True)) < 1e-12
    prepared = study.math.prepare(frame)
    answer = study.math.evaluate(prepared, counts)
    assert 'within_writer_correlation_difference' in answer['value']
    one = {next(iter(counts)): 320}
    refused = study.math.evaluate(prepared, one)
    assert refused['value']['within_writer_correlation_difference'] is None


def test_failed_draws_are_preserved_no_partial_uncertainty():
    point = {'value': {'pooled': .2}, 'failures': {}}
    draws = [{'value': {'pooled': .2}, 'failures': {}} for _ in range(2000)]
    draws[31] = {'value': {'pooled': None}, 'failures': {'pooled': 'rank deficient'}}
    result = study.summarize('pooled', point, draws, 50)
    assert result['failed_draws'] == [31] and 'interval' not in result
    with pytest.raises(ValueError):
        study.summarize('pooled', point, draws[:2], 50)


def test_small_writer_support_has_no_population_claim():
    point = {'value': {'pooled': .2}, 'failures': {}}
    draws = [point]*2000
    result = study.summarize('pooled', point, draws, 19)
    assert result['status'] == 'below floor, descriptive' and 'outcome' not in result


def test_serialized_config_and_changed_input_refusal(tmp_path):
    with pytest.raises(ValueError):
        study.settings({'phase': 'IN12', 'draws': 200})
    with pytest.raises(ValueError):
        study.load_source({})
    with pytest.raises(ValueError):
        study.load_prepared({})
    frame = fixture.world(); config = {'phase': 'IN12', 'max_new_draws': 1}
    with fixture.table_boundary(frame):
        assert study.execute(tmp_path, {}, config)['status'] == 'yielded'
    frame.loc[0, 'N'] += .01
    with fixture.table_boundary(frame), pytest.raises(ValueError, match='binding changed'):
        study.execute(tmp_path, {}, config)


def test_independent_rows_recover_weighted_cluster_solution():
    frame = fixture.world(); prepared = study.math.prepare(frame)
    weight = study.math.resample(prepared['keys'], 17)
    study.compare(study.math.evaluate(prepared, weight), study.math.evaluate(prepared, weight, True))
