import numpy as np
import pandas as pd
from runners.drive.cards import week5_sp as m


def test_fixture():
    assert m.fixture()['passed']


def test_griffiths_fallback_uses_mean_sensation():
    data=pd.DataFrame({'building_id':['a']*40,'publication':['s']*40,'cooling_type':[m.NV]*40,
                       'top':np.linspace(20,26,40),'thermal_sensation':np.full(40,.5),
                       't_mot_isd':np.full(40,20.),'thermal_acceptability':['acceptable']*40})
    table,_=m.building_summaries(data,{})
    assert table.griffiths.iloc[0]
    assert abs(table.neutral.iloc[0]-22)<1e-12


def test_missing_weather_never_imputed():
    table=pd.DataFrame({'cooling':[m.NV,m.AC],'weather':[np.nan,np.nan],'neutral':[20.,25.]})
    assert m.estimate(table,'SP1') is None


def test_range_bin_matching_keeps_every_supported_bin():
    table=pd.DataFrame({'building':list('abcdef'),'cooling':[m.NV]*6,'weather':[22,23,26,27,29,30],
                        'range':[2,4,2,4,2,4]})
    matched=m.range_match_bins(table)
    assert len(matched)==6


def test_grid_covers_three_primaries():
    assert {r['phase'] for r in m.grid()}=={'SP1','SP2','SP3'}
