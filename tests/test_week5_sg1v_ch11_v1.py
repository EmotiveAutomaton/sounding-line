import json,math
from collections import Counter
import numpy as np
import pytest
from runners.drive.cards import week5_sg1_instrument_v1 as instrument
from runners.drive.cards import week5_ch11_math_v1 as math11
from runners.drive.cards import week5_ch_table_regression_v1 as regression
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


def test_ch11_packet_hand_probabilities_thresholds_and_independent_formula():
    counts=Counter(e2e4=28,d2d4=8,c2c4=4)
    for move,expected in [('e2e4',.388),('d2d4',1.598),('c2c4',2.234),('g1f3',4.431)]:
        actual=math11.habit(counts,move)
        assert actual['departure']==pytest.approx(expected,abs=.001)
        assert actual==pytest.approx(math11.habit(counts,move,True))
    assert math11.habit(Counter(e2e4=19),'e2e4')['departure'] is None
    assert math11.habit(Counter(e2e4=29),'d2d4')['novel'] is None
    assert math11.habit(Counter(e2e4=30),'d2d4')['novel']==1


def rows():
    moves=['e2e4']*28+['d2d4']*8+['c2c4']*4+['g1f3','e2e4','d2d4','c2c4','e2e4','d2d4']
    result=[]
    for i,move in enumerate(moves):
        result.append(dict(game=str(i),start=1491004800+i*600,month='2017-04',time_control='blitz',colour='white',
            own_first_move=move,opponent_first_move=None,score=0. if i%2 else 1.,E=.7,
            surprise=-.7 if i%2 else .3,censored=i==len(moves)-1,index_in_session=i+1,
            rating=1500,opponent_rating=1400,next_row={'game':str(i+1)} if i<len(moves)-1 else None))
    return result


def test_ch11_actual_sequence_past_only_contexts_and_calm_distinction():
    data=rows();pairs,count=math11.choices(data)
    assert pairs[20]['earlier']==40 and pairs[20]['novel']==1
    assert pairs[20]['departure']==pytest.approx(-math.log(.5/42))
    prefix,_=math11.choices(data[:43]);later,_=math11.choices(data)
    assert prefix==later[:len(prefix)]
    assert not any(r['calm'] and r['favourite'] and r['loss'] for r in pairs)
    assert math11.context(dict(data[0],colour='black',opponent_first_move='e2e4'))!=math11.context(data[0])
    assert math11.context(dict(data[0],time_control='rapid'))!=math11.context(data[0])
    assert math11.context(dict(data[0],colour='black',opponent_first_move=None)) is None


def test_ch11_calm_means_retain_players_without_five_loud_losses():
    data=rows()
    for row in data:row.update(E=.5,score=.5,surprise=0.)
    prepared=math11.prepare({'constructed':data})
    assert prepared['case']['eligible_players']==0
    assert len(prepared['names'])==1 and prepared['calm'].sum()>0
    answer=math11.result(prepared,[math11.draw(prepared,np.ones(1))]*2)
    assert answer['calm_secondary']['calm']['point'][0] is not None
    assert 'unsupported' in answer['estimates']['primary']


def test_remaining_cards_regression_known_answer_and_rank_refusal():
    rng=np.random.default_rng(77);groups=[]
    for i in range(20):
        x=rng.normal(size=(30,3));y=.04*x[:,0]+.3*x[:,1]-.2*x[:,2]+i
        groups.append([(float(a),b.tolist()+[0.]) for a,b in zip(y,x)])
    for reference in [False,True]:
        stat,point=regression.prepare(iter(groups),['target','c1','c2','zero'],reference=reference)
        assert point['coefficients']==pytest.approx([.04,.3,-.2],abs=1e-10)
        assert stat['columns']==['target','c1','c2']
    invalid=[[(y,[x[0],x[0]]) for y,x in group] for group in groups]
    _,point=regression.prepare(iter(invalid),['target','same_control'])
    assert 'unsupported' in point and point['rows']==600


def test_ch11_complete_constructed_handler_replay(tmp_path):
    from runners.drive.cards import week5_ch11_table_v1 as handler
    fixture.source_case(tmp_path/'source')
    path=tmp_path/'source/output/PRIVATE_PLAYER_HISTORY.sqlite'
    inputs={'histories':dict(path=str(path),sha256=instrument.digest(path))}
    config=dict(card='CH11',constructed_fixture=True,draws=2)
    assert handler.execute(tmp_path/'out',inputs,config)['status']=='complete'
    assert handler.verify(tmp_path/'out',inputs,config)['independent_formulas']
    science=json.loads((tmp_path/'out/SCIENCE.json').read_text())
    assert science['activation'][0]['channel']=='PLAY'
