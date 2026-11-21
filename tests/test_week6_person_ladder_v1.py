"""Round 34 constructed source and scoring checks."""
import numpy as np
import pandas as pd
import pytest
from runners.drive.cards import week6_person_ladder_v1 as card
from runners.drive.cards.week5_rr3_v1 import compare_record


def made(member,n=30):
    rng=np.random.default_rng(3434)
    names=card.CONFIG[member][0]
    rows=[]
    for i in range(n):
        for day in range(1,9):
            for event in (0,1):
                row={key:int(rng.integers(1,6)) for key in names}
                row.update(id=str(i),day=day)
                if member=='0060':
                    row.update(intellect=1+event,argument_family=event,argument_friend=0)
                else:
                    row.update(interaction=1,status_criticised=1+event)
                rows.append(row)
    return pd.DataFrame(rows)


def test_student_binding():
    d=card.project(made('0060',3),'0060')
    rows,_=card.half_panel(d,d['splits']['time'],False)
    support=card.slope_support(rows)
    assert support['curiosity']==dict(people=3,events=[12,12],others=[12,12],excluded_people=0)
    assert np.array_equal(d['splits']['time'][:16],np.repeat([0,1],8))


def test_status_context():
    f=made('0057',3)
    f.loc[0,'interaction']=2
    f.loc[1,'day']=np.nan
    d=card.project(f,'0057')
    assert d['counts']['dated_context_reports']==46
    assert set(d['slopes'])=={'criticism_anger','criticism_shame'}


def test_reject_out_of_range():
    f=made('0060',1)
    f.loc[0,'intellect']=7
    with pytest.raises(ValueError,match='coding'):card.project(f,'0060')


def test_sparse_exposure():
    f=made('0060',3)
    f.loc[f.id=='1','intellect']=1
    d=card.project(f,'0060')
    groups,_=card.half_panel(d,d['splits']['time'],False)
    s=card.slope_support(groups)
    assert s['curiosity']['people']==2 and s['argument_anger']['people']==3


def test_original_and_grouped_replay(monkeypatch):
    monkeypatch.setattr(card,'DRAWS',100)
    d=card.project(made('0057'),'0057')
    halves=d['splits']['time']
    a=card.analyze_split(d,halves,110,False,lambda:None)
    b=card.analyze_split(d,halves,110,True,lambda:None)
    compare_record(a,b)
    assert a['PST2']['arms']['added_slopes']['valid_draws']==100
    assert len(a['PST2']['arms'])==4


def test_registered_decisions():
    pair=lambda v,l,u:card.factor_reading(dict(status='estimable pair',adjusted_correlation=dict(estimate=v,interval=[l,u])))['reading']
    assert [pair(.5,.31,.7),pair(.29,0,.49),pair(.5,.30,.7)]==['one','several','undecided']
    assert card.factor_reading(dict(status='no supported pair'))['reading']=='no verdict'
    assert card.variance_reading([-.02,.1],{'upper':.49})=='flat within bound'
    assert card.variance_reading([-.02,.1],None)=='could not say'
