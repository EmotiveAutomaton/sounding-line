"""D19 complete-source NMF cost, no scientific component interpretation.

DESIGN CHECK: LESSONS 3-5, CONTROLS 1-7 read. NULL has low-rank approximations
without mechanisms; ALTERNATIVE known nonnegative mixtures reconstruct. Refuse
unconverged fits and changed sources; all missing features carry explicit flags.
"""
from pathlib import Path
import gzip,json,math,time,warnings
import numpy as np
from sklearn.decomposition import NMF
from sklearn.exceptions import ConvergenceWarning
from threadpoolctl import threadpool_limits
from runners.stage14.common import read,filehash,freeze,atomic

CONFIG=dict(card='D19-cost',schema=1,ranks=list(range(5,16)),seed=20261026,max_iter=1000,tol=.0001)


def load(inputs):
    if set(inputs)!={'pmap_complete'}:raise ValueError('Source contract differs')
    path=Path(inputs['pmap_complete']);complete=read(path)
    if complete['status']!='COMPLETE' or not complete['fresh_process_verified']:raise ValueError('Incomplete PMAP source')
    files=sorted(f for f in complete['outputs'] if f.startswith('output/sessions/') and f.endswith('.json.gz'))
    if len(files)!=1399:raise ValueError('Incomplete session census')
    rows=[]
    for name in files:
        p=(path.parent/name).resolve();p.relative_to(path.parent.resolve())
        if filehash(p)!=complete['outputs'][name]:raise ValueError('Session source changed')
        rows.append(json.loads(gzip.decompress(p.read_bytes())))
    if len({r['session'] for r in rows})!=1399 or len({r['writer'] for r in rows})!=61:raise ValueError('Source identity census differs')
    return sorted(rows,key=lambda r:r['session'])


def matrix(rows):
    process=[];content=[];missing=0
    for r in rows:
        values=[];flags=[]
        def put(value):
            nonlocal missing
            absent=value is None;flags.append(float(absent));values.append(0. if absent else float(value));missing+=int(absent)
        handling=r['handling'];total=sum(handling.values())
        for action in ('accept','edit','dismiss','ignore'):put(handling.get(action,0)/total if total else None)
        for kind in ('content','housekeeping'):put(r['revision'].get(kind,0)/r['typed_words'] if r['typed_words'] else None)
        put(r['requests']/r['typed_words'] if r['typed_words'] else None)
        put(r['edited_accepted_characters']/r['accepted_characters'] if r['accepted_characters'] else None)
        put(math.log1p(r['typed_words']));put(math.log1p(r['final_words']))
        for field in ('within_intervals','onset_intervals'):
            raw=np.asarray(r[field],float)
            if not np.isfinite(raw).all() or np.any(raw<0):raise ValueError('Invalid timing')
            put(math.log1p(float(np.median(raw))) if len(raw) and r['tc_timing_mode']!='invalid' else None)
        c=[]
        for prefix in ('accepted','declined'):
            n=r[prefix+'_options'];a=np.asarray(r[prefix+'_vector_sum'],float)
            if type(n) is not int or n<0 or a.shape!=(384,) or not np.isfinite(a).all():raise ValueError('Invalid content source')
            if n==0 and np.any(a!=0):raise ValueError('Missing content has nonzero sum')
            a=a/n if n else a;flags.append(float(n==0));missing+=int(n==0)
            c.extend(np.maximum(a,0));c.extend(np.maximum(-a,0))
        process.append(values+flags);content.append(c)
    blocks=[];scales=[]
    for raw in (process,content):
        a=np.asarray(raw,float)
        if a.ndim!=2 or not len(a) or not np.isfinite(a).all() or np.any(a<0):raise ValueError('Nonnegative finite features required')
        scale=np.sqrt(np.mean(a*a,axis=0));scale=np.where(scale==0,1,scale)
        blocks.append(a/scale/math.sqrt(a.shape[1]));scales.append(scale.tolist())
    x=np.c_[*blocks]
    if not np.any(x):raise ValueError('Entire source constant zero')
    return x,dict(rows=len(rows),writers=len({r['writer'] for r in rows}),block_widths=[b.shape[1] for b in blocks],missing_cells=missing,rms_scales=scales,scientific_admission=False)


def fit(x,k):
    x=np.asarray(x,float)
    if x.ndim!=2 or not np.isfinite(x).all() or np.any(x<0) or not 1<=k<=min(x.shape):raise ValueError('Invalid NMF matrix')
    with warnings.catch_warnings():
        warnings.simplefilter('error',ConvergenceWarning)
        model=NMF(n_components=k,init='nndsvda',solver='cd',beta_loss='frobenius',tol=CONFIG['tol'],max_iter=CONFIG['max_iter'],random_state=CONFIG['seed'],alpha_W=0.,alpha_H=0.,l1_ratio=0.,shuffle=False)
        w=model.fit_transform(x);h=model.components_
    if not np.isfinite(w).all() or not np.isfinite(h).all() or np.any(w<0) or np.any(h<0):raise ValueError('Invalid factors')
    error=float(np.linalg.norm(x-w@h));return w,h,dict(rank=k,iterations=int(model.n_iter_),frobenius_error=error,relative_error=error/float(np.linalg.norm(x)))


def bootstrap(rows,seed):
    names=sorted({r['writer'] for r in rows});rng=np.random.default_rng(seed)
    return np.array([i for w in rng.choice(names,size=len(names),replace=True) for i,r in enumerate(rows) if r['writer']==w],int)


def run(output,inputs,config,verify=False,loader=load):
    if config!=CONFIG:raise ValueError('Frozen D19 config required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True);rows=loader(inputs);x,meta=matrix(rows)
    binding=dict(inputs={k:filehash(v) for k,v in inputs.items()},config=config)
    for name,value in (('BINDING.json',binding),('SOURCE.json',meta)):
        if verify:
            if read(output/name)!=value:raise ValueError('Source replay differs')
        else:freeze(output/name,value)
    selected=bootstrap(rows,config['seed']);timings=[];sizes=[]
    for k in config['ranks']:
        for arm,xx in (('real',x),('bootstrap',x[selected])):
            started=time.process_time();w,h,record=fit(xx,k);timings.append(time.process_time()-started)
            stem=f'{k:02d}-{arm}';dest=output/(stem+'.npz')
            if verify:
                with np.load(dest) as saved:
                    if not np.array_equal(w,saved['W']) or not np.array_equal(h,saved['H']):raise ValueError('Fresh factors differ')
                if read(output/(stem+'.json'))!=record:raise ValueError('Fresh fit record differs')
            else:
                if dest.exists():
                    with np.load(dest) as saved:
                        if not np.array_equal(w,saved['W']) or not np.array_equal(h,saved['H']):raise ValueError('Changed retained factors')
                else:np.savez_compressed(dest,W=w,H=h)
                freeze(output/(stem+'.json'),record)
            sizes.append(dest.stat().st_size);atomic(output/'PROGRESS.json',dict(phase='verify' if verify else 'execute',fits=len(timings),total=22))
            if (output/'YIELD_REQUEST.json').exists() or (output.parent/'STOP').exists():raise InterruptedError('D19 fit boundary yield')
    timing=dict(max_fit_cpu_seconds=max(timings),all_fit_cpu_seconds=sum(timings),fits=len(timings),max_bytes=max(sizes))
    freeze(output/('VERIFY_TIMING.json' if verify else 'EXECUTE_TIMING.json'),timing)
    if verify:
        old=read(output/'EXECUTE_TIMING.json');worst=max(old['max_fit_cpu_seconds'],timing['max_fit_cpu_seconds']);count=11*(1+2000+1000)
        freeze(output/'FORECAST.json',dict(full_cpu_seconds=6*(worst*count+120),both_passes=True,safety_factor=3,ranks=11,stability_bootstraps=2000,reliability_references=1000,upper_factor_bytes=count*max(old['max_bytes'],timing['max_bytes']),scientific_admission=False,scope='Conservative full-refit workload envelope; scientific controls and gate remain unimplemented'))
    return dict(verified=True,full_fresh_fit_replay=True,timing_only=True) if verify else dict(status='complete',timing_only=True)


def execute(output,inputs,config):
    with threadpool_limits(limits=2):return run(output,inputs,config)


def verify(output,inputs,config):
    with threadpool_limits(limits=2):return run(output,inputs,config,True)
