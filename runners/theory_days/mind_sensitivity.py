"""TD6.ic conditional rare-count calibration of the unchanged statistic.

DESIGN CHECK: LESSONS 3-5, CONTROLS 6-7. Retain undefined worlds, singleton
strata and the exact original bootstrap seed/call order. Null false support
and planted practical-size power have separate precommitted gates.
"""
from pathlib import Path
import numpy as np
from runners.stage14.common import read,freeze,filehash
from .intake import read_goemotions
from .emotions import matched_pairs,mind_contrast

DOSES=(0.,-.1,-.2,-.4,.2)

def bank(pairs,draws=2000,seed=20261106):
    if not pairs or draws<2:raise ValueError('Missing pair support or draws')
    groups={}
    for i,row in enumerate(pairs):groups.setdefault(row[0],[]).append(i)
    # Float64 stores these small integer multiplicities exactly and uses BLAS.
    rng=np.random.default_rng(seed);weights=np.zeros((draws,len(pairs)),dtype=float)
    for draw in range(draws):
        for ids in groups.values():
            w=np.bincount(rng.integers(len(ids),size=len(ids)),minlength=len(ids))
            weights[draw,ids]=w
    assert np.all(weights.sum(axis=1)==len(pairs))
    return weights

def summarize(values,weights):
    a=np.asarray(values)
    if a.ndim!=2 or a.shape[1]!=4 or len(a)!=weights.shape[1]:raise ValueError('Count shape')
    if not np.isfinite(a).all() or np.any(a<0) or np.any(a!=a.astype(np.int64)):raise ValueError('Invalid counts')
    if np.any(a[:,[0,2]]>a[:,[1,3]]):raise ValueError('Hits exceed tokens')
    total=a.sum(axis=0);boots=weights@a
    def ratio(v):
        x,n,y,m=np.moveaxis(v,-1,0)
        with np.errstate(divide='ignore',invalid='ignore'):
            r=(x/n-y/m)/(y/m)
        return np.where((n>0)&(m>0)&(y>0),r,np.nan)
    point=float(ratio(total));samples=ratio(boots)
    ci=np.quantile(samples,[.025,.975]).tolist() if np.isfinite(samples).all() else None
    verdict='inconclusive' if ci is None else 'supports' if ci[1]<-.1 else 'against' if ci[0]>-.1 else 'inconclusive'
    return dict(pairs=len(a),disgust_hits=int(total[0]),disgust_tokens=int(total[1]),anger_hits=int(total[2]),anger_tokens=int(total[3]),relative_difference=point if np.isfinite(point) else None,interval=ci,undefined_draws=int((~np.isfinite(samples)).sum()),verdict=verdict)

def wilson(k,n):
    if not 0<=k<=n or n<1:raise ValueError('Invalid binomial count')
    z=1.959963984540054;q=k/n;den=1+z*z/n
    mid=(q+z*z/(2*n))/den;rad=z*np.sqrt(q*(1-q)/n+z*z/(4*n*n))/den
    return [max(0.,float(mid-rad)),min(1.,float(mid+rad))]

def world(lengths,p,delta,rng):
    lengths=np.asarray(lengths)
    if lengths.ndim!=2 or lengths.shape[1]!=2 or np.any(lengths<0) or np.any(lengths!=lengths.astype(np.int64)):raise ValueError('Invalid lengths')
    if not (0<p<=1 and 0<=p*(1+delta)<=1):raise ValueError('Impossible binomial probability')
    hits=rng.binomial(lengths.astype(np.int64),np.array([p*(1+delta),p]))
    return np.column_stack([hits[:,0],lengths[:,0],hits[:,1],lengths[:,1]])

def calibration(pairs,worlds,draws,population):
    values=np.asarray([r[1:5] for r in pairs],dtype=np.int64);weights=bank(pairs,draws)
    original=summarize(values,weights)
    assert original==mind_contrast(pairs,draws), 'Parent bootstrap parity'
    p=float(values[:,[0,2]].sum()/values[:,[1,3]].sum())
    sizes={}
    for r in pairs:sizes[r[0]]=sizes.get(r[0],0)+1
    result={}
    for d,delta in enumerate(DOSES):
        records=[]
        for i in range(worlds):
            rng=np.random.default_rng(np.random.SeedSequence([20261106,population,d,i]))
            records.append(summarize(world(values[:,[1,3]],p,delta,rng),weights))
        counts={v:sum(r['verdict']==v for r in records) for v in ('supports','against','inconclusive')}
        counts.update(coverage=sum(r['interval'] is not None and r['interval'][0]<=delta<=r['interval'][1] for r in records),zero_exclusion=sum(r['interval'] is not None and (r['interval'][0]>0 or r['interval'][1]<0) for r in records),collapsed_interval=sum(r['interval'] is not None and r['interval'][0]==r['interval'][1] for r in records),undefined_interval=sum(r['interval'] is None for r in records),undefined_point=sum(r['relative_difference'] is None for r in records))
        result[str(delta)]=dict(delta=delta,worlds=worlds,counts=counts,wilson95={k:wilson(v,worlds) for k,v in counts.items()},records=records)
    adequate=result['0.0']['wilson95']['supports'][1]<=.1 and result['-0.2']['wilson95']['supports'][0]>=.8
    return dict(original=original,pooled_hit_probability=p,subreddits=len(sizes),singleton_subreddits=sum(n==1 for n in sizes.values()),worlds_per_dose=worlds,draws=draws,doses=result,sensitivity='adequate in construction' if adequate else 'limited in construction')

def fixtures():
    pairs=[('a',i%3,10,2,10,True,True) for i in range(8)]+[('singleton',0,10,1,10,True,True)]
    w=bank(pairs,64);assert np.all(w[:,-1]==1)
    baseline=summarize(np.array([p[1:5] for p in pairs]),w);assert baseline==mind_contrast(pairs,64)
    states={}
    for label,x,y in [('zero',2,2),('negative',1,4),('positive',4,1),('undefined',0,0)]:
        a=np.tile([x,10,y,10],(len(pairs),1));states[label]=summarize(a,w)
    assert states['zero']['relative_difference']==0 and states['zero']['verdict']=='against'
    assert states['negative']['verdict']=='supports' and states['positive']['verdict']=='against'
    assert states['undefined']['interval'] is None and states['undefined']['undefined_draws']==64
    return dict(states=states,calibration=calibration(pairs,2,64,0),singleton_bank=True)

def calculate(inputs,config):
    if config.get('constructed'):return fixtures()
    for item in inputs.values():assert filehash(item['path'])==item['sha256']
    frame=read_goemotions(inputs['go_emotions']['path']);frame=frame.loc[~frame.example_very_unclear]
    pairs,strict=matched_pairs(frame,2)
    if len(pairs)<300:pairs,used=matched_pairs(frame,1)
    else:used=strict
    if len(pairs)<300:raise ValueError('Missing parent support')
    person=[r for r in pairs if r[5] and r[6]]
    if not person:raise ValueError('Missing companion support')
    parent=read(inputs['parent']['path']);assert parent['strict']==strict and parent['used']==used
    result={}
    for pop,(name,rows) in enumerate((('primary',pairs),('person_targeted',person))):
        result[name]=calibration(rows,config['worlds'],2000,pop)
        assert result[name]['original']==parent[name], 'Complete parent reproduction'
    return dict(status='complete',constructed=True,strict=strict,used=used,populations=result,causal_claim=False)

def execute(output,inputs,config):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    freeze(output/'CALIBRATION.json',calculate(inputs,config));return dict(status='complete',constructed=True)

def verify(output,inputs,config):
    assert calculate(inputs,config)==read(Path(output)/'CALIBRATION.json')
    return dict(verified=True,complete_recalculation=True)
