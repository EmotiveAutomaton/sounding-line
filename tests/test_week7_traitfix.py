import pandas as pd
import pytest
from tests.test_week7_trait import test_packet_trait_operator,test_period_cut_support_and_replay
from runners.drive.cards.week7_traitfix_v1 import unique_traits


def test_unique_observation_per_person():
    raw=pd.DataFrame({'id':['a','a','a','b','b'],'neuroticism':[4,None,4,None,None]})
    rows=unique_traits(raw)
    assert len(rows)==2 and rows.neuroticism.iloc[0]==4 and pd.isna(rows.neuroticism.iloc[1])
    raw.loc[1,'neuroticism']=5
    with pytest.raises(ValueError,match='Conflicting'):unique_traits(raw)
