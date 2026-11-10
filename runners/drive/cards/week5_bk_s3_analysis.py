"""S3 equal-writer paired contrast, complete bootstrap and rematched reference."""
from collections import defaultdict
from pathlib import Path
import math,time
import numpy as np
from threadpoolctl import threadpool_limits
from .week5_bk_s3_source import match,SEED
from .timing_pmap_source import completed
from .timing_p6 import gzread,gzip_equal,write_equal,progress
from .timing_census import read

CELLS=('primary','next_paragraph','prompt','final_document')

def fit(rows,cell='primary',writer_counts=None):
    pairs=match(rows);usable=[]
    for a,b in pairs:
        if a['scores'].get(cell) is None or b['scores'].get(cell) is None:continue
        usable.append((a,b))
    by_writer=defaultdict(list)
    for a,b in usable:by_writer[a['writer']].append((a,b))
    if not usable:return dict(effect=None,writers=0,pairs=0,reason='no complete matched pairs')
    writer_counts={w:1 for w in by_writer} if writer_counts is None else writer_counts
    x=[];y=[];weights=[]
    for writer,pairs_ in by_writer.items():
        for a,b in pairs_:
            x.append([1.,a['position']-b['position'],(a['remaining']-b['remaining'])/60])
            y.append(a['scores'][cell]-b['scores'][cell]);weights.append(writer_counts.get(writer,0)/len(pairs_))
    x=np.asarray(x);y=np.asarray(y);weights=np.asarray(weights);chosen=weights>0
    if not chosen.any():return dict(effect=None,writers=0,pairs=0,reason='no selected writer pairs')
    x=x[chosen];y=y[chosen];weights=weights[chosen];scale=np.sqrt(weights)
    design=x*scale[:,None];target=y*scale
    # Intercept remains uniquely identified when nuisance variation vanishes;
    # a true intercept/nuisance confounding must not be hidden by a pseudoinverse.
    values,vectors=np.linalg.eigh(design.T@design);null=vectors[:,values<=max(1.,values.max())*1e-10]
    if null.size and np.any(np.abs(null[0])>1e-7):return dict(effect=None,writers=len(by_writer),pairs=len(usable),reason='paired contrast unidentified')
    beta=np.linalg.lstsq(design,target,rcond=1e-10)[0]
    return dict(effect=float(beta[0]),writers=len(by_writer),pairs=len(usable),covariate_coefficients=beta[1:].tolist())

def analyse(rows,cell='primary',draws=2000,permutations=200,callback=lambda *args:None):
    if cell not in CELLS:raise ValueError('Unknown S3 cell')
    observed=match(rows);keys={(r['session'],r['ordinal']) for pair in observed for r in pair}
    frame=[r for r in rows if (r['session'],r['ordinal']) in keys]
    point=fit(frame,cell);writers=sorted({r['writer'] for r in frame});rng=np.random.default_rng(SEED)
    if point['effect'] is None:return dict(status='below floor, descriptive',cell=cell,point=point,raw_events=len(rows),matched_events=len(frame))
    bootstrap=[]
    for i in range(draws):
        counts=dict(zip(writers,np.bincount(rng.integers(len(writers),size=len(writers)),minlength=len(writers))))
        result=fit(frame,cell,counts);bootstrap.append(result['effect']);callback('bootstrap',i+1,draws)
    by_session=defaultdict(list)
    for i,r in enumerate(frame):by_session[r['session']].append(i)
    reference=[]
    for i in range(permutations):
        changed=[dict(r) for r in frame]
        for ix in by_session.values():
            labels=rng.permutation([frame[j]['nonlocal_edit'] for j in ix])
            for j,label in zip(ix,labels):changed[j]['nonlocal_edit']=bool(label)
        reference.append(fit(changed,cell)['effect']);callback('permutation',i+1,permutations)
    invalid_boot=sum(v is None for v in bootstrap);invalid_ref=sum(v is None for v in reference)
    ci=None if invalid_boot else np.quantile(bootstrap,[.025,.975]).tolist()
    supported=point['pairs']>=300 and point['writers']>=25
    direction='invalid uncertainty' if ci is None else 'positive' if ci[0]>0 else 'negative' if ci[1]<0 else 'inconclusive'
    if not supported:direction='below floor, descriptive'
    if invalid_ref:direction='invalid permutation control; '+direction
    if cell!='primary':direction='descriptive companion; '+direction
    return dict(status='complete',cell=cell,point=point,interval=ci,support_gate=supported,direction=direction,raw_events=len(rows),matched_events=len(frame),draws=draws,
                reference=dict(draws=permutations,invalid_draws=invalid_ref,mean=None if invalid_ref else float(np.mean(reference)),
                    scope='Within-session labels in the outcome-blind matched frame, rematched and refitted; conditional diagnostic'),
                invalid_bootstrap_draws=invalid_boot,private_bootstrap=bootstrap,private_reference=reference)

def run(output,inputs,config,verification=False):
    cell=config.get('cell');draws=2000 if cell=='primary' else 200
    if config!=dict(card='BK-S3',cell=cell,draws=draws,permutations=200) or cell not in CELLS:raise ValueError('Frozen S3 configuration required')
    completion=Path(inputs['scored_completion']);path=completion.parent/'output/PRIVATE_SCORED.json.gz';completed(completion,path)
    rows=gzread(path);output=Path(output);output.mkdir(parents=True,exist_ok=True);start=time.process_time()
    def checkpoint(phase,done,total):
        if done%50==0:
            progress(output/'PROGRESS.json',dict(phase=('verify-' if verification else '')+phase,done=done,total=total))
            if (output/'YIELD_REQUEST.json').exists():raise InterruptedError('S3 complete draw boundary')
        if not verification and phase=='bootstrap' and done==max(1,draws//20):write_equal(output/'PILOT.json',dict(done=done,total=draws,cpu_seconds=time.process_time()-start))
    try:
        with threadpool_limits(limits=1):result=analyse(rows,cell,draws,200,checkpoint)
    except InterruptedError:return dict(status='yielded',reason='S3 draw boundary; new attempt restarts bounded inference')
    if verification:
        if result!=gzread(output/'PRIVATE_FULL_RESULT.json.gz'):raise ValueError('S3 complete numerical replay mismatch')
        return dict(verified=True,all_draws_recomputed=True)
    gzip_equal(output/'PRIVATE_FULL_RESULT.json.gz',result);write_equal(output/'SCIENCE.json',{k:v for k,v in result.items() if not k.startswith('private_')})
    return dict(status='complete')

def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
