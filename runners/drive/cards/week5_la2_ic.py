"""Fixed-design LA2 minimum-effect check, with exact cluster OLS operators.

DESIGN CHECK: no empirical effect chooses a dose or a threshold. Keep all
meeting clusters, missing-background exclusions and failed bootstrap draws.
Linearity amortizes repeated fits, while native fixtures compare with the
original expanded-row least squares and complete signed/null handlers.
"""
from pathlib import Path
import hashlib
import json
import time
import numpy as np
from . import week5_la as primary
from .week5_at_source import authenticate
from .week5_go import write, sha
from .timing_p6 import gzread

SEED=20261107
BAR=.02


def requested(root):
    return any((p/'YIELD_REQUEST.json').exists() for p in [root,*root.parents[:3]])


def design(rows):
    meetings=sorted({r['meeting'] for r in rows})
    if len(meetings)<20:raise ValueError('fewer than twenty meeting clusters: descriptive only')
    x=[];y=[];code=[]
    for index,meeting in enumerate(meetings):
        rr=[r for r in rows if r['meeting']==meeting]
        a=np.asarray([[r['same'],r['rate_a'],r['rate_b']] for r in rr],float)
        b=np.asarray([r['joined'] for r in rr],float)
        if not np.isfinite(a).all() or not np.isfinite(b).all():raise ValueError('nonfinite source')
        x.extend(a-a.mean(0));y.extend(b-b.mean());code.extend([index]*len(rr))
    return np.asarray(x),np.asarray(y),np.asarray(code,dtype=np.int64),len(meetings)


def operator(x,indices):
    """Exact first-coordinate OLS linear map, preserving original rank guards."""
    a=x[indices]
    if np.std(a[:,0])<=1e-12:raise ValueError('No within-meeting background contrast')
    if np.linalg.matrix_rank(a)<=np.linalg.matrix_rank(a[:,1:]):
        raise ValueError('Background and base rates are not separately identifiable')
    # Original LA2 uses lstsq(rcond=1e-10). SVD exposes the same Moore-Penrose
    # linear map without solving once per artificial response. Nuisance rank
    # deficiency is allowed exactly when the original target-rank guard allows.
    u,s,vh=np.linalg.svd(a,full_matrices=False)
    keep=s>1e-10*s[0]
    local=(vh[keep,0]/s[keep])@u[:,keep].T
    result=np.zeros(len(x));np.add.at(result,indices,local)
    return result


def matrix_hash(*arrays):
    h=hashlib.sha256()
    for a in arrays:
        a=np.ascontiguousarray(a);h.update(str((a.dtype.str,a.shape)).encode());h.update(a.tobytes())
    return h.hexdigest()


def calibration(x,y,code,clusters,config,output,source_binding):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    draws=int(config.get('draws',2000));worlds=int(config.get('worlds',100))
    if draws!=2000 or worlds!=100:raise ValueError('registered full sensitivity is 100 worlds and 2000 draws')
    semantic={k:v for k,v in config.items() if k not in {'max_new_draws','max_wall_seconds'}}
    binding=dict(source=source_binding,config=semantic,matrix=matrix_hash(x,y,code),
        module_sha256=sha(__file__),primary_sha256=sha(primary.__file__))
    bp=output/'BINDING.json'
    if bp.exists() and json.loads(bp.read_text('utf8'))!=binding:raise ValueError('fixed sensitivity binding changed')
    write(bp,binding)
    try:point=operator(x,np.arange(len(x)))
    except ValueError as error:return dict(status='design cannot test',reason=str(error),card='LA2.ic',source=source_binding)
    lookup=[np.flatnonzero(code==i) for i in range(clusters)]
    rng=np.random.default_rng(SEED);operators=[];failed=[];new=0;started=time.monotonic()
    for start in range(0,draws,100):
        selections=[rng.choice(clusters,clusters,replace=True) for _ in range(100)]
        path=output/'operators'/f'{start:04d}.npy';seal=path.with_suffix('.seal.json')
        if path.exists():
            saved=json.loads(seal.read_text('utf8'))
            if saved['binding']!=binding or saved['sha256']!=sha(path):raise ValueError('operator checkpoint changed')
            batch=np.load(path,allow_pickle=False)
            if batch.shape!=(100,len(y)):raise ValueError('operator shape changed')
            local_failed=saved['failed']
        else:
            if new>=config.get('max_new_draws',draws) or requested(output) or time.monotonic()-started>=config.get('max_wall_seconds',900):
                return dict(status='yielded',complete_card=False,completed_draws=start,draws=draws)
            batch=[];local_failed=[]
            for offset,selected in enumerate(selections):
                try:batch.append(operator(x,np.concatenate([lookup[i] for i in selected])))
                except ValueError as error:
                    batch.append(np.full(len(y),np.nan));local_failed.append(dict(draw=start+offset,reason=str(error)))
            batch=np.asarray(batch);path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('xb') as stream:np.save(stream,batch,allow_pickle=False)
            write(seal,dict(binding=binding,sha256=sha(path),failed=local_failed));new+=100
        operators.append(batch);failed.extend(local_failed)
        write(output/'PROGRESS.json',dict(completed_draws=start+100,total_draws=draws,new_draws=new))
        if not (output/'PILOT.json').exists():
            elapsed=time.monotonic()-started
            write(output/'PILOT.json',dict(completed_draws=start+100,total_draws=draws,wall_seconds=elapsed,
                forecast_operator_wall_seconds=elapsed*draws/(start+100),scope='operator bank only; world reduction and fresh replay additional'))
    if failed:
        return dict(status='invalid sensitivity',card='LA2.ic',failed_draws=failed,retained_draws=draws,
                    no_draws_discarded_or_replaced=True,source=source_binding)
    bank=np.concatenate(operators)
    beta=np.linalg.lstsq(x,y,rcond=1e-10)[0];residual=y-x@beta
    null=beta.copy();null[0]=0
    results=[]
    for multiple in (-1,0,1):
        truth=multiple*BAR;records=[]
        for world in range(worlds):
            rng=np.random.default_rng(np.random.SeedSequence([SEED,world,902]))
            signs=rng.choice([-1.,1.],clusters)
            planted=x@null+truth*x[:,0]+residual*signs[code]
            estimate=float(point@planted);samples=bank@planted
            lo,hi=np.quantile(samples,[.025,.975])
            records.append(dict(estimate=estimate,interval=[float(lo),float(hi)],
                covers_truth=bool(lo-1e-10<=truth<=hi+1e-10),
                excludes_zero=bool(lo>1e-10 if multiple>0 else hi< -1e-10 if multiple<0 else lo>1e-10 or hi< -1e-10),
                primary_positive_support=bool(lo>BAR)))
        write(output/'worlds'/f'effect-{multiple}.json',records)
        results.append(dict(effect_multiple=multiple,injected_contrast=truth,worlds=worlds,
            zero_exclusion_rate=float(np.mean([r['excludes_zero'] for r in records])),
            coverage=float(np.mean([r['covers_truth'] for r in records])),
            primary_positive_support_rate=float(np.mean([r['primary_positive_support'] for r in records])),
            estimate_quantiles=np.quantile([r['estimate'] for r in records],[.025,.5,.975]).tolist()))
    return dict(status='complete',card='LA2.ic',clusters=clusters,pairs=len(y),draws=draws,worlds_per_effect=worlds,
        practical_bar=BAR,effects=results,failed_draws=[],source=source_binding,
        sensitivity_pass=results[1]['zero_exclusion_rate']<=.1 and min(results[0]['zero_exclusion_rate'],results[2]['zero_exclusion_rate'])>=.8,
        rule='null zero-exclusion <=0.10 and both signed one-bar zero-exclusion >=0.80',
        scope='fixed original within-meeting design and whole-meeting wild residual vectors; linear estimator calibration, not new bounded source observations',
        bootstrap='original 2000 whole-meeting draws reused as common random numbers across worlds; exact OLS linear maps',
        decision_threshold_distinction='zero exclusion at the minimum effect is separate from crossing the positive primary practical bar')


def load(inputs,config):
    if set(inputs)!={'source_root','primary_root'}:raise ValueError('exact complete LA2 source and primary roots required')
    source=authenticate(inputs['source_root']);parent=authenticate(inputs['primary_root'])
    plan=json.loads((parent/'PLAN.json').read_text('utf8'))
    path=source/'output/ROWS.json.gz'
    if Path(plan['inputs']['rows']).resolve()!=path.resolve() or plan['config'].get('card')!='LA2' or plan['config'].get('draws',2000)!=2000:
        raise ValueError('parent source/primary scope mismatch')
    summary=json.loads((source/'output/SUMMARY.json').read_text('utf8'))
    scope=(summary['corpus'],summary['background'])
    if scope not in [('AMI','native_language'),('ICSI','english_variety'),('ICSI','region')]:raise ValueError('unregistered LA2 background scope')
    if summary.get('constructed',False)!=bool(config.get('constructed_fixture')):raise ValueError('constructed source mismatch')
    return gzread(path),dict(corpus=scope[0],background=scope[1],rows_sha256=sha(path),
        source_complete_sha256=sha(source/'COMPLETE.json'),primary_complete_sha256=sha(parent/'COMPLETE.json'),primary_plan_sha256=sha(parent/'PLAN.json'))


def execute(output,inputs,config):
    if set(config)-{'draws','worlds','max_new_draws','max_wall_seconds','constructed_fixture'}:raise ValueError('unregistered sensitivity setting')
    rows,binding=load(inputs,config)
    try:x,y,code,clusters=design(rows)
    except ValueError as error:result=dict(status='design cannot test',card='LA2.ic',reason=str(error),source=binding)
    else:result=calibration(x,y,code,clusters,config,Path(output),binding)
    if result.get('status')!='yielded':write(Path(output)/'RESULT.json',result)
    return result


def verify(output,inputs,config):
    output=Path(output);actual=execute(output/'independent-replay',inputs,config)
    if actual.get('status')=='yielded':return dict(actual,verified=False)
    if actual!=json.loads((output/'RESULT.json').read_text('utf8')):raise ValueError('complete LA2 sensitivity replay differs')
    for path in sorted((output/'worlds').glob('*.json')):
        if path.read_bytes()!=(output/'independent-replay/worlds'/path.name).read_bytes():raise ValueError('world bank differs')
    return dict(verified=True,complete_worlds_and_all_bootstrap_operators_replayed=True)
