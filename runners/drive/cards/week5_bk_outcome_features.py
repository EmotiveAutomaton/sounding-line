"""Checkpointed frozen MiniLM features for WC2/FR1, including thin cohorts.

DESIGN CHECK: LESSONS 2--5/CONTROLS 1--7, 2026-11-07. Exact same
visible-prefix CPU-float32 ruler in every arm. Below-floor observations remain
descriptive. FR1 calibration failure still closes its embedding comparison.
Every text is sealed and freshly re-encoded; partial banks cannot feed analysis.
"""
import math
from pathlib import Path
import time
import numpy as np

from runners.stage9.common import digest
from . import week3_failed_means as wc
from . import week3_frames_stats as fr
from . import week3_frames_analysis as fr_analysis
from .week3_failed_means_features import Encoder,ConstructedEncoder,text_id
from .timing_closure_measure import model_identity
from .timing_pmap_source import completed
from .week5_at_source import authenticate
from .timing_census import read,filehash
from .timing_p6 import gzread,gzip_equal,write_equal,progress


def configuration(config):
    if set(config)!={'card','mode','max_wall_seconds'} or config['card'] not in ('WC2','FR1') or config['mode'] not in ('full','pilot','constructed') or not 30<=config['max_wall_seconds']<=1500:
        raise ValueError('Frozen outcome feature contract required')


def load(inputs,config):
    configuration(config)
    if config['mode']=='constructed':
        if set(inputs)!={'fixture'}:raise ValueError('Constructed fixture only')
        value=read(inputs['fixture']);return value['data'],value.get('dictionary'),ConstructedEncoder()
    expected={'source_completion','content_complete','model_manifest'}|({'pmap_completion'} if config['card']=='FR1' else set())
    if set(inputs)!=expected:raise ValueError('Authenticated source/model inputs required')
    root=authenticate(Path(inputs['source_completion']).parent);binding=read(root/'output/BINDING.json')['config']
    if binding['card']!=config['card']+'-inputs' or binding['mode']!='full' or binding['expected_sessions']!=1399:
        raise ValueError('Complete source population required')
    data=gzread(root/'output/EVENTS.json.gz');dictionary=None
    if config['card']=='FR1':
        parent=Path(inputs['pmap_completion']).parent;path=parent/'output/STYLE_DICTIONARY.json'
        if not path.exists():path=parent/'STYLE_DICTIONARY.json'
        completed(inputs['pmap_completion'],path);dictionary=read(path)
    # Initialization is delayed until after a possible calibration stop.
    model_identity(inputs)
    return data,dictionary,None


def prepare(data,dictionary,card):
    if card=='WC2':
        selected,texts=wc.required(data['events'])
        return dict(data,events=selected),None,texts
    features=fr.features(data,dictionary) if data['pairs'] else dict(profile_writers=[],rows=[],source_summary=data['summary'])
    # The original gate is evaluated at its original draw count. The floor
    # changes reporting eligibility, never the planted-ruler threshold.
    primary=[row for row in features['rows'] if row['kind']=='frustration'];rng=np.random.default_rng(20261026)
    calibration={key:fr.interval(list(fr.grouped(primary,key).values()),rng,2000) for key in ('calibration20','calibration40_increment')}
    passed=all(value['ci95'] is not None and value['ci95'][0]>0 for value in calibration.values())
    texts=fr_analysis.required(data) if passed else []
    return data,dict(features=features,calibration=calibration,calibration_pass=passed),texts


def run(output,inputs,config,verifying=False):
    start=time.monotonic();cpu=time.process_time();root=Path(output);root.mkdir(parents=True,exist_ok=True)
    configuration(config)
    paused=lambda:(root/'YIELD_REQUEST.json').exists() or (root.parent/'STOP').exists() or time.monotonic()-start>=config['max_wall_seconds']
    if paused():return dict(status='yielded',operation='outcome-features',scientific_admission=False)
    data,dictionary,encoder=load(inputs,config);data,style,texts=prepare(data,dictionary,config['card'])
    total=len(texts);texts=texts[:max(1,math.ceil(total/10))] if config['mode']=='pilot' else texts
    binding=dict(card=config['card'],mode=config['mode'],inputs={k:filehash(v) for k,v in inputs.items()},texts=digest(texts))
    if verifying:
        if read(root/'BINDING.json')!=binding:raise ValueError('Feature binding differs')
    else:write_equal(root/'BINDING.json',binding)
    if paused():return dict(status='yielded',operation='outcome-features',scientific_admission=False)
    if texts and encoder is None:encoder=Encoder(inputs,2)
    vectors={};scopes={}
    for n,text in enumerate(texts):
        key=text_id(text);path=root/'texts'/(key+'.json');seal=path.with_suffix('.seal.json')
        unit=dict(binding=digest(binding),text_sha256=key)
        if seal.exists():
            stamp=read(seal)
            if stamp.get('unit')!=unit or stamp.get('sha256')!=filehash(path):raise ValueError('Feature checkpoint seal differs')
            saved=read(path)
        else:saved=None
        if verifying or saved is None:
            vector,scope=encoder.vector(text);value=dict(vector=vector,scope=scope)
            if verifying:
                if saved!=value:raise ValueError('Complete embedding replay differs')
            else:write_equal(path,value);write_equal(seal,dict(unit=unit,sha256=filehash(path)))
        else:value=saved
        vectors[text]=value['vector'];scopes[key]=value['scope']
        progress(root/'PROGRESS.json',dict(phase='verify-encoding' if verifying else 'encoding',done=n+1,total=len(texts)))
        if paused():return dict(status='yielded',operation='outcome-features',texts=n+1,scientific_admission=False)
    if config['mode']!='constructed':model_identity(inputs)
    if binding['inputs']!={k:filehash(v) for k,v in inputs.items()}:raise ValueError('Feature input changed')
    summary=dict(card=config['card'],mode=config['mode'],required_unique_texts=total,encoded=len(texts),analysis_ready=config['mode']=='full',
                 constructed_only=config['mode']=='constructed',scientific_admission=False,
                 calibration_pass=style['calibration_pass'] if style else None)
    payload={'SUMMARY.json':summary};compressed={'VECTORS.json.gz':vectors,'SCOPES.json.gz':scopes}
    if config['mode']!='pilot':compressed.update({'EVENTS.json.gz':data,'STYLE.json.gz':style})
    for name,value in payload.items():
        if verifying:
            if read(root/name)!=value:raise ValueError('Feature summary differs')
        else:write_equal(root/name,value)
    for name,value in compressed.items():
        if verifying:
            if gzread(root/name)!=value:raise ValueError('Feature population differs')
        else:gzip_equal(root/name,value)
    path=root/('VERIFY_TIME.json' if verifying else 'EXECUTE_TIME.json')
    if not path.exists():write_equal(path,dict(cpu_seconds=time.process_time()-cpu,required_texts=total,encoded=len(texts),
        excludes='Previous segments, source and analysis; charge complete native accounting including loads and verification'))
    return dict(verified=True,complete_encoding_replay=True) if verifying else dict(status='complete',scientific_admission=False)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
