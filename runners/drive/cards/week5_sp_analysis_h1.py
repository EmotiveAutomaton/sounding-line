"""SP analysis companion table; frozen primary estimators are unchanged.

DESIGN CHECK: LESSONS 2–5, CONTROLS 6–7. SP3 reports neutral-location movement
beside sensitivity change by the same weather-distance bins. A changing neutral
point cannot be silently interpreted as sensory dulling. Sparse bins retain
counts; no extra directional tests are added.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from . import week5_sp as core


def result(data,config):
    answer=core.analyse(data,config)
    if config['phase']=='SP3':
        table,_=core.building_summaries(data,config)
        if len(table)<20:table,_=core.building_summaries(data,{**config,'allow_small':True})
        rows=[]
        if not table.empty:
            if config.get('side')=='hot':table=table.loc[table.weather>=22]
            if config.get('side')=='cold':table=table.loc[table.weather<22]
            if config.get('range_matched'):table=core.range_match_bins(table)
            table=table.loc[table.cooling.eq(core.NV)].dropna(subset=['weather']).copy()
            table['distance_bin']=np.floor(np.abs(table.weather-22)/3).astype(int)
            for band,g in table.groupby('distance_bin',sort=True):
                rows.append({'distance_low_celsius':3*int(band),'distance_high_celsius':3*(int(band)+1),
                             'buildings':len(g),'observations':int(g.n.sum()),'mean_slope':float(g.slope.mean()),
                             'mean_neutral_celsius':float(g.neutral.mean()),'mean_observed_celsius':float(g.mean_temp.mean()),
                             'mean_outdoor_celsius':float(g.weather.mean()),'median_observed_range_celsius':float(g['range'].median())})
        answer['weather_distance_bin_descriptives']=rows
    return answer


def execute(output:Path,inputs:dict,config:dict):
    value=result(pd.read_parquet(inputs['data']),config);core.write(output/'RESULT.json',value);return value


def verify(output:Path,inputs:dict,config:dict):
    value=result(pd.read_parquet(inputs['data']),config)
    if value!=json.loads((output/'RESULT.json').read_text('utf8')):raise ValueError('SP analysis and companion replay mismatch')
    return {'verified':True,'primary_and_companion_replayed':True}
