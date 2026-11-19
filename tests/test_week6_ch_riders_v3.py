"""Constructed-only field, estimand, leakage and null/trap controls.

No human rows are read. Numerical execution must be in the owner's counted slot.
The supplied in-sample CH14 preflight is not the oracle for chronological gain.
"""
from collections import Counter
import copy
import math
import json
import sqlite3
import numpy as np
import pytest
from runners.drive.cards import week6_ch_riders_fields_v3 as fields
from runners.drive.cards import week6_ch13_math_v1 as ch13
from runners.drive.cards import week6_ch14_math_v3 as ch14
from runners.drive.cards import week6_ch_riders_fixture_v3 as fixture
from runners.drive.cards import week6_ch_riders_v3 as handler


def game(index,start,move='e2e4',**extra):
    value=dict(game=f'g{index:05}',start=start,month='2017-04',time_control='blitz',
        colour='white',own_first_move=move,opponent_first_move=None,
        tournament=True,tournament_id='constructed-arena',duration_est=60.,
        duration_status='constructed-clock-estimate',score=0. if index%2 else 1.,
        berserk_candidate=False,berserk_instrument_admitted=False)
    value.update(extra);return value


@pytest.mark.parametrize('minutes,expected',[(0,0),(1.999,0),(2,1),(5,2),(10,3),(20,4),(60,5),(600,5),(-1,None),(None,None)])
def test_literal_wait_partition(minutes,expected):assert fields.wait_bin(minutes)==expected


def test_wait_is_end_to_next_start_and_missing_is_not_zero():
    rows=[game(0,0),game(1,180),game(2,420,duration_est=None),game(3,700)]
    pairs,census=fields.arena_pairs('p',rows,lambda row:.5)
    assert [r['wait'] for r in pairs]==[2.,3.]
    assert census['missing_or_invalid_duration']==1 and census['window_tail']==1
    assert pairs[0]['end']==60 and pairs[0]['outcome']==-.5


def test_adjacency_does_not_skip_intervening_other_arena_or_negative_gap():
    rows=[game(0,0),game(1,30,tournament_id='other'),game(2,80),game(3,100)]
    pairs,census=fields.arena_pairs('p',rows,lambda row:.5)
    assert pairs==[] and census['not_same_identified_arena']==2
    assert census['estimated_end_after_next_start']==1


def test_peer_omits_all_target_rows_and_uses_nearest_one_per_other_player():
    rows=[dict(arena='a',player=p,game=g,end=e,wait=w) for p,g,e,w in
          [('p','p0',100,999),('p','p1',101,777),('q','q1',90,2),('q','q2',99,4),
           ('r','r1',160,8),('s','s1',161,100),('t','t1',40,6)]]
    left=fields.pool_waits(copy.deepcopy(rows));right=fields.pool_waits(copy.deepcopy(rows),True)
    assert left==right
    assert left[0]['pool_wait']==6 and left[0]['pool_donors']==3
    assert fields.pool_waits([dict(arena='a',player='p',game='g',end=0,wait=0)])[0]['pool_wait'] is None


def paired_rows(people=24,shift=-.026,composition=False):
    rows=[]
    for person in range(people):
        baseline=.2*(person%3-1)
        for wait in (1.,30.):
            for loss in (False,True):
                repetitions=5*(1+(person%3)*int(composition and wait==1 and loss))
                effect=shift if wait==1 else 0.
                for _ in range(repetitions):
                    rows.append(dict(player=f'p{person:03}',analysis=True,wait=wait,pool_wait=wait,
                        pool_donors=3,previous_score=0. if loss else 1.,previous_E=.7,
                        outcome=baseline+effect*loss,departure=1+effect*loss,
                        berserk=float(loss),berserk_admitted=False))
    return rows


def test_exact_within_person_primary_baselines_and_composition_trap():
    rows=paired_rows(composition=True);prepared=ch13.prepare(rows)
    actual=ch13.draw(prepared,np.ones(len(prepared['names'])))['primary_wait']['point']
    reference=ch13.draw(ch13.prepare(rows,True),np.ones(24),True)['primary_wait']['point']
    assert actual==pytest.approx(-.026,abs=1e-14) and actual==pytest.approx(reference,abs=1e-14)
    short=[r for r in rows if r['wait']<2]
    pooled=np.mean([r['outcome'] for r in short if r['previous_score']==0])-np.mean([r['outcome'] for r in short if r['previous_score']==1])
    assert abs(pooled-actual)>.02


def test_exact_null_is_zero_and_does_not_become_negative():
    prepared=ch13.prepare(paired_rows(shift=0))
    draws=[ch13.draw(prepared,np.ones(24)) for _ in range(20)]
    result=ch13.result(prepared,draws)
    assert result['metrics']['primary_wait']['point']==0.
    assert result['metrics']['primary_wait']['classification']=='inside practical band'


def test_secondary_forecast_stratum_applies_to_losses_and_wins():
    rows=paired_rows(people=1)
    for row in rows:
        if row['previous_score']==1:row['previous_E']=.3
    assert ch13.player_summary(rows,loss_kind='favourite')['contrast'] is None
    assert ch13.player_summary(rows)['contrast']==pytest.approx(-.026)


def test_no_support_is_not_pooled_or_null():
    prepared=ch13.prepare(paired_rows(people=1))
    result=ch13.result(prepared,[ch13.draw(prepared,np.ones(1))]*20)
    assert result['metrics']['primary_wait']['interval'] is None
    assert result['metrics']['primary_wait']['classification']=='below floor, descriptive'
    rows=paired_rows();rows=[r for r in rows if not(r['player']=='p000' and r['wait']>=20 and r['previous_score']==1)]
    item=ch13.prepare(rows)['metrics']['primary_wait'][0]
    assert item['contrast'] is None


@pytest.mark.parametrize('own,peer,selected',[
    ([-.03,-.01],[.01,.02],'pool_wait'),([.01,.02],[-.02,-.01],'pool_wait'),
    ([-.03,-.01],[-.02,.01],'wait'),([-.03,-.01],None,'wait'),
    ([-.03,0.],[.01,.02],'wait'),([-.03,-.01],[-.05,-.02],'wait')])
def test_exact_curator_priority_rule(own,peer,selected):assert ch13.priority(own,peer)['selected']==selected


def histories(n=80):
    return [game(i,i*3600,'e2e4' if i%2 else 'd2d4',month='2017-04' if i<40 else '2017-05') for i in range(n)]


def test_opening_past_only_split_and_novel_choice():
    rows=histories();rows[35]['own_first_move']='c2c4'
    choices,census=fields.opening_choices(rows)
    assert census['future_novel_choice']==1
    assert choices[0]['earlier']==30 and choices[0]['options']==['d2d4','e2e4']
    assert 'c2c4' not in choices[4]['options']
    assert any('c2c4' in row['options'] for row in choices if row['start']>35*3600)
    split=2*len(choices)//3
    assert all(row['train'] for row in choices[:split]) and not any(row['train'] for row in choices[split:])
    later=rows+[game(999,999*3600,'a2a3')]
    extended,_=fields.opening_choices(later)
    for old,new in zip(choices,extended):
        assert {k:v for k,v in old.items() if k!='train'}=={k:v for k,v in new.items() if k!='train'}


def test_black_context_control_and_chronology_remain_separate():
    rows=histories(40)+[game(90,90*3600,'e7e5',colour='black',opponent_first_move='e2e4'),
        game(91,91*3600,'d7d5',colour='black',opponent_first_move='d2d4'),
        game(92,92*3600,'e2e4',time_control='rapid')]
    choices,census=fields.opening_choices(list(reversed(rows)))
    assert all(row['context']==['blitz','white',None] for row in choices)
    assert census['under_30_context_games']==33


def test_seven_day_break_is_literal_and_games_are_not_hours():
    rows=histories(50)
    for row in rows[40:]:row['start']+=7*86400
    choices,_=fields.opening_choices(rows)
    first=next(r for r in choices if r['game']==rows[40]['game'])
    assert first['week_break'] and first['features'][0][1]>first['features'][0][2]


def choice_fixture():
    # Independent literal menu contrasts, with fractional replicate weights
    # unnecessary: six observed choices make a finite identifiable model.
    data=dict(x=np.array([[0.,0.],[1.,0.],[0.,0.],[0.,1.],[0.,0.],[1.,1.],
                         [0.,0.],[1.,0.],[0.,0.],[0.,1.],[0.,0.],[1.,1.]]),
        starts=np.arange(0,12,2),lengths=np.full(6,2),selected=np.array([1,2,5,6,9,10]),person=np.zeros(6,int),week=np.zeros(6,bool))
    return data


def test_conditional_likelihood_independent_derivatives_and_offset_invariance():
    data=choice_fixture();beta=np.array([.4,-.3]);weights=np.ones(1)
    a=ch14.likelihood(data,beta,weights,False,True);b=ch14.likelihood(data,beta,weights,True,True)
    for left,right in zip(a,b):assert np.allclose(left,right,rtol=1e-12,atol=1e-12)
    altered=dict(data,x=data['x']+np.repeat(np.array([[i,-i] for i in range(6)]),2,axis=0))
    c=ch14.likelihood(altered,beta,weights,False,True)
    for left,right in zip(a,c):assert np.allclose(left,right,rtol=1e-12,atol=1e-12)
    eps=1e-5
    numeric=[]
    for j in range(2):
        step=np.zeros(2);step[j]=eps
        numeric.append((ch14.likelihood(data,beta+step,weights)[0].mean()-ch14.likelihood(data,beta-step,weights)[0].mean())/(2*eps))
    assert np.allclose(a[1],numeric,atol=1e-8)


def test_conditional_solver_null_and_unidentifiable_refusal():
    data=choice_fixture()
    for reference in (False,True):
        value=ch14.fit(data,np.ones(1),reference)
        assert value['status']=='complete' and value['beta']==pytest.approx([0.,0.],abs=1e-8)
        collapsed=dict(data,x=np.zeros_like(data['x']))
        assert ch14.fit(collapsed,np.ones(1),reference)['status']=='invalid'


def test_equal_player_not_choice_weighting_and_heldout_future_is_unfitted(monkeypatch):
    prepared=ch14.prepare({'a':histories(80),'b':histories(110)})
    sets=ch14.model_sets(prepared)
    seen=[]
    def fitted(data,weights,reference=False,check=lambda:None):
        seen.append(len(data['starts']));return dict(status='complete',beta=[0.]*data['x'].shape[1])
    monkeypatch.setattr(ch14,'fit',fitted)
    point=ch14.draw(prepared,sets,np.ones(2))
    assert all(n==int(prepared['train'].sum()) for n in seen)
    assert point['gains']['hours']['point']==0.
    assert point['gains']['hours']['players']==2


def test_analytically_known_heldout_gain_null_and_standing_preference_trap():
    answer=fixture.qualify()
    assert answer['status']=='constructed_controls_passed'
    assert answer['records']['recency_at_bar']['observed_gain']>.003
    assert abs(answer['records']['null']['observed_gain'])<1e-7
    assert abs(answer['records']['fixed_preference']['observed_gain'])<1e-7


def test_supplied_ch13_worlds_reproduce_through_registered_within_player_formula():
    assert fixture.qualify_ch13_supplied()['status']=='constructed_controls_passed'


def constructed_source(tmp_path):
    path=tmp_path/'constructed.sqlite';rng=np.random.default_rng(20261115)
    names=[];calibration=analysis=0
    for i in range(1000):
        name=f'constructed-player-{i:05}'
        is_cal=handler.forecast.calibration(name)
        if (is_cal and calibration<8) or (not is_cal and analysis<8):
            names.append(name)
            if is_cal:calibration+=1
            else:analysis+=1
        if calibration==8 and analysis==8:break
    con=sqlite3.connect(path)
    con.execute('CREATE TABLE settings(key TEXT PRIMARY KEY,value TEXT)')
    con.executemany('INSERT INTO settings VALUES (?,?)',[
        ('complete','true'),('constructed_fixture','true'),('adapter_sha256',handler.digest(handler.sg1.__file__))])
    con.execute('CREATE TABLE player_history(player TEXT,month TEXT,game TEXT,payload TEXT, PRIMARY KEY(player,month,game))')
    for p,name in enumerate(names):
        start=p*3.
        for i in range(120):
            colour='white' if i%2 else 'black'
            move=(['e2e4','d2d4'] if colour=='white' else ['e7e5','c7c5'])[rng.integers(2)]
            row=game(i,start,move,player=name,colour=colour,opponent_first_move='e2e4' if colour=='black' else None,
                score=float(rng.choice([0.,.5,1.])),rating=1500+int(rng.integers(-200,201)),opponent_rating=1500)
            con.execute('INSERT INTO player_history VALUES (?,?,?,?)',(name,row['month'],row['game'],json.dumps(row)))
            start+=60+(60 if i%4<2 else 1800)
    con.commit();con.close()
    decisions=tmp_path/'decisions.json'
    decisions.write_text(json.dumps(dict(status='CONSTRUCTED_ONLY',choices=handler.DECISIONS)),'utf8')
    spec=lambda p:dict(path=str(p),sha256=handler.digest(p))
    return dict(histories=spec(path),decisions=spec(decisions))


@pytest.mark.parametrize('card',['CH13','CH14'])
def test_complete_constructed_adapter_and_fresh_replay_preserve_source(tmp_path,card):
    inputs=constructed_source(tmp_path);original=handler.digest(inputs['histories']['path'])
    config=dict(card=card,draws=2,constructed_fixture=True)
    output=tmp_path/'output'
    assert handler.execute(output,inputs,config)['status']=='complete'
    assert handler.verify(output,inputs,config)['verified'] is True
    assert handler.digest(inputs['histories']['path'])==original
    assert not any((tmp_path/('constructed.sqlite'+suffix)).exists() for suffix in ('-wal','-shm','-journal'))


def test_production_cannot_use_unreviewed_choices(tmp_path):
    inputs=constructed_source(tmp_path)
    with pytest.raises(ValueError,match='reviewed rider design'):
        handler.identity(inputs,dict(card='CH14'))
