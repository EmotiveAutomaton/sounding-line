import numpy as np
import pandas as pd
from runners.drive.cards import week5_sp as old,week5_sp1_h2 as new


def table():
    rows=[]
    for group,coefficient in [(old.AC,.1),(old.NV,.4),(old.MM,.7)]:
        for weather in range(10,25):rows.append(dict(cooling=group,weather=float(weather),neutral=21+coefficient*weather))
    return pd.DataFrame(rows)


def test_full_rank_joint_and_separate_are_identical():
    data=table();rng=np.random.default_rng(91)
    for _ in range(100):
        sample=data.iloc[rng.integers(0,len(data),len(data))]
        assert np.isclose(old.estimate(sample,'SP1'),new.estimate(sample,'SP1'),atol=1e-12)


def test_rank_loss_only_in_nuisance_does_not_change_estimand():
    data=table();data.loc[data.cooling.eq(old.MM),'weather']=20.
    assert old.estimate(data,'SP1') is None
    assert np.isclose(new.estimate(data,'SP1'),.3)


def test_primary_group_rank_loss_still_refuses():
    data=table();data.loc[data.cooling.eq(old.NV),'weather']=20.
    assert new.estimate(data,'SP1') is None
