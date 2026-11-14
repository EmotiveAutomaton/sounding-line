"""Counted CH8/CH12 table cards, with independent formula replay.

DESIGN CHECK: complete SG1 table only; no raw-source requalification. The split
and scope are frozen before fitting. Whole-player bootstrap draws checkpoint
individually. Forecast/setup cost and largest-player memory remain measured gates.
"""
from pathlib import Path
from collections.abc import Mapping
import json
import math
import numpy as np

from . import week5_sg1_source_v1 as sg1
from . import week5_ch_pipeline_checkpoint as ck
from . import week5_ch_forecast_two_day_v1 as forecast
from . import week5_ch8_math_v1 as ch8
from . import week5_ch12_math_v1 as ch12
from .week5_ch_source import digest,write_json

SEED=20261112


def identity(inputs,config):
    if set(config)-{'card','draws','floor','constructed_fixture','max_new_draws'}:
        raise ValueError('Unknown two-day chess table configuration')
    if config.get('card') not in ('CH8','CH12'):
        raise ValueError('Only current reviewed table formulas are implemented')
    if config.get('draws',2000)!=2000 and not config.get('constructed_fixture'):
        raise ValueError('Primaries require 2000 whole-player resamples')
    if 'floor' in config and (config['card']!='CH8' or not config.get('constructed_fixture')):
        raise ValueError('Only constructed CH8 fixture may reduce its case floor')
    return ck.binding(inputs,config,dict(handler=digest(__file__),source=digest(sg1.__file__),
        forecast=digest(forecast.__file__),ch8=digest(ch8.__file__),ch12=digest(ch12.__file__),
        reliability=digest(ch12.tr1.__file__)))


class EnrichedStore(Mapping):
    def __init__(self,store,model,root,reference=False):
        self.store=store;self.model=model;self.root=root;self.reference=reference
        self.names=[p for p in store if not forecast.calibration(p)]
    def __iter__(self):return iter(self.names)
    def __len__(self):return len(self.names)
    def __getitem__(self,key):
        ck.require(self.root)
        if forecast.calibration(key):raise KeyError(key)
        return forecast.enrich(self.store[key],self.model,self.reference)


def equivalent(left,right,path='result'):
    if isinstance(left,dict):
        if not isinstance(right,dict) or set(left)!=set(right):raise ValueError('Independent keys differ at '+path)
        for key in left:equivalent(left[key],right[key],path+'.'+key)
    elif isinstance(left,list):
        if not isinstance(right,list) or len(left)!=len(right):raise ValueError('Independent dimensions differ at '+path)
        for index,(a,b) in enumerate(zip(left,right)):equivalent(a,b,path+'.'+str(index))
    elif isinstance(left,(float,int)) and not isinstance(left,bool):
        if not isinstance(right,(float,int)) or not math.isclose(left,right,rel_tol=1e-6,abs_tol=1e-7):
            raise ValueError('Independent formula differs at '+path)
    elif left!=right:raise ValueError('Independent discrete outcome differs at '+path)


def run(output,root,inputs,config,reference=False):
    output=Path(output);root=Path(root);output.mkdir(parents=True,exist_ok=True)
    bound=identity(inputs,config);path=sg1.authenticate_consumer(inputs,config,root)
    checkpoint=output/'TABLE_CHECKPOINT.json'
    values=[]
    if checkpoint.exists():
        if reference:raise ValueError('Independent replay must start fresh')
        ck.copied(checkpoint,root,lambda:ck.require(root))
        prior=json.loads(checkpoint.read_text(encoding='utf8'))
        if prior['binding']!=bound:raise ValueError('Changed table-card checkpoint')
        values=prior['draws']
    new=0
    def save():write_json(checkpoint,dict(binding=bound,draws=values),mutable=True)
    try:
        with sg1.HistoryStore(path,bool(config.get('constructed_fixture'))) as store:
            model_path=output/'FORECAST.json'
            if model_path.exists() and not reference:
                ck.copied(model_path,root,lambda:ck.require(root))
                model=json.loads(model_path.read_text(encoding='utf8'))
            else:
                model=forecast.prepare(store,lambda:ck.require(root),reference)
                write_json(model_path,model)
            table=EnrichedStore(store,model,root,reference)
            if config['card']=='CH8':prepared=ch8.estimate(table,config.get('floor',3000),reference)
            else:prepared=ch12.prepare(table,reference)
            n=len(prepared['names']);draws=config.get('draws',2000)
            rng=np.random.default_rng(SEED)
            for ordinal in range(draws):
                weights=np.bincount(rng.integers(0,n,n),minlength=n) if n else np.zeros(0)
                if ordinal<len(values):continue
                ck.require(root)
                quantum=config.get('max_new_draws') if not reference else None
                if quantum is not None and new>=quantum:
                    save();return dict(status='yielded',phase='whole_player_draws',draws=len(values),total=draws)
                value=ch8.draw(prepared,weights,reference) if config['card']=='CH8' else ch12.evaluate(prepared,weights,reference)
                values.append(value);new+=1
                if new%25==0:save()
                write_json(output/'PROGRESS.json',dict(phase='bootstrap',completed=len(values),total=draws,
                    reference=reference,setup_complete=True),mutable=True)
                if len(values)>=math.ceil(draws/20) and not (output/'PILOT.json').exists():
                    write_json(output/'PILOT.json',dict(phase='bootstrap',completed=len(values),total=draws,
                        source_setup_already_charged=True,not_total_cpu_fraction=True,
                        basis='First 5% of whole-player bootstrap draws; does not represent source/forecast or replay cost'))
            result=ch8.result(prepared,values) if config['card']=='CH8' else ch12.result(prepared,values,reference)
            result.update(constructed_fixture=bool(config.get('constructed_fixture')),
                          forecast_split=dict(prefix=forecast.SPLIT_PREFIX,calibration_digits='012'),
                          forecast_control_status={tc:value['status'] for tc,value in model['controls'].items()},
                          independent_formula_replay_required=True)
            write_json(output/'SCIENCE.json',result);save()
            return dict(status='complete',card=config['card'],scientific_result_complete=True)
    except ck.YieldRequested:
        save();return dict(status='yielded',reason='Owner yield during source/table setup or draw boundary',
                           verification_prefix_credited=False,completed_draws=len(values))


def _execute(output,inputs,config):
    output=Path(output);bound=identity(inputs,config)
    if ck.sealed(output,bound,lambda:ck.require(output)):return dict(status='complete',sealed_output_reused=True)
    result=run(output,output,inputs,config)
    if result['status']=='complete':ck.seal(output,bound,['SCIENCE.json','FORECAST.json'],lambda:ck.require(output))
    return result


def _verify(output,inputs,config):
    output=Path(output)
    if not ck.sealed(output,identity(inputs,config),lambda:ck.require(output)):
        raise ValueError('Complete table output required before independent replay')
    ordinal=1
    while (output/f'independent-{ordinal:04}').exists():ordinal+=1
    target=output/f'independent-{ordinal:04}'
    answer=run(target,output,inputs,config,True)
    if answer['status']!='complete':return answer
    equivalent(json.loads((output/'SCIENCE.json').read_text()),json.loads((target/'SCIENCE.json').read_text()))
    original=json.loads((output/'FORECAST.json').read_text());other=json.loads((target/'FORECAST.json').read_text())
    if original['counts']!=other['counts'] or set(original['controls'])!=set(other['controls']):
        raise ValueError('Independent forecast population differs')
    for tc,model in original['controls'].items():
        replay=other['controls'][tc]
        if model['status']!=replay['status']:raise ValueError('Independent forecast support differs')
        if model['status']=='complete':
            equivalent(model['calibration'],replay['calibration'],'forecast.calibration.'+tc)
    return dict(verified=True,complete_recalculation=True,raw_source_requalification=False,
                independent_formulas=True,all_whole_player_draws_recomputed=True)


def execute(output,inputs,config):return ck.guarded(_execute,output,inputs,config)
def verify(output,inputs,config):return ck.guarded(_verify,output,inputs,config)
