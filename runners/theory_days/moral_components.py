"""B2.m paired decomposition of the original pooled refusal contrast.

DESIGN CHECK: LESSONS 3-5. Identical dimensions yield exact zero and finite
uncertainty. Signed and opposing components retain their direction. Invalid
binary input, lost pairing, source support or parent mismatch refuses admission.
"""
from pathlib import Path
import numpy as np
from runners.stage14.common import read,freeze,filehash
from runners.theory_days.moral_expectation import DIMS,load,classify

ALPHA=.025

def vectors(subset):
    a=np.asarray(subset,dtype=float)
    if a.ndim!=2 or a.shape[1]!=4 or not np.isfinite(a).all() or not np.isin(a,[0,1]).all():
        raise ValueError('Four binary dimension indicators required')
    ordinary=(a[:,2]+a[:,3])/2
    v=a[:,:2]-ordinary[:,None]
    assert np.array_equal(v.mean(axis=1),a[:,:2].mean(axis=1)-ordinary)
    return a,v

def summarize(subset,draws=2000):
    a,v=vectors(subset);n=len(v)
    if n<1000:return dict(status='design cannot test',common_fingerprints=n,required=1000)
    if type(draws) is not int or draws<32:raise ValueError('Invalid draw count')
    values,counts=np.unique(v,axis=0,return_counts=True)
    rng=np.random.default_rng(20261106);boot=np.empty((draws,2))
    for start in range(0,draws,16):
        w=rng.multinomial(n,counts/n,size=min(16,draws-start))
        boot[start:start+len(w)]=w@values/n
    point=counts@values/n;components={}
    for j,name in enumerate(DIMS[:2]):
        if np.all(v[:,j]==v[0,j]):
            radius=2*np.sqrt(np.log(2/ALPHA)/(2*n))
            ci=[max(-1,float(point[j])-radius),min(1,float(point[j])+radius)]
            method='bounded_mean_Hoeffding'
        else:
            ci=np.quantile(boot[:,j],[ALPHA/2,1-ALPHA/2]).tolist()
            method='paired_fingerprint_percentile'
        components[name]=dict(difference=float(point[j]),interval=ci,interval_method=method,verdict=classify(ci))
    pooled=float((a[:,:2].mean(axis=1)-a[:,2:].mean(axis=1)).mean())
    assert abs(float(point.mean())-pooled)<1e-14
    return dict(status='complete',common_fingerprints=n,draws=draws,components=components,
        original_subset_rates=dict(zip(DIMS,a.mean(axis=0).tolist())),original_subset_difference=pooled,
        compression_classes=len(values),marginal_interval_level=1-ALPHA,
        nominal_family_interval_level=.95,descriptive=True,causal_claim=False)

def check_parent(result,parent):
    if result['status']!='complete':return
    assert result['common_fingerprints']==parent['common_fingerprints'],'Parent cohort mismatch'
    assert result['original_subset_rates']==parent['equal_exposure_rates'],'Parent rate mismatch'
    assert abs(result['original_subset_difference']-parent['primary']['difference'])<1e-14,'Parent point mismatch'

def fixtures():
    # All values known directly from the binary indicators, not inferred from a fitted model.
    specs={'zero':[0,0,0,0],'positive':[1,1,0,0],'negative':[0,0,1,1],
           'opposing':[1,0,1,0]}
    out={name:summarize(np.tile(row,(1200,1)),64) for name,row in specs.items()}
    assert all(x['difference']==0 and x['interval'][0]<0<x['interval'][1] for x in out['zero']['components'].values())
    assert all(x['verdict']=='supports' for x in out['positive']['components'].values())
    assert all(x['verdict']=='against' for x in out['negative']['components'].values())
    assert out['opposing']['components']['Species']['difference']==.5
    assert out['opposing']['components']['Intervention']['difference']==-.5
    return out

def calculate(inputs,config):
    if config.get('constructed'):return fixtures()
    for item in inputs.values():assert filehash(Path(item['path']))==item['sha256']
    counts,subset=load(inputs['source']['path'])
    assert len(counts)==len(subset)
    result=summarize(subset,config.get('draws',2000));check_parent(result,read(inputs['parent']['path']))
    return result

def execute(output,inputs,config):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    freeze(output/'SCIENCE.json',calculate(inputs,config))
    return dict(status='complete',constructed=bool(config.get('constructed')))

def verify(output,inputs,config):
    assert calculate(inputs,config)==read(Path(output)/'SCIENCE.json')
    return dict(verified=True,complete_recalculation=True)
