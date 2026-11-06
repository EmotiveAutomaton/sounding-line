"""S6.s complete paired conflict-specification curve.

DESIGN CHECK: LESSONS3-5 / CONTROLS1-7 reread2026-11-04. Known NULL,
signed alternatives and the analytically nonzero omitted-conflict case must
recover. Retained focal rank failures invalidate, never remove or redraw.
The original full comparator and all reference streams stay unchanged.
"""
from pathlib import Path
import time
import numpy as np
from threadpoolctl import threadpool_limits
from runners.stage14.common import atomic, read, filehash
from . import week4_conflict_stats as parent
from . import week4_conflict_inference as inference
from .timing_stats import sufficient
from .timing_p6 import write_equal

VARIANTS=('entropy_only','margin_only')
MEASURES=('adjusted_own','original_own','paired_difference')


def columns(variant):
    if variant not in VARIANTS: raise ValueError('Unknown specification')
    return list(range(10))+[10 if variant=='entropy_only' else 11]


def subset(groups, keep):
    return [dict(n=g['n'],xx=g['xx'][np.ix_(keep,keep)],xy=g['xy'][keep],
                 yy=g['yy'],sx=g['sx'][keep],sy=g['sy']) for g in groups]


def fit_variant(groups, variant):
    keep=columns(variant);names=tuple(parent.NAMES[i] for i in keep)
    original_basis=parent.copied(parent.original.basis,NAMES=names)
    def basis(projected):
        selected,omitted=original_basis(projected)
        if names[-1] in omitted: raise ValueError('Retained conflict term not identifiable')
        return selected,omitted
    fit=parent.copied(parent.original.fit,NAMES=names,basis=basis)
    return fit(subset(groups,keep))


def paired_fit(groups,variant):
    a,b=fit_variant(groups,variant),parent.adjusted_fit(groups)
    return dict(adjusted_own=a['own'],original_own=b['own'],
                paired_difference=a['own']-b['own'],adjusted=a,original=b)


def run_variant(rows,variant,blocks=10,progress=None):
    columns(variant)
    run=parent.copied(parent.run,MEASURES=MEASURES,
        paired_fit=lambda groups,unused:paired_fit(groups,variant),
        adjusted_fit=lambda groups:fit_variant(groups,variant))
    return run(rows,blocks=blocks,progress=progress,seed=20261102)


def world(name):
    if name not in parent.WORLDS: raise ValueError('Unknown calibration world')
    rng=np.random.default_rng(20261102)
    raw=rng.normal(size=(80,12));raw-=raw.mean(axis=0)
    q=np.linalg.qr(raw)[0]*np.sqrt(80)
    x=np.zeros((80,12));x[:,2]=1.
    indexes=[i for i in range(12) if i!=2]
    for j,i in enumerate(indexes): x[:,i]=q[:,j]
    x[:,10]=1.+.5*x[:,0]+.4*x[:,10]
    x[:,11]=-.5+.1*x[:,11]
    beta=np.array([0.,.25 if name=='donor_only' else 0.,.4,.1,.08,-.1,.1,-.1,.2,.1,0.,0.])
    beta[0]=.4 if name in ('own','own_and_conflict') else -.4 if name=='reverse' else 0.
    if name in ('conflict_only','own_and_conflict'): beta[-2:]=[.6,.4]
    rows=[]
    for wi in range(20):
        noise=rng.normal(size=80);noise-=x@np.linalg.lstsq(x,noise,rcond=None)[0]
        y=x@beta+.3*noise+.2*rng.normal()
        for i in range(80):
            r=dict(zip(parent.NAMES,x[i].tolist()))
            r.update(writer=f'w{wi:02}',log_pause=float(y[i]),original_personal_surprise=r['own_surprise'])
            rows.append(r)
    targets={v:dict(adjusted_own=float(beta[0]+(.5*beta[10] if v=='margin_only' else 0.)),
                   original_own=float(beta[0]),paired_difference=float(.5*beta[10] if v=='margin_only' else 0.)) for v in VARIANTS}
    return rows,targets


def dense_coefficients(rows,variant,ratio):
    x,y,w=parent.design(rows);x=x[:,columns(variant)]
    a=np.zeros((11,11));b=np.zeros(11)
    for writer in sorted(set(w)):
        xx,yy=x[w==writer],y[w==writer]
        inverse=np.eye(len(yy))-ratio/(1+len(yy)*ratio)*np.ones((len(yy),len(yy)))
        a+=xx.T@inverse@xx;b+=xx.T@inverse@yy
    return np.linalg.solve(a,b)


def known_answers():
    results={}
    for name in parent.WORLDS:
        rows,targets=world(name);x,y,w=parent.design(rows);groups=sufficient(x,y,w)
        for v in VARIANTS:
            point=paired_fit(groups,v);dense=dense_coefficients(rows,v,point['adjusted']['variance_ratio'])
            actual=[point['adjusted']['coefficients'][parent.NAMES[i]] for i in columns(v)]
            if not np.allclose(actual,dense,atol=2e-8,rtol=0):raise ValueError('Independent dense GLS mismatch')
            if any(abs(point[k]-targets[v][k])>2e-8 for k in MEASURES):raise ValueError('Known omitted-variable target mismatch')
        results[name]=dict(verified=True,dense_gls_verified=True,targets=targets)
    return results


def configuration(mode):
    if mode not in inference.MODES:raise ValueError('Unknown mode')
    return dict(card='W4-S6.s-specification',mode=mode,seed=20261102,variants=list(VARIANTS),draws=2000,permutations=200)


def human_rows(inputs,full=False):
    keys={'source_completion','parent_completion'}|({'calibration_completion','cost_completion'} if full else set())
    if set(inputs)!=keys:raise ValueError('Exact S6.s dependency bundle required')
    root=Path(inputs['parent_completion']).resolve().parent
    summary=inference.authenticated(root);plan=read(root/'PLAN.json')
    if plan['module']!=inference.__name__ or plan['config']!=inference.configuration('human-full') or summary['state']!='complete':
        raise ValueError('Complete original parent required')
    if plan['inputs']['source_completion']!=inputs['source_completion']:raise ValueError('Different parent source')
    rows=inference.human_rows({'source_completion':inputs['source_completion']})
    if full:
        for key,mode in [('calibration_completion','calibration-full'),('cost_completion','human-cost')]:
            root=Path(inputs[key]).resolve().parent;s=inference.authenticated(root);p=read(root/'PLAN.json')
            if p['module']!=__name__ or p['config']!=configuration(mode):raise ValueError('Wrong specification validation')
            if key=='calibration_completion' and not s['calibration_pass']:raise ValueError('Calibration failed')
            if key=='cost_completion' and p['inputs']!={k:inputs[k] for k in ('source_completion','parent_completion')}:
                raise ValueError('Cost used different source')
    return rows


def calibration_check(value,target):
    if value['state']!='complete' or value['bootstrap_draws']!=2000 or value['permutation_draws']!=200:
        raise ValueError('Incomplete calibration bank')
    for item in [value['point']]+value['bootstrap_values']:
        if any(abs(item[k]-target[k])>2e-8 for k in MEASURES):raise ValueError('Complete algebraic target failed')
    if any(r['invalid_draws'] for r in value['controls'].values()):raise ValueError('Undefined calibration reference')
    return True


def one_pass(output,inputs,config,verifying=False):
    if config!=configuration(config.get('mode')):raise ValueError('Frozen specification configuration required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True);start=time.process_time();mode=config['mode']
    binding=dict(config=config,inputs={k:filehash(v) for k,v in inputs.items()})
    if verifying:
        if read(output/'INPUTS.json')!=binding:raise ValueError('Inputs changed')
    else:write_equal(output/'INPUTS.json',binding)
    if mode=='constructed':
        if inputs:raise ValueError('Constructed mode has no human input')
        summary=dict(native_known_answers=known_answers(),human_scored=False)
    else:
        if mode.startswith('calibration'):
            if inputs:raise ValueError('Calibration has no human input')
            tasks=[(name,*world(name)) for name in parent.WORLDS]
        else:
            rows=human_rows(inputs,mode=='human-full')
            if mode=='human-cost':
                rng=np.random.default_rng(20261102)
                rows=[dict(r,log_pause=float(.2*r['own_surprise']+.1*r['entropy']+e)) for r,e in zip(rows,rng.normal(size=len(rows)))]
            tasks=[('human' if mode=='human-full' else 'generated_human_shape',rows,None)]
        setup=time.process_time()-start;durations={};results={};passes=[]
        for name,rows,targets in tasks:
            for variant in VARIANTS:
                key=name+'-'+variant;began=time.process_time()
                def progress(item):atomic(output/'PROGRESS.json',dict(phase='verify' if verifying else 'execute',task=key,**item))
                value=run_variant(rows,variant,1 if mode.endswith('cost') else 10,progress)
                durations[key]=time.process_time()-began;results[key]=value
                if mode=='calibration-full':passes.append(calibration_check(value,targets[variant]))
                path=output/('PRIVATE_'+key+'.json')
                if verifying:
                    if read(path)!=value:raise ValueError('Complete specification replay differs: '+key)
                else:write_equal(path,value)
        if mode.endswith('cost'):
            if any(v.get('state')!='cost_only' for v in results.values()):raise ValueError('Undefined timing fit')
            summary=dict(mode=mode,tasks=len(results),blocks_per_task=1,human_scored=False,scientific_admission=False)
        elif mode=='calibration-full':
            summary=dict(mode=mode,tasks=len(results),calibration_pass=len(passes)==12 and all(passes),algebraic_known_answers=True,empirical_power_established=False,human_scored=False)
        else:
            summary=dict(mode=mode,state='complete' if all(v['state']=='complete' for v in results.values()) else 'invalid',writers=20,observations=len(rows),
                variants={v:{k:results['human-'+v].get(k) for k in ('statistics','controls','reason','bootstrap_draws','permutation_draws','complete_banks')} for v in VARIANTS},
                human_scored=True,descriptive=True,causal_claim=False,no_descendants=True)
        timing=dict(setup_cpu_seconds=setup,work_cpu_seconds=durations)
        write_equal(output/('VERIFY_TIMING.json' if verifying else 'EXECUTE_TIMING.json'),timing)
        if verifying and mode.endswith('cost'):
            previous=read(output/'EXECUTE_TIMING.json')
            forecast=6*(max(setup,previous['setup_cpu_seconds'])+10*sum(max(t,previous['work_cpu_seconds'][n]) for n,t in durations.items()))+30
            write_equal(output/'FORECAST.json',dict(full_cpu_seconds=forecast,safety_factor=3,includes_fresh_replay=True,includes_all_banks=True))
    if verifying:
        if read(output/'SUMMARY.json')!=summary:raise ValueError('Summary replay differs')
    else:write_equal(output/'SUMMARY.json',summary)
    return dict(verified=True,full_fresh_replay=True) if verifying else summary


def execute(output,inputs,config):
    with threadpool_limits(limits=1):return one_pass(output,inputs,config)


def verify(output,inputs,config):
    with threadpool_limits(limits=1):return one_pass(output,inputs,config,True)
