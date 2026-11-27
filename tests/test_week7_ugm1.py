import numpy as np
import pandas as pd
import pytest

from runners.drive.cards.week7_ugm1 import fit, responders


def made():
    rng = np.random.default_rng(83)
    records = []
    for p in range(20):
        last = .2
        for trial in range(1, 21):
            offer, expect = rng.choice(np.arange(1,11)*.05, 2)
            gap = offer-expect
            val = p + 2*offer + 3*gap - 4*(offer-last)
            arousal = 10*p + (5 if gap>0 else 8)*abs(gap)
            records.append(dict(sub=p,role="self",trial=trial,reward=offer,RP=expect,RPE=gap,
                                EP_X1=0,EP_Y1=0,feedback_X1=val,feedback_Y1=arousal,
                                EPE_X1=val,EPE_Y1=arousal))
            last = offer
    return pd.DataFrame(records)


def test_recovers_joint_and_both_signed_subset_slopes():
    frame = made()
    other = frame.copy()
    other["role"], other["sub"] = "other", other["sub"]+100
    results = fit(pd.concat([frame,other]).sample(frac=1,random_state=3), draws=80)
    for name, expected in zip(results["terms"], [2,3,-4,5,8]):
        row = results["terms"][name]
        assert row["estimate"] == pytest.approx(expected)
        np.testing.assert_allclose(row["interval"],[expected,expected])
    assert not results["registered_bar_met"] and results["trials_without_previous"]==20
    assert results["observer_trials"]==400


def test_missing_round_does_not_become_a_change_and_missing_rating_keeps_offer_history():
    data=made()
    data=data.drop(data[(data["sub"]==1)&(data.trial==4)].index)
    data.loc[(data["sub"]==1)&(data.trial==6),["feedback_X1","EPE_X1"]]=np.nan
    out=responders(data)
    out=out[out["sub"]==1].set_index("trial")
    assert pd.isna(out.loc[5,"change"])
    assert out.loc[7,"change"]==pytest.approx(out.loc[7,"reward"]-out.loc[6,"reward"])


def test_collinearity_and_bad_source_fail_closed():
    data=made()
    data["RP"]=.2
    data["RPE"]=data.reward-.2
    assert not fit(data,40)["terms"]["gap"]["identified"]
    data.loc[0,"RPE"]+=.1
    with pytest.raises(ValueError,match="binding"): responders(data)
    with pytest.raises(ValueError,match="duplicate"): responders(pd.concat([data,data]))

