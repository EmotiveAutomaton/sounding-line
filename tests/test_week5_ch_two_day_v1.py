import math
import json
import shutil
from pathlib import Path
import numpy as np
import pytest
from runners.drive.cards import week5_ch_forecast_two_day_v1 as forecast
from runners.drive.cards import week5_ch8_math_v1 as ch8
from runners.drive.cards import week5_ch12_math_v1 as ch12
from runners.drive.cards import week5_ch_two_day_fixture_v1 as fixture
from runners.drive.cards import week5_ch_tables_two_day_v1 as handler
from runners.drive.cards import week5_sg1_fixture_v1 as source_fixture


def test_approved_split_has_both_roles_inside_original_prefix():
    keys=['0'+f'{i:063x}' for i in range(1000)]
    assert all(key[0]=='0' for key in keys)
    n=sum(forecast.calibration(key) for key in keys)
    assert 100<n<300
    expected=[__import__('hashlib').sha256(('SG1-forecast|20261112|'+key).encode()).hexdigest()[0] in '012' for key in keys]
    assert [forecast.calibration(key) for key in keys]==expected


def test_ordered_probability_hand_answer_and_independent_formula():
    p=forecast.probabilities([0.,math.log(math.log(3)),0.,0.],[[0.,0.]])[0]
    assert p==pytest.approx([.5,.25,.25])
    assert forecast.expectation([0.,math.log(math.log(3)),0.,0.],[[0.,0.]])[0]==pytest.approx(.375)
    assert forecast.probabilities_reference([0.,math.log(math.log(3)),0.,0.],[[0.,0.]])[0]==pytest.approx(p)
    # The packet's SG1 examples use this explicit Elo arithmetic, independently
    # from the later fitted ordered forecast.
    for gap,expected in [(100,.6401),(76,.6077),(-201,.2392),(195,.7545),(-2,.4971)]:
        assert 1/(1+10**(-gap/400))==pytest.approx(expected,abs=.0001)


def test_ordered_forecast_recovers_constructed_probabilities():
    truth=[-.7,math.log(1.4),.8,.2];x=[];y=[]
    for gap in [-2.,-1.,0.,1.,2.]:
        for black in [0.,1.]:
            probabilities=forecast.probabilities(truth,[[gap,black]])[0]
            counts=np.floor(probabilities*400).astype(int);counts[2]+=400-counts.sum()
            for category,n in enumerate(counts):x.extend([[gap,black]]*n);y.extend([category]*n)
    fitted=forecast.fit(x,y)
    predicted=forecast.probabilities(fitted['parameters'],x)
    assert np.max(abs(predicted-forecast.probabilities(truth,x)))<.01
    reference=forecast.fit(x,y,True)
    assert np.max(abs(forecast.probabilities_reference(reference['parameters'],x)-predicted))<1e-5


def test_decile_boundary_recalibration_and_missing_categories():
    expected=np.repeat(np.arange(.05,1,.1),10)
    good=forecast.decile_calibration(expected,expected)
    assert not good['use_decile_calibration']
    bad=forecast.decile_calibration(expected,np.minimum(expected+.04,1.))
    assert bad['use_decile_calibration'] and sum(bad['n'])==100
    with pytest.raises(ValueError,match='loss, draw and win'):
        forecast.fit([[0.,0.],[1.,1.],[2.,0.]],[0,0,2])


@pytest.mark.parametrize('effect',[.06,0.])
def test_ch8_packet_400_player_positive_and_null(effect):
    result=fixture.ch8_proof(effect)
    assert result['draws']==2000 and result['players']==400
    assert result['estimates']['primary']['invalid_draws']==0


def test_ch8_independent_fixed_effect_formula_and_literal_dummies():
    rng=np.random.default_rng(23);groups=np.repeat(np.arange(7),20)
    x=rng.normal(size=(len(groups),3));fixed=np.linspace(-2,2,7)
    beta=np.array([.06,-.1,.2]);y=fixed[groups]+x@beta
    xx=[];xy=[];xr=[];yr=[]
    for g in range(7):
        a,b=ch8.block(y[groups==g],x[groups==g]);xx.append(a);xy.append(b)
        a,b=ch8.block(y[groups==g],x[groups==g],True);xr.append(a);yr.append(b)
    s=dict(xx=np.array(xx),xy=np.array(xy));r=dict(xx=np.array(xr),xy=np.array(yr))
    dense=np.column_stack((np.eye(7)[groups],x));expected=np.linalg.lstsq(dense,y,rcond=None)[0][-3:]
    assert ch8.coefficients(s)==pytest.approx(expected,abs=1e-10)
    assert ch8.coefficients(r,reference=True)==pytest.approx(expected,abs=1e-10)
    weights=np.arange(1,8)
    repeated=np.repeat(np.arange(len(groups)),weights[groups])
    expected=np.linalg.lstsq(dense[repeated],y[repeated],rcond=None)[0][-3:]
    assert ch8.coefficients(s,weights)==pytest.approx(expected,abs=1e-10)


def test_ch8_does_not_invent_missing_reference_or_drop_confounding_control():
    players=fixture.ch8_players(people=2)
    missing={p:[r for r in rows if r['E']>.35] for p,rows in players.items()}
    with pytest.raises(ValueError,match='not identifiable conditional'):
        ch8.statistics(missing,sorted(missing),('blitz',))
    for rows in players.values():
        for row in rows:row['form_before']=float(row['E']>=.65)
    with pytest.raises(ValueError,match='not identifiable conditional'):
        ch8.statistics(players,sorted(players),('blitz',))


def test_ch12_hand_indices_and_whole_session_halves():
    rows=[]
    for half in [0,1]:
        for session in range(4):
            for score,e,stop in [(1.,.8,False),(1.,.7,True),(0.,.2,False),(0.,.5,True),(0.,.8,True)]:
                rows.append(dict(score=score,E=e,stop=stop,censored=False,start=ch12.SPLIT+(-10000 if half==0 else 10000)+session*100,
                    session_id=f'{half}:{session}',provisional_session=False))
    expected=[.5,2/3-.5,1/.6]  # OLS on (.2,0),(.5,1),(.8,1): slope=5/3.
    a=ch12.player(rows)
    assert a['full'][0]==pytest.approx(expected)
    assert a['odd_even'][0][0]==pytest.approx(expected)
    assert a['counts'][0]['sessions']==4
    assert ch12.player(rows,True)['full'][0]==pytest.approx(expected)


def test_ch12_three_2000_player_stability_worlds_and_independent_formula():
    for world in fixture.ch12_proof().values():
        reference=ch12.evaluate(world['prepared'],reference=True)
        handler.equivalent(world['estimate'],reference)


def test_ch12_zero_variance_and_undefined_indices_not_stable():
    prepared=dict(names=[str(i) for i in range(400)],full=np.ones((400,2,3)),halves=np.ones((400,2,2,3)),
                  status='case_met',support={},provisional_rows_retained=0)
    point=ch12.evaluate(prepared)
    assert all(point[name]['stability'] is None for name in ch12.INDEX_NAMES)
    result=ch12.result(prepared,[point]*2000)
    assert result['indices']['GAIN']['verdict']=='inconclusive'
    assert not result['indices']['GAIN']['variance_gate_pass']


@pytest.mark.parametrize('card',['CH8','CH12'])
def test_complete_constructed_handler_independent_replay(tmp_path,card):
    source_fixture.source_case(tmp_path/'source')
    path=tmp_path/'source/output/PRIVATE_PLAYER_HISTORY.sqlite'
    inputs={'histories':dict(path=str(path),sha256=handler.digest(path))}
    config=dict(card=card,constructed_fixture=True,draws=2)
    result=handler.execute(tmp_path/'consumer',inputs,config)
    assert result['status']=='complete'
    assert handler.verify(tmp_path/'consumer',inputs,config)['independent_formulas']
    science=json.loads((tmp_path/'consumer/SCIENCE.json').read_text())
    assert science['constructed_fixture'] and isinstance(science['activation'],list)


def test_table_quantum_sealed_copy_full_replay_and_tamper_refusal(tmp_path):
    source_fixture.source_case(tmp_path/'source')
    path=tmp_path/'source/output/PRIVATE_PLAYER_HISTORY.sqlite'
    inputs={'histories':dict(path=str(path),sha256=handler.digest(path))}
    config=dict(card='CH12',constructed_fixture=True,draws=2,max_new_draws=1)
    first=tmp_path/'attempt1/output'
    assert handler.execute(first,inputs,config)['status']=='yielded'
    assert len(json.loads((first/'TABLE_CHECKPOINT.json').read_text())['draws'])==1
    second=tmp_path/'attempt2/output';shutil.copytree(first,second)
    copied={p.relative_to(second).as_posix():handler.digest(p) for p in second.rglob('*') if p.is_file()}
    (second.parent/'RESUMED_FROM.json').write_text(json.dumps(dict(copied=copied)))
    assert handler.execute(second,inputs,config)['status']=='complete'
    assert handler.verify(second,inputs,config)['all_whole_player_draws_recomputed']
    science=second/'SCIENCE.json';science.write_text(science.read_text()+' ')
    with pytest.raises(ValueError,match='Sealed source changed'):handler.verify(second,inputs,config)


def test_owner_yield_and_missing_predictor_boundary(tmp_path):
    source_fixture.source_case(tmp_path/'source')
    path=tmp_path/'source/output/PRIVATE_PLAYER_HISTORY.sqlite'
    inputs={'histories':dict(path=str(path),sha256=handler.digest(path))}
    target=tmp_path/'yielded';target.mkdir();(target/'YIELD_REQUEST.json').write_text('{}')
    answer=handler.execute(target,inputs,dict(card='CH12',constructed_fixture=True,draws=2))
    assert answer['status']=='yielded' and not (target/'SCIENCE.json').exists()
    assert forecast.predict(dict(time_control='blitz',score=0,rating=None,opponent_rating=1500),
                            dict(controls={'blitz':dict(status='complete')})) is None
