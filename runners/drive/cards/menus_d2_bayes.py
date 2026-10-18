"""D2's single hierarchical Bayesian spread extension, separate from primary.

DESIGN CHECK: LESSONS 3-5 and relevant TTI/reader sections read 2026-10-18.
The registered population spread is approximated by Laplace integration over
normal writer coefficients and fixed quadrature over a spike-and-slab spread.
Null/planted and numerical gates are fixed in menus_d2_bayes_stats. Failures
return invalid/blind, never scientific nulls. V4's blind label and D2's positive
uniform control remain attached; this does not establish individual taste.
"""
from __future__ import annotations
from pathlib import Path
import hashlib
import math
import time
import numpy as np

from . import menus_d2 as primary
from . import menus_d2_bayes_stats as stats
from . import states_v2 as states
from .menus_io import read, write, sha256, input_hashes, assert_equal, canonical

CONFIG=dict(seed=20261018,population_sd=2.,spike_prior=.5,slab_sd=1.,slab_upper=6.,
    quadrature_coarse=20,quadrature_fine=40,tail_start=4.8,maximum_tail_mass=.005,
    mean_absolute_tolerance=.02,mean_relative_tolerance=.05,spike_tolerance=.02,
    gradient_tolerance=1e-5,maxiter=4000,null_worlds=20,planted_worlds=5,planted_tau=1.,minimum_writers=4)


def completed(marker,path):
    marker=Path(marker);receipt=read(marker)
    if receipt.get('status')!='COMPLETE':raise ValueError('incomplete dependency')
    relative=Path(path).resolve().relative_to(marker.parent.resolve()).as_posix()
    if receipt['outputs'].get(relative)!=sha256(path):raise ValueError('dependency artifact changed')


def authenticate(inputs):
    primary.authenticated(inputs)
    completed(inputs['d2_complete'],inputs['d2_summary'])
    completed(inputs['v4_complete'],inputs['v4_summary'])
    base=read(inputs['d2_summary'])
    if base['state'] not in ('positive','marginal'):raise ValueError('D2 extension gate closed')
    for key in ('sessions','records','vectors','p8','content_complete','p8_complete'):
        if base['input_hashes'][key]!=sha256(inputs[key]):raise ValueError('D2 source population changed')
    return dict(primary_state=base['state'],primary=base['primary'],uniform_control=base['uniform_control'],
                v4_labels=read(inputs['v4_summary'])['labels'])


def designs(inputs,config):
    cases,_,excluded=primary.load(inputs);cases=[cases[k] for k in sorted(cases)]
    matrices=[c['x']-c['x'].mean(axis=0) for c in cases]
    scale=np.sqrt(np.mean(np.concatenate(matrices)**2,axis=0))
    active=np.flatnonzero(scale>1e-10).tolist()
    registered=[0,1,3,4,5]+list(range(8,32))
    random=[j for j,k in enumerate(active) if k in registered]
    if not random:raise ValueError('no varying registered attributes')
    matrices=[x[:,active]/scale[active] for x in matrices]
    writers=[c['writer'] for c in cases];truths=[c['truth'] for c in cases]
    if len(set(writers))<config['minimum_writers']:raise ValueError('insufficient hierarchical writers')
    data=stats.pack(matrices,truths,writers,random)
    metadata=dict(keys=[c['key'] for c in cases],writers=writers,truths=truths,
        active_columns=active,random_columns=random,scale=scale.tolist(),exclusions=excluded,
        coefficients='D2 registered length, normalized position, context/lexical overlap, novelty and decoding-setting interactions have isotropic writer deviations; first-position and raw-score nuisance covariates have population coefficients only.',
        population='All uniquely identified selected menus in the frozen prepared roster; conditional on uptake. This is a distribution fit, not held-out predictive gain.',
        preprocessing='Outcome-free within-menu centering and complete-design RMS scaling, no PCA, no new text features.')
    return data,metadata


def truth_hash(data):
    return hashlib.sha256(np.asarray(data['truths'],dtype='<i8').tobytes()).hexdigest()


def world(data,population,kind,replicate,config):
    if kind=='observed':return data
    rng=np.random.default_rng(config['seed']+replicate+(100000 if kind=='plant' else 0))
    tau=config['planted_tau'] if kind=='plant' else 0.
    deviations=rng.normal(size=(len(data['names']),data['z'].shape[1]))
    parameters=np.r_[population['mode'],deviations.ravel()] if tau else np.asarray(population['mode'])
    _,prob=stats.probability(parameters,data,tau)
    truths=np.array([rng.choice(int(n),p=prob[start:start+n]) for start,n in zip(data['starts'],data['sizes'])])
    return data|dict(truths=truths,selected=data['starts']+truths)


def node_path(output,kind,replicate,tau):
    name=hashlib.sha256(float(tau).hex().encode()).hexdigest()[:20]+'.json'
    return Path(output)/'fits'/f'{kind}-{replicate:02d}'/name


def save_node(output,kind,replicate,data,tau,config,binding):
    path=node_path(output,kind,replicate,tau)
    expected=dict(binding=binding,kind=kind,replicate=replicate,truth_hash=truth_hash(data))
    if path.exists():
        if sha256(path)!=read(path.with_suffix('.seal.json'))['sha256']:raise ValueError('changed fit checkpoint')
        saved=read(path);assert_equal({k:saved[k] for k in expected},expected)
    else:
        saved=expected|dict(result=stats.laplace(data,tau,config))
        write(path,saved);write(path.with_suffix('.seal.json'),dict(sha256=sha256(path)))
    return saved['result'],path.relative_to(output).as_posix(),sha256(path)


def grids(output,kind,replicate,data,config,binding,progress):
    results=[];hashes={}
    for nodes in (config['quadrature_coarse'],config['quadrature_fine']):
        grid=[]
        for tau in np.r_[0,stats.quadrature(config,nodes)[0]]:
            if (Path(output)/'YIELD_REQUEST.json').exists():return None,hashes
            result,name,digest=save_node(output,kind,replicate,data,float(tau),config,binding)
            grid.append(result)
            if name not in hashes:progress()
            hashes[name]=digest
        results.append(grid)
    return stats.grid_summary(*results,config),hashes


def report_from_worlds(worlds,context,config,binding,hashes,design_hash,population_hash):
    null=[worlds[f'null-{i:02d}'] for i in range(config['null_worlds'])]
    plant=[worlds[f'plant-{i:02d}'] for i in range(config['planted_worlds'])]
    gate=stats.calibration(null,plant,config);observed=worlds.get('observed-00')
    valid=gate['valid'] and observed is not None and observed['valid']
    primary_result=observed['primary'] if observed else dict(effect=None,ci95=[None,None],standard_error=None,p_approx=None)
    state=states.contrast_state(primary_result['effect'],*primary_result['ci95'],valid=valid)
    return dict(card='D2.extension',descriptive=True,scientific_admission=False,state=state,
        instrument_state='valid' if valid else 'blind',primary=primary_result,calibration=gate,
        observed_computed=observed is not None,worlds=worlds,context=context,config=config,
        input_hashes=binding['inputs'],fit_hashes=hashes,design_hash=design_hash,population_hash=population_hash,
        inference='Approximate Bayesian multinomial logit: certified Laplace integration and two fixed Gauss-Legendre grids; 0.5 spike at zero and truncated half-normal slab. CI is a posterior credible interval, not a writer bootstrap confidence interval.',
        restriction='Writer covariance is tau squared times identity on RMS-standardized registered varying attributes. Common coefficients and raw-score nuisances have N(0,2 squared) priors.',
        null_warning='Original D2 uniform-choice control was positive. V4 labels remain attached. No taste specificity, personal-panel admission or frequentist size guarantee follows.')


def execute(output,inputs,config):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);started=time.perf_counter()
    context=authenticate(inputs);binding=dict(inputs=input_hashes(inputs),config=config)
    if (output/'BINDING.json').exists():assert_equal(read(output/'BINDING.json'),binding)
    else:write(output/'BINDING.json',binding)
    if (output/'SUMMARY.json').exists():verify(output,inputs,config);return read(output/'SUMMARY.json')
    data,metadata=designs(inputs,config)
    if (output/'DESIGN.json').exists():assert_equal(read(output/'DESIGN.json'),metadata)
    else:write(output/'DESIGN.json',metadata)
    array_path=output/'DESIGN.npz'
    if not array_path.exists():
        np.savez_compressed(array_path,x=data['x'],z=data['z'],sizes=data['sizes'],starts=data['starts'],
                            truths=data['truths'],writer=data['writer'])
        write(output/'DESIGN_ARRAYS.json',dict(sha256=sha256(array_path)))
    if sha256(array_path)!=read(output/'DESIGN_ARRAYS.json')['sha256']:raise ValueError('changed saved design')
    if (output/'YIELD_REQUEST.json').exists():return dict(status='yielded',completed=0)
    population,popname,pophash=save_node(output,'population',0,data,0.,config,binding)
    hashes={popname:pophash};worlds={};completed_nodes=0
    total=(1+config['null_worlds']+config['planted_worlds'])*(1+config['quadrature_coarse']+config['quadrature_fine'])
    def tick():
        nonlocal completed_nodes
        completed_nodes+=1
        if completed_nodes>=math.ceil(.1*total) and not (output/'FIRST_TENTH.json').exists():
            elapsed=time.perf_counter()-started
            write(output/'FIRST_TENTH.json',dict(completed_fits=completed_nodes,total_fits=total,
                elapsed_seconds=elapsed,projected_seconds=elapsed*total/completed_nodes))
    schedule=[('null',i) for i in range(config['null_worlds'])]+[('plant',i) for i in range(config['planted_worlds'])]+[('observed',0)]
    for kind,replicate in schedule:
        if kind=='observed':
            gate=stats.calibration([worlds[f'null-{i:02d}'] for i in range(config['null_worlds'])],
                [worlds[f'plant-{i:02d}'] for i in range(config['planted_worlds'])],config)
            if not gate['valid']:break
        result,saved=grids(output,kind,replicate,world(data,population,kind,replicate,config),config,binding,tick)
        hashes.update(saved)
        if result is None:return dict(status='yielded',completed_fits=completed_nodes)
        worlds[f'{kind}-{replicate:02d}']=result
    if (output/'YIELD_REQUEST.json').exists():return dict(status='yielded',completed_fits=completed_nodes)
    report=report_from_worlds(worlds,context,config,binding,hashes,sha256(output/'DESIGN.json'),pophash)
    write(output/'SUMMARY.json',report);return report


def verify(output,inputs,config):
    output=Path(output);saved=read(output/'SUMMARY.json');context=authenticate(inputs)
    binding=dict(inputs=input_hashes(inputs),config=config)
    assert_equal(saved['input_hashes'],binding['inputs']);assert_equal(saved['config'],config)
    data,metadata=designs(inputs,config);assert_equal(read(output/'DESIGN.json'),metadata)
    if sha256(output/'DESIGN.json')!=saved['design_hash']:raise ValueError('saved design changed')
    if sha256(output/'DESIGN.npz')!=read(output/'DESIGN_ARRAYS.json')['sha256']:raise ValueError('design arrays changed')
    with np.load(output/'DESIGN.npz',allow_pickle=False) as archive:
        for key in archive.files:
            if not np.array_equal(archive[key],data[key]):raise ValueError('source design replay differs')
    def load_node(kind,replicate,world_data,tau):
        path=node_path(output,kind,replicate,tau);name=path.relative_to(output).as_posix()
        if saved['fit_hashes'].get(name)!=sha256(path):raise ValueError('saved fit changed')
        record=read(path)
        assert_equal({k:record[k] for k in ('binding','kind','replicate','truth_hash')},
            dict(binding=binding,kind=kind,replicate=replicate,truth_hash=truth_hash(world_data)))
        return record['result']
    population=load_node('population',0,data,0.);worlds={}
    for name in saved['worlds']:
        kind,replicate=name.split('-');replicate=int(replicate)
        wd=world(data,population,kind,replicate,config);records=[]
        for nodes in (config['quadrature_coarse'],config['quadrature_fine']):
            records.append([load_node(kind,replicate,wd,float(tau)) for tau in np.r_[0,stats.quadrature(config,nodes)[0]]])
        worlds[name]=stats.grid_summary(*records,config)
    actual=report_from_worlds(worlds,context,config,binding,saved['fit_hashes'],saved['design_hash'],saved['population_hash'])
    assert_equal(actual,saved)
    return dict(verified=True,primary_recomputed=actual['primary'],state=actual['state'],
                source_design_replayed=True,calibration_recomputed=actual['calibration'])
