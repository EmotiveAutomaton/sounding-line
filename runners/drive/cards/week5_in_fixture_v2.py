"""Constructed signed/exact-null plants through the actual IN analysis handlers.

DESIGN CHECK: LESSONS 2–5; CONTROLS 6–7. Positive and negative coefficients
must preserve direction after source-column mapping and normalization. A
response entirely explained by a nuisance control must produce a zero target
coefficient. Every primary handler executes and verifies its full bootstrap.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from . import week5_in as core
from . import week5_in_analysis_h1 as analysis


def frame(seed=108):
    rng=np.random.default_rng(seed);parts=[]
    for label in core.PROFILES:
        f=pd.DataFrame(rng.uniform(1,5,(360,len(core.APPRAISALS))),columns=core.APPRAISALS)
        f['confidence']=rng.uniform(1,5,len(f));f['emotion']=label;f['word_count']=25
        f['prolific_id']=[f'constructed-writer-{i//3}' for i in range(len(f))]
        f['text_id']=[f'{label}-constructed-{i}' for i in range(len(f))]
        parts.append(f)
    return pd.concat(parts,ignore_index=True)


def plant(base,card,sign):
    f=base.copy();f['intensity']=3.
    for label in core.PROFILES:
        index=f.emotion.eq(label);d=f.loc[index]
        if card=='IN1':
            profile=core.PROFILES[label]
            z=core.standardize(d[list(profile)].to_numpy())*np.array(list(profile.values()))
            target=core.standardize(z.mean(axis=1))
            rival=core.standardize(d['pleasantness' if label=='joy' else 'unpleasantness'].to_numpy())
            y=sign*.8*target+.4*rival
        elif card=='IN2':
            z=core.standardize(d[['unpleasantness','predict_conseq','urgency','confidence']].to_numpy())
            target=core.standardize(z[:,0]*z[:,1]);y=sign*.8*target+.4*z[:,0]
        else:
            z=core.standardize(d[['self_control','unpleasantness']].to_numpy())
            y=sign*(.7 if label=='anger' else -.7)*z[:,0]+.5*z[:,1]
        # Synthetic ratings stay in the source scale without clipping or rounding.
        f.loc[index,'intensity']=3.+y*.4/max(1.,float(np.max(np.abs(y))))
    return f


def run(output: Path,draws=2000):
    output.mkdir(parents=True,exist_ok=True);base=frame();checks=[]
    for card in ('IN1','IN2','IN3'):
        for sign in (-1,0,1):
            folder=output/f'{card}-{sign}';folder.mkdir(parents=True,exist_ok=True)
            data=plant(base,card,sign);path=folder/'constructed.parquet';data.to_parquet(path,index=False)
            cfg={'phase':card,'draws':draws};inputs={'generation':str(path)}
            result=analysis.execute(folder,inputs,cfg);receipt=analysis.verify(folder,inputs,cfg)
            if result['status']!='ok' or not receipt['verified']:
                raise ValueError('constructed full handler failed')
            value=result['estimate'][0]
            if (sign==0 and abs(value)>1e-10) or (sign and sign*value<.5):
                raise ValueError('mapped target direction or exact null failed')
            if sign==0 and result['outcome']!='against':
                raise ValueError('exact null did not exclude effect bar')
            checks.append({'card':card,'sign':sign,'execute_verify':True,'target_recovered':True,'draws':draws})
    # Include partial joy/boredom mappings, not only the four-channel primary.
    for label in core.PROFILES:
        for sign in (-1,0,1):
            result=core.in1(plant(base,'IN1',sign),{'channels':[label],'draws':200})
            value=result.get('estimate',[float('nan')])[0]
            if result['status']!='ok' or (sign==0 and abs(value)>1e-10) or (sign and sign*value<.5):
                raise ValueError('single-prompt mapping failed')
    # Each actually fitted design must reject a fully constant predictor matrix.
    constant=base.copy()
    constant[core.APPRAISALS+['confidence','intensity']]=3.
    for fn in (core.in1,core.in2,core.in3):
        if fn(constant,{'draws':20})['status']!='rank_deficient':
            raise ValueError('rank failure not detected')
    result={'passed':True,'constructed_only':True,'primary_handlers':checks,
            'all_six_prompt_maps_signed_and_null':True,'rank_guards':True,
            'source_columns_and_interaction_parents_exercised':True}
    core.write_json(output/'FIXTURE.json',result);return result


def execute(output:Path,inputs:dict,config:dict):
    return run(output,config.get('draws',2000))


def verify(output:Path,inputs:dict,config:dict):
    result=run(output/'fixture-replay',config.get('draws',2000))
    if result!=json.loads((output/'FIXTURE.json').read_text('utf8')):
        raise ValueError('IN native complete fixture replay differs')
    return {'verified':True,'complete_fixture_replay':True}
