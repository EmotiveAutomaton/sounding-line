"""Frozen WC2/FR1 primaries plus explicitly pooled below-floor descriptions.

DESIGN CHECK: LESSONS 3--5 and CONTROLS 1--7, 2026-11-07. A null must
produce exact zero and no positive classification; signed plants must recover
their signs. Primary support/calibration gates are unmodified. Amendment M's
fallback pools eligible events and retains writer clusters for uncertainty;
it can never claim personal identification or change a failed primary gate.
"""
from collections import defaultdict
from pathlib import Path
from types import FunctionType
import numpy as np

from . import week3_failed_means as wc
from . import week3_frames_stats as fr
from . import week3_frames_analysis as fr_analysis
from . import week3_frames_analysis_cluster as cluster
from .week5_at_source import authenticate
from .timing_census import read,filehash
from .timing_p6 import gzread,gzip_equal,write_equal


def pooled(rows,key,draws=200,seed=20261026):
    groups=defaultdict(list)
    for row in rows:
        value=row.get(key)
        if value is not None:
            if not np.isfinite(value):raise ValueError('Nonfinite pooled value')
            groups[row['writer']].append(float(value))
    names=sorted(groups);n=len(names)
    if not n:return dict(mean=None,ci95=None,events=0,writers=0,draws=0)
    sums=np.array([sum(groups[w]) for w in names]);counts=np.array([len(groups[w]) for w in names]);mean=float(sums.sum()/counts.sum())
    if n<2:ci=None;used=0
    else:
        ix=np.random.default_rng(seed).integers(n,size=(draws,n));bank=sums[ix].sum(1)/counts[ix].sum(1);ci=np.quantile(bank,[.025,.975]).tolist();used=draws
    return dict(mean=mean,ci95=ci,events=int(counts.sum()),writers=n,draws=used,
                interpretation='pooled event mean; descriptive whole-writer resampling; no primary route')


def wc_fallback(data,vectors):
    selected,_=wc.required(data['events']);rows=[]
    for event in selected:
        if event['kind']!='deleted':continue
        value=wc.contrast(event,vectors);sensitivity=wc.contrast(event,vectors,True)
        rows.append(dict(writer=event['writer'],**value['difference'],sensitivity=sensitivity['difference']['embedding'] if sensitivity else None,
                         id=event['id'],session=event['session'],prompt=event['prompt'],timestamp=event['timestamp'],persist=int(value['difference']['embedding']>0)))
    result=dict(state='below floor, descriptive',scientific_admission=False,
                pooled={k:pooled(rows,k) for k in ('embedding','phrase','function_phrase','content','sensitivity')},
                reliability=wc.reliability(rows,wc.CONFIG),route='not licensed below original support floor',
                persistence_ratio=dict(state='not inferred below primary support floor'))
    return result,rows


def fr_fallback(feature):
    names=feature['profile_writers'];ownership={w:i for i,w in enumerate(names)};rows=[]
    for row in feature['rows']:
        rows.append(dict(writer=row['writer'],kind=row['kind'],style=row['delta_by_profile'][ownership[row['writer']]],pause=row['pause_delta']))
    return dict(state='below floor, descriptive',scientific_admission=False,
                by_kind={kind:{key:pooled([r for r in rows if r['kind']==kind],key) for key in ('style','pause')} for kind in ('frustration','deleted')},
                identification='No person-specific or frustration-mechanism claim from below-floor pooled observations')


def analyze(card,data,vectors,style):
    if card=='WC2':
        result,details=wc.analyze(data,vectors,wc.CONFIG)
        if result['state']=='unsupported':result['fallback'],rows=wc_fallback(data,vectors);details=dict(rows=rows)
        return result,details
    feature=style['features'];fn=FunctionType(fr.analyze.__code__,dict(fr.__dict__,contrast=cluster.contrast))
    result=fn(feature,20261026,2000,200)
    if not data['summary']['support']:result['fallback']=fr_fallback(feature)
    if style['calibration_pass']!=result['calibration_pass'] or style['calibration']!=result['calibration']:
        raise ValueError('FR1 calibration differs between complete stages')
    if result['calibration_pass'] and data['pairs']:
        required=fr_analysis.required(data)
        if set(vectors)!=set(required):raise ValueError('Incomplete FR1 embedding bank')
        rows=fr_analysis.embedding_deltas(data,vectors)
        if data['summary']['support']:
            rng=np.random.default_rng(20261027)
            result['secondary_embedding']={kind:fr.interval(list(fr.grouped([r for r in rows if r['kind']==kind],'embedding_delta').values()),rng,2000) for kind in ('frustration','deleted')}
        else:result['fallback']['embedding']={kind:pooled([r for r in rows if r['kind']==kind],'embedding_delta') for kind in ('frustration','deleted')}
    else:result['secondary_embedding']=dict(state='not_run_calibration_failed' if not result['calibration_pass'] else 'no_eligible_pairs')
    return result,feature


def run(output,inputs,config,verifying=False):
    if set(config)!={'card','mode'} or config['card'] not in ('WC2','FR1') or config['mode'] not in ('full','constructed'):
        raise ValueError('Frozen outcome analysis required')
    root=Path(output);root.mkdir(parents=True,exist_ok=True)
    if config['mode']=='constructed':
        if set(inputs)!={'fixture'}:raise ValueError('Explicit constructed fixture only')
        value=read(inputs['fixture']);data,vectors,style=value['data'],value['vectors'],value.get('style')
    else:
        if set(inputs)!={'feature_completion'}:raise ValueError('Complete frozen feature bank required')
        source=authenticate(Path(inputs['feature_completion']).parent)/'output';summary=read(source/'SUMMARY.json')
        if not summary['analysis_ready'] or summary['mode']!='full' or summary['card']!=config['card']:
            raise ValueError('Partial/constructed feature bank cannot feed human analysis')
        data,vectors,style=(gzread(source/name) for name in ('EVENTS.json.gz','VECTORS.json.gz','STYLE.json.gz'))
    result,details=analyze(config['card'],data,vectors,style)
    result['constructed_only']=config['mode']=='constructed'
    if result['constructed_only']:result['scientific_admission']=False
    binding=dict(config=config,inputs={k:filehash(v) for k,v in inputs.items()})
    for name,value in [('BINDING.json',binding),('RESULT.json',result)]:
        if verifying:
            if read(root/name)!=value:raise ValueError('Complete outcome statistic replay differs')
        else:write_equal(root/name,value)
    if verifying:
        if gzread(root/'DETAILS.json.gz')!=details:raise ValueError('Full private statistic replay differs')
    else:gzip_equal(root/'DETAILS.json.gz',details)
    return dict(verified=True,full_original_primary_and_descriptive_replay=True) if verifying else dict(status='complete',scientific_admission=False)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
