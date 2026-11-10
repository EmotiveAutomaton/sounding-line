import math
import numpy as np
import pytest
from runners.drive.cards import week5_ch_models as m
from runners.drive.cards import week5_ch_histories as h

def test_fixed_effects_recover_signed_and_exact_zero_worlds():
    rng=np.random.default_rng(3);g=np.repeat(np.arange(40),30);x=rng.normal(size=(len(g),2));a=rng.normal(size=40)[g]
    for sign in (-1,0,1):
        y=a+sign*.1*x[:,0]+.2*x[:,1]
        r=m.regress(y,x,g,.03,64)
        assert r['coefficient']==pytest.approx(sign*.1,abs=1e-12)
        assert r['verdict']==('supports' if sign==1 else 'against')

def test_player_sufficient_statistics_match_explicit_duplicate_resampling():
    rng=np.random.default_rng(3);g=np.repeat(np.arange(4),10);x=rng.normal(size=(40,3));y=x@np.array([.2,.4,.6])+rng.normal(size=40)
    s=m.sufficient(y,x,g);weights=np.array([2,0,1,1]);expected=m.solve(np.tensordot(weights,s['xx'],axes=1),weights@s['xy'])
    rows=np.concatenate([np.flatnonzero(g==i) for i in (0,0,2,3)]);copy=np.repeat(np.arange(4),10)
    t=m.sufficient(y[rows],x[rows],copy);actual=m.solve(t['xx'].sum(0),t['xy'].sum(0))
    assert np.allclose(expected,actual)

def test_no_primary_variation_is_unsupported_not_null():
    r=m.regress(np.arange(20),np.ones((20,2)),np.repeat(np.arange(4),5),.03,16)
    assert r['status']=='unsupported' and r['verdict']=='inconclusive'

def test_three_way_exhaustive_boundaries():
    assert m.verdict([.04,.1],.03)=='supports'
    assert m.verdict([-.03,.03],.03)=='against'
    assert m.verdict([-.1,-.04],.03)=='against'
    assert m.verdict([.02,.04],.03)=='inconclusive'

def game(start,delta=1,month='2017-04'):
    return dict(game=str(start),month=month,start=float(start),end=None,rating_change=delta,result=1,time_control='blitz')

def test_session_tails_are_right_censored_and_thresholds_exact():
    rows,counts,sessions=h.make_sessions({'a':[game(0),game(1799),game(3599),game(3600,month='2017-05')]})
    assert [r['stop'] for r in rows]==[0,1]
    assert counts['right_censored_window_tail']==2 and counts['start_time_gap_proxy']==2
    assert sessions['a']==3

def test_direct_end_precedes_start_gap_proxy():
    a=game(0);a['end']=600
    rows,counts,_=h.make_sessions({'a':[a,game(2000)]})
    assert rows[0]['stop']==0 and counts['direct_end_gap']==1

def test_fixed_logit_signed_known_answers():
    rng=np.random.default_rng(2);groups=np.repeat(np.arange(50),100);x=rng.normal(size=(len(groups),2));a=rng.normal(0,.3,50)[groups]
    for sign in (-1,1):
        y=(rng.random(len(groups))<1/(1+np.exp(-(a+sign*.8*x[:,0]+.2*x[:,1])))).astype(float)
        fitted=h.fixed_logit(y,x,groups)
        assert sign*fitted['coefficients'][0]>.5

def test_two_hundred_planted_targets_recover_within_five_percent():
    result=h.target_recovery();assert result['players']==200 and result['pass_gate']

def test_clock_floor_is_observed_clock_not_centered_reserve():
    r=dict(ply=21,clock_before=16,think_time=2)
    g=dict(first_clock=100,initial=100,increment=0,rows=[r])
    a,z,_,counts=h.reserve_arrays([g],medians={11:.9})
    assert len(a)==1 and z[0]<-.7 and counts.get('clock_floor_moves',0)==0

def test_fixed_logit_constant_target_refuses():
    with pytest.raises(ValueError,match='not identifiable'):
        h.fixed_logit(np.tile([0,1],20),np.ones((40,1)),np.repeat(np.arange(4),10))

def test_loo_expected_time_matches_explicit_deleted_refits():
    rng=np.random.default_rng(4);rows=[]
    for player in range(6):
        for i in range(20):rows.append(dict(player=str(player),think_time=math.exp(rng.normal()),rating=1600,ply=i+5,k50=rng.integers(1,6),time_control='blitz'))
    actual=m.loo_expected_time(rows)
    y=np.log([r['think_time'] for r in rows]);g=np.array([r['player'] for r in rows]);dec=np.array([(r['ply']//2)//10 for r in rows])
    x=np.column_stack([g==p for p in sorted(set(g))]+[np.array([r['k50'] for r in rows])]+[dec==d for d in sorted(set(dec))[1:]])
    for i in (0,15,30,119):
        keep=np.arange(len(y))!=i;b=np.linalg.lstsq(x[keep],y[keep],rcond=None)[0]
        assert actual[i]==pytest.approx(y[i]-x[i]@b,abs=1e-10)

def test_overshoot_both_directions_and_end_censoring():
    from runners.drive.cards.week5_ch_reserve_secondaries import excursions
    def seq(values):return [dict(share=v,median=.5) for v in values]
    deficit=excursions(seq([.2,.4,.52,.5,.5]),0)
    surplus=excursions(seq([.8,.6,.48,.5,.5]),0)
    assert deficit['deficit_overshoots']==1 and surplus['surplus_overshoots']==1
    tail=excursions(seq([.2]),0)
    assert tail['deficit_end_censored']==1

def test_dynamic_null_preserves_residual_autocorrelation():
    from runners.drive.cards.week5_ch_reserve_secondaries import simulate,mean_response
    model=dict(target=0.,beta=np.zeros(6),phi=.7,sigma=.1,residual_sd=.14)
    seq=[dict(share=.8,median=.8,initial=100000,increment=1,move=i,logtime=0.) for i in range(2000)]
    result=simulate(seq,model,np.random.default_rng(7));r=[x['logtime']-mean_response(x,model) for x in result]
    assert .64<np.corrcoef(r[:-1],r[1:])[0,1]<.76

def test_profile_target_can_miss_no_target_world():
    rng=np.random.default_rng(7);z=rng.uniform(-.3,.3,500);base=np.column_stack([np.ones(500),rng.normal(size=(500,3))]);y=base@np.array([1,.2,.3,.4])
    target=h.target_fit(y,base,z)
    assert np.max(np.abs(target['beta'][-2:]))<1e-10

def test_precision_contrast_recovers_known_positive_difference():
    from runners.drive.cards.week5_ch_reserve_secondaries import precision_difference,concentration
    c=np.linspace(.25,1.,80);result=precision_difference(c,4*c,64)
    assert result['estimate']>1.3 and result['interval'][0]>1.0
    games=[dict(time_control='blitz',start=0),dict(time_control='blitz',start=1),dict(time_control='rapid',start=0),dict(time_control='rapid',start=86400)]
    assert concentration(games,'games')==.5 and concentration(games,'days')==pytest.approx(2/3)

def test_two_threshold_ruler_recovers_constructed_dead_band():
    rng=np.random.default_rng(15);z=rng.uniform(-.4,.4,1200);base=np.column_stack([np.ones(1200),rng.normal(size=(1200,3))])
    y=base@np.array([1,.2,.3,.4])+3*np.minimum(z+.1,0)-2*np.maximum(z-.1,0)+rng.normal(0,.005,1200)
    band=h.target_fit(y,base,z,band=True);point=h.target_fit(y,base,z,band=False)
    assert band['width']==.1 and abs(band['target'])<.01 and band['variance']<point['variance']/10

