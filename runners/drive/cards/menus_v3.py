"""V3 response-scale ICCs from D15's trial-level crossed model.

DESIGN CHECK: LESSONS 3-5 read 2026-10-18. Zero writer variance is an attainable
boundary; it implies infinite records for .8 reliability, not zero records.
Noise and known writer-variance constructions validate the moment estimator.
Bootstrap resamples entire writers and re-fits all variance components, assigning
each sampled writer copy a fresh identity. Unidentifiable or >5% undefined draws
are invalid, never clipped into a null. Prompt main effects are conditioned out;
writer-by-prompt variation stays in the within-person denominator.
"""
from __future__ import annotations
from collections import defaultdict,Counter
from pathlib import Path
import math
import time
import numpy as np

from . import menus_d15 as d15
from . import menus_crossed_stats as crossed
from . import menus_d12 as intervals
from . import states_v2 as states
from .menus_io import read,write,sha256,input_hashes,assert_equal

CONFIG=dict(seed=20261018,bootstrap=2000,minimum_writers=4,maximum_undefined_fraction=.05,checkpoint_draws=25)
FEATURES=('handling','accept','edit','dismiss','ignore','hover_events_log1p','typed_since_previous_log1p','observed_menu_latency_log1p')


def load(inputs):
    marker=Path(inputs['d15_complete']);receipt=read(marker)
    if receipt.get('status')!='COMPLETE':raise ValueError('D15 incomplete')
    summary_path=Path(inputs['d15_summary']);root=summary_path.parent
    for path in (summary_path,Path(inputs['d15_plan']),root/'ROWS.json',root/'SUPPORT.json'):
        name=path.resolve().relative_to(marker.parent.resolve()).as_posix()
        if receipt['outputs'].get(name)!=sha256(path):raise ValueError('D15 source artifact changed')
    summary=read(summary_path);plan=read(inputs['d15_plan'])
    for k,v in summary['input_hashes'].items():
        if sha256(plan['inputs'][k])!=v:raise ValueError('D15 original source changed')
    if sha256(root/'ROWS.json')!=summary['row_hash']:raise ValueError('D15 rows changed')
    return read(root/'ROWS.json'),read(root/'SUPPORT.json'),summary


def packed(rows):
    handling,groups,names=d15.encode(rows)
    others=np.asarray([[r['hover_log1p'],r['typed_log1p'],np.nan if r['latency_log1p'] is None else r['latency_log1p']] for r in rows])
    return dict(y=np.column_stack((handling,others)),groups=groups,names=names,
                writer_rows=[np.flatnonzero(groups[0]==w) for w in range(len(names[0]))],
                prompts=len(names[1]))


def fitted(data,index=None):
    y=data['y'];groups=data['groups']
    if index is not None:
        selected=np.concatenate([data['writer_rows'][i] for i in index])
        nodes=np.concatenate([np.full(len(data['writer_rows'][i]),j,int) for j,i in enumerate(index)])
        y=y[selected];groups=[nodes,groups[1][selected],groups[2][selected],nodes*data['prompts']+groups[1][selected]]
    values=[None]*len(FEATURES);diagnostics={}
    for label,columns in (('complete',[0,1,2,3,4,5]),('latency',[6])):
        mask=np.isfinite(y[:,columns]).all(axis=1)
        if np.sum(mask)<3 or len(set(groups[0][mask]))<3:
            diagnostics[label]=dict(valid=False,reason='fewer than three supported writers');continue
        try:
            result=crossed.fit(y[mask][:,columns],[g[mask] for g in groups],d15.GROUPS)
            variance=result['variance'];denominator=variance.sum(axis=0)-variance[1]
            feature=np.divide(variance[0],denominator,out=np.full(len(columns),np.nan),where=denominator>0)
            if label=='complete':
                denominator_handling=float(denominator[:4].sum())
                values[0]=float(variance[0,:4].sum()/denominator_handling) if denominator_handling>0 else None
                for j,value in enumerate(feature):values[j+1]=float(value) if np.isfinite(value) else None
            else:values[-1]=float(feature[0]) if np.isfinite(feature[0]) else None
            diagnostics[label]=dict(valid=True,observations=int(mask.sum()),writers=len(set(groups[0][mask])),
                variance=variance.tolist(),unconstrained=result['unconstrained'].tolist(),
                condition=result['condition'],structural_constants=result['structural_constants'])
        except ValueError as exc:
            diagnostics[label]=dict(valid=False,reason=str(exc))
    return dict(icc=values,diagnostics=diagnostics)


def shuffle(data,seed):
    strata=defaultdict(list)
    for i,(prompt,setting) in enumerate(zip(data['groups'][1],data['groups'][2])):strata[(int(prompt),int(setting))].append(i)
    y=data['y'].copy();rng=np.random.default_rng(seed)
    for _,index in sorted(strata.items()):y[index]=y[rng.permutation(index)]
    return data|dict(y=y)


def summarize(point,draws,config):
    output={}
    for i,name in enumerate(FEATURES):
        value=intervals.interval(point['icc'][i],[r['icc'][i] for r in draws],config)
        n=crossed.decisions_for_reliability(value['effect'])
        lower,upper=value['ci95'];n_low=crossed.decisions_for_reliability(upper);n_high=crossed.decisions_for_reliability(lower)
        value.update(decisions_for_point_eight=n,minimum_integer_records=max(1,math.ceil(n)) if n is not None else None,
            decisions_interval95=[n_low,n_high],unbounded_upper_records=lower==0,
            zero_icc_means_infinite_records=value['effect']==0)
        output[name]=value
    return dict(features=output,primary=output['handling'],state=output['handling']['state'],point=point,
        undefined_fit_counts=dict(Counter(reason.get('reason') for row in draws for reason in row['diagnostics'].values() if not reason['valid'])))


def execute(output,inputs,config):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);started=time.perf_counter()
    rows,support,parent=load(inputs);binding=dict(inputs=input_hashes(inputs),config=config)
    if (output/'BINDING.json').exists():assert_equal(read(output/'BINDING.json'),binding)
    else:write(output/'BINDING.json',binding)
    if (output/'SUMMARY.json').exists():verify(output,inputs,config);return read(output/'SUMMARY.json')
    data=packed(rows)
    if len(data['names'][0])<config['minimum_writers']:raise ValueError('insufficient ICC writers')
    arms={};hashes={};completed=0
    for arm,design in (('primary',data),('outcome_control',shuffle(data,config['seed']+1))):
        point=fitted(design);draws=[]
        for start in range(0,config['bootstrap'],config['checkpoint_draws']):
            if (output/'YIELD_REQUEST.json').exists():return dict(status='yielded',completed_draws=completed)
            path=output/'draws'/f'{arm}-{start:04d}.json';stop=min(start+config['checkpoint_draws'],config['bootstrap'])
            if path.exists():
                if sha256(path)!=read(path.with_suffix('.seal.json'))['sha256']:raise ValueError('changed ICC checkpoint')
                saved=read(path);assert_equal(saved['binding'],binding)
                if saved['start']!=start or saved['stop']!=stop or saved['arm']!=arm:raise ValueError('ICC checkpoint identity changed')
            else:
                batch=[]
                for draw in range(start,stop):
                    rng=np.random.default_rng(config['seed']+10000+draw)
                    index=rng.integers(len(design['names'][0]),size=len(design['names'][0]))
                    batch.append(fitted(design,index))
                saved=dict(binding=binding,start=start,stop=stop,arm=arm,draws=batch)
                write(path,saved);write(path.with_suffix('.seal.json'),dict(sha256=sha256(path)))
            hashes[path.relative_to(output).as_posix()]=sha256(path);draws.extend(saved['draws']);completed+=stop-start
            if completed>=math.ceil(.1*2*config['bootstrap']) and not (output/'FIRST_TENTH.json').exists():
                elapsed=time.perf_counter()-started
                write(output/'FIRST_TENTH.json',dict(completed_draws=completed,total_draws=2*config['bootstrap'],
                    elapsed_seconds=elapsed,projected_seconds=elapsed*2*config['bootstrap']/completed))
        arms[arm]=summarize(point,draws,config)
    if (output/'YIELD_REQUEST.json').exists():return dict(status='yielded',completed_draws=completed)
    report=dict(card='V3',descriptive=True,scientific_admission=False,primary=arms['primary']['primary'],
        state=arms['primary']['state'],arms=arms,draw_hashes=hashes,input_hashes=binding['inputs'],config=config,
        support=support,parent_d15_state=parent['state'],
        estimand='Observed-response ICC over writers conditional on these exact prompts. Prompt main-effect variance excluded; setting, writer-by-prompt and residual variance retained. Handling primary is the trace ratio across four one-hot response coordinates.',
        uncertainty=f"{config['bootstrap']} writer-node bootstrap draws refit trial-level variance components; duplicate sampled writers receive distinct writer and writer-by-prompt identities.",
        missing_features={'D17_slowest_pause_mixture':'Unavailable after D17 invalid; no fabricated replacement.'})
    write(output/'SUMMARY.json',report);return report


def verify(output,inputs,config):
    output=Path(output);report=read(output/'SUMMARY.json');rows,support,parent=load(inputs)
    binding=dict(inputs=input_hashes(inputs),config=config);assert_equal(report['input_hashes'],binding['inputs']);assert_equal(report['config'],config)
    assert_equal(report['support'],support);data=packed(rows)
    for arm,design in (('primary',data),('outcome_control',shuffle(data,config['seed']+1))):
        draws=[]
        for start in range(0,config['bootstrap'],config['checkpoint_draws']):
            name=f'draws/{arm}-{start:04d}.json';path=output/name
            if sha256(path)!=report['draw_hashes'][name]:raise ValueError('changed saved ICC draw')
            saved=read(path);assert_equal(saved['binding'],binding)
            stop=min(start+config['checkpoint_draws'],config['bootstrap'])
            if (saved['start'],saved['stop'],saved['arm'],len(saved['draws']))!=(start,stop,arm,stop-start):raise ValueError('ICC draw coverage differs')
            draws.extend(saved['draws'])
        assert_equal(summarize(fitted(design),draws,config),report['arms'][arm])
    assert_equal(report['primary'],report['arms']['primary']['primary'])
    return dict(verified=True,primary_recomputed=report['primary'],state=report['state'],point_refitted=True)
