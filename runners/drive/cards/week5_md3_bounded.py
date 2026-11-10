"""Bounded exact MD3 primary, dynamic-null and complete companion consumers.

DESIGN CHECK: LESSONS 2?5, CONTROLS 6?7. Partial fits have no scientific
completion; sealed draws and null trajectories resume under the same inputs.
Both yielded execute and yielded verification remain operational pauses.
"""
from pathlib import Path
import hashlib,json,os,time
import numpy as np
from scipy.special import expit
from . import week5_md as core
from . import week5_md as md
from . import week5_md_analysis as primary
from .week5_md_analysis import load_verified,dynamic_features,logistic_fixed,null_trajectory
from .week5_md3 import repeat_roster
from .week5_md12_bounded import clock_state,wants_yield,YieldRequested,atomic_replace
CLOCK=None

def check_yield(details):
    if CLOCK is not None and wants_yield(CLOCK):raise YieldRequested({'status':'yielded','reason':'bounded MD3 checkpoint',**details})

def first_play(output,inputs,config):
    output.mkdir(parents=True,exist_ok=True)
    data=load_verified(inputs['task']);p=data['first'];source_n=len(p)
    if config.get('participants'):
        order=np.random.default_rng(md.SEED).permutation(len(p));p=p[np.sort(order[:int(config['participants'])])]
    upstream=json.loads(Path(inputs['md12_result']).read_text('utf8'))
    gamma=float(upstream['pooled']['gamma'])
    raw=dynamic_features(p,gamma);scale=raw.reshape(-1,8).std(axis=0,ddof=1).clip(1e-10)
    # Both standing slopes use one common SD, required for their difference.
    scale[3:5]=np.std(raw[:,:,3]+raw[:,:,4],ddof=1)
    if scale[3]<=0:raise ValueError('standing has no variation')
    x=raw/scale;y=p[:,:,6];fit=logistic_fixed(x,y)
    state=raw[:,:,3]+raw[:,:,4];both=(state.min(axis=1)<0)&(state.max(axis=1)>0)
    rescue=(state<0)&(state+p[:,:,3]>=0)&(state+p[:,:,2]<0)
    null_slopes=[]
    null_binding=hashlib.sha256(np.ascontiguousarray(p).tobytes()+str(gamma).encode()+md.sha(Path(__file__)).encode()).hexdigest()
    null_path=output/"NULL_CHECKPOINT.json"
    if null_path.exists():
        old=json.loads(null_path.read_text("utf8"))
        if old["binding"]!=null_binding:raise ValueError("null checkpoint mismatch")
        null_slopes=old["values"]
    for i in range(len(null_slopes),20):
        check_yield({"phase":"dynamic_nulls","completed":i,"total":20})
        simulated=null_trajectory(p,gamma,fit,scale,np.random.SeedSequence([md.SEED,i,33]))
        z=dynamic_features(simulated,gamma)/scale;nf=logistic_fixed(z,simulated[:,:,6])
        null_slopes.append(float(nf['beta'][3]))
        md.save_json(null_path,{'binding':null_binding,'values':null_slopes})
        md.save_json(output/'PROGRESS.json',{'phase':'dynamic_nulls','completed':i+1,'total':20})
    nulls=np.asarray(null_slopes);bar=max(.01,2*float(np.mean(np.abs(nulls)))+3*float(np.std(nulls,ddof=1)))
    draws=int(config.get('draws',2000));bootstrap=[]
    binding=hashlib.sha256(np.ascontiguousarray(p).tobytes()+md.sha(Path(__file__)).encode()).hexdigest();checkpoint=output/'standing_bootstrap.npz'
    if checkpoint.exists():
        if md.sha(checkpoint)!=json.loads(checkpoint.with_suffix('.sha256.json').read_text('utf8'))['sha256']:raise ValueError('primary checkpoint seal differs')
        with np.load(checkpoint) as b:
            if str(b['binding'])!=binding or int(b['draws'])!=draws or float(b['gamma'])!=gamma:raise ValueError('MD3 checkpoint mismatch')
            bootstrap=b['values'].tolist()
    start_draw=len(bootstrap)
    for i in range(len(bootstrap),draws):
        check_yield({"phase":"primary_bootstrap","completed":i,"total":draws})
        rng=np.random.default_rng(np.random.SeedSequence([md.SEED,i,34]));w=np.bincount(rng.integers(0,len(p),len(p)),minlength=len(p))
        b=logistic_fixed(x,y,w)['beta'];bootstrap.append([float(b[3]),float(b[4]),float(b[3]-b[4])])
        yielding=wants_yield(CLOCK) or i+1-start_draw>=CLOCK['max_new_draws']
        if (i+1)%10==0 or i+1==draws or yielding:
            temp=output/'standing_bootstrap.tmp.npz';np.savez_compressed(temp,values=np.array(bootstrap),binding=binding,draws=draws,gamma=gamma);atomic_replace(temp,checkpoint);md.save_json(checkpoint.with_suffix('.sha256.json'),{'sha256':md.sha(checkpoint)})
            md.save_json(output/'PROGRESS.json',{'phase':'participant_bootstrap','completed':i+1,'total':draws})
        if yielding and i+1<draws:raise YieldRequested({'status':'yielded','phase':'primary_bootstrap','completed':i+1,'total':draws})
    intervals=np.quantile(bootstrap,[.025,.975],axis=0).T.tolist();lower=float(fit['beta'][3]);upper=float(fit['beta'][4])
    lo,hi=intervals[0];outcome='supports' if lo>bar else 'against' if hi<-bar else 'inconclusive'
    if both.sum()<10000 or rescue.sum()<10000:outcome='below floor, descriptive'
    result={'card':'MD3','source_first_plays':source_n,'analysed_first_plays':len(p),'informative_participants':int(fit['informative'].sum()),
            'both_sides_participants':int(both.sum()),'rescue_choices':int(rescue.sum()),'gamma':gamma,
            'standing_sd':float(scale[3]),'slopes':[lower,upper],'contrast_lower_minus_upper':lower-upper,
            'intervals_lower_upper_contrast':intervals,'bar':bar,'dynamic_null_slopes':null_slopes,'outcome':outcome,
            'complete_card':False,'remaining':['repeat-play best-earlier-score comparison','rescue-subset companion','independent replay'],
            'scope':'descriptive game score; not direct security; constructed fair-gamble nulls'}
    md.save_json(output/'RESULT.json',result);return result

def grouped_logit(x,y,person,weights=None,max_iter=150,tolerance=1e-6):
    x=np.asarray(x,float);y=np.asarray(y,float);keys,code=np.unique(person,return_inverse=True)
    counts=np.bincount(code);positives=np.bincount(code,weights=y)
    weight=np.ones(len(keys)) if weights is None else np.asarray(weights,float)
    valid=(positives>0)&(positives<counts)&(weight>0)
    keep=valid[code]
    if valid.sum()<2:return {'status':'unsupported','informative_participants':int(valid.sum())}
    remap=np.cumsum(valid)-1;g=remap[code[keep]];xx=x[keep];yy=y[keep];ww=weight[valid];row_weight=ww[g]
    alpha=np.log((positives[valid]+.5)/(counts[valid]-positives[valid]+.5));beta=np.zeros(x.shape[1]);objective=np.inf
    n=len(alpha)
    for iteration in range(max_iter):
        check_yield({"phase":"grouped_likelihood","iteration":iteration})
        eta=alpha[g]+xx@beta;prob=expit(eta);variance=(prob*(1-prob)).clip(1e-9);working=eta+(yy-prob)/variance
        den=np.bincount(g,weights=variance,minlength=n)
        xm=np.column_stack([np.bincount(g,weights=variance*xx[:,j],minlength=n) for j in range(xx.shape[1])])/den[:,None]
        zm=np.bincount(g,weights=variance*working,minlength=n)/den
        centered=xx-xm[g];zc=working-zm[g];v=variance*row_weight
        gram=(centered*v[:,None]).T@centered;rhs=centered.T@(v*zc)
        if np.linalg.matrix_rank(gram,tol=1e-8)<xx.shape[1]:return {'status':'rank_deficient','informative_participants':int(valid.sum())}
        newbeta=np.linalg.solve(gram,rhs);newalpha=zm-xm@newbeta;step=1.
        while step>1e-8:
            b=beta+step*(newbeta-beta);a=alpha+step*(newalpha-alpha);linear=a[g]+xx@b
            loss=float(row_weight@(np.logaddexp(0,linear)-yy*linear))
            if loss<=objective+1e-8:break
            step*=.5
        beta,alpha,objective=b,a,loss;residual=yy-expit(linear)
        gradient=xx.T@(row_weight*residual)/ww.sum();ag=np.bincount(g,weights=residual,minlength=n)
        if max(np.max(np.abs(gradient)),np.max(np.abs(ag)))<tolerance:
            return {'status':'ok','beta':beta,'informative_participants':int(valid.sum()),'gradient':float(np.max(np.abs(gradient))),'iterations':iteration+1}
    raise ValueError('grouped fixed-intercept likelihood failed convergence')

def bootstrap_panel(x,y,person,columns,output,draws,seed_offset):
    xx=x[:,columns];fit=grouped_logit(xx,y,person)
    if fit['status']!='ok':return fit
    unique=np.unique(person);bootstrap=[];output.mkdir(parents=True,exist_ok=True)
    binding=hashlib.sha256(xx.tobytes()+np.asarray(y).tobytes()+np.asarray(person).tobytes()+str(draws).encode()+core.sha(Path(__file__)).encode()).hexdigest()
    checkpoint=output/'bootstrap.npz'
    if checkpoint.exists():
        if core.sha(checkpoint)!=json.loads(checkpoint.with_suffix('.sha256.json').read_text('utf8'))['sha256']:raise ValueError('companion checkpoint seal differs')
        with np.load(checkpoint) as saved:
            if str(saved['binding'])!=binding:raise ValueError('companion checkpoint binding mismatch')
            bootstrap=saved['values'].tolist()
    start_draw=len(bootstrap)
    for draw in range(len(bootstrap),draws):
        check_yield({"phase":"companion_bootstrap","completed":draw,"total":draws})
        rng=np.random.default_rng(np.random.SeedSequence([core.SEED,draw,seed_offset]));w=np.bincount(rng.integers(0,len(unique),len(unique)),minlength=len(unique))
        fitted=grouped_logit(xx,y,person,w)
        if fitted['status']!='ok':
            return {'status':'bootstrap_fit_failure','draw':draw,'failure':fitted['status'],'informative_participants':fit['informative_participants']}
        b=fitted['beta'];lower=float(b[columns.index(3)]);upper=float(b[columns.index(4)]) if 4 in columns else None
        bootstrap.append([lower] if upper is None else [lower,upper,lower-upper])
        yielding=wants_yield(CLOCK) or draw+1-start_draw>=CLOCK['max_new_draws']
        if (draw+1)%10==0 or draw+1==draws or yielding:
            tmp=output/'bootstrap.tmp.npz';np.savez_compressed(tmp,values=np.asarray(bootstrap),binding=binding);atomic_replace(tmp,checkpoint);core.save_json(checkpoint.with_suffix('.sha256.json'),{'sha256':core.sha(checkpoint)})
            core.save_json(output/'PROGRESS.json',{'completed':draw+1,'total':draws})
        if yielding and draw+1<draws:raise YieldRequested({'status':'yielded','phase':'companion_bootstrap','completed':draw+1,'total':draws})
    beta=fit['beta'];values=[float(beta[columns.index(3)])]
    if 4 in columns:values.extend([float(beta[columns.index(4)]),float(beta[columns.index(3)]-beta[columns.index(4)])])
    return {'status':'ok','slopes_and_contrast':values,'intervals':np.quantile(bootstrap,[.025,.975],axis=0).T.tolist(),
            'participant_clusters':len(unique),'informative_participants':fit['informative_participants'],'draws':draws,'gradient':fit['gradient']}

def run(output,inputs,config):
    output.mkdir(parents=True,exist_ok=True)
    first=first_play(output/'first-play',inputs,config)
    data=primary.load_verified(inputs['task']);gamma=first['gamma'];p=data['first'];ids=data['first_person']
    if config.get('participants'):
        selected=np.sort(np.random.default_rng(core.SEED).permutation(len(p))[:int(config['participants'])]);p=p[selected];ids=ids[selected]
    raw=primary.dynamic_features(p,gamma);scale=raw.reshape(-1,8).std(axis=0,ddof=1).clip(1e-10);scale[3:5]=first['standing_sd']
    state=raw[:,:,3]+raw[:,:,4];rescue=(state<0)&(state+p[:,:,3]>=0)&(state+p[:,:,2]<0)
    people=np.repeat(ids,30);draws=int(config.get('draws',2000))
    rescue_fit=bootstrap_panel((raw/scale).reshape(-1,8)[rescue.ravel()],p[:,:,6].ravel()[rescue.ravel()],people[rescue.ravel()],
                               [0,1,2,3,5,6,7],output/'rescue',draws,35)
    ii,references,excluded=repeat_roster(data)
    if config.get('participants'):
        keep=np.isin(data['person'][ii],ids);ii=ii[keep];references=references[keep]
    repeats={}
    for label,reference in [('play_start',np.zeros(len(ii))),('best_observed_earlier_score',references)]:
        if not len(ii):repeats[label]={'status':'unsupported','reason':'no unambiguous observed repeat history'};continue
        rr=primary.dynamic_features(data['plays'][ii],gamma,reference);rr/=scale
        repeats[label]=bootstrap_panel(rr.reshape(-1,8),data['plays'][ii,:,6].ravel(),np.repeat(data['person'][ii],30),list(range(8)),
                                       output/label,draws,36 if label=='play_start' else 37)
    first.pop('remaining',None);first['complete_card']=True
    result={'card':'MD3','primary':first,'rescue_subset':rescue_fit,'repeat_companions':repeats,
            'repeat_plays':len(ii),'repeat_history_excluded_people':excluded,
            'reference_scope':'best observed earlier completed-play score; unobserved attempt scores unavailable',
            'complete_computation':True,'source_repeat_eligibility_enforced':True}
    core.save_json(output/'RESULT.json',result);return result

def execute(output:Path,inputs:dict,config:dict):
    global CLOCK
    CLOCK=clock_state(output,config)
    began=time.process_time()
    try:result=run(output,inputs,config)
    except YieldRequested as request:result=request.receipt
    core.save_json(output/'COST.json',{'process_cpu_seconds':time.process_time()-began,'status':result.get('status','complete'),'phase':result.get('phase'),'completed':result.get('completed'),'draws':config.get('draws',2000),'all_companion_and_replay_costs_still_charge':True})
    return result

def verify(output:Path,inputs:dict,config:dict):
    result=execute(output/'independent-replay',inputs,config)
    if result.get('status')=='yielded':return {**result,'verified':False}
    if result!=json.loads((output/'RESULT.json').read_text('utf8')):raise ValueError('complete bounded MD3 replay differs')
    for path in sorted(output.rglob('*.npz')):
        relative=path.relative_to(output)
        if relative.parts[0]=='independent-replay':continue
        with np.load(path,allow_pickle=False) as a,np.load(output/'independent-replay'/relative,allow_pickle=False) as b:
            if set(a.files)!=set(b.files):raise ValueError('MD3 checkpoint replay keys differ')
            for key in a.files:
                equal=np.array_equal(a[key],b[key],equal_nan=True) if np.issubdtype(a[key].dtype,np.number) else np.array_equal(a[key],b[key])
                if not equal:raise ValueError('MD3 complete draw replay differs')
    return {'verified':True,'all_nulls_draws_and_companions_replayed':True}
