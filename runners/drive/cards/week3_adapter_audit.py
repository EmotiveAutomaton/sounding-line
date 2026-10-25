"""WA1 canonical-label audit and conditional sensitivity of retained adapters.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-7. Equal losses cannot clear the
strict 0.01 margin; sufficiently large consistent improvements can. Calibration
uses only the original earlier partition. Every original cell/writer stays.
A legal true-choice mixture plants exactly the requested improvement in each
writer's mean half-Brier; an infeasible plant is unsupported, never clipped.
Power resamples complete writer clusters and applies BOTH original intervals
against ALL three rivals. This tests added improvement over retained forecasts,
not a universal total advantage or a retrained-preference mechanism. The exact
original crossed bootstrap gates writer weights on sampled prompt presence;
prompt multiplicity cancels within a writer's single evaluation prompt.
"""
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
import math

import numpy as np
from threadpoolctl import threadpool_limits

from . import week3_adapter_inputs as source
from .timing_census import read, filehash
from .timing_p6 import gzread, gzip_equal, write_equal, progress
from .timing_pmap_source import completed
from .timing_stats import bind, check_binding

CONFIG=dict(card='WA1',schema=1,mode='full',expected_cells=86,worlds=1000,
            bootstrap_draws=4000,seed=20261026,plants=[.01,.02,.03,.05],margin=.01)
CONSTRUCTED=dict(CONFIG,mode='constructed',expected_cells=2,worlds=32,bootstrap_draws=200)
RIVALS=('base','pooled','donor')
VARIANTS=('original_logged','canonical_fixed_temperature','canonical_recalibrated')


def loss(p,y):
    p=np.asarray(p,float)
    if p.ndim!=1 or len(p)<2 or not np.isfinite(p).all() or np.any(p<0) or abs(p.sum()-1)>1e-12:
        raise ValueError('invalid choice probability')
    if type(y) is not int or not 0<=y<len(p):raise ValueError('invalid choice label')
    return float(.5*np.sum((p-np.eye(1,len(p),y)[0])**2))


def plant(probabilities,truths,delta):
    """One mixture weight per writer, exact mean-loss improvement."""
    if len(probabilities)!=len(truths) or not probabilities or not math.isfinite(delta) or delta<0:
        raise ValueError('invalid plant population or size')
    before=np.array([loss(p,y) for p,y in zip(probabilities,truths)])
    mean=float(before.mean())
    if delta>mean:return None
    alpha=0. if delta==0 else 1-math.sqrt(1-delta/mean)
    after=[]
    for p,y in zip(probabilities,truths):
        q=(1-alpha)*np.asarray(p,float);q[y]+=alpha
        after.append(q.tolist())
    achieved=mean-np.mean([loss(p,y) for p,y in zip(after,truths)])
    if not np.isclose(achieved,delta,atol=5e-14,rtol=0):raise ValueError('plant does not achieve requested writer improvement')
    return dict(probabilities=after,alpha=alpha,mean_loss_before=mean,
                achieved_improvement=float(achieved),mean_loss_after=mean-delta)


@lru_cache(maxsize=32)
def writer_weights(n,draws):
    selected=np.random.default_rng(141010).integers(n,size=(draws,n))
    weights=np.zeros((draws,n),float)
    np.add.at(weights,(np.arange(draws)[:,None],selected),1.)
    return weights/n


@lru_cache(maxsize=64)
def crossed_bank(n,p,draws):
    rng=np.random.default_rng(141011);ww=np.empty((draws,n),float);pp=np.empty((draws,p),bool)
    for i in range(draws):
        ww[i]=rng.multinomial(n,np.ones(n)/n)
        pp[i]=rng.multinomial(p,np.ones(p)/p)>0
    return ww,pp


def distributions(differences,prompts,draws):
    """Rows are complete writer units; columns are any fixed contrasts."""
    differences=np.asarray(differences,float)
    if differences.ndim==1:differences=differences[:,None]
    n=len(differences)
    if n<2 or len(prompts)!=n or not np.isfinite(differences).all():raise ValueError('invalid writer contrast support')
    levels=sorted(set(prompts));pi=np.array([levels.index(p) for p in prompts])
    ww,pp=crossed_bank(n,len(levels),draws)
    weights=ww*pp[:,pi];total=weights.sum(1);keep=total>0
    if not keep.any():raise ValueError('all crossed bootstrap draws unsupported')
    weights=weights[keep]/total[keep,None]
    return writer_weights(n,draws)@differences,weights@differences


def intervals(differences,prompts,draws,margin=.01):
    x=np.asarray(differences,float)
    if len(x)<2:return dict(estimate=float(x.mean()) if len(x) else None,writer_interval=None,
        crossed_writer_prompt_interval=None,state='unsupported',reason='fewer than two writers',passes=False)
    writer,cross=distributions(x,prompts,draws)
    wi=np.quantile(writer[:,0],[.025,.975]).tolist();ci=np.quantile(cross[:,0],[.025,.975]).tolist()
    passing=wi[1]<-margin and ci[1]<-margin
    return dict(estimate=float(x.mean()),writer_interval=wi,crossed_writer_prompt_interval=ci,
        state='promising' if passing else 'exhausted_at_margin' if wi[0]>-margin else 'unresolved',
        passes=bool(passing),margin=margin,writer_draws=len(writer),crossed_draws=len(cross))


def calibrated(cell):
    writers=sorted(cell['writers'],key=lambda r:r['writer'])
    if len({w['writer'] for w in writers})!=len(writers):raise ValueError('duplicate original writer')
    rows=[];details=[]
    for w in writers:
        cal=w['cases']['calibration'];ev=w['cases']['evaluation']
        if not cal or not ev:raise ValueError('original partition empty')
        prompts={r['prompt'] for r in ev}
        if len(prompts)!=1:raise ValueError('single held-out prompt assumption failed; no population shrink permitted')
        if any(r['writer']!=w['writer'] for r in cal+ev):raise ValueError('case writer identity changed')
        if {r['key'] for r in cal}&{r['key'] for r in ev}:raise ValueError('calibration and evaluation overlap')
        canonical_cal=[dict(c,truth=c['canonical_truth']) for c in cal]
        temps={a:source.temperature(w['raw'][a]['calibration'],canonical_cal) for a in source.ARMS}
        old=w['old_temperatures'];by_variant={v:defaultdict(list) for v in VARIANTS};prob=[];truth=[]
        for i,c in enumerate(ev):
            oldp={a:source.normalized(w['raw'][a]['evaluation'][i],c['lengths'],old[a]) for a in source.ARMS}
            newp={a:source.normalized(w['raw'][a]['evaluation'][i],c['lengths'],temps[a]) for a in source.ARMS}
            for variant in VARIANTS:
                target=c['truth'] if variant=='original_logged' else c['canonical_truth']
                probabilities=newp if variant=='canonical_recalibrated' else oldp
                for a in source.ARMS:by_variant[variant][a].append(loss(probabilities[a],target))
                by_variant[variant]['uniform'].append(loss([1/len(c['lengths'])]*len(c['lengths']),target))
            prob.append(newp['own']);truth.append(c['canonical_truth'])
        rows.append(dict(writer=w['writer'],prompt=next(iter(prompts)),observations=len(ev),
            losses={v:{a:float(np.mean(values)) for a,values in arms.items()} for v,arms in by_variant.items()},
            own_probabilities=prob,truths=truth))
        details.append(dict(writer=w['writer'],old_temperatures=old,canonical_temperatures=temps,
            calibration_rows=len(cal),evaluation_rows=len(ev),
            changed_calibration=sum(c['truth']!=c['canonical_truth'] for c in cal),
            changed_evaluation=sum(c['truth']!=c['canonical_truth'] for c in ev)))
    return rows,details


def audited(cell,rows,details,config):
    prompts=[r['prompt'] for r in rows];variants={}
    for variant in VARIANTS:
        contrast={}
        for left,right in [('own',r) for r in RIVALS]+[('base','uniform')]:
            d=[r['losses'][variant][left]-r['losses'][variant][right] for r in rows]
            contrast[left+'_minus_'+right]=intervals(d,prompts,config['bootstrap_draws'],config['margin'])
        variants[variant]=dict(equal_writer_loss={a:float(np.mean([r['losses'][variant][a] for r in rows]))
            for a in (*source.ARMS,'uniform')},contrasts=contrast,
            useful_against_all_three=all(contrast['own_minus_'+r]['passes'] for r in RIVALS))
    return dict(cell=cell['cell'],backbone=cell.get('backbone'),producer=cell.get('producer'),
        corpus=cell.get('corpus'),rank=cell.get('rank'),seed=cell.get('seed'),writers=len(rows),
        prompts=len(set(prompts)),evaluation_rows=sum(r['observations'] for r in rows),
        calibration_rows=sum(r['calibration_rows'] for r in details),
        changed_calibration=sum(r['changed_calibration'] for r in details),
        changed_evaluation=sum(r['changed_evaluation'] for r in details),variants=variants)


def wilson(successes,total):
    z=1.959963984540054;rate=successes/total;den=1+z*z/total
    center=(rate+z*z/(2*total))/den
    half=z*math.sqrt(rate*(1-rate)/total+z*z/(4*total*total))/den
    return [max(0.,center-half),min(1.,center+half)]


def power_group(group,config,checkpoint=lambda *args:None):
    """Shared resampling for cells with IDENTICAL writer/prompt populations."""
    rows=group[0][1];n=len(rows);worlds=config['worlds'];sizes=config['plants']
    template=tuple((r['writer'],r['prompt']) for r in rows)
    if any(tuple((r['writer'],r['prompt']) for r in rr)!=template for _,rr in group):
        raise ValueError('power grouping changed original roster')
    outcomes={};valid={};counts={name:np.zeros(len(sizes),int) for name,_ in group}
    rival_counts={name:np.zeros((len(sizes),3),int) for name,_ in group}
    baseline=np.stack([[[r['losses']['canonical_recalibrated']['own']-r['losses']['canonical_recalibrated'][a]
                        for a in RIVALS] for r in rr] for _,rr in group],axis=1)
    for name,rr in group:
        cells=[];valid[name]=[]
        for delta in sizes:
            plants=[plant(r['own_probabilities'],r['truths'],delta) for r in rr]
            feasible=all(p is not None for p in plants) and n>=2;valid[name].append(feasible)
            base=dict(added_writer_improvement=delta,supported=feasible,
                unsupported_writers=sum(p is None for p in plants))
            if feasible:
                base.update(alpha_range=[min(p['alpha'] for p in plants),max(p['alpha'] for p in plants)],
                    achieved_improvement_range=[min(p['achieved_improvement'] for p in plants),max(p['achieved_improvement'] for p in plants)],
                    actual_post_plant_advantage={a:dict(equal_writer_mean=float(np.mean([
                        r['losses']['canonical_recalibrated'][a]-r['losses']['canonical_recalibrated']['own']+delta for r in rr])),
                        writer_range=[float(fn([r['losses']['canonical_recalibrated'][a]-r['losses']['canonical_recalibrated']['own']+delta for r in rr])) for fn in (min,max)]) for a in RIVALS})
            else:base['reason']='requested writer loss improvement infeasible or fewer than two independent writers'
            cells.append(base)
        outcomes[name]=cells
    if n>=2:
        rng=np.random.default_rng(config['seed']);prompts=np.array([r['prompt'] for r in rows])
        for world in range(worlds):
            selected=rng.integers(n,size=n)
            d=baseline[selected].reshape(n,-1)
            w,c=distributions(d,prompts[selected].tolist(),config['bootstrap_draws'])
            upper=np.maximum(np.quantile(w,.975,axis=0),np.quantile(c,.975,axis=0)).reshape(len(group),3)
            for j,(name,_) in enumerate(group):
                for k,delta in enumerate(sizes):
                    if valid[name][k]:
                        passed=upper[j]-delta < -config['margin']
                        rival_counts[name][k]+=passed;counts[name][k]+=int(passed.all())
            if (world+1)%10==0 or world+1==worlds:checkpoint('worlds',world+1,worlds)
    result={}
    for name,_ in group:
        values=outcomes[name]
        for k,row in enumerate(values):
            if row['supported']:
                hits=int(counts[name][k]);row.update(worlds=worlds,detected=hits,recovery_rate=hits/worlds,
                    monte_carlo_interval=wilson(hits,worlds),
                    detected_against_each_rival={a:int(rival_counts[name][k,j]) for j,a in enumerate(RIVALS)})
        passed=[r['added_writer_improvement'] for r in values if r['supported'] and r['recovery_rate']>=.8]
        mda=min(passed) if passed else None
        all_supported=all(r['supported'] for r in values)
        result[name]=dict(grid=values,minimum_detectable_added_improvement=mda,
            minimum_detectable_label=str(mda) if mda is not None else 'more than 0.05' if all_supported else 'unsupported',
            route='within_twice_margin_conditional_on_retained_forecasts' if mda is not None and mda<=.02 else
                  'underpowered_at_useful_added_improvement' if all_supported or mda is not None else 'unsupported_requested_plant',
            total_advantage_exclusion_licensed=False,retrained_preference_test='deferred; GPU required')
    return result


def analyze(cells,config,checkpoint=lambda *args:None):
    if len(cells)!=config['expected_cells'] or len({c['cell'] for c in cells})!=len(cells):raise ValueError('fixed complete cell roster changed')
    summaries={};details={};groups=defaultdict(list)
    for i,cell in enumerate(sorted(cells,key=lambda c:c['cell'])):
        rows,calibration=calibrated(cell)
        summaries[cell['cell']]=audited(cell,rows,calibration,config)
        details[cell['cell']]=dict(calibration=calibration,writer_losses=[{k:v for k,v in r.items() if k not in ('own_probabilities','truths')} for r in rows])
        groups[tuple((r['writer'],r['prompt']) for r in rows)].append((cell['cell'],rows))
        checkpoint('canonical_cells',i+1,len(cells))
    for i,group in enumerate(groups.values()):
        results=power_group(group,config,lambda phase,done,total:checkpoint(f'group_{i+1}_of_{len(groups)}_'+phase,done,total))
        for name,result in results.items():summaries[name]['power']=result
    return dict(card='WA1',cells=[summaries[n] for n in sorted(summaries)],original_cells=len(cells),
        population_groups=len(groups),worlds=config['worlds'],bootstrap_draws=config['bootstrap_draws'],
        interpretation='Conditional instrument audit of retained forecasts; plants add equal writer mean improvement over each existing personal model, not a common total advantage over every rival.',
        uncertainty='Original writer bootstrap seed141010 and crossed writer/prompt seed141011, both95%percentile, all3rival upperbounds strictly below-0.01; fixedtraining/donors.',
        power_worlds='Complete writer clusters resampled at original writer count; repeated writer copies are distinct synthetic units; seed20261026 common random indices within same original population. Prompt support rebuilt per world.',
        no_gpu=True,no_new_model_inference=True,no_independent_confirmation=True,
        total_advantage_exclusion_licensed=False),details


def load(inputs,config):
    if config['mode']=='constructed':
        if set(inputs)!={'fixture'}:raise ValueError('fixed constructed source required')
        return read(inputs['fixture'])
    if set(inputs)!={'source_completion'}:raise ValueError('completed source required')
    c=Path(inputs['source_completion']);output=c.parent/'output'
    for name in ('LIKELIHOODS.json.gz','SOURCE_BINDINGS.json','SUMMARY.json'):completed(c,output/name)
    binding=read(output/'SOURCE_BINDINGS.json')
    if binding['config']!=source.CONFIG:raise ValueError('full authenticated source configuration required')
    if any(filehash(p)!=expected for p,expected in binding['pins'].items()):raise ValueError('original source changed')
    return gzread(output/'LIKELIHOODS.json.gz')


def run(output,inputs,config,verification=False):
    if config not in (CONFIG,CONSTRUCTED):raise ValueError('fixed WA1 configuration required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    if verification:check_binding(output,inputs,config)
    cells=load(inputs,config)
    def tick(phase,done,total):
        if (output.parent/'STOP').exists() or (output/'YIELD_REQUEST.json').exists():raise InterruptedError('WA1 stop requested')
        progress(output/'PROGRESS.json',dict(phase=('verify_' if verification else '')+phase,done=done,total=total))
    with threadpool_limits(limits=1):summary,detail=analyze(cells,config,tick)
    if verification:
        if read(output/'SUMMARY.json')!=summary or gzread(output/'DETAILS.json.gz')!=detail:raise ValueError('fresh complete WA1 analysis differs')
        return dict(verified=True,all_cells_replayed=True)
    write_equal(output/'SUMMARY.json',summary);gzip_equal(output/'DETAILS.json.gz',detail)
    bind(output,inputs,config,['SUMMARY.json','DETAILS.json.gz'])
    return dict(status='complete',cells=len(cells))


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
