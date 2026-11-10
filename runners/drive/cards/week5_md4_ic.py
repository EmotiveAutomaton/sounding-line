"""MD4 conditional minimum-effect calibration after fixed person OLS projection.

DESIGN CHECK: preserve first-block eligibility, equal-person weights and all
observational condition/cohort limitations. Synthetic slopes are estimator
calibration responses, never claimed to be new valid raw mood ratings.
"""
from pathlib import Path
import json
import time
import numpy as np
from . import week5_md4_analysis as primary
from .week5_at_source import authenticate
from .week5_go import write,sha
from .week5_la2_ic import requested,matrix_hash


def operators(rows,draws):
    n=len(rows);point=np.zeros((3,n));bank=np.zeros((draws,3,n));rng=np.random.default_rng(primary.SEED)
    counts={}
    for c,condition in enumerate(primary.CONDITIONS):
        ids=np.asarray([i for i,r in enumerate(rows) if r['condition']==condition],dtype=int)
        counts[condition]=len(ids)
        if len(ids)<2:raise ValueError('condition lacks independent person uncertainty')
        point[c,ids]=1/len(ids)
        for draw in range(draws):
            selected=ids[rng.integers(0,len(ids),len(ids))]
            np.add.at(bank[draw,c],selected,1/len(ids))
    if counts['rest']<20 or counts['visuomotor']<20:raise ValueError('below primary twenty-person condition floor')
    return point,bank,counts


def calibrate(rows,config,output,binding):
    cpu_started=time.process_time();output=Path(output);output.mkdir(parents=True,exist_ok=True)
    draws=config.get('draws',2000);worlds=config.get('worlds',100)
    if draws!=2000 or worlds!=100:raise ValueError('registered sensitivity requires 100 worlds and 2000 draws')
    y=np.array([r['slope'] for r in rows]);codes=np.array([primary.CONDITIONS.index(r['condition']) for r in rows])
    binding=dict(binding,source_projection=matrix_hash(y,codes),module_sha256=sha(__file__),parent_module_sha256=sha(primary.__file__),draws=draws,worlds=worlds)
    bp=output/'BINDING.json'
    if bp.exists() and json.loads(bp.read_text('utf8'))!=binding:raise ValueError('MD4 instrument binding changed')
    write(bp,binding)
    try:point,bank,counts=operators(rows,draws)
    except ValueError as error:return dict(status='design cannot test',card='MD4.ic',reason=str(error))
    means=point@y;residual=y-means[codes]
    base=means[codes].copy();base[codes==1]=means[0]
    started=time.monotonic();world_cpu=time.process_time();new=0;results=[]
    for multiple in (-1,0,1):
        records=[];truth=multiple*primary.BAR
        for world in range(worlds):
            path=output/'worlds'/f'{multiple}-{world:03d}.json';seal=path.with_suffix('.seal.json')
            if path.exists():
                saved=json.loads(seal.read_text('utf8'))
                if saved['binding']!=binding or saved['sha256']!=sha(path):raise ValueError('MD4 sensitivity world changed')
                record=json.loads(path.read_text('utf8'))
            else:
                # max_new_draws uses the runtime's existing operational contract;
                # one complete 2000-draw world is the minimum indivisible unit.
                if new>=config.get('max_new_draws',600000) or requested(output) or time.monotonic()-started>=config.get('max_wall_seconds',900):
                    return dict(status='yielded',complete_card=False,new_draws=new,world=world,effect_multiple=multiple)
                rng=np.random.default_rng(np.random.SeedSequence([primary.SEED,world,904]))
                value=base+truth*(codes==1)+residual*rng.choice([-1.,1.],len(rows))
                condition_point=point@value;sample=np.einsum('dcn,n->dc',bank,value)
                intervals=np.quantile(sample,[.025,.975],axis=0)
                contrast=sample[:,1]-sample[:,0];lo,hi=np.quantile(contrast,[.025,.975])
                record=dict(estimate=float(condition_point[1]-condition_point[0]),interval=[float(lo),float(hi)],
                    rest_interval=intervals[:,0].tolist(),covers_truth=bool(lo-1e-12<=truth<=hi+1e-12),
                    excludes_zero=bool(lo>1e-12 if multiple>0 else hi< -1e-12 if multiple<0 else lo>1e-12 or hi< -1e-12),
                    primary_positive_support=bool(primary.rule([lo,hi],intervals[:,0])=='supports'))
                write(path,record);write(seal,dict(binding=binding,sha256=sha(path)));new+=draws
            records.append(record)
            write(output/'PROGRESS.json',dict(effect_multiple=multiple,worlds_complete=world+1,worlds_per_effect=worlds,new_draws=new))
            if new:
                elapsed=time.process_time()-world_cpu
                write(output/'COST.json',dict(new_worlds=new//draws,initialization_cpu_seconds=world_cpu-cpu_started,
                    world_cpu_seconds=elapsed,forecast_execute_and_replay_cpu_seconds=2*((world_cpu-cpu_started)+elapsed*worlds*3/(new/draws))))
        results.append(dict(effect_multiple=multiple,injected_contrast=truth,worlds=worlds,
            zero_exclusion_rate=float(np.mean([r['excludes_zero'] for r in records])),
            coverage=float(np.mean([r['covers_truth'] for r in records])),
            primary_positive_support_rate=float(np.mean([r['primary_positive_support'] for r in records]))))
    return dict(status='complete',card='MD4.ic',draws=draws,worlds_per_effect=worlds,counts=counts,effects=results,
        sensitivity_pass=results[1]['zero_exclusion_rate']<=.1 and min(results[0]['zero_exclusion_rate'],results[2]['zero_exclusion_rate'])>=.8,
        pass_rule='null zero-exclusion <=.10 and both signed one-bar zero-exclusion >=.80',
        practical_bar_mood_units_per_minute=primary.BAR,failed_draws=[],
        scope='conditional fixed person-slope design; whole-person wild residual signs; original first-block OLS projection and condition/cohort membership preserved',
        primary_rule='positive contrast must also cross .002 with rest upper bound below zero; reported separately from minimum-effect zero exclusion',
        source_domain='artificial linear-estimator responses after original valid 0-1 rating projection; no clipping or claim of new raw mood records',
        interpretation='calibration is conditional on observed slope dispersion and cannot identify a causal interest mechanism or recruitment independence')


def execute(output,inputs,config):
    if set(inputs)!={'ratings','primary_root'}:raise ValueError('exact original ratings and complete MD4 primary required')
    if set(config)-{'draws','worlds','max_new_draws','max_wall_seconds','constructed_fixture'}:raise ValueError('unregistered MD4 sensitivity setting')
    root=authenticate(inputs['primary_root']);plan=json.loads((root/'PLAN.json').read_text('utf8'))
    if Path(plan['inputs']['ratings']).resolve()!=Path(inputs['ratings']).resolve():raise ValueError('primary source differs')
    frame=primary.load({'ratings':inputs['ratings']},config);rows,audit=primary.slopes(frame)
    result=calibrate(rows,config,Path(output),dict(ratings_sha256=sha(inputs['ratings']),primary_complete_sha256=sha(root/'COMPLETE.json'),primary_plan_sha256=sha(root/'PLAN.json')))
    if result.get('status')!='yielded':
        result['dispositions']=audit;write(Path(output)/'RESULT.json',result)
    return result


def verify(output,inputs,config):
    output=Path(output);actual=execute(output/'independent-replay',inputs,config)
    if actual.get('status')=='yielded':return dict(actual,verified=False)
    if actual!=json.loads((output/'RESULT.json').read_text('utf8')):raise ValueError('MD4 full sensitivity replay differs')
    for path in (output/'worlds').glob('*.json'):
        if path.name.endswith('.seal.json'):continue
        if path.read_bytes()!=(output/'independent-replay/worlds'/path.name).read_bytes():raise ValueError('MD4 world record differs')
    return dict(verified=True,all_condition_draws_and_worlds_replayed=True)
