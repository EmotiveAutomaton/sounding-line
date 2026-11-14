"""CH10, with the explicitly approved two-plus-win arena-bonus control.

DESIGN CHECK: full categorical streaks encode previous-win exactly and cannot
identify its contrast. The curator approved the bonus indicator instead, before
fits. All eight distributed-lag targets must remain identifiable conditional
on controls; ratios with a zero denominator stay undefined.
"""
from collections import Counter
import numpy as np
from . import week5_ch10_features_v1 as features
from . import week5_ch_table_regression_v2 as regression
from .week5_ch8_math_v3 import interval

CONTROLS=['rating_gap_hundreds','previous_berserk','win_bonus','game_number','minutes_since_first']
MODELS=['primary','win_surprise','loss_surprise','failed_claim','time_courses']


def columns(label):
    if label=='primary':return ['previous_win','previous_draw']+CONTROLS,1
    if label=='time_courses':return ['win_lag_'+str(i) for i in range(1,5)]+['loss_lag_'+str(i) for i in range(1,5)]+CONTROLS,8
    if label=='failed_claim':return ['previous_berserk_after_loss']+[k for k in CONTROLS if k!='previous_berserk'],1
    return ['underdog_win' if label=='win_surprise' else 'favourite_loss']+CONTROLS,1


def analytic(row,label):
    controls=[row[k] for k in CONTROLS];score=row['previous_score'];expected=row['previous_E']
    if label=='primary':head=[float(score==1),float(score==.5)]
    elif label=='time_courses':
        if any(v not in (0.,.5,1.) for v in row['lag_scores']):return None
        head=[float(v==1) for v in row['lag_scores']]+[float(v==0) for v in row['lag_scores']]
    elif label=='failed_claim':
        if score!=0:return None
        head=[row['previous_berserk']];controls=[row[k] for k in CONTROLS if k!='previous_berserk']
    else:
        if score!=(1 if label=='win_surprise' else 0) or expected is None or .35<expected<.65:return None
        head=[float(expected<=.35) if label=='win_surprise' else float(expected>=.65)]
    return row['berserk'],head+controls


def prepare(players,reference=False):
    names=[];census=Counter();successes=total=0
    for name in players:
        rows,count=features.chronology(players[name]);census.update(count)
        if not rows:continue
        names.append(name);total+=len(rows);successes+=sum(r['berserk'] for r in rows)
    stats={};points={}
    for label in MODELS:
        def groups():
            for name in names:
                yield [value for r in features.chronology(players[name])[0] if (value:=analytic(r,label)) is not None]
        cols,required=columns(label)
        stats[label],points[label]=regression.prepare(groups(),cols,required,reference)
    return dict(names=names,census=dict(census),statistics=stats,points=points,
                base_rate=regression.ratio(successes,total),current_games=total)


def decay(coefficients):
    if coefficients is None:return dict(win=None,loss=None,difference=None)
    win=None if abs(coefficients[0])<=1e-10 else coefficients[2]/coefficients[0]
    loss=None if abs(coefficients[4])<=1e-10 else coefficients[6]/coefficients[4]
    return dict(win=win,loss=loss,difference=None if win is None or loss is None else win-loss)


def draw(prepared,weights,reference=False):
    fits={label:regression.sample(stat,weights,reference) for label,stat in prepared['statistics'].items()}
    return dict(models=fits,lag3_to_lag1=decay(fits.get('time_courses')))


def result(prepared,draws,reference=False):
    bar=None if prepared['base_rate'] is None else .1*prepared['base_rate']
    estimates={label:regression.summarize(point,[d['models'][label] for d in draws],bar if label=='primary' else None)
               for label,point in prepared['points'].items()}
    primary=estimates['primary'];ci=None if primary.get('intervals') is None else primary['intervals'][0]
    primary['descriptive_pattern']='inconclusive'
    if ci is not None and bar is not None:
        primary['descriptive_pattern']='more costly claims after winning' if ci[0]>bar else 'opposite direction' if ci[1]<0 else 'inside practical band' if ci[0]>=-bar and ci[1]<=bar else 'inconclusive'
    temporal=prepared['points']['time_courses'];point=decay(temporal.get('coefficients'))
    ratios={name:dict(point=point[name],interval=interval([d['lag3_to_lag1'][name] for d in draws])
                     if temporal.get('players',0)>=2 else None,
                     undefined_draws=sum(d['lag3_to_lag1'][name] is None for d in draws)) for name in point}
    gap=dict(unsupported='Current-gap column is not separately identified')
    if 'rating_gap_hundreds' in primary.get('columns',[]):
        j=primary['columns'].index('rating_gap_hundreds')
        gap=dict(coefficient=primary['coefficients'][j],interval=primary['intervals'][j],units='per100 own-minus-opponent rating points')
    return dict(card='CH10',status='descriptive',players=len(prepared['names']),census=prepared['census'],
        current_games=prepared['current_games'],base_berserk_rate=prepared['base_rate'],estimates=estimates,
        lag3_to_lag1=ratios,claim_follows_forecast=gap,
        approved_control='Indicator that the known current winning streak is at least two',
        curator_decision='Use the 2+ win bonus control (recommended)',
        original_categorical_model=dict(status='cannot identify win/loss contrast',fitted=False,
            identity='previous_win = streak_one + streak_two_plus',preserved=True),
        draws=len(draws),record_kind='claim',theory_tags=['H15-T2'],by_construction=False,
        activation=[dict(channel='pride claim versus SHAME output, packet proposals',set_point='claimed relative competence by analogy',
            moved='earlier win, loss or failed costly claim',could_do='halve the clock in an arena game',
            observed='validated BERSERK candidate and its lag pattern',relation='behavioral analogy; channel identity untested')],
        limitations=['A public game rating is not standing in a room.','Arena scoring,unobserved standings and selective participation remain rivals.',
          'Game number/minutes are relative to the first observed game,not an authenticated tournament start.',
          'Unknown left-edge streak states are retained as exclusions until identified by subsequent results.',
          'Lag coefficients compare wins/losses with draws in a joint distributed-lag model; all eight targets must be identified.',
          'A berserked loss is shorter; SG1.v support and owner admission are required before interpretation.'])
