"""S4.k actual-device contrast, distance matching and declared fallback.

DESIGN CHECK: LESSONS 3/5; BK_S4K.md. Identical rates give exact zero;
signed known answers retain direction. Within-writer, within-distance label
permutations preserve arm support. Below-floor pooled results remain descriptive.
"""
from pathlib import Path
import time
import numpy as np
from .week4_cursor_stats import arrays, writer_effects
from .states_v2 import contrast_state
from .week5_bk_klicke_intake import read,write,digest
from .timing_pmap_source import completed
from .timing_p6 import progress

SEED=20261102


def pooled(sessions):
    counts={b:np.zeros((2,2),dtype=int) for b in ('1','2','3-5','>5')}
    for session in sessions:
        for row in session['landings']:
            counts[row['bin']][int(row['kind']=='click'),int(row['edit_near'])]+=1
    numerator=0.;denominator=0;bins={}
    for b,table in counts.items():
        ns,nj=table.sum(axis=1);ss,sj=table[:,1]
        delta=None if not ns or not nj else float((sj*ns-ss*nj)/(nj*ns))
        weight=min(ns,nj)
        if delta is not None: numerator+=weight*delta;denominator+=weight
        bins[b]=dict(arrow=int(ns),click=int(nj),arrow_edits=int(ss),click_edits=int(sj),difference=delta)
    return dict(estimate=numerator/denominator if denominator else None,bins=bins,shared_bin_weight=int(denominator))


def analyze(sessions,draws=2000,permutations=200,callback=lambda *args:None):
    adapted=[{**s,'landings':[{**r,'kind':'jump' if r['kind']=='click' else 'step'} for r in s['landings']]} for s in sessions]
    a=arrays(adapted);effects,supported,support=writer_effects(a);n=int(supported.sum())
    pooled_result=pooled(sessions)
    coverage=dict(writers=len(sessions),writers_with_landings=len(a['writers']),supported_writers=n,required_writers=20,landings=a['rows'])
    point=float(np.mean(effects[supported])) if n else None
    summary=dict(coverage=coverage,within_writer_estimate=point,pooled_descriptive=pooled_result,seed=SEED,
                 scope='Within-writer, landing-distance-standardized logged click minus arrow association; no inferred intention or physical hand state.')
    private=dict(writers=a['writers'],effects=effects.tolist(),support=support,supported=supported.tolist())
    if n<20:
        summary.update(state='below floor, descriptive',estimate=pooled_result['estimate'],interval=None,
                       control_status='not applicable to population claim below floor',draws=0,permutations=0)
        return summary,private
    values=effects[supported];boot=[];rng=np.random.default_rng(SEED)
    for i in range(draws):
        boot.append(float(np.mean(values[rng.integers(0,n,size=n)])));callback('bootstrap',i+1,draws)
    interval=np.quantile(boot,[.025,.975]);reference=[];rng=np.random.default_rng(SEED+1)
    for i in range(permutations):
        labels=a['group'].copy()
        for indexes in a['strata']: labels[indexes]=rng.permutation(labels[indexes])
        shuffled,eligible,_=writer_effects(a,labels)
        if not np.array_equal(eligible,supported): raise ValueError('Reference changed support')
        reference.append(float(np.mean(shuffled[supported])));callback('permutation',i+1,permutations)
    ref=np.quantile(reference,[.025,.975]);biased=bool(ref[0]>0 or ref[1]<0)
    # Equal floating-point values need not have exactly zero np.var because
    # the rounded mean can differ from each identical value.
    degenerate=bool(np.ptp(values)==0 and point!=0)
    summary.update(state=contrast_state(point,*interval),estimate=point,interval=interval.tolist(),
                   control_status='biased reference' if biased else 'degenerate cluster uncertainty' if degenerate else 'passes',
                   draws=draws,permutations=permutations,
                   reference=dict(interval=ref.tolist(),mean=float(np.mean(reference)),biased=biased,
                       positive_probability=(1+sum(x>=point for x in reference))/(1+len(reference)),
                       two_sided_probability=(1+sum(abs(x)>=abs(point) for x in reference))/(1+len(reference))),
                   inference_eligible=not (biased or degenerate))
    private.update(bootstrap=boot,reference=reference)
    return summary,private


def load(inputs,window,mode):
    if set(inputs)!={'source_complete'}: raise ValueError('Exact navigation source required')
    c=Path(inputs['source_complete']).resolve();root=c.parent;out=root/'output'
    completed(c,root/'PLAN.json');completed(c,root/'VERIFIED.json');completed(c,out/'INDEX.json');completed(c,out/'SUMMARY.json')
    plan=read(root/'PLAN.json')
    if plan['module']!='runners.drive.cards.week5_bk_s4k_source' or plan['config']['mode']!=mode:
        raise ValueError('Navigation source scope mismatch')
    if read(root/'VERIFIED.json').get('complete_source_replay') is not True: raise ValueError('Whole navigation replay required')
    summary=read(out/'SUMMARY.json');index=read(out/'INDEX.json')
    if summary['collection_status']!='passes' or not summary['complete_population'] or len(index)!=summary['sessions']:
        raise ValueError('Navigation collection gate failed')
    sessions=[]
    for row in index:
        path=(out/row['path']).resolve();path.relative_to(out)
        completed(c,path)
        if digest(path)!=row['sha256']: raise ValueError('Source index hash mismatch')
        data=read(path)
        if data['session']!=row['session']: raise ValueError('Navigation identity mismatch')
        if data['status']=='reconstructed': sessions.append(data['windows'][str(window)])
    return sessions,summary


def run(output,inputs,config,verification=False):
    if set(config)!={'card','mode','window','draws','permutations'} or config['card']!='BK-S4.k' or config['mode'] not in ('constructed','corpus') or config['window'] not in (30,60) or config['permutations']!=200 or config['draws']!=(2000 if config['window']==30 else 200):
        raise ValueError('Frozen device comparison config required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True);sessions,census=load(inputs,config['window'],config['mode']);start=time.process_time()
    def checkpoint(phase,done,total):
        if done%50==0:
            progress(output/'PROGRESS.json',dict(phase=('verify-' if verification else '')+phase,done=done,total=total,cpu_seconds=time.process_time()-start))
            if (output/'YIELD_REQUEST.json').exists(): raise InterruptedError('Whole inference restart unit')
    try: summary,private=analyze(sessions,config['draws'],200,checkpoint)
    except InterruptedError: return dict(status='yielded',reason='bounded_inference_restart_boundary')
    summary.update(window_seconds=config['window'],texture_descriptive=config['window']==60,source_counts=census['counts'])
    values={'SUMMARY.json':summary,'PRIVATE_INFERENCE.json.gz':private,'BINDING.json':dict(config=config,source_sha256=digest(inputs['source_complete']))}
    for name,value in values.items():
        if verification:
            if read(output/name)!=value: raise ValueError('Fresh full numerical replay mismatch')
        else: write(output/name,value)
    return dict(verified=True,full_numerical_replay=True) if verification else dict(status='complete')


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
