import json
import math
import shutil
import numpy as np
import pytest
from runners.drive.cards import week5_ch7_math_v1 as original
from runners.drive.cards import week5_ch7_math_v3 as m
from runners.drive.cards import week5_ch7_reference_v1 as ref
from runners.drive.cards import week5_ch7_v3 as handler
from runners.drive.cards import week5_sg1_carried_v1 as old_bridge
from runners.drive.cards import week5_sg1_carried_v3 as bridge
from runners.drive.cards import week5_ch7_numerical_fixture_v4 as native
from runners.drive.cards.week5_ch_source import digest


def blocks():
    rng=np.random.default_rng(731)
    answer=[]
    for person in range(8):
        b=np.zeros((64,18))
        b[:,1]=-rng.uniform(0,2,64);b[:,2]=rng.uniform(0,2,64)
        b[:,3:11]=rng.normal(0,1,(64,8));b[:,4]=rng.integers(0,2,64)
        b[:,5]=rng.integers(0,2,64);b[:,11]=-rng.uniform(0,3,64)
        b[:,12]=np.tile([0,1],32);b[:,13]=1-b[:,12]
        b[:,14]=np.tile([2,2,4,4],16);b[:,16]=1;b[:,17]=1
        b[:,0]=.5-.15*b[:,1]-.04*b[:,2]+.03*b[:,3]+person/100
        b[:,15]=.08+.01*b[:,1]-.02*b[:,2]+person/1000
        answer.append(b)
    return answer


def test_hand_probabilities_draw_fit_and_positive_update():
    np.testing.assert_allclose(m.expected_score([-400,0,400]),[1/11,.5,10/11],atol=1e-15)
    np.testing.assert_allclose(m.result_probabilities(.5,.25),[.375,.25,.375],atol=0)
    assert m.fit_draw_fraction(np.full(8,.5),[0,0,1,1,-1,-1,1,-1])['fraction']==pytest.approx(.25,abs=1e-6)
    assert m.fit_draw_fraction(np.full(4,.5),[0,0,0,0])['fraction']==1
    trace=np.zeros((8,11));trace[:,3:5]=1500;trace[:,6]=[-1,1,0,-1,1,0,-1,1]
    trace[:,5]=10*trace[:,6];trace[:,7]=1
    rows=np.zeros((8,18));rows[:,0]=1
    result=m.fit_null(dict(trace=trace,rows=rows))['0']
    assert result['update_scale']==20 and result['update_rmse']==0
    assert result['play']['constant']==1
    trace[:,5]*=-1
    with pytest.raises(ValueError,match='not positive'):m.fit_null(dict(trace=trace,rows=rows))


def test_draw_likelihood_heterogeneous_expectations_stationary_score():
    p=np.array([.1,.2,.3,.4,.5,.6,.7,.8,.9]*8)
    results=np.tile([0,1,-1,0,1,-1,1,-1,1],8)
    fit=m.fit_draw_fraction(p,results)
    fraction=fit['fraction'];a=2*np.minimum(p,1-p);draw=results==0
    derivative=-sum(1/fraction for _ in a[draw])+sum(v/(1-fraction*v) for v in a[~draw])
    assert abs(derivative)<1e-3
    likelihood=-sum(math.log(fraction*v) for v in a[draw])-sum(math.log(1-fraction*v) for v in a[~draw])
    assert likelihood==pytest.approx(fit['negative_log_likelihood'],abs=1e-10)


def test_own_logistic_balanced_intercept_and_separation_refusal():
    rows=np.zeros((20,18));rows[:,0]=np.tile([0,1],10)
    fit=m.fit_playing_on(rows)
    assert fit['kept']==[0] and fit['beta']==pytest.approx([0])
    rows[:,3]=rows[:,0]
    with pytest.raises(ValueError,match='singular|separated|unconverged'):m.fit_playing_on(rows)


@pytest.mark.parametrize('constant',[0.,1.])
def test_independent_null_recurrence_exposes_and_repairs_session_reset(constant):
    trace=np.zeros((6,11));trace[:,1]=[0,0,0,1,1,1];trace[:,2]=np.arange(6)*600
    trace[:,3]=1000;trace[:,4]=10000;trace[:,7]=1
    parameters={'0':dict(update_scale=20,draw=dict(fraction=0),play=dict(constant=constant))}
    data=dict(trace=trace)
    expected=ref.simulate(trace,parameters,17)
    repaired=m.simulate(data,parameters,17)
    np.testing.assert_allclose(repaired,expected,atol=1e-11,equal_nan=True)
    assert repaired[:,6].tolist()==([1]*6 if constant==0 else [1,2,3,1,2,3])
    assert not np.array_equal(original.simulate(data,parameters,17)[:,6],expected[:,6])


def test_independent_null_recurrence_nonconstant_two_controls_and_masks():
    trace=np.zeros((80,11));trace[:,0]=np.repeat([0,1],40)
    trace[:,1]=np.tile(np.repeat([0,1],20),2);trace[:,2]=np.arange(80)*777
    trace[:,3]=1500;trace[:,4]=np.tile([1300,1500,1700,1600],20)
    trace[:,7]=1;trace[::9,7]=0;trace[39::40,8]=1;trace[:,10]=1
    fit=dict(update_scale=18,draw=dict(fraction=.2),play=dict(
        kept=[0,1,2,3,4,5],scale=[1,4,1,1,1,1],beta=[.3,-.15,.1,.05,.02,-.04]))
    parameters={'0':fit,'1':fit}
    np.testing.assert_allclose(m.simulate(dict(trace=trace),parameters,551),
                              ref.simulate(trace,parameters,551),atol=1e-9,rtol=1e-11,equal_nan=True)


@pytest.mark.parametrize('kind',['recent','window_slope','new_best','pace','provisional_start'])
def test_all_declared_estimands_against_independent_dummy_and_raw_sums(kind):
    data=blocks();s=m.sufficient_blocks(data,kind)
    expected=ref.dense_fit(data,kind,s['kept'])
    np.testing.assert_allclose(m.coefficients(s),expected,atol=1e-9,rtol=1e-9)
    xx,xy,gains=ref.raw_statistics(data,kind,s['kept'])
    np.testing.assert_allclose(s['xx'],xx,atol=1e-9)
    np.testing.assert_allclose(s['xy'],xy,atol=1e-9)
    if kind=='new_best':assert gains==[2.,4.]
    copies=np.array([2,0,1,3,0,1,0,1])
    np.testing.assert_allclose(m.coefficients(s,copies),ref.dense_fit(data,kind,s['kept'],copies),atol=1e-9)


def test_full_2000_whole_player_bootstrap_independent_quantiles_and_sensitivity():
    data=blocks();s=m.sufficient_blocks(data);xx,xy,_=ref.raw_statistics(data,'recent',s['kept'])
    rng=np.random.default_rng(m.SEED);values=[];expected=[]
    for _ in range(2000):
        selected=rng.integers(0,len(data),len(data));weights=np.bincount(selected,minlength=len(data))
        actual=m.coefficients(s,weights);independent=ref.weighted_fit(xx,xy,[sum(selected==i) for i in range(len(data))])
        np.testing.assert_allclose(actual,independent,atol=1e-9)
        values.append(dict(recent=dict(coefficients=actual.tolist(),contrast=m.contrast(actual))))
        expected.append(abs(independent[0])-abs(independent[1]))
    out=handler.intervals(values,'recent',dict(contrast=.11))
    ci,se=ref.interval(expected)
    np.testing.assert_allclose(out['interval'],ci,atol=1e-10)
    assert out['bootstrap_se']==pytest.approx(se,abs=1e-10)
    values[7]['recent']=dict(invalid=True)
    assert handler.intervals(values,'recent',dict(contrast=.11))['interval'] is None


def test_targets_confounded_with_required_controls_refuse_without_dropping_control():
    data=blocks()
    for b in data:b[:,4]=b[:,1]
    # Independent full design has a duplicate column and cannot identify below.
    with pytest.raises(ValueError,match='singular'):ref.dense_fit(data,'recent',list(range(10)))
    assert original.sufficient_blocks(data)['kept'][:2]==[0,1]
    with pytest.raises(ValueError,match='conditional'):m.sufficient_blocks(data)


def test_exact_zero_nuisance_columns_do_not_create_rank_from_roundoff():
    data=blocks()
    for b in data:b[:,3:11]=0
    s=m.sufficient_blocks(data)
    assert s['kept']==[0,1]
    np.testing.assert_allclose(m.coefficients(s),ref.dense_fit(data,'recent',[0,1]),atol=1e-10)


def test_bar_shapes_boundary_and_unsupported_null():
    null=[-.01,.01]*10
    bar=2*.01+3*math.sqrt(20*.0001/19)
    assert m.working_bar(.4,null)==pytest.approx(bar)
    assert m.working_bar(.4,[0.]*20)==pytest.approx(.04)
    assert m.working_bar(.4,[0.]*19) is None
    assert m.pattern([bar,bar+.1],[-1,-.1],[-.01,.01],bar)=='mixed'
    assert m.pattern([bar+.001,bar+.1],[-1,-.1],[-bar,bar],bar)=='floor'
    assert m.pattern([-bar,bar],[-1,-.1],[.1,1],bar)=='ladder'


def test_complete_carried_handler_checkpoint_replay_and_preserved_ch6(tmp_path):
    world,_=ref.histories(players=12,games=120,left=-.12)
    path=tmp_path/'constructed.sqlite';native.database(path,world)
    inputs={'histories':dict(path=str(path),sha256=digest(path))}
    config=dict(card='CH7',constructed_fixture=True,draws=32,null_draws=20,floor=8,max_new_draws=2)
    first=tmp_path/'first'/'output'
    assert bridge.execute(first,inputs,config)['status']=='yielded'
    copied={p.relative_to(first).as_posix():digest(p) for p in first.rglob('*') if p.is_file()}
    second=tmp_path/'second'/'output';shutil.copytree(first,second)
    (second.parent/'RESUMED_FROM.json').write_text(json.dumps(dict(copied=copied)))
    config['max_new_draws']=100000
    assert bridge.execute(second,inputs,config)['status']=='complete'
    assert bridge.verify(second,inputs,config)['verified']
    science=json.loads((second/'SCIENCE.json').read_text())
    assert science['record_kind']=='run' and science['by_construction'] is True and science['activation']==[]
    native.independent_comparison(world,science,32)
    assert all(digest(first/k)==v for k,v in copied.items())
    assert bridge.ch6 is old_bridge.ch6 and bridge.histories is old_bridge.histories
    assert digest(path)==inputs['histories']['sha256']


def test_authentication_yield_and_changed_checkpoint_refusal(tmp_path):
    output=tmp_path/'output';output.mkdir();(output/'YIELD_REQUEST.json').write_text('{}')
    path=tmp_path/'unused.sqlite';path.touch()
    inputs={'histories':dict(path=str(path),sha256=digest(path))}
    config=dict(card='CH7',constructed_fixture=True,draws=32,null_draws=20,floor=8)
    assert bridge.execute(output,inputs,config)['status']=='yielded'
    with bridge.adapted('CH7'):
        from runners.drive.cards.week5_ch_source import write_json
        controls={k:v for k,v in config.items() if k!='card'}
        write_json(output/'SOURCE_SEAL.json',dict(binding=handler.identity(inputs,controls),files={'unused':'0'*64}))
        (output/'unused').touch()
    assert bridge.verify(output,inputs,config)['status']=='yielded'
    (output/'YIELD_REQUEST.json').unlink()
    with pytest.raises(ValueError):bridge.verify(output,inputs,config)


def test_hand_rows_month_censor_session_reference_and_thirty_game_boundary():
    records=[]
    for i in range(60):
        records.append(dict(game=f'constructed-{i:03}',month=('2017-04','2017-05','2017-06')[i//20],
            start=i*600,rating=1500+2*i,opponent_rating=1500,rating_change=2,result=1,
            time_control='blitz',rows=[dict(think_time=20,clock_before=200)]))
    data=m.player_data(records)
    assert data['sessions']=={'blitz':3,'rapid':0}
    assert data['counts']['right_censored_month_tail']==3
    assert len(data['rows'])==57 and sum(data['rows'][:,16])==28
    # The thirty-first observation is May's eleventh game, not its first.
    r=data['rows'][29]
    assert r[1]==0 and r[2]==pytest.approx(1.1) and r[3]==11
    assert r[11]==0 and r[12]==1 and r[13]==0 and r[16]==1
    records[0]['rating_change']=30
    changed=m.player_data(records)
    assert changed['counts']['provisional_session_games_dropped']==20
    assert len(changed['rows'])==38 and np.all(changed['rows'][:,17]==1)
    assert sum(changed['rows'][:,16])==28


def test_original_separation_failure_retained_and_quasi_separation_refused():
    from runners.drive.cards import week5_ch7_math_v2 as prior
    rows=np.zeros((20,18));rows[:,0]=np.tile([0,1],10);rows[:,3]=rows[:,0]
    assert prior.fit_playing_on(rows)['status']=='own-player unpenalized logistic'
    with pytest.raises(ValueError,match='separated'):m.fit_playing_on(rows)
    x=np.column_stack([np.ones(4),[0.,1.,1.,2.]])
    with pytest.raises(ValueError,match='separated'):m.separation_certificate(x,np.array([0,0,1,1]))
    overlap=np.column_stack([np.ones(4),[0.,0.,1.,1.]])
    proof=m.separation_certificate(overlap,np.array([0,1,0,1]))
    assert proof['maximum_total_margin']==pytest.approx(0,abs=1e-9)
    assert proof['native_solver_threads']==1
