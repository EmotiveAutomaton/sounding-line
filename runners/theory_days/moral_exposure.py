"""B2.s fixed-exposure sensitivity on the original common cohort.

DESIGN CHECK: LESSONS 3-5. Identical histories and k=3 arm identity must give
exact paired zeros with finite uncertainty. Signed alternatives retain sign.
Invalid counts, missing support and failed parent reproduction refuse admission.
"""
from pathlib import Path
import numpy as np
from runners.stage14.common import read,freeze,filehash
from runners.theory_days.moral_expectation import DIMS,WEIGHTS,expectation,load,classify

def summaries(v,draws):
    n=len(v);values,counts=np.unique(v,axis=0,return_counts=True)
    rng=np.random.default_rng(20261106);boot=np.empty((draws,3))
    for start in range(0,draws,16):
        w=rng.multinomial(n,counts/n,size=min(16,draws-start))
        boot[start:start+len(w)]=w@values/n
    point=counts@values/n;result=[]
    for j,(alpha,lo,hi) in enumerate(((.025,-1,1),(.025,-1,1),(.05,-2,2))):
        if np.all(v[:,j]==v[0,j]):
            radius=(hi-lo)*np.sqrt(np.log(2/alpha)/(2*n))
            ci=[max(lo,float(point[j])-radius),min(hi,float(point[j])+radius)]
            method='bounded_mean_Hoeffding'
        else:
            ci=np.quantile(boot[:,j],[alpha/2,1-alpha/2]).tolist();method='paired_fingerprint_percentile'
        result.append(dict(difference=float(point[j]),interval=ci,interval_method=method,interval_level=1-alpha))
    return result,len(values)

def summarize(counts,subset,draws=2000):
    a=np.asarray(counts);subset=np.asarray(subset,dtype=float)
    if a.ndim!=3 or a.shape[1:]!=(4,2) or subset.shape!=(len(a),4):raise ValueError('Invalid count/indicator shape')
    if not np.isin(subset,[0,1]).all():raise ValueError('Nonbinary subset')
    n=a[:,:,0];s=a[:,:,1];k=n.min(axis=1)[:,None]
    if np.any(k<3):raise ValueError('Invalid common-cohort exposure')
    minimum=expectation(n,s,k);three=expectation(n,s,3)
    if len(a)<1000:return dict(status='design cannot test',common_fingerprints=len(a),required=1000)
    if type(draws) is not int or draws<32:raise ValueError('Invalid draw count')
    m=minimum@WEIGHTS;t=three@WEIGHTS
    out,classes=summaries(np.column_stack([m,t,t-m]),draws)
    for row in out[:2]:row['verdict']=classify(row['interval'])
    ks,frequencies=np.unique(k[:,0],return_counts=True)
    return dict(status='complete',common_fingerprints=len(a),draws=draws,
        minimum=out[0],three=out[1],paired_change=out[2],
        minimum_rates=dict(zip(DIMS,minimum.mean(axis=0).tolist())),
        three_rates=dict(zip(DIMS,three.mean(axis=0).tolist())),
        minimum_count_histogram={str(int(key)):int(value) for key,value in zip(ks,frequencies)},
        share_minimum_three=float(np.mean(k==3)),compression_classes=classes,
        original_subset_rates=dict(zip(DIMS,subset.mean(axis=0).tolist())),
        original_subset_difference=float((subset@WEIGHTS).mean()),
        descriptive=True,causal_claim=False)

def check_parents(result,parent,integrated):
    if result['status']!='complete':return
    assert result['common_fingerprints']==parent['common_fingerprints']==integrated['common_fingerprints']
    assert result['original_subset_rates']==parent['equal_exposure_rates']
    assert abs(result['original_subset_difference']-parent['primary']['difference'])<1e-14
    assert result['minimum_rates']==integrated['expected_rates']
    assert abs(result['minimum']['difference']-integrated['primary']['difference'])<1e-14

def fixtures():
    out={}
    for sign in (-1,0,1):
        a=np.tile([[8,4]]*4,(1200,1,1))
        if sign>0:a[:,:2,1]=0
        if sign<0:a[:,2:,1]=0
        out[str(sign)]=summarize(a,np.zeros((1200,4)),64)
    for name in ('minimum','three'):
        assert out['1'][name]['verdict']=='supports' and out['-1'][name]['verdict']=='against'
        assert out['0'][name]['difference']==0 and out['0'][name]['interval'][0]<0<out['0'][name]['interval'][1]
    return out

def calculate(inputs,config):
    if config.get('constructed'):return fixtures()
    for item in inputs.values():assert filehash(Path(item['path']))==item['sha256']
    result=summarize(*load(inputs['source']['path']),draws=config.get('draws',2000))
    check_parents(result,read(inputs['parent']['path']),read(inputs['integrated']['path']))
    return result

def execute(output,inputs,config):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    freeze(output/'SCIENCE.json',calculate(inputs,config));return dict(status='complete',constructed=bool(config.get('constructed')))

def verify(output,inputs,config):
    assert calculate(inputs,config)==read(Path(output)/'SCIENCE.json')
    return dict(verified=True,complete_recalculation=True)
