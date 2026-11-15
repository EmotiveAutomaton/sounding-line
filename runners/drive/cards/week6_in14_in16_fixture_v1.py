"""Constructed instruments only; never imports or reads a participant source.

DESIGN CHECK: LESSONS 2/3, CONTROLS 6/7. Fixed continuous instrument worlds
separate algebra from ordinal source encoding. Source ranks have separate tests.
"""
import numpy as np
import pandas as pd
from . import week6_in14_math_v1 as in14
from . import week5_in as original


def carryover(carry=.5, pairs=2000, writers=100, gaps=(2.,10.), seed=14):
    rng=np.random.default_rng(seed); rows=[]; offsets=rng.normal(0,.15,writers)
    for i in range(pairs):
        person=i%writers; first=str(rng.choice(in14.FEELINGS)); second=str(rng.choice([f for f in in14.FEELINGS if f!=first]))
        gap=float(rng.uniform(*gaps)); valence=in14.NEGATIVE if first in in14.NEGATIVE else in14.POSITIVE
        intensity=int(rng.integers(1,6));duration=int(rng.integers(1,6));second_intensity=float(rng.uniform(1,5))
        for feeling in in14.FEELINGS:
            baseline=float(rng.uniform(1,4));prompt=float(feeling==first);same=float(feeling in valence and feeling!=first);own=float(feeling==second)
            outcome=2+.3*(baseline-2)+offsets[person]+carry*np.exp(-gap/20)*prompt+.1*same+.12*own+rng.normal(0,.08)
            rows.append({'prolific_id':f'w{person:04}','pair_id':f'p{i:05}','first_text_id':f'a{i}','second_text_id':f'b{i}',
                'first_prompt':first,'second_prompt_label':second,'second_round':'round-3','feeling':feeling,'gap_minutes':gap,
                'baseline':baseline,'outcome':outcome,'prompt':prompt,'same_valence':same,'second_prompt':own,
                'first_intensity':intensity,'first_duration':duration,'second_intensity':second_intensity,'N':3.+person/writers})
    return pd.DataFrame(rows)


def share_frame(share=.2,writers=350,reports=8,seed=16):
    rng=np.random.default_rng(seed);n=writers*reports; people=np.repeat(np.arange(writers),reports)
    x=rng.normal(size=(n,21));prompts=np.where(np.arange(n)%2,'fear','joy')
    effects=rng.normal(0,np.sqrt(share),writers);error=rng.normal(0,np.sqrt(1-share),n)
    y=effects[people]+error+.1*x[:,0]+.15*(prompts=='joy')
    table=pd.DataFrame(x,columns=original.APPRAISALS)
    table['prolific_id']=[f'w{i:04}' for i in people];table['text_id']=[f't{i:06}' for i in range(n)]
    table['emotion']=prompts;table['intensity']=y
    return table


def clearing_frame(slope=.2,writers=250,reports=8,seed=161):
    table=share_frame(0,writers,reports,seed);rng=np.random.default_rng(seed+1)
    item=np.linspace(1,7,writers);rng.shuffle(item);table['N']=np.repeat(item,reports)
    table['event_duration_rank']=rng.integers(1,6,len(table));table['no_emotion_reported']=False
    table['emotion_duration_rank']=0.
    from . import week5_in12_math_v1 as inventory
    for _,idx in table.groupby('emotion').groups.items():
        part=table.loc[idx];n=part.N.to_numpy();n=n-n.mean()
        x=np.column_stack([np.ones(len(part)),n,part.intensity,part.event_duration_rank,part[list(inventory.STYLE)].mean(axis=1)])
        residual=rng.normal(size=len(part));residual-=x@np.linalg.lstsq(x,residual,rcond=None)[0]
        target_variance=1.-slope**2*np.var(n,ddof=1)
        residual*=np.sqrt(target_variance)/residual.std(ddof=1)
        table.loc[idx,'emotion_duration_rank']=3.+slope*n+residual
    return table
