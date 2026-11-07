"""Lossless input cache for the frozen B2 texture calculation.

DESIGN CHECK: LESSONS 3-5. Exact array and source binding precedes any reuse.
Null and signed worlds retain the same family calculation. Corruption refuses;
cache readiness never licenses a scientific claim or a larger allowance.
"""
from pathlib import Path
import gzip, json
import numpy as np
from runners.stage14.common import read,freeze,filehash
from .moral_expectation import load,DIMS,WEIGHTS,expectation
from .moral_exposure import check_parents
from .moral_texture import family


def save_cache(output, source):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    arrays=load(source)
    for name,a in zip(('counts','subset'),arrays):
        path=output/(name+'.npy')
        if path.exists():assert np.array_equal(np.load(path,allow_pickle=False),a)
        else:
            with path.open('xb') as f:np.save(f,a,allow_pickle=False)
    manifest=dict(source_sha256=filehash(source),rows=len(arrays[0]),
                  arrays={name:filehash(output/(name+'.npy')) for name in ('counts','subset')})
    freeze(output/'CACHE.json',manifest)
    return manifest


def get_cache(output, source_hash):
    output=Path(output);meta=read(output/'CACHE.json')
    if meta['source_sha256']!=source_hash:raise ValueError('Wrong cached source')
    arrays=[]
    for name in ('counts','subset'):
        path=output/(name+'.npy')
        if filehash(path)!=meta['arrays'][name]:raise ValueError('Corrupt count cache')
        arrays.append(np.load(path,allow_pickle=False))
    counts,subset=arrays
    if counts.shape!=(meta['rows'],4,2) or subset.shape!=(meta['rows'],4):raise ValueError('Invalid cache shape')
    if not np.isin(subset,[0,1]).all():raise ValueError('Invalid subset cache')
    expectation(counts[:,:,0],counts[:,:,1],3)
    return counts,subset


def fixture_source(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);path=output/'source.gz'
    if not path.exists():
        with gzip.open(path,'wt',encoding='utf8') as f:
            for i in range(1200):
                f.write(json.dumps(dict(eligible=True,dimensions={d:[12,6] for d in DIMS}))+'\n')
    return path


def calculate(inputs,config):
    for item in inputs.values():
        if filehash(item['path'])!=item['sha256']:raise ValueError('Changed input')
    counts,subset=get_cache(Path(inputs['cache']['path']).parent,inputs['source']['sha256'])
    parent=read(inputs['parent']['path']);integrated=read(inputs['integrated']['path'])
    exposure=read(inputs['exposure']['path'])
    n,s=counts[:,:,0],counts[:,:,1]
    minimum=expectation(n,s,n.min(axis=1)[:,None]);three=expectation(n,s,3)
    reproduction=dict(status='complete',common_fingerprints=len(counts),
        original_subset_rates=dict(zip(DIMS,subset.mean(axis=0).tolist())),
        original_subset_difference=float((subset@WEIGHTS).mean()),
        minimum_rates=dict(zip(DIMS,minimum.mean(axis=0).tolist())),
        minimum=dict(difference=float((minimum@WEIGHTS).mean())))
    check_parents(reproduction,parent,integrated)
    assert dict(zip(DIMS,three.mean(axis=0).tolist()))==exposure['three_rates']
    assert abs(float((three@WEIGHTS).mean())-exposure['three']['difference'])<1e-14
    assert sum(exposure['minimum_count_histogram'].values())==len(counts)
    result=family(counts,parent['primary']['difference'],parent['primary']['interval'],config['draws'],config['stopping'])
    if config['draws']==32:assert result==read(inputs['original_probe']['path'])
    return result


def execute(output,inputs,config):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    if config.get('cache_build'):
        source=fixture_source(output) if config.get('constructed') else inputs['source']['path']
        if not config.get('constructed'):assert filehash(source)==inputs['source']['sha256']
        save_cache(output,source)
    else:freeze(output/'SCIENCE.json',calculate(inputs,config))
    return dict(status='complete',constructed=bool(config.get('constructed')))


def verify(output,inputs,config):
    output=Path(output)
    if config.get('cache_build'):
        source=fixture_source(output) if config.get('constructed') else inputs['source']['path']
        original=load(source);cached=get_cache(output,filehash(source))
        assert all(np.array_equal(a,b) for a,b in zip(original,cached))
    else:assert calculate(inputs,config)==read(output/'SCIENCE.json')
    return dict(verified=True,complete_recalculation=True)
