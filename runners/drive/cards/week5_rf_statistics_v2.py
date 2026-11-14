"""RF1 signed-comment primary, prospectively specified by owner review.

DESIGN CHECK: unchanged election/candidate units; no fabricated election UID.
This numerical primitive cannot load SNAP, infer boundaries, or admit science.
No regularization or coefficient clipping. Non-convergence stays unsupported.
"""
import hashlib
import math
import numpy as np

MODELS=('TWO-A','TWO-B','TWO-C','THREE')
READS=('respect','trust','liking')
SEED=20261112
BOOT_SEED=20261107


class Unsupported(ValueError):
    pass



def early_counts(comments):
    """Already qualified early comments only; never infer election membership/order."""
    result={'comments':len(comments),'reads':{key:dict(for_comments=0,against_comments=0,overlap_comments=0,for_mentions=0,against_mentions=0) for key in READS}}
    for row in comments:
        for key in READS:
            counts=row['markers']['counts'][key];pos=counts['for'];neg=counts['against']
            if type(pos) is not int or type(neg) is not int or min(pos,neg)<0:raise ValueError('Invalid lexical mention count')
            read=result['reads'][key]
            read['for_comments']+=int(pos>0);read['against_comments']+=int(neg>0)
            read['overlap_comments']+=int(pos>0 and neg>0)
            read['for_mentions']+=pos;read['against_mentions']+=neg
    index_rates(result)
    return result


def index_rates(early):
    n=early['comments']
    if type(n) is not int or n<1:raise ValueError('Missing early-comment denominator')
    if set(early['reads'])!=set(READS):raise ValueError('Incomplete three-read counts')
    rates={}
    for key in READS:
        row=early['reads'][key]
        p,a,o,pm,am=(row[name] for name in ('for_comments','against_comments','overlap_comments','for_mentions','against_mentions'))
        if any(type(value) is not int or value<0 for value in (p,a,o,pm,am)):
            raise ValueError('Invalid early-comment or mention count')
        if max(p,a)>n or o>min(p,a) or p+a-o>n or pm<p or am<a or (p==0 and pm!=0) or (a==0 and am!=0):
            raise ValueError('Inconsistent polarity overlap or denominator')
        rates[key]={'for':p/n,'against':a/n}
    return rates


def folds(candidates):
    unique=sorted(set(candidates),key=lambda c:hashlib.sha256(f'RF1-fold|{SEED}|{c}'.encode()).digest())
    if len(unique)<5:raise Unsupported('Fewer than five candidate folds')
    assigned={key:i%5 for i,key in enumerate(unique)}
    return np.array([assigned[c] for c in candidates],dtype=int)


def bootstrap_weights(candidates,index):
    unique=sorted(set(candidates));positions={key:i for i,key in enumerate(unique)}
    seed=int.from_bytes(hashlib.sha256(f'RF1-bootstrap|{BOOT_SEED}|{index}'.encode()).digest()[:8],'big')
    rng=np.random.Generator(np.random.PCG64(seed))
    count=np.bincount(rng.integers(0,len(unique),size=len(unique)),minlength=len(unique))
    return np.array([count[positions[key]] for key in candidates],dtype=float)


def design(rows,model,representation='signed_rates'):
    rows=[dict(row,rates=index_rates(row['early'])) for row in rows]
    if model not in MODELS:raise ValueError('Unknown RF1 model')
    if representation not in ('separate_polarities','signed_rates'):
        raise ValueError('RF1 representation needs explicit prospective review')
    years=sorted({int(row['year']) for row in rows});names=['intercept']+['year_'+str(y) for y in years[1:]]+['early_support']
    columns=[np.ones(len(rows))]+[np.array([int(r['year'])==y for r in rows],dtype=float) for y in years[1:]]
    columns.append(np.array([r['early_support'] for r in rows],dtype=float))
    grouped={'THREE':(('respect',),('trust',),('liking',)),
        'TWO-A':(('respect',),('trust','liking')),'TWO-B':(('respect','trust'),('liking',)),
        'TWO-C':(('respect','liking'),('trust',))}[model]
    for group in grouped:
        if representation=='signed_rates':
            names.append('+'.join(group)+'_signed')
            columns.append(np.array([sum(r['rates'][name]['for']-r['rates'][name]['against'] for name in group) for r in rows],dtype=float))
        else:
            for polarity in ('for','against'):
                names.append('+'.join(group)+'_'+polarity)
                columns.append(np.array([sum(r['rates'][name][polarity] for name in group) for r in rows],dtype=float))
    x=np.column_stack(columns)
    if not np.isfinite(x).all():raise ValueError('Nonfinite RF1 predictors')
    return x,names


def fit_binomial(x,y,n,weights):
    """Unpenalized finite binomial MLE with explicit numerical refusals."""
    x=np.asarray(x,dtype=float);y=np.asarray(y,dtype=float);n=np.asarray(n,dtype=float);weights=np.asarray(weights,dtype=float)
    if not np.isfinite(weights).all() or (weights<0).any():raise ValueError('Invalid binomial weights')
    active=weights>0
    if not active.any():raise Unsupported('Empty training population')
    x=x[active];y=y[active];n=n[active];weights=weights[active]
    if x.ndim!=2 or not np.isfinite(x).all() or not np.isfinite(y).all() or not np.isfinite(n).all() or not np.isfinite(weights).all():
        raise ValueError('Invalid binomial training data')
    if (n<=0).any() or (y<0).any() or (y>n).any() or (weights<0).any():raise ValueError('Invalid binomial counts or weights')
    # Constants are exactly absorbed by the intercept; no nonconstant predictor
    # is removed to make a rank-deficient fit appear identified.
    selected=[0]+[j for j in range(1,x.shape[1]) if np.ptp(x[:,j])>0]
    constant={j:float(x[0,j]) for j in range(1,x.shape[1]) if j not in selected}
    raw=x[:,selected];mu=np.mean(raw,axis=0);scale=np.std(raw,axis=0)
    mu[0]=0;scale[0]=1;z=(raw-mu)/scale
    if np.linalg.matrix_rank(z)!=z.shape[1]:raise Unsupported('Nonconstant training predictors are rank deficient')
    w=weights*n;w/=np.sum(w);target=y/n;beta=np.zeros(z.shape[1])
    def objective(b):
        eta=z@b
        return float(np.sum(w*(np.logaddexp(0,eta)-target*eta)))
    for iteration in range(100):
        eta=z@beta;p=np.exp(-np.logaddexp(0,-eta))
        gradient=z.T@(w*(p-target));hessian=z.T@((w*p*(1-p))[:,None]*z)
        eig=np.linalg.eigvalsh(hessian)
        if eig[-1]<=0 or eig[0]<=1e-12*eig[-1]:raise Unsupported('Binomial Hessian unresolved or separating')
        step=np.linalg.solve(hessian,gradient)
        if np.max(np.abs(gradient))<1e-10 and np.max(np.abs(step))<1e-7:
            original=beta/scale;original[0]-=np.dot(original,mu)
            return {'selected':selected,'constant':constant,'coefficients':original,'iterations':iteration+1,
                'gradient_max':float(np.max(np.abs(gradient))),'step_max':float(np.max(np.abs(step)))}
        before=objective(beta);factor=1.;descent=float(gradient@step)
        for _ in range(40):
            trial=beta-factor*step
            if objective(trial)<=before-1e-4*factor*descent:
                beta=trial;break
            factor*=.5
        else:raise Unsupported('Binomial line search did not converge')
    raise Unsupported('Finite binomial maximum did not converge')


def predict_eta(x,fit):
    x=np.asarray(x,dtype=float)
    for j,value in fit['constant'].items():
        if not np.all(x[:,j]==value):raise Unsupported('Held-out predictor has no training support')
    return x[:,fit['selected']]@fit['coefficients']


def election_losses(rows,representation='signed_rates',weights=None):
    if len({r['election'] for r in rows})!=len(rows):raise ValueError('Duplicate qualified election row')
    candidates=[r['candidate'] for r in rows];assignment=folds(candidates)
    weights=np.ones(len(rows)) if weights is None else np.asarray(weights,dtype=float)
    if weights.shape!=(len(rows),) or (weights<0).any() or not np.isfinite(weights).all():raise ValueError('Invalid candidate bootstrap weights')
    n=np.array([r['later_support']+r['later_oppose'] for r in rows],dtype=float)
    y=np.array([r['later_support'] for r in rows],dtype=float)
    if (n<=0).any():raise ValueError('No later nonneutral votes')
    losses={};fits={}
    for model in MODELS:
        x,names=design(rows,model,representation);loss=np.full(len(rows),np.nan);model_fits=[]
        for fold in range(5):
            test=(assignment==fold)&(weights>0);train=(assignment!=fold)&(weights>0)
            if not test.any():continue
            fit=fit_binomial(x[train],y[train],n[train],weights[train])
            eta=predict_eta(x[test],fit)
            loss[test]=np.logaddexp(0,eta)-(y[test]/n[test])*eta
            model_fits.append({'fold':fold,'train_elections':int(train.sum()),'test_elections':int(test.sum()),
                'iterations':fit['iterations'],'gradient_max':fit['gradient_max']})
        if not np.isfinite(loss[weights>0]).all():raise Unsupported('Incomplete candidate-fold prediction')
        losses[model]=loss;fits[model]=model_fits
    means={model:float(np.sum(loss[weights>0]*weights[weights>0])/np.sum(weights)) for model,loss in losses.items()}
    best=min(MODELS[:3],key=lambda key:means[key])
    return {'primary':means[best]-means['THREE'],'mean_election_log_losses':means,'best_two':best,
        'candidate_clusters':len(set(candidates)),'folds':fits,'representation':representation,
        'scientific_admission':False}


def uncertainty(point,draws):
    values=[r.get('primary') for r in draws]
    valid=[v for v in values if v is not None and math.isfinite(v)]
    base={'estimate':point['primary'],'bar':.002,'valid_draws':len(valid),'requested_draws':2000,
        'interval':None,'se':None,'sees':None,'supports_at':None}
    if point['candidate_clusters']<20:return dict(base,status='below_floor_descriptive')
    if len(valid)!=2000:return dict(base,status='unsupported_or_incomplete_uncertainty')
    lo,hi=np.quantile(valid,[.025,.975],method='linear');se=float(np.std(valid,ddof=1))
    status='positive_candidate' if lo>.002 else 'negative_candidate' if hi<-.002 else 'within_practical_band' if lo>=-.002 and hi<=.002 else 'inconclusive'
    return dict(base,interval=[float(lo),float(hi)],se=se,sees=2.8*se,supports_at=.002+2.8*se,status=status)
