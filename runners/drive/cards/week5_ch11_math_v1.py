"""Past-only opening habit and the next choice after a forecast-linked result.

DESIGN CHECK: no future choice may enter its own habit count. Contexts remain
separate across colours, Black's opponent first move, and control classes.
The calm secondary is a mean, not an algebraically empty loud-loss contrast.
"""
from collections import Counter,defaultdict,deque
import math
import numpy as np
from . import week5_ch_table_regression_v1 as regression
from .week5_ch8_math_v2 import interval


def context(row):
    if row.get('own_first_move') is None:return None
    if row['colour']=='black' and row.get('opponent_first_move') is None:return None
    return (row['time_control'],row['colour'],row.get('opponent_first_move') if row['colour']=='black' else None)


def habit(counts,move,reference=False):
    n=sum(counts.values());k=len(counts)+1;frequency=counts.get(move,0)
    if reference:departure=math.log(n+k/2)-math.log(frequency+.5)
    else:departure=-math.log((frequency+.5)/(n+.5*k))
    return dict(earlier=n,departure=None if n<20 else departure,
                novel=None if n<30 else float(move not in counts))


def choices(rows,reference=False):
    ordered=sorted(rows,key=lambda r:(r['start'],r['game']))
    counts=defaultdict(Counter);last={};recent=defaultdict(lambda:deque(maxlen=3));measures={};calm={}
    for row in ordered:
        key=context(row)
        if key is not None:
            value=habit(counts[key],row['own_first_move'],reference)
            value['shift']=None if key not in last else float(last[key]!=row['own_first_move'])
            measures[row['game']]=value
            counts[key][row['own_first_move']]+=1;last[key]=row['own_first_move']
        group=(row['time_control'],row['month'])
        recent[group].append(row.get('surprise'))
        calm[row['game']]=len(recent[group])==3 and all(v is not None and abs(v)<.35 for v in recent[group])
    lookup={r['game']:r for r in ordered};pairs=[];census=Counter(source_games=len(rows))
    for row in ordered:
        following=row.get('next_row')
        if row['censored'] or following is None:census['month_or_class_tail']+=1;continue
        nxt=lookup.get(following['game']);measure=measures.get(following['game'])
        if nxt is None or measure is None:census['missing_next_context_or_move']+=1;continue
        if measure['departure'] is None:census['under_20_earlier_context_games']+=1;continue
        if nxt.get('rating') is None or nxt.get('opponent_rating') is None:
            census['missing_next_rating_gap']+=1;continue
        hour=nxt['start']/3600%24
        controls=[nxt['index_in_session'],math.sin(2*math.pi*hour/24),math.cos(2*math.pi*hour/24),
                  (nxt['rating']-nxt['opponent_rating'])/100.,measure['earlier']]
        favourite=row['E'] is not None and row['E']>=.65 and row['score'] in (0.,1.)
        pairs.append(dict(measure,controls=controls,control=row['time_control'],
                          favourite=favourite,loss=float(row['score']==0),calm=calm[row['game']]))
        census['qualified_next_choices']+=1
        census['clear_favourite_losses']+=int(favourite and row['score']==0)
        census['calm_next_choices']+=int(calm[row['game']])
    return pairs,dict(census)


def prepare(players,reference=False):
    names=[];case_names=set();census=Counter();control_set=set();calm_rows=[];all_rows=[];primary_sum=0.;primary_n=0
    for name in players:
        value,count=choices(players[name],reference);census.update(count)
        if not value:continue
        names.append(name);control_set.update(r['control'] for r in value)
        if sum(r['favourite'] and r['loss']==1 for r in value)>=5:
            case_names.add(name)
            for row in value:
                if row['favourite']:primary_sum+=row['departure'];primary_n+=1
        calm=np.zeros((3,2));all_choices=np.zeros((3,2))
        for row in value:
            for j,measure in enumerate(['departure','novel','shift']):
                if row[measure] is not None:
                    all_choices[j]+=[row[measure],1]
                    if row['calm']:calm[j]+=[row[measure],1]
        calm_rows.append(calm);all_rows.append(all_choices)
    status='case_met' if len(case_names)>=2000 else 'below floor, descriptive'
    controls=sorted(control_set)
    statistics={};points={}
    base=['loss_as_favourite','next_games_so_far','sin_next_hour','cos_next_hour','next_rating_gap_hundreds','earlier_context_games']
    specs=[('primary','departure',None,False),('NOVEL','novel',None,False),('SHIFT','shift',None,False),
           ('class_adjusted','departure',None,True)]+[('class_'+tc,'departure',tc,False) for tc in controls]
    for label,measure,control,adjusted in specs:
        def groups():
            for name in names:
                records=[]
                if name in case_names:
                    for row in choices(players[name],reference)[0]:
                        if not row['favourite'] or row[measure] is None or (control is not None and row['control']!=control):continue
                        x=[row['loss']]+row['controls']
                        if adjusted:x+=[float(row['control']==tc) for tc in controls[1:]]
                        records.append((row[measure],x))
                yield records
        columns=base+(['control_'+tc for tc in controls[1:]] if adjusted else [])
        statistics[label],points[label]=regression.prepare(groups(),columns,reference=reference)
    calm=np.asarray(calm_rows).reshape(-1,3,2);all_choices=np.asarray(all_rows).reshape(-1,3,2)
    return dict(names=names,status=status,census=dict(census),statistics=statistics,points=points,
        calm=calm,all_choices=all_choices,bar=None if not primary_n else .05*primary_sum/primary_n,
        control_classes=controls,case=dict(required_players=2000,eligible_players=len(case_names),earlier_context_games=20,clear_favourite_losses=5))


def means(array,weights):
    total=np.einsum('i,ijk->jk',weights,array)
    return [regression.ratio(row[0],row[1]) for row in total]


def draw(prepared,weights,reference=False):
    return dict(models={key:regression.sample(value,weights,reference) for key,value in prepared['statistics'].items()},
                calm=means(prepared['calm'],weights),all_choices=means(prepared['all_choices'],weights))


def result(prepared,draws,reference=False):
    estimates={name:regression.summarize(point,[d['models'][name] for d in draws],prepared['bar'] if name=='primary' else None)
               for name,point in prepared['points'].items()}
    primary=estimates['primary'];ci=None if primary.get('intervals') is None else primary['intervals'][0]
    primary['descriptive_pattern']='inconclusive'
    if ci is not None and prepared['bar'] is not None:
        primary['descriptive_pattern']='more routine after the loud loss' if ci[1]<-prepared['bar'] else 'more departure after the loud loss' if ci[0]>prepared['bar'] else 'inside practical band' if ci[0]>=-prepared['bar'] and ci[1]<=prepared['bar'] else 'inconclusive'
    weights=np.ones(len(prepared['names']))
    secondary={key:dict(point=means(prepared[key],weights),intervals=[interval([d[key][j] for d in draws]) for j in range(3)])
               for key in ['calm','all_choices']}
    return dict(card='CH11',status=prepared['status'],players=len(prepared['names']),case=prepared['case'],census=prepared['census'],
        controls=prepared['control_classes'],estimates=estimates,calm_secondary=secondary,
        calm_definition='Means of DEPARTURE/NOVEL/SHIFT over all qualified next choices after three consecutive surprises of magnitude <0.35; no favourite-loss calm contrast',
        draws=len(draws),record_kind='claim',theory_tags=['H14-play-trigger'],by_construction=False,
        activation=[dict(channel='PLAY',set_point='any set point, chess analogy',moved='loss as clear favourite',
                        could_do='repeat, switch within familiar moves, or choose a new first move',observed='past-only next-choice measures',relation='behavioral analogy; channel identity untested')],
        limitations=['A public game rating is not standing in a room.','Next observed choices omit month/class tails and may be in a later session.',
         'Habit contexts remain separate by class; the primary includes all eligible classes without adding a class term.',
         'Class-specific and class-adjusted fits are descriptive robustness, never substituted primaries.',
         'Whole-player resamples cover the union of qualified next-choice players; primary rows additionally require five favourite losses, while calm means retain all qualified next choices.',
         'Calm and loud-loss conditions cannot be intersected to produce an apparent null.'])
