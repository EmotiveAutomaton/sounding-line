import json
import numpy as np
import pytest
from runners.drive.cards import week5_ch10_features_v1 as features
from runners.drive.cards import week5_ch10_math_v1 as card
from runners.drive.cards import week5_ch10_fixture_v3 as fixture
from runners.drive.cards import week5_ch_table_regression_v2 as regression
from runners.drive.cards import week5_sg1_fixture_v1 as source_fixture
from runners.drive.cards.week5_ch_tables_two_day_v3 import equivalent


def test_exact_frequency_cell_matches_expanded_binary_cross_products():
    all_cells=fixture.cells('primary');rows=[all_cells[i] for i in [0,1,16,17]]
    compressed=[(r['berserk'],card.analytic(r,'primary')[1]) for r in rows]
    # Use the literal loss10/100 and win14/100 frequencies, with actual
    # binary records, independently of the frequency-world implementation.
    expanded=[(y,x) for row,(_,x) in zip(rows,compressed) for y in ([1.]*(10 if row['previous_score']==0 else 14)+[0.]*(90 if row['previous_score']==0 else 86))]
    a,b=regression.checked.block(np.array([r[0] for r in expanded]),np.array([r[1] for r in expanded]))
    c,d=regression.checked.block(np.array([r[0] for r in compressed]),np.array([r[1] for r in compressed]),True)
    assert np.allclose(a,c*100,atol=1e-8) and np.allclose(b,d*100,atol=1e-8)


@pytest.mark.parametrize('world',['primary','decay'])
def test_complete_300_player_2000_draw_world_and_independent_replay(world):
    actual=fixture.prove(world);replay=fixture.prove(world,True)
    assert actual['draws']==2000 and actual['players']==300
    assert actual['constructed_fixture'] and actual['by_construction'] and actual['activation']==[]
    assert actual['record_kind']=='run'
    equivalent(actual,replay)


def test_lag_ratio_zero_denominator_not_clipped_or_redrawn():
    assert card.decay([0.,1.,1.,1.,-.02,-.016,-.0128,-.01024])==dict(win=None,loss=.64,difference=None)
    assert card.decay(None)==dict(win=None,loss=None,difference=None)


def test_registered_secondaries_and_approved_bonus_columns():
    row=fixture.cells('primary')[0]
    assert 'win_bonus' in card.columns('primary')[0]
    assert 'streak_state' not in card.columns('primary')[0]
    failed=card.analytic(dict(row,previous_score=0,previous_berserk=1.),'failed_claim')
    assert failed[1][0]==1 and card.columns('failed_claim')[0].count('previous_berserk')==0
    assert card.analytic(dict(row,previous_score=1,previous_E=.5),'win_surprise') is None
    assert card.analytic(dict(row,lag_scores=[1,None,0,.5]),'time_courses') is None


def test_complete_tiny_source_handler_replay_and_instrument_hold(tmp_path):
    from runners.drive.cards import week5_ch10_table_v1 as handler
    source_fixture.source_case(tmp_path/'source');path=tmp_path/'source/output/PRIVATE_PLAYER_HISTORY.sqlite'
    inputs={'histories':dict(path=str(path),sha256=handler.digest(path))};config=dict(card='CH10',draws=2,constructed_fixture=True)
    assert handler.execute(tmp_path/'out',inputs,config)['status']=='complete'
    assert handler.verify(tmp_path/'out',inputs,config)['independent_formulas']
    science=json.loads((tmp_path/'out/SCIENCE.json').read_text())
    assert science['curator_decision']=='Use the 2+ win bonus control (recommended)'
    assert not science['original_categorical_model']['fitted']
    with pytest.raises(ValueError,match='instrument admission'):
        handler.authenticate({},dict(card='CH10',instrument_admitted=False),tmp_path)


def test_unsupported_frequency_world_keeps_binary_trial_denominators():
    prep=fixture.prepared('primary')
    assert 'unsupported' in prep['points']['time_courses']
    assert prep['points']['time_courses']['rows']==48*fixture.FREQUENCY*fixture.PEOPLE
