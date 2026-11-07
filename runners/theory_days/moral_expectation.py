"""B2.p exact expectation over all matched subsets.

DESIGN CHECK: LESSONS 3-5. Literal enumeration validates the probability;
identical dimensions yield exactly zero and retain finite uncertainty. Signed
fixtures exercise both directions. Invalid counts and support refuse, not null.
"""
from pathlib import Path
import gzip,json
import numpy as np
from scipy.special import gammaln
from runners.stage14.common import read,freeze,filehash

DIMS=('Species','Intervention','Gender','Fitness')
WEIGHTS=np.array([.5,.5,-.5,-.5])

def expectation(n,s,k):
    n,s,k=np.broadcast_arrays(np.asarray(n),np.asarray(s),np.asarray(k))
    for a in (n,s,k):
        if not np.isfinite(a).all() or not np.equal(a,np.floor(a)).all():raise ValueError('Noninteger counts')
    if np.any(n<1) or np.any(s<0) or np.any(s>n) or np.any(k<1) or np.any(k>n):raise ValueError('Invalid counts')
    def logchoose(a,b):return gammaln(a+1)-gammaln(b+1)-gammaln(a-b+1)
    denominator=logchoose(n,k);total=np.zeros(n.shape,dtype=float)
    for a in (s,n-s):
        ok=a>=k
        total[ok]+=np.exp(logchoose(a[ok],k[ok])-denominator[ok])
    total=np.where((s==0)|(s==n),1.,total)
    if not np.isfinite(total).all() or np.any(total<0) or np.any(total>1+1e-10):raise ValueError('Invalid probability')
    return np.minimum(1.,total)

def intervals(vectors,draws,bounds):
    """Exact value compression of a fingerprint bootstrap, no approximate bins."""
    vectors=np.asarray(vectors,dtype=float);n=len(vectors)
    if vectors.ndim!=2 or n<2 or not np.isfinite(vectors).all():raise ValueError('Invalid bootstrap input')
    values,counts=np.unique(vectors,axis=0,return_counts=True)
    rng=np.random.default_rng(20261106);boot=np.empty((draws,vectors.shape[1]))
    for start in range(0,draws,16):
        weights=rng.multinomial(n,counts/n,size=min(16,draws-start))
        boot[start:start+len(weights)]=weights@values/n
    point=counts@values/n;results=[]
    for j,(lo,hi) in enumerate(bounds):
        if np.all(vectors[:,j]==vectors[0,j]):
            radius=(hi-lo)*np.sqrt(np.log(40)/(2*n))
            ci=[max(lo,float(point[j])-radius),min(hi,float(point[j])+radius)];method='bounded_mean_Hoeffding'
        else:ci=np.quantile(boot[:,j],[.025,.975]).tolist();method='fingerprint_cluster_percentile'
        results.append(dict(difference=float(point[j]),interval=ci,interval_method=method))
    return results,len(values)

def classify(interval):
    lo,hi=interval
    return 'supports' if lo>.05 else 'against' if hi<0 or (lo>=-.05 and hi<=.05) else 'inconclusive'

def summarize(counts,subset,draws=2000):
    counts=np.asarray(counts,dtype=np.int64);subset=np.asarray(subset,dtype=float)
    n=len(counts)
    if n<1000:return dict(status='design cannot test',common_fingerprints=n,required=1000)
    totals=counts[:,:,0];positive=counts[:,:,1];k=totals.min(axis=1)[:,None]
    exact=expectation(totals,positive,k)
    exact_delta=exact@WEIGHTS;subset_delta=subset@WEIGHTS
    statistics,unique=intervals(np.column_stack([exact_delta,exact_delta-subset_delta]),draws,[(-1,1),(-2,2)])
    statistics[0]['verdict']=classify(statistics[0]['interval'])
    return dict(status='complete',common_fingerprints=n,draws=draws,primary=statistics[0],
        paired_subset_sensitivity=statistics[1],expected_rates=dict(zip(DIMS,exact.mean(axis=0).tolist())),
        original_subset_rates=dict(zip(DIMS,subset.mean(axis=0).tolist())),original_subset_difference=float(subset_delta.mean()),
        exact_bootstrap_vector_classes=unique,causal_claim=False)

def load(path):
    counts=[];subset=[];rng=np.random.default_rng(20261106)
    with gzip.open(path,'rt',encoding='utf8') as f:
        for line in f:
            row=json.loads(line)
            if not row['eligible']:continue
            v=row['dimensions'];numbers=np.array([v[d][:2] for d in DIMS],dtype=np.int64);k=int(numbers[:,0].min())
            signs=[]
            for count,positive in numbers:
                chosen=rng.hypergeometric(positive,count-positive,k);signs.append(int(chosen in (0,k)))
            counts.append(numbers);subset.append(signs)
    return np.asarray(counts),np.asarray(subset)

def fixture(sign):
    a=np.tile(np.array([[8,4]]*4),(1200,1,1))
    if sign>0:a[:,:2,1]=0
    if sign<0:a[:,2:,1]=0
    return summarize(a,np.zeros((1200,4)),64)

def calculate(inputs,config):
    if config.get('constructed'):
        result={str(sign):fixture(sign) for sign in (-1,0,1)}
        assert result['1']['primary']['verdict']=='supports' and result['-1']['primary']['verdict']=='against'
        assert result['0']['primary']['difference']==0 and result['0']['primary']['interval'][0]<0<result['0']['primary']['interval'][1]
        return result
    for x in inputs.values():assert filehash(Path(x['path']))==x['sha256']
    result=summarize(*load(inputs['source']['path']),draws=config.get('draws',2000))
    parent=read(inputs['parent']['path'])
    assert result['common_fingerprints']==parent['common_fingerprints']
    assert abs(result['original_subset_difference']-parent['primary']['difference'])<1e-14
    assert result['original_subset_rates']==parent['equal_exposure_rates']
    return result

def execute(output,inputs,config):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    freeze(output/'SCIENCE.json',calculate(inputs,config));return dict(status='complete',constructed=bool(config.get('constructed')))

def verify(output,inputs,config):
    assert calculate(inputs,config)==read(Path(output)/'SCIENCE.json')
    return dict(verified=True,complete_recalculation=True)
