"""Constructed three-edition checks. No original survey is read."""
import numpy as np
import pandas as pd
import pytest

from runners.drive.sealed import week7_sld2_original as s


def made():
    ids = np.arange(101, 197)
    frames = []
    for wave in (1, 2, 3):
        f = pd.DataFrame(index=pd.Index(ids, name="M2ID"), columns=s.field_list(wave), dtype=float)
        f = f.drop(columns="M2ID")
        f["M2FAMNUM"] = ids // 2
        strength = np.resize([2, 3, 5, 6], len(ids))
        for idx, name in enumerate(s.PURPOSE[wave-1]):
            f[name] = 8-strength if idx == 0 else strength
        frames.append(f)
    a,b,_ = frames
    a["A1PI_YR"],a["A1PI_MO"] = 1995,6
    b["B1PIDATE_YR"],b["B1PIDATE_MO"] = 2005,6
    b.loc[ids[:48], ["B1PB19","B1PB29Y","B1PB29M"]] = [4,2000,6]
    b.loc[ids[48:], ["B1PB22","B1PB25Y","B1PB25M"]] = [2,2000,6]
    return frames


def test_overlap_and_interview_month_boundaries():
    a,b,c = made()
    b.loc[101,["B1PB22","B1PB25Y","B1PB25M"]] = [2,2001,7]
    b.loc[102,["B1PB29Y","B1PB29M"]] = [1995,6]
    b.loc[103,["B1PB29Y","B1PB29M"]] = [2005,6]
    b.loc[104,"B1PB19"] = 2
    b.loc[105,"B1PB29M"] = 97
    death,divorce=s.loss_flags(a,b)
    assert death[101] and divorce[101]
    assert not death.loc[102:105].any()
    assert (death|divorce).sum() == 92


def test_midpoint_and_item_direction():
    frames=made()
    frames[0].loc[102,"A1SF1G"] = 4
    frames[1].loc[103,"B1SE1OO"] = 4
    frames[2].loc[104,"C1SE1QQ"] = 9
    a,b,c = s.scored(frames,False)
    assert list(a.loc[0,list(s.ITEMS)]) == [2,2,2]
    assert pd.isna(a.loc[1,"future"]) and b.loc[2,"aim"] == 4 and pd.isna(c.loc[3,"done"])
    assert pd.isna(s.scored(frames,True)[1].loc[2,"aim"])


def test_small_complement_suppresses_secondary():
    frames=made()
    frames[1].loc[101,"B1SE1OO"] = 4
    rows = s.analyze(frames,40)
    assert any(r["group"]==1 and r["reading"]==1 and r["n"]==96 for r in rows)
    assert not any(r["group"]==1 and r["reading"]==2 for r in rows)


def test_paired_return_and_family_conflict():
    frames=made()
    rows=s.analyze(frames,40)
    changes=[r for r in rows if r["measure"]==4]
    assert len(changes)==6 and all(r["estimate"]==r["lower"]==r["upper"]==0 for r in changes)
    frames[2].loc[101,"M2FAMNUM"] += 1
    with pytest.raises(s.SealedFailure):
        s.analyze(frames,40)

