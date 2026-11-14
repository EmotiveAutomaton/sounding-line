import json
import numpy as np
import pytest
from runners.drive.cards import week5_ch9_math_v1 as math9
from runners.drive.cards import week5_sg1_fixture_v1 as fixture
from runners.drive.cards.week5_ch_source import digest


def row(**changes):
    value=dict(score=0.,tournament=False,provisional_session=False,termination='Time forfeit',
        final_material_balance=2,last_move_checkmate=False,censored=False,seconds_to_next=200,
        duration_est=100,E=.7,form_before=0.,stop=False,rematch=True,index_in_session=2,
        losing_streak=1,start=1491004800,time_control='blitz')
    value.update(changes);return value


def test_packet_four_loss_kinds_are_literal():
    cases=[row(),row(termination='Normal',final_material_balance=-3),
           row(final_material_balance=-2),row(termination='Normal',final_material_balance=0)]
    assert [math9.kind(r) for r in cases]==[1,0,None,None]
    assert math9.kind(row(termination='Unknown',last_move_checkmate=True))==0
    assert math9.kind(row(tournament=True)) is None
    assert math9.kind(row(provisional_session=True)) is None


def test_quick_uses_estimated_end_and_refuses_overlap_missing_or_tail():
    assert math9.outcome(row(seconds_to_next=220))[0]==1
    assert math9.outcome(row(seconds_to_next=221))[0]==0
    assert math9.outcome(row(seconds_to_next=99))==(None,'next_start_precedes_estimated_end')
    assert math9.outcome(row(duration_est=None))[0] is None
    assert math9.outcome(row(censored=True))[0] is None


def test_full_fixed_effect_path_independent_reference_and_secondary_scopes():
    players={}
    for i in range(12):
        records=[]
        for j in range(40):
            flag=j%2==0
            records.append(row(termination='Time forfeit' if flag else 'Normal',final_material_balance=2 if flag else -3,
                seconds_to_next=200 if flag else 2000,stop=not flag,rematch=flag and j%4==0,
                index_in_session=j%7+1,losing_streak=j%3+1,form_before=j%5/10,
                start=1491004800+j*731+i*41,E=.7 if j%3 else .4))
        players[str(i)]=records
    first=math9.prepare(players);second=math9.prepare(players,True)
    assert first['points']['primary']['coefficients'][0]==pytest.approx(1.,abs=1e-8)
    assert second['points']['primary']['coefficients']==pytest.approx(first['points']['primary']['coefficients'],abs=1e-8)
    draws=[math9.draw(first,np.ones(12)) for _ in range(20)]
    result=math9.result(first,draws)
    assert result['census']['flagged_ahead']==240 and result['census']['outplayed']==240
    assert result['quick_rematches']['point'][0]==[None,.5]
    assert 'STOP_favourite' in result['estimates']


def test_complete_constructed_source_handler_and_independent_replay(tmp_path):
    from runners.drive.cards import week5_ch9_table_v1 as handler
    fixture.source_case(tmp_path/'source');path=tmp_path/'source/output/PRIVATE_PLAYER_HISTORY.sqlite'
    inputs={'histories':dict(path=str(path),sha256=digest(path))};config=dict(card='CH9',draws=2,constructed_fixture=True)
    assert handler.execute(tmp_path/'out',inputs,config)['status']=='complete'
    assert handler.verify(tmp_path/'out',inputs,config)['independent_formulas']
    value=json.loads((tmp_path/'out/SCIENCE.json').read_text())
    assert value['activation'][0]['channel']=='RAGE versus SHAME, analogy only'
