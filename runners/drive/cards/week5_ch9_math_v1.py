"""Contested versus outplayed losses and the next observed game.

DESIGN CHECK: classifications are mechanical, not inferred emotional labels.
Missing or overlapping estimated end times cannot become QUICK. Censored tails
remain missing outcomes. Duration uncertainty and the session rule stay visible.
"""
from collections import Counter
import math
import numpy as np
from . import week5_ch_table_regression_v2 as regression
from .week5_ch8_math_v3 import nuisance,interval


def kind(row):
    if row['score']!=0 or row['tournament'] or row['provisional_session']:return None
    if row['termination']=='Time forfeit' and row['final_material_balance']>=2:return 1
    if row['last_move_checkmate'] or (row['termination']=='Normal' and row['final_material_balance']<=-3):return 0
    return None


def outcome(row):
    if row['censored'] or row.get('seconds_to_next') is None:return None,'censored_next_game'
    duration=row.get('duration_est')
    if duration is None or not math.isfinite(duration) or duration<0:return None,'missing_or_invalid_duration'
    gap=row['seconds_to_next']-duration
    if gap<0:return None,'next_start_precedes_estimated_end'
    return float(gap<=120),'observed_estimated_gap'


def rows(games):
    result=[];census=Counter(source_games=len(games))
    for row in games:
        k=kind(row)
        if k is None:census['excluded_kind_or_row_scope']+=1;continue
        quick,reason=outcome(row);census[reason]+=1;census['flagged_ahead' if k else 'outplayed']+=1
        controls_ok=row['E'] is not None and math.isfinite(row['form_before'])
        if not controls_ok:census['missing_forecast_or_form']+=1
        result.append(dict(kind=k,quick=quick,stop=None if row['stop'] is None else float(row['stop']),
            rematch=row['rematch'],favourite=row['E'] is not None and row['E']>=.65,
            controls=None if not controls_ok else [row['E']]+nuisance(row)[:-1],
            control_class=row['time_control']))
    return result,dict(census)


def prepare(players,reference=False):
    names=[];census=Counter();counts=[];classes=Counter()
    for name in players:
        records,count=rows(players[name]);census.update(count)
        if not records:continue
        names.append(name);table=np.zeros((2,2,2))
        for row in records:
            classes[row['control_class']]+=1
            if row['quick']==1 and row['rematch'] is not None:
                table[0,row['kind']]+=[float(row['rematch']),1]
                if row['favourite']:table[1,row['kind']]+=[float(row['rematch']),1]
        counts.append(table)
    statistics={};points={}
    columns=['flagged_ahead','expected_score','games_so_far','form_before','losing_streak','sin_hour','cos_hour','tournament']
    for label,measurement,favourite in [('primary','quick',False),('STOP','stop',False),('STOP_favourite','stop',True)]:
        def groups():
            for name in names:
                yield [(r[measurement],[r['kind']]+r['controls']) for r in rows(players[name])[0]
                       if r[measurement] is not None and r['controls'] is not None and (not favourite or r['favourite'])]
        statistics[label],points[label]=regression.prepare(groups(),columns,reference=reference)
    return dict(names=names,census=dict(census),classes=dict(classes),statistics=statistics,points=points,
                rematches=np.asarray(counts).reshape(-1,2,2,2))


def rematches(prepared,weights):
    total=np.einsum('i,ijkl->jkl',weights,prepared['rematches'])
    return [[regression.ratio(pair[0],pair[1]) for pair in scope] for scope in total]


def draw(prepared,weights,reference=False):
    return dict(models={name:regression.sample(value,weights,reference) for name,value in prepared['statistics'].items()},
                rematches=rematches(prepared,weights))


def result(prepared,draws,reference=False):
    estimates={name:regression.summarize(value,[d['models'][name] for d in draws],.03 if name=='primary' else None)
               for name,value in prepared['points'].items()}
    primary=estimates['primary'];ci=None if primary.get('intervals') is None else primary['intervals'][0]
    primary['descriptive_pattern']='inconclusive'
    if ci is not None:
        primary['descriptive_pattern']='more quick return after flagging ahead' if ci[0]>.03 else 'opposite direction' if ci[1]<0 else 'inside practical band' if ci[0]>=-.03 and ci[1]<=.03 else 'inconclusive'
    point=rematches(prepared,np.ones(len(prepared['names'])))
    people=(prepared['rematches'][:,:,:,1]>0).sum(axis=0)
    intervals=[[interval([d['rematches'][i][j] for d in draws]) if people[i,j]>=2 and point[i][j] not in (None,0.,1.) else None
                for j in range(2)] for i in range(2)]
    return dict(card='CH9',status='descriptive',players=len(prepared['names']),census=prepared['census'],
        control_class_counts=prepared['classes'],estimates=estimates,
        quick_rematches=dict(point=point,intervals=intervals,people=people.tolist(),
                             scopes=['all_eligible_losses','clear_favourite_losses'],kinds=['outplayed','flagged_ahead']),
        draws=len(draws),record_kind='claim',theory_tags=['H15-T1'],by_construction=False,
        activation=[dict(channel='RAGE versus SHAME, analogy only',set_point='seen as competent',
                        moved='a loss while ahead on material versus an outplayed loss',
                        could_do='quickly start another game or rematch, with opponent consent',
                        observed='QUICK, source-defined REMATCH and STOP',relation='observational behavioral contrast; channel identity untested')],
        limitations=['A public game rating is not standing in a room.','Material advantage is not a win-probability estimate.',
         'Clock-derived duration excludes unobserved first-move latencies and is an estimate, not an observed end timestamp.',
         'Negative estimated end-to-start gaps are missing, never QUICK; trailing control/month observations are censored.',
         'REMATCH and STOP retain the source start-gap session rule; a long game can separate sessions even if the next start is soon after its estimated end.',
         'The primary uses all eligible control classes and the listed CH8 controls; class composition is reported as a rival.',
         'State, game length and clock state differ between loss types; rematching also requires the other player to agree.'])
