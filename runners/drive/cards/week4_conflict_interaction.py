"""S6.m complete centered-interaction comparison.

DESIGN CHECK: LESSONS3-5 / CONTROLS1-7 reread2026-11-04. Known NULL and
main-only worlds recover zero interaction; signed ALTERNATIVE targets recover.
Every history shuffle rebuilds the product. Rank loss, incomplete banks and
changed source/output refuse. Complete paired resampling retains the parent.
"""
from pathlib import Path
import time
import numpy as np
from threadpoolctl import threadpool_limits
from runners.stage14.common import atomic, read, filehash
from . import week4_conflict_stats as parent
from . import week4_conflict_inference as inference
from . import week4_conflict_spec as spec
from .timing_stats import sufficient
from .timing_p6 import write_equal

NAMES=parent.NAMES+('own_entropy_interaction',)
MEASURES=('interaction','adjusted_own','original_own','paired_difference')
WORLDS=('null','positive','negative','main_only','combined','donor_only')
_basis=parent.copied(parent.original.basis,NAMES=NAMES)


def basis(groups):
    keep,omitted=_basis(groups)
    if any(n in omitted for n in NAMES[-3:]):
        raise ValueError('Interaction or conflict coefficient not identifiable')
    return keep,omitted


fit=parent.copied(parent.original.fit,NAMES=NAMES,basis=basis)


def product(x,w):
    values=np.empty(len(x))
    for writer in sorted(set(w)):
        ix=np.flatnonzero(w==writer);a=x[ix,0];b=x[ix,10]
        values[ix]=(a-a.mean())*(b-b.mean())
    return values


def design(rows):
    x,y,w=parent.design(rows)
    return np.column_stack([x,product(x,w)]),y,w


def paired_fit(groups,base):
    a,b=fit(groups),parent.adjusted_fit(base)
    return dict(interaction=a['coefficients'][NAMES[-1]],adjusted_own=a['own'],
                original_own=b['own'],paired_difference=a['own']-b['own'],
                adjusted=a,original=b)


def references(x,y,w,source_rng,outcome_rng):
    xx,yy=x.copy(),y.copy()
    for writer in sorted(set(w)):
        ix=np.flatnonzero(w==writer)
        xx[ix,0]=source_rng.permutation(x[ix,0]);yy[ix]=outcome_rng.permutation(y[ix])
    xx[:,-1]=product(xx,w)
    return [('own_surprise',xx,y),('outcome',x,yy)]


def null_summary(values,observed):
    result=parent.original.null_summary(values,observed)
    result.pop('one_sided_p')
    result['two_sided_p']=None
    if not result['invalid_draws'] and result['valid_draws'] and observed is not None:
        result['two_sided_p']=(1+sum(abs(v)>=abs(observed) for v in values))/(len(values)+1)
    return result


def run(rows,blocks=10,progress=None):
    if blocks not in (1,10):raise ValueError('Only first tenth or complete bank')
    x,y,w=design(rows);writers=sorted(set(w))
    if len(writers)!=20:raise ValueError('Exactly twenty frozen writers required')
    groups,base=sufficient(x,y,w),sufficient(x[:,:12],y,w)
    try:point=paired_fit(groups,base)
    except ValueError as exc:return dict(state='invalid',reason=str(exc),attempted_bootstraps=0)
    rng=np.random.default_rng(20261102);draws=[];controls=[]
    for block in range(blocks):
        for _ in range(200):
            ids=rng.integers(0,len(writers),len(writers))
            try:draws.append(paired_fit([groups[i] for i in ids],[base[i] for i in ids]))
            except ValueError as exc:return dict(state='invalid',reason='undefined paired bootstrap: '+str(exc),attempted_bootstraps=len(draws)+1)
        source_rng=np.random.default_rng(np.random.SeedSequence([20261102,block,1]))
        outcome_rng=np.random.default_rng(np.random.SeedSequence([20261102,block,2]))
        for _ in range(20):
            item={}
            for name,a,b in references(x,y,w,source_rng,outcome_rng):
                try:item[name]=dict(effect=fit(sufficient(a,b,w))['coefficients'][NAMES[-1]],reason=None)
                except ValueError as exc:item[name]=dict(effect=None,reason=str(exc))
            controls.append(item)
        if progress is not None:progress(dict(blocks=block+1,total_blocks=blocks,bootstraps=len(draws),permutations=len(controls)))
    return dict(state='complete' if blocks==10 else 'cost_only',point=point,
                statistics={k:parent.original.interval(point[k],[r[k] for r in draws]) for k in MEASURES},
                controls={k:null_summary([r[k]['effect'] for r in controls],point['interaction']) for k in ('own_surprise','outcome')},
                bootstrap_draws=len(draws),permutation_draws=len(controls),writer_count=20,observations=len(rows),
                complete_banks=blocks==10,bootstrap_values=[{k:r[k] for k in MEASURES} for r in draws],reference_values=controls,causal_claim=False)


def world(name):
    if name not in WORLDS:raise ValueError('Unknown interaction world')
    rng=np.random.default_rng(20261102);x=rng.normal(size=(80,12));x[:,2]=1.
    for j in range(12):
        if j!=2:x[:,j]-=x[:,j].mean()
    x[:,10]+=1.;x[:,11]-=.5
    z=np.column_stack([x,product(x,np.array(['one']*len(x)))])
    beta=np.array([0.,.25 if name=='donor_only' else 0.,.4,.1,.08,-.1,.1,-.1,.2,.1,0.,0.,0.])
    if name in ('main_only','combined'):beta[0]=.4;beta[10:12]=[.6,.4]
    beta[-1]=.3 if name in ('positive','combined') else -.3 if name=='negative' else 0.
    rows=[]
    for wi in range(20):
        noise=rng.normal(size=80);noise-=z@np.linalg.lstsq(z,noise,rcond=None)[0]
        y=z@beta+.3*noise+.2*rng.normal()
        for i in range(80):
            r=dict(zip(parent.NAMES,x[i].tolist()));r.update(writer=f'w{wi:02}',log_pause=float(y[i]),original_personal_surprise=r['own_surprise']);rows.append(r)
    return rows,dict(interaction=float(beta[-1]),adjusted_own=float(beta[0]))


def dense_coefficients(rows,ratio):
    x,y,w=design(rows);a=np.zeros((13,13));b=np.zeros(13)
    for writer in sorted(set(w)):
        xx,yy=x[w==writer],y[w==writer]
        inverse=np.eye(len(yy))-ratio/(1+len(yy)*ratio)*np.ones((len(yy),len(yy)))
        a+=xx.T@inverse@xx;b+=xx.T@inverse@yy
    return np.linalg.solve(a,b)


def known_answers():
    results={}
    for name in WORLDS:
        rows,truth=world(name);x,y,w=design(rows);point=fit(sufficient(x,y,w))
        dense=dense_coefficients(rows,point['variance_ratio'])
        if not np.allclose(dense,[point['coefficients'][n] for n in NAMES],atol=2e-8,rtol=0):raise ValueError('Dense GLS mismatch')
        actual=dict(interaction=point['coefficients'][NAMES[-1]],adjusted_own=point['own'])
        if any(abs(actual[k]-v)>2e-8 for k,v in truth.items()):raise ValueError('Known coefficient failed')
        results[name]=dict(truth=truth,verified=True,dense_gls_verified=True)
    return results


def configuration(mode):
    if mode not in inference.MODES:raise ValueError('Unknown interaction mode')
    return dict(card='W4-S6.m-interaction',mode=mode,seed=20261102,draws=2000,permutations=200,center='within_writer',reference_tail='absolute_two_sided')


human_rows=parent.copied(spec.human_rows,__name__=__name__,configuration=configuration)


def calibration_check(value,truth):
    if value['state']!='complete' or value['bootstrap_draws']!=2000 or value['permutation_draws']!=200:raise ValueError('Incomplete calibration bank')
    for item in [value['point']]+value['bootstrap_values']:
        if any(abs(item[k]-v)>2e-8 for k,v in truth.items()):raise ValueError('Whole-bank algebraic target failed')
    if any(r['invalid_draws'] for r in value['controls'].values()):raise ValueError('Undefined calibration references')
    return True


def one_pass(output,inputs,config,verifying=False):
    if config!=configuration(config.get('mode')):raise ValueError('Frozen interaction configuration required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True);start=time.process_time();mode=config['mode']
    binding=dict(config=config,inputs={k:filehash(v) for k,v in inputs.items()})
    if verifying:
        if read(output/'INPUTS.json')!=binding:raise ValueError('Inputs changed')
    else:write_equal(output/'INPUTS.json',binding)
    if mode=='constructed':
        if inputs:raise ValueError('Constructed mode takes no human input')
        summary=dict(native_known_answers=known_answers(),human_scored=False)
    else:
        if mode.startswith('calibration'):
            if inputs:raise ValueError('Calibration takes no human input')
            tasks=[(name,*world(name)) for name in WORLDS]
        else:
            rows=human_rows(inputs,mode=='human-full')
            if mode=='human-cost':
                rng=np.random.default_rng(20261102);x,_,_=design(rows)
                rows=[dict(r,log_pause=float(.2*r['own_surprise']+.1*r['entropy']+.3*z+e)) for r,z,e in zip(rows,x[:,-1],rng.normal(size=len(rows)))]
            tasks=[('human' if mode=='human-full' else 'generated_human_shape',rows,None)]
        setup=time.process_time()-start;durations={};results={};passed=[]
        for name,rows,truth in tasks:
            began=time.process_time()
            def progress(item):atomic(output/'PROGRESS.json',dict(phase='verify' if verifying else 'execute',task=name,**item))
            value=run(rows,1 if mode.endswith('cost') else 10,progress);durations[name]=time.process_time()-began;results[name]=value
            if mode=='calibration-full' and value['state']=='complete':passed.append(calibration_check(value,truth))
            target=output/('PRIVATE_'+name+'.json')
            if verifying:
                if read(target)!=value:raise ValueError('Complete interaction replay differs')
            else:write_equal(target,value)
        if mode.endswith('cost'):
            if any(v['state']!='cost_only' for v in results.values()):raise ValueError('Undefined timing fit')
            summary=dict(mode=mode,tasks=len(tasks),blocks_per_task=1,human_scored=False,scientific_admission=False)
        elif mode=='calibration-full':summary=dict(mode=mode,tasks=6,calibration_pass=len(passed)==6 and all(passed),algebraic_known_answers=True,empirical_power_established=False,human_scored=False)
        else:
            value=results['human'];summary=dict(mode=mode,state=value['state'],writers=20,observations=len(rows),statistics=value.get('statistics'),controls=value.get('controls'),primary=value.get('statistics',{}).get('interaction'),reason=value.get('reason'),human_scored=True,descriptive=True,causal_claim=False,no_descendants=True)
        write_equal(output/('VERIFY_TIMING.json' if verifying else 'EXECUTE_TIMING.json'),dict(setup_cpu_seconds=setup,work_cpu_seconds=durations))
        if verifying and mode.endswith('cost'):
            previous=read(output/'EXECUTE_TIMING.json');forecast=6*(max(setup,previous['setup_cpu_seconds'])+10*sum(max(t,previous['work_cpu_seconds'][n]) for n,t in durations.items()))+30
            write_equal(output/'FORECAST.json',dict(full_cpu_seconds=forecast,safety_factor=3,includes_fresh_replay=True,includes_all_banks=True))
    if verifying:
        if read(output/'SUMMARY.json')!=summary:raise ValueError('Summary replay differs')
    else:write_equal(output/'SUMMARY.json',summary)
    return dict(verified=True,full_fresh_replay=True) if verifying else summary


def execute(output,inputs,config):
    with threadpool_limits(limits=1):return one_pass(output,inputs,config)


def verify(output,inputs,config):
    with threadpool_limits(limits=1):return one_pass(output,inputs,config,True)
