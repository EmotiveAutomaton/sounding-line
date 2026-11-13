"""Constructed complete-history CH7 worlds; no real data or engine.

Null, one-sided reference response and symmetric reference response share the
same generator and analytic machinery. Native qualification must run all three
complete handlers and fresh replay, with the full twenty-history null.
"""
from pathlib import Path
import json
import sqlite3
import numpy as np
from . import week5_ch7_math_v1 as m
from . import week5_ch7_v1 as handler
from .week5_ch_source import digest,write_json


def histories(players=48,games=240,left=0.,right=0.,seed=418):
    rng=np.random.default_rng(seed);world={};clipped=0;decisions=0
    for player in range(players):
        key=f'constructed-ch7-{player:05}'
        rating=1500+int(rng.normal(0,100));start=1500000000.+player*17;number=0;reference=rating;play=False;rows=[]
        for ordinal in range(games):
            month=m.MONTHS[min(2,3*ordinal//games)]
            month_start=ordinal==0 or month!=rows[-1]['month']
            if not play or month_start:number=0;reference=rating
            number+=1
            opponent=rating+int(rng.normal(0,110));expected=float(m.expected_score(rating-opponent))
            result=int(rng.choice([-1,0,1],p=m.result_probabilities(expected,.2)))
            delta=int(round(18*((result+1)/2-expected)))
            post=rating+delta;distance=(post-reference)/20.
            probability=.65-.015*(number-1)+.02*result+left*min(distance,0)+right*max(distance,0)
            clipped+=not .02<=probability<=.98;decisions+=1
            play=bool(rng.random()<np.clip(probability,.02,.98))
            measured_pace=.06+.002*max(-distance,0)
            rows.append(dict(game=f'constructed-game-{player}-{ordinal}',month=month,start=start,end=None,
                rating=rating,opponent_rating=opponent,rating_change=delta,result=result,initial=300,increment=2,
                time_control='blitz',first_clock=300,source_ordinal=ordinal,
                rows=[dict(ply=5,clock_before=300.,think_time=300*measured_pace),
                      dict(ply=7,clock_before=280.,think_time=280*measured_pace)]))
            start+=600 if play else 3600;rating=post
        world[key]=rows
    return world,dict(players=players,games_per_player=games,planted_below_slope=left,planted_above_slope=right,
                      probability_clipping_fraction=clipped/decisions,constructed=True)


def database(path,world):
    con=sqlite3.connect(path)
    con.executescript('CREATE TABLE player_history(player TEXT,month TEXT,game TEXT,payload TEXT,PRIMARY KEY(player,month,game));CREATE TABLE settings(key TEXT PRIMARY KEY,value TEXT);')
    con.executemany('INSERT INTO settings VALUES(?,?)',[('complete','true'),('constructed_fixture','true')])
    for player,games in world.items():
        for game in games:con.execute('INSERT INTO player_history VALUES(?,?,?,?)',(player,game['month'],game['game'],json.dumps(game,sort_keys=True)))
    con.commit();con.close()


def execute(output,inputs,config):
    if inputs or config!={'constructed_fixture':True}:raise ValueError('Exact source-free CH7 fixture required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True);results={}
    for case,left,right in [('null',0.,0.),('floor',-.16,0.),('ladder',-.16,-.16)]:
        root=output/case;root.mkdir(exist_ok=False)
        world,truth=histories(left=left,right=right)
        path=root/'PRIVATE_CONSTRUCTED_HISTORY.sqlite';database(path,world)
        spec=dict(path=str(path),sha256=digest(path));settings=dict(constructed_fixture=True,draws=2000,null_draws=20,floor=8)
        result=handler.execute(root/'analysis',dict(histories=spec),settings)
        if result['status']!='complete':raise ValueError('Complete fixture handler yielded; retain and restart bounded fixture')
        science=json.loads((root/'analysis/SCIENCE.json').read_text())
        beta=science['primary']['point']['coefficients']
        if max(abs(beta[0]-left),abs(beta[1]-right))>.05:raise AssertionError('Planted reference slopes not recovered')
        if science['null']['completed']!=20 or science['null']['invalid'] or science['null']['mean_absolute_contrast']>.05:
            raise AssertionError('Whole simulated histories did not remove the reference effect')
        if science['primary']['invalid_draws']:
            raise AssertionError('Constructed primary uncertainty has invalid resamples')
        if not handler.verify(root/'analysis',dict(histories=spec),settings)['verified']:
            raise AssertionError('Complete numerical replay differs')
        results[case]=dict(truth=truth,source_sha256=spec['sha256'],science_sha256=digest(root/'analysis/SCIENCE.json'),
                           complete_native_process_replay_still_required=True)
    write_json(output/'FIXTURE.json',dict(passed=True,cases=results,constructed_fixture=True,
        full_draws=2000,full_null_histories=20,scientific_admission=False))
    return dict(status='complete',constructed_fixture=True)


def verify(output,inputs,config):
    output=Path(output);execute(output/'independent_fixture',inputs,config)
    # Source SQLite page layouts and paths need not be identical; full scientific
    # numbers, cohort counts and private per-case source bytes must be identical.
    for case in ('null','floor','ladder'):
        old=output/case/'analysis/SCIENCE.json';new=output/'independent_fixture'/case/'analysis/SCIENCE.json'
        if digest(old)!=digest(new):raise ValueError('Fresh complete CH7 fixture differs')
    return dict(verified=True,full_constructed_source_and_numerical_replay=True)
