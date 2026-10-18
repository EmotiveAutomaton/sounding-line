"""Three canonical D2 comparisons using original likelihood/penalty procedure.

DESIGN CHECK: LESSONS3-5. Identical covariates give exactly uniform forecasts;
planted position/length rules improve held-out log score and reversed test
labels reduce it. Invalid fits fail the unchanged gradient certificate.
All model comparisons use identical rows and paired real-writer resampling.
"""
from collections import defaultdict
import math
import numpy as np
from . import menus_d2 as original
from . import menus_d2_recovery as recovery
from . import states_v2 as states
from .menus_io import assert_equal

MODELS=('content','position','length')
ARMS=('primary','uniform_control')


def baseline_transform(cases,columns,scale=None):
    matrices=[c['x'][:,columns] for c in cases]
    matrices=[x-x.mean(axis=0) for x in matrices]
    if scale is None:
        scale=np.sqrt(np.mean(np.concatenate(matrices)**2,axis=0));scale[scale<1e-10]=1.
    return [x/scale for x in matrices],scale


def fit_recipient(split,cases):
    config=original.CONFIG
    content=original.fit_recipient(split,cases,config)
    if content is None:raise ValueError('nonempty authenticated D2 partition disappeared')
    groups=[[cases[r['key']] for s in split[name] for r in s['rows'] if r['key'] in cases]
            for name in ('train','calibration','test')]
    output={'content':content}
    for name,columns in (('position',[1,2]),('length',[0])):
        tr,scale=baseline_transform(groups[0],columns)
        ca,_=baseline_transform(groups[1],columns,scale);te,_=baseline_transform(groups[2],columns,scale)
        result={k:content[k] for k in ('edges','train_count','calibration_count','test_count','cutoff','test_cutoff')}
        result.update(preprocessing=dict(scale=scale.tolist(),original_columns=columns),arms={})
        for arm in ARMS:
            ty,cy,ey=[original.labels(group,arm,config['seed']) for group in groups]
            candidates=[]
            for penalty in config['penalties']:
                beta,certificate=original.fit(original.pack(tr,ty),penalty)
                loss=float(-original.log_scores(beta,ca,cy).mean())
                candidates.append((loss,penalty,beta,certificate))
            loss,penalty,beta,certificate=min(candidates,key=lambda v:(v[0],v[1]))
            scores=original.log_scores(beta,te,ey)
            predictions=[dict(key=c['key'],session=c['session'],writer=c['writer'],truth=y,size=len(c['x']),
                quintile=int(np.searchsorted(content['edges'],c['dissimilarity'],side='right')),
                log_probability=float(lp),gain=float(lp+math.log(len(c['x'])))) for c,y,lp in zip(groups[2],ey,scores)]
            result['arms'][arm]=dict(beta=beta.tolist(),penalty=penalty,certificate=certificate,
                calibration_losses=[dict(penalty=p,loss=l) for l,p,_,_ in candidates],predictions=predictions)
        output[name]=result
    return output


def interval(values,draws):
    values=np.asarray(values,float);draws=np.asarray(draws,float);point=float(values.mean())
    if not np.isfinite(values).all() or not np.isfinite(draws).all():raise ValueError('nonfinite diagnostic contrast')
    ci=np.quantile(draws,[.025,.975]).tolist();se=float(draws.std(ddof=1))
    return dict(effect=point,ci95=ci,standard_error=se,p_approx=math.erfc(abs(point)/se/math.sqrt(2)) if se else float(point==0),
        state=states.contrast_state(point,*ci),writers=len(values))


def summarize(units):
    predictions={model:{arm:[] for arm in ARMS} for model in MODELS}
    for writer,result in sorted(units.items()):
        for arm in ARMS:
            reference=[{k:r[k] for k in ('key','writer','session','truth','size','quintile')}
                       for r in result['content']['arms'][arm]['predictions']]
            for model in MODELS:
                rows=result[model]['arms'][arm]['predictions']
                assert_equal([{k:r[k] for k in ('key','writer','session','truth','size','quintile')} for r in rows],reference)
                if any(r['writer']!=writer for r in rows):raise ValueError('diagnostic recipient rows differ')
                predictions[model][arm].extend(rows)
    writers=sorted(units)
    if len(writers)<original.CONFIG['minimum_writers']:raise ValueError('insufficient diagnostic writers')
    picks=np.random.default_rng(20261018).integers(len(writers),size=(2000,len(writers)))
    arrays={}
    for model in MODELS:
        arrays[model]={}
        for arm in ARMS:
            grouped=defaultdict(list)
            for row in predictions[model][arm]:grouped[row['writer']].append(row['gain'])
            arrays[model][arm]=np.asarray([np.mean(grouped[w]) for w in writers])
    comparisons={model:{arm:interval(values,values[picks].mean(1)) for arm,values in arms.items()} for model,arms in arrays.items()}
    paired={}
    for baseline in ('position','length'):
        values=arrays['content']['primary']-arrays[baseline]['primary']
        paired['content_minus_'+baseline]=interval(values,values[picks].mean(1))
    replications={}
    for arm in ARMS:
        rows=predictions['content'][arm]
        try:replications[arm]=recovery.summarize(rows,original.CONFIG)
        except ValueError as exc:
            if 'insufficient writers with both extreme quintiles' not in str(exc):raise
            replications[arm]=dict(state='invalid',reason=str(exc),primary=None)
    return dict(primary=comparisons['content']['primary'],all_three_against_uniform=comparisons,
        paired_model_differences=paired,original_quintile_replication=replications,
        writers=writers,menus=len(predictions['content']['primary']),bootstrap_seed=20261018,bootstrap=2000,
        uncertainty='Equal writer means of per-menu log gain; same writer draws paired across all models. Conditional on fitted forecasts/preprocessing/penalty choices, not training-refit uncertainty.',
        controls='Each model reruns original whole pipeline with independent per-menu uniform labels seed20261017. This is not a single outcome permutation; no fake writer comparison is claimed.',
        original_warning='Original D2 is source-held; its previously positive uniform-control warning is preserved. These newly fitted diagnostic comparisons do not restore the old inference.')
