"""Known-answer full IN followup consumers; constructed observations only."""
from pathlib import Path
import numpy as np
import pandas as pd
from . import week5_in as core,week5_in_followup as follow
from .week5_in_fixture_v2 import frame,plant


def run(output):
    output.mkdir(parents=True,exist_ok=True);base=frame();checks=[]
    for sign in [-1,0,1]:
        data=plant(base,'IN1',sign);path=output/f'items-{sign}.parquet';data.to_parquet(path,index=False)
        for channel in ['anger','disgust']:
            config={'phase':'IN1.w','channel':channel,'draws':2000};inputs={'generation':str(path)};out=output/f'items-{sign}-{channel}'
            result=follow.execute(out,inputs,config);assert follow.verify(out,inputs,config)['verified']
            for value in result['items'].values():
                assert value['status']=='ok'
                assert abs(value['estimate'][0])<1e-10 if sign==0 else sign*value['estimate'][0]>.05
            checks.append({'phase':'IN1.w','channel':channel,'sign':sign,'full_execute_verify':True})
    gpath=output/'in3.parquet';plant(base,'IN3',0).to_parquet(gpath,index=False)
    inputs={'generation':str(gpath)};cfg={'phase':'IN3.ic','worlds':5,'draws':2000,'max_new_worlds':1}
    out=output/'IN3.ic';assert follow.execute(out,inputs,cfg)['status']=='yielded';cfg.pop('max_new_worlds')
    result=follow.execute(out,inputs,cfg);assert result['sensitivity_pass'];assert follow.verify(out,inputs,cfg)['verified']
    generation=[];validation=[]
    for label in core.PRIMARY:
        for i in range(40):
            key=f'{label}-{i}';generation.append({**dict.fromkeys(core.APPRAISALS,3.),'emotion':label,'text_id':key,'word_count':20+i,'prolific_id':str(i)})
            for reader in range(5):validation.append({**dict.fromkeys(core.APPRAISALS,3.),'text_id':key,'prolific_id':str(reader)})
    gp=output/'in4-g.parquet';vp=output/'in4-v.parquet';pd.DataFrame(generation).to_parquet(gp,index=False);pd.DataFrame(validation).to_parquet(vp,index=False)
    inputs={'generation':str(gp),'validation':str(vp)};cfg={'phase':'IN4.ic','worlds':5,'draws':2000};out=output/'IN4.ic'
    result=follow.execute(out,inputs,cfg);assert result['sensitivity_pass'];assert follow.verify(out,inputs,cfg)['verified']
    rng=np.random.default_rng(99);x=np.column_stack([np.ones(120),rng.normal(size=(120,2))]);y=rng.normal(0,1000,120);ids=np.repeat(np.arange(40),3)
    failure=follow.calibrate(x,y,ids,np.array([0.,1.,0.]),.1,{'worlds':5,'draws':2000},output/'unreliable')
    assert failure['status']=='ok' and not failure['sensitivity_pass']
    result={'passed':True,'constructed_only':True,'itemwise_signed_null':checks,'IN3_IN4_actual_execute_verify':True,
            'calibration_worlds_per_effect':5,'signed_effect_multiples':[-2,-1,0,1,2],'draws':2000,'pause_resume':True,
            'reachable_sensitivity_failure':True,'module_sha256':core.digest(Path(follow.__file__))}
    core.write_json(output/'FIXTURE.json',result);return result
