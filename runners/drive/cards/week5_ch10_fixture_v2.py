"""Exact frequency-compressed binary controls for 300 constructed players.

Identical covariates within each frequency cell make its mean sufficient for
X'X and X'y. The multiplier restores every binary trial and player; no fitted
population is shortened. These worlds check arithmetic, never empirical power.
"""
from itertools import product
from pathlib import Path
import numpy as np
from . import week5_ch10_math_v1 as card
from . import week5_ch_table_regression_v2 as regression
from .week5_ch_source import write_json
from .week5_ch_tables_two_day_v3 import equivalent

PEOPLE=300
FREQUENCY=100000


def cells(world):
    values=[]
    histories=[(0.,.5,.5,.5),(1.,.5,.5,.5),(1.,1.,.5,.5)] if world=='primary' else list(product([0.,.5,1.],repeat=4))
    for lag,gap,previous,number,minutes in product(histories,[-1.,1.],[0.,1.],[10.,20.],[1.,3.]):
        if world=='primary':successes=10000 if lag[0]==0 else 14000
        else:successes=22000+sum((4000,2000,1000,500)[i] for i,v in enumerate(lag) if v==1)+sum((-2000,-1600,-1280,-1024)[i] for i,v in enumerate(lag) if v==0)
        assert 0<successes<FREQUENCY
        values.append(dict(berserk=successes/FREQUENCY,successes=successes,trials=FREQUENCY,
            previous_score=lag[0],previous_E=.2 if number==10 else .8,rating_gap_hundreds=gap,
            previous_berserk=previous,win_bonus=float(lag[0]==1 and lag[1]==1),game_number=number,
            minutes_since_first=minutes,lag_scores=list(lag),lag_expectations=[.5]*4))
    return values


def prepared(world,reference=False):
    data=cells(world);stats={};points={}
    for name in card.MODELS:
        group=[value for row in data if (value:=card.analytic(row,name)) is not None]
        cols,required=card.columns(name)
        stat,point=regression.prepare([group],cols,required,reference)
        point["rows"]*=FREQUENCY*PEOPLE  # Same binary-trial unit even when target rank is unsupported.
        if stat is not None:
            stat['xx']=np.repeat(stat['xx']*FREQUENCY,PEOPLE,axis=0)
            stat['xy']=np.repeat(stat['xy']*FREQUENCY,PEOPLE,axis=0)
            stat['rows']*=FREQUENCY*PEOPLE;stat['players_with_rows']=PEOPLE
            point.update(rows=stat['rows'],players=PEOPLE,outcome_minimum=0.,outcome_maximum=1.)
        stats[name]=stat;points[name]=point
    return dict(names=[str(i) for i in range(PEOPLE)],census=dict(constructed_frequency_cells=len(data),
        binary_trials_per_cell=FREQUENCY,constructed_players=PEOPLE),statistics=stats,points=points,
        base_rate=sum(r['successes'] for r in data)/(len(data)*FREQUENCY),current_games=len(data)*FREQUENCY*PEOPLE)


def prove(world,reference=False):
    prep=prepared(world,reference);rng=np.random.default_rng(20261112);draws=[]
    for _ in range(2000):
        weights=np.bincount(rng.integers(0,PEOPLE,PEOPLE),minlength=PEOPLE)
        draws.append(card.draw(prep,weights,reference))
    result=card.result(prep,draws,reference)
    if world=='primary':
        primary=result['estimates']['primary'];ci=primary['intervals'][0]
        assert abs(primary['coefficients'][0]-.04)<1e-8
        assert ci is not None and ci[0]-1e-8<=.04<=ci[1]+1e-8
    else:
        coefficients=result['estimates']['time_courses']['coefficients'][:8]
        truth=[.04,.02,.01,.005,-.02,-.016,-.0128,-.01024]
        assert np.allclose(coefficients,truth,rtol=1e-7,atol=1e-9)
        for name,expected in [('win',.25),('loss',.64),('difference',-.39)]:
            item=result['lag3_to_lag1'][name];assert abs(item['point']-expected)<1e-7
            assert item['interval'][0]-1e-7<=expected<=item['interval'][1]+1e-7
    return result


def execute(output,inputs,config):
    if inputs or config!={'world':config.get('world')} or config['world'] not in ('primary','decay'):
        raise ValueError('Only the two complete constructed controls are supported')
    result=prove(config['world']);write_json(Path(output)/'FIXTURE.json',result)
    return dict(status='complete',constructed_only=True,draws=2000)


def verify(output,inputs,config):
    import json
    if inputs or config!={'world':config.get('world')} or config['world'] not in ('primary','decay'):
        raise ValueError('Only the two complete constructed controls are supported')
    actual=json.loads((Path(output)/'FIXTURE.json').read_text())
    equivalent(actual,prove(config['world'],True))
    return dict(verified=True,independent_formula_replay=True,complete_binary_frequency_world=True)
