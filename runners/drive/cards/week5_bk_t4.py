"""T4 complete refit uncertainty, preserving the certified Week4 model.

DESIGN CHECK: fixed source/sample, train-only scaling, same estimator and
certificates in point, reference, calibration and every bootstrap. Failed fits
remain indexed; they are never dropped to manufacture an interval.
"""
from pathlib import Path
import copy, time
import numpy as np
from scipy.special import logsumexp, softmax
from threadpoolctl import threadpool_limits
from . import week4_t4_sample_cost as sample
from . import week4_t4_inputs as packing
from . import week4_t4_variable as model
from . import week4_t4_kernel_h1 as kernel
from .week5_at_source import authenticate
from .timing_pmap_source import completed
from .timing_census import read, filehash
from .timing_p6 import gzread, gzip_equal, write_equal, progress
from .week5_at_scoring import digest

SEED=20261107
KINDS={'calibration':40,'bootstrap':2000,'parameter':2000,'reference':200}


def source(inputs):
    if set(inputs)!={'sample_completion','covariates_completion'}:
        raise ValueError('Exact original sample and covariates required')
    sc=Path(inputs['sample_completion']);cc=Path(inputs['covariates_completion'])
    for p in (sc,cc):completed(p,p.parent/'PLAN.json')
    plan=read(sc.parent/'PLAN.json')
    if plan['module']!='runners.drive.cards.week4_t4_sample_cost' or plan['config']!=sample.configuration('cost'):
        raise ValueError('Original complete sample identity required')
    packed,selection=sample.load(plan['inputs'])
    completed(sc,sc.parent/'output/PRIVATE_SELECTION.json')
    if read(sc.parent/'output/PRIVATE_SELECTION.json')!=selection:
        raise ValueError('Frozen whole-writer sample changed')
    cp=read(cc.parent/'PLAN.json')
    if cp['module']!='runners.drive.cards.week4_t4_covariates':raise ValueError('Original covariates required')
    completed(cc,cc.parent/'output/PRIVATE_COVARIATES.json')
    cov=read(cc.parent/'output/PRIVATE_COVARIATES.json')
    if sorted(r['writer'] for r in cov)!=packed['writers']:raise ValueError('Covariate writer support differs')
    return dict(packed=packed,selection=selection,covariates=cov,
                source_pins={k:filehash(v) for k,v in inputs.items()})


def resample(packed, selected):
    """Duplicate writers become independent bootstrap groups; retain all menus."""
    out={}
    for half in ('train','test'):
        data=packing.arrays(packed,half);parts={k:[] for k in data}
        for new,old in enumerate(selected):
            take=np.flatnonzero(data['w']==old)
            if not len(take):raise ValueError('Resampled writer lacks a temporal half')
            for key,value in data.items():parts[key].append(np.full(len(take),new,dtype=int) if key=='w' else value[take])
        out[half]={k:np.concatenate(v) for k,v in parts.items()}
    # Original x is a common affine transform of raw features. Recentring and
    # rescaling the sampled training rows therefore recovers its own raw-scale
    # standardization; padding is excluded and later menus never set scales.
    train=out['train'];real=train['x'][train['mask']]
    xm=real.mean(0);xs=real.std(0);zm=train['z'].mean(0);zs=train['z'].std(0)
    xs=np.where(xs>1e-12,xs,1.);zs=np.where(zs>1e-12,zs,1.)
    for data in out.values():
        data['x']=(data['x']-xm)/xs;data['x'][~data['mask']]=0
        data['z']=(data['z']-zm)/zs;model.checked(data)
    return out


def logscore(fit, data, individual, probabilities=None):
    logits=model.logits(np.asarray(fit['theta']),data,individual)
    lp=logits-logsumexp(logits,axis=1)[:,None]
    if probabilities is None:return float(np.mean(lp[np.arange(len(lp)),data['y']]))
    return float(np.mean(np.sum(probabilities*np.where(probabilities>0,lp,0.),axis=1)))


def correlation(x,y):
    pairs=[(a,b) for a,b in zip(x,y) if b is not None and np.isfinite(a) and np.isfinite(b)]
    if len(pairs)<3:return dict(value=None,writers=len(pairs),status='unsupported')
    a,b=np.asarray(pairs).T
    if np.std(a)<1e-12 or np.std(b)<1e-12:return dict(value=None,writers=len(pairs),status='constant')
    return dict(value=float(np.corrcoef(a,b)[0,1]),writers=len(pairs),status='descriptive')


def companions(temperatures,covariates,selected):
    temp=np.asarray(temperatures);lookup={r['writer']:r for r in covariates}
    ordered=sorted(lookup);records=[lookup[ordered[i]] for i in selected]
    return dict(log_temperature_sd=float(np.std(np.log(temp),ddof=1)) if len(temp)>1 else 0.,
                temperature_quantiles=np.quantile(temp,[0,.25,.5,.75,1]).tolist(),
                margin=correlation(temp,[(r.get('identification') or {}).get('margin') for r in records]),
                hesitancy=correlation(temp,[r.get('mean_hesitancy') for r in records]))


def pair(data,covariates,selected,probabilities=None):
    shared=kernel.fit(data['train'],False);individual=kernel.fit(data['train'],True)
    a=logscore(shared,data['test'],False,probabilities);b=logscore(individual,data['test'],True,probabilities)
    return dict(gain=b-a,shared_logscore=a,individual_logscore=b,shared=shared,individual=individual,
                companions=companions(individual['temperatures'],covariates,selected))


def calibration_data(packed, index):
    individual=bool(index%2);seed=20261102+index//2;w=len(packed['writers'])
    theta=np.r_[[1.,-.5,.2,.1,.3,.3,-.2],np.where((np.arange(w)//2)%2,1.5,-1.5),
                np.where(np.arange(w)%2,np.log(4.),np.log(.25)) if individual else np.zeros(w)]
    rng=np.random.default_rng(seed);data={h:packing.arrays(packed,h) for h in ('train','test')};probs={}
    for h,d in data.items():
        d['y']=np.zeros(len(d['w']),dtype=int)
        probs[h]=softmax(model.logits(theta,d,True),axis=1)
        d['y']=(rng.random(len(d['w']))[:,None]>np.cumsum(probs[h],axis=1)).sum(1)
        model.checked(d)
    return data,probs['test'],individual


def draw(bundle,kind,index,point=None):
    packed=bundle['packed'];w=len(packed['writers']);rng=np.random.default_rng(np.random.SeedSequence([SEED,{'bootstrap':1,'parameter':2,'reference':3,'calibration':4}[kind],index]))
    if kind=='calibration':
        data,probabilities,regime=calibration_data(packed,index)
        result=pair(data,bundle['covariates'],range(w),probabilities)
        oracle=float(np.mean(np.sum(probabilities*np.log(np.maximum(probabilities,1e-300)),axis=1)))
        if max(result['shared_logscore'],result['individual_logscore'])>oracle+1e-10:
            raise ValueError('Fitted score exceeded expected generating oracle')
        return dict(result,regime='individual' if regime else 'shared',oracle=oracle)
    if kind=='bootstrap':
        selected=rng.integers(0,w,w).tolist();data=resample(packed,selected)
        return dict(pair(data,bundle['covariates'],selected),selected=selected)
    data={h:packing.arrays(packed,h) for h in ('train','test')}
    if kind=='parameter':
        if point is None:raise ValueError('Frozen point fit required for conditional parameter uncertainty')
        train=data['train'];p=softmax(model.logits(np.asarray(point['individual']['theta']),train,True),axis=1)
        train['y']=(rng.random(len(p))[:,None]>np.cumsum(p,axis=1)).sum(1)
        fit=kernel.fit(train,True)
        return dict(individual=fit,companions=companions(fit['temperatures'],bundle['covariates'],range(w)))
    if kind=='reference':
        for half,d in data.items():
            sizes=d['mask'].sum(1)
            for writer in range(w):
                for size in sorted(set(sizes[d['w']==writer])):
                    ix=np.flatnonzero((d['w']==writer)&(sizes==size));d['y'][ix]=rng.permutation(d['y'][ix])
            model.checked(d)
        return pair(data,bundle['covariates'],range(w))
    raise ValueError('Unknown draw kind')


def interval(values):
    if not values or any(v is None or not np.isfinite(v) for v in values):return None
    return np.quantile(values,[.025,.975]).tolist()


def reduce_values(point,blocks,draws):
    if draws not in (200,2000):raise ValueError('Registered draw count required')
    families={kind:{} for kind in KINDS};bindings=set()
    for block in blocks:
        bindings.add(block['binding']);kind=block['kind']
        for record in block['records']:
            i=record['index']
            if i in families[kind]:raise ValueError('Duplicate global draw')
            families[kind][i]=record
    if len(bindings)!=1:raise ValueError('Mixed scientific inputs')
    if point.get('binding') is not None and point['binding'] not in bindings:raise ValueError('Point and uncertainty source differ')
    for kind,records in families.items():
        wanted=range(draws if kind in ('bootstrap','parameter') else KINDS[kind])
        if set(records)!=set(wanted):raise ValueError('Missing uncertainty or calibration draw: '+kind)
    invalid={k:[i for i,r in rows.items() if r['status']!='complete'] for k,rows in families.items()}
    if any(invalid.values()):return dict(status='invalid',failed_draws=invalid,complete_draws=draws,no_failed_draws_discarded=True)
    values={k:[r['value'] for _,r in sorted(v.items())] for k,v in families.items()}
    cal=values['calibration'];shared=[r['gain'] for r in cal if r['regime']=='shared'];personal=[r['gain'] for r in cal if r['regime']=='individual']
    gate=bool(np.mean(shared)<=.005 and np.mean(personal)>.02)
    boot=values['bootstrap'];ci=interval([r['gain'] for r in boot])
    state='supports' if ci[0]>0 else 'against' if ci[1]<0 else 'inconclusive'
    if not gate:state='invalid; matched calibration failed'
    elif draws==200:state='screening only'
    refs=[r['gain'] for r in values['reference']]
    parameter=values['parameter'];temps=np.array([r['individual']['temperatures'] for r in parameter])
    result=dict(status='complete',card='BK-T4',primary=dict(estimate=point['gain'],interval=ci,draws=draws,state=state),
                calibration=dict(gate=gate,worlds=40,shared_mean=float(np.mean(shared)),individual_mean=float(np.mean(personal))),
                spread=dict(estimate=point['companions']['log_temperature_sd'],interval=interval([r['companions']['log_temperature_sd'] for r in boot]),scale='SD log temperature'),
                parameter_interval_method='conditional parametric training-choice bootstrap; fixed observed feature/state paths',
                per_writer_intervals=np.quantile(temps,[.025,.975],axis=0).T.tolist(),
                reference=dict(draws=200,mean=float(np.mean(refs)),interval=interval(refs),interpretation='within-writer/menu-size/half permutation diagnostic; not an exchangeability claim'),
                boundary_fit_draws=sum(r['individual']['boundary_coordinates']>0 for k in values for r in values[k]),
                descriptive=True,screening_only=draws==200)
    for key in ('margin','hesitancy'):
        result[key]=dict(point['companions'][key],interval=interval([r['companions'][key]['value'] for r in boot]))
    return result


def produce(output,inputs,config,verifying=False):
    root=Path(output);root.mkdir(parents=True,exist_ok=True);operation=config.get('operation')
    began=time.process_time()
    if operation=='source':
        bundle=source(inputs)
        if verifying:
            if gzread(root/'BUNDLE.json.gz')!=bundle:raise ValueError('Original source reconstruction differs')
            return dict(verified=True,complete_source_replay=True)
        gzip_equal(root/'BUNDLE.json.gz',bundle);write_equal(root/'SUMMARY.json',dict(writers=len(bundle['packed']['writers']),scientific_admission=False))
        return dict(status='complete')
    if operation=='reduce':
        pointroot=authenticate(inputs['point_root'])/'output';point=read(pointroot/'POINT.json')
        blocks=[]
        for p in read(inputs['blocks']):
            blockroot=authenticate(p)/'output';blocks.append(read(blockroot/'BLOCK.json'))
        value=reduce_values(point,blocks,int(config.get('draws',2000)))
        if value.get('per_writer_intervals') is not None:
            private=value.pop('per_writer_intervals')
            if verifying:
                if read(root/'PRIVATE_PARAMETER_INTERVALS.json')!=private:raise ValueError('Writer intervals differ')
            else:write_equal(root/'PRIVATE_PARAMETER_INTERVALS.json',private)
        if verifying:
            if read(root/'RESULT.json')!=value:raise ValueError('Complete T4 reduction differs')
            return dict(verified=True,complete_reduction=True)
        write_equal(root/'RESULT.json',value);return dict(status='complete',scientific_status=value['status'])
    bundle_root=authenticate(inputs['source_root'])/'output';bundle=gzread(bundle_root/'BUNDLE.json.gz')
    binding=digest(dict(source=filehash(bundle_root/'BUNDLE.json.gz'),estimator='Week4 T4.h1 unchanged',seed=SEED))
    if operation=='cost':
        if set(inputs)!={'source_root'} or set(config)!={'operation'}:raise ValueError('Exact generated cost input required')
        receipts=[];durations={k:[] for k in ('point','bootstrap','parameter','reference')}
        with threadpool_limits(limits=2):
            for law in (0,1):
                generated,_,_=calibration_data(bundle['packed'],law)
                clean=copy.deepcopy(bundle)
                for half in ('train','test'):
                    clean['packed'][half]['y']=generated[half]['y'].tolist()
                tick=time.process_time();point=pair(generated,clean['covariates'],range(len(clean['packed']['writers'])))
                durations['point'].append(time.process_time()-tick)
                receipts.append(dict(law=law,kind='point',value=point))
                for kind in ('bootstrap','parameter','reference'):
                    for index in range(3):
                        tick=time.process_time();value=draw(clean,kind,index,point)
                        durations[kind].append(time.process_time()-tick);receipts.append(dict(law=law,kind=kind,index=index,value=value))
        if verifying:
            if read(root/'GENERATED_FITS.json')!=receipts:raise ValueError('Generated cost fit replay differs')
            return dict(verified=True,complete_generated_cost_refit=True,human_choices_fitted=False)
        write_equal(root/'GENERATED_FITS.json',receipts)
        # Both complete phases and factor two contingency. Setup/serialization
        # and all earlier charges are added by native campaign accounting.
        projected=4*(max(durations['point'])*41+max(durations['bootstrap'])*2000+
                     max(durations['parameter'])*2000+max(durations['reference'])*200)
        write_equal(root/'COST.json',dict(process_cpu_seconds=time.process_time()-began,
                    per_kind_cpu_seconds=durations,full_primary_forecast_cpu_seconds=projected,
                    fresh_replay_factor=2,contingency_factor=2,human_choices_fitted=False,
                    remaining_setup_and_native_charges_additional=True))
        return dict(status='complete',scientific_admission=False,human_choices_fitted=False)
    if operation=='point':
        calibration=[]
        for p in read(inputs['calibration_blocks']):
            b=read(authenticate(p)/'output/BLOCK.json')
            if b['binding']!=binding or b['kind']!='calibration':raise ValueError('Calibration binding differs')
            calibration.extend(b['records'])
        if sorted(r['index'] for r in calibration)!=list(range(40)) or any(r['status']!='complete' for r in calibration):raise ValueError('All forty matched worlds required')
        means={reg:np.mean([r['value']['gain'] for r in calibration if r['value']['regime']==reg]) for reg in ('shared','individual')}
        if means['shared']>.005 or means['individual']<=.02:raise ValueError('Matched feature calibration gate failed; no human fit')
        packed=bundle['packed'];value=pair({h:packing.arrays(packed,h) for h in ('train','test')},bundle['covariates'],range(len(packed['writers'])))
        value['binding']=binding
        if verifying:
            if read(root/'POINT.json')!=value:raise ValueError('Full point refit differs')
            return dict(verified=True,complete_point_refit=True)
        write_equal(root/'POINT.json',value);return dict(status='complete',scientific_admission=False)
    if operation!='block':raise ValueError('Unknown T4 operation')
    kind=config['kind'];start=int(config.get('start',0));count=int(config.get('count',1))
    if kind not in KINDS or not 1<=count<=100 or start<0 or start+count>KINDS[kind]:raise ValueError('Invalid global block range')
    point=None
    if kind!='calibration':
        point=read(authenticate(inputs['point_root'])/'output/POINT.json')
        if point['binding']!=binding:raise ValueError('Point fit source differs')
    records=[]
    with threadpool_limits(limits=2):
        for index in range(start,start+count):
            path=root/f'draw-{index:04d}.json'
            if path.exists() and not verifying:
                record=read(path)
                if read(path.with_suffix('.receipt.json'))['sha256']!=filehash(path):raise ValueError('Checkpoint seal changed')
            else:
                try:value=draw(bundle,kind,index,point);record=dict(index=index,status='complete',value=value,binding=binding,kind=kind)
                except ValueError as error:record=dict(index=index,status='invalid',reason=str(error),binding=binding,kind=kind)
                if verifying:
                    if read(path)!=record:raise ValueError('Independent draw refit differs')
                else:
                    write_equal(path,record);write_equal(path.with_suffix('.receipt.json'),dict(sha256=filehash(path)))
            if record['binding']!=binding or record['kind']!=kind or record['index']!=index:raise ValueError('Wrong checkpoint identity')
            records.append(record);progress(root/'PROGRESS.json',dict(phase='verify' if verifying else 'execute',kind=kind,draw=index,block_end=start+count))
            if (root/'YIELD_REQUEST.json').exists() and index+1<start+count:
                return dict(status='yielded',reason='sealed T4 fit boundary',completed=len(records))
    value=dict(binding=binding,kind=kind,start=start,count=count,records=records)
    if verifying:
        if read(root/'BLOCK.json')!=value:raise ValueError('Block reduction differs')
        return dict(verified=True,complete_global_block_refit=True)
    write_equal(root/'BLOCK.json',value);write_equal(root/'COST.json',dict(process_cpu_seconds=time.process_time()-began,draws=count,kind=kind,includes_native_verify=False))
    return dict(status='complete',invalid=sum(r['status']!='complete' for r in records))


def execute(output,inputs,config):return produce(output,inputs,config)
def verify(output,inputs,config):return produce(output,inputs,config,True)
