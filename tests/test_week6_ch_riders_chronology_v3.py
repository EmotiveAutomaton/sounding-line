"""Literal chronology boundaries; never reads participant or game-source rows.

DESIGN CHECK: LESSONS 2/3/5. Unknown or tied start times cannot establish order.
Missing records anywhere in the list refuse the entire player's chronological
projection under null and alternative, while full counts remain auditable.
"""
import copy
import math
import pytest
from runners.drive.cards import week6_ch_riders_fields_v1 as original
from runners.drive.cards import week6_ch_riders_fields_v3 as fixed


def row(i,start):
    return dict(game=f'constructed-{i}',start=start,time_control='blitz',colour='white',
                own_first_move='e2e4' if i%2 else 'd2d4',opponent_first_move=None,
                tournament=True,tournament_id='constructed-arena',duration_est=30.,
                score=float(i%2),duration_status='constructed',berserk_candidate=False)


def histories():return [row(i,i*100.) for i in range(50)]


@pytest.mark.parametrize('index',[0,20,49])
@pytest.mark.parametrize('missing',[None,float('nan'),float('inf')])
def test_any_unorderable_position_holds_both_comparisons_and_keeps_counts(index,missing):
    values=histories();values[index]['start']=missing
    def no_forecast(_):raise AssertionError('Unknown chronology must refuse before forecasting')
    pairs,census=fixed.arena_pairs('constructed-player',values,no_forecast)
    choices,choice_census=fixed.opening_choices(list(reversed(values)))
    assert pairs==choices==[]
    for counts in (census,choice_census):
        assert counts['source_games']==50 and counts['missing_start']==1
        assert counts['chronology_unsupported_players']==1
        assert counts['chronology_excluded_games']==50
    assert census['chronology_unsupported_analysis_players']==1


def test_tied_times_are_not_ordered_by_game_id():
    values=histories();values[31]['start']=values[30]['start']
    for payload in (values,list(reversed(values))):
        pairs,census=fixed.arena_pairs('constructed-player',payload,lambda _: .5)
        choices,counts=fixed.opening_choices(payload)
        assert pairs==choices==[]
        assert census['tied_start_games']==counts['tied_start_games']==2
        assert census['chronology_excluded_games']==counts['chronology_excluded_games']==50


def test_calibration_player_with_missing_order_cannot_supply_donor_timing():
    values=histories();values[20]['start']=None
    pairs,census=fixed.arena_pairs('constructed-calibration-player',values,lambda _: .5,analysis=False)
    assert pairs==[] and census['chronology_unsupported_calibration_players']==1
    assert 'chronology_unsupported_analysis_players' not in census


def test_defensible_interleaved_input_preserves_original_pairs_and_options():
    values=histories();interleaved=values[::2]+values[1::2]
    a,ac=fixed.arena_pairs('constructed-player',interleaved,lambda _: .5)
    b,bc=original.arena_pairs('constructed-player',values,lambda _: .5)
    assert a==b
    assert {k:v for k,v in ac.items() if k!='tied_start_games'}==bc
    a,ac=fixed.opening_choices(interleaved);b,bc=original.opening_choices(values)
    assert a==b
    assert {k:v for k,v in ac.items() if k!='tied_start_games'}==bc
    assert 'chronology_unsupported_players' not in ac


def test_missing_interleaved_game_exposes_old_gap_without_salvage():
    values=[row(0,0),row(1,None),row(2,180)]
    old,_=original.arena_pairs('constructed-player',values,lambda _: .5)
    assert len(old)==1 and old[0]['game']=='constructed-0' and old[0]['next_game']=='constructed-2'
    new,census=fixed.arena_pairs('constructed-player',values,lambda _: .5)
    assert new==[] and census['source_games']==census['chronology_excluded_games']==3


def test_duplicate_identity_remains_integrity_error_even_with_missing_time():
    values=histories();values[20]=copy.deepcopy(values[10]);values[20]['start']=None
    with pytest.raises(ValueError,match='Duplicate player-game'):
        fixed.arena_pairs('constructed-player',values,lambda _: .5)
    with pytest.raises(ValueError,match='Duplicate player-game'):
        fixed.opening_choices(values)
