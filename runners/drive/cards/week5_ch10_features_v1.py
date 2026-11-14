"""Outcome-blind tournament chronology for CH10; no primary encoding selected.

DESIGN CHECK: only earlier games can describe a current claim. Missing clocks
are not non-berserks. Unknown chronology cannot be bridged into a prior game.
All rows stay private and tournament keys are salted by the verified source.
"""
from collections import Counter,defaultdict
import math


def berserk(row):
    ratio=row.get('first_clock_ratio')
    if (not row['tournament'] or row['increment']!=0 or ratio is None
            or not math.isfinite(ratio) or not 0<=ratio<=1):return None
    return float(.45<=ratio<=.55)


def chronology(games):
    groups=defaultdict(list);census=Counter(source_games=len(games));output=[]
    for row in games:
        if not row['tournament']:census['non_tournament_games']+=1;continue
        if row.get('tournament_id') is None:census['missing_tournament_identity']+=1;continue
        groups[row['tournament_id']].append(row)
    for key in sorted(groups):
        rows=groups[key]
        if any(r['start'] is None for r in rows):
            census['unusable_missing_chronology_tournament']+=1
            census['games_in_missing_chronology_tournament']+=len(rows)
            continue
        rows=sorted(rows,key=lambda r:(r['start'],r['game']))
        # The first observed game need not be the player's first tournament
        # game before the corpus boundary. Carry possible capped streaks until
        # a known result history identifies the state (two wins suffice).
        possible_streaks={0,1,2}
        for index,row in enumerate(rows):
            streak=next(iter(possible_streaks)) if len(possible_streaks)==1 else None
            current=berserk(row);prev=rows[index-1] if index else None
            if row['increment']!=0:census['positive_increment_current_games']+=1
            elif current is None:census['missing_or_outside_current_clock']+=1
            elif prev is None:census['first_observed_tournament_game']+=1
            else:
                past_flag=berserk(prev)
                rating=row.get('rating');opponent=row.get('opponent_rating')
                complete=(past_flag is not None and prev['score'] in (0.,.5,1.)
                          and streak is not None and rating is not None and opponent is not None)
                if not complete:census['missing_prior_outcome_clock_streak_or_current_gap']+=1
                else:
                    lags=[rows[index-lag] if index>=lag else None for lag in range(1,5)]
                    output.append(dict(berserk=current,previous_score=prev['score'],previous_E=prev.get('E'),
                        rating_gap_hundreds=(rating-opponent)/100.,previous_berserk=past_flag,
                        streak_state=min(streak,2),win_bonus=float(streak>=2),game_number=index+1,
                        minutes_since_first=(row['start']-rows[0]['start'])/60.,
                        lag_scores=[None if r is None else r['score'] for r in lags],
                        lag_expectations=[None if r is None else r.get('E') for r in lags]))
                    census['qualified_current_games']+=1
            # Current outcomes enter only the next game's history, never its own.
            if row['score'] in (0.,.5):possible_streaks={0}
            elif row['score']==1:possible_streaks={min(value+1,2) for value in possible_streaks}
            else:possible_streaks={0,1,2}
    return output,dict(census)
