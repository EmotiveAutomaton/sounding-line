import numpy as np
import pandas as pd
import pytest
from runners.drive.cards.week7_psd2_checklist import COLUMNS, describe


def grid():
    # Pride and embarrassment are independent; guilt coincides with pride.
    return pd.DataFrame([(i, a, b, a) for i in range(24) for a in (0,1) for b in (0,1)],columns=COLUMNS)


def test_independence_and_complete_coincidence():
    result = describe(grid())['pairs']
    assert result['Embarassment']['interval']==[1,1]
    assert result['Guilt']['interval']==[2,2]
    assert result['Guilt']['eligible_prompts']==96


def test_missing_and_ineligible_are_pair_specific():
    data = grid()
    data.loc[data.id==0,'Embarassment'] = np.nan
    data.loc[data.id==1,'Embarassment'] = 0
    result = describe(data)['pairs']
    assert result['Embarassment']['eligible_people']==22
    assert result['Embarassment']['pairwise_missing_prompts']==4
    assert result['Guilt']['eligible_people']==24


def test_prompt_weights_and_bounds():
    data=grid()
    data=pd.concat([data,pd.DataFrame([(24,1,0,0),(24,0,1,1)], columns=COLUMNS)])
    assert describe(data)['pairs']['Embarassment']['ratio']==pytest.approx(96/98)
    assert 'ratio' not in describe(data[data.id<19])['pairs']['Guilt']
    data.loc[data.id==0,'Pride']=2
    with pytest.raises(ValueError,match='binary'):
        describe(data)

