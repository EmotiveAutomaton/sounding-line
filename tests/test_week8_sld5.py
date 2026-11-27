"""Known-answer three-wave tests; all people and survey values are constructed."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'runners/drive/sealed/week6-sm-science'),str(ROOT/'runners/drive/cards')]
from runners.drive.sealed import week8_sld5 as study


def panels(recovery=False):
    ids=np.arange(400)
    base=np.resize([6,7,3,2],len(ids))
    group=ids//80
    frames=[]
    for w in range(3):
        df=pd.DataFrame(np.nan,index=pd.Index(ids,name='M2ID'),columns=[c for c in study.fields(w+1) if c!='M2ID'])
        df.M2FAMNUM=ids//2+1
        y=base-np.where((group<2)&(w>0)&(not recovery or w==1),1,0)
        for k,col in enumerate(study.old.PURPOSE[w]):
            df[col]=8-y if k==0 else y
        df[study.STATUS[w]]=1
        frames.append(df)
    a,b,c=frames
    a[study.AGE]=40+(ids%3)*10
    a['A1PI_MO'],a['A1PI_YR']=6,1995
    for f,prefix,year in [(b,'B1',2005),(c,'C1',2015)]:
        f[prefix+'PIDATE_MO'],f[prefix+'PIDATE_YR']=6,year
    b.loc[group==0,['B1PB19','B1PB29M','B1PB29Y']]=[4,6,2000]
    b.loc[group==1,['B1PB19','B1PB28M','B1PB28Y']]=[3,6,2000]
    c.loc[group==0,'C1PB19']=4
    c.loc[group==1,'C1PB19']=3
    c.loc[group==2,['C1PB19','C1PB29M','C1PB29Y']]=[4,6,2010]
    known={f'{g}-{mode}':160 if g==1 else 80 for g in (1,2,3) for mode in (1,2)}
    return frames,known


@pytest.mark.parametrize('recovery,expected',[(False,[-1,-1,0]),(True,[-1,0,1])])
def test_age_standardized_changes_and_before_loss(recovery,expected):
    frames,known=panels(recovery)
    res=study.calculate(frames,known,40)['purpose']
    for g in [1,2,3]:
        chosen=[r for r in res if r['group']==g and r['form']==1]
        assert [r['transition'] for r in chosen]==[1,2,3]
        for r,value in zip(chosen,expected):
            assert r['n']==known[f'{g}-1']
            assert np.allclose([r['lower'],r['estimate'],r['upper']],value)
    before=next(r for r in res if r['group']==4 and r['form']==1)
    assert before['n']==80 and np.isclose(before['estimate'],0)


def test_no_event_order_in_interview_month_or_unknown_age_decade():
    frames,known=panels()
    obs,_,comp,later=study.membership(frames,known)
    assert len(comp)==160 and len(later)==80
    frames[2].loc[160,'C1PB29Y']=2005
    assert 160 not in study.membership(frames,known)[3]
    g=frozenset(range(80))
    obs.loc[0,'age']=90
    assert not study.estimates(obs,g,comp,study.PAIRS,20)


def test_changed_historical_roster_refuses():
    frames,known=panels()
    known['1-1']-=1
    with pytest.raises(study.SealedFailure):
        study.calculate(frames,known,10)
