"""Actual SP1–SP3 handlers with signed/null known worlds and full bootstraps.

DESIGN CHECK: LESSONS 2–5, CONTROLS 6–7. Exact linear sensation curves identify
neutral temperature independently of sensitivity. Signed/null group and
weather-distance contrasts pass the same complete handlers used for data.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from . import week5_sp as base
from . import week5_sp_analysis_h1 as analysis


def world(card,sign):
    rows=[]
    for index in range(48):
        cooling=base.AC if index<24 else base.NV;weather=10+index%24
        neutral=22+(.1+sign*.3*float(cooling==base.NV))*(weather-20) if card=='SP1' else 22+.3*(weather-20)
        slope=.5+sign*.2*float(cooling==base.AC) if card=='SP2' else .8
        if card=='SP3' and cooling==base.NV:slope+=sign*.02*(np.floor(abs(weather-22)/3)*3+1.5)
        for temp in np.linspace(neutral-3,neutral+3,40):
            rows.append(dict(building_id=f'constructed-{index}',publication=f'study-{index//3}',cooling_type=cooling,
                             top=temp,thermal_sensation=slope*(temp-neutral),t_mot_isd=weather,thermal_acceptability='acceptable'))
    return pd.DataFrame(rows)


def run(output:Path,draws=2000):
    output.mkdir(parents=True,exist_ok=True);checks=[]
    for card,size in [('SP1',.3),('SP2',.2),('SP3',.02)]:
        for sign in [-1,0,1]:
            folder=output/f'{card}-{sign}';folder.mkdir(parents=True,exist_ok=True);source=folder/'constructed.parquet'
            world(card,sign).to_parquet(source,index=False);inputs={'data':str(source)};config={'phase':card,'draws':draws}
            result=analysis.execute(folder/'run',inputs,config)
            if result['status']!='ok' or abs(result['estimate']-sign*size)>1e-10:raise ValueError('SP actual signed/null handler failed')
            if not analysis.verify(folder/'run',inputs,config)['verified']:raise ValueError('SP actual replay failed')
            checks.append({'card':card,'sign':sign,'passed':True});base.write(output/'PROGRESS.json',{'completed':len(checks),'total':9})
    receipt={'passed':True,'constructed_only':True,'draws':draws,'signed_null_whole_handlers':checks,'complete_execute_verify':True}
    base.write(output/'FIXTURE.json',receipt);return receipt


def execute(output:Path,inputs:dict,config:dict):return run(output,config.get('draws',2000))
def verify(output:Path,inputs:dict,config:dict):
    if run(output/'fixture-replay',config.get('draws',2000))!=json.loads((output/'FIXTURE.json').read_text('utf8')):raise ValueError('SP fixture replay differs')
    return {'verified':True,'complete_fixture_replay':True}
