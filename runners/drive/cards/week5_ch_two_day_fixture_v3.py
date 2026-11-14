"""Constructed table fixtures with hand answers and separately planted truth."""
import math
import numpy as np
from . import week5_ch8_math_v3 as ch8
from . import week5_ch12_math_v1 as ch12


def ch8_players(effect=.06,people=400,seed=993):
    rng=np.random.default_rng(seed);players={}
    for i in range(people):
        rows=[]
        for b,e in enumerate([.2,.5,.8]):
            target=.2+(effect if b==2 else effect/2 if b==1 else 0)
            if b==2 and effect:target+=.04*math.sin(2*math.pi*i/people)
            outcome=np.zeros(100);outcome[:round(target*100)]=1;rng.shuffle(outcome)
            for j,y in enumerate(outcome):
                rows.append(dict(time_control='blitz',provisional_session=False,censored=False,
                    E=e,score=0.,surprise=-e,form_before=0.,session_id=f'{i}:{j//10}',
                    index_in_session=j%10+1,losing_streak=j%3+1,start=1491004800+j*600,
                    tournament=False,stop=bool(y),rematch=not bool(y) and j%2==0,
                    previous_start_gap=600.,remaining_games=9-j%10,rating_change=-round(20*e)))
        players[str(i)]=rows
    return players


def ch8_proof(effect=.06,draws=2000,reference=False):
    prepared=ch8.estimate(ch8_players(effect),floor=300,reference=reference)
    rng=np.random.default_rng(20261112);values=[];n=len(prepared['names'])
    for _ in range(draws):
        weights=np.bincount(rng.integers(0,n,n),minlength=n)
        values.append(ch8.draw(prepared,weights,reference))
    result=ch8.result(prepared,values)
    primary=result['estimates']['primary']
    assert 'coefficients' in primary,repr(primary)
    assert abs(primary['coefficients'][0]-effect)<1e-9,'Planted adjusted contrast differs'
    ci=primary['intervals'][0]
    assert ci is not None and ci[0]-1e-9<=effect<=ci[1]+1e-9,'Planted contrast outside interval'
    return result


def ch12_proof():
    worlds=ch12.constructed_controls()
    for world in worlds.values():
        for name in ch12.INDEX_NAMES:
            answer=world['estimate'][name]
            assert answer['status']=='complete'
            assert abs(answer['stability']-world['expected'])<.1,'TR1 stability control missed truth'
    return worlds
