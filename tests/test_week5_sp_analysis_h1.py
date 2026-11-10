import pandas as pd
import numpy as np
from runners.drive.cards import week5_sp as core,week5_sp_analysis_h1 as analysis


def test_actual_sp3_handler_reports_location_beside_sensitivity(tmp_path):
    rows=[]
    for i in range(48):
        weather=10+i%24;center=np.floor(abs(weather-22)/3)*3+1.5
        neutral=20+.3*(weather-20);slope=.8-.02*center
        for t in np.linspace(neutral-3,neutral+3,40):
            rows.append(dict(building_id=f'constructed-{i}',publication=f'study-{i//3}',cooling_type=core.NV,
                             top=t,thermal_sensation=slope*(t-neutral),t_mot_isd=weather,thermal_acceptability='acceptable'))
    path=tmp_path/'constructed.parquet';pd.DataFrame(rows).to_parquet(path,index=False)
    cfg={'phase':'SP3','draws':50};inputs={'data':str(path)}
    r=analysis.execute(tmp_path/'run',inputs,cfg)
    assert r['status']=='ok' and abs(r['estimate']+.02)<1e-10
    assert sum(v['buildings'] for v in r['weather_distance_bin_descriptives'])==48
    assert analysis.verify(tmp_path/'run',inputs,cfg)['verified']
