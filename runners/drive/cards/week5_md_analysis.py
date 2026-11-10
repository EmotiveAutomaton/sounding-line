"""Complete MD1/2 companions and MD3 dynamic-history logistic consumer.

DESIGN CHECK: LESSONS 2–5; CONTROLS 6–7. Bootstrap whole participants, train
normalizations only on training data, regenerate all choice-dependent histories
in null trajectories, and reject unconverged likelihoods. Positive and negative
constructed standing effects must both be recoverable. No real counterfactual
outcome is claimed observed.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
for k in ("OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS","NUMEXPR_NUM_THREADS"):
    os.environ[k]="2"
import numpy as np
from scipy.special import expit
from runners.drive.cards import week5_md as md


def load_verified(path):
    path=Path(path)
    receipt=json.loads((path.parent/'SOURCE.json').read_text('utf8'))
    if md.sha(path)!=receipt['task_sha256']:raise ValueError('MD projected source mismatch')
    if not json.loads((path.parent/'VERIFIED.json').read_text('utf8'))['verified']:raise ValueError('source not verified')
    with np.load(path,allow_pickle=False) as bundle:return {k:bundle[k] for k in bundle.files}


def late_and_time(plays,gamma,seed=md.SEED):
    split=min(5000,max(0,len(plays)//3));order=np.random.default_rng(seed).permutation(len(plays));p=plays[np.sort(order[split:])]
    x,y=md.rating_history(p,gamma);x,y,keep=md.center_training(x,y)
    late=np.tile(np.arange(12)>=6,(len(y),1));xx=np.concatenate([x[:,:,:5],(x[:,:,4]*late)[:,:,None]],axis=2)
    # Recenter the newly formed interaction on training ratings, like all fixed-effect regressors.
    xx=xx-xx[:,:10].mean(axis=1)[:,None,:]
    beta=md.fit_stats(md.stats(xx,y),list(range(6)))[0]
    retained=p[keep];components=[];valid=[]
    for i,play in enumerate(retained):
        choice=play[:,8];spin=np.where(play[:,6]==1,np.abs(play[:,13]),0.)
        rating=np.where(np.isfinite(play[:,9]),play[:,11],0.)
        if not (np.isfinite(choice).all() and np.isfinite(spin).all() and np.isfinite(rating).all()):continue
        indices=np.flatnonzero(np.isfinite(play[:,9]));time=np.cumsum(choice+spin+rating)[indices]/60.;time[0]=0.
        components.append(time);valid.append(i)
    time_weight=None
    if len(valid)>1:
        raw_x,raw_y=md.rating_history(retained[valid],gamma)
        time=np.array(components)
        xt=np.concatenate([raw_x[:,:,:3],time[:,:,None]],axis=2)
        xt-=xt[:,:10].mean(axis=1)[:,None,:];raw_y-=raw_y[:,:10].mean(axis=1)[:,None]
        time_weight=float(md.fit_stats(md.stats(xt,raw_y),list(range(4)))[0][-1])
    return {'late_level_interaction':float(beta[-1]),'late_level_weight':float(beta[-2]+beta[-1]),
            'early_level_weight':float(beta[-2]),'observed_component_minutes_weight_percent_mood':time_weight,
            'time_participants':len(valid),'time_scope':'sum of observed response/spin/rating durations; unobserved transitions omitted'}


def md12(output,inputs,config):
    data=load_verified(inputs['task']);plays=data['first']
    if config.get('participants'):
        take=min(int(config['participants']),len(plays));order=np.random.default_rng(md.SEED).permutation(len(plays));plays=plays[np.sort(order[:take])]
    first=md.pooled(plays,output/'pooled',config.get('draws',2000))
    companion=md.companions(plays,output/'companions')
    extra=late_and_time(plays,first['gamma'])
    result={'cards':['MD1','MD2'],'pooled':first,'companions':companion,'late_and_time':extra,
            'complete_computation':True,'independent_replay_required':True,
            'scope':'descriptive first-play participants; sample-scoped' if len(plays)<len(data['first']) else 'descriptive first-play participants',
            'source_first_plays':len(data['first']),'analysed_first_plays':len(plays)}
    md.save_json(output/'RESULT.json',result);return result


def dynamic_features(plays,gamma,reference=None):
    n=len(plays);standing=np.zeros(n);prior=np.zeros(n);recent=np.zeros(n);x=np.zeros((n,30,8))
    if reference is None:reference=np.zeros(n)
    for t in range(30):
        p=plays[:,t];state=standing-reference
        x[:,t]=np.column_stack([p[:,2]>0,p[:,2]<0,(p[:,3]+p[:,4])/2-p[:,2],
                               np.minimum(state,0),np.maximum(state,0),prior,np.full(n,t),recent])
        standing+=p[:,7];prior+=p[:,6];recent=gamma*recent+p[:,7]
    return x


def logistic_fixed(x,y,weights=None,max_iter=100,tolerance=1e-6):
    """Profiled participant intercepts via the exact IRLS Schur complement."""
    n,t,p=x.shape;y=np.asarray(y,float)
    use=(y.sum(axis=1)>0)&(y.sum(axis=1)<t)
    if weights is None:weights=np.ones(n)
    use &= weights>0
    x=x[use];y=y[use];cluster_weight=np.asarray(weights,float)[use]
    if len(x)<2:raise ValueError('fewer than two informative participants')
    alpha=np.log((y.sum(axis=1)+.5)/(t-y.sum(axis=1)+.5));beta=np.zeros(p)
    objective=np.inf
    for iteration in range(max_iter):
        eta=alpha[:,None]+np.einsum('nti,i->nt',x,beta);prob=expit(eta)
        variance=(prob*(1-prob)).clip(1e-9);working=eta+(y-prob)/variance
        total=variance.sum(axis=1);xm=np.einsum('nt,nti->ni',variance,x)/total[:,None]
        zm=np.sum(variance*working,axis=1)/total
        centered=x-xm[:,None,:];zc=working-zm[:,None]
        gram=np.einsum('n,nt,nti,ntj->ij',cluster_weight,variance,centered,centered,optimize=True)
        rhs=np.einsum('n,nt,nti,nt->i',cluster_weight,variance,centered,zc,optimize=True)
        if np.linalg.matrix_rank(gram,tol=1e-8)<p:raise ValueError('fixed-effect logistic rank deficient')
        newbeta=np.linalg.solve(gram,rhs);newalpha=zm-xm@newbeta
        # Backtracking prevents a near-separated participant from increasing loss.
        step=1.
        while step>1e-8:
            b=beta+step*(newbeta-beta);a=alpha+step*(newalpha-alpha)
            linear=a[:,None]+np.einsum('nti,i->nt',x,b)
            loss=float(np.sum(cluster_weight[:,None]*(np.logaddexp(0,linear)-y*linear)))
            if loss<=objective+1e-8:break
            step*=.5
        beta,alpha=b,a;objective=loss
        residual=y-expit(linear)
        gradient=np.einsum('n,nti,nt->i',cluster_weight,x,residual,optimize=True)
        alpha_gradient=np.sum(residual,axis=1)
        if max(np.max(np.abs(gradient))/max(1,cluster_weight.sum()),np.max(np.abs(alpha_gradient)))<tolerance:
            allalpha=np.full(n,np.nan);allalpha[use]=alpha
            return {'beta':beta,'alpha':allalpha,'informative':use,'iterations':iteration+1,
                    'gradient':float(np.max(np.abs(gradient))/cluster_weight.sum())}
    raise ValueError('fixed-effect logistic did not satisfy gradient tolerance')


def null_trajectory(plays,gamma,fit,scale,seed,reference=None):
    rng=np.random.default_rng(seed);out=plays.copy();n=len(out)
    standing=np.zeros(n);prior=np.zeros(n);recent=np.zeros(n)
    beta=fit['beta'].copy();beta[3:5]=0
    alpha=fit['alpha'];valid=np.isfinite(alpha)
    if reference is None:reference=np.zeros(n)
    # Noninformative all-one/all-zero histories are carried as such, and excluded
    # by the same fixed-effect support rule in refits, never assigned an arbitrary alpha.
    fixed_choice=(plays[:,:,6].mean(axis=1)>.5).astype(float)
    for t in range(30):
        row=out[:,t];state=standing-reference
        raw=np.column_stack([row[:,2]>0,row[:,2]<0,(row[:,3]+row[:,4])/2-row[:,2],
                             np.minimum(state,0),np.maximum(state,0),prior,np.full(n,t),recent])
        probability=np.full(n,np.nan);probability[valid]=expit(alpha[valid]+(raw[valid]/scale)@beta)
        choice=fixed_choice.copy();choice[valid]=(rng.random(valid.sum())<probability[valid]).astype(float)
        coin=rng.random(n)<.5
        outcome=np.where(choice,np.where(coin,row[:,3],row[:,4]),row[:,2])
        out[:,t,6]=choice;out[:,t,7]=outcome
        standing+=outcome;prior+=choice;recent=gamma*recent+outcome
    return out


def md3(output,inputs,config):
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
    for i in range(20):
        simulated=null_trajectory(p,gamma,fit,scale,np.random.SeedSequence([md.SEED,i,33]))
        z=dynamic_features(simulated,gamma)/scale;nf=logistic_fixed(z,simulated[:,:,6])
        null_slopes.append(float(nf['beta'][3]))
        md.save_json(output/'PROGRESS.json',{'phase':'dynamic_nulls','completed':i+1,'total':20})
    nulls=np.asarray(null_slopes);bar=max(.01,2*float(np.mean(np.abs(nulls)))+3*float(np.std(nulls,ddof=1)))
    draws=int(config.get('draws',2000));bootstrap=[]
    binding=hashlib.sha256(np.ascontiguousarray(p).tobytes()).hexdigest();checkpoint=output/'standing_bootstrap.npz'
    if checkpoint.exists():
        with np.load(checkpoint) as b:
            if str(b['binding'])!=binding or int(b['draws'])!=draws or float(b['gamma'])!=gamma:raise ValueError('MD3 checkpoint mismatch')
            bootstrap=b['values'].tolist()
    for i in range(len(bootstrap),draws):
        rng=np.random.default_rng(np.random.SeedSequence([md.SEED,i,34]));w=np.bincount(rng.integers(0,len(p),len(p)),minlength=len(p))
        b=logistic_fixed(x,y,w)['beta'];bootstrap.append([float(b[3]),float(b[4]),float(b[3]-b[4])])
        if (i+1)%10==0 or i+1==draws:
            temp=output/'standing_bootstrap.tmp.npz';np.savez_compressed(temp,values=np.array(bootstrap),binding=binding,draws=draws,gamma=gamma);os.replace(temp,checkpoint)
            md.save_json(output/'PROGRESS.json',{'phase':'participant_bootstrap','completed':i+1,'total':draws})
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


def fixture():
    rng=np.random.default_rng(57);n=120;t=30;x=rng.normal(size=(n,t,3));beta=np.array([.8,-.6,.3]);a=rng.normal(0,.3,n)
    y=(rng.random((n,t))<expit(a[:,None]+x@beta)).astype(float)
    fit=logistic_fixed(x,y)
    assert np.sign(fit['beta']).tolist()==np.sign(beta).tolist()
    assert fit['gradient']<1e-6
    # Degenerate clusters are excluded with their count retained; never fitted
    # as finite intercepts with invented uncertainty.
    y[0]=0;y[1]=1;fit=logistic_fixed(x,y)
    assert not fit['informative'][0] and not fit['informative'][1]
    return {'passed':True,'signed_logit_recovery':True,'gradient_certificate':True,'degenerate_cluster_guard':True}


def execute(output:Path,inputs:dict,config:dict):
    output.mkdir(parents=True,exist_ok=True)
    phase=config.get('phase','MD12')
    if phase=='fixture':a=fixture();md.save_json(output/'FIXTURE.json',a);return a
    if phase=='MD12':return md12(output,inputs,config)
    if phase=='MD3':return md3(output,inputs,config)
    raise ValueError('unknown MD analysis phase')


def verify(output:Path,inputs:dict,config:dict):
    phase=config.get('phase','MD12')
    if phase=='fixture':
        if fixture()!=json.loads((output/'FIXTURE.json').read_text('utf8')):raise ValueError('fixture mismatch')
        return {'verified':True,'phase':phase}
    replay=output/'independent-replay';replay.mkdir(exist_ok=True)
    actual=execute(replay,inputs,config);expected=json.loads((output/'RESULT.json').read_text('utf8'))
    if actual!=expected:raise ValueError('complete MD analysis replay mismatch')
    return {'verified':True,'phase':phase,'all_statistics_and_draws_replayed':True}
