"""Constructed reciprocal conversations and known answers for the liking gap."""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'runners/drive/sealed/week6-sm-science'),str(ROOT/'runners/drive/cards')]
from runners.drive.sealed import week8_lkg1 as study


def sample():
    rng=np.random.default_rng(72871)
    count=160
    likes=rng.integers(2,6,count)
    bias=rng.choice([-1,0,1],count)
    rows=[]
    for k in range(4):
        people=rng.permutation(count).reshape(-1,2)
        for i,(a,b) in enumerate(people):
            directed=[(x,y,int(np.clip(likes[y]+rng.choice([-1,0,0,1]),1,7))) for x,y in [(a,b),(b,a)]]
            for side,(x,y,rating) in enumerate(directed):
                estimate=int(np.clip(directed[1-side][2]-1+bias[x],1,7))
                d=dict(conversation_id=f'm{k}-{i}',user_id=f'p{x:03}',partner_id=f'p{y:03}',
                       date=f'2026-05-{k+1:02}',i_like_you=rating,you_like_me=estimate)
                d.update(dict.fromkeys(study.HISTORY,5))
                rows.append(d)
    df=pd.DataFrame(rows)
    previous=dict(survey={k:count for k in ['user_id','technical_quality',*study.RATINGS,'date']},cad1=[count,0],sc2=count,lgh2=count)
    return df,previous


def test_gap_uses_other_persons_actual_rating():
    df,known=sample()
    panel,_,_=study.project(df,known)
    first=panel.iloc[0]
    other=df.loc[(df.conversation_id==first.conversation)&(df.user_id!=first.person)].iloc[0]
    assert first.R==other.i_like_you
    res=study.analyze(df,known,64)
    metrics={r['measure']:r for r in res['liking']}
    assert metrics[1]['estimate']==pytest.approx(panel.G.mean())
    assert metrics[1]['upper']<0
    assert metrics[2]['lower']>0 and metrics[3]['lower']>0
    assert set(metrics)==set(range(1,10))
    assert all(r['n']==160 for r in metrics.values())


def test_ambiguous_date_only_affects_ordered_measures():
    df,known=sample()
    df['date']='2026-05-01'
    result=study.analyze(df,known,48)
    assert set(r['measure'] for r in result['liking'])=={1,2,3,4}


def test_broken_reciprocity_removes_conversation_and_false_census_refuses():
    df,known=sample()
    cid=df.loc[0,'conversation_id']
    df.loc[0,'partner_id']=df.loc[0,'user_id']
    assert cid not in set(study.project(df,known)[0].conversation)
    known['survey']['user_id']-=1
    with pytest.raises(study.SealedFailure):
        study.project(df,known)


def test_unbalanced_icc_matches_literal_anova():
    y=[np.array([1.,2.]),np.array([4.,7.,4.]),np.array([3.,4.,5.,4.])]
    n=np.array(list(map(len,y)))
    sums=np.array([a.sum() for a in y]);squares=np.array([(a*a).sum() for a in y])
    avg=sums.sum()/n.sum()
    b=sum(len(a)*(a.mean()-avg)**2 for a in y)/(len(y)-1)
    e=sum(((a-a.mean())**2).sum() for a in y)/(n.sum()-len(y))
    n0=(n.sum()-(n@n)/n.sum())/(len(n)-1)
    assert study.icc(np.ones((1,3)),n,sums,squares)[0]==pytest.approx((b-e)/(b+(n0-1)*e))
