"""AT2--AT4 writer-disjoint prediction and complete paired uncertainty.

DESIGN CHECK: LESSONS 3--5, 2026-11-07. Null/identical predictors give exact
zero gain; positive/reversed planted predictors test reachable signed bands.
All transforms are learned on training writers only. Undefined focal fits,
one-class AUC, partial model banks and nonfinite observations refuse inference.
"""
from pathlib import Path
import math
import numpy as np
from scipy.special import expit
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from threadpoolctl import threadpool_limits

from .timing_census import read,filehash
from .timing_p6 import gzread,write_equal
from .week5_at_scoring import SEED,ENGINE_MODELS,MODELS,digest


def outcome(effect, samples, bar, *, direction=1):
    a=np.asarray(samples,float)
    if len(a)<2 or not np.isfinite(a).all() or not math.isfinite(effect):
        return dict(state='invalid',reason='absent or nonfinite complete uncertainty')
    low,high=map(float,np.quantile(a,[.025,.975]))
    oriented=sorted((direction*low,direction*high))
    state=('supports' if oriented[0]>bar else 'against' if oriented[1]<0 or
           (oriented[0]>=-bar and oriented[1]<=bar) else 'inconclusive')
    return dict(effect=float(effect),ci_low=low,ci_high=high,bar=bar,state=state,draws=len(a))


def folds(writers, count=5):
    unique=sorted(set(writers))
    if len(unique)<count:raise ValueError('Fewer writers than folds')
    shuffled=np.random.default_rng(SEED).permutation(unique)
    lookup={w:i%count for i,w in enumerate(shuffled)}
    return np.array([lookup[w] for w in writers])


def standardized(train,test):
    mu=train.mean(0);sd=train.std(0)
    keep=sd>1e-12
    return (train[:,keep]-mu[keep])/sd[keep],(test[:,keep]-mu[keep])/sd[keep]


def gaussian_predictions(x,y,writers,assignment,within=True):
    """Training-writer fixed-effect slopes; zero new-writer effect at test.

    Average training intercept predicts the unobserved new writer. No held-out
    outcome or held-out writer mean is ever used by the prediction function.
    """
    pred=np.full(len(y),np.nan);logp=np.full(len(y),np.nan)
    for fold in sorted(set(assignment)):
        train=assignment!=fold;test=~train
        a,b=standardized(x[train],x[test]);target=y[train];groups=writers[train]
        centered_x=a.copy();centered_y=target.copy()
        if within:
            for writer in sorted(set(groups)):
                m=groups==writer;centered_x[m]-=a[m].mean(0);centered_y[m]-=target[m].mean()
        else:
            centered_x-=a.mean(0);centered_y-=target.mean()
        beta=np.linalg.lstsq(centered_x,centered_y,rcond=1e-10)[0]
        intercept=float(np.mean(target-a@beta))
        # Population predictive residual includes unexplained writer variation.
        residual=target-(a@beta+intercept)
        variance=float(np.mean(residual**2))
        if variance<=1e-15 or not math.isfinite(variance):raise ValueError('Degenerate training variance')
        pred[test]=b@beta+intercept
        logp[test]=-.5*(math.log(2*math.pi*variance)+(y[test]-pred[test])**2/variance)
    if not np.isfinite(logp).all():raise ValueError('Incomplete held-out prediction')
    return pred,logp


def classifier_predictions(x,y,assignment):
    pred=np.full(len(y),np.nan)
    for fold in sorted(set(assignment)):
        train=assignment!=fold;test=~train
        if len(set(y[train]))<2:raise ValueError('One-class training fold')
        a,b=standardized(x[train],x[test])
        model=LogisticRegression(C=1.,solver='lbfgs',max_iter=2000,tol=1e-8).fit(a,y[train])
        if np.any(model.n_iter_>=2000):raise ValueError('Classifier did not converge')
        pred[test]=model.predict_proba(b)[:,1]
    return pred


def nuisance(rows,timing=False):
    values=[[r['length'],r['log_frequency'],float(r['sentence_start']),
             float(r['paragraph_start']),r['position']] for r in rows]
    if timing:
        values=[a+[r['after_punctuation'],r['on_screen'],r['session_surprisal']] for a,r in zip(values,rows)]
    return np.asarray(values,float)


def pause_outcome(rows,kind='log_pause'):
    if kind=='log_pause':return np.log([r['pause_seconds'] for r in rows])
    if kind=='hesitancy':return np.array([1-r['fast'] for r in rows])
    if kind=='stop':return np.array([r['fast']<.5 for r in rows],float)
    raise ValueError('Unregistered pause outcome')


def prediction_folds(writers):
    n=len(set(writers))
    if n>=2:return folds(writers,min(5,n))
    if len(writers)<10:raise ValueError('Pooled fallback lacks ten words')
    return np.random.default_rng(SEED).permutation(len(writers))%5


def cluster_indices(writers,draws,seed=SEED):
    unique=sorted(set(writers));groups=[np.flatnonzero(writers==w) for w in unique]
    rng=np.random.default_rng(seed)
    for _ in range(draws):
        ids=rng.integers(0,len(unique),len(unique))
        yield np.concatenate([groups[i] for i in ids])


def at2(rows, model_names, draws=2000,timing=False,outcome_name='log_pause'):
    if any(m not in model_names for m in ENGINE_MODELS):raise ValueError('Both engine models are required')
    writers=np.array([r['writer'] for r in rows]);y=pause_outcome(rows,outcome_name);x=nuisance(rows,timing)
    assignment=prediction_folds(writers);within=len(set(writers))>=40
    _,baseline=gaussian_predictions(np.c_[x,[r['population_surprisal'] for r in rows]],y,writers,assignment,within)
    gains={};scores={}
    for name in sorted(model_names):
        scores[name]=np.array([r['scores'][name]['surprisal_nats'] for r in rows])
        _,lp=gaussian_predictions(np.c_[x,scores[name]],y,writers,assignment,within)
        gains[name]=lp-baseline
    boot={m:[] for m in model_names};primary=[]
    for ix in cluster_indices(writers,draws):
        for m in model_names:boot[m].append(float(gains[m][ix].mean()))
        primary.append(max(boot[m][-1] for m in ENGINE_MODELS))
    means={m:float(gains[m].mean()) for m in model_names}
    best=min(means,key=lambda m:(-means[m],m))
    names=sorted(model_names);corr=np.corrcoef([scores[m] for m in names])
    return dict(card='AT2',writers=len(set(writers)),words=len(rows),
                scope='below floor, descriptive' if len(set(writers))<40 else 'descriptive',
                primary=outcome(max(means[m] for m in ENGINE_MODELS),primary,.002),
                secondary={m:outcome(means[m],boot[m],.002) for m in names},selected_model=best,
                pairwise_correlations=dict(models=names,matrix=corr.tolist()),
                estimator='within-training-writer slopes' if within else 'pooled descriptive fallback',
                timing_controls=timing,outcome=outcome_name,fold_unit='writer' if len(set(writers))>=2 else 'word',
                selection='Best final-context held-out gain; engine maximum repeated inside bootstrap')


def within_coefficient(x,y,writers,focal=0):
    a=x.copy();b=y.copy()
    for writer in sorted(set(writers)):
        ix=writers==writer;a[ix]-=x[ix].mean(0);b[ix]-=y[ix].mean()
    keep=np.std(a,0)>1e-12
    if not keep[focal]:raise ValueError('Focal term has no within-writer variation')
    reduced=a[:,keep]
    focal_position=list(np.flatnonzero(keep)).index(focal)
    without=np.delete(reduced,focal_position,axis=1)
    if np.linalg.matrix_rank(reduced,tol=1e-9)<=np.linalg.matrix_rank(without,tol=1e-9):
        raise ValueError('Focal term not separately identifiable')
    return float(np.linalg.lstsq(reduced,b,rcond=1e-10)[0][focal_position])


def at3(rows,model,draws=2000,residualized=False,timing=False,outcome_name='log_pause'):
    writers=np.array([r['writer'] for r in rows]);y=pause_outcome(rows,outcome_name);n=nuisance(rows,timing)
    entropy=np.array([r['scores'][model]['entropy_nats'] for r in rows]);surprise=np.array([r['scores'][model]['surprisal_nats'] for r in rows])
    if residualized:
        control=np.c_[np.ones(len(rows)),surprise,n]
        entropy=entropy-control@np.linalg.lstsq(control,entropy,rcond=1e-10)[0]
    x=np.c_[entropy,surprise,n]
    within=len(set(writers))>=20;groups=[]
    for writer in sorted(set(writers)):
        ix=writers==writer;a=x[ix];b=y[ix]
        if within:a=a-a.mean(0);b=b-b.mean()
        else:a=np.c_[a,np.ones(len(a))]
        groups.append((a.T@a,a.T@b))
    def fit_groups(selected):
        xx=sum(groups[i][0] for i in selected);xy=sum(groups[i][1] for i in selected)
        keep=np.diag(xx)>1e-12;scale=np.sqrt(np.maximum(np.diag(xx),1e-30));standard=xx/np.outer(scale,scale)
        reduced=standard[np.ix_(keep,keep)]
        for focal in (0,1):
            others=[i for i in np.flatnonzero(keep) if i!=focal]
            if not keep[focal] or np.linalg.matrix_rank(reduced,tol=1e-9)<=np.linalg.matrix_rank(standard[np.ix_(others,others)],tol=1e-9):
                raise ValueError('Focal term not separately identifiable')
        beta=np.linalg.lstsq(reduced,xy[keep]/scale[keep],rcond=1e-10)[0]/scale[keep]
        kept=list(np.flatnonzero(keep));return [float(beta[kept.index(k)]) for k in (0,1)]
    point=fit_groups(range(len(groups)));boot=[[],[]];rng=np.random.default_rng(SEED)
    for _ in range(draws):
        fitted=fit_groups(rng.integers(0,len(groups),len(groups)))
        for k in (0,1):boot[k].append(fitted[k])
    r=float(np.corrcoef(entropy,surprise)[0,1])
    return dict(card='AT3',model=model,writers=len(set(writers)),words=len(rows),
                primary=outcome(point[0],boot[0],.01),secondary_surprisal=outcome(point[1],boot[1],.01),
                entropy_surprisal_correlation=r,pair_variance_inflation=1/(1-r*r) if abs(r)<1 else None,
                residualized=residualized,scope='below floor, descriptive' if len(set(writers))<20 else 'descriptive',
                estimator='within-writer' if within else 'pooled descriptive fallback',timing_controls=timing,outcome=outcome_name)


def at4(rows,model,draws=2000,threshold=.5):
    writers=np.array([r['writer'] for r in rows]);y=np.array([r['fast']<threshold for r in rows],int)
    x=nuisance(rows);assignment=prediction_folds(writers)
    b=classifier_predictions(x,y,assignment)
    features=np.array([[r['scores'][model]['surprisal_nats'],r['scores'][model]['entropy_nats']] for r in rows])
    p=classifier_predictions(np.c_[x,features],y,assignment)
    if len(set(y))<2:raise ValueError('AUC requires two outcome classes')
    delta=float(roc_auc_score(y,p)-roc_auc_score(y,b));boot=[]
    for ix in cluster_indices(writers,draws):
        if len(set(y[ix]))<2:raise ValueError('Undefined cluster-bootstrap AUC')
        boot.append(float(roc_auc_score(y[ix],p[ix])-roc_auc_score(y[ix],b[ix])))
    return dict(card='AT4',model=model,writers=len(set(writers)),words=len(rows),threshold=threshold,
                primary=outcome(delta,boot,.02),baseline_auc=float(roc_auc_score(y,b)),full_auc=float(roc_auc_score(y,p)),
                scope='below floor, descriptive' if len(set(writers))<20 else 'descriptive')


def run(output,inputs,config,verifying=False):
    rows=gzread(inputs['rows']);card=config['card'];draws=config.get('draws',2000)
    if config.get('genre'):rows=[r for r in rows if r['genre']==config['genre']]
    if config.get('position')=='sentence_start':rows=[r for r in rows if r['sentence_start']]
    elif config.get('position')=='inside':rows=[r for r in rows if not r['sentence_start']]
    if draws not in (200,2000):raise ValueError('Registered uncertainty count required')
    if not rows:raise ValueError('No supported observations')
    binding=dict(rows_sha256=filehash(inputs['rows']),config=config)
    with threadpool_limits(limits=2):
        if card in ('AT2','AT3') and any(any(k not in r for k in ('after_punctuation','on_screen','session_surprisal')) for r in rows):
            raise ValueError('Complete Week 4 timing covariates required')
        if card=='AT2':result=at2(rows,config['models'],draws,True,config.get('outcome','log_pause'))
        elif card=='AT3':result=at3(rows,config['model'],draws,config.get('residualized',False),True,config.get('outcome','log_pause'))
        elif card=='AT4':result=at4(rows,config['model'],draws,config.get('threshold',.5))
        else:raise ValueError('Unknown AT analysis')
    result['descriptive']=True
    if card=='AT2':
        commissioned=set(MODELS);actual=set(config['models'])
        for name in ('EleutherAI/pythia-410m','EleutherAI/pythia-1.4b'):
            if name in actual:actual.remove(name);actual.add(name+'-deduped')
        result['selection_admissible']=bool(draws==2000 and actual==commissioned and
            config.get('context','final')=='final' and config.get('context_length',1024)==1024 and
            not config.get('genre') and config.get('outcome','log_pause')=='log_pause')
    if draws==200:result['screening_only']=True
    output=Path(output)
    if verifying:
        if read(output/'BINDING.json')!=binding or read(output/'RESULT.json')!=result:
            raise ValueError('Independent AT refit differs')
        return dict(verified=True,complete_refit=True)
    write_equal(output/'BINDING.json',binding);write_equal(output/'RESULT.json',result)
    return dict(status='complete',card=card)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
