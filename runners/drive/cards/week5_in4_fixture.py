"""Actual IN4 agreement execution under both signs and an exact null.

DESIGN CHECK: LESSONS 2–5, CONTROLS 6–7. Identical readers have zero pairwise
error. Only a known writer discrepancy in the profile or outside comparator
sets the signed contrast. The whole 2,000-text-cluster bootstrap is replayed.
"""
from pathlib import Path
import json
import pandas as pd
from . import week5_in as base
from . import week5_in_analysis_h1 as analysis


def run(output:Path,draws=2000):
    output.mkdir(parents=True,exist_ok=True)
    for sign in [-1,0,1]:
        generation=[];validation=[]
        for label in base.PROFILES:
            for index in range(40):
                text=f'constructed-{label}-{index}'
                row={**dict.fromkeys(base.APPRAISALS,3.),'emotion':label,'text_id':text,'word_count':10+index,'prolific_id':str(index)}
                generation.append(row)
                changed=list(base.PROFILES[label]) if sign>0 else base.OUTSIDE if sign<0 else []
                for reader in range(5):
                    r={**dict.fromkeys(base.APPRAISALS,3.),'text_id':text,'prolific_id':f'reader-{reader}'}
                    for name in changed:r[name]=4.
                    validation.append(r)
        folder=output/f'sign-{sign}';folder.mkdir(parents=True,exist_ok=True)
        g=folder/'generation.parquet';v=folder/'validation.parquet'
        pd.DataFrame(generation).to_parquet(g,index=False);pd.DataFrame(validation).to_parquet(v,index=False)
        inputs={'generation':str(g),'validation':str(v)};config={'phase':'IN4','draws':draws}
        result=analysis.execute(folder/'run',inputs,config)
        if result['status']!='ok' or abs(result['estimate'][0]-sign)>1e-10:
            raise ValueError('IN4 signed/null exact handler failed')
        for r in result['secondary_channels'].values():
            if r['status']!='ok' or abs(r['estimate'][0]-sign)>1e-10:raise ValueError('IN4 channel handler failed')
        if not analysis.verify(folder/'run',inputs,config)['verified']:raise ValueError('IN4 replay failed')
    receipt={'passed':True,'constructed_only':True,'signed_and_exact_null':True,'draws':draws,'complete_execute_verify':True,'all_primary_channels':True}
    base.write_json(output/'FIXTURE.json',receipt);return receipt


def execute(output:Path,inputs:dict,config:dict):return run(output,config.get('draws',2000))
def verify(output:Path,inputs:dict,config:dict):
    if run(output/'fixture-replay',config.get('draws',2000))!=json.loads((output/'FIXTURE.json').read_text('utf8')):raise ValueError('fixture replay differs')
    return {'verified':True,'complete_fixture_replay':True}
