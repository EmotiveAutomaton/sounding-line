"""S2 controlled within-writer revision risk difference and full controls.

DESIGN CHECK: sentence provenance and timing fixed before the outcome; whole
writers in every bootstrap; within-session labels in every permutation. The
within coefficient of a correlated random-intercept linear probability model
is computed from exact within-writer sufficient statistics, with an explicit
random-intercept likelihood fit and independent dense GLS fixture.
"""
from collections import Counter,defaultdict
from pathlib import Path
import math,time
import numpy as np
from scipy.linalg import qr
from scipy.optimize import minimize_scalar
from threadpoolctl import threadpool_limits
from .timing_census import read,filehash
from .timing_p6 import gzread,write_equal,gzip_equal,progress
from .timing_pmap_source import completed

SEED=20261102
CONTROL_NAMES=('sentence_length','mean_word_length','population_log_frequency','own_prior_log_frequency',
               'bigram_log_seconds','paragraph_boundary','sentence_boundary','time_on_task_minutes','session_order',
               'distance_sentences','remaining_minutes','creative')
CELLS=('primary','paragraph','within_two_minutes','later_than_two_minutes','argumentative','creative','currently_typed_companion')

def select(sessions,cell='primary'):
    rows=[];counts=Counter();events=set()
    for s in sessions:
        if cell in ('argumentative','creative') and s['genre']!=cell:continue
        for r in s['sentences']:
            if r['timing_state']!='eligible':counts['excluded_'+r['timing_state']]+=1;continue
            if r.get('class') not in ('flow','hesitant'):counts['middle_third']+=1;continue
            if cell in ('within_two_minutes','later_than_two_minutes') and r['remaining_seconds']<120:counts['less_than_two_minutes_followup']+=1;continue
            future=r['later_revisions']
            if cell=='paragraph':future=[v for v in future if v['paragraph_nonlocal']]
            elif cell=='within_two_minutes':future=[v for v in future if v['lag_seconds']<=120]
            elif cell=='later_than_two_minutes':future=[v for v in future if v['lag_seconds']>120]
            elif cell=='currently_typed_companion':future=[v for v in future if v['current_target_fully_typed']]
            controls=dict(r['controls'],creative=int(s['genre']=='creative'))
            if set(controls)!=set(CONTROL_NAMES) or not all(math.isfinite(v) for v in controls.values()):raise ValueError('S2 controls missing or nonfinite')
            rows.append(dict(writer=s['writer'],session=s['session'],flow=int(r['class']=='flow'),outcome=int(bool(future)),
                             controls=controls,events=[(s['session'],v['ordinal']) for v in future]))
            counts['intervening_nonuser_edit']+=int(r['intervening_nonuser_edit'])
    supported={w for w in {r['writer'] for r in rows} if len({r['flow'] for r in rows if r['writer']==w})==2}
    kept=[r for r in rows if r['writer'] in supported];counts['without_both_arms']=len(rows)-len(kept)
    for r in kept:events.update(r['events'])
    counts.update(rows=len(kept),writers=len(supported),distinct_nonlocal_events=len(events),revised_sentences=sum(r['outcome'] for r in kept))
    return kept,dict(counts)

def arrays(rows):
    writers=sorted({r['writer'] for r in rows});lookup={w:i for i,w in enumerate(writers)}
    x=np.array([[r['flow']]+[r['controls'][k] for k in CONTROL_NAMES] for r in rows],float)
    y=np.array([r['outcome'] for r in rows],float);g=np.array([lookup[r['writer']] for r in rows])
    if not len(rows):return None
    means=np.array([x[g==i].mean(0) for i in range(len(writers))]);ym=np.array([y[g==i].mean() for i in range(len(writers))])
    xc=x-means[g];yc=y-ym[g];scale=np.std(xc,axis=0);nonzero=np.flatnonzero(scale>1e-12)
    if 0 not in nonzero:raise ValueError('No within-writer flow variation')
    # Keep flow first and remove nuisance columns linearly dependent on it.
    keep=[0];rank=1
    for j in nonzero:
        if j==0:continue
        proposal=xc[:,keep+[j]]/scale[keep+[j]]
        new=np.linalg.matrix_rank(proposal,tol=1e-9)
        if new>rank:keep.append(int(j));rank=new
    z=xc[:,keep]/scale[keep]
    stats=[dict(xx=z[g==i].T@z[g==i],xy=z[g==i].T@yc[g==i]) for i in range(len(writers))]
    return dict(x=x,y=y,g=g,xc=xc,yc=yc,z=z,means=means,ym=ym,scale=scale[keep],keep=keep,stats=stats,writers=writers)

def coefficient(bundle,indices=None):
    ss=bundle['stats'];indices=range(len(ss)) if indices is None else indices
    xx=sum((ss[int(i)]['xx'] for i in indices),start=np.zeros_like(ss[0]['xx']))
    xy=sum((ss[int(i)]['xy'] for i in indices),start=np.zeros_like(ss[0]['xy']))
    eigenvalues,vectors=np.linalg.eigh(xx);null=vectors[:,eigenvalues<=max(1.,eigenvalues.max())*1e-10]
    if null.size and np.any(np.abs(null[0])>1e-7):raise ValueError('Resample flow contrast unidentified; cannot discard this draw')
    beta=np.linalg.lstsq(xx,xy,rcond=1e-10)[0] if null.size else np.linalg.solve(xx,xy)
    return float(beta[0]/bundle['scale'][0])

def random_intercept_fit(bundle):
    # Mundlak writer means permit correlation between a person's predictors and
    # intercept. Within columns sum exactly to zero, so their GLS coefficients
    # are algebraically independent of the random-intercept variance ratio.
    x=bundle['x'];g=bundle['g'];y=bundle['y'];w=len(bundle['writers'])
    between=np.column_stack([np.ones(len(x)),bundle['means'][g]])
    _,r,piv=qr(between,mode='economic',pivoting=True);rank=int(np.sum(np.abs(np.diag(r))>1e-9))
    design=np.column_stack([bundle['z'],between[:,sorted(piv[:rank])]])
    n,p=design.shape;groups=[np.flatnonzero(g==i) for i in range(w)]
    xx=design.T@design;xy=design.T@y;yy=y@y
    sums=[(len(ii),design[ii].sum(0),y[ii].sum()) for ii in groups]
    def at(ratio,details=False):
        a=xx.copy();b=xy.copy();c=float(yy);logv=0.
        for size,sx,sy in sums:
            f=ratio/(1+ratio*size);a-=f*np.outer(sx,sx);b-=f*sx*sy;c-=f*sy*sy;logv+=math.log1p(ratio*size)
        sign,logdet=np.linalg.slogdet(a)
        if sign<=0:return math.inf
        beta=np.linalg.solve(a,b);rss=c-b@beta
        if rss<=0:return math.inf
        objective=(n-p)*math.log(rss/(n-p))+logv+logdet
        return (objective,beta,rss/(n-p)) if details else objective
    opt=minimize_scalar(lambda value:at(math.exp(value)),bounds=(-15,15),method='bounded',options={'xatol':1e-7})
    if not opt.success:raise ValueError('Random-intercept likelihood did not converge')
    ratio=0. if at(0)<=opt.fun else math.exp(opt.x)
    objective,beta,variance=at(ratio,True);effect=float(beta[0]/bundle['scale'][0])
    if abs(effect-coefficient(bundle))>1e-8:raise ValueError('Within/random-intercept effect disagreement')
    return dict(effect=effect,writer_variance_ratio=ratio,residual_variance=variance,reml_objective=objective,
                fixed_columns=design.shape[1],nuisance_columns_dropped=[CONTROL_NAMES[j-1] for j in range(1,len(CONTROL_NAMES)+1) if j not in bundle['keep']],
                model='correlated writer random-intercept linear probability model; writer means and within-centered predictors',
                _design=design)

def analyse(sessions,cell='primary',draws=2000,permutations=200,callback=lambda *args:None):
    rows,counts=select(sessions,cell)
    if counts['writers']<2 or not rows:return dict(status='unsupported',card='BK-S2',cell=cell,counts=counts)
    bundle=arrays(rows);point=random_intercept_fit(bundle);point.pop('_design');rng=np.random.default_rng(SEED);boot=[]
    for i in range(draws):
        boot.append(coefficient(bundle,rng.integers(0,len(bundle['writers']),len(bundle['writers']))));callback('bootstrap',i+1,draws)
    sessions_ix=defaultdict(list)
    for i,row in enumerate(rows):sessions_ix[row['session']].append(i)
    reference=[]
    for i in range(permutations):
        labels=np.array([r['flow'] for r in rows]);permuted=[dict(r) for r in rows]
        for ix in sessions_ix.values():labels[ix]=rng.permutation(labels[ix])
        for j,value in enumerate(labels):permuted[j]['flow']=int(value)
        reference.append(coefficient(arrays(permuted)));callback('permutation',i+1,permutations)
    ci=np.quantile(boot,[.025,.975]).tolist();supported=counts['distinct_nonlocal_events']>=300 and counts['writers']>=25
    state='positive' if ci[0]>0 else 'negative' if ci[1]<0 else 'inconclusive'
    if not supported:state='unsupported; ScholaWrite fallback queued'
    if cell!='primary':state='descriptive texture; '+state
    return dict(status='complete',card='BK-S2',cell=cell,counts=counts,primary=point,interval=ci,draws=draws,
                direction=state,support_gate=supported,reference=dict(draws=permutations,mean=float(np.mean(reference)),interval=np.quantile(reference,[.025,.975]).tolist(),
                scope='within-session label permutation diagnostic, not proof of randomized exchangeability'),
                uncertainty='whole-writer bootstrap, exact within-writer random-intercept coefficient; no failed draws discarded',
                private_bootstrap=boot,private_reference=reference)

def run(output,inputs,config,verification=False):
    if config.get('cell','primary') not in CELLS:raise ValueError('Unknown S2 cell')
    cell=config.get('cell','primary');draws=2000 if cell=='primary' else 200
    mode=config.get('mode','corpus')
    if mode not in ('corpus','constructed') or config!=dict(card='BK-S2',cell=cell,draws=draws,permutations=200,mode=mode):raise ValueError('Frozen S2 analysis configuration required')
    completion=Path(inputs['source_completion']);path=completion.parent/'output'/'PRIVATE_SENTENCES.json.gz';completed(completion,path)
    summary=completion.parent/'output'/'SUMMARY.json';completed(completion,summary)
    if bool(read(summary).get('constructed'))!=(mode=='constructed'):raise ValueError('S2 constructed/corpus source mismatch')
    data=gzread(path);output=Path(output);started=time.process_time()
    def checkpoint(phase,done,total):
        if done%100==0:progress(output/'PROGRESS.json',dict(phase=('verify-' if verification else '')+phase,done=done,total=total))
        if not verification and phase=='bootstrap' and done==max(1,draws//20):write_equal(output/'PILOT.json',dict(draws=done,total=draws,cpu_seconds=time.process_time()-started,forecast_cpu_seconds=(time.process_time()-started)*draws/done))
        if done%100==0 and (output/'YIELD_REQUEST.json').exists():raise InterruptedError('S2 owner request at complete draw boundary')
    try:
        with threadpool_limits(limits=1):result=analyse(data,cell,draws,200,checkpoint)
    except InterruptedError:
        write_equal(output/('VERIFY_CHECKPOINT.json' if verification else 'CHECKPOINT.json'),dict(restart_from_authenticated_input_required=True))
        return dict(status='yielded',reason='S2 owner request; new attempt restarts the bounded inference unit')
    result['constructed']=mode=='constructed'
    if verification:
        if result!=gzread(output/'PRIVATE_FULL_RESULT.json.gz'):raise ValueError('Complete S2 inference replay differs')
        return dict(verified=True,all_bootstrap_and_permutations_recomputed=True)
    gzip_equal(output/'PRIVATE_FULL_RESULT.json.gz',result)
    write_equal(output/'SCIENCE.json',{k:v for k,v in result.items() if not k.startswith('private_')})
    return dict(status='complete',card='BK-S2')

def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
