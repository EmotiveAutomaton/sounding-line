import json
import numpy as np
import pytest
from runners.drive.cards import week5_ch7_math_v1 as m
from runners.drive.cards import week5_ch7_source_v1 as source
from runners.drive.cards import week5_ch7_fixture_v1 as fixture
from runners.drive.cards import week5_ch_grid_backhalf_v1 as grid
from runners.drive.cards.week5_ch_grid import grid as old_grid


def game(index,month='2017-04',start=None,rating=1500,delta=2):
    return dict(game=f'constructed-{index}',month=month,start=index*600 if start is None else start,end=None,
        rating=rating,opponent_rating=1500,rating_change=delta,result=1 if delta>0 else -1,
        time_control='blitz',initial=300,increment=0,first_clock=300,
        rows=[dict(ply=5,clock_before=200.,think_time=20.)])


def test_session_censor_provisional_exclusion_and_window_carry():
    games=[game(i,month='2017-04' if i<20 else '2017-05' if i<40 else '2017-06',
                rating=1500+2*i,start=i*600) for i in range(60)]
    result=m.player_data(games)
    assert result['counts']['right_censored_month_tail']==3
    assert result['rows'].shape[0]==57
    assert np.sum(result['rows'][:,m.BEST_READY])==28 # games 31..59 except May tail
    assert np.all(result['rows'][:,m.NEW_BEST]==1)
    assert np.all(result['rows'][:,m.WB_BELOW]==0)
    assert result['sessions']['blitz']==3
    games[0]['rating_change']=30
    changed=m.player_data(games)
    assert changed['counts']['provisional_sessions_dropped']==1
    assert changed['rows'].shape[0]==38
    assert np.all(changed['rows'][:,m.PROV_START]==1)
    assert np.allclose(changed['rows'][changed['rows'][:,m.PLAY]==1,m.PACE],.1)


def test_three_outcome_probabilities_preserve_expected_score():
    p=np.array([0,.01,.25,.5,.8,.99,1.])
    for fraction in (0.,.2,1.):
        probabilities=m.result_probabilities(p,fraction)
        assert np.all(probabilities>=0)
        assert np.allclose(probabilities.sum(axis=1),1)
        assert np.allclose(probabilities[:,2]+.5*probabilities[:,1],p)
    assert m.fit_draw_fraction(np.full(30,.5),np.ones(30))['fraction']==0
    with pytest.raises(ValueError):m.result_probabilities(p,1.01)


def test_new_projection_preserves_legacy_fields_and_adds_ratings():
    payload=dict(game='constructed',meta=dict(players=['constructed-a','constructed-b'],ratings=[1500,1450],
        start=0,end=None,initial=300,increment=2,time_control='blitz',rating_changes=[5,-5],result='1-0'),
        first_clocks=[300,300],rows=[dict(player='constructed-a',ply=1,clock_before=300,think_time=3)])
    old=list(source.ORIGINAL_PROJECTED('2017-04',0,json.dumps(payload)))
    new=list(source.projected('2017-04',0,json.dumps(payload)))
    assert new[0][0]==old[0][0]
    assert {k:new[0][1][k] for k in old[0][1]}==old[0][1]
    assert new[0][1]['rating']==1500 and new[0][1]['opponent_rating']==1450


def test_fixed_effect_sufficient_fit_matches_independent_dummy_matrix():
    world,_=fixture.histories(players=20,games=120,left=-.12,right=-.03)
    blocks=[m.player_data(games)['rows'] for games in world.values()]
    statistics=m.sufficient_blocks(blocks)
    actual=m.coefficients(statistics)
    designs=[m.design(block)[0][:,statistics['kept']] for block in blocks]
    x=np.concatenate(designs);y=np.concatenate([block[:,m.PLAY] for block in blocks])
    ids=np.concatenate([np.full(len(block),i) for i,block in enumerate(blocks)])
    dummy=np.eye(len(blocks))[ids]
    expected=np.linalg.lstsq(np.column_stack([x,dummy]),y,rcond=None)[0][:len(actual)]
    assert np.max(np.abs(expected-actual))<1e-8
    weights=np.ones(len(blocks),int);weights[0]=2;weights[1]=0
    replicated=[block for i,block in enumerate(blocks) for _ in range(weights[i])]
    assert np.max(np.abs(m.coefficients(statistics,weights)-m.coefficients(m.sufficient_blocks(replicated))))<1e-8


def test_full_simulated_history_removes_planted_reference_effect():
    world,_=fixture.histories(players=32,games=180,left=-.16,right=0.)
    data=[m.player_data(games) for games in world.values()]
    blocks=[datum['rows'] for datum in data]
    point=m.coefficients(m.sufficient_blocks(blocks))
    assert abs(point[0]+.16)<.05 and abs(point[1])<.05
    fitted=[m.fit_null(datum) for datum in data]
    values=[]
    for draw in range(20):
        simulated=[m.simulate(datum,fit,np.random.SeedSequence([m.SEED,draw,i])) for i,(datum,fit) in enumerate(zip(data,fitted))]
        values.append(m.contrast(m.coefficients(m.sufficient_blocks(simulated))))
    assert np.mean(np.abs(values))<.05
    bad=dict(data[0],trace=data[0]['trace'].copy());bad['trace'][:,m.T_DELTA]*=-1
    with pytest.raises(ValueError,match='not positive'):m.fit_null(bad)


def test_pattern_and_working_bar_are_joint_interval_rules():
    assert m.working_bar(.4,[0.]*20)==pytest.approx(.04)
    assert m.working_bar(.4,[0.]*19) is None
    assert m.pattern([.1,.2],[-.2,-.1],[-.01,.01],.04)=='floor'
    assert m.pattern([-.01,.01],[-.2,-.1],[-.2,-.1],.04)=='ladder'
    assert m.pattern([.01,.1],[-.2,-.1],[-.01,.01],.04)=='mixed'


def test_only_four_era_component_rows_withdrawn_other_controls_identical():
    old={r['id']:r for r in old_grid()['cells']};new=grid.grid()
    assert len(new['cells'])==44
    assert {r['id'] for r in new['cells'] if r['state']=='withdrawn'}==set(grid.WITHDRAWN)
    assert sum(r['state']=='dependency-gated' for r in new['cells'])==40
    for row in new['cells']:
        assert row['config']==old[row['id']]['config']
        assert row['cpu_ceiling']==old[row['id']]['cpu_ceiling']
        if row['config'].get('measure') in ('entropy','entropy_fixed100'):
            assert row['policy_entropy_outcome_months']==['2017-05','2017-06']


def test_constructed_handler_sealed_continuation_full_replay_and_counts(tmp_path):
    import shutil
    from runners.drive.cards import week5_ch7_v1 as handler
    from runners.drive.cards.week5_ch_source import digest
    world,_=fixture.histories(players=12,games=120,left=-.12,right=0.)
    database=tmp_path/'constructed.sqlite';fixture.database(database,world)
    inputs={'histories':{'path':str(database),'sha256':digest(database)}}
    config=dict(constructed_fixture=True,draws=32,null_draws=20,floor=8,max_new_draws=2)
    original=tmp_path/'attempt1'/'output'
    assert handler.execute(original,inputs,config)['status']=='yielded'
    copied={p.relative_to(original).as_posix():digest(p) for p in original.rglob('*') if p.is_file()}
    successor=tmp_path/'attempt2'/'output';shutil.copytree(original,successor)
    (successor.parent/'RESUMED_FROM.json').write_text(json.dumps(dict(copied=copied)))
    settings=dict(config,max_new_draws=100000)
    assert handler.execute(successor,inputs,settings)['status']=='complete'
    result=json.loads((successor/'SCIENCE.json').read_text())
    assert result['primary']['draws']==32 and result['primary']['rows']>0
    assert result['primary']['players_with_rows']==12
    assert handler.verify(successor,inputs,settings)['verified']
    assert all(digest(original/name)==value for name,value in copied.items())


def test_authentication_yield_is_safe_for_both_operations(tmp_path):
    from runners.drive.cards import week5_ch7_v1 as handler
    output=tmp_path/'output';output.mkdir();(output/'YIELD_REQUEST.json').write_text('{}')
    config=dict(constructed_fixture=True,draws=32,null_draws=20,floor=8)
    inputs={'histories':{'path':str(tmp_path/'unused.sqlite'),'sha256':'0'*64}}
    # Execute reaches cooperative input hashing before opening a missing file.
    # Supply a real zero-byte file so the request, not filesystem absence, wins.
    (tmp_path/'unused.sqlite').touch()
    assert handler.execute(output,inputs,config)['status']=='yielded'
    # A sealed output is needed to enter the verifier authentication boundary.
    from runners.drive.cards.week5_ch_source import write_json
    write_json(output/'SOURCE_SEAL.json',dict(binding=handler.identity(inputs,config),files={'unused': '0'*64}))
    (output/'unused').touch()
    assert handler.verify(output,inputs,config)['status']=='yielded'
