"""Prepared complete V4.c-MC199 continuation; cost admission is mandatory.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-7 reread 2026-10-30.
NULL: original false-alarm bands remain decisive. ALTERNATIVE: original
medium/large detection bands are unchanged. No partial reference bank, failed
fit or missing outer world can produce a label. Every saved statistic must
exactly match the original split. Fresh verification regenerates all choices
and refits all 199 references for all 110 worlds. No automatic human route.
"""
from pathlib import Path
import hashlib,json,time,math
from runners.stage14.common import read,freeze,atomic,filehash
from . import menus_v4_saved_diagnostics as source
from . import menus_v4_split as original
from . import week3_v4c_mc_reference as core

CONFIG=dict(seed=20261030,optimizer_maxiter=100,reference_datasets=199,outer_worlds=110,bootstrap_draws=2000,shard_count=4)
EXTRA={'cost_complete','split_complete','admission'}


def checked_complete(path):
    path=Path(path);c=read(path)
    if c.get('status')!='COMPLETE' or not c.get('fresh_process_verified'):
        raise ValueError('Verified completion required')
    for name,h in c['outputs'].items():
        if filehash(path.parent/name)!=h:raise ValueError('Completed artifact changed: '+name)
    return c


def validate_admission(a,cost_sha,forecast,source_hashes):
    if not a.get('full_write_through') or not a.get('cost_admitted') or a.get('scope')!='110x199 CPU only':
        raise ValueError('Full landed cost admission required')
    if a.get('cost_complete_sha256')!=cost_sha or a.get('source_hashes')!=source_hashes:
        raise ValueError('Cost/source admission binding differs')
    if not 0<forecast<=a['fixed_total_cpu_seconds']-a['prior_cpu_seconds_charged']:
        raise ValueError('Complete projection exceeds remaining admission')


def load(inputs,config):
    if set(config)!=set(CONFIG)|{'shard_index'} or any(config[k]!=v for k,v in CONFIG.items()) or type(config['shard_index']) is not int or not 0<=config['shard_index']<4 or set(inputs)!=source.INPUTS|EXTRA:raise ValueError('Frozen complete MC design required')
    s=source.load({k:inputs[k] for k in source.INPUTS},dict(bootstrap_draws=2000,bootstrap_seed=20261017))
    if s['complete'].get('synthetic_fixture_only'):raise ValueError('Synthetic source cannot enter full continuation')
    checked_complete(inputs['cost_complete']);cost_root=Path(inputs['cost_complete']).parent
    c=read(cost_root/'output/SUMMARY.json');binding=read(cost_root/'output/BINDING.json')
    if not c['cost_only'] or c['constructed'] or c['complete_pipeline_units']!=6 or binding['inputs']!=s['identity']:
        raise ValueError('Complete original-source cost probe required')
    a=read(inputs['admission']);validate_admission(a,filehash(inputs['cost_complete']),c['projected_full_cpu_seconds'],s['identity'])
    s['split_complete']=checked_complete(inputs['split_complete']);s['split_root']=Path(inputs['split_complete']).parent
    plan=read(s['split_root']/'PLAN.json')
    if plan['module']!='runners.drive.cards.menus_v4_split_admitted' or plan['config']['mode']!='full' or plan['config']['optimizer_maxiter']!=config['optimizer_maxiter']:
        raise ValueError('Original complete split design required')
    for key in source.INPUTS:
        if Path(plan['inputs'][key]).resolve()!=Path(inputs[key]).resolve():raise ValueError('Split/source mismatch')
    return s


def trace_hash(trace):
    return hashlib.sha256(json.dumps(trace,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def full_summary(worlds):
    expected={source.world_name(c) for c in source.roster()}
    if len(worlds)!=110 or {source.world_name(w['cell']) for w in worlds}!=expected:
        raise ValueError('Complete 110-world roster required')
    for w in worlds:
        if w['reference_count']!=199 or not 0<w['probability']<=1 or w['detected']!=(w['probability']<=.05):
            raise ValueError('Complete finite reference verdict required')
    def count(ws):
        n=len(ws);k=sum(w['detected'] for w in ws)
        return dict(detected=k,worlds=n,rate=k/n,wilson95=original.wilson(k,n))
    shuffled=count([w for w in worlds if w['cell']['permuted']]);curves={};labels={}
    for plant in source.PLANTS:
        cells={str(d):count([w for w in worlds if not w['cell']['permuted'] and w['cell']['plant']==plant and w['cell']['delta']==d]) for d in source.SIZES}
        curves[plant]=dict(cells=cells,shuffled_null=shuffled)
        labels[plant]=original.label(cells['0.0']['rate'],cells['0.4']['rate'],cells['0.8']['rate'],shuffled['rate'])
    pick=lambda d:[w['detected'] for w in worlds if not w['cell']['permuted'] and w['cell']['plant']=='taste_matched' and w['cell']['delta']==d]
    valid=curves['taste_matched']['cells']['0.0']['rate']<=.1 and shuffled['rate']<=.1
    return dict(status='complete',card='V4.c-MC199',worlds=110,references_per_world=199,curves=curves,labels=labels,
        primary=original.difference(pick(.4),pick(0.),CONFIG['seed'],CONFIG['bootstrap_draws'],valid),
        original_labels_unchanged=True,scientific_admission=False,
        scope='Complete constructed calibration of a fitted conditional reference; no human taste claim or automatic route')


def compute(output,inputs,config,verification=False):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);s=load(inputs,config)
    binding=dict(config=config,inputs={k:filehash(v) for k,v in inputs.items()},code={str(Path(m.__file__).resolve()):filehash(m.__file__) for m in (core,source,original)},consumer_sha256=filehash(__file__))
    def keep(name,value):
        p=output/name
        if verification:
            if read(p)!=value:raise ValueError('Fresh reference replay differs: '+name)
        else:freeze(p,value)
    def pause():
        if (output/'YIELD_REQUEST.json').exists() or (output.parent/'STOP').exists():raise InterruptedError('Complete reference boundary yield')
    keep('BINDING.json',binding);worlds=[];started=time.process_time();computed_worlds=0
    selected=s['worlds'][config['shard_index']::4]
    for wi,world in enumerate(selected):
        pause();name=source.world_name(world['cell']);prefix='worlds/'+name+'/'
        construction,saved=source.load_world(s,world);rows=source.rebuild(s['sessions'],construction,s['plan']['config']['seed'])
        model=core.fit_null(rows,saved,s['base'],config['optimizer_maxiter']);keep(prefix+'NULL_MODEL.json',model)
        observed=core.statistic(rows,s['sessions'],saved,s['geometry'],s['base'],config['optimizer_maxiter']);keep(prefix+'OBSERVED.json',observed)
        old_path=s['split_root']/'output/worlds'/(name+'.json')
        if s['split_complete']['outputs'].get(old_path.relative_to(s['split_root']).as_posix())!=filehash(old_path):raise ValueError('Original split world binding differs')
        if observed['likelihood_ratio']!=read(old_path)['readers']['R-both']['likelihood_ratio']:raise ValueError('Original R-both statistic differs')
        values=[];new=False
        for j in range(199):
            pause();seed=config['seed']+1000*source.roster().index(world['cell'])+j
            name=prefix+f'null-{j:03d}.json';seal=output/(name+'.seal.json')
            if seal.exists() and not verification:
                if read(seal)!=dict(binding=binding,sha256=filehash(output/name)):raise ValueError('Retained reference seal differs')
                value=read(output/name)
                if value['seed']!=seed:raise ValueError('Retained reference seed differs')
            else:
                generated,trace=core.generate(rows,s['base'],model,seed)
                fitted=core.statistic(generated,s['sessions'],saved,s['geometry'],s['base'],config['optimizer_maxiter'])
                value=dict(seed=seed,generated_trace_sha256=trace_hash(trace),statistic=fitted)
                keep(name,value);keep(name+'.seal.json',dict(binding=binding,sha256=filehash(output/name)));new=True
            values.append(value['statistic']['likelihood_ratio'])
            atomic(output/'PROGRESS.json',dict(phase='verify' if verification else 'execute',completed_worlds=wi,reference=j+1,reference_total=199,shard_world_total=len(selected),global_world_total=110))
        probability=core.reference_probability(observed['likelihood_ratio'],values)
        result=dict(cell=world['cell'],reference_count=199,probability=probability,detected=probability<=.05)
        keep(prefix+'RESULT.json',result);worlds.append(result)
        computed_worlds+=int(new)
        if not verification and computed_worlds>=math.ceil(len(selected)/10) and not (output/'FIRST_TENTH.json').exists():
            freeze(output/'FIRST_TENTH.json',dict(projected_cpu_seconds=2*len(selected)*(time.process_time()-started)/computed_worlds,includes_fresh_replay=True))
    summary=dict(status='complete',card='V4.c-MC199-shard',config=config,worlds=worlds,primary=None,scientific_admission=False,aggregate_verdict_pending=True)
    keep('SUMMARY.json',summary)
    return dict(verified=True,worlds=len(selected),full_fresh_generation_and_refit=True) if verification else summary


def execute(output,inputs,config):
    try:return compute(output,inputs,config)
    except InterruptedError:return dict(status='yielded',scientific_admission=False)


def verify(output,inputs,config):return compute(output,inputs,config,True)
