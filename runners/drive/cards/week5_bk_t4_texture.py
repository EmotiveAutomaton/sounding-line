"""T4 genre projection and identified writer-weight texture with complete blocks."""
from pathlib import Path
import copy,time
import numpy as np
from scipy.special import softmax
from threadpoolctl import threadpool_limits
from . import week5_bk_t4 as core
from . import week5_bk_t4_weights as weights
from . import week5_bk_t4_texture_solver_h1 as comparator
from .week5_at_source import authenticate
from .timing_census import read,filehash
from .timing_p6 import gzread,gzip_equal,write_equal,progress


def genre_bundle(bundle,genre):
    if genre not in ('creative','argumentative'):raise ValueError('Unregistered genre')
    packed=bundle['packed'];counts={}
    for half in ('train','test'):
        ids=np.asarray(packed[half]['w']);g=np.asarray(packed[half]['genres'])
        counts[half]=np.bincount(ids[g==genre],minlength=len(packed['writers']))
    selected=[i for i in range(len(packed['writers'])) if min(counts[h][i] for h in counts)>=20]
    floor_pass=len(selected)>=25
    if not floor_pass:selected=[i for i in range(len(packed['writers'])) if min(counts[h][i] for h in counts)>=1]
    if not selected:raise ValueError('No writer has genre menus in both temporal halves')
    new=copy.deepcopy(bundle);p=new['packed'];p['writers']=[packed['writers'][i] for i in selected]
    for half in ('train','test'):
        original=packed[half];take=[i for i,(w,g) in enumerate(zip(original['w'],original['genres'])) if w in selected and g==genre]
        p[half]={k:[v[i] for i in take] for k,v in original.items()}
        p[half]['w']=[selected.index(w) for w in p[half]['w']]
    normalized=core.resample(p,list(range(len(selected))))
    for half in ('train','test'):
        for key,value in normalized[half].items():p[half][key]=value.tolist()
    keep=set(p['writers']);new['covariates']=[r for r in bundle['covariates'] if r['writer'] in keep]
    new['texture_scope']=dict(genre=genre,writers=len(selected),original_sample_writers=len(packed['writers']),
                              scope='descriptive texture' if floor_pass else 'below floor, descriptive',
                              support_route='twenty menus per half' if floor_pass else 'at least one per half; pooled descriptive comparison',
                              requires_pooled_fallback=not floor_pass)
    return new


def pair(data,covariates,selected,probabilities=None):
    baseline=comparator.fit(data['train'],True);model=weights.fit(data['train'],baseline)
    a=core.logscore(baseline,data['test'],True,probabilities);b=weights.score(model,data['test'],probabilities)
    u=np.asarray(model['unit_directions'])
    return dict(gain=b-a,baseline_logscore=a,weight_logscore=b,baseline=baseline,individual=model,
                direction_dispersion=float(1-np.dot(u.mean(0),u.mean(0))),
                companions=core.companions(model['temperatures'],covariates,selected))


def generated(bundle,index):
    packed=bundle['packed'];w=len(packed['writers']);heterogeneous=bool(index%2);rng=np.random.default_rng(20261107+index//2)
    beta=np.array([1.,-.5,.2,.1,.3]);m=np.linalg.norm(beta)
    directions=np.tile(beta/m,(w,1))
    if heterogeneous:directions[(np.arange(w)//2)%2==1,0]*=-1
    q=np.where(np.arange(w)%2,np.log(4.),np.log(.25));q-=q.mean()
    theta=np.r_[np.log(m),[.3,-.2],np.where((np.arange(w)//2)%2,1.5,-1.5),q,
                np.concatenate([weights.angles_of(v) for v in directions])]
    data={h:core.packing.arrays(packed,h) for h in ('train','test')};probabilities={}
    for half,d in data.items():
        d['y']=np.zeros(len(d['w']),int);probabilities[half]=softmax(weights.logits(theta,d),axis=1)
        d['y']=(rng.random(len(d['w']))[:,None]>np.cumsum(probabilities[half],axis=1)).sum(1)
    return data,probabilities['test'],heterogeneous


def draw(bundle,kind,index):
    w=len(bundle['packed']['writers'])
    if kind=='calibration':
        data,probability,heterogeneous=generated(bundle,index);value=pair(data,bundle['covariates'],range(w),probability)
        oracle=float(np.mean(np.sum(probability*np.log(np.maximum(probability,1e-300)),axis=1)))
        if max(value['baseline_logscore'],value['weight_logscore'])>oracle+1e-10:raise ValueError('Texture exceeded oracle')
        return dict(value,regime='different-directions' if heterogeneous else 'common-direction',oracle=oracle)
    if kind!='bootstrap':raise ValueError('Unknown weight texture draw kind')
    rng=np.random.default_rng(np.random.SeedSequence([20261107,8,index]));selected=rng.integers(0,w,w).tolist()
    return dict(pair(core.resample(bundle['packed'],selected),bundle['covariates'],selected),selected=selected)


def reduce_values(point,blocks,draws=200):
    if draws not in (200,2000):raise ValueError('Registered texture uncertainty required')
    rows={'calibration':{},'bootstrap':{}};bindings=set()
    for block in blocks:
        bindings.add(block['binding'])
        for r in block['records']:
            if r['index'] in rows[block['kind']]:raise ValueError('Duplicate texture draw')
            rows[block['kind']][r['index']]=r
    if len(bindings)!=1 or (point.get('binding') is not None and point['binding'] not in bindings):raise ValueError('Mixed texture binding')
    if set(rows['calibration'])!=set(range(40)) or set(rows['bootstrap'])!=set(range(draws)):
        raise ValueError('Incomplete texture calibration or uncertainty')
    invalid={k:[i for i,r in values.items() if r['status']!='complete'] for k,values in rows.items()}
    if any(invalid.values()):return dict(status='invalid',failed_draws=invalid,no_failed_draws_discarded=True)
    cal=[r['value'] for r in rows['calibration'].values()];boot=[r['value'] for _,r in sorted(rows['bootstrap'].items())]
    means={reg:float(np.mean([r['gain'] for r in cal if r['regime']==reg])) for reg in ('common-direction','different-directions')}
    gate=means['common-direction']<=.005 and means['different-directions']>.02
    result=dict(status='complete',card='BK-T4.writer-weights',descriptive=True,draws=draws,
                primary=dict(estimate=point['gain'],interval=core.interval([r['gain'] for r in boot]),state='descriptive texture' if gate else 'invalid; matched calibration failed'),
                calibration=dict(gate=gate,worlds=40,means=means),direction_dispersion=dict(estimate=point['direction_dispersion'],interval=core.interval([r['direction_dispersion'] for r in boot])),
                temperature_spread=dict(estimate=point['companions']['log_temperature_sd'],interval=core.interval([r['companions']['log_temperature_sd'] for r in boot])),
                boundary_draws=sum(r['individual']['boundary_coordinates']>0 for r in boot))
    for key in ('margin','hesitancy'):result[key]=dict(point['companions'][key],interval=core.interval([r['companions'][key]['value'] for r in boot]))
    return result


def run(output,inputs,config,verifying=False):
    root=Path(output);root.mkdir(parents=True,exist_ok=True);operation=config['operation']
    source=authenticate(inputs['source_root'])/'output';bundle=gzread(source/'BUNDLE.json.gz')
    binding=core.digest(dict(source=filehash(source/'BUNDLE.json.gz'),model='unit-directions-v1',seed=20261107))
    if operation=='genre_fallback':
        scope=bundle.get('texture_scope',{})
        if not scope.get('requires_pooled_fallback'):raise ValueError('Pooled fallback only for failed genre floor')
        data={h:core.packing.arrays(bundle['packed'],h) for h in ('train','test')}
        for d in data.values():d['w']=np.zeros(len(d['w']),int)
        fitted=core.kernel.fit(data['train'],False)
        value=dict(card='BK-T4.genre.'+scope['genre'],scope=scope,pooled_logscore=core.logscore(fitted,data['test'],False),
                   training_menus=len(data['train']['w']),test_menus=len(data['test']['w']),
                   individual_temperature_contrast='unsupported at registered floor; pooled descriptive fit only',descriptive=True)
        if verifying:
            if read(root/'RESULT.json')!=value or read(root/'PRIVATE_FIT.json')!=fitted:raise ValueError('Pooled genre replay differs')
            return dict(verified=True,complete_pooled_genre_refit=True)
        write_equal(root/'PRIVATE_FIT.json',fitted);write_equal(root/'RESULT.json',value);return dict(status='complete')
    if operation=='genre':
        value=genre_bundle(bundle,config['genre'])
        if verifying:
            if gzread(root/'BUNDLE.json.gz')!=value:raise ValueError('Genre source replay differs')
            return dict(verified=True,complete_genre_projection=True)
        gzip_equal(root/'BUNDLE.json.gz',value);write_equal(root/'SUMMARY.json',value['texture_scope']);return dict(status='complete')
    if operation=='reduce':
        point=read(authenticate(inputs['point_root'])/'output/POINT.json')
        if point['binding']!=binding:raise ValueError('Texture reduction source differs')
        blocks=[read(authenticate(p)/'output/BLOCK.json') for p in read(inputs['blocks'])]
        result=reduce_values(point,blocks,config.get('draws',200))
        if verifying:
            if read(root/'RESULT.json')!=result:raise ValueError('Texture full reduction differs')
            return dict(verified=True,complete_texture_reduction=True)
        write_equal(root/'RESULT.json',result);return dict(status='complete')
    if operation=='point':
        records=[]
        for p in read(inputs['calibration_blocks']):
            block=read(authenticate(p)/'output/BLOCK.json')
            if block['binding']!=binding or block['kind']!='calibration':raise ValueError('Texture calibration binding differs')
            records.extend(block['records'])
        if sorted(r['index'] for r in records)!=list(range(40)) or any(r['status']!='complete' for r in records):raise ValueError('All texture calibration worlds required')
        means={reg:np.mean([r['value']['gain'] for r in records if r['value']['regime']==reg]) for reg in ('common-direction','different-directions')}
        if means['common-direction']>.005 or means['different-directions']<=.02:raise ValueError('Texture matched calibration failed; no human fit')
        value=pair({h:core.packing.arrays(bundle['packed'],h) for h in ('train','test')},bundle['covariates'],range(len(bundle['packed']['writers'])));value['binding']=binding
        if verifying:
            if read(root/'POINT.json')!=value:raise ValueError('Texture point refit differs')
            return dict(verified=True,complete_texture_point_refit=True)
        write_equal(root/'POINT.json',value);return dict(status='complete')
    if operation!='block':raise ValueError('Unknown texture operation')
    kind=config['kind'];start=int(config['start']);count=int(config['count']);total=40 if kind=='calibration' else 2000
    if kind not in ('calibration','bootstrap') or not 1<=count<=100 or not 0<=start or start+count>total:raise ValueError('Invalid texture block range')
    if kind=='bootstrap':
        point=read(authenticate(inputs['point_root'])/'output/POINT.json')
        if point['binding']!=binding:raise ValueError('Texture point source differs')
    records=[];began=time.process_time()
    with threadpool_limits(limits=2):
        for index in range(start,start+count):
            path=root/f'draw-{index:04d}.json'
            if path.exists() and not verifying:
                record=read(path)
                if read(path.with_suffix('.receipt.json'))['sha256']!=filehash(path):raise ValueError('Texture checkpoint changed')
            else:
                try:record=dict(index=index,status='complete',value=draw(bundle,kind,index),binding=binding)
                except ValueError as error:record=dict(index=index,status='invalid',reason=str(error),binding=binding)
                if verifying:
                    if read(path)!=record:raise ValueError('Independent texture refit differs')
                else:
                    write_equal(path,record);write_equal(path.with_suffix('.receipt.json'),dict(sha256=filehash(path)))
            if record['binding']!=binding or record['index']!=index:raise ValueError('Wrong texture checkpoint')
            records.append(record);progress(root/'PROGRESS.json',dict(phase='verify' if verifying else 'fit',index=index,kind=kind))
            if (root/'YIELD_REQUEST.json').exists() and len(records)<count:return dict(status='yielded',reason='sealed texture fit boundary')
    block=dict(binding=binding,kind=kind,records=records,start=start,count=count)
    if verifying:
        if read(root/'BLOCK.json')!=block:raise ValueError('Texture block reduction differs')
        return dict(verified=True,full_texture_block_refit=True)
    write_equal(root/'BLOCK.json',block);write_equal(root/'COST.json',dict(process_cpu_seconds=time.process_time()-began,kind=kind,draws=count));return dict(status='complete')

def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
