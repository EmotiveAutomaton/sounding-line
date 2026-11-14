"""Focused clock-flag fixtures preserved from the reviewed combined suite."""
import pytest
from runners.drive.cards import week5_sg1_instrument_v1 as instrument
from runners.drive.cards import week5_sg1_fixture_v1 as fixture


def clock(ratio,tournament=True):
    value=None if ratio is None else ratio*100
    return dict(own_first_clock=value,initial=100,first_clock_ratio=None if value is None else value/100,
                increment=0,tournament=tournament)


def test_instrument_literal_boundary_bins_and_reference():
    rows=[clock(v) for v in [0,.45,.5,.55,1,None,-.1,1.1]]
    first=instrument.histogram(rows);second=instrument.histogram(rows,True)
    assert first==second
    expected=[0]*20
    for index in [0,9,10,11,19]:expected[index]+=1
    assert first['tournament']==dict(bins=expected,in_band=3,denominator=7,missing=1,outside=2)
    rows[0]['first_clock_ratio']=.5
    with pytest.raises(ValueError,match='ratio disagrees'):instrument.histogram(rows,True)


def test_instrument_exact_gate_missing_denominator_and_single_mode():
    hist=instrument.histogram([clock(.5)]*10+[clock(1)]*40+[clock(1,False)]*999+[clock(.5,False)])
    hist['other']['missing']=1000;hist['other']['outside']=2000;hist['other']['denominator']+=2000
    result=instrument.decision(hist)
    assert result['instrument_supported'] and not result['flag_admitted']
    assert result['non_tournament_valid_clock_denominator']==1000
    assert result['non_tournament_band_rate']==.001
    hist['other']['bins'][19]-=1;hist['other']['bins'][10]+=1;hist['other']['in_band']+=1
    assert not instrument.decision(hist)['instrument_supported']  # exactly 0.002 fails
    empty=instrument.histogram([clock(1)]*40)
    assert not instrument.decision(empty)['instrument_supported']
    assert instrument.decision(empty)['non_tournament_band_rate'] is None


def test_instrument_complete_table_handler_replay_and_owner_yield(tmp_path):
    fixture.source_case(tmp_path/'source')
    path=tmp_path/'source/output/PRIVATE_PLAYER_HISTORY.sqlite'
    inputs={'histories':dict(path=str(path),sha256=instrument.digest(path))};config=dict(constructed_fixture=True)
    output=tmp_path/'out'
    assert instrument.execute(output,inputs,config)['status']=='complete'
    assert instrument.verify(output,inputs,config)['independent_clock_arithmetic']
    waiting=tmp_path/'waiting';waiting.mkdir();(waiting/'YIELD_REQUEST.json').write_text('{}')
    assert instrument.execute(waiting,inputs,config)['status']=='yielded'
