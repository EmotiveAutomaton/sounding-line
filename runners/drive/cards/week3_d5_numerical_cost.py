"""D5 cost only: real layout and masks, entirely constructed numerical values.

DESIGN CHECK: LESSONS 3-5, CONTROLS 1-7 read for parent build. NULL and
ALTERNATIVE share fixed provenance/support/coverage. Invalid source refuses;
cost exhaustion yields; full deterministic replay passes operationally only.
"""
from pathlib import Path
import hashlib
import json
import time
import numpy as np
from runners.stage14.common import read, freeze, filehash, atomic
from .timing_p6 import gzread
from . import week3_d5_context_support as context
from . import week3_d5_reader_cache as reader
from . import week3_d5_scoring_core as core
from . import week3_d5_scoring_validation as validation

CONFIG = dict(card='D5-numerical-cost', schema=1, mode='full', sample_draws=12, seed=20261026, bootstrap=2000)
CONSTRUCTED = dict(CONFIG, mode='constructed', sample_draws=2)


def load(inputs, config):
    if config not in (CONFIG, CONSTRUCTED): raise ValueError('Frozen numerical cost configuration required')
    if config == CONSTRUCTED:
        if inputs: raise ValueError('Constructed fixture takes no source')
        rows, folds, roster = validation.fixture()
        writers = sorted(folds)
        banks = {name:dict(writer_order=writers, assignments=[
            [writers.index(context.reference.label_draw(rows,folds,i,config['seed'],name=='independent')[r['session']]) for r in rows]
            for i in range(config['sample_draws'])]) for name in ('literal','independent')}
        masks = {c:np.ones((len(rows),n),bool) for c,n in [('selection',4),('rhythm',22)]}
        shares=[context.reference.share_draw(rows,i,config['seed']) for i in range(200)]
        return rows,folds,roster,banks,masks,shares,{}
    if set(inputs) != {'context_complete','reader_complete'}: raise ValueError('Both completed producers required')
    pins = {}; plans = {}; roots = {}; completions = {}
    def artifact(key,name):
        p=roots[key]/name; h=filehash(p)
        if completions[key]['outputs'].get(name)!=h: raise ValueError('Completed producer bytes differ')
        pins[str(p)]=h
        return gzread(p) if p.suffix=='.gz' else read(p)
    for key,module in [('context_complete',context),('reader_complete',reader)]:
        terminal=Path(inputs[key]).resolve();roots[key]=terminal.parent;completions[key]=read(terminal)
        if completions[key].get('status')!='COMPLETE' or not completions[key].get('fresh_process_verified'):
            raise ValueError('Independently completed source required')
        pins[str(terminal)]=filehash(terminal);plans[key]=artifact(key,'PLAN.json')
        if plans[key]['module']!=module.__name__ or plans[key]['config']!=module.CONFIG:raise ValueError('Wrong source producer')
        binding=artifact(key,'output/BINDING.json')
        if binding['config']!=module.CONFIG:raise ValueError('Wrong source binding')
        for p,h in binding['inputs'].items():
            if filehash(p)!=h:raise ValueError('Source ancestor differs')
            pins[p]=h
    rows,folds,roster,banks,ancestors=context.load(plans['context_complete']['inputs'],context.CONFIG)
    if artifact('context_complete','output/BINDING.json')['inputs']!=ancestors:raise ValueError('Context ancestry differs')
    pins.update(ancestors)
    reference_terminal=Path(plans['context_complete']['inputs']['reference_complete']).resolve()
    reference_completion=read(reference_terminal);share_path=reference_terminal.parent/'output/SHARE_BANK.json.gz'
    if reference_completion['outputs'].get('output/SHARE_BANK.json.gz')!=filehash(share_path):raise ValueError('Share bank bytes differ')
    pins[str(share_path)]=filehash(share_path);share_bank=gzread(share_path)
    if share_bank['sessions']!=[r['session'] for r in rows] or len(share_bank['bins'])!=200:raise ValueError('Complete share bank required')
    shares=share_bank['bins']
    if any(bins!=context.reference.share_draw(rows,i,config['seed']) for i,bins in enumerate(shares)):raise ValueError('Share seed replay differs')
    complete_support=artifact('context_complete','output/SUMMARY.json')
    if any(complete_support['unsupported_reference_draws'][name][channel] for name in banks for channel in ('final','process')):
        raise ValueError('Complete bank support is required')
    data=artifact('reader_complete','output/ROWS.json.gz')
    if data['rows']!=rows:raise ValueError('Exact complete reader/source row order required')
    masks={}
    for c,n in [('selection',4),('rhythm',22)]:
        raw=np.asarray([[np.nan if x is None else x for x in p[c]] for p in data['process']],float)
        if raw.shape!=(len(rows),n) or np.isinf(raw).any():raise ValueError('Invalid process shape')
        masks[c]=np.isfinite(raw)
        if any(bool(masks[c][i].any())!=r['support'][c] for i,r in enumerate(rows)):raise ValueError('Process support differs')
    # No human feature values are returned. Character kernels are never read.
    return rows,folds,roster,banks,masks,shares,pins


def compute(output, inputs, config, verification=False):
    started=time.process_time();output=Path(output);output.mkdir(parents=True,exist_ok=True)
    rows,folds,roster,banks,masks,shares,pins=load(inputs,config)
    rng=np.random.default_rng(config['seed']);n=len(rows)
    x=rng.uniform(.1,1.,(n,n));kernel=x@x.T/n+np.eye(n)
    values={c:np.where(mask,rng.normal(size=mask.shape),np.nan) for c,mask in masks.items()}
    source_seconds=time.process_time()-started
    def retain(name,value):
        path=output/name
        if verification:
            if read(path)!=value:raise ValueError('Fresh constructed cost replay differs')
        else:freeze(path,value)
    retain('BINDING.json',dict(config=config,inputs=pins))
    hashes=[];timings=[];base_seconds=0.;operations=0
    total=2*(1+config['sample_draws'])
    def boundary():
        if (output/'YIELD_REQUEST.json').exists() or (output.parent/'STOP').exists():raise InterruptedError('Numerical cost boundary yield')
    for name,bank in banks.items():
        for index in [-1]+list(range(config['sample_draws'])):
            boundary();begin=time.process_time()
            assignment=None if index==-1 else context.assignment_for(rows,folds,bank,index,config['seed'],name=='independent')
            results=[]
            for fold in [None] if name=='literal' else [0,1,2]:
                for channel in ('final','process'):
                    plan=core.profile_plan(rows,folds,roster,channel,assignment,fold)
                    for mode in ['real',name]:
                        boundary()
                        scores=(core.score_character(rows,folds,plan,kernel,np.asarray([r['support']['final'] for r in rows]),mode)
                                if channel=='final' else core.score_process(rows,folds,plan,values,mode)[0])
                        record=dict(channel=channel,fold=fold,mode=mode,scores=scores.tolist(),probes=len(plan['probes']),gallery=len(plan['gallery']))
                        if index==-1:
                            ww=[rows[i]['writer'] for i in plan['probes']];bb=[rows[i]['share_bin'] for i in plan['probes']]
                            probe_roster=sorted(set(ww))
                            record['bootstrap']=core.slope_interval(ww,bb,scores,probe_roster,config['bootstrap'],config['seed'])
                            terms=[]
                            for bins in shares:
                                a,b,s=core.slope_terms(ww,[bins[i] for i in plan['probes']],scores,probe_roster)
                                terms.append([a.tolist(),b.tolist(),s])
                            record['share_terms']=terms
                        results.append(record);operations+=1
            hashes.append(hashlib.sha256(json.dumps(results,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest())
            elapsed=time.process_time()-begin
            if index==-1:base_seconds+=elapsed
            else:timings.append(dict(bank=name,draw=index,cpu_seconds=elapsed))
            done=len(hashes);atomic(output/'PROGRESS.json',dict(phase='verify' if verification else 'execute',done=done,total=total,numerical_operations=operations,constructed_features_only=True))
            if not verification and done==3:
                freeze(output/'FIRST_TENTH.json',dict(projected_cpu_seconds=4*(time.process_time()-started)*total/done,scope='Both probe passes times two; no scientific workload admission'))
    summary=dict(sessions=n,original_writers=len(folds),fixed_candidates=len(roster),sampled_draws_per_bank=config['sample_draws'],
        channels=['final','process'],operation_hashes=hashes,numerical_operations=operations,bootstrap_draws=2000,share_draws=200,
        scientific_admission=False,human_outcomes_computed=False,constructed_features_only=True,
        scope='Declared timing sample on full source layout and masks; not a reduced scientific analysis')
    retain('SUMMARY.json',summary)
    worst={name:max(t['cpu_seconds'] for t in timings if t['bank']==name) for name in banks}
    forecast=4*(source_seconds+base_seconds+1000*sum(worst.values()))
    freeze(output/('VERIFY_TIMING.json' if verification else 'TIMING.json'),dict(source_cpu_seconds=source_seconds,base_cpu_seconds=base_seconds,
        draws=timings,complete_single_world_both_passes_margin_cpu_seconds=forecast,
        scope='One numerical world only; calibration-world count and scientific admission remain separate'))
    return dict(verified=True,full_fresh_constructed_cost_replay=True) if verification else dict(status='complete',scientific_admission=False)


def execute(output,inputs,config):
    try:return compute(output,inputs,config)
    except InterruptedError:return dict(status='yielded')
def verify(output,inputs,config):return compute(output,inputs,config,True)
