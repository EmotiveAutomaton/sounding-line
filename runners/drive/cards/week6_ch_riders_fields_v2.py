"""Prospective CH13/CH14 fields on the unchanged complete SG1 history.

DESIGN CHECK: LESSONS 2/3/5. Earlier-only histories, literal minute boundaries,
same-arena adjacency and exclusion of the entire focal player are invariant
under null and alternative. Missing clocks never become zero waits. No engine,
raw-source traversal, demographic field or source mutation is used here.
"""
from collections import Counter, defaultdict
from bisect import bisect_left, bisect_right
import math
import statistics

from .week5_ch11_math_v2 import context, habit

BINS = (0., 2., 5., 10., 20., 60., math.inf)


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def wait_bin(value):
    if not finite(value) or value < 0: return None
    return min(5, bisect_right(BINS, value)-1)


def ordered(rows):
    """Full window across months; missing starts retained in exclusion census."""
    return sorted((dict(r) for r in rows if finite(r.get('start'))),
                  key=lambda r:(r['start'], r['game']))


def arena_pairs(player, rows, predict, analysis=True):
    rows = list(rows)
    census = Counter(source_games=len(rows), missing_start=sum(not finite(r.get('start')) for r in rows))
    sequence = ordered(rows)
    if len({r['game'] for r in sequence}) != len(sequence):
        raise ValueError('Duplicate player-game identity')
    counts = defaultdict(Counter)
    departures = {}
    for row in sequence:
        key = context(row)
        if key is not None:
            departures[row['game']] = habit(counts[key], row['own_first_move'])['departure']
            counts[key][row['own_first_move']] += 1
    answer = []
    for index, first in enumerate(sequence):
        if index+1 == len(sequence): census['window_tail'] += 1; continue
        following = sequence[index+1]
        arena = first.get('tournament_id')
        if not (first.get('tournament') and following.get('tournament') and arena and
                arena == following.get('tournament_id')):
            census['not_same_identified_arena'] += 1; continue
        if following['start'] <= first['start']:
            census['tied_or_nonincreasing_start'] += 1; continue
        duration = first.get('duration_est')
        if not finite(duration) or duration < 0:
            census['missing_or_invalid_duration'] += 1; continue
        end = first['start']+duration
        wait = (following['start']-end)/60.
        if wait < 0:
            census['estimated_end_after_next_start'] += 1; continue
        expected = predict(following) if analysis else None
        score = following.get('score')
        outcome = score-expected if finite(expected) and score in (0.,.5,1.) else None
        answer.append(dict(player=player, game=first['game'], next_game=following['game'],
            arena=arena, end=end, wait=wait, pool_wait=None, pool_donors=0,
            analysis=bool(analysis), previous_score=first.get('score'),
            previous_E=predict(first) if analysis else None, outcome=outcome,
            departure=departures.get(following['game']),
            berserk=float(bool(following.get('berserk_candidate'))),
            berserk_admitted=bool(following.get('berserk_instrument_admitted')),
            duration_status=first.get('duration_status')))
        census['valid_timing_pairs'] += 1
    return answer, dict(census)


def pool_waits(pairs, reference=False, check=lambda:None):
    """Median of one nearest-ending pair per other sampled player within ±60s.

    This construction uses no outcomes, forecasts or calibration membership.
    The literal exhaustive reference is for constructed/native formula replay.
    """
    groups=defaultdict(list)
    for row in pairs: groups[row['arena']].append(row)
    for arena in sorted(groups):
        group=sorted(groups[arena], key=lambda r:(r['end'],r['player'],r['game']))
        ends=[r['end'] for r in group]
        lo=hi=0
        for target in group:
            check()
            if reference:
                while lo<len(group) and group[lo]['end']<target['end']-60:lo+=1
                while hi<len(group) and group[hi]['end']<=target['end']+60:hi+=1
                possible=group[lo:hi]
            else:possible=group[bisect_left(ends,target['end']-60):bisect_right(ends,target['end']+60)]
            donors={}
            for row in possible:
                if row['player']==target['player'] or abs(row['end']-target['end'])>60: continue
                key=(abs(row['end']-target['end']),row['end'],row['game'])
                old=donors.get(row['player'])
                if old is None or key<old[0]: donors[row['player']]=(key,row['wait'])
            values=[donors[p][1] for p in sorted(donors)]
            target['pool_donors']=len(values)
            target['pool_wait']=None
            if values:
                values.sort(); n=len(values)
                target['pool_wait']=(values[(n-1)//2]+values[n//2])/2 if reference else statistics.median(values)
    return pairs


def opening_choices(rows):
    """Score a choice before updating history; no pseudo-options or future moves."""
    rows=list(rows); sequence=ordered(rows)
    if len({r['game'] for r in sequence})!=len(sequence): raise ValueError('Duplicate player-game identity')
    census=Counter(source_games=len(rows),missing_start=len(rows)-len(sequence))
    counts=defaultdict(Counter); last_time=defaultdict(dict); last_game=defaultdict(dict)
    answer=[]; previous_start=None
    for ordinal,row in enumerate(sequence):
        key=context(row); week_break=previous_start is not None and row['start']-previous_start>=7*86400
        previous_start=row['start']
        if key is None: census['missing_opening_context']+=1; continue
        count=counts[key]; move=row['own_first_move']; earlier=sum(count.values())
        options=sorted(count)
        if earlier<30: census['under_30_context_games']+=1
        elif len(options)<2: census['under_two_prior_options']+=1
        elif move not in count: census['future_novel_choice']+=1
        else:
            features=[]
            for option in options:
                hours=(row['start']-last_time[key][option])/3600.
                games=ordinal-last_game[key][option]
                if hours<0 or games<1: raise ValueError('Nonchronological opening history')
                features.append([math.log(count[option]),math.log1p(hours),math.log1p(games)])
            answer.append(dict(game=row['game'],start=row['start'],context=list(key),
                earlier=earlier,options=options,chosen=options.index(move),features=features,
                week_break=week_break))
            census['eligible_choices']+=1
        count[move]+=1;last_time[key][move]=row['start'];last_game[key][move]=ordinal
    split=2*len(answer)//3
    for index,row in enumerate(answer): row['train']=index<split
    census.update(train_choices=split,test_choices=len(answer)-split)
    if split<2 or len(answer)-split<1:
        census['player_without_train_test_support']=1
        answer=[]
    return answer,dict(census)
