"""Three fixed-dose MD1/MD2 instrument demonstrations with full gamma reselection.

DESIGN CHECK: the oracle dose is fixed before recovery and never tuned to the
recovered held-out gain. Three worlds do not estimate power or prove absence.
Keep the original source, cohort, normalization, bootstrap and every failure.
"""
from pathlib import Path
import hashlib,json,time
import numpy as np
from . import week5_md as md, week5_md_analysis as analysis
from .week5_at_source import authenticate
from .week5_go import write,sha
from .week5_la2_ic import requested,matrix_hash


def source(inputs,config):
    if set(inputs)!={'task','primary_root'}:raise ValueError('exact task and completed MD12 parent required')
    parent=authenticate(inputs['primary_root']);plan=json.loads((parent/'PLAN.json').read_text('utf8'))
    if Path(plan['inputs']['task']).resolve()!=Path(inputs['task']).resolve() or plan['config'].get('participants'):
        raise ValueError('primary source/scope differs from complete first-play scope')
    receipt=json.loads((Path(inputs['task']).parent/'SOURCE.json').read_text('utf8'))
    if bool(receipt.get('constructed_only'))!=bool(config.get('constructed_fixture')):raise ValueError('constructed scope mismatch')
    data=analysis.load_verified(inputs['task']);result=json.loads((parent/'output/RESULT.json').read_text('utf8'))
    if not result.get('complete_computation'):raise ValueError('incomplete MD12 parent')
    return data['first'],result,dict(task_sha256=sha(inputs['task']),parent_complete_sha256=sha(parent/'COMPLETE.json'),parent_plan_sha256=sha(parent/'PLAN.json'))


def fixed_design(plays):
    order=np.random.default_rng(md.SEED).permutation(len(plays));split=min(5000,max(0,len(plays)//3))
    main=plays[np.sort(order[split:])]
    cutoff=np.array([np.flatnonzero(np.isfinite(p[:,9]))[9] for p in main])
    mask=(np.arange(30)[None,:]<=cutoff[:,None])&(main[:,:,6]==1)
    spread=(main[:,:,3]-main[:,:,4])[mask];mean=float(spread.mean());sd=float(spread.std(ddof=1))
    if not np.isfinite(sd) or sd<=0:raise ValueError('training spread unsupported')
    xs=[];objective=[];y=None
    for gamma in md.GAMMAS:
        x,response=md.rating_history(main,float(gamma),mean,sd);x,response,keep=md.center_training(x,response)
        if y is not None and not np.array_equal(y,response):raise ValueError('gamma changed normalization or cohort')
        y=response;xs.append(x);objective.append(md.fit_stats(md.stats(x,y),[0,1,2,3])[1])
    if len(y)<20:raise ValueError('fewer than twenty eligible primary participants')
    index=int(np.argmin(objective))
    return xs,y,index,dict(first_plays=len(plays),exploratory_set_aside=split,main_participants=len(y),constant_training_excluded=int((~keep).sum()))


def residual_direction(x,column,nuisance):
    train=x[:,:10,nuisance].reshape(-1,len(nuisance));target=x[:,:10,column].ravel()
    theta=np.linalg.lstsq(train,target,rcond=1e-12)[0]
    direction=x[:,:,column]-x[:,:,nuisance]@theta
    sd=float(direction[:,:10].std(ddof=1))
    if not np.isfinite(sd) or sd<=1e-12:raise ValueError('target has no nuisance-residual training support')
    return direction,sd


def planted_worlds(xs,y,generating,card):
    x=xs[generating]
    if card=='MD1.ic':columns=[0,1,2,3,4];target=4;nuisance=[0,1,2,3]
    elif card=='MD2.ic':columns=[0,1,2,3,5,6];target=5;nuisance=[0,1,2,3,6]
    else:raise ValueError('unregistered MD instrument parent')
    beta=md.fit_stats(md.stats(x,y),columns)[0];fitted=x[:,:,columns]@beta
    residual=y-fitted;null=fitted-beta[columns.index(target)]*x[:,:,target]
    direction,sd=residual_direction(x,target,nuisance)
    if card=='MD1.ic':
        noise_energy=float(np.mean(residual[:,10:]**2));signal_energy=float(np.mean(direction[:,10:]**2))
        if min(noise_energy,signal_energy)<=1e-15:raise ValueError('oracle dose has no held-out noise or residual-level energy')
        amplitude=float(np.sqrt(.01/(1-.01)*noise_energy/signal_energy))
        dose=dict(oracle_relative_MSE_gain=.01,oracle_definition='alpha squared held-out residual-level energy / (held-out noise energy + alpha squared residual-level energy)',
            nuisance_projection='training only',heldout_noise_energy=noise_energy,heldout_residual_level_energy=signal_energy,
            coefficient_magnitude=amplitude,recovered_gain_is_not_oracle_gain=True)
    else:
        amplitude=.01/sd;dose=dict(standardized_spread_dose=.01,generating_training_residual_sd=sd,coefficient_magnitude=amplitude)
    signs=np.random.default_rng(np.random.SeedSequence([md.SEED,912])).choice([-1.,1.],len(y))
    return [(multiple,null+multiple*amplitude*direction+residual*signs[:,None]) for multiple in (-1,0,1)],dose


def estimate(bank,card,scale,weights=None):
    fits=[md.fit_stats(s,[0,1,2,3],weights) for s in bank]
    index=int(np.argmin([f[1] for f in fits]));base=fits[index]
    if card=='MD1.ic':
        fit=md.fit_stats(bank[index],[0,1,2,3,4],weights)
        if not np.isfinite(base[2]) or base[2]<=1e-15:raise ValueError('undefined held-out relative MSE')
        values=[float((base[2]-fit[2])/base[2]),float(fit[0][-1]),float(md.GAMMAS[index])]
    else:
        fit=md.fit_stats(bank[index],[0,1,2,3,5,6],weights)
        values=[float(fit[0][4]*scale),float(fit[0][4]),float(md.GAMMAS[index])]
    if not np.isfinite(values).all():raise ValueError('nonfinite refit retained')
    return values


def run(plays,parent,config,output,source_binding):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);start=time.monotonic();startcpu=time.process_time()
    card=config['card'];draws=config.get('draws',2000)
    if draws!=2000:raise ValueError('instrument demonstration requires all 2000 draws')
    semantic={k:v for k,v in config.items() if k not in {'max_new_draws','max_wall_seconds'}}
    binding=dict(source=source_binding,config=semantic,source_code={Path(m.__file__).name:sha(m.__file__) for m in [md,analysis]},module_sha256=sha(__file__))
    bp=output/'BINDING.json'
    if bp.exists() and json.loads(bp.read_text('utf8'))!=binding:raise ValueError('MD instrument checkpoint binding changed')
    write(bp,binding)
    try:xs,y,generator,counts=fixed_design(plays)
    except ValueError as error:return dict(status='design cannot test',card=card,reason=str(error))
    if float(md.GAMMAS[generator])!=parent['pooled']['gamma']:raise ValueError('original source M0 gamma failed exact reconciliation')
    if counts['main_participants']!=parent['pooled']['main_participants']:raise ValueError('original primary cohort changed')
    try:worlds,dose=planted_worlds(xs,y,generator,card)
    except ValueError as error:return dict(status='design cannot test',card=card,reason=str(error))
    write(output/'DOSE.json',dict(generating_gamma=float(md.GAMMAS[generator]),**dose))
    results=[];new=0;total=draws*3
    for multiple,response in worlds:
        bank=[md.stats(x,response) for x in xs]
        chosen=int(np.argmin([md.fit_stats(s,[0,1,2,3])[1] for s in bank]))
        scale=residual_direction(xs[chosen],5,[0,1,2,3,6])[1] if card=='MD2.ic' else 1.
        point=estimate(bank,card,scale);path=output/'worlds'/f'{multiple}.json';seal=path.with_suffix('.seal.json')
        world_binding=dict(binding=binding,response_sha256=matrix_hash(response),point=point,scale=scale)
        if path.exists():
            saved=json.loads(seal.read_text('utf8'))
            if saved['binding']!=world_binding or saved['sha256']!=sha(path):raise ValueError('MD world checkpoint changed')
            values=json.loads(path.read_text('utf8'))
        else:values=[]
        for draw in range(len(values),draws):
            if new>=config.get('max_new_draws',total) or requested(output) or time.monotonic()-start>=config.get('max_wall_seconds',900):
                write(path,values);write(seal,dict(binding=world_binding,sha256=sha(path)))
                return dict(status='yielded',complete_card=False,card=card,world=multiple,completed_draws=len(values),intended_draws=draws,new_draws=new)
            rng=np.random.default_rng(np.random.SeedSequence([md.SEED,draw,12]));weight=np.bincount(rng.integers(0,len(y),len(y)),minlength=len(y))
            try:value=dict(values=estimate(bank,card,scale,weight))
            except (ValueError,np.linalg.LinAlgError) as error:value=dict(failed=True,reason=str(error),draw=draw)
            values.append(value);new+=1
            if (draw+1)%25==0 or draw+1==draws or new>=config.get('max_new_draws',total) or requested(output):
                write(path,values);write(seal,dict(binding=world_binding,sha256=sha(path)))
                write(output/'PROGRESS.json',dict(card=card,effect_multiple=multiple,completed=draw+1,total=draws,new_draws=new))
                elapsed=time.process_time()-startcpu
                write(output/'COST.json',dict(new_draws=new,cpu_seconds=elapsed,forecast_full_execute_plus_replay_cpu_seconds=2*elapsed*total/new,
                    basis='all initialization charged in forecast; prior attempts remain separately charged'))
        failed=[i for i,v in enumerate(values) if v.get('failed')]
        if failed:
            results.append(dict(effect_multiple=multiple,state='invalid instrument world',failed_draws=failed,draws=draws));continue
        samples=np.array([v['values'] for v in values]);lo,hi=np.quantile(samples[:,0],[.025,.975]);clo,chi=np.quantile(samples[:,1],[.025,.975])
        result=dict(effect_multiple=multiple,point=point[0],interval=[float(lo),float(hi)],coefficient=point[1],coefficient_interval=[float(clo),float(chi)],
            selected_gamma=point[2],bootstrap_gamma_counts={str(g):int(np.sum(samples[:,2]==g)) for g in md.GAMMAS},failed_draws=[],draws=draws)
        if card=='MD1.ic':result.update(recovered_relative_MSE_gain=point[0],recovered_gain_at_least_one_percent=bool(point[0]>=.01),
            signed_level_zero_exclusion=bool(clo>0 if multiple>0 else chi<0 if multiple<0 else clo>0 or chi<0),
            original_point_gain_and_level_interval_rule=bool(point[0]>=.01 and (clo>0 or chi<0)))
        else:result.update(standardized_spread=point[0],standardization_residual_sd=scale,
            signed_spread_zero_exclusion=bool(lo>0 if multiple>0 else hi<0 if multiple<0 else lo>0 or hi<0),
            original_negative_bar_crossing=bool(hi<-.01))
        results.append(result)
    return dict(status='complete' if all(not r['failed_draws'] for r in results) else 'invalid instrument demonstration',card=card,
        dose=dose,counts=counts,generating_gamma=float(md.GAMMAS[generator]),worlds=results,draws_per_world=draws,
        all_gamma_reselection=True,bootstrap='original whole-person draws, common random numbers across three fixed worlds',
        normalization='original training-only per-person standardization frozen; no post-plant renormalization',
        scope='three prespecified conditional planted worlds; instrument demonstration, not a power curve or evidence of absence',
        primary_unchanged=True,no_failed_draws_dropped_or_redrawn=True)


def execute(output,inputs,config):
    if set(config)-{'card','draws','max_new_draws','max_wall_seconds','constructed_fixture'}:raise ValueError('unregistered instrument setting')
    plays,parent,binding=source(inputs,config);result=run(plays,parent,config,Path(output),binding)
    if result.get('status')!='yielded':write(Path(output)/'RESULT.json',result)
    return result


def verify(output,inputs,config):
    output=Path(output);actual=execute(output/'independent-replay',inputs,config)
    if actual.get('status')=='yielded':return dict(actual,verified=False)
    if actual!=json.loads((output/'RESULT.json').read_text('utf8')):raise ValueError('MD whole instrument demonstration replay differs')
    for name in ['DOSE.json',*[str(p.relative_to(output)) for p in (output/'worlds').glob('*.json') if not p.name.endswith('.seal.json')]]:
        if (output/name).read_bytes()!=(output/'independent-replay'/name).read_bytes():raise ValueError('MD dose/draw replay differs')
    return dict(verified=True,all_three_worlds_all_draws_and_gamma_reselection_replayed=True)
