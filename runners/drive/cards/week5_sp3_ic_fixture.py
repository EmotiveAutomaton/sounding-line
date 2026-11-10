"""Constructed whole-handler and direct expanded-row SP3 sensitivity proof.

DESIGN CHECK: every exact linear operator draw must equal an independently
expanded least-squares fit. Raw planted response slopes must map to the same
building statistic. The full high-noise grid must fail sensitivity.
"""
from pathlib import Path
import argparse,json
import numpy as np
import pandas as pd
from . import week5_sp3_ic as instrument
from .week5_sp_fixture_v2 import world

parent=instrument.parent


def arithmetic(data):
    table,_=parent.building_summaries(data,{})
    ordered,at,x,y=instrument.design(table)
    matrix,failed=instrument.operators(ordered,2000)
    if failed:raise ValueError('Supported known-answer design lost bootstrap support')
    mask=np.zeros(len(ordered),bool);mask[at]=True;center=np.zeros(len(ordered));center[at]=x[:,1]
    rng=np.random.default_rng(instrument.SEED);reference=[]
    for _ in range(2000):
        take=rng.integers(0,len(ordered),len(ordered));use=take[mask[take]]
        reference.append(np.linalg.lstsq(np.column_stack([np.ones(len(use)),center[use]]),y[use],rcond=None)[0][1])
    if not np.allclose(matrix@y,reference,rtol=0,atol=1e-8):raise ValueError('All-draw expanded OLS differs')
    base_beta=np.linalg.lstsq(x,y[at],rcond=None)[0]
    for dose in (-.01,0,.01):
        planted=data.copy()
        for i in at:
            row=ordered.iloc[i];select=planted.building_id.eq(row.building)
            temperatures=planted.loc[select,'top'].to_numpy()
            delta=(dose-base_beta[1])*center[i]
            planted.loc[select,'thermal_sensation']+=delta*(temperatures-temperatures.mean())
        rebuilt,_=parent.building_summaries(planted,{})
        value=parent.estimate(rebuilt,'SP3')
        if not np.isclose(value,dose,rtol=0,atol=1e-8):raise ValueError('Raw-response slope injection differs')
    sparse=ordered.copy();sparse['cooling']=parent.AC
    for i in (at[0],at[-1]):sparse.loc[i,'cooling']=parent.NV
    _,failures=instrument.operators(sparse,2000)
    if not failures:raise ValueError('Reachable unsupported bootstrap missing')
    return dict(verified=True,expanded_row_all_2000_draws=True,raw_response_signed_null_parity=True,
                failed_draw_indices_retained=True,unsupported_fixture_draw_count=len(failures),
                source_sha256=parent.sha(instrument.__file__))


def check_inputs(inputs,config):
    manifest=json.loads(Path(inputs['fixture_manifest']).read_text('utf8'))
    if manifest.get('constructed_only') is not True or manifest['case']!=config['case']:raise ValueError('Constructed source scope required')
    if manifest['sha256']!=parent.sha(inputs['data']):raise ValueError('Fixture source changed')
    if config['case'] not in ('exact','high-noise'):raise ValueError('Unknown constructed case')


def execute(output,inputs,config):
    check_inputs(inputs,config);output=Path(output)
    proof=output/'ARITHMETIC.json'
    value=arithmetic(pd.read_parquet(inputs['data']))
    if proof.exists() and value!=json.loads(proof.read_text('utf8')):raise ValueError('Native arithmetic replay differs')
    parent.write(proof,value)
    return instrument.execute(output,{'data':inputs['data']},dict(phase='SP3.ic',worlds=100,draws=2000,max_wall_seconds=config.get('max_wall_seconds',900)))


def verify(output,inputs,config):
    check_inputs(inputs,config);output=Path(output)
    value=instrument.verify(output,{'data':inputs['data']},dict(phase='SP3.ic',worlds=100,draws=2000,max_wall_seconds=config.get('max_wall_seconds',900)))
    if value.get('status')=='yielded':return value
    result=json.loads((output/'RESULT.json').read_text('utf8'))
    if result['sensitivity_pass']!=(config['case']=='exact'):raise ValueError('Known sensitivity pass/failure differs')
    if config['case']=='exact':
        for dose in result['effects']:
            if not np.allclose(dose['estimate_quantiles'],dose['injected_slope'],rtol=0,atol=1e-8):raise ValueError('Known world doses differ')
    return {**value,'constructed_expected_sensitivity_verified':True,'full_100_worlds_all_2000_draws':True}


def prepare(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=False)
    original=world('SP3',0)
    rng=np.random.default_rng(1009)
    for case in ('exact','high-noise'):
        data=original.copy()
        if case=='high-noise':
            for _,group in data.groupby('building_id',sort=True):
                if group.cooling_type.iloc[0]!=parent.NV:continue
                delta=float(rng.normal(0,1000));temperature=group.top.to_numpy()
                data.loc[group.index,'thermal_sensation']+=delta*(temperature-temperature.mean())
        path=root/(case+'.parquet');data.to_parquet(path,index=False)
        parent.write(root/(case+'.json'),dict(constructed_only=True,case=case,sha256=parent.sha(path)))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('output');args=parser.parse_args();prepare(args.output)
