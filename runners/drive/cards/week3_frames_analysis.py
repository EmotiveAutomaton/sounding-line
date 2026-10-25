"""FR1 counted full comparison and separately non-admitting cost pilot.

DESIGN CHECK: LESSONS3-5 and CONTROLS, 2026-10-25. Full source, style roster
and MiniLM identity are authenticated. Calibration, paired whole-profile fake
and arm-label references are recomputed completely during fresh verification.
Known-answer fixtures use a labelled synthetic encoder only in constructed mode.
No partial embedding bank or timing pilot can become a completed science card.
"""
from pathlib import Path
import math
import time

import numpy as np

from . import week3_frames_stats as stats
from .week3_failed_means_features import Encoder,ConstructedEncoder
from .timing_closure_measure import model_identity
from .timing_pmap_source import completed
from .timing_census import read,filehash
from .timing_p6 import gzread,gzip_equal,write_equal,progress

CONFIG=dict(card='FR1',mode='full',seed=20261026,bootstraps=2000,permutations=200,threads=2)
PILOT=dict(CONFIG,mode='pilot')
CONSTRUCTED=dict(CONFIG,mode='constructed',bootstraps=100,permutations=40,threads=1)


def load(inputs,config):
    if config not in (CONFIG,PILOT,CONSTRUCTED):raise ValueError('frozen FR1 configuration required')
    if config==CONSTRUCTED:
        if set(inputs)!={'fixture'}:raise ValueError('constructed fixture required')
        value=read(inputs['fixture']);return value['data'],value['dictionary'],ConstructedEncoder()
    if set(inputs)!={'source_completion','pmap_completion','content_complete','model_manifest'}:raise ValueError('authenticated FR1 inputs required')
    parent=Path(inputs['source_completion']).parent
    for name in ('EVENTS.json.gz','SUMMARY.json','BINDING.json'):completed(inputs['source_completion'],parent/'output'/name)
    source=read(parent/'output/BINDING.json')
    if source['config']['card']!='FR1-inputs' or source['config']['mode']!='full' or source['config']['expected_sessions']!=1399:raise ValueError('full FR1 census required')
    pmap=Path(inputs['pmap_completion']).parent
    dictionary=pmap/'output/STYLE_DICTIONARY.json'
    if not dictionary.is_file():dictionary=pmap/'STYLE_DICTIONARY.json'
    completed(inputs['pmap_completion'],dictionary)
    data=gzread(parent/'output/EVENTS.json.gz')
    return data,read(dictionary),Encoder(inputs,config['threads']) if data['summary']['support'] else None


def required(data):
    return sorted({text for p in data['pairs'] for arm in ('event','control')
                   for text in [p[arm]['window']['text'],*p[arm]['offers']]})


def embedding_deltas(data,vectors):
    rows=[]
    for p in data['pairs']:
        distances=[]
        for arm in ('event','control'):
            row=p[arm];v=np.asarray(vectors[row['window']['text']],float)
            offers=np.asarray([vectors[t] for t in row['offers']],float)
            if not len(offers):raise ValueError('observed dismissal without offers')
            distances.append(float(np.mean(np.clip(1-offers@v,0,2))))
        rows.append(dict(writer=p['event']['writer'],kind=p['event']['kind'],embedding_delta=distances[0]-distances[1]))
    return rows


def run(output,inputs,config,verification=False):
    started=time.process_time();output=Path(output);output.mkdir(parents=True,exist_ok=True)
    data,dictionary,encoder=load(inputs,config)
    binding=dict(config=config,inputs={k:filehash(v) for k,v in sorted(inputs.items())})
    feature=stats.features(data,dictionary) if data['summary']['support'] else dict(profile_writers=[],rows=[],source_summary=data['summary'])
    statistics=stats.analyze(feature,config['seed'],config['bootstraps'],config['permutations'])
    base_cpu=time.process_time()-started
    all_texts=required(data) if data['summary']['support'] and statistics['calibration_pass'] else []
    selected=all_texts[:max(1,math.ceil(len(all_texts)/10))] if config==PILOT else all_texts
    vectors={};scopes={};encoded_start=time.process_time()
    for i,text in enumerate(selected):
        v,scope=encoder.vector(text);vectors[text]=v;scopes[text]=scope
        if i%16==0 or i+1==len(selected):
            progress(output/'PROGRESS.json',dict(phase='verify' if verification else 'encode',done=i+1,total=len(selected)))
            if (output.parent/'STOP').exists() or (output/'YIELD_REQUEST.json').exists():raise InterruptedError('owner requested yield')
    encode_cpu=time.process_time()-encoded_start
    if config!=CONSTRUCTED and encoder is not None:model_identity(inputs)
    if binding['inputs']!={k:filehash(v) for k,v in sorted(inputs.items())}:raise ValueError('FR1 source changed during analysis')
    if config==PILOT:
        result=dict(card='FR1-cost-pilot',state='incomplete_timing_only',required_texts=len(all_texts),encoded=len(selected),scientific_admission=False)
    else:
        result=statistics
        if all_texts:
            embedding=embedding_deltas(data,vectors)
            rng=np.random.default_rng(config['seed']+1)
            result['secondary_embedding']={kind:stats.interval(list(stats.grouped([r for r in embedding if r['kind']==kind],'embedding_delta').values()),rng,config['bootstraps']) for kind in ('frustration','deleted')}
        else:result['secondary_embedding']=dict(state='unsupported_primary_source' if not data['summary']['support'] else 'not_run_calibration_failed')
        result['constructed_only']=config==CONSTRUCTED
        if config==CONSTRUCTED:result['scientific_admission']=False
    payloads={'BINDING.json':binding,'RESULT.json':result}
    compressed={'FEATURES.json.gz':feature,'VECTORS.json.gz':vectors,'SCOPES.json.gz':scopes}
    for name,value in payloads.items():
        if verification:
            if read(output/name)!=value:raise ValueError('FR1 fresh replay differs')
        else:write_equal(output/name,value)
    for name,value in compressed.items():
        if verification:
            if gzread(output/name)!=value:raise ValueError('FR1 fresh feature replay differs')
        else:gzip_equal(output/name,value)
    timing=dict(base_cpu_seconds=base_cpu,embedding_cpu_seconds=encode_cpu,
                projected_full_execute_and_replay_cpu_seconds=2*(base_cpu+encode_cpu*len(all_texts)/max(1,len(selected))),
                excludes='all prior/native/pilot/source charges; owner accounts these against3600secondparent')
    name='VERIFY_TIME.json' if verification else 'EXECUTE_TIME.json'
    if not (output/name).exists():write_equal(output/name,timing)
    return dict(verified=True,complete_fresh_replay=True) if verification else result


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
