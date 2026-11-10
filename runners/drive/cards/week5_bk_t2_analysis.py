"""T2 final-only prediction, writer-separated folds and complete uncertainty.

DESIGN CHECK: LESSONS3-5, CONTROLS1-7. Known signal must increase AUC;
identical/null and baseline-only worlds must not license added predictive value.
Labels are never features. Every permutation retrains both models and all folds.
"""
from pathlib import Path
import math,warnings,time
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.exceptions import ConvergenceWarning
from threadpoolctl import threadpool_limits
from .timing_pmap_source import completed
from .timing_p6 import gzread,write_equal,progress
from .timing_census import read,filehash

SEED=20261102
CELLS=('primary','argumentative','creative','trees')


def folds(writers):
    unique=sorted(set(writers))
    if len(unique)<5:raise ValueError('Five whole-writer folds unavailable')
    lookup={w:i%5 for i,w in enumerate(np.random.default_rng(SEED).permutation(unique))}
    return np.array([lookup[w] for w in writers])


def auc(y,pred,weight=None):
    y=np.asarray(y,int);pred=np.asarray(pred,float);weight=np.ones(len(y)) if weight is None else np.asarray(weight,float)
    if not len(y) or not np.isfinite(pred).all():return None
    positive=float(weight[y==1].sum());negative=float(weight[y==0].sum())
    if positive<=0 or negative<=0:return None
    order=np.argsort(pred,kind='stable');values=pred[order];labels=y[order];w=weight[order]
    start=np.r_[0,np.flatnonzero(np.diff(values))+1];pos=np.add.reduceat(w*labels,start);neg=np.add.reduceat(w*(1-labels),start)
    return float(pos@(np.cumsum(neg)-.5*neg)/(positive*negative))


def predict(x,y,assignment,model,check=lambda:None):
    x=np.asarray(x,float);y=np.asarray(y,int);prediction=np.full(len(y),np.nan)
    if len(set(y))<2:raise ValueError('One-class target')
    if not np.isfinite(x).all():raise ValueError('Nonfinite final-only feature')
    for fold in sorted(set(assignment)):
        check();test=np.ones(len(y),bool) if fold==-1 else assignment==fold;train=np.ones(len(y),bool) if fold==-1 else ~test
        if len(set(y[train]))<2:raise ValueError('One-class training fold')
        mean=x[train].mean(0);std=x[train].std(0);keep=std>1e-12
        a=(x[train][:,keep]-mean[keep])/std[keep];b=(x[test][:,keep]-mean[keep])/std[keep]
        if a.shape[1]==0:a=np.zeros((sum(train),1));b=np.zeros((sum(test),1))
        if model=='ridge':estimator=LogisticRegression(C=1.,solver='lbfgs',max_iter=2000,tol=1e-8,random_state=SEED)
        elif model=='trees':estimator=HistGradientBoostingClassifier(max_iter=100,learning_rate=.1,max_depth=3,min_samples_leaf=20,l2_regularization=1.,early_stopping=False,random_state=SEED)
        else:raise ValueError('Unregistered classifier')
        with warnings.catch_warnings():
            warnings.simplefilter('error',ConvergenceWarning);estimator.fit(a,y[train])
        if model=='ridge' and np.any(estimator.n_iter_>=2000):raise ValueError('Nonconverged classifier')
        prediction[test]=estimator.predict_proba(b)[:,1]
    if not np.isfinite(prediction).all():raise ValueError('Incomplete prediction bank')
    return prediction


def select(rows,target,cell):
    if target not in ('a','b','c') or cell not in CELLS:raise ValueError('Unregistered T2 target/cell')
    selected=[r for r in rows if r['labels'][target] is not None and (cell not in ('creative','argumentative') or r['genre']==cell)]
    if any(r['labels'][target] not in (0,1) for r in selected):raise ValueError('Nonbinary T2 label')
    return selected


def point(rows,target,cell,check=lambda:None):
    selected=select(rows,target,cell);writers=[r['writer'] for r in selected];y=np.array([r['labels'][target] for r in selected],int)
    base=np.array([r['baseline'] for r in selected],float);full=np.array([r['features'] for r in selected],float)
    if len(selected) and (base.ndim!=2 or base.shape[1]!=3 or full.ndim!=2 or full.shape[1]<3 or not np.array_equal(full[:,:3],base)):raise ValueError('T2 baseline columns do not match')
    result=dict(sentences=len(selected),writers=len(set(writers)),positives=int(sum(y)),negatives=int(len(y)-sum(y)),target=target,cell=cell,
                support_floor=20,model='trees' if cell=='trees' else 'ridge',scope='held-out writers' if len(set(writers))>=20 else 'below floor, descriptive',reason=None)
    if len(set(y))<2:
        result.update(scope='below floor, descriptive',reason='one-class/empty target',auc=None,baseline_auc=None,gain=None,prediction=[],baseline_prediction=[],assignment=[])
        return result,selected
    assignment=folds(writers) if len(set(writers))>=20 else np.full(len(y),-1)
    try:
        baseline=predict(base,y,assignment,result['model'],check);prediction=predict(full,y,assignment,result['model'],check)
    except (ValueError,ConvergenceWarning) as error:
        if np.all(assignment==-1):
            result.update(reason=str(error),auc=None,baseline_auc=None,gain=None,prediction=[],baseline_prediction=[],assignment=[])
            return result,selected
        result.update(scope='below floor, descriptive',reason='whole-writer cross-validation unavailable: '+str(error));assignment=np.full(len(y),-1)
        try:
            baseline=predict(base,y,assignment,result['model'],check);prediction=predict(full,y,assignment,result['model'],check)
        except (ValueError,ConvergenceWarning) as second:
            result.update(reason=str(second),auc=None,baseline_auc=None,gain=None,prediction=[],baseline_prediction=[],assignment=[])
            return result,selected
    aa,bb=auc(y,prediction),auc(y,baseline)
    result.update(auc=aa,baseline_auc=bb,gain=aa-bb,prediction=prediction.tolist(),baseline_prediction=baseline.tolist(),assignment=assignment.tolist())
    return result,selected


def work_units(draws,permutations):
    # Spread expensive refits throughout the pilot, not after all cheap draws.
    out=[];previous=0
    for p in range(permutations):
        boundary=(p+1)*draws//permutations
        out += [('bootstrap',i) for i in range(previous,boundary)];out.append(('permutation',p));previous=boundary
    return out


def same(a,b):
    if isinstance(a,dict):return isinstance(b,dict) and set(a)==set(b) and all(same(v,b[k]) for k,v in a.items())
    if isinstance(a,list):return isinstance(b,list) and len(a)==len(b) and all(same(x,y) for x,y in zip(a,b))
    if type(a)is float:return isinstance(b,(int,float)) and math.isfinite(b) and abs(a-b)<=1e-10
    return a==b


def run(output,inputs,config,verification=False):
    target,cell,draws,permutations,quantum=(config.get(k) for k in ('target','cell','draws','permutations','max_new_draws'))
    required=2000 if cell=='primary' else 200
    if config!=dict(card='BK-T2',target=target,cell=cell,draws=draws,permutations=permutations,max_new_draws=quantum) or target not in ('a','b','c') or cell not in CELLS or draws!=required or permutations!=200 or type(quantum)is not int or quantum<1:raise ValueError('Frozen complete T2 config required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True);c=Path(inputs['feature_completion']);path=c.parent/'output/PRIVATE_FEATURES.json.gz';completed(c,path);rows=gzread(path)
    binding=dict(inputs={k:filehash(v) for k,v in inputs.items()},features_sha256=filehash(path),config={k:v for k,v in config.items() if k!='max_new_draws'})
    if verification:
        if read(output/'BINDING.json')!=binding:raise ValueError('T2 numerical source changed')
    else:write_equal(output/'BINDING.json',binding)
    def check():
        if (output/'YIELD_REQUEST.json').exists():raise InterruptedError('T2 owner checkpoint request')
    try:
        with threadpool_limits(limits=2):
            if (output/'PRIVATE_POINT.json').exists() and not verification:
                fitted=read(output/'PRIVATE_POINT.json');selected=select(rows,target,cell)
            else:
                fitted,selected=point(rows,target,cell,check)
                if verification:
                    if not same(fitted,read(output/'PRIVATE_POINT.json')):raise ValueError('Fresh T2 point/prediction bank differs')
                else:write_equal(output/'PRIVATE_POINT.json',fitted)
            tasks=work_units(draws,permutations);state=dict(bootstrap=[],permutation=[],done=0)
            if not verification and (output/'PRIVATE_STATE.json').exists():state=read(output/'PRIVATE_STATE.json')
            if state['done']!=len(state['bootstrap'])+len(state['permutation']) or state['done']>len(tasks):raise ValueError('Invalid T2 checkpoint coverage')
            oldstate=read(output/'PRIVATE_STATE.json') if verification else None
            writers=np.array([r['writer'] for r in selected]);unique=sorted(set(writers));groups=[np.flatnonzero(writers==w) for w in unique]
            y=np.array([r['labels'][target] for r in selected],int);assignment=np.asarray(fitted['assignment']);base=np.asarray([r['baseline'] for r in selected]);full=np.asarray([r['features'] for r in selected]);new=0;started=time.process_time()
            if fitted['gain'] is not None:
                for kind,i in tasks[state['done']:]:
                    check();rng=np.random.default_rng(np.random.SeedSequence([SEED,0 if kind=='bootstrap' else 1,i]))
                    if kind=='bootstrap':
                        copies=np.bincount(rng.integers(0,len(unique),len(unique)),minlength=len(unique));weight=np.zeros(len(y))
                        for n,group in zip(copies,groups):weight[group]=n
                        aa,bb=auc(y,fitted['prediction'],weight),auc(y,fitted['baseline_prediction'],weight)
                        value=None if aa is None or bb is None else [aa,bb,aa-bb]
                    else:
                        shuffled=y.copy()
                        for group in groups:shuffled[group]=rng.permutation(y[group])
                        try:
                            pp=predict(full,shuffled,assignment,fitted['model'],check);bp=predict(base,shuffled,assignment,fitted['model'],check)
                            aa,bb=auc(shuffled,pp),auc(shuffled,bp);value=None if aa is None or bb is None else aa-bb
                        except (ValueError,ConvergenceWarning):value=None
                    state[kind].append(value);state['done']+=1;new+=1
                    progress(output/'PROGRESS.json',dict(done=state['done'],total=len(tasks),phase='verify' if verification else 'inference',unit=kind))
                    if not verification:
                        progress(output/'PRIVATE_STATE.json',state)
                        if state['done']==math.ceil(.05*len(tasks)) and not (output/'PILOT.json').exists():write_equal(output/'PILOT.json',dict(done=state['done'],total=len(tasks),bootstrap=len(state['bootstrap']),permutations=len(state['permutation']),segment_cpu_seconds=time.process_time()-started))
                    if not verification and new>=quantum and state['done']<len(tasks):return dict(status='yielded',reason='T2 saved numerical quantum')
            if verification and not same(state,oldstate):raise ValueError('Fresh complete T2 bootstrap/permutations differ')
            if not verification and fitted['gain'] is None:progress(output/'PRIVATE_STATE.json',state)
    except InterruptedError:return dict(status='yielded',reason='T2 owner request at safe numerical boundary; verification restarts fully')
    valid=[v for v in state['bootstrap'] if v is not None];invalid_boot=len(state['bootstrap'])-len(valid);invalid_perm=sum(v is None for v in state['permutation'])
    interval=None if len(valid)!=draws else np.quantile(np.asarray(valid),[.025,.975],axis=0).tolist()
    reference=[v for v in state['permutation'] if v is not None];pvalue=None if fitted['gain'] is None or len(reference)!=permutations else (1+sum(v>=fitted['gain']-1e-15 for v in reference))/(permutations+1)
    controlled=fitted['scope']=='held-out writers' and interval is not None and not invalid_perm and len(reference)==permutations
    useful=bool(controlled and fitted['gain']>=.05 and interval[0][2]>0)
    scientific={k:v for k,v in fitted.items() if k not in ('prediction','baseline_prediction','assignment')}
    scientific.update(interval_columns=['auc','baseline_auc','gain'],interval=interval,conditional_on_fitted_prediction_bank=True,
        bootstrap_draws=len(state['bootstrap']),permutations=len(state['permutation']),invalid_bootstrap=invalid_boot,invalid_permutations=invalid_perm,
        reference_tail_probability=pvalue,control_complete=controlled,practical_bar=.05,useful=useful,
        interval_clears_practical_bar=bool(controlled and interval[0][2]>=.05),
        status='useful' if useful else 'below floor, descriptive' if fitted['scope']!='held-out writers' else 'invalid uncertainty/control' if not controlled else 'inconclusive',
        texture=cell!='primary',rev_baseline='unavailable:97/100valid calibration fails format; no main sentence-score bank')
    if verification:
        if not same(scientific,read(output/'SCIENCE.json')):raise ValueError('T2 aggregate replay differs')
        return dict(verified=True,full_prediction_bootstrap_and_refitted_permutation_replay=True)
    write_equal(output/'SCIENCE.json',scientific);return dict(status='complete')


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
