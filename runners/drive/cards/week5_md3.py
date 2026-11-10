"""MD3 complete first/repeat/reference and rescue-subset consumers.

DESIGN CHECK: LESSONS 2–5; CONTROLS 6–7. Grouped fixed intercepts remain
participant intercepts when several plays enter. A best-earlier-score reference
never uses the current or future play. Ambiguous source histories cannot enter
repeat companions. Every bootstrap resamples participants, not trials or plays.
"""
from pathlib import Path
import hashlib
import json
import os
import numpy as np
from scipy.special import expit
from . import week5_md as core
from . import week5_md_analysis as primary


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


def repeat_roster(data):
    if 'repeat_eligible' not in data:raise ValueError('source lacks repaired repeat-history support mask')
    selected=[];references=[];excluded_people=0
    for person in np.unique(data['person']):
        ii=np.flatnonzero(data['person']==person)
        if not data['repeat_eligible'][ii].all():excluded_people+=1;continue
        order=ii[np.argsort(data['counter'][ii],kind='stable')]
        if len(order)<2:continue
        # At least one observed earlier score is required. No unobserved attempt
        # score is invented; the companion is explicitly observed-history scoped.
        best=float(data['plays'][order[0],:,7].sum())
        for index in order[1:]:
            selected.append(index);references.append(best)
            best=max(best,float(data['plays'][index,:,7].sum()))
    return np.asarray(selected,int),np.asarray(references,float),excluded_people


def bootstrap_panel(x,y,person,columns,output,draws,seed_offset):
    xx=x[:,columns];fit=grouped_logit(xx,y,person)
    if fit['status']!='ok':return fit
    unique=np.unique(person);bootstrap=[];output.mkdir(parents=True,exist_ok=True)
    binding=hashlib.sha256(xx.tobytes()+np.asarray(y).tobytes()+np.asarray(person).tobytes()+str(draws).encode()+core.sha(Path(__file__)).encode()).hexdigest()
    checkpoint=output/'bootstrap.npz'
    if checkpoint.exists():
        with np.load(checkpoint) as saved:
            if str(saved['binding'])!=binding:raise ValueError('companion checkpoint binding mismatch')
            bootstrap=saved['values'].tolist()
    for draw in range(len(bootstrap),draws):
        rng=np.random.default_rng(np.random.SeedSequence([core.SEED,draw,seed_offset]));w=np.bincount(rng.integers(0,len(unique),len(unique)),minlength=len(unique))
        fitted=grouped_logit(xx,y,person,w)
        if fitted['status']!='ok':
            return {'status':'bootstrap_fit_failure','draw':draw,'failure':fitted['status'],'informative_participants':fit['informative_participants']}
        b=fitted['beta'];lower=float(b[columns.index(3)]);upper=float(b[columns.index(4)]) if 4 in columns else None
        bootstrap.append([lower] if upper is None else [lower,upper,lower-upper])
        if (draw+1)%10==0 or draw+1==draws:
            tmp=output/'bootstrap.tmp.npz';np.savez_compressed(tmp,values=np.asarray(bootstrap),binding=binding);os.replace(tmp,checkpoint)
            core.save_json(output/'PROGRESS.json',{'completed':draw+1,'total':draws})
    beta=fit['beta'];values=[float(beta[columns.index(3)])]
    if 4 in columns:values.extend([float(beta[columns.index(4)]),float(beta[columns.index(3)]-beta[columns.index(4)])])
    return {'status':'ok','slopes_and_contrast':values,'intervals':np.quantile(bootstrap,[.025,.975],axis=0).T.tolist(),
            'participant_clusters':len(unique),'informative_participants':fit['informative_participants'],'draws':draws,'gradient':fit['gradient']}


def run(output,inputs,config):
    output.mkdir(parents=True,exist_ok=True)
    first=primary.md3(output/'first-play',inputs,config)
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


def fixture():
    rng=np.random.default_rng(711);x=rng.normal(size=(100,30,3));beta=np.array([.6,-.5,.3]);y=(rng.random((100,30))<expit(x@beta)).astype(float)
    a=primary.logistic_fixed(x,y);b=grouped_logit(x.reshape(-1,3),y.ravel(),np.repeat(np.arange(100),30))
    if b['status']!='ok' or not np.allclose(a['beta'],b['beta'],atol=1e-8):raise ValueError('grouped fit differs from balanced exact fit')
    plays=np.zeros((4,30,15));plays[:,:,7]=np.array([1,3,-1,8])[:,None]
    data=dict(plays=plays,person=np.array([0,0,0,1]),counter=np.array([1,2,3,1]),repeat_eligible=np.ones(4,bool))
    ii,refs,_=repeat_roster(data)
    if ii.tolist()!=[1,2] or refs.tolist()!=[30.,90.]:raise ValueError('best earlier score uses future or current outcome')
    data['repeat_eligible'][0]=False
    if len(repeat_roster(data)[0]):raise ValueError('ambiguous repeat history admitted')
    return {'passed':True,'participant_intercept_grouping':True,'past_only_reference':True,'ambiguous_histories_excluded':True}


def execute(output:Path,inputs:dict,config:dict):
    if config.get('phase')=='fixture':r=fixture();core.save_json(output/'FIXTURE.json',r);return r
    return run(output,inputs,config)


def verify(output:Path,inputs:dict,config:dict):
    if config.get('phase')=='fixture':actual=fixture();name='FIXTURE.json'
    else:actual=run(output/'independent-replay',inputs,config);name='RESULT.json'
    if actual!=json.loads((output/name).read_text('utf8')):raise ValueError('whole MD3 replay mismatch')
    return {'verified':True,'all_companions_replayed':True}
