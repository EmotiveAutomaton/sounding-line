import numpy as np
import pandas as pd
import pytest
from runners.drive.cards import week6_person_more_sources_v1 as sources
from runners.drive.cards import week6_person_more_pairs_v1 as pairs
from runners.drive.cards import week6_person_ladder_v1 as base

def frame(member,n=120):
    rng=np.random.default_rng(42)
    sizes=48
    out={'id':np.repeat(np.arange(n).astype(str),sizes),'day':np.tile(np.arange(1,25).repeat(2),n)}
    for col in (*sources.SOURCES[member][0],*sources.SOURCES[member][1]):
        hi=7 if member=='0072' else 5 if member in ('0060','0076') else 6
        lo=1
        if col in sources.PARENT_EVENTS[:2] or col in ('argument_family','argument_friend'):lo,hi=0,1
        if col=='interaction':hi=2
        if col=='intellect':hi=3
        out[col]=rng.integers(lo,hi+1,len(out['id']))
    if member=='0072':out['day']=np.tile(np.arange(1,sizes+1),n)
    return pd.DataFrame(out)

@pytest.mark.parametrize('member',['0056','0057','0060','0072','0076'])
def test_context_and_rosters(member):
    f=frame(member,5)
    if member=='0072':
        f.loc[0,'day']=f.loc[1,'day']
        f.loc[2,['stressor_health','stressor_financial']]=[1,np.nan]
        f.loc[3,['stressor_health','stressor_financial']]=[0,np.nan]
    if member=='0076':f.loc[0,'interaction_pleasant']=np.nan
    data=sources.project(f,member);assert data['n']==5
    assert np.unique(data['splits']['time']).tolist()==[0,1]
    if member=='0072':
        assert data['counts']['duplicate_day_rows']==2
        result=data['slopes']['stressor_fear'][0]
        assert result[0]==1 and np.isnan(result[1])
    elif member=='0076':
        assert len(data['ids'])==len(f)-1 and not data['unpleasant']
    elif member=='0057':
        interaction=data['slopes']['criticised_anger'][0];alone=data['slopes']['intellectual_occup_relaxed'][0]
        assert not np.any(np.isfinite(interaction)&np.isfinite(alone))
    elif member=='0060':
        assert np.allclose(data['slopes']['curiosity_minus_contentment'][1],data['feelings']['curious']-data['feelings']['content'])
    else: assert len(data['ids'])==int(sum(f.interaction==1))
    a,fa=base.half_panel(data,data['splits']['time'],False);b,fb=base.half_panel(data,data['splits']['time'],True)
    for k in a:
        for j in range(2):
            for key in a[k][j]:assert np.allclose(a[k][j][key],b[k][j][key],equal_nan=True)

def test_joint_planted_and_empty_pairs(monkeypatch):
    monkeypatch.setattr(base,'DRAWS',100)
    rng=np.random.default_rng(63);n=320
    factor=rng.normal(size=n);groups={};singles={}
    for k in ['a','b','c']:
        true=.85*factor+.45*rng.normal(size=n)
        level=rng.normal(size=n)
        groups[k]=[dict(b=true+.15*rng.normal(size=n),L=level+.1*rng.normal(size=n),
                        S=np.ones(n),n1=np.ones(n),n0=np.ones(n)) for _ in (0,1)]
        singles[k]=dict(adjusted_variance=dict(interval=[.2,1.5]))
    groups['c'][0]['b'][:15]=np.nan
    rows,pool=pairs.summarize(groups,n,list(groups),singles,37,lambda:None)
    assert len(rows)==3 and pool['qualifying_pairs']==3 and pool['reading']=='one'
    assert pool['first_factor_share']>.5
    assert rows['a / b']['people']==320 and rows['b / c']['people']==305
    assert pairs.summarize(groups,n,['a'],singles,37,lambda:None)[1]['qualifying_pairs']==0

