"""Native declared IN/SP texture-grid rehearsals on constructed observations."""
from pathlib import Path
import numpy as np
import pandas as pd
from . import week5_in as incore,week5_in_analysis_h1 as ina
from .week5_in_fixture_v2 import frame,plant
from . import week5_sp as sp,week5_sp_analysis_h1 as spa,week5_sp1_h2 as sp1


def in_grid(output):
    output.mkdir(parents=True,exist_ok=True);base=frame();paths={};checks=[]
    for task in ['IN1','IN2','IN3']:
        data=plant(base,task,1)
        if task=='IN1':
            for label in incore.PROFILES:
                use=data.emotion.eq(label);values=data.loc[use,'intensity'].to_numpy()-3
                data.loc[use,'intensity']=3.95+.35*values/max(abs(values));data.loc[use,'word_count']=np.arange(use.sum())%40
        paths[task]=output/(task+'.parquet');data.to_parquet(paths[task],index=False)
    generation=[];validation=[]
    for label in incore.PROFILES:
        for i in range(40):
            key=f'{label}-{i}';generation.append({**dict.fromkeys(incore.APPRAISALS,3.),'emotion':label,'text_id':key,'word_count':10+i,'prolific_id':str(i)})
            for reader in range(5):
                r={**dict.fromkeys(incore.APPRAISALS,3.),'text_id':key,'prolific_id':str(reader)}
                for item in incore.PROFILES[label]:r[item]=4.
                validation.append(r)
    gp=output/'IN4-generation.parquet';vp=output/'IN4-validation.parquet';pd.DataFrame(generation).to_parquet(gp,index=False);pd.DataFrame(validation).to_parquet(vp,index=False)
    for cfg in incore.grid():
        inputs={'generation':str(gp),'validation':str(vp)} if cfg['phase']=='IN4' else {'generation':str(paths[cfg['phase']])}
        result=ina.execute(output/cfg['cell'],inputs,cfg);assert result['status']=='ok'
        direction=-1 if cfg.get('variant')=='reverse' else 1
        assert direction*result['estimate'][0]>.05
        assert ina.verify(output/cfg['cell'],inputs,cfg)['verified']
        checks.append({'cell':cfg['cell'],'draws':cfg['draws'],'signed_effect_present':True,'complete_replay':True})
    receipt={'passed':True,'constructed_only':True,'declared_grid':checks,'cells':len(checks),
             'source_sha256':incore.digest(Path(incore.__file__)),'analysis_sha256':incore.digest(Path(ina.__file__))}
    incore.write_json(output/'FIXTURE.json',receipt);return receipt


def sp_grid(output):
    output.mkdir(parents=True,exist_ok=True);rng=np.random.default_rng(441);rows=[]
    for i in range(60):
        group=sp.AC if i<30 else sp.NV;weather=7+(i%30);distance=np.floor(abs(weather-22)/3)*3+1.5
        neutral=20+(.4 if group==sp.NV else .1)*(weather-20)
        slope=.9 if group==sp.AC else .7-.025*distance
        t=np.linspace(neutral-4,neutral+4,120);latent=slope*(t-neutral)+rng.normal(0,1,len(t));y=np.digitize(latent,[-2.5,-1.5,-.5,.5,1.5,2.5])-3
        for j in range(len(t)):
            rows.append({'building_id':f'b{i:03d}','publication':f's{i//2:03d}','cooling_type':group,'top':t[j],
                         'thermal_sensation':float(y[j]),'t_mot_isd':float(weather),'thermal_acceptability':'acceptable',
                         'window':int(rng.integers(0,2)),'fan':int(rng.integers(0,2)),
                         'clo':float(rng.uniform(.3,1.)), 'met':float(rng.uniform(.8,1.8)),'vel':float(rng.uniform(.05,.6))})
    data=output/'comfort.parquet';pd.DataFrame(rows).to_parquet(data,index=False);checks=[]
    for cfg in sp.grid():
        module=sp1 if cfg['phase']=='SP1' else spa;folder=output/cfg['cell'];result=module.execute(folder,{'data':str(data)},cfg)
        assert result['status']=='ok', (cfg['cell'],result['status'])
        assert np.isfinite(result['estimate']) and result['failed_draws']==0
        if cfg['phase']=='SP2':assert result['estimate']>.05
        if cfg['phase']=='SP3':assert result['estimate']<0
        assert module.verify(folder,{'data':str(data)},cfg)['verified']
        checks.append({'cell':cfg['cell'],'draws':cfg['draws'],'complete_replay':True,'latent_ordinal':bool(cfg.get('ordinal'))})
    receipt={'passed':True,'constructed_only':True,'declared_grid':checks,'cells':len(checks),'integer_ordinal_world':True,
             'source_sha256':sp.sha(Path(sp.__file__)),'analysis_sha256':sp.sha(Path(spa.__file__)),'sp1_sha256':sp.sha(Path(sp1.__file__))}
    sp.write(output/'FIXTURE.json',receipt);return receipt
